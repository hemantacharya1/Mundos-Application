import os
import json
import re
from typing import TypedDict, Annotated, List, Literal
from datetime import date
import markdown

# --- LangChain Core Imports ---
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# --- Pydantic Models for Tool Inputs (ensures type safety) ---
from pydantic import BaseModel, Field

# --- Existing Project Imports ---
from .. import crud, schemas, clinic_tools
from ..database import SessionLocal
from ..models import LeadStatusEnum, CommTypeEnum, CommDirectionEnum
from ..utils import knowledge_base_semantic_search, send_email
from ..agents.triage_agent import load_and_populate_template

# --- 1. Define Tools using the @tool decorator ---
# Docstrings are now the descriptions for the LLM.

@tool
def search_knowledge_base(query: str) -> str:
    """
    Use this to find information about dental procedures, insurance policies,
    clinic pricing, or general clinic information when you don't know the answer.
    """
    print(f"--- TOOL: Searching Knowledge Base for: '{query}' ---")
    search_results = knowledge_base_semantic_search(query=query, top_k=2)
    if search_results:
        return "Relevant Information Found:\n" + "\n".join([res['content'] for res in search_results])
    return "No specific information was found in the knowledge base about that topic."

@tool
def get_available_slots(day: str) -> str:
    """Use this to find available appointment times or slots for a specific day that the user mentions."""
    print(f"--- TOOL: Getting available slots for: {day} ---")
    return clinic_tools.get_available_slots(day=day)

class BookAppointmentInput(BaseModel):
    date: str = Field(description="The exact date for the appointment, e.g., '2025-09-23'.")
    time: str = Field(description="The exact time for the appointment, e.g., '14:00'.")
    reason: str = Field(description="A brief reason for the visit, e.g., 'checkup', 'tooth pain'.")

@tool
def book_appointment(date: str, time: str, reason:str, lead_id: str) -> str:
    """Use this to finalize an appointment booking once a specific date and time have been confirmed by the user."""
    print(f"--- TOOL: Booking appointment for Lead ID {lead_id} at {date} {time} ---")
    # The lead_id is injected by our agent node, not guessed by the LLM
    return clinic_tools.book_appointment(date=date, time=time, reason=reason, lead_id=lead_id)

@tool
def escalate_to_human(reason: str, lead_id: str) -> str:
    """
    Use this tool ONLY when a conversation is a complaint, is emotionally charged,
    or is too complex for you to handle. This is for situations needing a human touch.
    """
    print(f"--- TOOL: Escalating to human for Lead ID: {lead_id} ---")
    db = SessionLocal()
    try:
        lead = crud.get_lead_by_id(db, lead_id)
        if lead:
            lead.status = LeadStatusEnum.needs_immediate_attention
            lead.ai_summary = f"AI Escalation Reason: {reason}"
            db.commit()
            # This reply informs the agent that the task is done and it should not continue.
            return "Successfully flagged for human attention. Do not reply to the user further."
    finally:
        db.close()
    return "Escalation failed: Could not find lead."


# --- 2. Define LangGraph State ---
class ReplyGraphState(TypedDict):
    messages: Annotated[list, add_messages]
    lead_id: str
    email: str
    first_name: str


# --- 3. Configure LLM and Tools ---
OPENAI_MODEL = "gpt-4o-mini"
tools = [search_knowledge_base, get_available_slots, book_appointment, escalate_to_human]

# The ToolNode is a pre-built node that executes tools for us
tool_node = ToolNode(tools)

# Configure the LLM and bind the tools to it
llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0, streaming=False)
llm_with_tools = llm.bind_tools(tools)


# --- 4. Define Agent Nodes ---

def agent_node(state: ReplyGraphState):
    """The core 'brain' of the agent. It decides whether to reply or use a tool."""
    print(f"--- AGENT NODE for Lead ID: {state['lead_id']} ---")

    # This is a key pattern: we inject context from the state into tool calls
    # without the LLM needing to know about it.
    response = llm_with_tools.invoke(state['messages'])
    
    if response.tool_calls:
        for call in response.tool_calls:
            if "lead_id" in call["args"]:
                 call["args"]["lead_id"] = state['lead_id']
    
    return {"messages": [response]}


def send_reply_node(state: ReplyGraphState):
    """This is a terminal node. It sends the final email reply."""
    print(f"--- SENDING REPLY to Lead ID: {state['lead_id']} ---")
    final_message_content = state['messages'][-1].content
    print("final email",final_message_content)
    
    # The AI's response content is now directly used as the personalized HTML.
    # The system prompt has instructed it to generate simple HTML.
    final_markdown_content = final_message_content

    # --- KEY CHANGE: Convert Markdown to HTML ---
    # The `markdown.markdown()` function does the conversion for us.

    clean_markdown_content = final_markdown_content
    if clean_markdown_content.startswith("```markdown"):
        clean_markdown_content = clean_markdown_content[len("```markdown"):].strip()
    if clean_markdown_content.endswith("```"):
        clean_markdown_content = clean_markdown_content[:-len("```")].strip()

    personalized_body_html = markdown.markdown(clean_markdown_content,extensions=['tables'])

    # For the plain text version, we can use the original Markdown.
    personalized_body_plain = final_markdown_content

    context = {"personalized_content": personalized_body_html, "first_name": state['first_name']}
    html_body = load_and_populate_template('nurture_email.html', context)
    
    reply_domain = os.getenv("REPLY_DOMAIN")
    tracking_reply_to = f"replies+{state['lead_id']}@{reply_domain}"
    subject = f"Re: Your Inquiry with Bright Smile Clinic"
    
    send_email(
        to_email=state['email'],
        subject=subject,
        body=personalized_body_plain,
        html_body=html_body,
        reply_to_address=tracking_reply_to
    )
    
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


