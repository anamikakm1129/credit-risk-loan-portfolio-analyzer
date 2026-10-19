from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models import Loan, Borrower, RepaymentTransaction, RepaymentSchedule
from backend.app.services.repayment_analysis import calculate_loan_repayment_state

router = APIRouter(prefix="/repayments", tags=["Repayments"])

@router.get("/overview")
def get_repayments_overview(
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns portfolio-wide repayment performance, aging buckets, and collection stats.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    loans = db.query(Loan).all()

    total_due = 0.0
    total_paid = 0.0
    total_overdue = 0.0

    buckets = {
        "Current (0 DPD)": {"count": 0, "principal": 0.0, "overdue": 0.0},
        "Late (1-30 DPD)": {"count": 0, "principal": 0.0, "overdue": 0.0},
        "Delinquent (31-60 DPD)": {"count": 0, "principal": 0.0, "overdue": 0.0},
        "Severely Delinquent (61-89 DPD)": {"count": 0, "principal": 0.0, "overdue": 0.0},
        "Defaulted (90+ DPD)": {"count": 0, "principal": 0.0, "overdue": 0.0},
    }

    for l in loans:
        rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff)
        total_due += rep["total_due"]
        total_paid += rep["total_paid"]
        total_overdue += rep["overdue_amount"]

        dpd = rep["days_past_due"]
        is_default = (l.status == "Defaulted" or dpd >= 90)

        if is_default:
            b_key = "Defaulted (90+ DPD)"
        elif dpd >= 61:
            b_key = "Severely Delinquent (61-89 DPD)"
        elif dpd >= 31:
            b_key = "Delinquent (31-60 DPD)"
        elif dpd >= 1:
            b_key = "Late (1-30 DPD)"
        else:
            b_key = "Current (0 DPD)"

        buckets[b_key]["count"] += 1
        if l.status != "Settled":
            buckets[b_key]["principal"] += l.outstanding_principal
        buckets[b_key]["overdue"] += rep["overdue_amount"]

    aging_list = []
    total_open_principal = sum(b["principal"] for b in buckets.values())
    for name, data in buckets.items():
        share = (data["principal"] / total_open_principal * 100.0) if total_open_principal > 0 else 0.0
        aging_list.append({
            "bucket_name": name,
            "loans_count": data["count"],
            "outstanding_principal": round(data["principal"], 2),
            "overdue_amount": round(data["overdue"], 2),
            "portfolio_share_pct": round(share, 1)
        })

    repayment_rate = (total_paid / total_due * 100.0) if total_due > 0 else 100.0

    return {
        "reporting_date": cutoff.isoformat(),
        "total_due": round(total_due, 2),
        "total_paid": round(total_paid, 2),
        "total_overdue": round(total_overdue, 2),
        "repayment_rate": round(min(100.0, repayment_rate), 2),
        "aging_buckets": aging_list
    }

@router.get("/transactions")
def list_repayment_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    loan_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Paginated list of payment transactions across all loans.
    """
    query = db.query(RepaymentTransaction).join(Loan, RepaymentTransaction.loan_id == Loan.loan_id)

    if status:
        query = query.filter(RepaymentTransaction.payment_status == status)
    if loan_id:
        query = query.filter(RepaymentTransaction.loan_id.ilike(f"%{loan_id}%"))

    total = query.count()
    transactions = (
        query.order_by(RepaymentTransaction.payment_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for t in transactions:
        b = t.loan.borrower
        items.append({
            "payment_id": t.payment_id,
            "loan_id": t.loan_id,
            "borrower_name": b.full_name,
            "payment_date": t.payment_date.isoformat(),
            "amount": t.amount,
            "payment_status": t.payment_status,
            "reference": t.reference
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 1
    }

