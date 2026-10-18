import uuid
import json
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
    return [db_prospect_to_schema(p) for p in prospects]

@router.get("/{prospect_id}")
def get_prospect(prospect_id: str, db: Session = Depends(get_db)):
    prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect with ID '{prospect_id}' not found"
        )
    return db_prospect_to_schema(prospect)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_prospect(payload: ProspectCreate, db: Session = Depends(get_db)):
    # Duplicate check: check name or website URL
    clean_name = payload.name.strip()
    existing = db.query(ProspectModel).filter(ProspectModel.name.ilike(clean_name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Prospect with name '{clean_name}' already exists in database (ID: {existing.id})"
        )
        
    if payload.websiteUrl:
        clean_url = payload.websiteUrl.strip().rstrip("/")
        existing_url = db.query(ProspectModel).filter(ProspectModel.website_url.ilike(clean_url)).first()
        if existing_url:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Prospect with website '{clean_url}' already exists (ID: {existing_url.id})"
            )

    new_id = f"pros_{uuid.uuid4().hex[:8]}"
    
    new_prospect = ProspectModel(
        id=new_id,
        name=payload.name,
        category=payload.category,
        city=payload.location.city if payload.location else "Navi Mumbai",
        state=payload.location.state if payload.location else "Maharashtra",
        country=payload.location.country if payload.location else "India",
        website_url=payload.websiteUrl,
        website_status=payload.websiteStatus or "active",
        opportunity_score=payload.opportunityScore,
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
        notes=payload.notes or ""
    )
    
    db.add(new_prospect)
    db.commit()
    db.refresh(new_prospect)
    return db_prospect_to_schema(new_prospect)

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
        prospect.website_url = payload.websiteUrl
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
    db.commit()
    db.refresh(prospect)
    return db_prospect_to_schema(prospect)

@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prospect(prospect_id: str, db: Session = Depends(get_db)):
    prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect with ID '{prospect_id}' not found"
        )
    db.delete(prospect)
    db.commit()
    return None
