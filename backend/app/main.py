from fastapi import FastAPI,Request
from apscheduler.schedulers.background import BackgroundScheduler # Import scheduler
from .database import engine
from . import models
from .api import leads,webhooks,dashboard,appointments 
from .scheduler.nurture_engine import nurture_and_recall_job # Import our job
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware

# This command tells SQLAlchemy to create the tables if they don't exist
# In a production app, you'd use a migration tool like Alembic
models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Bright Smile Clinic MVP",
    description="API for recovering lost leads and improving patient recall workflows.",
    version="0.1.0"
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Scheduler Setup ---
scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    # For testing, run the job every 1 minute.
    # For production, you would change this to 'cron', day_of_week='mon-sun', hour=9
    scheduler.add_job(nurture_and_recall_job, 'interval', minutes=10, id="nurture_job")
    scheduler.start()
    print("Scheduler started... Nurture job will run every 10 minute for testing.")

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
    print("Scheduler shut down.")

# Include the router from our leads API file
app.include_router(webhooks.router, prefix="/api")
app.include_router(leads.router, prefix="/api/leads")
app.include_router(dashboard.router, prefix="/api") 
app.include_router(appointments.router, prefix="/api")

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Bright Smile Clinic API"}



# @app.post("/api/webhooks/email-reply")
# async def email_reply(request: Request):
#     data = await request.form()
#     print("\n📩 Incoming Email Payload:")
#     for key, value in data.items():
#         print(f"{key}: {value}\n")
#     return {"status": "received"}