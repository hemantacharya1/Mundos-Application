import os
import json
from typing import TypedDict, Literal, List
import google.generativeai as genai
from langgraph.graph import StateGraph, END
from datetime import date
from pydantic import BaseModel, Field

from .. import crud, schemas, clinic_tools
from ..database import SessionLocal
from ..models import LeadStatusEnum, CommTypeEnum, CommDirectionEnum
from ..utils import send_email
from ..agents.triage_agent import load_and_populate_template

# --- Pydantic Models for this Agent ---
class AgentDecision(BaseModel):
    next_action: Literal['use_tool', 'reply_to_user', 'escalate_to_human'] = Field(description="The next immediate action the agent should take.")
    thought: str = Field(description="A brief thought process explaining the decision.")
    tool_to_use: str | None = Field(None, description="The name of the tool to use, if next_action is 'use_tool'.")
    tool_parameters: dict | None = Field(None, description="The parameters for the tool, if next_action is 'use_tool'.")
    reply_content: str | None = Field(None, description="The content of the email to send, if next_action is 'reply_to_user'.")

# --- Updated LangGraph State ---
class ReplyGraphState(TypedDict):
    lead_id: str
    first_name: str
    email: str
    conversation_history: List[str] # We'll now pass the whole history
    
    # Agent's working memory
    decision: AgentDecision | None = None
    tool_output: str | None = None

# --- Configure Gemini API ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="You are an autonomous AI assistant for a dental clinic. Your job is to handle email conversations with patients, use tools to answer questions, book appointments, and escalate to a human only when necessary."
)

# --- Agent Nodes ---

def decision_node(state: ReplyGraphState):
    """The core 'brain' of the agent. It decides the next action."""
    print(f"--- DECISION NODE for Lead ID: {state['lead_id']} ---")
    
    # The tools are described in the prompt, just like with Vapi
    tools_description = """
    - `get_plan_details(plan_name: str)`: Use this to find pricing and details for services.
    - `get_available_slots(day: str)`: Use this to find open appointment times.
    - `book_appointment(date: str, time: str, reason: str)`: Use this to finalize a booking.
    """
    
    # ADDED: Include the tool output in the prompt if it exists
    tool_output_context = ""
    if state.get('tool_output'):
        tool_output_context = f"\n**Tool Execution Result:**\n{state['tool_output']}\n"
    
    prompt = f"""
        You are an autonomous email agent for a dental clinic. Analyze the latest message in the conversation history and decide on the next action.

        **Conversation History (most recent message last):**
        {state['conversation_history']}

        **Available Tools:**
        {tools_description}
        
        {tool_output_context}

        **Your Task:**
        Based on the last message, decide the single next step.

        1. If you can answer a question or book an appointment using a tool, set `next_action` to `"use_tool"`.
        2. If you have enough information to reply directly (e.g., after a tool has been used), set `next_action` to `"reply_to_user"`.
        3. If the user's request is complex, emotionally charged, or a complaint, set `next_action` to `"escalate_to_human"`.

        **Output Format (MANDATORY):**
        Return ONLY a valid JSON object with the following exact schema:

        {{
        "next_action": "use_tool" | "reply_to_user" | "escalate_to_human",
        "thought": "A brief thought process explaining why you chose this action.",
        "tool_to_use": "string or null (if next_action is 'use_tool')",
        "tool_parameters": {{}} or null,
        "reply_content": "string or null (if next_action is 'reply_to_user')"
        }}

        ⚠️ Do not invent different field names. Use EXACTLY these keys.
        ⚠️ Never omit `thought`. Always include it as a short one-sentence rationale.
        ⚠️ Output ONLY the JSON object — no explanations, no extra text.
        **Context**
        -Today's Date is {date.today().strftime("%d-%m-%Y")} use this to return date param in MM-dd-YYYY
        """
    
    response = model.generate_content(prompt)
    try:
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        print(cleaned_response)
        decision_data = json.loads(cleaned_response)
        state['decision'] = AgentDecision(**decision_data)
    except Exception as e:
        print(f"Error making decision: {e}. Escalating to human.")
        state['decision'] = AgentDecision(next_action='escalate_to_human', thought="Could not parse LLM response.", tool_to_use=None, tool_parameters=None, reply_content=None)
        
    return state

def execute_tool_node(state: ReplyGraphState):
    """Executes the tool chosen by the decision_node."""
    decision = state['decision']
    tool_name = decision.tool_to_use
    params = decision.tool_parameters
    print(f"--- EXECUTING TOOL: {tool_name} with params: {params} ---")
    
    result = "Error: Tool not found."
    if tool_name == 'get_plan_details':
        result = clinic_tools.get_plan_details(**params)
    elif tool_name == 'get_available_slots':
        result = clinic_tools.get_available_slots(**params)
    elif tool_name == 'book_appointment':
        # We need to pass the lead_id to the booking tool
        result = clinic_tools.book_appointment(**params, lead_id=state['lead_id'])

    # MODIFIED: After executing a tool, we keep the decision in the state
    # and also append the tool output to the conversation history for full context
    state['tool_output'] = result
    state['conversation_history'].append(f"AI Tool Output: {result}")
    state['decision'] = None # Clear the decision to force a new one
    
    return state

def send_reply_node(state: ReplyGraphState):
    """Sends the AI-generated reply to the user."""
    print(f"--- SENDING REPLY to Lead ID: {state['lead_id']} ---")
    decision = state['decision']
    
    # Use our template system for a professional look
    context = {
        "first_name": state['first_name'],
        "summary": decision.reply_content, # The LLM-generated content
        "kb_section": "" # Placeholder for now
    }
    html_body = load_and_populate_template('nurture_email.html', context)
    
    reply_domain = os.getenv("REPLY_DOMAIN")
    tracking_reply_to = f"replies+{state['lead_id']}@{reply_domain}"
    
    send_email(
        to_email=state['email'],
        subject=f"Re: Your Inquiry with Bright Smile Clinic",
        body=decision.reply_content,
        html_body=html_body,
        reply_to_address=tracking_reply_to
    )
    
    # Log this automated reply
    db = SessionLocal()
    try:
        crud.create_communication_log(db, schemas.CommunicationCreate(
            lead_id=state['lead_id'],
            type=CommTypeEnum.email,
            direction=CommDirectionEnum.outgoing_auto,
            content=f"Subject: Re: Your Inquiry...\n\n{decision.reply_content}"
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
