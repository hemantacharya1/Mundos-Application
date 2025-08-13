from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from .models import LeadStatusEnum,CommTypeEnum,CommDirectionEnum

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