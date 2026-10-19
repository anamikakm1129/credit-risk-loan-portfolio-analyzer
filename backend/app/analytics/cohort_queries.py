from datetime import date
from typing import Dict, Any, List, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.app.models import Borrower, Loan, RiskAssessment, RiskRuleSet
from backend.app.services.repayment_analysis import calculate_loan_repayment_state

SCORE_BANDS = [
    {"name": "Super Prime (750-850)", "min": 750, "max": 850},
    {"name": "Prime (700-749)", "min": 700, "max": 749},
    {"name": "Near Prime (650-699)", "min": 650, "max": 699},
    {"name": "Subprime (580-649)", "min": 580, "max": 649},
    {"name": "Deep Subprime (300-579)", "min": 300, "max": 579},
]

def get_credit_score_band_comparisons(db: Session, cutoff_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Compares borrower counts, exposure, overdue amount, and default rates across standard FICO score bands.
    """
    if cutoff_date is None:
        cutoff_date = date.today()

    borrowers = db.query(Borrower).all()
    results = []

    for band in SCORE_BANDS:
        b_in_band = [
            b for b in borrowers 
            if b.credit_score is not None and band["min"] <= b.credit_score <= band["max"]
        ]

        b_count = len(b_in_band)
        all_loans = [l for b in b_in_band for l in b.loans]
        loan_count = len(all_loans)

        total_principal = sum(l.principal_amount for l in all_loans)
        outstanding = sum(l.outstanding_principal for l in all_loans if l.status != "Settled")

        overdue_total = 0.0
        defaults = 0
        total_due = 0.0
        total_paid = 0.0
        dti_values = [b.dti_ratio for b in b_in_band if b.dti_ratio is not None]

        for l in all_loans:
            rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff_date)
            overdue_total += rep["overdue_amount"]
            total_due += rep["total_due"]
            total_paid += rep["total_paid"]
            if l.status == "Defaulted" or rep["days_past_due"] >= 90:
                defaults += 1

        default_rate = (defaults / loan_count * 100.0) if loan_count > 0 else 0.0
        repayment_rate = (total_paid / total_due * 100.0) if total_due > 0 else 100.0
        avg_dti = (sum(dti_values) / len(dti_values)) if dti_values else 0.0

        results.append({
            "band_name": band["name"],
            "score_min": band["min"],
            "score_max": band["max"],
            "borrower_count": b_count,
            "total_loans": loan_count,
            "total_principal": round(total_principal, 2),
            "outstanding_principal": round(outstanding, 2),
            "overdue_amount": round(overdue_total, 2),
            "default_rate": round(default_rate, 2),
            "repayment_rate": round(min(100.0, repayment_rate), 2),
            "avg_dti": round(avg_dti, 1)
        })

    return results

def get_portfolio_monthly_trends(db: Session, cutoff_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Returns monthly time-series of loan origination, outstanding balance, overdue amount and repayment rate.
    """
    if cutoff_date is None:
        cutoff_date = date.today()

    loans = db.query(Loan).all()
    months_data = defaultdict(lambda: {
        "count": 0, "originated": 0.0, "outstanding": 0.0, "overdue": 0.0, "defaults": 0, "due": 0.0, "paid": 0.0
    })

    for l in loans:
        m_key = l.issue_date.strftime("%Y-%m")
        months_data[m_key]["count"] += 1
        months_data[m_key]["originated"] += l.principal_amount
        if l.status != "Settled":
            months_data[m_key]["outstanding"] += l.outstanding_principal

        rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff_date)
        months_data[m_key]["overdue"] += rep["overdue_amount"]
        months_data[m_key]["due"] += rep["total_due"]
        months_data[m_key]["paid"] += rep["total_paid"]
        if l.status == "Defaulted" or rep["days_past_due"] >= 90:
            months_data[m_key]["defaults"] += 1

    trends = []
    for m in sorted(months_data.keys()):
        d = months_data[m]
        rep_rate = (d["paid"] / d["due"] * 100.0) if d["due"] > 0 else 100.0
        trends.append({
            "period": m,
            "loan_count": d["count"],
            "originated_amount": round(d["originated"], 2),
            "outstanding_principal": round(d["outstanding"], 2),
            "overdue_amount": round(d["overdue"], 2),
            "default_count": d["defaults"],
            "repayment_rate": round(min(100.0, rep_rate), 1)
        })

    return trends

def get_risk_segments_distribution(db: Session, cutoff_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Aggregates borrower counts, monetary exposure, and average metrics grouped by risk band.
    """
    if cutoff_date is None:
        cutoff_date = date.today()

    borrowers = db.query(Borrower).all()
    active_rule = db.query(RiskRuleSet).filter(RiskRuleSet.active == True).first()
    rule_version = active_rule.version if active_rule else "v1.0"
    effective_date = active_rule.effective_from.isoformat() if active_rule else "2026-01-01"

    band_groups = defaultdict(list)
    total_exposure = 0.0

    for b in borrowers:
        latest_assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.borrower_id == b.borrower_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .first()
        )
        band = latest_assessment.risk_band if latest_assessment else "Medium"
        band_groups[band].append(b)

    total_borrowers = len(borrowers)
    segments = []

    for band_name in ["Low", "Medium", "High", "Review Required"]:
        b_list = band_groups[band_name]
        b_count = len(b_list)
        b_share = (b_count / total_borrowers * 100.0) if total_borrowers > 0 else 0.0

        all_loans = [l for b in b_list for l in b.loans]
        band_exposure = sum(l.outstanding_principal for l in all_loans if l.status != "Settled")
        total_exposure += band_exposure

        dti_vals = [b.dti_ratio for b in b_list if b.dti_ratio is not None]
        score_vals = [b.credit_score for b in b_list if b.credit_score is not None]

        overdue_sum = 0.0
        defaults = 0
        for l in all_loans:
            rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff_date)
            overdue_sum += rep["overdue_amount"]
            if l.status == "Defaulted" or rep["days_past_due"] >= 90:
                defaults += 1

        def_rate = (defaults / len(all_loans) * 100.0) if all_loans else 0.0

        segments.append({
            "risk_band": band_name,
            "borrower_count": b_count,
            "borrower_share_pct": round(b_share, 1),
            "total_exposure": round(band_exposure, 2),
            "exposure_share_pct": 0.0, # calculated below once total is known
            "avg_dti": round(sum(dti_vals)/len(dti_vals), 1) if dti_vals else 0.0,
            "avg_credit_score": round(sum(score_vals)/len(score_vals), 0) if score_vals else 0.0,
            "overdue_amount": round(overdue_sum, 2),
            "default_rate": round(def_rate, 2)
        })

    # Compute exposure shares
    for s in segments:
        s["exposure_share_pct"] = round((s["total_exposure"] / total_exposure * 100.0), 1) if total_exposure > 0 else 0.0

    return {
        "rule_version": rule_version,
        "rule_effective_date": effective_date,
        "total_borrowers": total_borrowers,
        "total_exposure": round(total_exposure, 2),
        "segments": segments
    }
