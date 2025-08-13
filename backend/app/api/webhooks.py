import os
import re
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Header
from sqlalchemy.orm import Session

from .. import crud, models,clinic_tools,schemas
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
    

@router.post("/vapi-tool-handler")
async def handle_vapi_tool_calls(request: Request, db: Session = Depends(get_db)):
    """
    This single endpoint handles all messages from Vapi during a call.
    It executes tools and receives the final call report.
    """
    payload = await request.json()
    
    # Safely get the message type using .get() to avoid KeyError
    message = payload.get('message', {})
    message_type = message.get('type')
    print(message_type)
    if message_type == 'tool-calls':
        print(message)
        tool_call = message['tool_call']
        tool_name = tool_call['name']
        parameters = tool_call['parameters']
        
        print(f"Received tool call: {tool_name} with params: {parameters}")
        
        result = None
        if tool_name == 'get_plan_details':
            result = clinic_tools.get_plan_details(**parameters)
        elif tool_name == 'get_available_slots':
            result = clinic_tools.get_available_slots(**parameters)
        elif tool_name == 'book_appointment':
            result = clinic_tools.book_appointment(**parameters)
            # If booking is successful, update the lead's status
            lead_id = payload['call']['metadata']['lead_id']
            crud.update_lead_status(db, lead_id=lead_id, status=models.LeadStatusEnum.converted)

        return {"result": result}

    elif message_type == 'end-of-call-report':
        # Correctly access the 'report' key which is a direct child of 'message'
        report_data = message.get('report', {})
        
        call_data = payload.get('call', {})
        metadata = call_data.get('metadata', {})
        lead_id = metadata.get('lead_id')
        
        if lead_id:
            summary = f"Call Summary: {report_data.get('summary', 'N/A')}\n\nTranscript:\n{report_data.get('transcript', 'N/A')}"
            
            # Log the entire summary and transcript
            comm_log = schemas.CommunicationCreate(
                lead_id=lead_id,
                type=models.CommTypeEnum.phone_call,
                direction=models.CommDirectionEnum.incoming, # It's a report about the call
                content=summary
            )
            crud.create_communication_log(db, comm=comm_log)
            print(f"Saved call report for lead {lead_id}")
        
        return {"status": "report received"}

    return {"status": "message received"}