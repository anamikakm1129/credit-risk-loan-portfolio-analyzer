import sys
import os

# Ensure both repo root and backend directory are in Python module search path
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../backend/app
backend_dir = os.path.dirname(current_dir)               # .../backend
repo_root = os.path.dirname(backend_dir)                 # .../ (repo root)

for p in [repo_root, backend_dir]:
    if p and p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.core.config import settings
    from backend.app.core.database import engine, Base
    import backend.app.models
    from backend.app.api.routes import (
        dashboard, borrowers, loans, repayments, risk, analysis, reports, data_quality
    )
except ModuleNotFoundError:
    from app.core.config import settings
    from app.core.database import engine, Base
    import app.models
    from app.api.routes import (
        dashboard, borrowers, loans, repayments, risk, analysis, reports, data_quality
    )

db_status_msg = "connected"

def init_db_defaults():
    try:
        try:
            from backend.app.core.database import SessionLocal
            from backend.app.models import RiskRuleSet
            from backend.app.services.risk_rules import DEFAULT_RULE_SET
        except ImportError:
            from app.core.database import SessionLocal
            from app.models import RiskRuleSet
            from app.services.risk_rules import DEFAULT_RULE_SET
        from datetime import date
        with SessionLocal() as db:
            if not db.query(RiskRuleSet).filter(RiskRuleSet.active == True).first():
                rule = RiskRuleSet(
                    rule_set_id="RRS-V1.0",
                    version="1.0",
                    effective_from=date(2024, 1, 1),
                    configuration=DEFAULT_RULE_SET.to_dict(),
                    active=True,
                    description="Default Production Risk Scoring Policy v1.0"
                )
                db.add(rule)
                db.commit()
    except Exception as e:
        print(f"Notice: initial rules check: {e}")

def init_db():
    global db_status_msg
    try:
        Base.metadata.create_all(bind=engine)
        init_db_defaults()
        db_status_msg = "connected"
        print("Database connected and tables initialized successfully.")
    except Exception as e:
        db_status_msg = f"Database connection warning: {e}"
        print(f"DATABASE INITIALIZATION WARNING: {e}")
        print("Tip: If using Supabase on Render, use IPv4 pooler URI: aws-0-ap-northeast-1.pooler.supabase.com:5432 with username postgres.telbaduznhrtbjmzvbwu")

init_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CredVista — Credit Risk & Loan Portfolio Intelligence Platform API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(borrowers.router, prefix=settings.API_V1_STR)
app.include_router(loans.router, prefix=settings.API_V1_STR)
app.include_router(repayments.router, prefix=settings.API_V1_STR)
app.include_router(risk.router, prefix=settings.API_V1_STR)
app.include_router(analysis.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(data_quality.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": f"{settings.API_V1_STR}/docs"
    }

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy" if db_status_msg == "connected" else "degraded",
        "database": db_status_msg,
        "version": "1.0.0"
    }
