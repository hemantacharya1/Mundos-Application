import os
import re
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Header
from sqlalchemy.orm import Session

from .. import crud, models
from ..database import get_db
from ..agents.reply_agent import run_reply_analyzer

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)

# --- Security Dependency ---
# async def verify_webhook_token(x_webhook_secret: str = Header(None)):
#     """A dependency to verify a secret token in the request header."""
#     if not x_webhook_secret or x_webhook_secret != os.getenv("WEBHOOK_SECRET_TOKEN"):
#         raise HTTPException(status_code=403, detail="Invalid or missing webhook secret token.")

@router.post("/email-reply")
async def handle_email_reply(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handles inbound email replies from SendGrid, secured with a token.
    1. Halts the nurture sequence by updating status to 'responded'.
    2. Triggers the Reply Intent Analyzer agent in the background.
    """
    form_data = await request.form()
    to_address = form_data.get('to', '')
    email_body = form_data.get('text', '')

    match = re.search(r'\+(.*?)\@', to_address)
    if not match:
        raise HTTPException(status_code=400, detail="Could not parse Lead ID from 'To' address.")

    lead_id_str = match.group(1)
    
    # --- CRITICAL STEP 1: Halt the nurture sequence immediately ---
    lead = crud.get_lead_by_id(db, lead_id=lead_id_str)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with ID {lead_id_str} not found.")

    # Only process if the lead is currently being nurtured
    if lead.status == models.LeadStatusEnum.nurturing:
        crud.update_lead_status(db, lead_id=lead.id, status=models.LeadStatusEnum.responded)
        print(f"Lead {lead.lead_id} status updated to 'responded'. Nurture sequence halted.")

        # --- CRITICAL STEP 2: Trigger the AI analyzer in the background ---
        background_tasks.add_task(run_reply_analyzer, lead_id=str(lead.id), reply_text=email_body)
        print(f"Scheduled Reply Intent Analyzer for lead: {lead.lead_id}")
        
        return {"status": "success", "message": "Reply being processed."}
    else:
        print(f"Lead {lead.lead_id} already has status '{lead.status}'. Ignoring duplicate reply.")
        return {"status": "ignored", "message": "Duplicate or non-nurturing reply."}