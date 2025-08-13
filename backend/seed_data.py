#!/usr/bin/env python3
"""
Database Seeding Script for Mundos Application
Populates the database with realistic sample data to test dashboard metrics
"""

import os
import sys
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, engine
from app.models import Base, Lead, Communication, LeadStatusEnum, CommTypeEnum, CommDirectionEnum

# Load environment variables
load_dotenv()

def generate_lead_id():
    """Generate a unique lead ID in format LEAD-XXXXXX"""
    return f"LEAD-{random.randint(100000, 999999)}"

def generate_realistic_inquiry_notes():
    """Generate realistic inquiry notes for leads"""
    inquiries = [
        "Hi, I'm interested in teeth whitening services. Can you provide more information about your procedures and pricing?",
        "I need to schedule a dental cleaning and checkup. What are your available times this month?",
        "My child needs braces. Do you offer pediatric orthodontic services? What's the consultation process?",
        "I have a severe toothache and need emergency dental care. Are you accepting new patients?",
        "Looking for cosmetic dental work including veneers. Can you send me information about your cosmetic services?",
        "I'm interested in dental implants to replace missing teeth. What's the procedure timeline and cost?",
        "Need a root canal treatment. Do you accept my insurance? Can you provide a quote?",
        "Looking for a family dentist for regular checkups. Do you have weekend appointments available?",
        "I'm interested in Invisalign treatment. How long does the process typically take?",
        "Need wisdom teeth extraction. What's your availability for oral surgery?",
        "Looking for preventive dental care for my family. What packages do you offer?",
        "I have dental anxiety. Do you offer sedation dentistry options?",
        "Need urgent dental care for a broken tooth. Can you see me today?",
        "Interested in a smile makeover. What cosmetic options do you recommend?",
        "Looking for affordable dental care options. Do you have payment plans available?"
    ]
    return random.choice(inquiries)

def generate_ai_summary():
    """Generate realistic AI summaries"""
    summaries = [
        "High-priority lead seeking cosmetic dental services. Shows strong interest in veneers and whitening. Budget appears flexible.",
        "Routine dental care inquiry. Family looking for regular checkups and cleanings. Good potential for ongoing relationship.",
        "Emergency dental case requiring immediate attention. Patient in pain, needs urgent care scheduling.",
        "Orthodontic inquiry for child. Parents researching options, likely to compare multiple providers.",
        "Insurance-conscious patient seeking covered treatments. Price-sensitive but has genuine dental needs.",
        "Cosmetic-focused lead with multiple service interests. High-value potential patient.",
        "Preventive care focused family. Looking for long-term dental home.",
        "Anxiety-conscious patient needing special care approach. Requires gentle communication.",
        "Urgent care needed. Potential for immediate conversion if handled quickly.",
        "Complex treatment case requiring detailed consultation and treatment planning."
    ]
    return random.choice(summaries)

def generate_ai_drafted_reply():
    """Generate realistic AI-drafted replies"""
    replies = [
        "Thank you for your interest in our dental services! I'd be happy to schedule a consultation to discuss your specific needs and provide detailed pricing information. Our team specializes in cosmetic dentistry and we offer flexible payment options. When would be a convenient time for you to visit our office?",
        "Hello! We'd love to help you and your family with your dental care needs. We have several appointment slots available this month for cleanings and checkups. Our office accepts most major insurance plans. Would you prefer a morning or afternoon appointment?",
        "I understand you're dealing with dental pain, and I want to help you get relief as soon as possible. We have emergency appointment slots available today. Please call our office immediately at [phone number] so we can schedule you for urgent care.",
        "Thank you for considering our practice for your orthodontic needs. We offer comprehensive consultations for children's braces, including traditional metal braces and clear aligners. I'd be happy to schedule a complimentary consultation to discuss the best options for your child.",
        "I appreciate your inquiry about our cosmetic dental services. We offer a full range of treatments including veneers, whitening, and smile makeovers. I'd love to schedule a consultation where we can discuss your goals and create a personalized treatment plan."
    ]
    return random.choice(replies)

def generate_communication_content(comm_type, direction):
    """Generate realistic communication content based on type and direction"""
    if comm_type == CommTypeEnum.email:
        if direction == CommDirectionEnum.incoming:
            return "Follow-up email from patient asking about appointment availability and insurance coverage."
        elif direction == CommDirectionEnum.outgoing_auto:
            return "Automated appointment reminder email sent 24 hours before scheduled visit."
        else:
            return "Personal follow-up email from dental coordinator addressing patient questions and scheduling next steps."
    
    elif comm_type == CommTypeEnum.sms:
        if direction == CommDirectionEnum.incoming:
            return "Patient text: 'Can I reschedule my appointment for next week?'"
        elif direction == CommDirectionEnum.outgoing_auto:
            return "Automated SMS reminder: Your appointment is tomorrow at 2 PM. Reply CONFIRM to confirm."
        else:
            return "Personal text from office: 'Hi! Just checking if you have any questions before your visit tomorrow.'"
    
    elif comm_type == CommTypeEnum.phone_call:
        if direction == CommDirectionEnum.incoming:
            return "Incoming call - Patient inquired about emergency appointment availability."
        else:
            return "Outbound call - Discussed treatment options and scheduled consultation."
    
    else:  # note
        return "Internal note: Patient expressed interest in multiple services. Flagged for comprehensive treatment planning."

