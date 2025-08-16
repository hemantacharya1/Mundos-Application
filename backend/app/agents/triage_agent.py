import os
from typing import TypedDict, Literal
import google.generativeai as genai
import openai
import re
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import json

from .. import crud, schemas
from ..database import SessionLocal
# Import your new KB search function and the existing utilities
from ..utils import send_email, send_whatsapp, knowledge_base_semantic_search
from ..models import LeadStatusEnum, CommTypeEnum, CommDirectionEnum

# --- Pydantic model for structured output from the LLM ---
# ADD the new kb_search_query field to the model
class TriageResult(BaseModel):
    category: Literal['Emergency', 'Insurance_Query', 'Scheduling_Query', 'Service_Inquiry', 'General_Follow_Up'] = Field(description="The primary category of the user's inquiry.")
    summary: str = Field(description="A concise noun phrase describing the service or issue.")
    is_emergency: bool = Field(description="A boolean flag indicating if the inquiry is a dental emergency.")
    kb_search_query: str | None = Field(None, description="A concise search query for a vector database if information is needed, otherwise null.")

# --- Updated LangGraph State Definition ---
# ADD the new kb_search_query field to the state
class GraphState(TypedDict):
    lead_id: str
    first_name: str
    email: str
    inquiry_notes: str
    category: str | None = None
    summary: str | None = None
    is_emergency: bool | None = None
    kb_info: str | None = None
    kb_search_query: str | None = None # New field
    email_subject: str | None = None
    email_body_plain: str | None = None
    email_body_html: str | None = None

# --- Configure Gemini API (No changes here) ---
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# model = genai.GenerativeModel(
#     model_name='gemini-1.5-flash',
#     system_instruction="You are an expert dental clinic receptionist AI. Your job is to analyze patient inquiries and provide concise information for communication."
# )

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-mini" # Use the new model

# --- Helper function to load and populate templates (No changes here) ---
def load_and_populate_template(template_name: str, context: dict) -> str:
    template_path = os.path.join(os.path.dirname(__file__), '..', 'template', template_name)
    with open(template_path, 'r') as f:
        template_str = f.read()
    for key, value in context.items():
        template_str = template_str.replace(f"{{{key}}}", str(value))
    return template_str

# --- Agent Nodes ---
def triage_node(state: GraphState):
    """
    Analyzes inquiry, categorizes it, and generates a KB search query if needed.
    """
    print(f"--- ADVANCED TRIAGE NODE for Lead ID: {state['lead_id']} ---")
    
    # ENHANCED PROMPT to generate the search query
    prompt = f"""
    You are a multi-tasking AI assistant for a dental clinic, Your JOb is to successfuly convert the lead. Analyze the following patient inquiry and perform a detailed classification. If no inquiry is present do a general followup and attract the lead.

    Inquiry: "{state['inquiry_notes']}"

    Your task is to return a JSON object with FOUR keys:
    1.  "category": Classify into ONE of ['Emergency', 'Insurance_Query', 'Scheduling_Query', 'Service_Inquiry', 'General_Follow_Up'].
    2.  "summary": Provide a short, concise noun phrase describing the exact service, issue, or topic mentioned (e.g., "teeth whitening cost", "wisdom tooth pain"). Keep it under 6 words.
    3.  "is_emergency": A boolean value (true/false).
    4.  "kb_search_query":
        - If the category is 'Service_Inquiry' or 'Insurance_Query', generate a concise, keyword-focused search query for a vector database.
        - For all other categories, this value MUST be null.
    """
    try:
        response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are an expert dental clinic receptionist AI. Your job is to analyze patient inquiries and provide a structured JSON output."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} # Use JSON mode for reliable output
            )
        result_json_str = response.choices[0].message.content
        result_json = json.loads(result_json_str)
        triage_data = TriageResult(**result_json)

        state.update({
            'category': triage_data.category,
            'summary': triage_data.summary,
            'is_emergency': triage_data.is_emergency,
            'kb_search_query': triage_data.kb_search_query
        })

    except Exception as e:
        print(f"Error parsing LLM response: {e}. Defaulting to General_Follow_Up.")
        state.update({
            'is_emergency': False,
            'category': 'General_Follow_Up',
            'summary': state['inquiry_notes'],
            'kb_search_query': None # Ensure it's null on error
        })
    return state

def kb_lookup_node(state: GraphState):
    """
    Performs a semantic search on the knowledge base if a query was generated.
    """
    search_query = state.get('kb_search_query')
    
    if not search_query:
        print(f"--- KB LOOKUP NODE (SKIPPED - No Query) for Lead ID: {state['lead_id']} ---")
        state['kb_info'] = None
        return state

    print(f"--- KB LOOKUP NODE (EXECUTING) for Lead ID: {state['lead_id']} ---")
    print(f"Searching KB with query: '{search_query}'")
    
    # Call your wrapper function from utils.py
    search_results = knowledge_base_semantic_search(query=search_query, top_k=2)
    
    if not search_results:
        print("No relevant information found in the knowledge base.")
        state['kb_info'] = None
        return state

    # Process the results into a clean string for the next LLM prompt.
    context_str = "Here is some potentially relevant information from our knowledge base:\n"
    for i, result in enumerate(search_results):
        # # Check if the score is high enough to be considered relevant
        # if result.get('score', 0) >: # You can adjust this threshold
        context_str += f"\n- {result['content']}\n"
    
    print(f"Found KB info: {context_str}")
    state['kb_info'] = context_str
    
    return state

