from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models import Borrower, Loan, RiskRuleSet, RiskAssessment
from backend.app.analytics.cohort_queries import get_risk_segments_distribution
from backend.app.services.risk_rules import (
    RiskRuleConfig, evaluate_risk, BorrowerRiskFeatures, DEFAULT_RULE_SET
)
from backend.app.services.repayment_analysis import calculate_loan_repayment_state

router = APIRouter(prefix="/risk", tags=["Risk Analysis"])

@router.get("/segments")
def get_risk_segments(
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns counts and monetary exposure aggregated by risk band with explicit denominators.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()
    return get_risk_segments_distribution(db, cutoff_date=cutoff)

@router.get("/rules")
def get_risk_rules(db: Session = Depends(get_db)):
    """
    Returns the currently active risk rule set and its parameters.
    """
    rule = db.query(RiskRuleSet).filter(RiskRuleSet.active == True).first()
    if not rule:
        return DEFAULT_RULE_SET.to_dict()

    return {
        "rule_set_id": rule.rule_set_id,
        "version": rule.version,
        "effective_from": rule.effective_from.isoformat(),
        "effective_to": rule.effective_to.isoformat() if rule.effective_to else None,
        "configuration": rule.configuration,
        "active": rule.active,
        "description": rule.description
    }

@router.post("/simulate")
def simulate_risk_rules(
    high_dti_pct: float = Body(43.0),
    low_score_threshold: int = Body(620),
    overdue_days_threshold: int = Body(30),
    high_dti_weight: float = Body(35.0),
    low_score_weight: float = Body(40.0),
    overdue_weight: float = Body(45.0),
    medium_threshold: float = Body(25.0),
    high_threshold: float = Body(50.0),
    reporting_date: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Simulates segment distribution changes if rule thresholds or weights are adjusted.
    Enables portfolio analysts to stress-test policy boundaries.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()

    sim_config = RiskRuleConfig(
        version="v-simulated",
        high_dti_pct=high_dti_pct,
        low_score_threshold=low_score_threshold,
        overdue_days_threshold=overdue_days_threshold,
        high_dti_weight=high_dti_weight,
        low_score_weight=low_score_weight,
        overdue_weight=overdue_weight,
        medium_threshold=medium_threshold,
        high_threshold=high_threshold
    )

    borrowers = db.query(Borrower).all()
    band_counts = {"Low": 0, "Medium": 0, "High": 0, "Review Required": 0}
    band_exposure = {"Low": 0.0, "Medium": 0.0, "High": 0.0, "Review Required": 0.0}

    for b in borrowers:
        max_dpd = 0
        total_overdue = 0.0
        exposure = 0.0
        for l in b.loans:
            rep = calculate_loan_repayment_state(l.schedules, l.transactions, cutoff)
            total_overdue += rep["overdue_amount"]
            max_dpd = max(max_dpd, rep["days_past_due"])
            if l.status != "Settled":
                exposure += l.outstanding_principal

        features = BorrowerRiskFeatures(
            borrower_id=b.borrower_id,
            annual_income=b.annual_income,
            monthly_debt=b.monthly_debt_obligations,
            credit_score=b.credit_score,
            max_overdue_days=max_dpd,
            total_overdue_amount=total_overdue,
            active_loans_count=len([l for l in b.loans if l.status != "Settled"])
        )
        result = evaluate_risk(features, rules=sim_config)
        band_counts[result.risk_band] += 1
        band_exposure[result.risk_band] += exposure

    total_b = len(borrowers)
    total_exp = sum(band_exposure.values())

    return {
        "simulation_parameters": sim_config.to_dict(),
        "total_borrowers": total_b,
        "total_exposure": round(total_exp, 2),
        "results": [
            {
                "risk_band": band,
                "borrower_count": band_counts[band],
                "borrower_share_pct": round(band_counts[band] / total_b * 100.0, 1) if total_b > 0 else 0.0,
                "exposure_amount": round(band_exposure[band], 2),
                "exposure_share_pct": round(band_exposure[band] / total_exp * 100.0, 1) if total_exp > 0 else 0.0
            }
            for band in ["Low", "Medium", "High", "Review Required"]
        ]
    }

