import pandas as pd
import io
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi import Query, Body # Add these imports
from ..agents.triage_agent import run_triage_agent # Ensure this is imported
from ..utils import send_email,get_lead_conversion_probability # Ensure this is imported
from sqlalchemy.orm import Session
from .. import models, schemas, crud,voice_utils
from ..database import get_db
from datetime import datetime
from fastapi import BackgroundTasks # Add this import
from typing import List # Make sure this is imported from typing
from ..agents.triage_agent import load_and_populate_template

router = APIRouter(
    prefix="/leads",
    tags=["Leads"]
)

@router.post("/upload", response_model=list[schemas.Lead])
def upload_leads_csv(
    background_tasks: BackgroundTasks, # Add this dependency
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """
    Uploads a CSV file with lead data, creates new leads in the database,
    and triggers the AI Triage Agent for each new lead.
    """
    # ... (keep the file validation logic)
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    try:
        # ... (keep the pandas DataFrame logic)
        # Read the file content into a pandas DataFrame
        content = file.file.read()
        df = pd.read_csv(
        io.StringIO(content.decode('utf-8')),
        dtype={'PhoneNumber': str} # This is the key change
        )
        # Basic validation for required columns
        required_columns = ['Email', 'InquiryDate']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"Missing required columns: {required_columns}")
        
        created_leads = []
        for _, row in df.iterrows():
            existing_lead = crud.get_lead_by_email(db, email=row['Email'])
            if existing_lead:
                continue

            lead_data = schemas.LeadCreate(
                first_name=row.get('FirstName'),
                last_name=row.get('LastName'),
                email=row['Email'],
                phone_number=row.get('PhoneNumber'),
                inquiry_notes=row.get('InquiryNotes'),
                inquiry_date=pd.to_datetime(row['InquiryDate'])
            )
            new_lead = crud.create_lead(db=db, lead=lead_data)
            created_leads.append(new_lead)

            # *** THIS IS THE NEW, CRITICAL PART ***
            # Add the agent task to the background
            from ..agents.triage_agent import run_triage_agent
            background_tasks.add_task(run_triage_agent, lead_id=new_lead.id)
            print(f"Scheduled AI Triage for lead: {new_lead.lead_id}")

        return created_leads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the file: {e}")
    

@router.put("/{lead_id}/status", response_model=schemas.Lead)
def update_lead_status_endpoint(
    lead_id: str,
    status_update: schemas.LeadStatusEnum,
    db: Session = Depends(get_db)
):
    """
    Updates the status of a specific lead.
    """
    db_lead = crud.get_lead_by_id(db, lead_id)
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    updated_lead = crud.update_lead_status(db, lead_id=lead_id, status=status_update)
    return updated_lead

# --- NEW ENDPOINTS ---

