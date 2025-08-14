from sqlalchemy import Column, String, Text, DateTime, Integer, Enum, func, UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from .database import Base
import enum
import uuid

# Replicating the ENUM types from our SQL schema
class LeadStatusEnum(str, enum.Enum):
    new = "new"
    needs_immediate_attention = "needs_immediate_attention"
    nurturing = "nurturing"
    responded = "responded"
    converted = "converted"
    archived_no_response = "archived_no_response"
    archived_not_interested = "archived_not_interested"

# SQLAlchemy model for the 'leads' table
class Lead(Base):
    __tablename__ = "leads"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), nullable=False)
    phone_number = Column(String(50))
    inquiry_notes = Column(Text)
    inquiry_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(LeadStatusEnum), nullable=False, default=LeadStatusEnum.new)
    nurture_attempts = Column(Integer, nullable=False, default=0)
    # --- NEW COLUMNS ---
    ai_summary = Column(Text, nullable=True)
    ai_drafted_reply = Column(Text, nullable=True)
    conversation_state = Column(String(50), default='pending_agent_action')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Note: The 'communications' table model is not needed yet, but will be added here later.

# Replicating the ENUM types for communications
class CommTypeEnum(str, enum.Enum):
    email = "email"
    sms = "sms"
    note = "note"
    phone_call = "phone_call" # Add this new type

class CommDirectionEnum(str, enum.Enum):
    outgoing_auto = "outgoing_auto"
    outgoing_manual = "outgoing_manual"
    incoming = "incoming"

# SQLAlchemy model for the 'communications' table
class Communication(Base):
    __tablename__ = "communications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(PG_UUID(as_uuid=True), nullable=False) # Note: We won't use a formal FK constraint in the model to keep background tasks simple
    type = Column(Enum(CommTypeEnum), nullable=False)
    direction = Column(Enum(CommDirectionEnum), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

# Replicating the ENUM type for slot status
class SlotStatusEnum(str, enum.Enum):
    available = "available"
    booked = "booked"
    cancelled = "cancelled"

# SQLAlchemy model for the 'appointment_slots' table
class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_time = Column(DateTime(timezone=True), nullable=False, unique=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(SlotStatusEnum), nullable=False, default=SlotStatusEnum.available)
    
    lead_id = Column(PG_UUID(as_uuid=True), nullable=True)
    reason_for_visit = Column(Text, nullable=True)
    booked_by_method = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Knowledge Base model for storing text content
class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    chunk_id = Column(String(255), nullable=True)  # Pinecone vector ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())