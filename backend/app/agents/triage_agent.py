import os
from typing import TypedDict, Literal
import google.generativeai as genai
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
import json

from .. import crud, schemas
from ..database import SessionLocal
from ..utils import send_email
from ..models import LeadStatusEnum, CommTypeEnum, CommDirectionEnum

# --- Pydantic model for structured output from the LLM ---
class TriageResult(BaseModel):
    is_emergency: bool
    reason: str

# --- LangGraph State Definition ---
class GraphState(TypedDict):
    lead_id: str
    first_name: str
    email: str
    inquiry_notes: str
    is_emergency: bool | None = None
    email_subject: str | None = None
    email_body: str | None = None

# --- Configure Gemini API ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="You are an expert dental clinic receptionist AI. Your job is to analyze patient inquiries and perform tasks based on their content."
)

# --- Agent Nodes ---

def triage_node(state: GraphState):
    """Analyzes inquiry notes to determine if it's an emergency."""
    print(f"--- TRIAGE NODE for Lead ID: {state['lead_id']} ---")
    prompt = f"""
    Analyze the following patient inquiry and determine if it suggests a dental emergency or a complex query requiring immediate human attention.
    Emergency keywords include: pain, broken tooth, swelling, accident, bleeding, emergency, urgent.
    Complex queries include specific insurance questions.

    Inquiry: "{state['inquiry_notes']}"

    Respond ONLY with a JSON object with two keys: "is_emergency" (boolean) and "reason" (a brief explanation).
    Example: {{"is_emergency": true, "reason": "The user mentioned 'severe pain'."}}
    """
    response = model.generate_content(prompt)
    
    try:
        # Clean the response and parse it
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        result_json = json.loads(cleaned_response)
        triage_data = TriageResult(**result_json)
        state['is_emergency'] = triage_data.is_emergency
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing LLM response: {e}. Defaulting to non-emergency.")
        state['is_emergency'] = False
        
    return state

def human_handoff_node(state: GraphState):
    """Generates email content for an emergency lead."""
    print(f"--- HUMAN HANDOFF NODE for Lead ID: {state['lead_id']} ---")
    state['email_subject'] = "Urgent Inquiry Received - Bright Smile Clinic"
    state['email_body'] = f"Hi {state['first_name']},\n\nThank you for your inquiry. We've flagged it for immediate review due to its urgent nature.\n\nA member of our team will contact you shortly.\n\nSincerely,\nThe Bright Smile Clinic Team"
    return state

def nurture_node(state: GraphState):
    """Generates the first follow-up email for a standard lead."""
    print(f"--- NURTURE NODE for Lead ID: {state['lead_id']} ---")
    state['email_subject'] = "Following Up on Your Inquiry - Bright Smile Clinic"
    state['email_body'] = f"Hi {state['first_name']},\n\nThis is a friendly follow-up from the team at Bright Smile Clinic regarding your recent inquiry.\n\nWe wanted to see if you had any questions or if you were ready to book a visit. We're here to help!\n\nSincerely,\nThe Bright Smile Clinic Team"
    return state

def action_node(state: GraphState):
    """Performs the final actions: updates DB and sends email."""
    print(f"--- ACTION NODE for Lead ID: {state['lead_id']} ---")
    db = SessionLocal()
    try:
        is_nurture_start = not state['is_emergency']
        status_to_set = LeadStatusEnum.needs_immediate_attention if state['is_emergency'] else LeadStatusEnum.nurturing
        
        # 1. Update lead status in DB
        db_lead = crud.get_lead_by_id(db, state['lead_id'])
        if db_lead:
            db_lead.status = status_to_set
            # *** THIS IS THE NEW PART ***
            if is_nurture_start:
                db_lead.nurture_attempts = 1 # Set the first attempt!
            db.commit()
        
        # *** THIS IS THE NEW PART ***
        # Construct the dynamic Reply-To address
        reply_domain = os.getenv("REPLY_DOMAIN")
        tracking_reply_to = f"replies+{state['lead_id']}@{reply_domain}"

        # 2. Send the email
        send_email(
            to_email=state['email'],
            subject=state['email_subject'],
            body=state['email_body'],
            reply_to_address=tracking_reply_to # Pass it here
        )
        
        # 3. Log the communication
        comm_log = schemas.CommunicationCreate(
            lead_id=state['lead_id'],
            type=CommTypeEnum.email,
            direction=CommDirectionEnum.outgoing_auto,
            content=f"Subject: {state['email_subject']}\n\n{state['email_body']}"
        )
        crud.create_communication_log(db, comm=comm_log)
        
    finally:
        db.close()
    return state

# --- Conditional Router ---
def router(state: GraphState) -> Literal["human_handoff_node", "nurture_node"]:
    """Routes to the appropriate node based on the triage result."""
    if state['is_emergency']:
        return "human_handoff_node"
    else:
        return "nurture_node"

# --- Build the Graph ---
workflow = StateGraph(GraphState)
workflow.add_node("triage_node", triage_node)
workflow.add_node("human_handoff_node", human_handoff_node)
workflow.add_node("nurture_node", nurture_node)
workflow.add_node("action_node", action_node)

workflow.set_entry_point("triage_node")
workflow.add_conditional_edges("triage_node", router)
workflow.add_edge("human_handoff_node", "action_node")
workflow.add_edge("nurture_node", "action_node")
workflow.add_edge("action_node", END)

app_graph = workflow.compile()

# --- Main function to run the agent ---
def run_triage_agent(lead_id: str):
    db = SessionLocal()
    try:
        lead = crud.get_lead_by_id(db, lead_id)
        if not lead:
            print(f"Could not find lead with ID: {lead_id}")
            return

        initial_state = GraphState(
            lead_id=str(lead.id),
            first_name=lead.first_name,
            email=lead.email,
            inquiry_notes=lead.inquiry_notes
        )
        app_graph.invoke(initial_state)
    finally:
        db.close()