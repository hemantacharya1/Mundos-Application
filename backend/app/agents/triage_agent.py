import os
from typing import TypedDict, Literal
import google.generativeai as genai
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import json

from .. import crud, schemas
from ..database import SessionLocal
from ..utils import send_email, send_whatsapp
from ..models import LeadStatusEnum, CommTypeEnum, CommDirectionEnum

# --- Pydantic model for structured output from the LLM ---
class TriageResult(BaseModel):
    category: Literal['Emergency', 'Insurance_Query', 'Scheduling_Query', 'Service_Inquiry', 'General_Follow_Up'] = Field(description="The primary category of the user's inquiry.")
    summary: str = Field(description="A concise one-sentence summary of the user's specific inquiry.")
    is_emergency: bool = Field(description="A boolean flag indicating if the inquiry is a dental emergency.")

# --- Updated LangGraph State Definition ---
class GraphState(TypedDict):
    lead_id: str
    first_name: str
    email: str
    inquiry_notes: str
    category: str | None = None
    summary: str | None = None
    is_emergency: bool | None = None
    kb_info: str | None = None
    email_subject: str | None = None
    email_body_plain: str | None = None
    email_body_html: str | None = None

# --- Configure Gemini API ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="You are an expert dental clinic receptionist AI. Your job is to analyze patient inquiries and provide concise information for communication."
)

# --- Helper function to load and populate templates ---
def load_and_populate_template(template_name: str, context: dict) -> str:
    """Loads an HTML template from a file and injects context data."""
    template_path = os.path.join(os.path.dirname(__file__), '..', 'template', template_name)
    with open(template_path, 'r') as f:
        template_str = f.read()
    for key, value in context.items():
        template_str = template_str.replace(f"{{{key}}}", str(value))
    return template_str

# --- Agent Nodes ---
def triage_node(state: GraphState):
    """Analyzes inquiry notes to categorize it and extract key details."""
    print(f"--- REFINED TRIAGE NODE for Lead ID: {state['lead_id']} ---")
    prompt = f"""
    Analyze the following patient inquiry for a dental clinic. Your task is to perform a detailed classification.
    Inquiry: "{state['inquiry_notes']}"

    Based on the inquiry, provide a JSON object with the following three keys:
    1.  "category": Classify into ONE of ['Emergency', 'Insurance_Query', 'Scheduling_Query', 'Service_Inquiry', 'General_Follow_Up'].
    2.  "summary": Provide a short, concise noun phrase describing the exact service, issue, or topic mentioned by the patient (no full sentences, no extra words like "the patient is asking about"). Keep it under 6 words.
    3.  "is_emergency": A boolean value (true/false).
    """
    response = model.generate_content(prompt)
    try:
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        result_json = json.loads(cleaned_response)
        triage_data = TriageResult(**result_json)
        state.update({
            'category': triage_data.category,
            'summary': triage_data.summary,
            'is_emergency': triage_data.is_emergency
        })
    except Exception as e:
        print(f"Error parsing LLM response: {e}. Defaulting to General_Follow_Up.")
        state.update({
            'is_emergency': False,
            'category': 'General_Follow_Up',
            'summary': state['inquiry_notes']
        })
    return state

def kb_lookup_node(state: GraphState):
    """*** FUTURE IMPLEMENTATION HOOK ***"""
    print(f"--- KB LOOKUP NODE (SKIPPED) for Lead ID: {state['lead_id']} ---")
    # In the future, your KB search logic will go here.
    # It will populate state['kb_info'].
    return state

def generate_email_content_node(state: GraphState):
    """Selects a template and assembles the final HTML email."""
    print(f"--- TEMPLATE-BASED EMAIL GENERATION for Lead ID: {state['lead_id']} ---")
    context = {"first_name": state['first_name'], "summary": state['summary']}

    if state['is_emergency']:
        state['email_subject'] = f"Urgent Inquiry Received - {state['summary']}"
        state['email_body_html'] = load_and_populate_template('emergency_email.html', context)
        state['email_body_plain'] = f"Hi {state['first_name']}, Thank you for your inquiry regarding an urgent matter: '{state['summary']}'. A team member will call you shortly."
    else:
        state['email_subject'] = f"Following Up on Your Inquiry about {state['summary']}"
        kb_info = state.get('kb_info')
        kb_section_html = ""
        if kb_info:
            # This is where you could use an LLM for a small task if needed, or just format the text.
            kb_section_html = f'<div class="kb-section"><p>{kb_info}</p></div>'
        
        context['kb_section'] = kb_section_html
        state['email_body_html'] = load_and_populate_template('nurture_email.html', context)
        state['email_body_plain'] = f"Hi {state['first_name']}, Following up on your inquiry about '{state['summary']}'. {kb_info or 'We are looking into your question and will get back to you.'}"
    return state

def action_node(state: GraphState):
    """Performs the final actions: updates DB and sends communications."""
    print(f"--- ACTION NODE for Lead ID: {state['lead_id']} ---")
    db = SessionLocal()
    try:
        status_to_set = LeadStatusEnum.needs_immediate_attention if state['is_emergency'] else LeadStatusEnum.nurturing
        
        db_lead = crud.get_lead_by_id(db, state['lead_id'])
        if db_lead:
            db_lead.status = status_to_set
            if not state['is_emergency']:
                db_lead.nurture_attempts = 1
            db.commit()
        
        reply_domain = os.getenv("REPLY_DOMAIN")
        tracking_reply_to = f"replies+{state['lead_id']}@{reply_domain}"

        # 1. Send the dynamic email
        send_email(
            to_email=state['email'],
            subject=state['email_subject'],
            body=state['email_body_plain'],
            html_body=state['email_body_html'],
            reply_to_address=tracking_reply_to
        )
        
        # 2. Send a consistent WhatsApp message
        if db_lead and db_lead.phone_number:
            # Use the plain text body for WhatsApp for consistency
            if send_whatsapp(db_lead.phone_number, body=state['email_body_plain']):
                print("WhatsApp message sent successfully.")
        
        # 3. Log the primary communication (email)
        crud.create_communication_log(db, schemas.CommunicationCreate(
            lead_id=state['lead_id'],
            type=CommTypeEnum.email,
            direction=CommDirectionEnum.outgoing_auto,
            # CORRECTED: Use email_body_plain, which is guaranteed to exist.
            content=f"Subject: {state['email_subject']}\n\n{state['email_body_plain']}"
        ))
    finally:
        db.close()
    return state

# --- This is the single, correct router for this graph ---
def router(state: GraphState) -> Literal["kb_lookup_node", "generate_email_content_node"]:
    """Decides if a KB lookup is needed before generating the email."""
    print(f"--- ROUTER for category: {state['category']} ---")
    # For now, we bypass the KB for all categories.
    # In the future, you can add logic here:
    # if state['category'] == 'Service_Inquiry':
    #     return "kb_lookup_node"
    return "generate_email_content_node"

# --- Build the Final Graph ---
workflow = StateGraph(GraphState)
workflow.add_node("triage_node", triage_node)
workflow.add_node("kb_lookup_node", kb_lookup_node)
workflow.add_node("generate_email_content_node", generate_email_content_node)
workflow.add_node("action_node", action_node)

workflow.set_entry_point("triage_node")
# The triage node now goes to our new router
workflow.add_conditional_edges("triage_node", router)
# The KB node (even though it does nothing yet) connects to the email generator
workflow.add_edge("kb_lookup_node", "generate_email_content_node")
# The email generator connects to the final action node
workflow.add_edge("generate_email_content_node", "action_node")
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