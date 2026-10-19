from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.services.vintage_analysis import compute_vintage_matrix
from backend.app.analytics.cohort_queries import get_credit_score_band_comparisons

router = APIRouter(prefix="/analysis", tags=["Analytics"])

@router.get("/vintage")
def get_vintage_analysis(
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns the vintage cohort matrix across origination months and loan ages.
    Immature cohorts are explicitly marked as is_immature=True and null default rate.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()
    return compute_vintage_matrix(db, cutoff_date=cutoff)

@router.get("/credit-score-bands")
def get_credit_score_bands(
    reporting_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns portfolio performance (exposure, overdue, default rate, DTI)
    across Super Prime, Prime, Near Prime, Subprime, and Deep Subprime bands.
    """
    cutoff = datetime.strptime(reporting_date or settings.DEFAULT_REPORTING_DATE, "%Y-%m-%d").date()
    return {"bands": get_credit_score_band_comparisons(db, cutoff_date=cutoff)}

