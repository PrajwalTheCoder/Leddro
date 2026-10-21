import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.core.database import get_db
from backend.app.models.prospect import ProspectModel
from backend.app.schemas.prospect import (
    ProspectCreate,
    ProspectUpdate,
    db_prospect_to_schema
)
from backend.app.discovery.providers.csv_import import (
    preview_csv_import,
    commit_csv_import,
    CsvImportPreviewResponse,
    CsvImportSummaryResponse
)
from pydantic import BaseModel

class CsvPreviewInput(BaseModel):
    csvContent: str
    columnMapping: Optional[dict] = None

class CsvConfirmInput(BaseModel):
    records: List[dict]
    skipDuplicates: bool = True

router = APIRouter(prefix="/prospects", tags=["Prospects"])

@router.post("/import/preview", response_model=CsvImportPreviewResponse)
def preview_import(payload: CsvPreviewInput, db: Session = Depends(get_db)):
    """
    Validates CSV records, detects duplicates against the database,
    and returns parsed and invalid rows without writing to the database.
    """
    try:
        preview = preview_csv_import(db, payload.csvContent, payload.columnMapping)
        return preview
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV preview parsing failed: {str(e)}"
        )

@router.post("/import/confirm", response_model=CsvImportSummaryResponse)
def confirm_import(payload: CsvConfirmInput, db: Session = Depends(get_db)):
    """
    Commits validated records into the SQLite database.
    """
    try:
        summary = commit_csv_import(db, payload.records, payload.skipDuplicates)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV import confirmation failed: {str(e)}"
        )


@router.get("")
def list_prospects(
    search: Optional[str] = Query(None, description="Search by name, category, or city"),
    status: Optional[str] = Query(None, description="Filter by prospect status"),
    db: Session = Depends(get_db)
):
    from backend.app.models.audit import AuditReportModel
    from backend.app.services.prospect_scoring import calculate_prospect_score
    from sqlalchemy.orm import joinedload

    query = db.query(ProspectModel)
    
    if status and status != "all":
        query = query.filter(ProspectModel.status == status)
        
    if search:
        search_fmt = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                ProspectModel.name.ilike(search_fmt),
                ProspectModel.category.ilike(search_fmt),
                ProspectModel.city.ilike(search_fmt),
                ProspectModel.website_url.ilike(search_fmt)
            )
        )
        
    prospects = query.order_by(ProspectModel.opportunity_score.desc()).all()

    # Query latest audits in batch to avoid N+1 queries
    latest_audit_ids = [p.latest_audit_id for p in prospects if p.latest_audit_id]
    audits_map = {}
    if latest_audit_ids:
        audits = (
            db.query(AuditReportModel)
            .options(joinedload(AuditReportModel.findings))
            .filter(AuditReportModel.id.in_(latest_audit_ids))
            .all()
        )
        audits_map = {a.id: a for a in audits}

    results = []
    for p in prospects:
        audit = audits_map.get(p.latest_audit_id)
        scoring_res = calculate_prospect_score(p, audit)
        results.append(db_prospect_to_schema(p, scoring_res))

    return results

@router.get("/{prospect_id}")
def get_prospect(prospect_id: str, db: Session = Depends(get_db)):
    from backend.app.models.audit import AuditReportModel
    from backend.app.services.prospect_scoring import calculate_prospect_score
    from sqlalchemy.orm import joinedload

    prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect with ID '{prospect_id}' not found"
        )

    audit = None
    if prospect.latest_audit_id:
        audit = (
            db.query(AuditReportModel)
            .options(joinedload(AuditReportModel.findings))
            .filter(AuditReportModel.id == prospect.latest_audit_id)
            .first()
        )

    scoring_res = calculate_prospect_score(prospect, audit)
    return db_prospect_to_schema(prospect, scoring_res)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_prospect(payload: ProspectCreate, db: Session = Depends(get_db)):
    from backend.app.discovery.deduplication import check_single_duplicate
    from backend.app.services.prospect_scoring import calculate_prospect_score

    # Check duplicates using central deduplication service
    match = check_single_duplicate(
        db=db,
        name=payload.name,
        website_url=payload.websiteUrl,
        city=payload.location.city if payload.location else None,
        state=payload.location.state if payload.location else None,
        country=payload.location.country if payload.location else None,
        source_provider=payload.sourceProvider,
        source_record_id=payload.sourceRecordId
    )
    if match:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Prospect already exists: {match.reason} (ID: {match.existing_id})"
        )

    new_id = f"pros_{uuid.uuid4().hex[:8]}"
    
    # Calculate baseline explainable score for the new prospect
    from backend.app.services.identity_verifier import verify_business_identity
    id_ev = verify_business_identity(
        business_name=payload.name,
        location={
            "city": (payload.location.city if payload.location else "") or "",
            "state": (payload.location.state if payload.location else "") or "",
        },
        website_url=payload.websiteUrl,
        phone=payload.phone,
        source_provider=payload.sourceProvider,
    )
    scoring_res = calculate_prospect_score(payload, None)
    initial_opp_score = payload.opportunityScore if payload.opportunityScore != 70 else scoring_res["opportunity_score"]

    new_prospect = ProspectModel(
        id=new_id,
        name=payload.name,
        category=payload.category,
        city=payload.location.city if payload.location else "Navi Mumbai",
        state=payload.location.state if payload.location else "Maharashtra",
        country=payload.location.country if payload.location else "India",
        website_url=payload.websiteUrl,
        website_status=payload.websiteStatus or "active",
        opportunity_score=initial_opp_score,
        score_urgency=payload.scoreBreakdown.technicalUrgency if payload.scoreBreakdown else 25,
        score_intent=payload.scoreBreakdown.commercialIntent if payload.scoreBreakdown else 25,
        score_ease=payload.scoreBreakdown.resolutionEase if payload.scoreBreakdown else 20,
        status=payload.status or "new",
        last_activity="Created just now",
        phone=payload.phone,
        email=payload.email,
        audit_count=0,
        latest_audit_id=None,
        tags=json.dumps(payload.tags or []),
        recommended_action=payload.recommendedAction or "Execute initial website audit.",
        notes=payload.notes or "",
        identity_status=id_ev["status"],
        identity_evidence=json.dumps(id_ev),
        contact_provenance=json.dumps(payload.contactProvenance or {}),
        social_profiles=json.dumps(payload.socialProfiles or {}),
    )
    
    db.add(new_prospect)
    try:
        db.commit()
        db.refresh(new_prospect)
    except Exception:
        db.rollback()
        raise
    scoring_res = calculate_prospect_score(new_prospect, None)
    return db_prospect_to_schema(new_prospect, scoring_res)

