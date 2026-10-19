from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from backend.app.core.database import get_db
from backend.app.models import Borrower, Loan, RepaymentSchedule, DataQualityRun
from backend.app.ingestion.csv_importer import import_portfolio_csvs

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])

@router.get("/latest")
def get_latest_data_quality_run(db: Session = Depends(get_db)):
    """
    Returns latest data quality audit run.
    """
    latest = db.query(DataQualityRun).order_by(DataQualityRun.completed_at.desc()).first()
    if not latest:
        # Run a diagnostic check on existing database
        return run_database_diagnostics(db)

    return {
        "run_id": latest.run_id,
        "evaluated_at": latest.completed_at.isoformat() if latest.completed_at else latest.started_at.isoformat(),
        "status": latest.status,
        "total_records_checked": latest.records_read,
        "records_rejected": latest.records_rejected,
        "issues": latest.issue_summary or []
    }

@router.post("/run-diagnostics")
def run_database_diagnostics(db: Session = Depends(get_db)):
    """
    Scans the current database for data health:
    - Missing required fields (credit score, income)
    - Out of range credit scores (<300 or >850)
    - Negative principal, interest or income
    - Orphan loans
    """
    borrowers = db.query(Borrower).all()
    loans = db.query(Loan).all()
    issues = []

    # Check borrowers
    missing_scores = 0
    missing_incomes = 0
    invalid_scores = 0

    for b in borrowers:
        if b.credit_score is None:
            missing_scores += 1
            issues.append({
                "issue_type": "Missing Critical Input",
                "entity": "Borrower",
                "record_id": b.borrower_id,
                "field": "credit_score",
                "description": f"Borrower {b.borrower_id} ({b.full_name}) has missing credit score. Flagged for review.",
                "severity": "Warning"
            })
        elif b.credit_score < 300 or b.credit_score > 850:
            invalid_scores += 1
            issues.append({
                "issue_type": "Invalid Value",
                "entity": "Borrower",
                "record_id": b.borrower_id,
                "field": "credit_score",
                "description": f"Score {b.credit_score} out of valid [300, 850] range",
                "severity": "Critical"
            })

        if b.annual_income is None or b.annual_income <= 0:
            missing_incomes += 1
            issues.append({
                "issue_type": "Missing Critical Input",
                "entity": "Borrower",
                "record_id": b.borrower_id,
                "field": "annual_income",
                "description": f"Borrower {b.borrower_id} income missing or zero.",
                "severity": "Warning"
            })

    # Check loans
    b_ids = set(b.borrower_id for b in borrowers)
    for l in loans:
        if l.borrower_id not in b_ids:
            issues.append({
                "issue_type": "Orphan Loan Record",
                "entity": "Loan",
                "record_id": l.loan_id,
                "field": "borrower_id",
                "description": f"Loan {l.loan_id} links to unknown borrower {l.borrower_id}",
                "severity": "Critical"
            })
        if l.principal_amount <= 0:
            issues.append({
                "issue_type": "Invalid Value",
                "entity": "Loan",
                "record_id": l.loan_id,
                "field": "principal_amount",
                "description": f"Loan {l.loan_id} has invalid non-positive principal",
                "severity": "Critical"
            })

    total_records = len(borrowers) + len(loans)
    flagged_records = len(issues)
    status = "Success" if flagged_records == 0 else "Warning"

    run_record = DataQualityRun(
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        records_read=total_records,
        records_rejected=0,
        status=status,
        issue_summary=issues
    )
    db.add(run_record)
    db.commit()

    return {
        "run_id": run_record.run_id,
        "evaluated_at": run_record.completed_at.isoformat(),
        "status": status,
        "total_records_checked": total_records,
        "clean_records_count": total_records - flagged_records,
        "flagged_records_count": flagged_records,
        "missing_credit_scores_count": missing_scores,
        "missing_incomes_count": missing_incomes,
        "issues": issues
    }

@router.post("/upload")
async def upload_csv_files(
    borrowers_file: Optional[UploadFile] = File(None),
    loans_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Accepts CSV uploads for borrowers and loans, validates and ingests into database.
    """
    b_content = None
    l_content = None

    if borrowers_file:
        b_content = (await borrowers_file.read()).decode("utf-8")
    if loans_file:
        l_content = (await loans_file.read()).decode("utf-8")

    if not b_content and not l_content:
        raise HTTPException(status_code=400, detail="Must provide at least borrowers_file or loans_file")

    result = import_portfolio_csvs(db, borrowers_csv_content=b_content, loans_csv_content=l_content)
    return result
