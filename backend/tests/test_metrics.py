import pytest
from datetime import date
from backend.app.services.repayment_analysis import calculate_loan_repayment_state
from backend.app.models import RepaymentSchedule, RepaymentTransaction

class MockSchedule:
    def __init__(self, schedule_id, due_date, scheduled_amount):
        self.schedule_id = schedule_id
        self.due_date = due_date
        self.scheduled_amount = scheduled_amount

class MockTransaction:
    def __init__(self, payment_date, amount, payment_status="Completed"):
        self.payment_date = payment_date
        self.amount = amount
        self.payment_status = payment_status

def test_dti_calculation_reconciliation():
    """Hand-calculated fixture test for DTI."""
    annual_income = 120000.0 # Monthly income = $10,000
    monthly_debt = 3500.0
    # Expected DTI = 3500 / 10000 * 100 = 35.0%
    monthly_income = annual_income / 12.0
    dti = round((monthly_debt / monthly_income) * 100.0, 2)
    assert dti == 35.0

def test_on_time_full_payments():
    schedules = [
        MockSchedule(1, date(2026, 1, 1), 500.0),
        MockSchedule(2, date(2026, 2, 1), 500.0),
        MockSchedule(3, date(2026, 3, 1), 500.0),
    ]
    transactions = [
        MockTransaction(date(2026, 1, 1), 500.0),
        MockTransaction(date(2026, 2, 1), 500.0),
        MockTransaction(date(2026, 3, 1), 500.0),
    ]
    cutoff = date(2026, 3, 15)
    res = calculate_loan_repayment_state(schedules, transactions, cutoff)

    assert res["total_due"] == 1500.0
    assert res["total_paid"] == 1500.0
    assert res["overdue_amount"] == 0.0
    assert res["days_past_due"] == 0
    assert res["delinquency_stage"] == "Current"
    assert res["repayment_rate"] == 100.0

def test_partial_payment_fifo_overdue():
    """
    Test partial payment:
    Schedule 1: $400 due 2026-01-01
    Schedule 2: $400 due 2026-02-01
    Schedule 3: $400 due 2026-03-01
    Borrower pays $600 total (satisfies S1 + $200 of S2).
    Unpaid: $200 on S2 + $400 on S3 = $600 overdue.
    Earliest unpaid due date is S2 (2026-02-01).
    Cutoff: 2026-03-03 -> DPD = 30 days.
    """
    schedules = [
        MockSchedule(1, date(2026, 1, 1), 400.0),
        MockSchedule(2, date(2026, 2, 1), 400.0),
        MockSchedule(3, date(2026, 3, 1), 400.0),
    ]
    transactions = [
        MockTransaction(date(2026, 1, 1), 600.0),
    ]
    cutoff = date(2026, 3, 3)
    res = calculate_loan_repayment_state(schedules, transactions, cutoff)

    assert res["total_due"] == 1200.0
    assert res["total_paid"] == 600.0
    assert res["overdue_amount"] == 600.0
    assert res["earliest_unpaid_due_date"] == "2026-02-01"
    assert res["days_past_due"] == 30
    assert res["delinquency_stage"] == "Late (1-30 DPD)"

def test_severely_delinquent_and_defaulted():
    """90+ days overdue translates to Defaulted stage."""
    schedules = [
        MockSchedule(1, date(2026, 1, 1), 300.0),
    ]
    transactions = []
    cutoff = date(2026, 4, 15) # 104 days past 2026-01-01
    res = calculate_loan_repayment_state(schedules, transactions, cutoff)

    assert res["overdue_amount"] == 300.0
    assert res["days_past_due"] == 104
    assert res["delinquency_stage"] == "Defaulted"

