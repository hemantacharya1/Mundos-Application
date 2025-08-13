from datetime import datetime

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

def get_available_slots(day: str) -> str:
    """Gets available appointment slots for a given day."""
    day = day.lower()
    if day in AVAILABLE_SLOTS:
        slots = ", ".join(AVAILABLE_SLOTS[day])
        return f"For {day}, we have the following slots available: {slots}."
    return f"I'm sorry, I don't see any available slots for {day}."

def book_appointment(date: str, time: str, reason: str) -> str:
    """Books an appointment for the user and confirms it."""
    print(f"--- SIMULATING APPOINTMENT BOOKING ---")
    print(f"Date: {date}, Time: {time}, Reason: {reason}")
    print(f"--- BOOKING CONFIRMED IN SYSTEM ---")
    return f"Great! I have successfully booked your appointment for a {reason} on {date} at {time}. You will receive a confirmation message shortly."