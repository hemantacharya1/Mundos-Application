from sqlalchemy.orm import Session
from datetime import datetime,timezone,timedelta

from .. import crud, models, schemas,voice_utils
from ..database import SessionLocal
from ..utils import send_email,send_sms
from ..models import LeadStatusEnum, CommTypeEnum, CommDirectionEnum


# --- The Main Nurture Job ---

def nurture_and_recall_job():
    """
    This job runs periodically to follow up with leads in the 'nurturing' state.
    """
    print(f"--- Running Nurture & Recall Job at {datetime.now()} ---")
    db: Session = SessionLocal()
    try:
        # 1. Fetch all leads that are currently being nurtured
        nurturing_leads = db.query(models.Lead).filter(
            models.Lead.status == LeadStatusEnum.nurturing
        ).all()

        print(f"Found {len(nurturing_leads)} leads to process.")

        for lead in nurturing_leads:
            now = datetime.now(tz=lead.updated_at.tzinfo) 
            time_since_last_update = now - lead.updated_at

            # --- Attempt 1: Email (immediately after being set to 'nurturing') ---
            # This is handled by the Triage Agent, so nurture_attempts will be 0 initially.
            # The agent sends the first email and we will update the attempts there.
            # Let's adjust the Triage Agent to set the attempt count.
            # --- Attempt 2: SMS (2 days after last attempt) ---
            if lead.nurture_attempts == 1 and time_since_last_update > timedelta(seconds=30):
                print(f"Processing Attempt 2 (SMS) for Lead ID: {lead.lead_id}")
                body = f"Hi {lead.first_name}, it's the team from Bright Smile Clinic. Just checking in to see if you had any questions. You can reply to this message or call us."
                
                # if send_sms(lead.phone_number, body):
                #     lead.nurture_attempts += 1
                #     crud.create_communication_log(db, schemas.CommunicationCreate(
                #         lead_id=lead.id,
                #         type=CommTypeEnum.sms,
                #         direction=CommDirectionEnum.outgoing_auto,
                #         content=body
                #     ))
                #     db.commit()
            # --- Attempt 3: AI Phone Call (3 days after last attempt) ---
            elif lead.nurture_attempts == 2 and time_since_last_update > timedelta(days=3):
                print(f"Processing Attempt 3 (AI Phone Call) for Lead ID: {lead.lead_id}")
                
                if lead.phone_number:
                    call_data = voice_utils.make_tool_based_vapi_call(lead)
                    if call_data:
                        lead.nurture_attempts += 1
                        # Log the initiation of the call
                        crud.create_communication_log(db, schemas.CommunicationCreate(
                            lead_id=lead.id,
                            type=models.CommTypeEnum.phone_call,
                            direction=models.CommDirectionEnum.outgoing_auto,
                            content=f"AI call initiated. Vapi Call ID: {call_data.get('id')}"
                        ))
                        db.commit()
            # --- Attempt 3: Final Email (4 days after last attempt) ---
            elif lead.nurture_attempts == 3 and time_since_last_update > timedelta(minutes=1):
                print(f"Processing Attempt 4 (Final Email) for Lead ID: {lead.lead_id}")
                subject = "A quick question from Bright Smile Clinic"
                body = f"Hi {lead.first_name},\n\nWe haven't heard back and wanted to make one last reach-out. We're currently offering a complimentary consultation for new patients if you're still interested.\n\nThis will be our last automated message. We wish you the best!\n\nSincerely,\nThe Bright Smile Clinic Team"
                
                if send_email(lead.email, subject, body):
                    lead.nurture_attempts += 1
                    crud.create_communication_log(db, schemas.CommunicationCreate(
                        lead_id=lead.id,
                        type=CommTypeEnum.email,
                        direction=CommDirectionEnum.outgoing_auto,
                        content=f"Subject: {subject}\n\n{body}"
                    ))
                    db.commit()

            # --- Archive Lead (if all attempts are exhausted) ---
            elif lead.nurture_attempts >= 3:
                print(f"Archiving Lead ID: {lead.lead_id} after 3 attempts.")
                crud.update_lead_status(db, lead_id=lead.id, status=LeadStatusEnum.archived_no_response)

    finally:
        db.close()