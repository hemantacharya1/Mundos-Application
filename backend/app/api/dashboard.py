from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, and_
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .. import models
from ..database import get_db

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Calculates and returns key performance indicators for the dashboard."""
    
    active_statuses = [
        models.LeadStatusEnum.needs_immediate_attention,
        models.LeadStatusEnum.responded,
        models.LeadStatusEnum.nurturing
    ]
    
    total_active_leads = db.query(models.Lead).filter(models.Lead.status.in_(active_statuses)).count()
    needs_attention_count = db.query(models.Lead).filter(models.Lead.status == models.LeadStatusEnum.needs_immediate_attention).count()
    responded_count = db.query(models.Lead).filter(models.Lead.status == models.LeadStatusEnum.responded).count()
    nurturing_count = db.query(models.Lead).filter(models.Lead.status == models.LeadStatusEnum.nurturing).count()

    # Metrics for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    converted_this_month = db.query(models.Lead).filter(
        models.Lead.status == models.LeadStatusEnum.converted,
        models.Lead.updated_at >= thirty_days_ago
    ).count()

    # Calculate conversion rate
    total_handled_this_month = converted_this_month + db.query(models.Lead).filter(
        models.Lead.status.in_([models.LeadStatusEnum.archived_no_response, models.LeadStatusEnum.archived_not_interested]),
        models.Lead.updated_at >= thirty_days_ago
    ).count()

    conversion_rate_percent = (converted_this_month / total_handled_this_month * 100) if total_handled_this_month > 0 else 0

    return {
        "total_active_leads": total_active_leads,
        "needs_attention_count": needs_attention_count,
        "responded_count": responded_count,
        "nurturing_count": nurturing_count,
        "converted_this_month": converted_this_month,
        "conversion_rate_percent": round(conversion_rate_percent, 2)
    }

@router.get("/advanced-metrics")
def get_advanced_dashboard_metrics(db: Session = Depends(get_db)):
    """Returns advanced metrics for different visualization types."""
    
    # 1. LEAD STATUS DISTRIBUTION (Pie Chart)
    status_counts = db.query(
        models.Lead.status,
        func.count(models.Lead.id).label('count')
    ).group_by(models.Lead.status).all()
    
    lead_status_distribution = [
        {"status": status.value, "count": count} 
        for status, count in status_counts
    ]
    
    # 2. DAILY LEAD VOLUME TREND (Line Chart)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_leads = db.query(
        func.date(models.Lead.created_at).label('date'),
        func.count(models.Lead.id).label('count')
    ).filter(
        models.Lead.created_at >= seven_days_ago
    ).group_by(
        func.date(models.Lead.created_at)
    ).order_by(
        func.date(models.Lead.created_at)
    ).all()
    
    daily_lead_volume = [
        {"date": str(date), "count": count} 
        for date, count in daily_leads
    ]
    
    # 3. LEAD VELOCITY BY STATUS (Bar Chart)
    lead_velocity = db.query(
        models.Lead.status,
        func.avg(
            extract('epoch', models.Lead.updated_at - models.Lead.created_at) / 3600
        ).label('avg_hours')
    ).filter(
        models.Lead.status.in_([
            models.LeadStatusEnum.responded,
            models.LeadStatusEnum.converted,
            models.LeadStatusEnum.nurturing
        ])
    ).group_by(models.Lead.status).all()
    
    lead_velocity_data = [
        {"status": status.value, "avg_hours": round(avg_hours, 2) if avg_hours else 0}
        for status, avg_hours in lead_velocity
    ]
    
    # 4. NURTURE ATTEMPTS DISTRIBUTION (Histogram/Bar Chart)
    nurture_distribution = db.query(
        models.Lead.nurture_attempts,
        func.count(models.Lead.id).label('count')
    ).filter(
        models.Lead.nurture_attempts > 0
    ).group_by(models.Lead.nurture_attempts).order_by(
        models.Lead.nurture_attempts
    ).all()
    
    nurture_attempts_data = [
        {"attempts": attempts, "count": count}
        for attempts, count in nurture_distribution
    ]
    
    # 5. COMMUNICATION TYPE BREAKDOWN (Donut Chart)
    comm_type_counts = db.query(
        models.Communication.type,
        func.count(models.Communication.id).label('count')
    ).group_by(models.Communication.type).all()
    
    communication_types = [
        {"type": comm_type.value, "count": count}
        for comm_type, count in comm_type_counts
    ]
    
    # 6. RESPONSE TIME DISTRIBUTION (Box Plot Data)
    response_times = db.query(
        func.extract('epoch', models.Lead.updated_at - models.Lead.created_at) / 3600
    ).filter(
        models.Lead.status == models.LeadStatusEnum.responded
    ).all()
    
    response_hours = [float(time[0]) for time in response_times if time[0] is not None]
    response_time_stats = {
        "min": min(response_hours) if response_hours else 0,
        "max": max(response_hours) if response_hours else 0,
        "median": sorted(response_hours)[len(response_hours)//2] if response_hours else 0,
        "q1": sorted(response_hours)[len(response_hours)//4] if len(response_hours) >= 4 else 0,
        "q3": sorted(response_hours)[3*len(response_hours)//4] if len(response_hours) >= 4 else 0
    }
    
    # 7. LEAD QUALITY SCORE DISTRIBUTION (Scatter Plot)
    quality_scores = db.query(
        func.length(models.Lead.inquiry_notes).label('notes_length'),
        func.length(models.Lead.email).label('email_completeness'),
        models.Lead.status
    ).filter(
        models.Lead.inquiry_notes.isnot(None)
    ).all()
    
    lead_quality_data = [
        {
            "notes_length": notes_len if notes_len else 0,
            "email_completeness": email_len if email_len else 0,
            "status": status.value,
            "quality_score": (notes_len or 0) + (email_len or 0)
        }
        for notes_len, email_len, status in quality_scores
    ]
    
    # 8. HOURLY INQUIRY PATTERN (Heatmap Data)
    hourly_pattern = db.query(
        extract('hour', models.Lead.created_at).label('hour'),
        func.count(models.Lead.id).label('count')
    ).group_by(
        extract('hour', models.Lead.created_at)
    ).order_by(
        extract('hour', models.Lead.created_at)
    ).all()
    
    hourly_inquiry_pattern = [
        {"hour": hour, "count": count}
        for hour, count in hourly_pattern
    ]
    
    # 9. AI UTILIZATION METRICS (Progress Bars)
    total_leads = db.query(models.Lead).count()
    ai_summary_count = db.query(models.Lead).filter(
        models.Lead.ai_summary.isnot(None)
    ).count()
    ai_draft_count = db.query(models.Lead).filter(
        models.Lead.ai_drafted_reply.isnot(None)
    ).count()
    
    ai_utilization = {
        "total_leads": total_leads,
        "ai_summary_rate": round((ai_summary_count / total_leads * 100), 2) if total_leads > 0 else 0,
        "ai_draft_rate": round((ai_draft_count / total_leads * 100), 2) if total_leads > 0 else 0
    }
    
    # 10. CONVERSION FUNNEL (Funnel Chart)
    funnel_data = db.query(
        models.Lead.status,
        func.count(models.Lead.id).label('count')
    ).group_by(models.Lead.status).all()
    
    # Order by funnel progression
    funnel_order = [
        models.LeadStatusEnum.new,
        models.LeadStatusEnum.needs_immediate_attention,
        models.LeadStatusEnum.responded,
        models.LeadStatusEnum.nurturing,
        models.LeadStatusEnum.converted
    ]
    
    conversion_funnel = []
    for status in funnel_order:
        count = next((item[1] for item in funnel_data if item[0] == status), 0)
        conversion_funnel.append({
            "stage": status.value,
            "count": count,
            "percentage": round((count / total_leads * 100), 2) if total_leads > 0 else 0
        })
    
    return {
        "lead_status_distribution": lead_status_distribution,  # Pie Chart
        "daily_lead_volume": daily_lead_volume,  # Line Chart
        "lead_velocity": lead_velocity_data,  # Bar Chart
        "nurture_attempts": nurture_attempts_data,  # Histogram/Bar Chart
        "communication_types": communication_types,  # Donut Chart
        "response_time_stats": response_time_stats,  # Box Plot
        "lead_quality": lead_quality_data,  # Scatter Plot
        "hourly_pattern": hourly_inquiry_pattern,  # Heatmap
        "ai_utilization": ai_utilization,  # Progress Bars
        "conversion_funnel": conversion_funnel  # Funnel Chart
    }
