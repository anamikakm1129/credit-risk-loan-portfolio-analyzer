from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

# Borrower schemas
class BorrowerBase(BaseModel):
    borrower_id: str
    full_name: str
    annual_income: Optional[float] = None
    credit_score: Optional[int] = None
    monthly_debt_obligations: Optional[float] = None
    employment_status: Optional[str] = "Employed"
    home_ownership: Optional[str] = "MORTGAGE"

class BorrowerSummary(BorrowerBase):
    dti_ratio: Optional[float] = None
    active_loans_count: int = 0
    total_exposure: float = 0.0
    total_overdue: float = 0.0
    risk_band: str = "Unknown"
    latest_status: str = "Active"

    class Config:
        from_attributes = True

class BorrowerDetail(BorrowerSummary):
    loans: List[Dict[str, Any]] = []
    risk_assessment: Optional[Dict[str, Any]] = None
    repayment_summary: Optional[Dict[str, Any]] = None

# Loan schemas
class LoanSummary(BaseModel):
    loan_id: str
    borrower_id: str
    borrower_name: Optional[str] = None
    principal_amount: float
    issue_date: date
    term_months: int
    annual_rate: float
    status: str
    outstanding_principal: float
    purpose: Optional[str] = None
    risk_band: Optional[str] = None

    class Config:
        from_attributes = True

class LoanDetail(LoanSummary):
    borrower: Optional[BorrowerBase] = None
    schedules: List[Dict[str, Any]] = []
    transactions: List[Dict[str, Any]] = []
    total_paid: float = 0.0
    total_due: float = 0.0
    overdue_amount: float = 0.0
    days_past_due: int = 0

# Repayments
class RepaymentScheduleItem(BaseModel):
    schedule_id: int
    loan_id: str
    installment_number: int
    due_date: date
    scheduled_amount: float
    principal_due: float
    interest_due: float
    status: str

    class Config:
        from_attributes = True

class RepaymentTransactionItem(BaseModel):
    payment_id: str
    loan_id: str
    schedule_id: Optional[int] = None
    payment_date: date
    amount: float
    payment_status: str
    reference: Optional[str] = None

    class Config:
        from_attributes = True

# Dashboard
class KPICard(BaseModel):
    label: str
    value: float
    formatted_value: str
    definition: str
    period: str
    change_pct: Optional[float] = None
    trend_direction: Optional[str] = None # up, down, flat

class DashboardSummaryResponse(BaseModel):
    reporting_date: str
    total_loans: KPICard
    outstanding_principal: KPICard
    default_rate: KPICard
    overdue_amount: KPICard
    repayment_rate: KPICard
    weighted_avg_dti: KPICard
    weighted_avg_credit_score: KPICard
    active_borrowers_count: int
    active_rule_version: str

class TrendPoint(BaseModel):
    period: str # "2025-01"
    loan_count: int
    originated_amount: float
    outstanding_principal: float
    overdue_amount: float
    default_count: int
    repayment_rate: float

class DashboardTrendsResponse(BaseModel):
    monthly_trends: List[TrendPoint]

# Risk Engine
class RiskFactors(BaseModel):
    reasons: List[str]
    missing_inputs: List[str]
    contributing_weights: Dict[str, float]
    dti_snapshot: Optional[float] = None
    credit_score_snapshot: Optional[int] = None
    overdue_days_snapshot: int = 0

class RiskAssessmentResponse(BaseModel):
    borrower_id: str
    risk_band: str # Low, Medium, High, Review Required
    risk_score: float
    rule_version: str
    assessed_at: str
    factors: RiskFactors
    plain_language_explanation: str

class RiskSimulationRequest(BaseModel):
    high_dti_threshold: float = 43.0
    low_credit_score_threshold: int = 620
    overdue_days_threshold: int = 30
    high_dti_weight: float = 35.0
    low_score_weight: float = 40.0
    overdue_weight: float = 45.0

class RiskDistributionItem(BaseModel):
    risk_band: str
    borrower_count: int
    borrower_share_pct: float
    total_exposure: float
    exposure_share_pct: float
    avg_dti: float
    avg_credit_score: float
    overdue_amount: float
    default_rate: float

class RiskSegmentsResponse(BaseModel):
    rule_version: str
    rule_effective_date: str
    total_borrowers: int
    total_exposure: float
    segments: List[RiskDistributionItem]

# Vintage analysis
class VintageCell(BaseModel):
    loan_age_months: int # 1, 3, 6, 9, 12, 18, 24
    cumulative_default_rate: Optional[float] = None # None means immature / not observable
    cumulative_defaults: Optional[int] = None
    cumulative_delinquency_rate: Optional[float] = None
    is_immature: bool

class VintageCohortRow(BaseModel):
    origination_cohort: str # "2025-01"
    cohort_loans_count: int
    cohort_original_principal: float
    cells: List[VintageCell]

class VintageAnalysisResponse(BaseModel):
    reporting_date: str
    loan_age_milestones: List[int]
    cohorts: List[VintageCohortRow]
    immature_definition: str

# Credit Score Bands
class ScoreBandComparisonItem(BaseModel):
    band_name: str # e.g. "Excellent (750+)", "Good (700-749)", etc.
    score_min: int
    score_max: int
    borrower_count: int
    total_loans: int
    total_principal: float
    outstanding_principal: float
    overdue_amount: float
    default_rate: float
    repayment_rate: float
    avg_dti: float

# Reports
class ReportGenerationRequest(BaseModel):
    user_id: Optional[str] = "analyst@credvista.internal"
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    risk_bands: Optional[List[str]] = None
    loan_statuses: Optional[List[str]] = None
    notes: Optional[str] = None

class ReportRunResponse(BaseModel):
    report_id: str
    generated_at: str
    user_id: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    filters: Dict[str, Any]
    metric_version: str
    portfolio_summary: Dict[str, Any]
    download_url: Optional[str] = None

# Data quality
class DataQualityIssue(BaseModel):
    issue_type: str # Missing Field, Duplicate ID, Invalid Value, Orphan FK, Out of Range
    entity: str # Borrower, Loan, Repayment
    record_id: str
    field: str
    description: str
    severity: str # Warning, Critical

class DataQualitySummaryResponse(BaseModel):
    run_id: int
    evaluated_at: str
    status: str # Success, Partial, Failed
    total_records_checked: int
    clean_records_count: int
    flagged_records_count: int
    duplicate_ids_count: int
    missing_required_fields_count: int
    invalid_numeric_values_count: int
    issues: List[DataQualityIssue]

