import os
import requests
from .models import Lead
from .agents.prompt import DENTAL_CLINIC_TOOL_PROMPT

VAPI_API_URL = "https://api.vapi.ai/call"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('VAPI_API_KEY')}",
    "Content-Type": "application/json"
}

            # This is the crucial part
SERVER_BASE_URL = os.getenv("SERVER_BASE_URL")
tool_handler_url=  f"{SERVER_BASE_URL}/api/webhooks/vapi-tool-handler"

def make_tool_based_vapi_call(lead: Lead):
    """Places a dynamic, tool-using call to a specific lead."""
    
    # The public URL of our server (from ngrok or production deployment)
    # This is where Vapi will send tool call and report requests.
    SECRET_PATH = os.getenv("WEBHOOK_SECRET_PATH")
    payload = {
        "phoneNumberId": os.getenv("VAPI_PHONE_NUMBER_ID"),
        "customers": [{"number": lead.phone_number}],
        "assistantId": os.getenv("VAPI_ASSISTANT_ID"),
        "metadata": {
            "lead_id": str(lead.id) # Pass our internal lead ID
        },
        "assistantOverrides": {
            "voice":{
                "provider":"vapi",
                "voiceId":"Neha"
            },
            "firstMessage": f"Hi, this is Nancy from Bright smiles. Am I speaking with customer {lead.first_name}.",
            "model": {
                "provider": "openai", # Vapi recommends OpenAI for tool use
                "model": "gpt-4o",
                "systemPrompt": DENTAL_CLINIC_TOOL_PROMPT
            },
            "tools": [
                {"type": "function", "function": {"name": "get_plan_details", "description": "Gets the price and details for a specific dental plan.", "parameters": {"type": "object", "properties": {"plan_name": {"type": "string"}}}, "server": {"url": tool_handler_url}}},
                {"type": "function", "function": {"name": "get_available_slots", "description": "Gets available appointment slots for a given day.", "parameters": {"type": "object", "properties": {"day": {"type": "string"}}},"server": {"url": tool_handler_url}}},
                {"type": "function", "function": {"name": "book_appointment", "description": "Books an appointment for the user.", "parameters": {"type": "object", "properties": {"date": {"type": "string"}, "time": {"type": "string"}, "reason": {"type": "string"}}},"server": {"url": tool_handler_url}}},
            ],
        }
    }

    try:
        response = requests.post(VAPI_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error placing Vapi call: {e}")
        return None