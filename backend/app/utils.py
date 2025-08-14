import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

from .knowledge_base import knowledge_base_service

def send_email(to_email: str, subject: str, body: str, reply_to_address: str | None = None):
    """Sends an email using SMTP credentials, with an optional custom Reply-To address."""
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv("SENDER_EMAIL")
        msg['To'] = to_email
        msg['Subject'] = subject

        # This is the critical part that enables our tracking
        if reply_to_address:
            msg.add_header('Reply-To', reply_to_address)

        msg.attach(MIMEText(body, 'plain'))

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