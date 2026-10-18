import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.schemas.draft import HealthResponse
from backend.app.models.prospect import ProspectModel
from backend.app.models.audit import AuditReportModel

router = APIRouter(prefix="/health", tags=["Health"])

START_TIME = time.time()

@router.get("", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """
    Check backend health, DB connectivity, and table metrics.
    """
    uptime = time.time() - START_TIME
    
    # Test DB connection
    db_status = "connected"
    prospects_count = 0
    audits_count = 0
    try:
        db.execute(text("SELECT 1"))
        prospects_count = db.query(ProspectModel).count()
        audits_count = db.query(AuditReportModel).count()
    except Exception:
        db_status = "unhealthy: database unreachable"

    db_driver = "SQLite" if "sqlite" in settings.DATABASE_URL.lower() else "Neon PostgreSQL"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.APP_VERSION,
        database=db_status,
        engine=f"Python FastAPI + {db_driver} SQLAlchemy ORM",
        uptimeSeconds=round(uptime, 2),
        prospectsCount=prospects_count,
        auditsCount=audits_count
    )

