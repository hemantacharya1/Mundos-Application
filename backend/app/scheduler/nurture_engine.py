import os
import json
import markdown
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import openai

# --- Project Imports ---
from .. import crud, models, schemas, voice_utils
from ..database import SessionLocal
from ..utils import send_email, send_sms, knowledge_base_semantic_search
from ..models import LeadStatusEnum, CommTypeEnum, CommDirectionEnum
from ..agents.triage_agent import load_and_populate_template

# --- OpenAI Client Initialization (Self-contained, no external llm_client needed) ---
try:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    MODEL_NAME = "gpt-4o-mini"
except Exception as e:
    print(f"FATAL: Could not initialize OpenAI client in nurture_engine.py: {e}")
    client = None

# --- NEW: Centralized, High-Performance Content Generation ---

def generate_follow_up_content(lead: models.Lead, attempt_number: int) -> dict:
    """
    Generates personalized, KB-aware, Markdown-formatted content for follow-ups.
    """
    if not client:
        # Fallback if OpenAI client fails to initialize
        return {"subject": "Following Up", "body_plain": "Just checking in.", "body_html": "<p>Just checking in.</p>"}

    print(f"--- Generating content for Lead {lead.lead_id}, Attempt #{attempt_number} ---")

    # Step 1: Search the Knowledge Base
    search_query = lead.inquiry_notes
    kb_results = knowledge_base_semantic_search(search_query, top_k=2)
    kb_info = "\n".join([res['content'] for res in kb_results]) if kb_results else "No specific information was found."

    # Step 2: Use a strategic prompt similar to the reply_agent
    system_prompt = "You are a helpful and persuasive marketing assistant for a dental clinic. Your goal is to re-engage a cold lead by providing value and encouraging them to book an appointment. Respond in a structured JSON format."
    user_prompt = f"""
    Your task is to write a friendly and persuasive follow-up message for a potential patient.

    **Patient Name:** {lead.first_name}
    **Their Original Inquiry Was About:** "{lead.inquiry_notes}"
    **This is Follow-up Attempt Number:** {attempt_number}
    **Relevant Information from our Knowledge Base:**
    ---
    {kb_info}
    ---

    **Instructions:**
    1.  Synthesize the Knowledge Base info into a helpful, easy-to-understand paragraph.
    2.  Craft a message that bridges from their original inquiry to a clear call-to-action (CTA).
    3.  For the final email attempt (attempt 4), create a sense of value (e.g., mention a free consultation) and gentle urgency.
    4.  The message body MUST be formatted in Markdown (using headings, lists, bold text).
    5.  ALWAYS end the message with a question or a clear next step.
    6.  Attempt 2 is for SMS so generate the markdown_body/content in less then 100 words. 

    Return ONLY a JSON object with two keys: "subject" (a compelling subject line) and "markdown_body" (the full message content in Markdown).
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        content_data = json.loads(response.choices[0].message.content)
        subject = content_data.get('subject', 'A quick follow-up from Bright Smile Clinic')
        markdown_body = content_data.get('markdown_body', 'Just checking in!')
    except Exception as e:
        print(f"Error generating follow-up content with OpenAI: {e}. Using fallback.")
        subject = "A quick follow-up from Bright Smile Clinic"
        markdown_body = f"Hi {lead.first_name},\n\nJust checking in on your recent inquiry about '{lead.inquiry_notes}'. Please let us know if we can help."

    # Step 3: Convert Markdown to HTML, exactly like the reply_agent
    html_body = markdown.markdown(markdown_body, extensions=['tables'])

    return {"subject": subject, "body_plain": markdown_body, "body_html": html_body}


# --- The Main Nurture Job (Using the new content and templates) ---

def nurture_and_recall_job():
    """
    This job runs periodically to follow up with leads in the 'nurturing' state.
    """
    print(f"--- Running Nurture & Recall Job at {datetime.now()} ---")
    db: Session = SessionLocal()
    try:
        nurturing_leads = db.query(models.Lead).filter(
            models.Lead.status == LeadStatusEnum.nurturing
        ).all()

        print(f"Found {len(nurturing_leads)} leads to process.")

        for lead in nurturing_leads:
            now = datetime.now(tz=lead.updated_at.tzinfo)
            time_since_last_update = now - lead.updated_at
            
            # --- Attempt 2: SMS (e.g., 2 days after initial contact) ---
            if lead.nurture_attempts == 1 and time_since_last_update > timedelta(day=1):
                content = generate_follow_up_content(lead, attempt_number=2)
                # For SMS, we use the plain text (Markdown) version, which is clean and readable.
                if send_sms(lead.phone_number, content['body_plain']):
                    lead.nurture_attempts += 1
                    crud.create_communication_log(db, schemas.CommunicationCreate(
                        lead_id=lead.id, type=CommTypeEnum.sms, direction=CommDirectionEnum.outgoing_auto, content=content['body_plain']
                    ))
                    db.commit()

            # --- Attempt 3: AI Phone Call (e.g., 4 days after initial contact) ---
            elif lead.nurture_attempts == 2 and time_since_last_update > timedelta(day=2):
                # ... (This logic remains the same)
                 if lead.phone_number:
                    call_data = voice_utils.make_tool_based_vapi_call(lead)
                    if call_data:
                        lead.nurture_attempts += 1
                        crud.create_communication_log(db, schemas.CommunicationCreate(
                            lead_id=lead.id, type=CommTypeEnum.phone_call, direction=CommDirectionEnum.outgoing_auto, content=f"AI call initiated. Vapi Call ID: {call_data.get('id')}"
                        ))
                        db.commit()
                    else:
                        lead.nurture_attempts += 1
                        db.commit()

            # --- Attempt 4: Final Email (e.g., 6 days after initial contact) ---
            elif lead.nurture_attempts == 3 and time_since_last_update > timedelta(day=3):
                content = generate_follow_up_content(lead, attempt_number=4)
                
                # Populate the main HTML template with our generated content
                context = {"first_name": lead.first_name, "personalized_content": content['body_html']}
                final_html_body = load_and_populate_template('nurture_email.html', context)
                
                reply_domain = os.getenv("REPLY_DOMAIN")
                tracking_reply_to = f"replies+{str(lead.id)}@{reply_domain}"
                
                if send_email(lead.email, content['subject'], "", html_body=final_html_body, reply_to_address=tracking_reply_to):
                    lead.nurture_attempts += 1
                    crud.create_communication_log(db, schemas.CommunicationCreate(
                        lead_id=lead.id, type=CommTypeEnum.email, direction=CommDirectionEnum.outgoing_auto, content=f"Subject: {content['subject']}\n\n{content['body_plain']}"
                    ))
                    db.commit()

            # --- Archive Lead (logic remains the same) ---
            elif lead.nurture_attempts >= 4:
                print(f"Archiving Lead ID: {lead.lead_id} after all attempts.")
                crud.update_lead_status(db, lead_id=lead.id, status=LeadStatusEnum.archived_no_response)
    finally:
        db.close()