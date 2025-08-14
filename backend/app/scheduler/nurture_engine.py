from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import json
import openai
from .. import crud, models, schemas, voice_utils
from ..database import SessionLocal
from ..utils import send_email, send_sms
from ..models import LeadStatusEnum, CommTypeEnum, CommDirectionEnum

# We can reuse the same Gemini model configuration
from ..agents.triage_agent import load_and_populate_template

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-mini"

# --- NEW: Centralized Content Generation Function ---

def generate_follow_up_content(lead: models.Lead, attempt_number: int, kb_info: str | None = None) -> dict:
    """
    Generates personalized content for a specific follow-up attempt.
    Returns a dictionary with 'subject', 'body_plain', and 'body_html'.
    """
    print(f"--- Generating content for Lead {lead.lead_id}, Attempt #{attempt_number} ---")
    
    # This prompt asks the LLM to act as a creative copywriter for follow-ups
    prompt = f"""
    You are a marketing expert at a dental clinic. Your task is to write a concise, friendly, and non-pushy follow-up message for a potential patient.

    **Patient Name:** {lead.first_name}
    **Their Original Inquiry Was About:** "{lead.inquiry_notes}"
    **This is Follow-up Attempt Number:** {attempt_number}
    **Relevant Information from our Knowledge Base:** {kb_info or 'None'}

    Based on this, generate a short message.
    - For attempt 2 (SMS), it should be very brief and conversational.
    - For the final email attempt, it should be a "last chance" message that offers value (e.g., a free consultation) and clearly states it's the last automated message.
    - If there is Knowledge Base info, incorporate it to be helpful.

    Return ONLY a JSON object with two keys: "subject" (for emails) and "body" (for the message content).
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful marketing assistant for a dental clinic. You will be given details and must return a JSON object with 'subject' and 'body' keys."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} # Use JSON mode for reliability
        )
        content_data = json.loads(response.choices[0].message.content)
        subject = content_data.get('subject', 'A quick follow-up from Bright Smile Clinic')
        body_plain = content_data.get('body', 'Just checking in!')

    except Exception as e:
        print(f"Error generating follow-up content with OpenAI: {e}. Using fallback.")
        subject = "A quick follow-up from Bright Smile Clinic"
        body_plain = f"Hi {lead.first_name}, just checking in on your recent inquiry about {lead.inquiry_notes}."

    # Populate the HTML template for the final email
    body_html = None
    if attempt_number >= 3: # Assuming attempt 3 or 4 is the final email
        context = {
            "first_name": lead.first_name,
            "summary": body_plain, # Use the generated body as the main content
            "kb_section": f'<div class="kb-section"><p>{kb_info}</p></div>' if kb_info else ""
        }
        body_html = load_and_populate_template('nurture_email.html', context)

    return {"subject": subject, "body_plain": body_plain, "body_html": body_html}


# --- The Main Nurture Job (Now much cleaner) ---

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
            
            # --- FUTURE KB HOOK ---
            # Here you would call your KB search function based on the lead's inquiry
            # kb_info = your_kb_search_function(lead.inquiry_notes)
            kb_info = None # Placeholder for now

            # --- Attempt 2: SMS (e.g., 2 days after initial contact) ---
            if lead.nurture_attempts == 1 and time_since_last_update > timedelta(days=2):
                content = generate_follow_up_content(lead, attempt_number=2, kb_info=kb_info)
                if send_sms(lead.phone_number, content['body_plain']):
                    lead.nurture_attempts += 1
                    crud.create_communication_log(db, schemas.CommunicationCreate(
                        lead_id=lead.id, type=CommTypeEnum.sms, direction=CommDirectionEnum.outgoing_auto, content=content['body_plain']
                    ))
                    db.commit()

            # --- Attempt 3: AI Phone Call (e.g., 4 days after initial contact) ---
            elif lead.nurture_attempts == 2 and time_since_last_update > timedelta(days=2): # 2 days after SMS
                if lead.phone_number:
                    call_data = voice_utils.make_tool_based_vapi_call(lead)
                    if call_data:
                        lead.nurture_attempts += 1
                        crud.create_communication_log(db, schemas.CommunicationCreate(
                            lead_id=lead.id, type=CommTypeEnum.phone_call, direction=CommDirectionEnum.outgoing_auto, content=f"AI call initiated. Vapi Call ID: {call_data.get('id')}"
                        ))
                        db.commit()
                else: # Fallback if no phone number
                    lead.nurture_attempts += 1
                    db.commit() # Increment attempt to move to the next step

            # --- Attempt 4: Final Email (e.g., 6 days after initial contact) ---
            elif lead.nurture_attempts == 3 and time_since_last_update > timedelta(days=2): # 2 days after call attempt
                content = generate_follow_up_content(lead, attempt_number=4, kb_info=kb_info)
                reply_domain = os.getenv("REPLY_DOMAIN")
                tracking_reply_to = f"replies+{str(lead.id)}@{reply_domain}"
                
                if send_email(lead.email, content['subject'], content['body_plain'], html_body=content['body_html'], reply_to_address=tracking_reply_to):
                    lead.nurture_attempts += 1
                    crud.create_communication_log(db, schemas.CommunicationCreate(
                        lead_id=lead.id, type=CommTypeEnum.email, direction=CommDirectionEnum.outgoing_auto, content=f"Subject: {content['subject']}\n\n{content['body_plain']}"
                    ))
                    db.commit()

            # --- Archive Lead (if all attempts are exhausted) ---
            elif lead.nurture_attempts >= 4:
                print(f"Archiving Lead ID: {lead.lead_id} after all attempts.")
                crud.update_lead_status(db, lead_id=lead.id, status=LeadStatusEnum.archived_no_response)

    finally:
        db.close()