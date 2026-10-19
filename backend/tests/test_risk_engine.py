import pytest
from backend.app.services.risk_rules import (
    RiskRuleConfig, evaluate_risk, BorrowerRiskFeatures
)

def test_missing_credit_score_triggers_review_required():
    """Missing critical input must NOT silently default to Low risk."""
    features = BorrowerRiskFeatures(
        borrower_id="TEST-001",
        annual_income=80000.0,
        monthly_debt=1000.0,
        credit_score=None, # Missing!
        max_overdue_days=0
    )
    result = evaluate_risk(features)
    assert result.risk_band == "Review Required"
    assert "Credit score missing" in result.missing_inputs
    assert "Review Required" in result.explanation

def test_missing_income_triggers_review_required():
    features = BorrowerRiskFeatures(
        borrower_id="TEST-002",
        annual_income=None, # Missing!
        monthly_debt=1000.0,
        credit_score=750,
        max_overdue_days=0
    )
    result = evaluate_risk(features)
    assert result.risk_band == "Review Required"
    assert "Verified annual income missing or zero" in result.missing_inputs

def test_prime_low_risk_classification():
    features = BorrowerRiskFeatures(
        borrower_id="TEST-003",
        annual_income=120000.0, # monthly $10k
        monthly_debt=2000.0, # DTI 20%
        credit_score=780,
        max_overdue_days=0
    )
    result = evaluate_risk(features)
    assert result.risk_band == "Low"
    assert result.risk_score == 0.0
    assert "Low Risk" in result.explanation

def test_high_risk_multiple_triggers():
    features = BorrowerRiskFeatures(
        borrower_id="TEST-004",
        annual_income=50000.0, # monthly ~$4166
        monthly_debt=2200.0, # DTI ~52.8% (>43%)
        credit_score=590, # (<620)
        max_overdue_days=35 # (>=30)
    )
    result = evaluate_risk(features)
    assert result.risk_band == "High"
    assert len(result.reasons) >= 3
    assert "High DTI" in result.weights_breakdown
    assert "Low Credit Score" in result.weights_breakdown
    assert "Delinquent Repayments" in result.weights_breakdown

def test_deterministic_reproducibility():
    """Identical inputs must yield identical assessments and scores."""
    f1 = BorrowerRiskFeatures("BRW-DUP", 70000.0, 2000.0, 670, 10, 300.0)
    f2 = BorrowerRiskFeatures("BRW-DUP", 70000.0, 2000.0, 670, 10, 300.0)
    
    r1 = evaluate_risk(f1)
    r2 = evaluate_risk(f2)

    assert r1.risk_band == r2.risk_band
    assert r1.risk_score == r2.risk_score
    assert r1.reasons == r2.reasons
