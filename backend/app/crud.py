from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from sqlalchemy import or_
from typing import List

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

def get_leads(db: Session, status: models.LeadStatusEnum | None, search: str | None, page: int, limit: int) -> List[models.Lead]:
    """Gets a paginated list of leads with optional filtering and searching."""
    query = db.query(models.Lead)

    if status:
        query = query.filter(models.Lead.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Lead.first_name.ilike(search_term),
                models.Lead.last_name.ilike(search_term),
                models.Lead.email.ilike(search_term)
            )
        )
    
    # Apply ordering and pagination
    query = query.order_by(models.Lead.created_at.desc())
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    return query.all()

def get_communications_by_lead_id(db: Session, lead_id: UUID) -> List[models.Communication]:
    """Gets all communication logs for a specific lead, sorted chronologically."""
    return db.query(models.Communication).filter(models.Communication.lead_id == lead_id).order_by(models.Communication.sent_at.asc()).all()