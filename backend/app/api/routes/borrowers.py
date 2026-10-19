from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models import Borrower, Loan, RiskAssessment
from backend.app.services.repayment_analysis import calculate_loan_repayment_state
from backend.app.services.risk_rules import evaluate_risk, BorrowerRiskFeatures

router = APIRouter(prefix="/borrowers", tags=["Borrowers"])

@router.get("")
def list_borrowers(
    search: Optional[str] = Query(None, description="Search by borrower name or ID"),
    risk_band: Optional[str] = Query(None, description="Filter by risk band (Low, Medium, High, Review Required)"),
    min_score: Optional[int] = Query(None),
    max_score: Optional[int] = Query(None),
    min_dti: Optional[float] = Query(None),
    max_dti: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    sort_by: str = Query("borrower_id", description="Sort field: borrower_id, full_name, credit_score, annual_income, dti, exposure"),
    sort_dir: str = Query("asc", description="Sort direction: asc or desc"),
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Searchable, sortable, paginated borrower directory.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    query = db.query(Borrower)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Borrower.full_name.ilike(s)) | (Borrower.borrower_id.ilike(s)))

    if min_score is not None:
        query = query.filter(Borrower.credit_score >= min_score)
    if max_score is not None:
        query = query.filter(Borrower.credit_score <= max_score)

    borrowers = query.all()

    # Calculate derived stats for each borrower
    enriched = []
    for b in borrowers:
        dti = b.dti_ratio
        if min_dti is not None and (dti is None or dti < min_dti):
            continue
        if max_dti is not None and (dti is None or dti > max_dti):
            continue

        latest_assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.borrower_id == b.borrower_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .first()
        )
        band = latest_assessment.risk_band if latest_assessment else "Medium"
        if risk_band and risk_band != "All" and band != risk_band:
            continue

        active_loans = [l for l in b.loans if l.status in ["Active", "Overdue", "Delinquent"]]
        total_exposure = sum(l.outstanding_principal for l in active_loans)
        
        total_overdue = 0.0
        max_dpd = 0
        latest_status = "Active"
        for l in b.loans:
            rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff)
            total_overdue += rep["overdue_amount"]
            max_dpd = max(max_dpd, rep["days_past_due"])
            if l.status in ["Overdue", "Delinquent", "Defaulted"]:
                latest_status = l.status

        enriched.append({
            "borrower_id": b.borrower_id,
            "full_name": b.full_name,
            "annual_income": b.annual_income,
            "credit_score": b.credit_score,
            "monthly_debt_obligations": b.monthly_debt_obligations,
            "employment_status": b.employment_status,
            "home_ownership": b.home_ownership,
            "dti_ratio": dti,
            "active_loans_count": len(active_loans),
            "total_exposure": round(total_exposure, 2),
            "total_overdue": round(total_overdue, 2),
            "days_past_due": max_dpd,
            "risk_band": band,
            "latest_status": latest_status
        })

    # Sorting
    reverse = (sort_dir.lower() == "desc")
    if sort_by == "credit_score":
        enriched.sort(key=lambda x: (x["credit_score"] is not None, x["credit_score"]), reverse=reverse)
    elif sort_by == "annual_income":
        enriched.sort(key=lambda x: (x["annual_income"] is not None, x["annual_income"]), reverse=reverse)
    elif sort_by == "dti":
        enriched.sort(key=lambda x: (x["dti_ratio"] is not None, x["dti_ratio"]), reverse=reverse)
    elif sort_by == "exposure":
        enriched.sort(key=lambda x: x["total_exposure"], reverse=reverse)
    elif sort_by == "overdue":
        enriched.sort(key=lambda x: x["total_overdue"], reverse=reverse)
    elif sort_by == "full_name":
        enriched.sort(key=lambda x: x["full_name"].lower(), reverse=reverse)
    else:
        enriched.sort(key=lambda x: x["borrower_id"], reverse=reverse)

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

@router.get("/{borrower_id}")
def get_borrower_profile(
    borrower_id: str,
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns full borrower profile, risk factors explanation, loans and repayment metrics.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    b = db.query(Borrower).filter(Borrower.borrower_id == borrower_id).first()
    if not b:
        raise HTTPException(status_code=404, detail=f"Borrower {borrower_id} not found")

    # Assessment
    latest_assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.borrower_id == b.borrower_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .first()
    )

    # Calculate real-time fresh evaluation
    max_dpd = 0
    total_overdue = 0.0
    for l in b.loans:
        rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff)
        total_overdue += rep["overdue_amount"]
        max_dpd = max(max_dpd, rep["days_past_due"])

    features = BorrowerRiskFeatures(
        borrower_id=b.borrower_id,
        annual_income=b.annual_income,
        monthly_debt=b.monthly_debt_obligations,
        credit_score=b.credit_score,
        max_overdue_days=max_dpd,
        total_overdue_amount=total_overdue,
        active_loans_count=len([l for l in b.loans if l.status != "Settled"])
    )
    fresh_eval = evaluate_risk(features)

    # Loan list
    loans_list = []
    total_exposure = 0.0
    total_due_all = 0.0
    total_paid_all = 0.0

    for l in b.loans:
        rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff)
        total_due_all += rep["total_due"]
        total_paid_all += rep["total_paid"]
        if l.status != "Settled":
            total_exposure += l.outstanding_principal

        loans_list.append({
            "loan_id": l.loan_id,
            "principal_amount": l.principal_amount,
            "issue_date": l.issue_date.isoformat(),
            "term_months": l.term_months,
            "annual_rate": l.annual_rate,
            "status": l.status,
            "outstanding_principal": l.outstanding_principal,
            "purpose": l.purpose,
            "overdue_amount": rep["overdue_amount"],
            "days_past_due": rep["days_past_due"],
            "repayment_rate": rep["repayment_rate"]
        })

    return {
        "borrower_id": b.borrower_id,
        "full_name": b.full_name,
        "annual_income": b.annual_income,
        "credit_score": b.credit_score,
        "monthly_debt_obligations": b.monthly_debt_obligations,
        "employment_status": b.employment_status,
        "home_ownership": b.home_ownership,
        "dti_ratio": b.dti_ratio,
        "active_loans_count": len([l for l in b.loans if l.status != "Settled"]),
        "total_exposure": round(total_exposure, 2),
        "total_overdue": round(total_overdue, 2),
        "days_past_due": max_dpd,
        "risk_band": fresh_eval.risk_band,
        "risk_assessment": fresh_eval.to_dict(),
        "loans": loans_list,
        "repayment_summary": {
            "total_due": round(total_due_all, 2),
            "total_paid": round(total_paid_all, 2),
            "total_overdue": round(total_overdue, 2),
            "overall_repayment_rate": round((total_paid_all / total_due_all * 100.0) if total_due_all > 0 else 100.0, 1)
        }
    }
