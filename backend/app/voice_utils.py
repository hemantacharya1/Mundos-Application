import os
import requests
from .models import Lead
from .agents.prompt import REFINED_DENTAL_PROMPT

VAPI_API_URL = "https://api.vapi.ai/call/phone"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('VAPI_API_KEY')}",
    "Content-Type": "application/json",
}

def make_tool_based_vapi_call(lead: Lead):
    """
    Places a dynamic, tool-using call to a specific lead using the correct Vapi payload structure.
    """
    
    # Construct the full, secret URL for the tool handler webhook
    SERVER_BASE_URL = os.getenv("SERVER_BASE_URL")
    # SECRET_PATH = os.getenv("WEBHOOK_SECRET_PATH")
    
    # if not SERVER_BASE_URL or not SECRET_PATH:
    #     print("ERROR: SERVER_BASE_URL and WEBHOOK_SECRET_PATH must be set in .env")
    #     raise ValueError("Server URL or Webhook Secret Path not configured.")
        
    tool_handler_url = f"{SERVER_BASE_URL}/api/webhooks/vapi-tool-handler"

    # Define the tools with the server URL injected into each one
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_plan_details",
                "description": "Gets the price and details for a specific dental plan.",
                "parameters": {"type": "object", "properties": {"plan_name": {"type": "string"}}}
            },
            "server": {"url": tool_handler_url}
        },
        {
            "type": "function",
            "function": {
                "name": "get_available_slots",
                "description": "Gets available appointment slots for a given day.",
                "parameters": {"type": "object", "properties": {"day": {"type": "string"}}}
            },
            "server": {"url": tool_handler_url}
        },
        {
            "type": "function",
            "function": {
                "name": "book_appointment",
                "description": "Books an appointment for the user.",
                "parameters": {"type": "object", "properties": {"date": {"type": "string"}, "time": {"type": "string"}, "reason": {"type": "string"}}}
            },
            "server": {"url": tool_handler_url}
        }
    ]
    # 1. Prepare the contextual data with fallbacks for safety
    lead_name = lead.first_name or "the customer"
    # Provide a generic fallback if the inquiry notes are empty
    inquiry_notes = lead.inquiry_notes or "your dental health needs"

    # 2. Dynamically create the system prompt by replacing placeholders
    system_prompt = REFINED_DENTAL_PROMPT.replace("{LEAD_NAME}", lead_name)
    system_prompt = system_prompt.replace("{LEAD_INQUIRY_NOTES}", inquiry_notes)
    system_prompt = system_prompt.replace("{DATE}",str(lead.created_at))
    # Construct the final payload according to the new structure
    payload = {
        "phoneNumberId": os.getenv("VAPI_PHONE_NUMBER_ID"),
        "assistantId": os.getenv("VAPI_ASSISTANT_ID"),
        "customers": [
            {"number": lead.phone_number}
        ],
        "metadata": {
            "lead_id": str(lead.id)
        },
        "assistantOverrides": {
            "voice": {
                "provider": "vapi",
                "voiceId": "Neha"
            },
            "firstMessage": f"Hi, this is Neha from Bright smiles. Am I speaking with customer {lead.first_name}.",
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "systemPrompt": system_prompt,
                "tools": tools
            },
            "serverUrl":tool_handler_url
        }
    }

    try:
        print("Placing call with Vapi using updated payload structure...")
        response = requests.post(VAPI_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        print("Call placed successfully!")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error placing Vapi call: {http_err}")
        print("Response body:", response.text)
        return None
    except Exception as e:
        print(f"An other error occurred: {e}")
        return None