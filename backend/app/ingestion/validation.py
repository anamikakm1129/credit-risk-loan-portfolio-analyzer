from typing import List, Dict, Any, Tuple
from datetime import datetime, date

def validate_borrowers_data(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates borrower records.
    Returns: (valid_records, rejected_records, issues)
    """
    valid = []
    rejected = []
    issues = []
    seen_ids = set()

    for idx, row in enumerate(records):
        b_id = str(row.get("borrower_id", "")).strip()
        row_issues = []

        if not b_id or b_id == "nan":
            row_issues.append({
                "issue_type": "Missing Field",
                "entity": "Borrower",
                "record_id": f"Row #{idx+1}",
                "field": "borrower_id",
                "description": "borrower_id is mandatory",
                "severity": "Critical"
            })
        elif b_id in seen_ids:
            row_issues.append({
                "issue_type": "Duplicate ID",
                "entity": "Borrower",
                "record_id": b_id,
                "field": "borrower_id",
                "description": f"Duplicate borrower identifier: {b_id}",
                "severity": "Critical"
            })
        else:
            seen_ids.add(b_id)

        # Name check
        name = str(row.get("full_name", "")).strip()
        if not name or name == "nan":
            row_issues.append({
                "issue_type": "Missing Field",
                "entity": "Borrower",
                "record_id": b_id or f"Row #{idx+1}",
                "field": "full_name",
                "description": "Borrower full_name is missing",
                "severity": "Warning"
            })

        # Credit score validation
        score_val = row.get("credit_score")
        if score_val is not None and str(score_val).strip() not in ["", "nan"]:
            try:
                score = int(float(score_val))
                if score < 300 or score > 850:
                    row_issues.append({
                        "issue_type": "Invalid Value",
                        "entity": "Borrower",
                        "record_id": b_id,
                        "field": "credit_score",
                        "description": f"Credit score {score} outside valid range [300, 850]",
                        "severity": "Warning"
                    })
            except (ValueError, TypeError):
                row_issues.append({
                    "issue_type": "Invalid Value",
                    "entity": "Borrower",
                    "record_id": b_id,
                    "field": "credit_score",
                    "description": f"Non-numeric credit score: {score_val}",
                    "severity": "Warning"
                })

        # Income validation
        income_val = row.get("annual_income")
        if income_val is not None and str(income_val).strip() not in ["", "nan"]:
            try:
                inc = float(income_val)
                if inc < 0:
                    row_issues.append({
                        "issue_type": "Invalid Value",
                        "entity": "Borrower",
                        "record_id": b_id,
                        "field": "annual_income",
                        "description": f"Negative annual income: {inc}",
                        "severity": "Critical"
                    })
            except (ValueError, TypeError):
                row_issues.append({
                    "issue_type": "Invalid Value",
                    "entity": "Borrower",
                    "record_id": b_id,
                    "field": "annual_income",
                    "description": f"Non-numeric annual income: {income_val}",
                    "severity": "Critical"
                })

        has_critical = any(i["severity"] == "Critical" for i in row_issues)
        issues.extend(row_issues)

        if has_critical:
            rejected.append(row)
        else:
            valid.append(row)

    return valid, rejected, issues

def validate_loans_data(
    records: List[Dict[str, Any]], 
    existing_borrower_ids: set
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates loan records and checks foreign key linkage.
    """
    valid = []
    rejected = []
    issues = []
    seen_loan_ids = set()

    for idx, row in enumerate(records):
        loan_id = str(row.get("loan_id", "")).strip()
        row_issues = []

        if not loan_id or loan_id == "nan":
            row_issues.append({
                "issue_type": "Missing Field",
                "entity": "Loan",
                "record_id": f"Row #{idx+1}",
                "field": "loan_id",
                "description": "loan_id is mandatory",
                "severity": "Critical"
            })
        elif loan_id in seen_loan_ids:
            row_issues.append({
                "issue_type": "Duplicate ID",
                "entity": "Loan",
                "record_id": loan_id,
                "field": "loan_id",
                "description": f"Duplicate loan identifier: {loan_id}",
                "severity": "Critical"
            })
        else:
            seen_loan_ids.add(loan_id)

        # Borrower FK check
        b_id = str(row.get("borrower_id", "")).strip()
        if not b_id or b_id == "nan":
            row_issues.append({
                "issue_type": "Missing Field",
                "entity": "Loan",
                "record_id": loan_id,
                "field": "borrower_id",
                "description": "Loan is missing borrower_id FK",
                "severity": "Critical"
            })
        elif b_id not in existing_borrower_ids:
            row_issues.append({
                "issue_type": "Orphan FK",
                "entity": "Loan",
                "record_id": loan_id,
                "field": "borrower_id",
                "description": f"Referenced borrower {b_id} does not exist",
                "severity": "Critical"
            })

        # Principal amount
        try:
            principal = float(row.get("principal_amount", 0))
            if principal <= 0:
                row_issues.append({
                    "issue_type": "Invalid Value",
                    "entity": "Loan",
                    "record_id": loan_id,
                    "field": "principal_amount",
                    "description": f"Principal amount must be positive, got {principal}",
                    "severity": "Critical"
                })
        except (ValueError, TypeError):
            row_issues.append({
                "issue_type": "Invalid Value",
                "entity": "Loan",
                "record_id": loan_id,
                "field": "principal_amount",
                "description": "Non-numeric principal amount",
                "severity": "Critical"
            })

        # Issue date
        date_str = str(row.get("issue_date", "")).strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            row_issues.append({
                "issue_type": "Invalid Value",
                "entity": "Loan",
                "record_id": loan_id,
                "field": "issue_date",
                "description": f"Invalid issue date format '{date_str}', expected YYYY-MM-DD",
                "severity": "Critical"
            })

        has_critical = any(i["severity"] == "Critical" for i in row_issues)
        issues.extend(row_issues)

        if has_critical:
            rejected.append(row)
        else:
            valid.append(row)

    return valid, rejected, issues

