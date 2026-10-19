from typing import Dict, Any, List, Optional
from datetime import date, datetime

class RiskRuleConfig:
    def __init__(
        self,
        version: str = "v1.0",
        high_dti_pct: float = 43.0,
        low_score_threshold: int = 620,
        overdue_days_threshold: int = 30,
        high_dti_weight: float = 35.0,
        low_score_weight: float = 40.0,
        overdue_weight: float = 45.0,
        medium_threshold: float = 25.0,
        high_threshold: float = 50.0,
        effective_date: str = "2026-01-01"
    ):
        self.version = version
        self.high_dti_pct = high_dti_pct
        self.low_score_threshold = low_score_threshold
        self.overdue_days_threshold = overdue_days_threshold
        self.high_dti_weight = high_dti_weight
        self.low_score_weight = low_score_weight
        self.overdue_weight = overdue_weight
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold
        self.effective_date = effective_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "high_dti_pct": self.high_dti_pct,
            "low_score_threshold": self.low_score_threshold,
            "overdue_days_threshold": self.overdue_days_threshold,
            "high_dti_weight": self.high_dti_weight,
            "low_score_weight": self.low_score_weight,
            "overdue_weight": self.overdue_weight,
            "medium_threshold": self.medium_threshold,
            "high_threshold": self.high_threshold,
            "effective_date": self.effective_date
        }

DEFAULT_RULE_SET = RiskRuleConfig()

class BorrowerRiskFeatures:
    def __init__(
        self,
        borrower_id: str,
        annual_income: Optional[float],
        monthly_debt: Optional[float],
        credit_score: Optional[int],
        max_overdue_days: int = 0,
        total_overdue_amount: float = 0.0,
        active_loans_count: int = 0
    ):
        self.borrower_id = borrower_id
        self.annual_income = annual_income
        self.monthly_debt = monthly_debt
        self.credit_score = credit_score
        self.max_overdue_days = max_overdue_days
        self.total_overdue_amount = total_overdue_amount
        self.active_loans_count = active_loans_count

    @property
    def dti_pct(self) -> Optional[float]:
        if self.annual_income and self.annual_income > 0 and self.monthly_debt is not None:
            monthly_income = self.annual_income / 12.0
            return round((self.monthly_debt / monthly_income) * 100.0, 2)
        return None

    @property
    def missing_critical_inputs(self) -> List[str]:
        missing = []
        if self.credit_score is None:
            missing.append("Credit score missing")
        if self.annual_income is None or self.annual_income <= 0:
            missing.append("Verified annual income missing or zero")
        if self.monthly_debt is None:
            missing.append("Monthly debt obligations missing")
        return missing

class RiskAssessmentResult:
    def __init__(
        self,
        borrower_id: str,
        risk_band: str,
        risk_score: float,
        reasons: List[str],
        missing_inputs: List[str],
        weights_breakdown: Dict[str, float],
        rule_version: str,
        assessed_at: str,
        explanation: str,
        dti_snapshot: Optional[float] = None,
        credit_score_snapshot: Optional[int] = None,
        overdue_days_snapshot: int = 0
    ):
        self.borrower_id = borrower_id
        self.risk_band = risk_band
        self.risk_score = risk_score
        self.reasons = reasons
        self.missing_inputs = missing_inputs
        self.weights_breakdown = weights_breakdown
        self.rule_version = rule_version
        self.assessed_at = assessed_at
        self.explanation = explanation
        self.dti_snapshot = dti_snapshot
        self.credit_score_snapshot = credit_score_snapshot
        self.overdue_days_snapshot = overdue_days_snapshot

    def to_dict(self) -> Dict[str, Any]:
        return {
            "borrower_id": self.borrower_id,
            "risk_band": self.risk_band,
            "risk_score": self.risk_score,
            "rule_version": self.rule_version,
            "assessed_at": self.assessed_at,
            "factors": {
                "reasons": self.reasons,
                "missing_inputs": self.missing_inputs,
                "contributing_weights": self.weights_breakdown,
                "dti_snapshot": self.dti_snapshot,
                "credit_score_snapshot": self.credit_score_snapshot,
                "overdue_days_snapshot": self.overdue_days_snapshot
            },
            "plain_language_explanation": self.explanation
        }

