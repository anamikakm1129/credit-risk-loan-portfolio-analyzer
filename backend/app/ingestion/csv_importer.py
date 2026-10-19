import io
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from backend.app.models import Borrower, Loan, RepaymentSchedule, RepaymentTransaction, DataQualityRun, RiskAssessment
from backend.app.ingestion.validation import validate_borrowers_data, validate_loans_data
from backend.app.services.risk_rules import evaluate_risk, BorrowerRiskFeatures

def import_portfolio_csvs(
    db: Session,
    borrowers_csv_content: str,
    loans_csv_content: str,
    schedules_csv_content: str = None,
    transactions_csv_content: str = None
) -> Dict[str, Any]:
    """
    Parses and ingests portfolio data with strict schema validation.
    Generates a DataQualityRun record and returns import audit statistics.
    """
    start_time = datetime.utcnow()
    total_read = 0
    total_rejected = 0
    all_issues = []

    # 1. Ingest Borrowers
    borrower_records = []
    if borrowers_csv_content:
        df_b = pd.read_csv(io.StringIO(borrowers_csv_content))
        total_read += len(df_b)
        b_dicts = df_b.to_dict(orient="records")
        valid_b, rej_b, b_issues = validate_borrowers_data(b_dicts)
        total_rejected += len(rej_b)
        all_issues.extend(b_issues)

        for row in valid_b:
            b_id = str(row["borrower_id"]).strip()
            # Upsert borrower
            b = db.query(Borrower).filter(Borrower.borrower_id == b_id).first()
            if not b:
                b = Borrower(borrower_id=b_id)
                db.add(b)
            
            b.full_name = str(row.get("full_name", f"Borrower {b_id}"))
            b.annual_income = float(row["annual_income"]) if pd.notna(row.get("annual_income")) else None
            b.credit_score = int(row["credit_score"]) if pd.notna(row.get("credit_score")) else None
            b.monthly_debt_obligations = float(row["monthly_debt_obligations"]) if pd.notna(row.get("monthly_debt_obligations")) else None
            b.employment_status = str(row.get("employment_status", "Employed"))
            b.home_ownership = str(row.get("home_ownership", "MORTGAGE"))
            borrower_records.append(b)

        db.flush()

    # 2. Ingest Loans
    existing_b_ids = set(r[0] for r in db.query(Borrower.borrower_id).all())
    loan_records = []

    if loans_csv_content:
        df_l = pd.read_csv(io.StringIO(loans_csv_content))
        total_read += len(df_l)
        l_dicts = df_l.to_dict(orient="records")
        valid_l, rej_l, l_issues = validate_loans_data(l_dicts, existing_b_ids)
        total_rejected += len(rej_l)
        all_issues.extend(l_issues)

        for row in valid_l:
            l_id = str(row["loan_id"]).strip()
            l = db.query(Loan).filter(Loan.loan_id == l_id).first()
            if not l:
                l = Loan(loan_id=l_id)
                db.add(l)

            l.borrower_id = str(row["borrower_id"]).strip()
            l.principal_amount = float(row["principal_amount"])
            l.issue_date = datetime.strptime(str(row["issue_date"]).strip(), "%Y-%m-%d").date()
            l.term_months = int(row.get("term_months", 36))
            l.annual_rate = float(row.get("annual_rate", 0.089))
            l.status = str(row.get("status", "Active"))
            l.outstanding_principal = float(row.get("outstanding_principal", row["principal_amount"]))
            l.purpose = str(row.get("purpose", "Debt Consolidation"))
            loan_records.append(l)

        db.flush()

    # 3. Assess risk for all updated borrowers
    for b in borrower_records:
        features = BorrowerRiskFeatures(
            borrower_id=b.borrower_id,
            annual_income=b.annual_income,
            monthly_debt=b.monthly_debt_obligations,
            credit_score=b.credit_score,
            max_overdue_days=0,
            total_overdue_amount=0.0
        )
        assessment = evaluate_risk(features)
        
        # Save assessment
        risk_record = RiskAssessment(
            borrower_id=b.borrower_id,
            assessed_at=datetime.utcnow(),
            rule_set_id=1,
            risk_band=assessment.risk_band,
            risk_score=assessment.risk_score,
            factors_json=assessment.to_dict()["factors"]
        )
        db.add(risk_record)

    # 4. Record DataQualityRun
    completed_time = datetime.utcnow()
    run_status = "Success" if total_rejected == 0 else ("Partial" if len(borrower_records) > 0 else "Failed")

    dq_run = DataQualityRun(
        started_at=start_time,
        completed_at=completed_time,
        records_read=total_read,
        records_rejected=total_rejected,
        status=run_status,
        issue_summary=all_issues[:100] # store top 100 issues
    )
    db.add(dq_run)
    db.commit()

    return {
        "run_id": dq_run.run_id,
        "status": run_status,
        "records_read": total_read,
        "records_accepted": total_read - total_rejected,
        "records_rejected": total_rejected,
        "issues_count": len(all_issues),
        "sample_issues": all_issues[:10]
    }

