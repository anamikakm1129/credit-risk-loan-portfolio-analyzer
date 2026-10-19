import random
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models import (
    Borrower, Loan, RepaymentSchedule, RepaymentTransaction,
    RiskRuleSet, RiskAssessment, DataQualityRun, ReportRun
)
from backend.app.services.risk_rules import evaluate_risk, BorrowerRiskFeatures, RiskRuleConfig
from backend.app.services.repayment_analysis import calculate_loan_repayment_state

# Deterministic seed for reproducible testing
random.seed(42)

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell"
]

EMPLOYMENT_STATUSES = ["Employed", "Self-Employed", "Government", "Executive", "Professional"]
HOME_OWNERSHIPS = ["MORTGAGE", "RENT", "OWN"]
PURPOSES = [
    "Debt Consolidation", "Home Improvement", "Small Business Expansion",
    "Major Purchase", "Medical Expenses", "Vehicle Refinance", "Green Energy / Solar"
]

def seed_database():
    db = SessionLocal()
    print("Re-creating all database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 1. Active Risk Rule Set
    print("Creating active risk rules set v1.0...")
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
    db.flush()

    # 2. Seed 120 Borrowers
    print("Generating 120 realistic borrowers...")
    borrowers_list = []
    
    # Stratified credit score distribution:
    # 40% Super Prime (750+), 30% Prime (700-749), 18% Near Prime (650-699), 10% Subprime (580-649), 2% with missing data
    for i in range(1, 121):
        b_id = f"BRW-{1000 + i}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        
        # Determine segment
        rand_segment = random.random()
        if i in [23, 77]: # missing data intentionally for PR-10 & Review Required testing
            credit_score = None
            annual_income = random.choice([55000.0, 72000.0])
            monthly_debt = 1200.0
        elif i == 89: # missing income
            credit_score = 680
            annual_income = None
            monthly_debt = None
        elif rand_segment < 0.40: # Super Prime
            credit_score = random.randint(750, 830)
            annual_income = round(random.uniform(75000, 180000), -2)
            monthly_debt = round(annual_income / 12.0 * random.uniform(0.12, 0.32), 2)
        elif rand_segment < 0.70: # Prime
            credit_score = random.randint(700, 749)
            annual_income = round(random.uniform(55000, 125000), -2)
            monthly_debt = round(annual_income / 12.0 * random.uniform(0.25, 0.40), 2)
        elif rand_segment < 0.88: # Near Prime
            credit_score = random.randint(650, 699)
            annual_income = round(random.uniform(42000, 85000), -2)
            monthly_debt = round(annual_income / 12.0 * random.uniform(0.35, 0.48), 2)
        else: # Subprime
            credit_score = random.randint(540, 649)
            annual_income = round(random.uniform(30000, 65000), -2)
            monthly_debt = round(annual_income / 12.0 * random.uniform(0.42, 0.60), 2)

        borrower = Borrower(
            borrower_id=b_id,
            full_name=name,
            annual_income=annual_income,
            credit_score=credit_score,
            monthly_debt_obligations=monthly_debt,
            employment_status=random.choice(EMPLOYMENT_STATUSES),
            home_ownership=random.choice(HOME_OWNERSHIPS),
            created_at=datetime.utcnow() - timedelta(days=random.randint(100, 900))
        )
        db.add(borrower)
        borrowers_list.append(borrower)

    db.flush()

    # 3. Seed 180 Loans
    print("Generating 180 loans across cohorts from 2024 to 2026...")
    cohort_dates = [
        date(2024, 1, 15), date(2024, 4, 15), date(2024, 7, 15), date(2024, 10, 15),
        date(2025, 1, 15), date(2025, 4, 15), date(2025, 7, 15), date(2025, 10, 15),
        date(2026, 1, 15), date(2026, 4, 15), date(2026, 7, 15)
    ]
    
    current_cutoff = date(2026, 10, 19)
    loan_id_counter = 1001

    # Assign 1 to 2 loans per borrower
    for b in borrowers_list:
        num_loans = 2 if random.random() < 0.50 and b.borrower_id not in ["BRW-1023", "BRW-1077", "BRW-1089"] else 1
        for _ in range(num_loans):
            issue_date = random.choice(cohort_dates)
            term_months = random.choice([12, 24, 36, 48, 60])
            principal = round(random.uniform(4000, 50000), -2)
            
            # Risk-based pricing: lower score -> higher rate
            if b.credit_score is None:
                rate = 0.145
            elif b.credit_score >= 750:
                rate = round(random.uniform(0.059, 0.089), 3)
            elif b.credit_score >= 700:
                rate = round(random.uniform(0.089, 0.125), 3)
            elif b.credit_score >= 650:
                rate = round(random.uniform(0.125, 0.169), 3)
            else:
                rate = round(random.uniform(0.170, 0.239), 3)

            # Monthly payment formula: P * (r*(1+r)^n) / ((1+r)^n - 1)
            monthly_rate = rate / 12.0
            factor = (1 + monthly_rate) ** term_months
            monthly_payment = principal * (monthly_rate * factor) / (factor - 1)

            # Determine realistic performance status
            months_since_issue = (current_cutoff.year - issue_date.year) * 12 + (current_cutoff.month - issue_date.month)
            
            if months_since_issue >= term_months:
                # Fully matured
                if b.credit_score and b.credit_score < 620 and random.random() < 0.25:
                    status = "Defaulted"
                else:
                    status = "Settled"
            else:
                # Still active or delinquent
                if b.credit_score is None:
                    status = "Active"
                elif b.credit_score < 620:
                    status_rand = random.random()
                    if status_rand < 0.35:
                        status = "Defaulted"
                    elif status_rand < 0.65:
                        status = "Delinquent"
                    elif status_rand < 0.85:
                        status = "Overdue"
                    else:
                        status = "Active"
                elif b.credit_score < 680:
                    status_rand = random.random()
                    if status_rand < 0.08:
                        status = "Defaulted"
                    elif status_rand < 0.20:
                        status = "Delinquent"
                    elif status_rand < 0.35:
                        status = "Overdue"
                    else:
                        status = "Active"
                else: # Prime
                    status = "Active" if random.random() < 0.96 else "Overdue"

            # Compute remaining principal
            if status == "Settled":
                outstanding = 0.0
            else:
                # amortized remaining principal approximation
                paid_months = max(0, min(months_since_issue, term_months))
                outstanding = round(principal * max(0.10, (1.0 - (paid_months / term_months) * 0.9)), 2)

            loan = Loan(
                loan_id=f"LN-{issue_date.year}-{loan_id_counter}",
                borrower_id=b.borrower_id,
                principal_amount=principal,
                issue_date=issue_date,
                term_months=term_months,
                annual_rate=rate,
                status=status,
                outstanding_principal=outstanding,
                purpose=random.choice(PURPOSES),
                created_at=datetime.combine(issue_date, datetime.min.time())
            )
            db.add(loan)
            loan_id_counter += 1

            # 4. Generate Repayment Schedule & Transactions
            sched_date = issue_date + relativedelta(months=1)
            for inst in range(1, term_months + 1):
                interest_due = round(principal * monthly_rate, 2)
                principal_due = round(monthly_payment - interest_due, 2)
                sched_amount = round(monthly_payment, 2)

                sched = RepaymentSchedule(
                    loan=loan,
                    installment_number=inst,
                    due_date=sched_date,
                    scheduled_amount=sched_amount,
                    principal_due=principal_due,
                    interest_due=interest_due,
                    status="Pending"
                )
                db.add(sched)

                # Generate transaction if before cutoff and based on status
                if sched_date <= current_cutoff:
                    if status == "Settled":
                        sched.status = "Paid"
                        tx = RepaymentTransaction(
                            payment_id=f"TX-{sched_date.strftime('%y%m')}-{random.randint(10000, 99999)}",
                            loan=loan,
                            schedule=sched,
                            payment_date=sched_date - timedelta(days=random.randint(0, 3)),
                            amount=sched_amount,
                            payment_status="Completed",
                            reference=f"ACH-AutoPay-{sched_date.strftime('%Y%m%d')}"
                        )
                        db.add(tx)
                    elif status == "Active":
                        sched.status = "Paid"
                        tx = RepaymentTransaction(
                            payment_id=f"TX-{sched_date.strftime('%y%m')}-{random.randint(10000, 99999)}",
                            loan=loan,
                            schedule=sched,
                            payment_date=sched_date - timedelta(days=random.randint(0, 4)),
                            amount=sched_amount,
                            payment_status="Completed",
                            reference=f"ACH-DirectDebit"
                        )
                        db.add(tx)
                    elif status == "Overdue":
                        # Missed the most recent 1 installment
                        months_ago = (current_cutoff.year - sched_date.year) * 12 + (current_cutoff.month - sched_date.month)
                        if months_ago >= 1:
                            sched.status = "Paid"
                            tx = RepaymentTransaction(
                                payment_id=f"TX-{sched_date.strftime('%y%m')}-{random.randint(10000, 99999)}",
                                loan=loan,
                                schedule=sched,
                                payment_date=sched_date + timedelta(days=random.randint(2, 10)),
                                amount=sched_amount,
                                payment_status="Completed",
                                reference="ACH-Late-Payment"
                            )
                            db.add(tx)
                        else:
                            sched.status = "Overdue"
                    elif status == "Delinquent":
                        # Missed 2 installments
                        months_ago = (current_cutoff.year - sched_date.year) * 12 + (current_cutoff.month - sched_date.month)
                        if months_ago >= 2:
                            sched.status = "Paid"
                            tx = RepaymentTransaction(
                                payment_id=f"TX-{sched_date.strftime('%y%m')}-{random.randint(10000, 99999)}",
                                loan=loan,
                                schedule=sched,
                                payment_date=sched_date + timedelta(days=random.randint(5, 20)),
                                amount=sched_amount,
                                payment_status="Completed",
                                reference="Wire-Remittance"
                            )
                            db.add(tx)
                        else:
                            sched.status = "Overdue"
                    elif status == "Defaulted":
                        # Stopped paying after first 2-4 installments
                        if inst <= 3:
                            sched.status = "Paid"
                            tx = RepaymentTransaction(
                                payment_id=f"TX-{sched_date.strftime('%y%m')}-{random.randint(10000, 99999)}",
                                loan=loan,
                                schedule=sched,
                                payment_date=sched_date,
                                amount=sched_amount,
                                payment_status="Completed",
                                reference="Initial-Installment"
                            )
                            db.add(tx)
                        else:
                            sched.status = "Overdue"

                sched_date += relativedelta(months=1)

    db.flush()

    # 5. Run initial Risk Assessment for all borrowers
    print("Evaluating deterministic risk bands for all borrowers under v1.0...")
    all_loans = db.query(Loan).all()
    for b in borrowers_list:
        max_dpd = 0
        total_overdue = 0.0
        for l in b.loans:
            rep = calculate_loan_repayment_state(l.schedules, l.transactions, current_cutoff)
            total_overdue += rep["overdue_amount"]
            max_dpd = max(max_dpd, rep["days_past_due"])

        features = BorrowerRiskFeatures(
            borrower_id=b.borrower_id,
            annual_income=b.annual_income,
            monthly_debt=b.monthly_debt_obligations,
            credit_score=b.credit_score,
            max_overdue_days=max_dpd,
            total_overdue_amount=total_overdue,
            active_loans_count=len([l for l in b.loans if l.status != "Settled"])
        )
        assessment = evaluate_risk(features)

        ra = RiskAssessment(
            borrower_id=b.borrower_id,
            assessed_at=datetime.utcnow(),
            rule_set_id=active_rule.rule_set_id,
            risk_band=assessment.risk_band,
            risk_score=assessment.risk_score,
            factors_json=assessment.to_dict()["factors"]
        )
        db.add(ra)

    # 6. Seed initial DataQualityRun
    print("Logging initial Data Quality baseline run...")
    dq = DataQualityRun(
        started_at=datetime.utcnow() - timedelta(minutes=10),
        completed_at=datetime.utcnow(),
        records_read=len(borrowers_list) + len(all_loans),
        records_rejected=0,
        status="Warning",
        issue_summary=[
            {
                "issue_type": "Missing Critical Input",
                "entity": "Borrower",
                "record_id": "BRW-1023",
                "field": "credit_score",
                "description": "Borrower BRW-1023 has missing credit bureau score. Flagged for Review Required.",
                "severity": "Warning"
            },
            {
                "issue_type": "Missing Critical Input",
                "entity": "Borrower",
                "record_id": "BRW-1077",
                "field": "credit_score",
                "description": "Borrower BRW-1077 has missing credit bureau score. Flagged for Review Required.",
                "severity": "Warning"
            },
            {
                "issue_type": "Missing Critical Input",
                "entity": "Borrower",
                "record_id": "BRW-1089",
                "field": "annual_income",
                "description": "Borrower BRW-1089 has unverified annual income. Flagged for Review Required.",
                "severity": "Warning"
            }
        ]
    )
    db.add(dq)

    db.commit()
    print("Seed complete! Database populated with realistic credit risk portfolio data.")

if __name__ == "__main__":
    seed_database()