def create_sample_data():
    """Create comprehensive sample data for testing dashboard metrics"""
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        print("Clearing existing data...")
        db.query(Communication).delete()
        db.query(Lead).delete()
        db.commit()
        
        # Sample names for realistic data
        first_names = ["John", "Sarah", "Michael", "Emma", "David", "Lisa", "Robert", "Jennifer", "William", "Ashley", 
                      "James", "Jessica", "Christopher", "Amanda", "Daniel", "Melissa", "Matthew", "Michelle", "Anthony", "Kimberly"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                     "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
        
        leads_data = []
        communications_data = []
        
        # Generate leads with different statuses and time distributions
        print("Generating sample leads...")
        
        # Status distribution for realistic metrics
        status_distribution = {
            LeadStatusEnum.new: 15,
            LeadStatusEnum.needs_immediate_attention: 8,
            LeadStatusEnum.responded: 20,
            LeadStatusEnum.nurturing: 25,
            LeadStatusEnum.converted: 12,
            LeadStatusEnum.archived_no_response: 10,
            LeadStatusEnum.archived_not_interested: 10
        }
        
        lead_counter = 0
        
        for status, count in status_distribution.items():
            for _ in range(count):
                lead_counter += 1
                
                # Generate time ranges for different statuses
                if status in [LeadStatusEnum.new, LeadStatusEnum.needs_immediate_attention]:
                    # Recent leads (last 3 days)
                    days_ago = random.randint(0, 3)
                    hours_ago = random.randint(0, 23)
                elif status in [LeadStatusEnum.responded, LeadStatusEnum.nurturing]:
                    # Active leads (last 2 weeks)
                    days_ago = random.randint(1, 14)
                    hours_ago = random.randint(0, 23)
                else:
                    # Older leads (last month)
                    days_ago = random.randint(7, 30)
                    hours_ago = random.randint(0, 23)
                
                created_time = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
                inquiry_time = created_time - timedelta(hours=random.randint(0, 4))
                
                # Updated time based on status
                if status == LeadStatusEnum.new:
                    updated_time = created_time
                else:
                    updated_time = created_time + timedelta(hours=random.randint(1, 48))
                
                # Nurture attempts based on status
                if status == LeadStatusEnum.nurturing:
                    nurture_attempts = random.randint(1, 5)
                elif status in [LeadStatusEnum.converted, LeadStatusEnum.archived_no_response]:
                    nurture_attempts = random.randint(0, 3)
                else:
                    nurture_attempts = 0
                
                # Generate lead
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                
                lead = Lead(
                    lead_id=generate_lead_id(),
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{first_name.lower()}.{last_name.lower()}@email.com",
                    phone_number=f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    inquiry_notes=generate_realistic_inquiry_notes(),
                    inquiry_date=inquiry_time,
                    status=status,
                    nurture_attempts=nurture_attempts,
                    ai_summary=generate_ai_summary() if random.random() > 0.3 else None,  # 70% have AI summaries
                    ai_drafted_reply=generate_ai_drafted_reply() if random.random() > 0.4 else None,  # 60% have AI drafts
                    created_at=created_time,
                    updated_at=updated_time
                )
                
                leads_data.append(lead)
        
        # Insert leads
        print(f"Inserting {len(leads_data)} leads...")
        db.add_all(leads_data)
        db.commit()
        
        # Generate communications for leads
        print("Generating communications...")
        
        for lead in leads_data:
            # Skip new leads (no communications yet)
            if lead.status == LeadStatusEnum.new:
                continue
            
            # Generate 1-5 communications per lead based on status
            if lead.status in [LeadStatusEnum.converted, LeadStatusEnum.nurturing]:
                comm_count = random.randint(3, 6)
            elif lead.status == LeadStatusEnum.responded:
                comm_count = random.randint(2, 4)
            else:
                comm_count = random.randint(1, 3)
            
            for i in range(comm_count):
                # Communication types with realistic distribution
                comm_type = random.choices([
                    CommTypeEnum.email,
                    CommTypeEnum.sms,
                    CommTypeEnum.phone_call,
                    CommTypeEnum.note
                ], weights=[40, 25, 20, 15])[0]
                
                # Direction based on communication flow
                if i == 0:  # First communication is usually incoming inquiry
                    direction = CommDirectionEnum.incoming
                else:
                    direction = random.choices([
                        CommDirectionEnum.outgoing_auto,
                        CommDirectionEnum.outgoing_manual,
                        CommDirectionEnum.incoming
                    ], weights=[30, 40, 30])[0]
                
                # Communication timing
                comm_time = lead.created_at + timedelta(
                    hours=i * random.randint(4, 24),
                    minutes=random.randint(0, 59)
                )
                
                communication = Communication(
                    lead_id=lead.id,
                    type=comm_type,
                    direction=direction,
                    content=generate_communication_content(comm_type, direction),
                    sent_at=comm_time
                )
                
                communications_data.append(communication)
        
        # Insert communications
        print(f"Inserting {len(communications_data)} communications...")
        db.add_all(communications_data)
        db.commit()
        
        print("✅ Sample data creation completed successfully!")
        print(f"Created {len(leads_data)} leads and {len(communications_data)} communications")
        
        # Print summary statistics
        print("\n📊 Data Summary:")
        for status, count in status_distribution.items():
            print(f"  {status.value.replace('_', ' ').title()}: {count} leads")
        
        print(f"\n🔄 Communications by type:")
        comm_types = {}
        for comm in communications_data:
            comm_types[comm.type] = comm_types.get(comm.type, 0) + 1
        for comm_type, count in comm_types.items():
            print(f"  {comm_type.value.title()}: {count}")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting database seeding...")
    create_sample_data()
    print("🎉 Database seeding completed!")