from sqlalchemy import Column, Integer, String, Float, Numeric, Date, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, date
from backend.app.core.database import Base

class Borrower(Base):
    __tablename__ = "borrowers"

    borrower_id = Column(String(50), primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    annual_income = Column(Float, nullable=True)
    credit_score = Column(Integer, nullable=True, index=True)
    monthly_debt_obligations = Column(Float, nullable=True)
    employment_status = Column(String(50), default="Employed")
    home_ownership = Column(String(50), default="MORTGAGE")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    loans = relationship("Loan", back_populates="borrower", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="borrower", cascade="all, delete-orphan")

    @property
    def dti_ratio(self) -> float:
        """
        DTI = (Monthly Debt / Gross Monthly Income) * 100
        Returns None or 0.0 if income is missing or zero.
        """
        if self.annual_income and self.annual_income > 0 and self.monthly_debt_obligations is not None:
            monthly_income = self.annual_income / 12.0
            return round((self.monthly_debt_obligations / monthly_income) * 100.0, 2)
        return None

class Loan(Base):
    __tablename__ = "loans"

    loan_id = Column(String(50), primary_key=True, index=True)
    borrower_id = Column(String(50), ForeignKey("borrowers.borrower_id"), nullable=False, index=True)
    principal_amount = Column(Float, nullable=False)
    issue_date = Column(Date, nullable=False, index=True)
    term_months = Column(Integer, nullable=False)
    annual_rate = Column(Float, nullable=False) # e.g. 0.089 for 8.9%
    status = Column(String(30), nullable=False, index=True) # Active, Overdue, Delinquent, Defaulted, Settled
    outstanding_principal = Column(Float, nullable=False)
    purpose = Column(String(100), default="General Purpose")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    borrower = relationship("Borrower", back_populates="loans")
    schedules = relationship("RepaymentSchedule", back_populates="loan", cascade="all, delete-orphan", order_by="RepaymentSchedule.due_date")
    transactions = relationship("RepaymentTransaction", back_populates="loan", cascade="all, delete-orphan", order_by="RepaymentTransaction.payment_date")

class RepaymentSchedule(Base):
    __tablename__ = "repayment_schedule"

    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(String(50), ForeignKey("loans.loan_id"), nullable=False, index=True)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    scheduled_amount = Column(Float, nullable=False)
    principal_due = Column(Float, nullable=False)
    interest_due = Column(Float, nullable=False)
    status = Column(String(30), default="Pending") # Pending, Paid, Partially Paid, Overdue

    # Relationships
    loan = relationship("Loan", back_populates="schedules")
    transactions = relationship("RepaymentTransaction", back_populates="schedule")

class RepaymentTransaction(Base):
    __tablename__ = "repayment_transactions"

    payment_id = Column(String(50), primary_key=True, index=True)
    loan_id = Column(String(50), ForeignKey("loans.loan_id"), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey("repayment_schedule.schedule_id"), nullable=True)
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_status = Column(String(30), default="Completed") # Completed, Pending, Failed
    reference = Column(String(100), nullable=True)

    # Relationships
    loan = relationship("Loan", back_populates="transactions")
    schedule = relationship("RepaymentSchedule", back_populates="transactions")

class RiskRuleSet(Base):
    __tablename__ = "risk_rule_sets"

    rule_set_id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(20), nullable=False, unique=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    configuration = Column(JSON, nullable=False) # thresholds and weights
    active = Column(Boolean, default=True, index=True)
    description = Column(String(255), nullable=True)

    # Relationships
    assessments = relationship("RiskAssessment", back_populates="rule_set")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    assessment_id = Column(Integer, primary_key=True, autoincrement=True)
    borrower_id = Column(String(50), ForeignKey("borrowers.borrower_id"), nullable=False, index=True)
    assessed_at = Column(DateTime, default=datetime.utcnow, index=True)
    rule_set_id = Column(Integer, ForeignKey("risk_rule_sets.rule_set_id"), nullable=False)
    risk_band = Column(String(30), nullable=False, index=True) # Low, Medium, High, Review Required
    risk_score = Column(Float, nullable=False)
    factors_json = Column(JSON, nullable=False) # reason codes, details, missing inputs

    # Relationships
    borrower = relationship("Borrower", back_populates="risk_assessments")
    rule_set = relationship("RiskRuleSet", back_populates="assessments")

class DataQualityRun(Base):
    __tablename__ = "data_quality_runs"

    run_id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    records_read = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    status = Column(String(30), default="Success") # Success, Partial, Failed
    issue_summary = Column(JSON, nullable=False) # list of validation issues found

class ReportRun(Base):
    __tablename__ = "report_runs"

    report_id = Column(String(50), primary_key=True, index=True)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(50), default="analyst@credvista.internal")
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    filters_json = Column(JSON, nullable=True)
    metric_version = Column(String(20), default="v1.0")
    summary_json = Column(JSON, nullable=False)
    file_reference = Column(String(255), nullable=True)
