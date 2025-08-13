import pandas as pd
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from .. import models, schemas, crud
from ..database import get_db
from datetime import datetime
from fastapi import BackgroundTasks # Add this import
from typing import List # Make sure this is imported from typing

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
    

@router.get("/", response_model=List[schemas.Lead])
def read_leads(status: schemas.LeadStatusEnum | None = None, db: Session = Depends(get_db)):
    """
    Retrieves a list of leads.
    Can be filtered by status (e.g., 'needs_immediate_attention', 'responded').
    """
    if status:
        leads = db.query(models.Lead).filter(models.Lead.status == status).order_by(models.Lead.created_at.desc()).all()
    else:
        leads = db.query(models.Lead).order_by(models.Lead.created_at.desc()).all()
    return leads

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
