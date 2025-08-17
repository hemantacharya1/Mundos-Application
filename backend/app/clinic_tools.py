from datetime import datetime
from . import crud
from .database import SessionLocal
from .utils import send_email, knowledge_base_semantic_search # Import the email utility
from .models import LeadStatusEnum
import platform
from .agents.triage_agent import load_and_populate_template
import os
import openai


client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-mini" # Use the new model

def get_plan_details(query: str) -> str:
    """
    Performs a semantic search and then uses an LLM to generate a
    voice-friendly summary of the results.
    """
    print(f"TOOL: get_plan_details called with query='{query}'")
    
    # Step 1: RETRIEVAL - Get the raw data from the vector DB
    # We might want to get a bit more context (top_k=3) for the LLM to have more to work with.
    raw_results = knowledge_base_semantic_search(query, top_k=3)

    if not raw_results:
        return "I'm sorry, I couldn't find any specific information on that topic."

    # Step 2: GENERATION - Use our new function to create a conversational summary
    conversational_summary = create_voice_friendly_summary(query, raw_results)
    
    print(f"Generated conversational summary: '{conversational_summary}'")
    
    return conversational_summary

def create_voice_friendly_summary(query: str, search_results: list) -> str:
    """
    Uses an LLM to synthesize raw KB search results into a concise,
    conversational response suitable for a voice AI.
    """
    if not search_results:
        return "I'm sorry, I couldn't find any specific information on that topic in our knowledge base."

    # Combine the content of the search results into a single context string
    context_string = "\n\n---\n\n".join([res['content'] for res in search_results])

    # This is the crucial prompt that does the summarization
    prompt = f"""
    You are an AI assistant whose job is to summarize information for a voice agent on a live phone call.
    A user has asked a question related to: "{query}"
    We have retrieved the following relevant information from our knowledge base.

    **Retrieved Information:**
    ---
    {context_string}
    ---

    **Your Task:**
    Synthesize this information into a brief, clear, and conversational response that the voice agent can say directly to the user.
    - Keep the response concise and easy to understand over the phone (ideally under 40 words).
    - Directly address the user's likely question based on the retrieved info.
    - If you see a price and a special offer, combine them into a helpful statement.
    - Do NOT just list facts. Create a natural-sounding sentence.

    Example: If the user asked about "teeth whitening cost" and the info contains a price range and a special offer, a perfect response would be:
    "Our professional in-office teeth whitening normally ranges from $500 to $800, but we're currently running a special for just $299."

    Provide only the final, speakable text for the voice agent to say. Do not add any conversational filler like "Sure, I can help with that."
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing KB results: {e}")
        # Fallback to a simpler, safer response if the LLM fails
        return "I found some information on that topic. Our patient coordinator can provide you with the specific details."

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
            context = {
            "first_name": lead.first_name,
            "personalized_content": f"<p> Great! I have successfully booked your appointment for a <strong>{reason}</strong> on <strong>{date}</strong> at <strong>{time}</strong>. </p>"
            }
            html_body = load_and_populate_template('nurture_email.html', context)
            reply_domain = os.getenv("REPLY_DOMAIN")
            tracking_reply_to = f"replies+{lead.id}@{reply_domain}"
            send_email(
                to_email=lead.email,
                subject=subject,
                body="",
                html_body=html_body,
                reply_to_address=tracking_reply_to
            )

        return f"Great! I have successfully booked your appointment for a {reason} on {date} at {time}. I've also sent a confirmation email with all the details."
    finally:
        db.close()