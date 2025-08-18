# Mundos: AI-Powered Patient Lead Recovery Platform


**Mundos is an autonomous, multi-agent platform designed to help dental clinics recover lost revenue by intelligently re-engaging cold leads, automating multi-channel communication, and seamlessly booking appointments.**

---

## 🚀 Live Demo

You can view a live deployment of the frontend dashboard here:
**[https://mundos-application.vercel.app/](https://mundos-application.vercel.app/)**

---

## 🎯 The Problem Statement

High-traffic dental practices face a significant operational challenge: **lead leakage**. Despite receiving thousands of inquiries, approximately **30% of patient leads go cold** due to inconsistent or manual follow-up processes. For a busy clinic, this can result in over **$1 million in lost annual revenue**. Mundos was built to solve this specific, high-value problem.

## ✨ Our Solution

Mundos is not just a simple CRM; it's an intelligent, proactive system that acts as a team of AI employees. It automates the entire lead nurturing lifecycle, from initial contact to a booked appointment, allowing human staff to focus only on high-intent patients and complex cases.

---

## 🌟 Key Features

- **🧠 AI-Powered Lead Triage:** Instantly analyzes new leads using a LangGraph agent, categorizes their intent, and performs a semantic search on a knowledge base (Pinecone) to craft a perfectly personalized first-contact email.
- **🔄 Autonomous Nurture Sequences:** Deploys a multi-day, multi-channel follow-up strategy across Email, SMS, and AI-powered voice calls to ensure no lead is ever forgotten.
- **🤖 Intelligent Email Reply Handling:** A second, autonomous LangGraph agent reads incoming email replies, understands the user's intent, and uses a suite of tools to handle the conversation.
- **📞 Proactive Voice AI (Vapi.ai Integration):** The nurture sequence can trigger an AI voice agent to call a lead. This agent is dynamically prompted with the lead's name and original inquiry for a hyper-personalized conversation.
- **🛠️ Real-Time Tool Use:** Both the email and voice agents can use tools in real-time to:
  - Query the PostgreSQL database for available appointment slots.
  - Book appointments directly into the system.
  - Search the knowledge base for information on pricing and services.
- **📅 Dynamic Appointment Booking:** A complete backend system for creating and managing available appointment slots, which are the single source of truth for both the AI agents and the admin UI.
- **🖥️ Admin Dashboard:** A clean React-based interface for staff to upload leads, view prioritized tasks, see the full communication history for any lead, and manage appointments.

---

## 🏗️ System Architecture

Mundos is built on a modern, decoupled, API-first architecture.

```
+----------------+ (HTTP API) +-----------------+ (Webhooks) +--------------------+
|                | <------------------> |                 | <------------------> |                    |
| React (Vite)   |                      | FastAPI Backend |                      | Vapi.ai Voice      |
| Frontend       |                      | (Python)        |                      | Platform           |
|                | <------------------> |                 | <------------------> |                    |
+----------------+                      +-------+---------+                      +--------------------+
                                                |
                                                | (SQLAlchemy)
                                                v
                                        +--------+--------+
                                        |                 |
                                        | PostgreSQL      |
                                        | Database        |
                                        +--------+--------+
                                                |
                                                | (LangGraph Orchestration)
                                                v
                                        +--------+--------+ (API Calls) +--------------------+
                                        |                 | <------------------> |                    |
                                        | AI Agents       |                      | OpenAI & Pinecone  |
                                        | (Triage, Reply) |                      | (LLM & Vector DB)  |
                                        |                 | <------------------> |                    |
                                        +-----------------+                      +--------------------+
```

---

## 💻 Technology Stack

| Category      | Technology                                      |
| :------------ | :---------------------------------------------- |
| **Frontend**  | React, Vite, Axios                              |
| **Backend**   | FastAPI, Uvicorn, SQLAlchemy                    |
| **Database**  | PostgreSQL                                      |
| **AI/ML**     | LangGraph, OpenAI (GPT-4o), Pinecone (Vector DB)|
| **Voice AI**  | Vapi.ai                                         |
| **Deployment**| Vercel (Frontend), AWS (Backend)          |

---

## 🛠️ Local Setup and Installation

Follow these steps to run the project on your local machine.

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL installed and running
- `ngrok` for testing webhooks locally

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Create the database in PostgreSQL
# (Using psql or a GUI tool like DBeaver)
CREATE DATABASE bright_smile_db;

# Create a .env file in the backend/ directory
# Copy the contents of .env.example (see below) and fill in your credentials
cp .env.example .env
nano .env # Edit the file with your keys
```

### 2. Frontend Setup

```bash
# Navigate to the frontend directory from the root
cd frontend

# Install dependencies
npm install
```

## 🔑 Environment Variables (.env)

Create a `.env` file in the `backend/` directory and populate it with the following keys:

```ini
# PostgreSQL Database Configuration
DATABASE_URL="postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/bright_smile_db"

# OpenAI API Key
OPENAI_API_KEY="sk-..."

# SMTP Email Configuration (e.g., SendGrid)
SMTP_HOST="smtp.sendgrid.net"
SMTP_PORT=587
SMTP_USER="apikey"
SMTP_PASSWORD="YOUR_SENDGRID_API_KEY"
SENDER_EMAIL="your_verified_sender_email@yourdomain.com"

# Domain for Inbound Email Replies
REPLY_DOMAIN="replies.yourdomain.com"

# VAPI Voice AI Configuration
VAPI_API_KEY="your_vapi_api_key_here"
VAPI_PHONE_NUMBER_ID="your_vapi_phone_number_id_here"
VAPI_ASSISTANT_ID="your_vapi_assistant_id_here"

# Pinecone Vector DB
PINECONE_API_KEY="your_pinecone_api_key"
PINECONE_INDEX_NAME="your_pinecone_index_name"

# Public URL for Webhooks (during local testing, this is your ngrok URL)
SERVER_BASE_URL="https://<your-id>.ngrok-free.app"
```

## ▶️ Running the Application

### Run the Backend Server:
```bash
# From the backend/ directory
uvicorn app.main:app --reload
```
The backend will be available at http://localhost:8000. The API docs are at http://localhost:8000/docs.

### Run the Frontend Server:
```bash
# From the frontend/ directory
npm run dev
```
The frontend will be available at http://localhost:3000.

### Run ngrok for Webhooks:
```bash
# In a new terminal
ngrok http 8000
```
Use the public https://... URL provided by ngrok as your `SERVER_BASE_URL` in the `.env` file and for configuring your SendGrid and Vapi webhooks.
