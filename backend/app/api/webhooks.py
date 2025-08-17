import os
import re
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Header
from sqlalchemy.orm import Session

from .. import crud, models,clinic_tools,schemas
from ..database import get_db
from ..agents.reply_agent import run_reply_analyzer
from ..models import CommTypeEnum,CommDirectionEnum

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
    subject = form_data.get('subject','')
    reply_only = re.split(r"On .*wrote:", email_body, flags=re.DOTALL)[0]
    reply_only = "\n".join(
        line for line in reply_only.splitlines()
        if not line.strip().startswith(">")
    ).strip()
    reply_only = f'User reply: {reply_only}'

    match = re.search(r'\+(.*?)\@', to_address)
    if not match:
        raise HTTPException(status_code=400, detail="Could not parse Lead ID from 'To' address.")

    lead_id_str = match.group(1)
    
    # --- CRITICAL STEP 1: Halt the nurture sequence immediately ---
    lead = crud.get_lead_by_id(db, lead_id=lead_id_str)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with ID {lead_id_str} not found.")

    crud.create_communication_log(db, schemas.CommunicationCreate(
            lead_id=lead.id,
            type=CommTypeEnum.email,
            direction=CommDirectionEnum.incoming,
            content=reply_only
        ))

    # Only process if the lead is currently being nurtured
    if lead.status == models.LeadStatusEnum.nurturing:
        crud.update_lead_status(db, lead_id=lead.id, status=models.LeadStatusEnum.responded)

        # --- CRITICAL STEP 2: Trigger the AI analyzer in the background ---
    background_tasks.add_task(run_reply_analyzer, lead_id=str(lead.id))
    print(f"Scheduled Reply Intent Analyzer for lead: {lead.lead_id}")   
    
    print("status: success", "message: Reply being processed by autonomous agent.")
    return {"status": "success", "message": "Reply being processed by autonomous agent."}
    

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

    if message_type == 'tool-calls':
        toolCalls = message.get("toolCalls", [])
        
        # Handle multiple tool calls if present
        results = []
        for tool_call in toolCalls:
            # Extract tool information from the nested structure
            function_info = tool_call.get('function', {})
            tool_name = function_info.get('name')
            
            # Parse arguments - they come as a JSON string
            import json
            arguments_str = function_info.get('arguments', '{}')
            if isinstance(arguments_str, str):
                try:
                    parameters = json.loads(arguments_str)
                except json.JSONDecodeError:
                    print(f"Failed to parse arguments: {arguments_str}")
                    parameters = {}
            else:
                parameters = arguments_str
            
            # --- THIS IS THE NEW PART ---
            # Get the lead_id from the call's metadata to pass to the tool
            lead_id = message.get('call', {}).get('metadata', {}).get('lead_id')

            print(f"Received tool call: {tool_name} with params: {parameters}")

            result = None
            if tool_name == 'get_knowledge':
                result = clinic_tools.get_plan_details(**parameters)
            elif tool_name == 'get_available_slots':
                result = clinic_tools.get_available_slots(**parameters)
            elif tool_name == 'book_appointment':
                if not lead_id:
                    result = "I'm sorry, I seem to have a technical issue and can't access your file to book the appointment. Please call our office directly."
                else:
                    # Pass the lead_id to the booking function
                    result = clinic_tools.book_appointment(**parameters, lead_id=lead_id)
    
            # Store result with tool call ID for proper mapping
            results.append({
                "toolCallId": tool_call.get('id'),
                "result": result
            })
        
        # Return results - VAPI expects this format for multiple tool calls
        print(results)
        return {"results": results}

    elif message_type == 'end-of-call-report':
        # Correctly access the 'report' key which is a direct child of 'message'\
        analysis = message.get('analysis', {})
        summary = analysis.get('summary')
        call_data=message.get('call')
        metadata=call_data.get('metadata')
        lead_id=metadata.get('lead_id')
        if lead_id:
            summary = f"Call Summary: {summary}"
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