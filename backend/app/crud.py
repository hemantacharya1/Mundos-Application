from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime,date, time, timedelta
from sqlalchemy import or_, and_, func
from typing import List
from dateutil.parser import parse as date_parse # A powerful date parsing library
from sqlalchemy.exc import NoResultFound

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


# --- NEW APPOINTMENT CRUD FUNCTIONS ---

def create_appointment_slots(db: Session, slots: List[models.AppointmentSlot]):
    """Bulk inserts a list of appointment slot objects."""
    # Use bulk_save_objects for efficiency, but it doesn't return the created objects with IDs.
    # For this use case, that's acceptable.
    db.bulk_save_objects(slots)
    db.commit()

def get_appointment_slots_by_range(db: Session, start_date: date, end_date: date) -> List[models.AppointmentSlot]:
    """Gets all appointment slots within a given date range."""
    return db.query(models.AppointmentSlot).filter(
        and_(
            func.date(models.AppointmentSlot.start_time) >= start_date,
            func.date(models.AppointmentSlot.start_time) <= end_date
        )
    ).order_by(models.AppointmentSlot.start_time.asc()).all()

def get_slot_by_id(db: Session, slot_id: UUID) -> models.AppointmentSlot | None:
    """Gets a single slot by its UUID."""
    return db.query(models.AppointmentSlot).filter(models.AppointmentSlot.id == slot_id).first()

def book_slot(db: Session, slot: models.AppointmentSlot, lead_id: UUID, reason: str, method: str) -> models.AppointmentSlot:
    """Updates a slot to 'booked' status and links it to a lead."""
    slot.status = models.SlotStatusEnum.booked
    slot.lead_id = lead_id
    slot.reason_for_visit = reason
    slot.booked_by_method = method
    db.commit()
    db.refresh(slot)
    return slot


def find_available_slot_by_natural_language(db: Session, day_str: str, time_str: str) -> models.AppointmentSlot | None:
    """
    Finds a single available slot that matches a natural language date and time.
    e.g., day_str="tomorrow", time_str="around 2pm"
    """
    try:
        print("ahiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",day_str,time_str)
        # Use dateutil.parser to convert natural language to a datetime object
        target_datetime = date_parse(f"{day_str} {time_str}")
        print("hhhhhhhhhhhhh",target_datetime)
        
        # Find a slot where the target time falls between the slot's start and end time
        slot = db.query(models.AppointmentSlot).filter(
            models.AppointmentSlot.status == models.SlotStatusEnum.available,
            models.AppointmentSlot.start_time <= target_datetime,
            models.AppointmentSlot.end_time > target_datetime
        ).first()
        print(slot)
        return slot
    except (ValueError, NoResultFound):
        # Handle cases where the date/time string is not parseable
        print("errrrrrrror")
        return None
    
def get_available_slots_by_natural_language_day(db: Session, day_str: str) -> List[models.AppointmentSlot]:
    """
    Finds all available slots on a given natural language day.
    e.g., day_str="tuesday" or day_str="tomorrow"
    """
    try:
        target_date = date_parse(day_str).date()
        print('111111111111111111111111',day_str,'111111111111111111111',target_date)
        # Find all available slots on that specific date
        return db.query(models.AppointmentSlot).filter(
            func.date(models.AppointmentSlot.start_time) == target_date,
            models.AppointmentSlot.status == models.SlotStatusEnum.available
        ).order_by(models.AppointmentSlot.start_time.asc()).all()
    except (ValueError, NoResultFound):
        print('22222222222222222222222222222','errrrrrr')
        return []
