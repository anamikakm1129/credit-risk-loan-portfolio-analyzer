from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models import Loan, Borrower, RiskAssessment
from backend.app.services.repayment_analysis import calculate_loan_repayment_state

router = APIRouter(prefix="/loans", tags=["Loans"])

@router.get("")
def list_loans(
    search: Optional[str] = Query(None, description="Search by loan ID, borrower ID or name"),
    status: Optional[str] = Query(None, description="Active, Overdue, Delinquent, Defaulted, Settled"),
    term_months: Optional[int] = Query(None),
    risk_band: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    sort_by: str = Query("issue_date", description="Sort by: issue_date, loan_id, principal_amount, outstanding_principal, status"),
    sort_dir: str = Query("desc", description="asc or desc"),
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Searchable, sortable, paginated loan directory.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    query = db.query(Loan).join(Borrower, Loan.borrower_id == Borrower.borrower_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (Loan.loan_id.ilike(s)) | 
            (Loan.borrower_id.ilike(s)) | 
            (Borrower.full_name.ilike(s))
        )

    if status and status != "All":
        query = query.filter(Loan.status == status)

    if term_months:
        query = query.filter(Loan.term_months == term_months)

    if min_amount is not None:
        query = query.filter(Loan.principal_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Loan.principal_amount <= max_amount)

    loans = query.all()

    enriched = []
    for l in loans:
        b = l.borrower
        rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff)
        
        assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.borrower_id == b.borrower_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .first()
        )
        band = assessment.risk_band if assessment else "Medium"
        if risk_band and risk_band != "All" and band != risk_band:
            continue

        enriched.append({
            "loan_id": l.loan_id,
            "borrower_id": b.borrower_id,
            "borrower_name": b.full_name,
            "principal_amount": l.principal_amount,
            "issue_date": l.issue_date.isoformat(),
            "term_months": l.term_months,
            "annual_rate": l.annual_rate,
            "status": l.status,
            "outstanding_principal": l.outstanding_principal,
            "purpose": l.purpose,
            "risk_band": band,
            "overdue_amount": rep["overdue_amount"],
            "days_past_due": rep["days_past_due"],
            "repayment_rate": rep["repayment_rate"],
            "delinquency_stage": rep["delinquency_stage"]
        })

    reverse = (sort_dir.lower() == "desc")
    if sort_by == "principal_amount":
        enriched.sort(key=lambda x: x["principal_amount"], reverse=reverse)
    elif sort_by == "outstanding_principal":
        enriched.sort(key=lambda x: x["outstanding_principal"], reverse=reverse)
    elif sort_by == "overdue_amount":
        enriched.sort(key=lambda x: x["overdue_amount"], reverse=reverse)
    elif sort_by == "days_past_due":
        enriched.sort(key=lambda x: x["days_past_due"], reverse=reverse)
    elif sort_by == "loan_id":
        enriched.sort(key=lambda x: x["loan_id"], reverse=reverse)
    else: # issue_date
        enriched.sort(key=lambda x: x["issue_date"], reverse=reverse)

    total_count = len(enriched)
    start_idx = (page - 1) * page_size
    paged_items = enriched[start_idx : start_idx + page_size]

    return {
        "items": paged_items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1
    }

@router.get("/{loan_id}")
def get_loan_detail(
    loan_id: str,
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns full loan details, borrower info, and repayment state.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    l = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not l:
        raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")

    b = l.borrower
    rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff)

    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.borrower_id == b.borrower_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .first()
    )

    schedules_data = [
        {
            "schedule_id": s.schedule_id,
            "installment_number": s.installment_number,
            "due_date": s.due_date.isoformat(),
            "scheduled_amount": s.scheduled_amount,
            "principal_due": s.principal_due,
            "interest_due": s.interest_due,
            "status": s.status
        }
        for s in l.schedules
    ]

    transactions_data = [
        {
            "payment_id": t.payment_id,
            "payment_date": t.payment_date.isoformat(),
            "amount": t.amount,
            "payment_status": t.payment_status,
            "reference": t.reference
        }
        for t in l.transactions
    ]

    return {
        "loan_id": l.loan_id,
        "borrower": {
            "borrower_id": b.borrower_id,
            "full_name": b.full_name,
            "credit_score": b.credit_score,
            "annual_income": b.annual_income,
            "dti_ratio": b.dti_ratio,
            "employment_status": b.employment_status
        },
        "principal_amount": l.principal_amount,
        "issue_date": l.issue_date.isoformat(),
        "term_months": l.term_months,
        "annual_rate": l.annual_rate,
        "status": l.status,
        "outstanding_principal": l.outstanding_principal,
        "purpose": l.purpose,
        "risk_band": assessment.risk_band if assessment else "Medium",
        "repayment_state": rep,
        "schedules": schedules_data,
        "transactions": transactions_data
    }

@router.get("/{loan_id}/repayments")
def get_loan_repayments(
    loan_id: str,
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns schedules and payments history for a loan.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    l = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not l:
        raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")

    rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff)

    return {
        "loan_id": l.loan_id,
        "summary": rep,
        "schedules": [
            {
                "schedule_id": s.schedule_id,
                "installment_number": s.installment_number,
                "due_date": s.due_date.isoformat(),
                "scheduled_amount": s.scheduled_amount,
                "principal_due": s.principal_due,
                "interest_due": s.interest_due,
                "status": s.status
            }
            for s in l.schedules
        ],
        "transactions": [
            {
                "payment_id": t.payment_id,
                "payment_date": t.payment_date.isoformat(),
                "amount": t.amount,
                "payment_status": t.payment_status,
                "reference": t.reference
            }
            for t in l.transactions
        ]
    }

