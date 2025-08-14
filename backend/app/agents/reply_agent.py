import os
import json
from typing import TypedDict, Literal, List
import openai
import re
from langgraph.graph import StateGraph, END
from datetime import date
from pydantic import BaseModel, Field

from .. import crud, schemas, clinic_tools
from ..database import SessionLocal
from ..models import LeadStatusEnum, CommTypeEnum, CommDirectionEnum
from ..utils import knowledge_base_semantic_search, send_email
from ..agents.triage_agent import load_and_populate_template

# --- Pydantic Models for this Agent ---
class AgentDecision(BaseModel):
    next_action: Literal['use_tool', 'reply_to_user', 'escalate_to_human'] = Field(description="The next immediate action the agent should take.")
    thought: str = Field(description="A brief thought process explaining the decision.")
    
    # --- Fields for 'use_tool' action ---
    tool_to_use: str | None = Field(None, description="The name of the tool to use, if next_action is 'use_tool'.")
    tool_parameters: dict | None = Field(None, description="The parameters for the tool, if next_action is 'use_tool'.")
    kb_search_query: str | None = Field(None, description="A search query for the vector database if the tool is 'search_knowledge_base'.")

    # --- Field for 'reply_to_user' action ---
    personalized_html_content: str | None = Field(None, description="A clean HTML snippet to be injected into the main email template, if next_action is 'reply_to_user'.")
# --- Updated LangGraph State ---
class ReplyGraphState(TypedDict):
    lead_id: str
    first_name: str
    email: str
    conversation_history: List[str] # We'll now pass the whole history
    
    # Agent's working memory
    decision: AgentDecision | None = None
    tool_output: str | None = None
    kb_search_query: str | None = None
    kb_info: str | None = None

# --- Configure Gemini API ---
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# model = genai.GenerativeModel(
#     model_name='gemini-1.5-flash',
#     system_instruction="You are an autonomous AI assistant for a dental clinic. Your job is to handle email conversations with patients, use tools to answer questions, book appointments, and escalate to a human only when necessary."
# )
client = openai.OpenAI()
OPENAI_MODEL = "gpt-4o-mini" 

# --- Agent Nodes ---

