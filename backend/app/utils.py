import os
import requests
import openai
from typing import List,Literal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from . import crud, models
from .database import SessionLocal
import json

from .knowledge_base import knowledge_base_service


RISK_ANALYSIS_API_URL = os.getenv("RISK_ANALYSIS_API_URL", "https://49a9467a9cf6.ngrok-free.app/predict?threshold=0.5")
SUMMARIZER_MODEL = "gpt-4o-mini" # A fast and cost-effective model for summarization

# Instantiate the OpenAI client once at the module level for efficiency
client = openai.OpenAI()

def send_email(to_email: str, subject: str, body: str, reply_to_address: str | None = None,html_body: str | None = None):
    """Sends an email using SMTP credentials, with an optional custom Reply-To address."""
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv("SENDER_EMAIL")
        msg['To'] = to_email
        msg['Subject'] = subject

        # This is the critical part that enables our tracking
        if reply_to_address:
            msg.add_header('Reply-To', reply_to_address)

        # msg.attach(MIMEText(body, 'plain'))

        # *** THIS IS THE NEW PART ***
        # If HTML content is provided, attach it as well.
        # Email clients will prefer to render the HTML version.
        # if html_body:
        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")))
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
        text = msg.as_string()
        server.sendmail(os.getenv("SENDER_EMAIL"), to_email, text)
        server.quit()
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    
    
# --- FIXED send_sms function ---
def send_sms(to_number: str, body: str) -> bool:
    """
    Sends an SMS message using the Twilio client.
    """
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not account_sid or not auth_token or not from_number:
            print("Error: Twilio environment variables are not set.")
            return False

        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        print(f"SMS sent successfully to {to_number}. SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send SMS to {to_number}. Error: {e}")
        return False
    
def send_whatsapp(to_number: str, body: str) -> bool:
    """
    Sends an SMS message using the Twilio client.
    """
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")
        from_number = f"whatsapp:+14155238886"
        to_number = f"whatsapp:{to_number}"
       
        if not account_sid or not auth_token or not from_number:
            print("Error: Twilio environment variables are not set.")
            return False

        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        print(f"whatsapp message sent successfully to {to_number}. SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send whatsapp message to {to_number}. Error: {e}")
        return False


def knowledge_base_semantic_search(query: str, top_k: int = 5) -> list:
    """
    Perform semantic search on the knowledge base.
    
    Args:
        query (str): The search query
        top_k (int): Number of top results to return
        
    Returns:
        list: List of search results with content and metadata
    """
    try:
        results = knowledge_base_service.search_knowledge_base(query, top_k)
        return results
    except Exception as e:
        # Log the error but don't fail the application
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in knowledge base semantic search: {e}")
        return []
    

# --- Private Helper Function for Summarization ---
def _get_conversation_summaries(agent_messages: List[str], user_messages: List[str]) -> dict:
    """
    Uses an LLM to create concise summaries for both the user and agent,
    and returns them as a dictionary.
    """
    # Join messages with a clear separator for the LLM
    agent_messages_list = "\n---\n".join(agent_messages) if agent_messages else "No messages from agent yet."
    user_messages_list = "\n---\n".join(user_messages)

    # This prompt now includes the JSON requirement AND the stylistic examples
    prompt = f"""
    You are an expert conversation analyst. Your task is to create two concise, one-sentence, third-person summaries based on the provided conversation text.
    The summary style must be an exact match to the examples provided.

    ### User Summary Style Examples
    - Inquired about the cost of a routine dental cleaning, mentioned the $150 price was a bit steep at the moment.
    - Was curious about the price of a root canal treatment and stated they needed some time to think it over after hearing the quote.

    ### Agent Summary Style Examples
    - Provided detailed information on the cleaning service and its cost; the customer expressed some concerns about the price and decided not to book an appointment at this time.
    - Gave a comprehensive breakdown of the root canal costs, and the customer indicated they needed to consider their options before proceeding with scheduling.

    ### Conversation to Summarize
    User messages so far:
    ---
    {user_messages_list}
    ---
    Agent messages so far:
    ---
    {agent_messages_list}
    ---

    ### Your Output
    Return your response as a single, valid JSON object with two keys: "user_summary" and "agent_summary".
    """

    try:
        response = client.chat.completions.create(
            model=SUMMARIZER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, # Set to 0.0 for maximum consistency
            response_format={"type": "json_object"} # Enforce JSON output
        )
        # Parse the JSON string from the LLM's response
        summary_data = json.loads(response.choices[0].message.content.strip())
        return summary_data
    except Exception as e:
        print(f"Error during LLM summarization: {e}")
        # Return a default error object that the main function can check for
        return {"user_summary": "Error generating summary.", "agent_summary": "Error generating summary."}


# --- 2. UPDATED MAIN FUNCTION ---
def get_lead_conversion_probability(lead_id: str) -> int | None:
    """
    Analyzes a lead's conversation history to predict the probability of conversion.
    This version uses a single LLM call to generate both summaries.
    """
    print(f"--- Starting Conversion Probability Analysis for Lead ID: {lead_id} ---")
    db = SessionLocal()
    try:
        comms = crud.get_communications_by_lead_id(db, lead_id=lead_id)

        if not comms:
            print("No communications found for this lead. Cannot perform analysis.")
            return None

        customer_message = next((c.content for c in reversed(comms) if c.direction == models.CommDirectionEnum.incoming),None)
        agent_message = next((c.content for c in reversed(comms) if c.direction == models.CommDirectionEnum.outgoing_auto),None)
        
        if not customer_message:
            print("No customer messages found. Cannot perform analysis.")
            return None

        # --- KEY CHANGE: Call the summarizer ONCE to get both summaries ---
        print("Generating conversation summaries...")
        summaries = _get_conversation_summaries(agent_messages=agent_message, user_messages=customer_message)
        
        # Extract the summaries from the returned dictionary
        customer_summary = summaries.get("user_summary", "Summary not available.")
        agent_summary = summaries.get("agent_summary", "Summary not available.")
        
        print(f"Customer Summary: {customer_summary}")
        print(f"Agent Summary: {agent_summary}")

        # Check if summarization failed
        if "Error" in customer_summary:
            print("Aborting analysis due to summarization error.")
            return None

        # Prepare and send the request to your ML model's API
        payload = {
            "customer_summary": customer_summary,
            "agent_summary": agent_summary
        }
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        print(f"Sending summaries to risk analysis API: {RISK_ANALYSIS_API_URL}")
        response = requests.post(RISK_ANALYSIS_API_URL, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        conversion_probability = data.get("conversion_probability")
        print(dict(data))
        # if conversion_probability is not None:
        #     percentage = int(conversion_probability * 100)
        #     print(f"Analysis complete. Conversion probability: {percentage}%")
        #     return percentage
        # else:
        #     print("API response did not contain 'conversion_probability'.")
        return None

    except requests.RequestException as e:
        print(f"Error calling the risk analysis API: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during analysis for lead {lead_id}: {e}")
        return None
    finally:
        db.close()