# The generate_email_content_node and action_node remain exactly the same as your working version.
# They are already designed to handle the kb_info if it exists.
def generate_email_content_node(state: GraphState):
    """
    Generates a personalized, human-like email using an LLM and populates
    a high-quality HTML template.
    """
    print(f"--- FINAL EMAIL GENERATION for Lead ID: {state['lead_id']} ---")
    context = {
        "first_name": state['first_name'],
        "summary": state['summary']
    }

    # Emergency path remains unchanged, using a simpler template if needed.
    if state['is_emergency']:
        state['email_subject'] = f"Urgent Inquiry Received - {state['summary']}"
        # You can create a separate, simpler emergency HTML template if you wish
        state['email_body_html'] = load_and_populate_template('emergency_email.html', context)
        state['email_body_plain'] = f"Hi {state['first_name']}, Thank you for your inquiry regarding an urgent matter: '{state['summary']}'. A team member will call you shortly."
        return state

    # --- Non-Emergency Path: Generate content and use the new template ---
    state['email_subject'] = f"{state['summary']}"
    kb_info = state.get('kb_info')

    # This prompt instructs the LLM to act as a helpful human receptionist.
    prompt = f"""
    You are an expert dental receptionist and lead manager for "Bright Smile Clinic". Your tone is warm, professional, and helpful.

    **Your Task:**
    Write a concise and easy-to-read email body. **Your output must be a clean HTML snippet.**

    **Patient Details:**
    - Name: {state['first_name']}
    - Their Inquiry Summary: "{state['summary']}"

    **Internal Knowledge Base Notes (for your reference):**
    ---
    {kb_info if kb_info else "No specific notes found for this topic."}
    ---

    **Instructions for the HTML snippet:**
    1.  **Be Concise:** Keep the email under 120 words. The goal is to be helpful and start a conversation, not to overwhelm.
    2.  **Use Simple HTML Tags:** Use `<p>`, `<ul>`, `<li>`, and `<strong>` for emphasis.
    3.  **DO NOT** include `<html>`, `<head>`, or `<body>` tags. The output must be ONLY the content that goes inside the email body.
    4.  **Be Selective:** Acknowledge their question about "{state['summary']}". if query is general attempt to covert the lead.
    5.  **End with a clear call to action** or a question to encourage a reply. Example: "<p>Would you like to know about the services we offer?</p>"
    """

    # Generate the personalized content from the LLM
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are an expert dental clinic receptionist AI. Your job is to write helpful and personal emails to patients."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7 # Add some temperature for more natural-sounding emails
    )
    personalized_body_html = response.choices[0].message.content.strip()

    # ### --- CODE CHANGE: Create plain text by stripping HTML tags --- ###
    # A simple regex to remove tags for the plain text version of the email.
    personalized_body_plain = re.sub('<[^<]+?>', '', personalized_body_html).strip()

    # Add the generated HTML to the context for the template
    context['personalized_content'] = personalized_body_html

    # Populate the HTML template with our newly formatted HTML
    state['email_body_html'] = load_and_populate_template('nurture_email.html', context)
    # The plain text version is now the cleaned HTML
    state['email_body_plain'] = personalized_body_plain

    return state

def action_node(state: GraphState):
    """Performs the final actions: updates DB and sends communications."""
    # This function does not need any changes.
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

        send_email(
            to_email=state['email'],
            subject=state['email_subject'],
            body=state['email_body_plain'],
            html_body=state['email_body_html'],
            reply_to_address=tracking_reply_to
        )
        
        # if db_lead and db_lead.phone_number:
        #     if send_whatsapp(db_lead.phone_number, body=state['email_body_plain']):
        #         print("WhatsApp message sent successfully.")
        
        crud.create_communication_log(db, schemas.CommunicationCreate(
            lead_id=state['lead_id'],
            type=CommTypeEnum.email,
            direction=CommDirectionEnum.outgoing_auto,
            content=f"Subject: {state['email_subject']}\n\n{state['email_body_plain']}"
        ))
    finally:
        db.close()
    return state

# --- This is the single, correct router for this graph ---
# UPDATED ROUTER LOGIC
def router(state: GraphState) -> Literal["kb_lookup_node", "generate_email_content_node"]:
    """Checks if a KB search query was generated and routes accordingly."""
    print(f"--- ROUTER: Checking for KB query ---")
    if state.get('kb_search_query'):
        # If a query exists, go to the lookup node
        return "kb_lookup_node"
    else:
        # Otherwise, skip straight to email generation
        return "generate_email_content_node"

# --- Build the Final Graph (No changes here) ---
workflow = StateGraph(GraphState)
workflow.add_node("triage_node", triage_node)
workflow.add_node("kb_lookup_node", kb_lookup_node)
workflow.add_node("generate_email_content_node", generate_email_content_node)
workflow.add_node("action_node", action_node)

workflow.set_entry_point("triage_node")
workflow.add_conditional_edges("triage_node", router)
workflow.add_edge("kb_lookup_node", "generate_email_content_node")
workflow.add_edge("generate_email_content_node", "action_node")
workflow.add_edge("action_node", END)

app_graph = workflow.compile()

# --- Main function to run the agent (No changes here) ---
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