@router.post("", response_model=schemas.Lead)
def create_single_lead(
    lead_data: schemas.LeadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Creates a single lead from a form/JSON input."""
    existing_lead = crud.get_lead_by_email(db, email=lead_data.email)
    if existing_lead:
        raise HTTPException(status_code=409, detail="A lead with this email already exists.")
    
    new_lead = crud.create_lead(db=db, lead=lead_data)
    
    background_tasks.add_task(run_triage_agent, lead_id=new_lead.id)
    print(f"Scheduled AI Triage for manually created lead: {new_lead.lead_id}")
    
    return new_lead

@router.get("", response_model=List[schemas.Lead])
def get_all_leads(
    status: models.LeadStatusEnum | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Gets a paginated and filterable list of all leads."""
    leads = crud.get_leads(db, status=status, search=search, page=page, limit=limit)
    return leads

@router.get("/{lead_id}", response_model=schemas.Lead)
def get_single_lead(lead_id: str, db: Session = Depends(get_db)):
    """Gets a single lead by UUID."""
    lead = crud.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.get("/{lead_id}/communications", response_model=List[schemas.Communication]) # Assuming you create a Communication schema
def get_lead_communications(lead_id: str, db: Session = Depends(get_db)):
    """Gets the full communication history for a single lead."""
    # First, ensure the lead exists
    lead = crud.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return crud.get_communications_by_lead_id(db, lead_id=lead_id)

@router.post("/{lead_id}/notes")
def add_manual_note(
    lead_id: str,
    content: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Adds a manual, internal note to a lead's history."""
    lead = crud.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    comm_log = schemas.CommunicationCreate(
        lead_id=lead.id,
        type=models.CommTypeEnum.note,
        direction=models.CommDirectionEnum.outgoing_manual,
        content=content
    )
    crud.create_communication_log(db, comm=comm_log)
    return {"status": "success", "message": "Note added successfully."}

@router.post("/{lead_id}/reply")
def send_manual_reply(
    lead_id: str,
    content: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Sends a manual email reply from the UI to a lead."""
    lead = crud.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    print(lead.first_name)
    # Construct the tracking reply-to address
    reply_domain = os.getenv("REPLY_DOMAIN")
    tracking_reply_to = f"replies+{lead.id}@{reply_domain}"
    subject = f"Re: Your inquiry with Bright Smile Clinic"

    context = {
        'first_name': lead.first_name,
        'personalized_content': f'<p>{content}</p>'
    }

    html_content = load_and_populate_template('nurture_email.html', context)
    # Send the email
    success = send_email(
        to_email=lead.email,
        subject=subject,
        body="",
        html_body=html_content,
        reply_to_address=tracking_reply_to
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email via SMTP service.")

    # Log the manual reply
    comm_log = schemas.CommunicationCreate(
        lead_id=lead.id,
        type=models.CommTypeEnum.email,
        direction=models.CommDirectionEnum.outgoing_manual,
        content=f"Subject: {subject}\n\n{content}"
    )
    crud.create_communication_log(db, comm=comm_log)
    
    return {"status": "success", "message": "Reply sent successfully."}


@router.post("/{lead_id}/test-ai-call", tags=["Testing"])
def test_tool_based_ai_call(lead_id: str, db: Session = Depends(get_db)):
    """
    [FOR TESTING ONLY] Initiates a full, tool-based AI voice call to a lead.
    This allows for manual testing without waiting for the nurture scheduler.
    """
    print(f"--- INITIATING TEST CALL for Lead ID: {lead_id} ---")
    lead = crud.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.phone_number:
        raise HTTPException(status_code=400, detail="Lead does not have a phone number.")

    # Use the tool-based call function we designed
    call_data = voice_utils.make_tool_based_vapi_call(lead)

    if not call_data:
        raise HTTPException(status_code=500, detail="Failed to initiate call via Vapi.")

    vapi_call_id=call_data.get('results')[0].get('id')
    # Log the initiation of the call
    comm_log = schemas.CommunicationCreate(
        lead_id=lead.id,
        type=models.CommTypeEnum.phone_call,
        direction=models.CommDirectionEnum.outgoing_auto,
        content=f"[TEST] AI call initiated. Vapi Call ID: {vapi_call_id}"
    )
    crud.create_communication_log(db, comm=comm_log)

    return {"status": "success", "message": "Test AI call initiated.", "vapi_call_id":vapi_call_id}

@router.get("/{lead_id}/risk-analysis", response_model=schemas.RiskAnalysisResponse)
def get_risk_analysis(lead_id: str, db: Session = Depends(get_db)):
    """
    Performs a risk analysis on a lead's conversation history to predict
    their interest level and probability of conversion.
    """
    lead = crud.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    print('*'*200)
    # Call the corrected main analysis function from utils.py
    prediction_data = get_lead_conversion_probability(lead_id=lead_id)
    print(prediction_data)
    if not prediction_data:
        raise HTTPException(status_code=500, detail="Failed to perform risk analysis. Check server logs for details.")

    try:
        # Extract the required information from the ML model's response
        predicted_label = prediction_data["predicted_label"]
        predicted_prob = prediction_data["predicted_prob"]
        
        # Format the response into the clean structure our frontend expects
        response_data = {
            "predicted_label": predicted_label,
            "probability_percent": round(predicted_prob * 100, 2)
        }
        return response_data
    except KeyError as e:
        print(f"ML model response was missing an expected key: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed due to unexpected data format from the ML model.")