# CredVista — Technical Requirements Document (TRD)

## Proposed MVP stack
React + TypeScript frontend; FastAPI/Python backend; PostgreSQL; SQL for aggregations; pandas for ingestion/validation; pytest for tests. This is a recommendation, not an assertion about an existing repository.

## Architecture
Presentation → API/application → domain services → SQL analytics/repositories → PostgreSQL. CSV ingestion validates and reports quality before records are accepted.

## Suggested modules
`frontend/src/features/{dashboard,borrowers,loans,repayments,risk-analysis,vintage-analysis,reports}`; `backend/app/{api,schemas,models,repositories,services,analytics,ingestion}`; `database/{migrations,seeds,queries}`; `docs/`.

## Data entities
- `borrowers`: borrower_id, reference/name, annual_income, credit_score.
- `loans`: loan_id, borrower_id FK, principal, issue_date, term, rate, status, outstanding principal.
- `repayment_schedule`: schedule_id, loan_id FK, due_date, scheduled amount and components.
- `repayment_transactions`: payment_id, loan_id, optional schedule_id, payment date, amount, status, reference.
- `risk_rule_sets`: versioned configuration and effective dates.
- `risk_assessments`: entity scope, assessment date, rule version, band and reason codes.
- `data_quality_runs`: import counts and issue summary.
- `report_runs`: period, filters, metric version and generated artifact reference.

## Calculation/data rules
Use NUMERIC/DECIMAL for currency; consistent date/time conventions; enforce primary/foreign keys; validate non-negative amounts where applicable, allowed statuses and dates. DTI must use consistent monthly income/debt inputs. Calculate overdue as of a defined cutoff with an agreed partial-payment policy. Define default and observation window explicitly. Missing data is not zero. Reconcile Python and SQL metrics with fixtures.

## Risk engine
Deterministic service with validated features and configurable/versioned thresholds. Return band, reason codes, explanation, rule version and missing inputs. Illustrative thresholds/weights must be validated before use. Missing critical inputs should result in review/unknown, not automatic low risk.

## API sketch
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/trends`
- `GET /api/v1/borrowers` and `/api/v1/borrowers/{borrower_id}`
- `GET /api/v1/loans` and `/api/v1/loans/{loan_id}`
- `GET /api/v1/loans/{loan_id}/repayments`
- `GET /api/v1/risk/segments`
- `GET /api/v1/analysis/vintage`
- `GET /api/v1/analysis/credit-score-bands`
- `POST /api/v1/reports`
- `GET /api/v1/data-quality/latest`

Use parameterized SQL, allowlisted sort fields, server-side pagination, suitable indexes and explicit null/immature-cohort semantics.

## Frontend requirements
Shared shell and reusable KPI cards, filters, tables, status badges, chart containers, explanation panels and empty/loading/error states. Keep dashboard to four KPIs and a few charts. Use accessible labels, responsive navigation, consistent tokens and no colour-only meanings.

## Security
Server-side auth and role checks, request/file validation, secrets in environment management, least-privilege DB users, parameterized queries, minimized logs, protected exports, synthetic/de-identified demo data.

## Testing
Unit tests for DTI, overdue, partial payments, defaults and risk boundaries; DB tests for joins/aggregations/cohorts; API validation/auth/pagination tests; UI state tests; end-to-end CSV→validation→DB→metrics→dashboard→export; metric reconciliation against hand-calculated fixtures.

## Deployment
Separate environments, migrations, repeatable seed data, health checks, structured logs, error monitoring, CI tests and documented setup commands.

## Technical acceptance
Endpoints validate inputs; metrics have tested formulas/cutoffs; rules are deterministic/versioned; imports report quality; large tables paginate; screens handle errors/empty states; end-to-end portfolio report reconciles.
