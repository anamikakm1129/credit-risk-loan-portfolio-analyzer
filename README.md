# CredVista — Credit Risk & Loan Portfolio Intelligence Platform

CredVista is a credit-risk and loan-portfolio analytics application built for risk analysts, portfolio managers, lending operations teams, and data owners.

CredVista consolidates borrower, loan, and repayment data into an explainable, transparent view of portfolio exposure and repayment health, strictly adhering to the **CredVista PRD**, **Technical Requirements Document (TRD)**, and **Product Features & UX Specification**.

---

## Key Features

1. **Portfolio Health Dashboard**:
   - Four headline KPI cards: **Total Loans**, **Outstanding Principal**, **Default Rate**, and **Overdue Amount** with calculation formula tooltips.
   - Secondary indicators: Collection Repayment Rate, Weighted Average DTI, and Weighted Average Credit Bureau Score.
   - Monthly portfolio exposure trend, credit score distribution, and risk band allocation.
   - High-risk borrower and recent origination drill-downs.

2. **Searchable Borrower Directory & Explainable Profile**:
   - Filter by risk band, FICO score range, DTI range, and status.
   - Sortable paginated table.
   - Borrower Profile modal featuring an **Explainable Risk Engine Card** detailing assigned band, rule version, reason codes, contributing weights, and missing-input warnings.

3. **Loan Facility Management & Amortization**:
   - Loan directory with terms, interest rates, status, and outstanding principal.
   - Loan drill-down modal showing scheduled amortization installments, payment transactions, and Days Past Due (DPD).

4. **Repayment & Delinquency Aging (DPD)**:
   - Tracks scheduled due vs actual collected amounts.
   - **Delinquency Aging Buckets**: Current (0 DPD), Late (1–30 DPD), Delinquent (31–60 DPD), Severely Delinquent (61–89 DPD), and Defaulted (90+ DPD).
   - FIFO allocation policy for partial payments against earliest unpaid installments.

5. **Explainable Deterministic Risk Rules & Interactive Simulator**:
   - Active **Ruleset v1.0** (configurable cutoffs for DTI, credit score, and delinquency).
   - **Policy Stress Simulator**: Interactive sliders allowing risk teams to simulate how altering DTI or score cutoffs reclassifies portfolio risk bands and exposure before committing policy changes.
   - **Data Quarantine Rule**: Missing critical inputs (e.g. unverified income or missing credit score) trigger **Review Required**, never silently defaulting to Low risk.

6. **Vintage & Cohort Analysis**:
   - Origination-month cohorts evaluated at milestone loan ages: 1, 3, 6, 9, 12, 18, and 24 months.
   - **PRD Compliance**: Immature cohorts whose observation age is less than the milestone are explicitly labeled as **Immature / Not Observable** and never conflated with zero.

7. **Reports & Audit Exports**:
   - Generate immutable, versioned report snapshots with full filter tracking.
   - Direct CSV export of all loan facilities, risk factors, and repayment states (`GET /api/v1/reports/export.csv`).
   - Audit trail of historical report runs.

8. **Data Quality & Diagnostics**:
   - Automated diagnostics scanning for duplicate IDs, missing critical inputs, out-of-range credit scores (<300 or >850), and invalid dates.
   - Ingestion logging via `data_quality_runs`.

---

## Technical Architecture

- **Backend**: Python 3.11, FastAPI, Pydantic V2, SQLAlchemy, Pandas, Pytest.
- **Frontend**: React 19, TypeScript, Vite, Lucide Icons.
- **Design Tokens**: Warm ivory canvas (`#FAF8F5`), charcoal navigation (`#161A1E`), muted bronze accents (`#9C7A4A`), restrained semantic status badges (non-color-only with iconography and text labels).
- **Database**: SQLite (default zero-config `credvista.db`) with full PostgreSQL schema compatibility.

```
credvista/
  ├── backend/
  │   ├── app/
  │   │   ├── main.py                  # FastAPI application entrypoint
  │   │   ├── core/                    # Config & database setup
  │   │   ├── models/                  # SQLAlchemy models (Borrower, Loan, Repayments, Risk)
  │   │   ├── schemas/                 # Pydantic schemas
  │   │   ├── services/
  │   │   │   ├── portfolio_metrics.py # Headline KPIs & definitions
  │   │   │   ├── risk_rules.py        # Versioned deterministic risk engine
  │   │   │   ├── repayment_analysis.py# FIFO payments, DPD & delinquency
  │   │   │   ├── vintage_analysis.py  # Cohort matrix & immature handling
  │   │   │   └── report_service.py    # Audited reports & CSV export
  │   │   ├── analytics/               # Score bands & monthly trends
  │   │   ├── ingestion/               # CSV validation & quality diagnostics
  │   │   └── api/routes/              # REST API endpoints
  │   └── tests/                       # 21 unit & integration tests
  ├── frontend/
  │   ├── src/
  │   │   ├── components/              # KPICard, StatusBadge, Modals
  │   │   ├── features/                # Dashboard, Borrowers, Loans, Risk, Vintage, Reports, Settings
  │   │   ├── services/api.ts          # API client
  │   │   └── index.css                # CredVista UX design tokens
  │   └── vite.config.ts               # Proxy configuration
  ├── database/
  │   └── seeds/seed_data.py           # 120 borrowers, 180 loans across cohorts
  ├── docs/                            # Extracted PRD, TRD, UX specs
  ├── run_dev.bat                      # One-click Windows runner
  ├── run_dev.ps1                      # One-click PowerShell runner
  └── requirements.txt
```

---

## Quick Start & Running Locally

### 1. Backend Setup & Seed Data

Ensure Python 3.10+ is installed:
```powershell
# Install dependencies
pip install -r requirements.txt

# Seed the database with realistic portfolio data
python -m database.seeds.seed_data

# Run tests (21 tests covering metrics, risk rules, and API)
python -m pytest backend/tests/ -v

# Start the FastAPI backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation (Swagger UI): [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)

### 2. Frontend Setup

In a separate terminal:
```powershell
cd frontend
npm install
npm run dev
```
- Application Web UI: [http://localhost:5173](http://localhost:5173)

### 3. One-Click Launch (Windows)

Simply run:
```powershell
.\run_dev.ps1
```
or double-click `run_dev.bat`.

---

## Metric Formula Reference

| Metric | Formula | Policy Rule |
| :--- | :--- | :--- |
| **Outstanding Principal** | $\sum \text{Remaining Principal Balance}$ | Excludes settled/closed facilities. |
| **Overdue Amount** | $\sum \text{Unpaid amounts past due as of cutoff}$ | FIFO payment allocation to earliest installment. |
| **Default Rate** | $\frac{\text{Defaulted Loans}}{\text{Total Loans in Scope}} \times 100$ | Defaulted status or DPD $\ge$ 90 days. |
| **Repayment Rate** | $\frac{\text{Total Paid}}{\text{Total Scheduled Due}} \times 100$ | Cash realization vs schedule. |
| **Debt-to-Income (DTI)** | $\frac{\text{Monthly Debt}}{\text{Monthly Gross Income}} \times 100$ | Standardized monthly frequency. |
| **Vintage Default** | $\frac{\text{Cohort Defaults at Age } M}{\text{Cohort Population}}$ | Immature cohorts marked non-observable. |

