import os
import json
from typing import TypedDict, Literal
import google.generativeai as genai
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from .. import crud
from ..database import SessionLocal
from ..models import LeadStatusEnum

# --- Pydantic Models for Structured LLM Output ---
class IntentResult(BaseModel):
    intent: Literal['Positive_Interest', 'Question', 'Objection', 'Unsubscribe', 'General_Chatter']
    summary: str

class DraftedReply(BaseModel):
    reply_text: str

# --- LangGraph State Definition ---
class ReplyGraphState(TypedDict):
    lead_id: str
    reply_text: str
    intent: str | None = None
    summary: str | None = None
    drafted_reply: str | None = None

# --- Configure Gemini API ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="You are an expert AI assistant for a dental clinic. Your job is to analyze patient email replies and help the staff respond efficiently."
)

# --- Agent Nodes ---

def classify_intent_node(state: ReplyGraphState):
    """Analyzes the user's reply to classify its intent."""
    print(f"--- CLASSIFY INTENT for Lead ID: {state['lead_id']} ---")
    prompt = f"""
    Analyze the following patient reply and classify its intent into ONE of the following categories:
    ['Positive_Interest', 'Question', 'Objection', 'Unsubscribe', 'General_Chatter']
    Also, provide a one-sentence summary of their message.

    Patient Reply: "{state['reply_text']}"

    Respond ONLY with a valid JSON object with two keys: "intent" and "summary".
    Example: {{"intent": "Question", "summary": "The user is asking about insurance coverage."}}
    """
    response = model.generate_content(prompt)
    
    try:
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        result_json = json.loads(cleaned_response)
        intent_data = IntentResult(**result_json)
        state['intent'] = intent_data.intent
        state['summary'] = intent_data.summary
    except Exception as e:
        print(f"Error parsing intent classification: {e}. Defaulting to General_Chatter.")
        state['intent'] = 'General_Chatter'
        state['summary'] = 'Could not automatically determine intent.'
        
    return state

def ai_assisted_reply_node(state: ReplyGraphState):
    """If the user asked a question, this node drafts a suggested reply."""
    print(f"--- DRAFTING AI REPLY for Lead ID: {state['lead_id']} ---")
    prompt = f"""
    A patient has asked a question summarized as: "{state['summary']}".
    Their original message was: "{state['reply_text']}".

    Draft a helpful, friendly, and professional reply.
    - If you can answer confidently, do so.
    - If the question is about pricing, insurance, or appointments, state that our patient coordinator will follow up with specifics.
    - Keep the tone warm and reassuring.

    Respond ONLY with a valid JSON object with one key: "reply_text".
    Example: {{"reply_text": "Thanks for asking! Our patient coordinator will get back to you shortly with details about your insurance coverage."}}
    """
    response = model.generate_content(prompt)
    try:
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        result_json = json.loads(cleaned_response)
        reply_data = DraftedReply(**result_json)
        state['drafted_reply'] = reply_data.reply_text
    except Exception as e:
        print(f"Error drafting AI reply: {e}")
        state['drafted_reply'] = "AI could not draft a reply. Please respond manually."
        
    return state

def final_action_node(state: ReplyGraphState):
    """Performs the final database updates based on the graph's path."""
    print(f"--- FINAL ACTION for Lead ID: {state['lead_id']} ---")
    db = SessionLocal()
    try:
        lead = crud.get_lead_by_id(db, state['lead_id'])
        if not lead:
            return

        # Always save the summary
        lead.ai_summary = state['summary']

        # Handle different intents
        if state['intent'] == 'Unsubscribe' or state['intent'] == 'General_Chatter':
            lead.status = LeadStatusEnum.archived_not_interested
            print(f"Archiving lead {lead.lead_id} due to intent: {state['intent']}")
        
        elif state['intent'] == 'Question':
            lead.ai_drafted_reply = state['drafted_reply']
            print(f"Saved drafted reply for lead {lead.lead_id}")

        # For Positive_Interest and Objection, we just save the summary.
        # The status is already 'responded', correctly placing it in the human queue.
        
        db.commit()
    finally:
        db.close()
    return state

# --- Conditional Router ---
def router(state: ReplyGraphState) -> Literal["ai_assisted_reply_node", "final_action_node"]:
    """Routes to the appropriate node based on the classified intent."""
    intent = state['intent']
    if intent == 'Question':
        return "ai_assisted_reply_node"
    else: # For all other intents, we go straight to the final action.
        return "final_action_node"

# --- Build the Graph ---
workflow = StateGraph(ReplyGraphState)
workflow.add_node("classify_intent_node", classify_intent_node)
workflow.add_node("ai_assisted_reply_node", ai_assisted_reply_node)
workflow.add_node("final_action_node", final_action_node)

workflow.set_entry_point("classify_intent_node")
workflow.add_conditional_edges("classify_intent_node", router)
workflow.add_edge("ai_assisted_reply_node", "final_action_node")
workflow.add_edge("final_action_node", END)

reply_app_graph = workflow.compile()

# --- Main function to run the agent ---
def run_reply_analyzer(lead_id: str, reply_text: str):
    initial_state = ReplyGraphState(
        lead_id=lead_id,
        reply_text=reply_text
    )
    reply_app_graph.invoke(initial_state)