from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from .models import LeadStatusEnum,CommTypeEnum,CommDirectionEnum,SlotStatusEnum

# Base schema for a lead's properties
class LeadBase(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    phone_number: str | None = None
    inquiry_notes: str | None = None
    inquiry_date: datetime

# Schema for creating a lead (used internally)
class LeadCreate(LeadBase):
    pass

# Schema for reading a lead (what the API will return)
class Lead(LeadBase):
    id: UUID
    lead_id: str
    status: LeadStatusEnum
    nurture_attempts: int
     # --- NEW FIELDS ---
    ai_summary: str | None = None
    ai_drafted_reply: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # This allows Pydantic to read data from ORM models

# ... (keep the existing Lead schemas)
from .models import CommTypeEnum, CommDirectionEnum

# Schema for creating a communication log
class CommunicationCreate(BaseModel):
    lead_id: UUID
    type: CommTypeEnum
    direction: CommDirectionEnum
    content: str

class Communication(BaseModel):
    id: UUID
    type: CommTypeEnum
    direction: CommDirectionEnum
    content: str
    sent_at: datetime

    class Config:
        orm_mode = True # This allows Pydantic to read data directly from the SQLAlchemy model


# Base schema for an appointment slot's properties
class AppointmentSlotBase(BaseModel):
    start_time: datetime
    end_time: datetime

# Schema for viewing an appointment slot
class AppointmentSlot(AppointmentSlotBase):
    id: UUID
    status: SlotStatusEnum
    lead_id: UUID | None = None
    reason_for_visit: str | None = None
    booked_by_method: str | None = None

    class Config:
        orm_mode = True

# Schema for the bulk creation request body
class CreateBulkSlotsRequest(BaseModel):
    start_date: str # e.g., "2025-09-01"
    end_date: str   # e.g., "2025-09-05"
    start_time_of_day: str # e.g., "09:00"
    end_time_of_day: str   # e.g., "17:00"
    slot_duration_minutes: int

# Schema for the booking request body
class BookSlotRequest(BaseModel):
    lead_id: UUID
    reason_for_visit: str
    booked_by_method: str