def decision_node(state: ReplyGraphState):
    """The core 'brain' of the agent. It decides the next action using a more robust prompt."""
    print(f"--- DECISION NODE (OpenAI) for Lead ID: {state['lead_id']} ---")
    
    tools_description = """
    - `search_knowledge_base(query: str)`: Use this to find information about dental procedures, insurance policies, or general clinic info.
    - `get_available_slots(day: str)`: Use this to find open appointment times.
    - `book_appointment(date: str, time: str, reason: str)`: Use this to finalize a booking.
    """
    
    previous_output_context = ""
    if state.get('tool_output'):
        previous_output_context = f"\n**Context from Previous Tool Result:**\n{state['tool_output']}\n"
    elif state.get('kb_info'):
        previous_output_context = f"\n**Context from Knowledge Base Search:**\n{state['kb_info']}\n"

    # This new prompt is more direct and provides clear JSON examples for the LLM to follow.
    prompt = f"""
    You are an autonomous email agent for a dental clinic. Your goal is to resolve the user's needs efficiently.
    Today's Date is {date.today().strftime("%Y-%m-%d")}.

    **Conversation History (most recent message last):**
    {state['conversation_history']}

    **Previous Output Context
    {previous_output_context}

    **Available Tools:**
    {tools_description}

    **Your Task:**
    Analyze the full context and decide on the single next step. Respond with a JSON object.

    1.  **If you need more information to answer the user's question**, your `next_action` MUST be `"use_tool"`.
        - Set `tool_to_use` to `"search_knowledge_base"`.
        - Generate a `kb_search_query` based on the user's question.
        - Example: {{"next_action": "use_tool", "thought": "The user is asking about crowns, I need to look that up.", "tool_to_use": "search_knowledge_base", "kb_search_query": "cost of dental crowns"}}

    2.  **If the user wants to schedule and have mention a available slot**, your `next_action` MUST be `"use_tool"`.
        - Set `tool_to_use` to the appropriate tool (`book_appointment`).
        - Provide the necessary `tool_parameters`.
        - Example: {{"next_action": "use_tool", "thought": "The user wants to book for Tuesday afternoon.", "tool_to_use": "book_appointment", "tool_parameters": {{"date": "Tuesday", "time": "2:00 PM", "reason": "checkup"}}}}

    3.  **If the user wants to check availability or have asked to book appointement without mentioning a slot then offer available slots and reply to get back time from user**, your `next_action` MUST be `"use_tool"`.
        - Set `tool_to_use` to the appropriate tool (`get_available_slots`).
        - Provide the necessary `tool_parameters`.
        - Example: {{"next_action": "use_tool", "thought": "The user wants to know available slots", "tool_to_use": "get_available_slots", "tool_parameters": {{"day": "Tuesday","}}}}


    4.  **If you have all the information you need to reply and have previous_output_context**, your `next_action` MUST be `"reply_to_user"`.
        - Generate a `personalized_html_content` snippet for the email body. Use simple HTML tags like `<p>` and `<strong>`.
        - Example: {{"next_action": "reply_to_user", "thought": "I have the KB info about crowns, now I can answer the user.", "personalized_html_content": "<p>Thanks for asking! A dental crown typically costs between X and Y. Would you like to book a consultation?</p>"}}

    5.  **If the request is a complaint, very complex, or emotionally charged**, your `next_action` MUST be `"escalate_to_human"`.
        - Example: {{"next_action": "escalate_to_human", "thought": "The user seems upset about their last visit. A human should handle this."}}
    """
    
    messages = [
        {"role": "system", "content": "You are an AI assistant that strictly follows instructions and only outputs valid JSON based on the provided schema and examples."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            response_format={"type": "json_object"}
        )
        decision_json = response.choices[0].message.content
        # Manually fill in missing optional keys to prevent Pydantic errors
        decision_data = json.loads(decision_json)
        decision_data.setdefault('tool_to_use', None)
        decision_data.setdefault('tool_parameters', None)
        decision_data.setdefault('kb_search_query', None)
        decision_data.setdefault('personalized_html_content', None)
        
        state['decision'] = AgentDecision(**decision_data)
    except Exception as e:
        print(f"Error making OpenAI decision: {e}. Escalating to human.")
        state['decision'] = AgentDecision(next_action='escalate_to_human', thought="Could not parse LLM response.", tool_to_use=None, tool_parameters=None, kb_search_query=None, personalized_html_content=None)
        
    return state


def execute_tool_node(state: ReplyGraphState):
    """Executes the tool chosen by the decision_node, including KB search."""
    decision = state['decision']
    tool_name = decision.tool_to_use
    params = decision.tool_parameters
    print(f"--- EXECUTING TOOL: {tool_name} with params: {params} ---")
    
    result = "Error: Tool not found."
    # Add the new KB search tool to our execution logic
    if tool_name == 'search_knowledge_base':
        query = decision.kb_search_query
        search_results = knowledge_base_semantic_search(query=query, top_k=2)
        if search_results:
            result = "Here is some relevant information:\n" + "\n".join([res['content'] for res in search_results])
        else:
            result = "No specific information was found in the knowledge base regarding that topic."
        state['kb_info'] = result # Store result in kb_info
        state['tool_output'] = None # Clear tool_output
    elif tool_name == 'get_plan_details':
        # This tool is now effectively replaced by the KB search, but we can keep it for legacy reasons
        result = clinic_tools.get_plan_details(**params)
        state['tool_output'] = result
        state['kb_info'] = None
    elif tool_name == 'get_available_slots':
        result = clinic_tools.get_available_slots(**params)
        state['tool_output'] = result
        state['kb_info'] = None
    elif tool_name == 'book_appointment':
        result = clinic_tools.book_appointment(**params, lead_id=state['lead_id'])
        state['tool_output'] = result
        state['kb_info'] = None

    # After executing a tool, we must always make a new decision
    state['decision'] = None
    return state
    
def send_reply_node(state: ReplyGraphState):
    """
    Sends a high-quality, template-based reply using AI-generated HTML content.
    """
    print(f"--- SENDING TEMPLATE-BASED REPLY to Lead ID: {state['lead_id']} ---")
    decision = state['decision']
    
    # The LLM has generated the core HTML content for us.
    personalized_body_html = decision.personalized_html_content

    # Create a plain text version by stripping HTML tags.
    # This is crucial for email clients that don't render HTML.
    personalized_body_plain = re.sub('<[^<]+?>', '', personalized_body_html).strip()

    # Populate our main, high-quality template
    context = {
        "personalized_content": personalized_body_html
    }
    # NOTE: We are using a new template name here for clarity.
    # You should use the same template file as your other agent.
    html_body = load_and_populate_template('nurture_email.html', context)
    
    reply_domain = os.getenv("REPLY_DOMAIN")
    tracking_reply_to = f"replies+{state['lead_id']}@{reply_domain}"
    
    # The subject can be static for replies, or you can have the LLM generate it.
    subject = f"Re: Your Inquiry with Bright Smile Clinic"
    
    # Call the utility that supports HTML
    send_email(
        to_email=state['email'],
        subject=subject,
        body=personalized_body_plain, # Plain text version for compatibility
        html_body=html_body,         # Rich HTML version
        reply_to_address=tracking_reply_to
    )
    
    # Log this automated reply
    db = SessionLocal()
    try:
        crud.create_communication_log(db, schemas.CommunicationCreate(
            lead_id=state['lead_id'],
            type=CommTypeEnum.email,
            direction=CommDirectionEnum.outgoing_auto,
            content=f"Subject: {subject}\n\n{personalized_body_plain}"
        ))
    finally:
        db.close()
    
    return state

def escalate_to_human_node(state: ReplyGraphState):
    """Flags the lead for immediate human attention."""
    print(f"--- ESCALATING to human for Lead ID: {state['lead_id']} ---")
    db = SessionLocal()
    try:
        lead = crud.get_lead_by_id(db, state['lead_id'])
        if lead:
            lead.status = LeadStatusEnum.needs_immediate_attention
            # Save the agent's thought process as a summary for the human
            lead.ai_summary = state['decision'].thought
            db.commit()
    finally:
        db.close()
    return state

# --- Conditional Router ---
def router(state: ReplyGraphState):
    """Routes to the next appropriate node based on the agent's decision."""
    if not state.get('decision'):
        # This will be true after a tool is used, forcing a re-evaluation
        return 'decision_node'
        
    next_action = state['decision'].next_action
    if next_action == 'use_tool':
        return 'execute_tool_node'
    elif next_action == 'reply_to_user':
        return 'send_reply_node'
    elif next_action == 'escalate_to_human':
        return 'escalate_to_human_node'
    return END

# --- Build the Graph ---
workflow = StateGraph(ReplyGraphState)
workflow.add_node("decision_node", decision_node)
workflow.add_node("execute_tool_node", execute_tool_node)
workflow.add_node("send_reply_node", send_reply_node)
workflow.add_node("escalate_to_human_node", escalate_to_human_node)

workflow.set_entry_point("decision_node")
workflow.add_conditional_edges("decision_node", router)
# After executing a tool, the agent must re-evaluate the situation
workflow.add_edge("execute_tool_node", "decision_node")
workflow.add_edge("send_reply_node", END)
workflow.add_edge("escalate_to_human_node", END)

reply_app_graph = workflow.compile()

# --- Main function to run the agent ---
def run_reply_analyzer(lead_id: str):
    db = SessionLocal()
    try:
        lead = crud.get_lead_by_id(db, lead_id)
        if not lead:
            return
        
        # Fetch the conversation history
        comms = crud.get_communications_by_lead_id(db, lead_id=lead.id)
        # Format history for the LLM
        conversation_history = [f"{c.direction}: {c.content}" for c in comms]

        initial_state = ReplyGraphState(
            lead_id=str(lead.id),
            first_name=lead.first_name,
            email=lead.email,
            conversation_history=conversation_history
        )
        reply_app_graph.invoke(initial_state)
    finally:
        db.close()
