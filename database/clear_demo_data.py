import sqlite3
import os
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models import (
    Borrower, Loan, RepaymentSchedule, RepaymentTransaction,
    RiskAssessment, DataQualityRun, ReportRun, RiskRuleSet
)
from datetime import date

def clear_all_demo_data():
    db = SessionLocal()
    print("Clearing all demo borrowers, loans, repayments, assessments, and reports...")
    
    # Delete dependent child tables first
    db.query(RepaymentTransaction).delete()
    db.query(RepaymentSchedule).delete()
    db.query(Loan).delete()
    db.query(RiskAssessment).delete()
    db.query(ReportRun).delete()
    db.query(DataQualityRun).delete()
    db.query(Borrower).delete()
    
    # Ensure active ruleset exists
    rule = db.query(RiskRuleSet).filter(RiskRuleSet.active == True).first()
    if not rule:
        active_rule = RiskRuleSet(
            version="v1.0",
            effective_from=date(2026, 1, 1),
            effective_to=None,
            configuration={
                "high_dti_pct": 43.0,
                "low_score_threshold": 620,
                "overdue_days_threshold": 30,
                "high_dti_weight": 35.0,
                "low_score_weight": 40.0,
                "overdue_weight": 45.0,
                "medium_threshold": 25.0,
                "high_threshold": 50.0
            },
            active=True,
            description="Standard Baseline Risk Ruleset v1.0 — 2026 Policy"
        )
        db.add(active_rule)

    db.commit()
    db.close()
    print("All demo data removed successfully. Database is clean and ready for user upload.")

if __name__ == "__main__":
    clear_all_demo_data()