@router.post("/{prospect_id}/recalculate-score")
def recalculate_score_endpoint(prospect_id: str, db: Session = Depends(get_db)):
    """Recalculates deterministic opportunity score and confidence against the latest audit data."""
    from backend.app.models.audit import AuditReportModel
    from backend.app.services.prospect_scoring import calculate_prospect_score
    from sqlalchemy.orm import joinedload

    prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect with ID '{prospect_id}' not found"
        )

    audit = None
    if prospect.latest_audit_id:
        audit = (
            db.query(AuditReportModel)
            .options(joinedload(AuditReportModel.findings))
            .filter(AuditReportModel.id == prospect.latest_audit_id)
            .first()
        )

    scoring_res = calculate_prospect_score(prospect, audit)
    prospect.opportunity_score = scoring_res["opportunity_score"]
    try:
        db.commit()
        db.refresh(prospect)
    except Exception:
        db.rollback()
        raise
    return db_prospect_to_schema(prospect, scoring_res)

@router.patch("/{prospect_id}")
def update_prospect(prospect_id: str, payload: ProspectUpdate, db: Session = Depends(get_db)):
    prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect with ID '{prospect_id}' not found"
        )
        
    if payload.name is not None:
        prospect.name = payload.name
    if payload.category is not None:
        prospect.category = payload.category
    if payload.location is not None:
        prospect.city = payload.location.city
        prospect.state = payload.location.state
        prospect.country = payload.location.country
    if payload.websiteUrl is not None:
        if payload.websiteUrl != prospect.website_url:
            from backend.app.services.identity_verifier import verify_business_identity
            new_ev = verify_business_identity(
                business_name=payload.name or prospect.name,
                location={"city": prospect.city or "", "state": prospect.state or ""},
                website_url=payload.websiteUrl,
                phone=prospect.phone,
                source_provider=prospect.source_provider,
            )
            prospect.identity_status = new_ev["status"]
            prospect.identity_evidence = json.dumps(new_ev)
        prospect.website_url = payload.websiteUrl
    if payload.identityStatus is not None and payload.identityStatus in (
        "verified", "likely_match", "uncertain", "conflicting", "not_found", "not_checked"
    ):
        # Explicit operator resolution; preserve prior automated evidence for auditability.
        try:
            prior = json.loads(prospect.identity_evidence or "{}")
        except Exception:
            prior = {}
        prior["operator_override"] = {
            "status": payload.identityStatus,
            "previous_status": prospect.identity_status,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        prospect.identity_status = payload.identityStatus
        prospect.identity_evidence = json.dumps(prior)
    if payload.contactProvenance is not None:
        prospect.contact_provenance = json.dumps(payload.contactProvenance)
    if payload.socialProfiles is not None:
        prospect.social_profiles = json.dumps(payload.socialProfiles)
    if payload.websiteStatus is not None:
        prospect.website_status = payload.websiteStatus
    if payload.opportunityScore is not None:
        prospect.opportunity_score = payload.opportunityScore
    if payload.scoreBreakdown is not None:
        prospect.score_urgency = payload.scoreBreakdown.technicalUrgency
        prospect.score_intent = payload.scoreBreakdown.commercialIntent
        prospect.score_ease = payload.scoreBreakdown.resolutionEase
    if payload.status is not None:
        prospect.status = payload.status
    if payload.phone is not None:
        prospect.phone = payload.phone
    if payload.email is not None:
        prospect.email = payload.email
    if payload.tags is not None:
        prospect.tags = json.dumps(payload.tags)
    if payload.recommendedAction is not None:
        prospect.recommended_action = payload.recommendedAction
    if payload.notes is not None:
        prospect.notes = payload.notes
        
    prospect.last_activity = "Updated just now"
    try:
        db.commit()
        db.refresh(prospect)
    except Exception:
        db.rollback()
        raise
    return db_prospect_to_schema(prospect)

@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prospect(prospect_id: str, db: Session = Depends(get_db)):
    prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect with ID '{prospect_id}' not found"
        )
    try:
        from backend.app.models.audit import AuditReportModel
        from backend.app.models.draft import EmailDraftModel
        from backend.app.models.history import EmailHistoryModel

        # 1. Null out prospect_id on associated audit reports
        db.query(AuditReportModel).filter(AuditReportModel.prospect_id == prospect_id).update(
            {AuditReportModel.prospect_id: None}, synchronize_session=False
        )
        # 2. Clean up associated email drafts
        db.query(EmailDraftModel).filter(EmailDraftModel.prospect_id == prospect_id).delete(
            synchronize_session=False
        )
        # 3. Preserve email history but clear prospect link
        db.query(EmailHistoryModel).filter(EmailHistoryModel.prospect_id == prospect_id).update(
            {EmailHistoryModel.prospect_id: None}, synchronize_session=False
        )
        db.delete(prospect)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return None
