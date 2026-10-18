import uuid
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.draft import EmailDraftModel
from backend.app.schemas.draft import EmailDraftCreate, EmailDraftUpdate
from backend.app.ai.models import (
    DraftGenerationRequest,
    DraftRegenerationRequest
)
from backend.app.ai.service import ai_service
from backend.app.ai.base import (
    AIConfigurationError,
    AIValidationError,
    AIRateLimitError,
    AITimeoutError,
    AIResponseParseError,
    AIProviderError
)

logger = logging.getLogger("leddro.api.drafts")
router = APIRouter(prefix="/drafts", tags=["Drafts"])

def db_draft_to_dict(model: EmailDraftModel) -> dict:
    alts = []
    if model.subject_alternatives:
        try:
            alts = json.loads(model.subject_alternatives)
        except Exception:
            alts = [model.subject_alternatives]

    findings = []
    if model.findings_referenced:
        try:
            findings = json.loads(model.findings_referenced)
        except Exception:
            findings = [model.findings_referenced]

    rationale = []
    if model.ai_claims_rationale:
        try:
            rationale = json.loads(model.ai_claims_rationale)
        except Exception:
            rationale = []

    meta = {}
    if getattr(model, "generation_metadata", None):
        try:
            meta = json.loads(model.generation_metadata)
        except Exception:
            meta = {}

    return {
        "id": model.id,
        "prospectId": model.prospect_id,
        "auditId": getattr(model, "audit_id", None),
        "recipientEmail": model.recipient_email,
        "recipientName": model.recipient_name,
        "subject": model.subject,
        "subjectAlternatives": alts,
        "body": model.body,
        "findingsReferenced": findings,
        "aiClaimsRationale": rationale,
        "outreachPurpose": getattr(model, "outreach_purpose", "website_improvement"),
        "writingTone": getattr(model, "writing_tone", "professional"),
        "aiProvider": getattr(model, "ai_provider", None),
        "aiModel": getattr(model, "ai_model", None),
        "generationMetadata": meta,
        "status": model.status,
        "createdAt": model.created_at.strftime("%Y-%m-%d %H:%M UTC") if model.created_at else "Just now",
        "updatedAt": model.updated_at.strftime("%Y-%m-%d %H:%M UTC") if model.updated_at else "Just now"
    }

@router.get("")
def list_drafts(
    prospect_id: Optional[str] = Query(None, description="Filter drafts by prospect ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter drafts by status"),
    db: Session = Depends(get_db)
):
    query = db.query(EmailDraftModel)
    if prospect_id:
        query = query.filter(EmailDraftModel.prospect_id == prospect_id)
    if status_filter and status_filter != "all":
        query = query.filter(EmailDraftModel.status == status_filter)

    drafts = query.order_by(EmailDraftModel.created_at.desc()).all()
    return [db_draft_to_dict(d) for d in drafts]

@router.get("/{draft_id}")
def get_draft(draft_id: str, db: Session = Depends(get_db)):
    draft = db.query(EmailDraftModel).filter(EmailDraftModel.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email draft with ID '{draft_id}' not found"
        )
    return db_draft_to_dict(draft)

@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_draft(payload: DraftGenerationRequest, db: Session = Depends(get_db)):
    """
    Generates a personalized, evidence-backed email draft for a prospect using the configured AI provider.
    Requires explicit privacy consent. Validates factual claims against actual audit findings and persists to SQLite.
    """
    try:
        draft_model = await ai_service.generate_draft(db, payload)
        return db_draft_to_dict(draft_model)
    except AIValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except AITimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e)
        )
    except AIResponseParseError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Model response parsing failed: {str(e)}"
        )
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred generating the draft: {str(e)}"
        )

@router.post("/{draft_id}/regenerate")
async def regenerate_draft(draft_id: str, payload: DraftRegenerationRequest, db: Session = Depends(get_db)):
    """
    Regenerates an existing saved draft using updated purpose, tone, or custom guidance.
    Overwrites the draft body while preserving the database draft ID.
    """
    try:
        updated_draft = await ai_service.regenerate_draft(db, draft_id, payload)
        return db_draft_to_dict(updated_draft)
    except AIValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except AITimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e)
        )
    except AIResponseParseError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Model response parsing failed: {str(e)}"
        )
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected regeneration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred regenerating the draft: {str(e)}"
        )

@router.post("", status_code=status.HTTP_201_CREATED)
def create_draft(payload: EmailDraftCreate, db: Session = Depends(get_db)):
    draft_id = f"draft_{uuid.uuid4().hex[:8]}"
    rationale_list = [r.dict() if hasattr(r, "dict") else r for r in payload.aiClaimsRationale]

    model = EmailDraftModel(
        id=draft_id,
        prospect_id=payload.prospectId,
        audit_id=payload.auditId,
        recipient_email=payload.recipientEmail,
        recipient_name=payload.recipientName,
        subject=payload.subject,
        subject_alternatives=json.dumps(payload.subjectAlternatives or []),
        body=payload.body,
        findings_referenced=json.dumps(payload.findingsReferenced or []),
        ai_claims_rationale=json.dumps(rationale_list),
        outreach_purpose=payload.outreachPurpose or "website_improvement",
        writing_tone=payload.writingTone or "professional",
        ai_provider=payload.aiProvider,
        ai_model=payload.aiModel,
        generation_metadata=json.dumps(payload.generationMetadata or {}),
        status=payload.status or "draft"
    )
    
    db.add(model)
    db.commit()
    db.refresh(model)
    return db_draft_to_dict(model)

@router.patch("/{draft_id}")
def update_draft(draft_id: str, payload: EmailDraftUpdate, db: Session = Depends(get_db)):
    draft = db.query(EmailDraftModel).filter(EmailDraftModel.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email draft with ID '{draft_id}' not found"
        )
        
    if payload.recipientEmail is not None:
        draft.recipient_email = payload.recipientEmail
    if payload.recipientName is not None:
        draft.recipient_name = payload.recipientName
    if payload.subject is not None:
        draft.subject = payload.subject
    if payload.subjectAlternatives is not None:
        draft.subject_alternatives = json.dumps(payload.subjectAlternatives)
    if payload.body is not None:
        draft.body = payload.body
    if payload.outreachPurpose is not None:
        draft.outreach_purpose = payload.outreachPurpose
    if payload.writingTone is not None:
        draft.writing_tone = payload.writingTone
    if payload.status is not None:
        draft.status = payload.status

    db.commit()
    db.refresh(draft)
    return db_draft_to_dict(draft)

@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(draft_id: str, db: Session = Depends(get_db)):
    draft = db.query(EmailDraftModel).filter(EmailDraftModel.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email draft with ID '{draft_id}' not found"
        )
    db.delete(draft)
    db.commit()
    return None
