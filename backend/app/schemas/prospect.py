from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
import json

class LocationSchema(BaseModel):
    city: str = "Navi Mumbai"
    state: str = "Maharashtra"
    country: str = "India"

class ScoreBreakdownSchema(BaseModel):
    technicalUrgency: int = 25
    commercialIntent: int = 25
    resolutionEase: int = 20

class ProspectBase(BaseModel):
    name: str
    category: str = "Commercial Services"
    location: LocationSchema = Field(default_factory=LocationSchema)
    websiteUrl: Optional[str] = None
    websiteStatus: str = "active"
    opportunityScore: int = 70
    scoreBreakdown: ScoreBreakdownSchema = Field(default_factory=ScoreBreakdownSchema)
    status: str = "new"
    phone: Optional[str] = None
    email: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    recommendedAction: Optional[str] = "Execute initial website audit."
    notes: Optional[str] = None
    sourceProvider: Optional[str] = None
    sourceRecordId: Optional[str] = None
    sourceUrl: Optional[str] = None
    discoveredAt: Optional[str] = None
    lastVerifiedAt: Optional[str] = None

class ProspectCreate(ProspectBase):
    pass

class ProspectUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    location: Optional[LocationSchema] = None
    websiteUrl: Optional[str] = None
    websiteStatus: Optional[str] = None
    opportunityScore: Optional[int] = None
    scoreBreakdown: Optional[ScoreBreakdownSchema] = None
    status: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tags: Optional[List[str]] = None
    recommendedAction: Optional[str] = None
    notes: Optional[str] = None
    sourceProvider: Optional[str] = None
    sourceRecordId: Optional[str] = None
    sourceUrl: Optional[str] = None
    discoveredAt: Optional[str] = None
    lastVerifiedAt: Optional[str] = None

class ProspectResponse(ProspectBase):
    id: str
    lastActivity: str = "Just now"
    auditCount: int = 0
    latestAuditId: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

def db_prospect_to_schema(model) -> Dict[str, Any]:
    """Helper to convert ProspectModel to dictionary matching frontend Prospect schema"""
    tags_list = []
    if model.tags:
        try:
            tags_list = json.loads(model.tags)
        except Exception:
            tags_list = [model.tags]

    return {
        "id": model.id,
        "name": model.name,
        "category": model.category,
        "location": {
            "city": model.city,
            "state": model.state,
            "country": model.country
        },
        "websiteUrl": model.website_url,
        "websiteStatus": model.website_status,
        "opportunityScore": model.opportunity_score,
        "scoreBreakdown": {
            "technicalUrgency": model.score_urgency,
            "commercialIntent": model.score_intent,
            "resolutionEase": model.score_ease
        },
        "status": model.status,
        "lastActivity": model.last_activity,
        "phone": model.phone,
        "email": model.email,
        "auditCount": model.audit_count,
        "latestAuditId": model.latest_audit_id,
        "tags": tags_list,
        "recommendedAction": model.recommended_action,
        "notes": model.notes,
        "sourceProvider": getattr(model, "source_provider", None),
        "sourceRecordId": getattr(model, "source_record_id", None),
        "sourceUrl": getattr(model, "source_url", None),
        "discoveredAt": model.discovered_at.isoformat() if getattr(model, "discovered_at", None) else None,
        "lastVerifiedAt": model.last_verified_at.isoformat() if getattr(model, "last_verified_at", None) else None
    }
