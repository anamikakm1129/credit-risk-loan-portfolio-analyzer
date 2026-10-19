# CredVista — Product Requirements Document (PRD)

## Summary
CredVista is a credit-risk and loan-portfolio analytics application for risk analysts, portfolio managers, lending operations and data owners. MVP focuses on portfolio analytics and explainable rules, not automated approval or ML prediction.

## Problem
Loan and repayment data can be scattered across tables/files, making exposure, repayment stress and cohort comparisons hard to understand consistently. CredVista creates a traceable, user-friendly view.

## Goals
- Single portfolio health view.
- Transparent, configurable risk segmentation.
- Comparisons by risk band, credit score, DTI and origination cohort.
- Traceable metrics and repeatable exports.

## Non-goals
Automated loan decisions, individual default prediction by ML, replacement of an origination/servicing system, or complex enterprise integrations in MVP.

## Personas
- Credit Risk Analyst: explain risk patterns.
- Portfolio Manager: monitor exposure and trends.
- Lending Operations Analyst: find borrowers/loans and review repayments.
- Data Owner/Admin: manage data quality and rule definitions.

## Functional requirements
- Dashboard KPIs and trends.
- Global search and page-level filters.
- Borrower/loan directories and detail views.
- Repayment and overdue calculations.
- Explainable, versioned risk rules.
- Risk and credit-score segment comparison.
- Vintage/cohort analysis at fixed loan ages.
- Filter-aware report/export.
- Data-quality diagnostics.
- Access control and important-change audit trail.

## Metric definitions
- **Outstanding principal:** sum of remaining principal for in-scope loans.
- **Overdue amount:** unpaid amounts past due at reporting cutoff, using agreed partial-payment allocation.
- **Default rate:** defaulted loans / defined eligible population, with default definition and window stated.
- **Repayment rate:** amount paid / amount due for defined population and period.
- **DTI:** monthly debt obligations / gross monthly income × 100.
- **Risk-band share:** count share or exposure share, explicitly labelled.
- **Vintage default rate:** cohort defaults at a specified loan age / eligible cohort population; immature cohorts are not comparable as zeros.

## Risk rules
Thresholds are configurable placeholders until policy and data are reviewed. Each assessment includes band, reasons, rule version, date and missing-input warnings. Keep risk band separate from loan status. Never silently classify missing inputs as low risk.

## Non-functional requirements
Usable navigation; primary pages normally render within 2 seconds for the agreed MVP dataset; robust error states; server-side authorization; privacy-conscious logs/exports; accessible controls; maintainable modules; report traceability.

## Success criteria
Metrics reconcile to sample records; classifications are reproducible; filters match exports; vintage comparisons use equal observation ages; analysts can locate records quickly; usability review finds the UI clear and uncluttered.

## Assumptions and risks
Need stable borrower/loan IDs, origination dates, repayment events and balances. Default, DTI, partial-payment and reporting-timezone definitions must be agreed. Static snapshots may not support historical vintage reconstruction. Mockup figures are illustrative, not actual portfolio data.

## Release criteria
Must-have features verified; metric definitions reviewed; risk rules versioned/tested; exports and filters consistent; security/data-quality checks pass; responsive UI review completed.
