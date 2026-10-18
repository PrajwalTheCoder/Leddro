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
from backend.app.api import health, prospects, audits, drafts, discovery, ai, google, email_dispatch


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("leddro.backend")

INITIAL_SEEDS = [
    {
        "id": "pr-1",
        "name": "Northstar Interiors",
        "category": "Interior design",
        "city": "Navi Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "website_url": "https://northstarinteriors.in",
        "website_status": "broken_pages",
        "opportunity_score": 82,
        "score_urgency": 35,
        "score_intent": 25,
        "score_ease": 22,
        "status": "needs_review",
        "last_activity": "12 mins ago",
        "phone": "+91 22 2789 4412",
        "email": "contact@northstarinteriors.in",
        "audit_count": 2,
        "latest_audit_id": "audit-northstar-1",
        "tags": json.dumps(["High Value", "Broken Contact Form", "Navi Mumbai Hub"]),
        "recommended_action": "Send outreach proposal detailing HTTP 404 on contact portal and mobile viewport fix.",
        "notes": "Premium commercial studio with 22 team members. Primary lead capture form is currently unreachable."
    },
    {
        "id": "pr-2",
        "name": "Harbor Furniture Works",
        "category": "Manufacturing",
        "city": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "website_url": "https://harborfurniture.co.in",
        "website_status": "active",
        "opportunity_score": 78,
        "score_urgency": 28,
        "score_intent": 26,
        "score_ease": 24,
        "status": "needs_review",
        "last_activity": "1 hour ago",
        "phone": "+91 20 6645 8890",
        "email": "inquiries@harborfurniture.co.in",
        "audit_count": 1,
        "latest_audit_id": "audit-harbor-1",
        "tags": json.dumps(["Export Ready", "Heavy Assets", "Pune Industrial"]),
        "recommended_action": "Propose website speed optimization and asset compression for international buyers.",
        "notes": "B2B wooden furniture exporter. Homepage takes 3.8s to load due to 14MB uncompressed hero assets."
    },
    {
        "id": "pr-3",
        "name": "Willow Studio",
        "category": "Architecture",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "website_url": "https://willowstudio.design",
        "website_status": "active",
        "opportunity_score": 64,
        "score_urgency": 18,
        "score_intent": 24,
        "score_ease": 22,
        "status": "draft_ready",
        "last_activity": "Yesterday",
        "phone": "+91 80 4112 9081",
        "email": "studio@willowstudio.design",
        "audit_count": 1,
        "latest_audit_id": "audit-willow-1",
        "tags": json.dumps(["Sustainable Architecture", "Outdated TLS"]),
        "recommended_action": "Review prepared email draft regarding TLS deprecation and OpenGraph card preview fixes.",
        "notes": "Award-winning sustainable architect practice. Insecure cipher configuration triggers corporate browser warnings."
    },
    {
        "id": "pr-4",
        "name": "Apex Precision Tech",
        "category": "Machining & Tooling",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "website_url": "https://apexprecisiontech.com",
        "website_status": "ssl_expired",
        "opportunity_score": 91,
        "score_urgency": 40,
        "score_intent": 28,
        "score_ease": 23,
        "status": "approved",
        "last_activity": "3 days ago",
        "phone": "+91 44 2811 7099",
        "email": "ops@apexprecisiontech.com",
        "audit_count": 3,
        "latest_audit_id": "audit-apex-1",
        "tags": json.dumps(["Critical SSL", "Industrial CNC", "High Urgency"]),
        "recommended_action": "Execute approved outreach alerting them to expired certificate blocking inquiry submissions.",
        "notes": "Tier-1 auto component supplier. Their production domain certificate expired 4 days ago."
    },
    {
        "id": "pr-5",
        "name": "Kaveri Logistics & Freight",
        "category": "Logistics",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "website_url": "https://kaverilogistics.in",
        "website_status": "unreachable",
        "opportunity_score": 88,
        "score_urgency": 38,
        "score_intent": 27,
        "score_ease": 23,
        "status": "contacted",
        "last_activity": "5 days ago",
        "phone": "+91 40 4455 1200",
        "email": "info@kaverilogistics.in",
        "audit_count": 1,
        "latest_audit_id": "audit-kaveri-1",
        "tags": json.dumps(["DNS Misconfig", "Fleet Logistics", "Follow-up Due"]),
        "recommended_action": "Follow up on initial outreach regarding root domain DNS record misconfiguration.",
        "notes": "50-vehicle fleet logistics provider. DNS records missing A record for apex domain."
    }
]

def seed_database_if_empty():
    db = SessionLocal()
    try:
        count = db.query(ProspectModel).count()
        if count == 0:
            logger.info("Database prospects table is empty. Seeding initial prospects...")
            for seed in INITIAL_SEEDS:
                p = ProspectModel(**seed)
                db.add(p)
            db.commit()
            logger.info(f"Seeded {len(INITIAL_SEEDS)} initial prospects successfully.")
        else:
            logger.info(f"Database already contains {count} prospects.")
    except Exception as e:
        logger.error(f"Error checking/seeding database: {e}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist
    logger.info("Initializing Leddro SQLite database schema...")
    Base.metadata.create_all(bind=engine)
    migrate_db(engine)
    seed_database_if_empty()
    logger.info("Leddro backend engine initialized successfully.")
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


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health"
    }
