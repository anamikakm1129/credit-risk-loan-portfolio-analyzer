from datetime import date, datetime
from typing import List, Dict, Any, Tuple
from backend.app.models import RepaymentSchedule, RepaymentTransaction

def calculate_loan_repayment_state(
    schedules: List[RepaymentSchedule],
    transactions: List[RepaymentTransaction],
    cutoff_date: date
) -> Dict[str, Any]:
    """
    Computes due, paid, overdue amount, and days past due (DPD) for a single loan
    as of a reporting cutoff_date using FIFO partial-payment allocation.
    """
    # 1. Total paid on or before cutoff date
    valid_transactions = [
        t for t in transactions 
        if t.payment_date <= cutoff_date and t.payment_status == "Completed"
    ]
    total_paid = sum(t.amount for t in valid_transactions)

    # 2. Schedules due on or before cutoff date
    due_schedules = [s for s in schedules if s.due_date <= cutoff_date]
    sorted_schedules = sorted(due_schedules, key=lambda s: s.due_date)

    total_due = sum(s.scheduled_amount for s in sorted_schedules)

    # 3. FIFO allocation of total_paid against sorted due installments
    remaining_cash = total_paid
    overdue_amount = 0.0
    earliest_unpaid_due_date = None

    for item in sorted_schedules:
        installment_due = item.scheduled_amount
        if remaining_cash >= installment_due:
            remaining_cash -= installment_due
        else:
            unpaid_on_this_item = installment_due - remaining_cash
            overdue_amount += unpaid_on_this_item
            remaining_cash = 0.0
            if earliest_unpaid_due_date is None:
                earliest_unpaid_due_date = item.due_date

    # 4. Calculate Days Past Due (DPD)
    days_past_due = 0
    if earliest_unpaid_due_date and overdue_amount > 0.01:
        delta = (cutoff_date - earliest_unpaid_due_date).days
        days_past_due = max(0, delta)

    # 5. Delinquency stage classification
    if days_past_due >= 90:
        delinquency_stage = "Defaulted"
    elif days_past_due >= 31:
        delinquency_stage = "Delinquent (31-89 DPD)"
    elif days_past_due >= 1:
        delinquency_stage = "Late (1-30 DPD)"
    else:
        delinquency_stage = "Current"

    repayment_rate = (total_paid / total_due * 100.0) if total_due > 0 else 100.0

    return {
        "total_due": round(total_due, 2),
        "total_paid": round(total_paid, 2),
        "overdue_amount": round(overdue_amount, 2),
        "days_past_due": days_past_due,
        "earliest_unpaid_due_date": earliest_unpaid_due_date.isoformat() if earliest_unpaid_due_date else None,
        "delinquency_stage": delinquency_stage,
        "repayment_rate": round(min(100.0, repayment_rate), 2)
    }