def evaluate_risk(features: BorrowerRiskFeatures, rules: Optional[RiskRuleConfig] = None) -> RiskAssessmentResult:
    """
    Deterministic rule-based risk evaluation according to CredVista PRD & TRD.
    Does NOT use opaque ML. Missing critical inputs trigger 'Review Required',
    never silently defaulting to Low risk.
    """
    if rules is None:
        rules = DEFAULT_RULE_SET

    assessed_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    missing_critical = features.missing_critical_inputs

    if missing_critical:
        explanation = (
            f"Borrower flagged for Review Required under rule {rules.version} due to missing critical input data: "
            + ", ".join(missing_critical)
            + ". Policy prohibits silent Low-risk default."
        )
        return RiskAssessmentResult(
            borrower_id=features.borrower_id,
            risk_band="Review Required",
            risk_score=999.0,
            reasons=["Critical data inputs missing for automated rule assessment"],
            missing_inputs=missing_critical,
            weights_breakdown={},
            rule_version=rules.version,
            assessed_at=assessed_time,
            explanation=explanation,
            dti_snapshot=features.dti_pct,
            credit_score_snapshot=features.credit_score,
            overdue_days_snapshot=features.max_overdue_days
        )

    score = 0.0
    reasons: List[str] = []
    weights: Dict[str, float] = {}

    # 1. Debt-To-Income check
    dti = features.dti_pct
    if dti is not None and dti >= rules.high_dti_pct:
        score += rules.high_dti_weight
        reasons.append(f"Elevated DTI of {dti}% exceeds {rules.high_dti_pct}% threshold")
        weights["High DTI"] = rules.high_dti_weight

    # 2. Credit score check
    if features.credit_score is not None and features.credit_score < rules.low_score_threshold:
        score += rules.low_score_weight
        reasons.append(f"Credit score {features.credit_score} is below policy threshold ({rules.low_score_threshold})")
        weights["Low Credit Score"] = rules.low_score_weight

    # 3. Delinquency / Overdue check
    if features.max_overdue_days >= rules.overdue_days_threshold:
        score += rules.overdue_weight
        reasons.append(f"Active repayment overdue by {features.max_overdue_days} days (threshold: {rules.overdue_days_threshold} days)")
        weights["Delinquent Repayments"] = rules.overdue_weight
    elif features.total_overdue_amount > 0:
        score += 15.0
        reasons.append(f"Unpaid balance past due: ${features.total_overdue_amount:,.2f}")
        weights["Minor Overdue Amount"] = 15.0

    # Band assignment
    if score >= rules.high_threshold or features.max_overdue_days >= 60:
        risk_band = "High"
    elif score >= rules.medium_threshold:
        risk_band = "Medium"
    else:
        risk_band = "Low"

    # Human-readable explanation
    if risk_band == "Low":
        explanation = (
            f"Assigned Low Risk (Score: {score:.1f}/{rules.high_threshold:.0f}, Rule {rules.version}). "
            f"Credit score ({features.credit_score}) meets prime criteria, DTI ({dti}%) is within bounds, "
            f"and repayments are on schedule."
        )
    elif risk_band == "Medium":
        explanation = (
            f"Assigned Medium Risk (Score: {score:.1f}/{rules.high_threshold:.0f}, Rule {rules.version}). "
            f"Key contributing factors: " + "; ".join(reasons) + "."
        )
    else:
        explanation = (
            f"Assigned High Risk (Score: {score:.1f}/{rules.high_threshold:.0f}, Rule {rules.version}). "
            f"Primary risk triggers: " + "; ".join(reasons) + "."
        )

    return RiskAssessmentResult(
        borrower_id=features.borrower_id,
        risk_band=risk_band,
        risk_score=score,
        reasons=reasons if reasons else ["No elevated risk factors detected"],
        missing_inputs=[],
        weights_breakdown=weights,
        rule_version=rules.version,
        assessed_at=assessed_time,
        explanation=explanation,
        dti_snapshot=dti,
        credit_score_snapshot=features.credit_score,
        overdue_days_snapshot=features.max_overdue_days
    )
