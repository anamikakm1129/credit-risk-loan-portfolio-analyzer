from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.schemas import DashboardSummaryResponse, DashboardTrendsResponse
from backend.app.services.portfolio_metrics import compute_portfolio_summary
from backend.app.analytics.cohort_queries import get_portfolio_monthly_trends, get_risk_segments_distribution

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    reporting_date: Optional[str] = Query(None, description="Cutoff date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """
    Returns headline portfolio KPIs (Total Loans, Outstanding Principal, Default Rate,
    Overdue Amount, Repayment Rate, Weighted DTI/Credit Score) with definition metadata.
    """
    if reporting_date:
        try:
            cutoff = datetime.strptime(reporting_date, "%Y-%m-%d").date()
        except ValueError:
            cutoff = datetime.strptime(settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()
    else:
        cutoff = datetime.strptime(settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    return compute_portfolio_summary(db, cutoff_date=cutoff)

@router.get("/trends", response_model=DashboardTrendsResponse)
def get_dashboard_trends(
    reporting_date: Optional[str] = Query(None, description="Cutoff date"),
    db: Session = Depends(get_db)
):
    """
    Returns monthly trend data points for portfolio origination, balance, and defaults.
    """
    if reporting_date:
        try:
            cutoff = datetime.strptime(reporting_date, "%Y-%m-%d").date()
        except ValueError:
            cutoff = datetime.strptime(settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()
    else:
        cutoff = datetime.strptime(settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    trends = get_portfolio_monthly_trends(db, cutoff_date=cutoff)
    return {"monthly_trends": trends}
