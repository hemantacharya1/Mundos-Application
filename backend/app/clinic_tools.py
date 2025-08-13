from datetime import datetime
from . import crud
from .database import SessionLocal
from .utils import send_email # Import the email utility
from .models import LeadStatusEnum
import platform

# This is a mock knowledge base. In a real app, this would come from a DB.
KNOWLEDGE_BASE = {
    "checkup": {"price": 75, "details": "A standard dental check-up and cleaning."},
    "whitening": {"price": 350, "details": "Our professional teeth whitening service."},
}

# This is a mock appointment system. In a real app, this would query your calendar/DB.
AVAILABLE_SLOTS = {
    "tuesday": ["10:00 AM", "2:00 PM", "4:00 PM"],
    "wednesday": ["9:00 AM", "11:00 AM"],
}

def get_plan_details(plan_name: str) -> str:
    """Gets the price and details for a specific dental plan."""
    plan_name = plan_name.lower()
    if plan_name in KNOWLEDGE_BASE:
        plan = KNOWLEDGE_BASE[plan_name]
        print(f"The {plan_name} service costs ${plan['price']} and includes: {plan['details']}.")
        return f"The {plan_name} service costs ${plan['price']} and includes: {plan['details']}."
    return "I'm sorry, I couldn't find details for that specific plan."

# def get_available_slots(day: str) -> str:
#     """Gets available appointment slots for a given day."""
#     day = day.lower()
#     if day in AVAILABLE_SLOTS:
#         slots = ", ".join(AVAILABLE_SLOTS[day])
#         return f"For {day}, we have the following slots available: {slots}."
#     return f"I'm sorry, I don't see any available slots for {day}."
def get_available_slots(day: str) -> str:
    """
    Gets REAL available appointment slots from the database for a given day.
    """
    print(f"TOOL: get_available_slots called with day='{day}'")
    db = SessionLocal()
    try:
        available_slots = crud.get_available_slots_by_natural_language_day(db, day_str=day)
        if not available_slots:
            return f"I'm sorry, I don't see any available slots for {day}."
        
        slot_times = []
        for slot in available_slots:
            if isinstance(slot.start_time, datetime):
                slot_times.append(slot.start_time.strftime("%I:%M %p"))
            elif slot.start_time:  # in case it's already a string
                slot_times.append(str(slot.start_time))

        return f"For {day}, we have the following times available: {', '.join(slot_times)}."
    finally:
        db.close()

def book_appointment(date: str, time: str, reason: str, lead_id: str) -> str:
    """
    Finds a specific available slot in the database, books it, updates the lead,
    and sends a confirmation email.
    """
    print(f"TOOL: book_appointment called with date='{date}', time='{time}', reason='{reason}'")
    db = SessionLocal()
    try:
        # 1. Find the specific slot the user wants to book
        slot_to_book = crud.find_available_slot_by_natural_language(db, day_str=date, time_str=time)

        if not slot_to_book:
            return "I'm sorry, that specific time slot seems to be unavailable. Could we try another time?"

        # 2. Book the slot
        booked_slot = crud.book_slot(
            db,
            slot=slot_to_book,
            lead_id=lead_id,
            reason=reason,
            method='vapi_ai'
        )
        
        # 3. CRITICAL: Update the lead's status to 'converted'
        lead = crud.get_lead_by_id(db, lead_id)
        if lead:
            crud.update_lead_status(db, lead_id=lead.id, status=LeadStatusEnum.converted)
            date_str = booked_slot.start_time.strftime("%A, %B %d, %Y")
            time_str = booked_slot.start_time.strftime("%I:%M %p").lstrip("0")  # ✅ Works everywhere
            # 4. CRITICAL: Send a confirmation email
            subject = "Your Appointment is Confirmed at Bright Smile Clinic!"
            body = (
                f"Hi {lead.first_name},\n\n"
                f"This is a confirmation for your upcoming appointment.\n\n"
                f"Service: {reason}\n"
                f"Date: {date_str}\n"
                f"Time: {time_str}\n\n"
                f"We look forward to seeing you!\n\n"
                f"Sincerely,\nThe Bright Smile Clinic Team"
            )
            send_email(to_email=lead.email, subject=subject, body=body)

        return f"Great! I have successfully booked your appointment for a {reason} on {date} at {time}. I've also sent a confirmation email with all the details."
    finally:
        db.close()