from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

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