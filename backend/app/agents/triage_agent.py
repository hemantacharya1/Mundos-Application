import os
from typing import TypedDict, Literal
import google.generativeai as genai
import openai
import re
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import json
import markdown

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
    You are a multi-tasking AI assistant for a dental clinic. Your primary objective is to understand a new inquiry so you can help convert this person into a patient.

    Analyze the following inquiry: "{state['inquiry_notes']}"
    If the inquiry is empty, assume it's a general sign-up requiring a warm follow-up.

    Return a JSON object with FOUR keys:
    1.  "category": Classify into ONE of ['Emergency', 'Insurance_Query', 'Scheduling_Query', 'Service_Inquiry', 'General_Follow_Up'].
    2.  "summary": A short noun phrase describing the topic , will be used as email subject(e.g., "Teeth whitening cost," "wisdom tooth pain," "New inquiry").
    3.  "is_emergency": A boolean value (true/false).
    4.  "kb_search_query": If the person is asking about a specific service or insurance, generate a concise search query for our database. Otherwise, this MUST be null.
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
        context_str += f"\n- {result['content']}\n"
    
    print(f"Found KB info: {context_str}")
    state['kb_info'] = context_str
    
    return state

# The generate_email_content_node and action_node remain exactly the same as your working version.
# They are already designed to handle the kb_info if it exists.
def generate_email_content_node(state: GraphState):
    """
    Generates a lead-nurturing email in Markdown, then converts it to HTML.
    """
    print(f"--- LEAD MANAGER EMAIL GENERATION for Lead ID: {state['lead_id']} ---")
    
    # Emergency path remains a simple, direct response.
    if state['is_emergency']:
        state['email_subject'] = f"{state['summary']}"
        # ... (emergency logic remains the same)
        return state

    # --- Lead Nurturing Path ---
    state['email_subject'] = f"{state['summary']}"
    kb_info = state.get('kb_info')

    # THE NEW, CONVERSION-FOCUSED PROMPT
    prompt = f"""
    You are an AI assistant for "Bright Smile Clinic", acting as a friendly and professional Lead Nurturing Specialist.
    Your primary goal is to convert this patient inquiry into a booked appointment.

    **Patient Details:**
    - Name: {state['first_name']}
    - Their Inquiry Summary: "{state['summary']}"

    **Internal Knowledge Base Notes (Use this to provide value):**
    ---
    {kb_info if kb_info else "No specific notes found. Acknowledge their inquiry and pivot to the value of a consultation."}
    ---

    **Your Task:**
    Write a warm, helpful, and persuasive email. Your response MUST be in Markdown format.
    
    **Communication & Conversion Tactics:**
    1.  **Acknowledge & Empathize:** Start by warmly addressing them by name and acknowledging their inquiry about "{state['summary']}".
    2.  **Provide Value:** Briefly answer their question using the Knowledge Base Notes.
    3.  **Bridge to the Goal:** Seamlessly connect your answer to the benefit of booking an appointment (e.g., "for a precise quote," "to discuss your options," "to create a personalized plan").
    4.  **Clear Call to Action (CTA):** ALWAYS end with a direct question to encourage a reply.
    
    **Example of a good CTA:**
    "Would you like to see what times we have available for a complimentary consultation next week?"
    
    ### FORMATTING ###
        -   **Greeting:** ALWAYS start your reply by addressing the user by their first name: '{state['first_name']}'.
        -   **Format:** Structure your final reply using Markdown for clarity. Use headings (`###`), bold (`**text**`), and lists (`* item`).
        -   **Persuasive Example:**
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful and persuasive dental clinic assistant who communicates in clear Markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    raw_llm_output = response.choices[0].message.content.strip()

    # --- NEW ROBUST PARSING LOGIC TO FIX THE BUG ---
    # This logic checks for and removes the markdown code block fences.
    clean_markdown_content = raw_llm_output
    if clean_markdown_content.startswith("```markdown"):
        clean_markdown_content = clean_markdown_content[len("```markdown"):].strip()
    if clean_markdown_content.endswith("```"):
        clean_markdown_content = clean_markdown_content[:-len("```")].strip()
    # --- END OF FIX ---

    # Use the cleaned content for conversion and logging
    personalized_body_html = markdown.markdown(clean_markdown_content,extensions=['tables'])
    personalized_body_plain = clean_markdown_content

    context = {
        'first_name': state['first_name'],
        'personalized_content': personalized_body_html
    }

    state['email_body_html'] = load_and_populate_template('nurture_email.html', context)
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
            body="",
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