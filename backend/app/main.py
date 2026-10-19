import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal, migrate_db
from backend.app.models.prospect import ProspectModel
from backend.app.models.audit import AuditReportModel, AuditFindingModel
from backend.app.models.draft import EmailDraftModel
from backend.app.models.history import EmailHistoryModel, SuppressionRecordModel
from backend.app.models.google_auth import GoogleAccountModel, OAuthStateModel, EmailSendAttemptModel
from backend.app.api import health, prospects, audits, drafts, discovery, ai, google, email_dispatch, enrichment


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("leddro.backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist
    logger.info("Initializing Leddro SQLite database schema...")
    Base.metadata.create_all(bind=engine)
    migrate_db(engine)
    logger.info("Leddro backend engine initialized successfully (clean state - no mock seeds).")
    yield
    # Shutdown
    logger.info("Leddro backend shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Leddro High-Precision Website Audit & Prospect Intelligence Backend API",
    lifespan=lifespan
)

# CORS configuration
origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Request validation failed",
            "details": exc.errors(),
            "path": request.url.path
        }
    )

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred processing your request.",
            "path": request.url.path
        }
    )

# Include Routers under /api
app.include_router(health.router, prefix="/api")
app.include_router(prospects.router, prefix="/api")
app.include_router(audits.router, prefix="/api")
app.include_router(drafts.router, prefix="/api")
app.include_router(discovery.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(google.router, prefix="/api")
app.include_router(email_dispatch.router, prefix="/api")
app.include_router(enrichment.router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health"
    }
