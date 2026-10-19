import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_dashboard_summary():
    response = client.get("/api/v1/dashboard/summary?reporting_date=2026-10-19")
    assert response.status_code == 200
    data = response.json()
    assert "total_loans" in data
    assert "outstanding_principal" in data
    assert "default_rate" in data
    assert "overdue_amount" in data
    assert data["total_loans"]["value"] > 0

def test_dashboard_trends():
    response = client.get("/api/v1/dashboard/trends?reporting_date=2026-10-19")
    assert response.status_code == 200
    data = response.json()
    assert "monthly_trends" in data
    assert len(data["monthly_trends"]) > 0

def test_borrowers_directory_and_filters():
    # List all
    res = client.get("/api/v1/borrowers?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 100

    # Filter by risk band
    res_high = client.get("/api/v1/borrowers?risk_band=High")
    assert res_high.status_code == 200
    for item in res_high.json()["items"]:
        assert item["risk_band"] == "High"

def test_borrower_profile_drilldown():
    # Fetch borrower
    res = client.get("/api/v1/borrowers/BRW-1001")
    assert res.status_code == 200
    data = res.json()
    assert data["borrower_id"] == "BRW-1001"
    assert "risk_assessment" in data
    assert "loans" in data

def test_loans_directory():
    res = client.get("/api/v1/loans?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 150

def test_repayments_overview():
    res = client.get("/api/v1/repayments/overview?reporting_date=2026-10-19")
    assert res.status_code == 200
    data = res.json()
    assert "aging_buckets" in data
    assert len(data["aging_buckets"]) == 5

def test_risk_segments():
    res = client.get("/api/v1/risk/segments")
    assert res.status_code == 200
    data = res.json()
    assert "segments" in data
    assert len(data["segments"]) == 4

def test_vintage_analysis_immature_semantics():
    res = client.get("/api/v1/analysis/vintage?reporting_date=2026-10-19")
    assert res.status_code == 200
    data = res.json()
    assert "cohorts" in data
    
    # Check that recent cohorts (e.g. 2026-07) have immature cells for milestone 12, 18, 24
    recent_cohort = [c for c in data["cohorts"] if c["origination_cohort"] == "2026-07"][0]
    cell_24 = [cell for cell in recent_cohort["cells"] if cell["loan_age_months"] == 24][0]
    assert cell_24["is_immature"] is True
    assert cell_24["cumulative_default_rate"] is None

def test_reports_generation_and_export():
    # Generate report
    res = client.post("/api/v1/reports", json={
        "user_id": "test_analyst@credvista.internal",
        "period_end": "2026-10-19",
        "notes": "Q4 Risk Committee Summary"
    })
    assert res.status_code == 200
    data = res.json()
    assert "report_id" in data
    assert data["report_id"].startswith("REP-")

    # CSV download
    csv_res = client.get("/api/v1/reports/export.csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Loan ID,Borrower ID" in csv_res.text

def test_data_quality_endpoint():
    res = client.get("/api/v1/data-quality/latest")
    assert res.status_code == 200
    data = res.json()
    assert "issues" in data
    assert len(data["issues"]) >= 3 # Detects our seeded test missing data

