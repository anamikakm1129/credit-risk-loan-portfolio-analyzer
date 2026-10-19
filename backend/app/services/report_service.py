import io
import csv
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from backend.app.models import Loan, Borrower, ReportRun, RiskAssessment
from backend.app.services.portfolio_metrics import compute_portfolio_summary
from backend.app.services.repayment_analysis import calculate_loan_repayment_state

def generate_portfolio_report(
    db: Session,
    user_id: str = "analyst@credvista.internal",
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    risk_bands: Optional[List[str]] = None,
    loan_statuses: Optional[List[str]] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates an audited ReportRun snapshot with metric versioning and applied filters.
    """
    if period_end is None:
        period_end = date.today()

    # Query loans with applied filters
    query = db.query(Loan).join(Borrower, Loan.borrower_id == Borrower.borrower_id)

    if loan_statuses and len(loan_statuses) > 0:
        query = query.filter(Loan.status.in_(loan_statuses))

    if period_start:
        query = query.filter(Loan.issue_date >= period_start)
    if period_end:
        query = query.filter(Loan.issue_date <= period_end)

    loans = query.all()

    # Filter by risk bands if specified
    if risk_bands and len(risk_bands) > 0:
        filtered_loans = []
        for l in loans:
            assessment = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.borrower_id == l.borrower_id)
                .order_by(RiskAssessment.assessed_at.desc())
                .first()
            )
            band = assessment.risk_band if assessment else "Medium"
            if band in risk_bands:
                filtered_loans.append(l)
        loans = filtered_loans

    summary = compute_portfolio_summary(db, cutoff_date=period_end)

    report_id = f"REP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    filters_meta = {
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat() if period_end else None,
        "risk_bands": risk_bands or ["All"],
        "loan_statuses": loan_statuses or ["All"],
        "notes": notes or "Standard periodic review"
    }

    report_run = ReportRun(
        report_id=report_id,
        generated_at=datetime.utcnow(),
        user_id=user_id,
        period_start=period_start,
        period_end=period_end,
        filters_json=filters_meta,
        metric_version="v1.0",
        summary_json=summary,
        file_reference=f"/api/v1/reports/{report_id}/download.csv"
    )

    db.add(report_run)
    db.commit()

    return {
        "report_id": report_id,
        "generated_at": report_run.generated_at.isoformat(),
        "user_id": user_id,
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat(),
        "filters": filters_meta,
        "metric_version": "v1.0",
        "portfolio_summary": summary,
        "matching_loans_count": len(loans),
        "download_url": report_run.file_reference
    }

def export_loans_to_csv(db: Session, cutoff_date: Optional[date] = None) -> str:
    """
    Exports loan-level records with calculated repayment and risk status to CSV.
    """
    if cutoff_date is None:
        cutoff_date = date.today()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Loan ID", "Borrower ID", "Borrower Name", "Credit Score", "DTI (%)",
        "Principal ($)", "Issue Date", "Term (Months)", "Rate (%)",
        "Outstanding Principal ($)", "Overdue Amount ($)", "Days Past Due",
        "Loan Status", "Risk Band"
    ])

    loans = db.query(Loan).all()
    for l in loans:
        b = l.borrower
        rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff_date)
        assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.borrower_id == l.borrower_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .first()
        )
        risk_band = assessment.risk_band if assessment else "Medium"

        writer.writerow([
            l.loan_id,
            b.borrower_id,
            b.full_name,
            b.credit_score or "",
            b.dti_ratio or "",
            f"{l.principal_amount:.2f}",
            l.issue_date.isoformat(),
            l.term_months,
            f"{l.annual_rate * 100.0:.2f}%",
            f"{l.outstanding_principal:.2f}",
            f"{rep['overdue_amount']:.2f}",
            rep["days_past_due"],
            l.status,
            risk_band
        ])

    return output.getvalue()

