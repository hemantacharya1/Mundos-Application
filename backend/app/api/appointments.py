from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date, time, timedelta

from .. import crud, schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)

@router.post("/create-bulk-slots", status_code=201)
def create_bulk_slots(
    request: schemas.CreateBulkSlotsRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a range of available appointment slots for an admin.
    """
    slots_to_create = []
    try:
        start_dt = datetime.fromisoformat(request.start_date).date()
        end_dt = datetime.fromisoformat(request.end_date).date()
        start_t = time.fromisoformat(request.start_time_of_day)
        end_t = time.fromisoformat(request.end_time_of_day)
        duration = timedelta(minutes=request.slot_duration_minutes)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format.")

    current_date = start_dt
    while current_date <= end_dt:
        # Skip weekends
        if current_date.weekday() < 5: # Monday is 0, Sunday is 6
            current_time = datetime.combine(current_date, start_t)
            day_end_time = datetime.combine(current_date, end_t)
            
            while current_time < day_end_time:
                slot = models.AppointmentSlot(
                    start_time=current_time,
                    end_time=current_time + duration
                )
                slots_to_create.append(slot)
                current_time += duration
        current_date += timedelta(days=1)
    
    # This simple implementation doesn't check for existing duplicates.
    # A production system might need to be more careful.
    crud.create_appointment_slots(db, slots=slots_to_create)
    return {"status": "success", "message": f"{len(slots_to_create)} slots created."}

@router.get("", response_model=List[schemas.AppointmentSlot])
def get_all_slots_in_range(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """Gets all appointment slots for a given date range to display on a calendar."""
    return crud.get_appointment_slots_by_range(db, start_date=start_date, end_date=end_date)

@router.put("/{slot_id}/book", response_model=schemas.AppointmentSlot)
def book_an_appointment_slot(
    slot_id: str,
    request: schemas.BookSlotRequest,
    db: Session = Depends(get_db)
):
    """Books a specific, available appointment slot for a lead."""
    slot = crud.get_slot_by_id(db, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Appointment slot not found.")
    if slot.status != models.SlotStatusEnum.available:
        raise HTTPException(status_code=409, detail="Slot is no longer available.")
    
    # Also check if the lead exists
    lead = crud.get_lead_by_id(db, request.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    booked_slot = crud.book_slot(
        db,
        slot=slot,
        lead_id=request.lead_id,
        reason=request.reason_for_visit,
        method=request.booked_by_method
    )
    
    # Here you could also trigger a confirmation email to the lead
    
    return booked_slot