from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

def get_lead_by_email(db: Session, email: str):
    return db.query(models.Lead).filter(models.Lead.email == email).first()

def create_lead(db: Session, lead: schemas.LeadCreate):
    # Generate a unique, human-readable lead ID
    # This is a simple implementation; a more robust one might be needed for high concurrency
    last_lead_id = db.query(models.Lead.lead_id).order_by(models.Lead.created_at.desc()).first()
    if last_lead_id:
        last_num = int(last_lead_id[0].split('-')[-1])
        new_id_num = last_num + 1
    else:
        new_id_num = 1
    new_lead_id = f"BS-LID-{new_id_num:04d}"

    db_lead = models.Lead(
        **lead.dict(),
        lead_id=new_lead_id
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

# ... (keep existing get_lead_by_email and create_lead)
from .models import Communication, LeadStatusEnum
from uuid import UUID

def get_lead_by_id(db: Session, lead_id: UUID):
    return db.query(models.Lead).filter(models.Lead.id == lead_id).first()

def update_lead_status(db: Session, lead_id: UUID, status: LeadStatusEnum):
    db_lead = get_lead_by_id(db, lead_id)
    if db_lead:
        db_lead.status = status
        db.commit()
        db.refresh(db_lead)
        return db_lead
    return None

def create_communication_log(db: Session, comm: schemas.CommunicationCreate):
    db_comm = models.Communication(**comm.dict())
    db.add(db_comm)
    db.commit()
    db.refresh(db_comm)
    return db_comm