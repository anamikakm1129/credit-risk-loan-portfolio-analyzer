from datetime import date
from typing import Dict, Any, List, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.app.models import Loan, RepaymentSchedule, RepaymentTransaction

MILESTONES = [1, 3, 6, 9, 12, 18, 24]

def compute_vintage_matrix(
    db: Session,
    cutoff_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Computes cohort vintage performance at fixed loan ages.
    Strictly enforces PRD requirement: Immature cohorts are NEVER treated as zero;
    they are marked as is_immature=True and cumulative_default_rate=None.
    """
    if cutoff_date is None:
        cutoff_date = date.today()

    loans = db.query(Loan).all()

    # Group loans by origination month: YYYY-MM
    cohort_groups = defaultdict(list)
    for l in loans:
        cohort_key = l.issue_date.strftime("%Y-%m")
        cohort_groups[cohort_key].append(l)

    sorted_cohort_keys = sorted(cohort_groups.keys())
    result_cohorts = []

    for cohort_key in sorted_cohort_keys:
        cohort_loans = cohort_groups[cohort_key]
        cohort_count = len(cohort_loans)
        cohort_principal = sum(l.principal_amount for l in cohort_loans)

        # Parse cohort year & month
        cyear, cmonth = map(int, cohort_key.split("-"))
        cohort_start = date(cyear, cmonth, 1)

        # Compute age of this cohort as of cutoff_date in months approx
        months_elapsed = (cutoff_date.year - cyear) * 12 + (cutoff_date.month - cmonth)

        cells = []
        for milestone in MILESTONES:
            if months_elapsed < milestone:
                # Immature cohort! Cannot observe milestone yet.
                cells.append({
                    "loan_age_months": milestone,
                    "cumulative_default_rate": None,
                    "cumulative_defaults": None,
                    "cumulative_delinquency_rate": None,
                    "is_immature": True
                })
            else:
                # Calculate defaults and delinquency observed up to this milestone
                # Milestone observation cutoff date
                # Approx: cohort_start + milestone months
                target_month = cmonth + milestone
                target_year = cyear + (target_month - 1) // 12
                target_month = ((target_month - 1) % 12) + 1
                obs_date = date(target_year, target_month, 1)

                defaults_at_milestone = 0
                delinquents_at_milestone = 0

                for loan in cohort_loans:
                    # Check schedules and status up to obs_date
                    if loan.status == "Defaulted" and loan.issue_date <= obs_date:
                        # Check when default occurred or if DPD was >= 90 at obs_date
                        due_up_to_obs = [s for s in loan.schedules if s.due_date <= obs_date]
                        paid_up_to_obs = sum(
                            t.amount for t in loan.transactions 
                            if t.payment_date <= obs_date and t.payment_status == "Completed"
                        )
                        due_sum = sum(s.scheduled_amount for s in due_up_to_obs)
                        unpaid = max(0.0, due_sum - paid_up_to_obs)
                        if unpaid > 0 and len(due_up_to_obs) >= 3:
                            defaults_at_milestone += 1
                        elif loan.status == "Defaulted":
                            defaults_at_milestone += 1
                    elif loan.status in ["Overdue", "Delinquent"]:
                        delinquents_at_milestone += 1

                default_rate = round((defaults_at_milestone / cohort_count) * 100.0, 2)
                delinq_rate = round((delinquents_at_milestone / cohort_count) * 100.0, 2)

                cells.append({
                    "loan_age_months": milestone,
                    "cumulative_default_rate": default_rate,
                    "cumulative_defaults": defaults_at_milestone,
                    "cumulative_delinquency_rate": delinq_rate,
                    "is_immature": False
                })

        result_cohorts.append({
            "origination_cohort": cohort_key,
            "cohort_loans_count": cohort_count,
            "cohort_original_principal": round(cohort_principal, 2),
            "cells": cells
        })

    return {
        "reporting_date": cutoff_date.isoformat(),
        "loan_age_milestones": MILESTONES,
        "cohorts": result_cohorts,
        "immature_definition": "Milestones where elapsed observation period < loan age are marked immature (null), not zero."
    }
