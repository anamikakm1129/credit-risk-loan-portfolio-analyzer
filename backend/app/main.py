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

# Initialize database tables
Base.metadata.create_all(bind=engine)

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
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }
