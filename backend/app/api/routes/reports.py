from fastapi import APIRouter, Depends, Query, Body, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models import ReportRun
from backend.app.services.report_service import generate_portfolio_report, export_loans_to_csv

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("")
def create_report(
    user_id: Optional[str] = Body("analyst@credvista.internal"),
    period_start: Optional[str] = Body(None),
    period_end: Optional[str] = Body(None),
    risk_bands: Optional[List[str]] = Body(None),
    loan_statuses: Optional[List[str]] = Body(None),
    notes: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Generates and records an audited report run with exact filters and metric snapshots.
    """
    p_start = datetime.strptime(period_start, "%Y-%m-%d").date() if period_start else None
    p_end = datetime.strptime(period_end or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    return generate_portfolio_report(
        db=db,
        user_id=user_id,
        period_start=p_start,
        period_end=p_end,
        risk_bands=risk_bands,
        loan_statuses=loan_statuses,
        notes=notes
    )

@router.get("/history")
def list_reports_history(db: Session = Depends(get_db)):
    """
    Returns audit list of previously generated reports.
    """
    runs = db.query(ReportRun).order_by(ReportRun.generated_at.desc()).limit(50).all()
    return [
        {
            "report_id": r.report_id,
            "generated_at": r.generated_at.isoformat(),
            "user_id": r.user_id,
            "period_start": r.period_start.isoformat() if r.period_start else None,
            "period_end": r.period_end.isoformat() if r.period_end else None,
            "filters": r.filters_json,
            "metric_version": r.metric_version,
            "portfolio_summary": r.summary_json,
            "file_reference": r.file_reference
        }
        for r in runs
    ]

@router.get("/export.csv")
def download_loans_csv(
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Exports loan-level portfolio data to CSV.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()
    csv_data = export_loans_to_csv(db, cutoff_date=cutoff)

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=credvista_portfolio_{cutoff.isoformat()}.csv"
        }
    )

