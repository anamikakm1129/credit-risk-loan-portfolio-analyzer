# CredVista — Product Features & UX Specification

## Product vision
CredVista turns loan and repayment data into clear portfolio insights for lending teams. The UI should feel premium, calm, readable, and uncluttered.

## UX principles
- Warm ivory canvas, charcoal navigation, muted bronze accents, restrained semantic status colours.
- One clear primary task per screen; progressive disclosure for detail.
- Explainable risk labels; colour is never the only signal.
- Responsive, accessible tables and charts; explicit loading, error and empty states.

## Navigation
Dashboard · Borrowers · Loans · Repayments · Risk Analysis · Vintage Analysis · Reports · Settings

## Core features
1. **Dashboard:** Total loans, outstanding principal, default rate, overdue amount; portfolio trend, credit-score distribution, risk segmentation, vintage snapshot, top high-risk borrowers and recent activity.
2. **Borrowers:** Search by name/ID; filter by risk band, credit score, DTI and status; sortable paginated table.
3. **Borrower profile:** Income, credit score, DTI, active loans, exposure, overdue, repayment summary, risk factors and explanation.
4. **Loans:** Loan ID, borrower, principal, issue date, term, outstanding balance, status and risk band.
5. **Repayments:** Due, paid, overdue, payment date, days past due and status; definitions distinguish delinquency from default.
6. **Risk segmentation:** Configurable Low/Medium/High rules, reason codes, version and effective date. Rules are not an ML prediction.
7. **Portfolio analytics:** Default rate, overdue, repayment rate, exposure and segment distribution with explicit denominators.
8. **Vintage/cohort:** Compare origination-month cohorts at common loan ages; immature cohorts are not shown as zero.
9. **Credit-score comparison:** Counts, exposure, overdue and default rates by score band.
10. **Reports:** Export filtered data with reporting period, definitions, filters and timestamp.
11. **Global search/date filter:** Consistent search and reporting-period behavior.
12. **Data quality:** Flag missing fields, duplicate IDs, invalid dates, rejected rows and stale refreshes.

## Dashboard layout
Header/search/date range; left navigation; four KPI cards; three focused charts; vintage snapshot; high-risk and recent-activity tables. Keep detailed investigation on dedicated pages.

## Design tokens
- Canvas: warm ivory; navigation: charcoal/deep brown; accent: muted bronze/sand.
- Status: muted green, amber and red with text labels.
- Clean sans-serif body typography, restrained display heading, consistent 8-point spacing.

## MVP
Dashboard, borrower/loan directories and details, repayment metrics, rule-based risk segmentation, score-band/vintage comparisons, CSV/report export, data-quality checks. Later: advanced alerts, scenario analysis, validated ML models and integrations.

## Acceptance
Every KPI reconciles to documented logic; every risk label has an explanation; filters carry through to exports; tables paginate; missing data is not silently treated as zero; UI is responsive and uncluttered.