# --- 5. Define Conditional Router ---
def router(state: ReplyGraphState) -> Literal["tools", "__end__"]:
    """Routes to the tool executor or ends the graph if no tools are called."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        # If the agent decided to escalate, it's a terminal action.
        if any(call['name'] == 'escalate_to_human' for call in last_message.tool_calls):
            return "tools" # Execute the escalation tool, then end.
        return "tools"
    # Otherwise, the LLM has generated a final reply.
    return "__end__"


# --- 6. Build the Graph ---
workflow = StateGraph(ReplyGraphState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_node("send_reply", send_reply_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    router,
    # The router will decide which node to visit next
    {
        "tools": "tools",
        "__end__": "send_reply" # If no tools, send the reply
    }
)

# After tools are executed, loop back to the agent to reassess
workflow.add_edge("tools", "agent")

# After sending the reply, the process is finished
workflow.add_edge("send_reply", END)

# Compile the graph
reply_app_graph = workflow.compile()


# --- 7. Main function to run the agent ---
def run_reply_analyzer(lead_id: str):
    db = SessionLocal()
    try:
        lead = crud.get_lead_by_id(db, lead_id)
        if not lead:
            print(f"No lead found for ID: {lead_id}")
            return
        
        comms = crud.get_communications_by_lead_id(db, lead_id=lead.id)
        messages: List[BaseMessage] = []
        for c in comms:
            if c.direction == CommDirectionEnum.incoming:
                messages.append(HumanMessage(content=c.content))
            elif c.direction == CommDirectionEnum.outgoing_auto:
                # We log the plain text, but for the model's history, it's an AIMessage
                # This could be improved by logging the full AI output if needed
                messages.append(AIMessage(content=c.content.split('\n\n', 1)[-1]))

        # This new system prompt is cleaner and focuses on the persona and task.
        # In the `run_reply_analyzer` function:

        system_prompt = f"""
        You are an autonomous AI assistant for 'Bright Smile Clinic'. Your name is 'Neha', and you act as a friendly and professional Lead Nurturing Specialist.
        Today's Date is {date.today().strftime("%Y-%m-%d")}.

        ### PRIMARY OBJECTIVE ###
        Your main goal is to convert patient inquiries into booked appointments. Every response should be crafted to build trust, provide value, and guide the person towards the next logical step: scheduling a visit.

        ### STRATEGIC WORKFLOW ###
        1.  **Acknowledge & Empathize:** Start by warmly acknowledging their question. Show you understand their needs.
        2.  **Provide Value & Use Tools:** Use your available tools to give a clear and comprehensive answer.
        3.  **Bridge to the Goal:** Seamlessly connect your answer to the benefit of booking an appointment.
        4.  **Clear Call to Action (CTA):** ALWAYS end your message with a direct question or a suggested next step that encourages a reply and moves the conversation forward.

        ### COMMUNICATION & CONVERSION TACTICS ###
        -   **Persona:** You are a helpful, empathetic, and trustworthy guide. Your tone is professional yet approachable. You are confident in the clinic's services.
        -   **Always End with a Call to Action (CTA):** Never leave the conversation at a dead end. Your reply must always end with a question or a suggested next step.
            -   *Good CTA:* "Would you like me to book one of those times for you?"
            -   *Bad CTA:* "Let me know if you have other questions."
        -   **Anticipate Needs:** Think one step ahead. If they ask about the cost of a procedure, answer it and then immediately suggest a consultation for an exact quote and to discuss payment options.
        -   **Highlight Benefits, Not Just Features:**
            -   *Instead of:* "The cost is X."
            -   *Try:* "A dental crown is a great long-term investment in your smile. While the typical range is X, the best way to get a precise quote for your specific needs is to come in for a quick consultation. We can also discuss flexible payment plans then. Would you like to see our availability for next week?"
        -   **Create Gentle Urgency:** When providing appointment times, you can add phrases like "These slots tend to fill up quickly" to encourage prompt action.

        ### FORMATTING ###
        -   **Greeting:** ALWAYS start your reply by addressing the user by their first name: '{lead.first_name}'.
        -   **Format:** Structure your final reply using Markdown for clarity. Use headings (`###`), bold (`**text**`), and lists (`* item`).
        -   **Persuasive Example:**
            ### Available Times for This Friday
            * 10:00 AM
            * 11:00 AM
            * 2:00 PM

            These are our last few openings for the week and they tend to fill up quickly. **Which of these times works best for you, and I can reserve your spot right away?**

        ### IMPORTANT RULES ###
        -   Never use the word "lead". Refer to the person simply by their name.
        -   The 'lead_id' will be provided to tools automatically. Do not ask for it.
        -   Do not add Warm regards, [Your Name] Lead Nurturing Specialist etc. at the end of the email
        """
        
        initial_messages: List[BaseMessage] = [SystemMessage(content=system_prompt)] + messages

        initial_state = ReplyGraphState(
            lead_id=str(lead.id),
            email=lead.email,
            first_name=lead.first_name,
            messages=initial_messages
        )
        print(f"\n--- INVOKING GRAPH FOR LEAD: {lead.first_name} ({lead_id}) ---\n")
        reply_app_graph.invoke(initial_state)
        print(f"\n--- GRAPH EXECUTION FINISHED FOR LEAD: {lead.first_name} ({lead_id}) ---\n")

    except Exception as e:
        print(f"An error occurred while running the reply analyzer for lead {lead_id}: {e}")
    finally:
        db.close()