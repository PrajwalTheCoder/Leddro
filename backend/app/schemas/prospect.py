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
    identityStatus: Optional[str] = "not_checked"
    identityEvidence: Optional[Dict[str, Any]] = None
    contactProvenance: Optional[Dict[str, Any]] = None
    socialProfiles: Optional[Dict[str, Any]] = None
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
    identityStatus: Optional[str] = None
    identityEvidence: Optional[Dict[str, Any]] = None
    contactProvenance: Optional[Dict[str, Any]] = None
    socialProfiles: Optional[Dict[str, Any]] = None
    discoveredAt: Optional[str] = None
    lastVerifiedAt: Optional[str] = None

class ScoringEvidenceSchema(BaseModel):
    findingId: Optional[str] = None
    title: str
    severity: str
    category: Optional[str] = None
    observed: Optional[str] = None
    contribution: int = 0

class ScoringFactorSchema(BaseModel):
    key: str
    label: str
    contribution: int
    maxContribution: int
    status: str
    nature: str = "informational"
    summary: str
    evidence: List[ScoringEvidenceSchema] = Field(default_factory=list)

class SeveritySummarySchema(BaseModel):
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0

class ProspectScoringSchema(BaseModel):
    opportunityScore: int
    scoreVersion: str = "1.0"
    confidenceScore: int
    priorityLabel: str
    contactReadiness: str
    contactTrust: Optional[str] = None
    identityStatus: Optional[str] = None
    auditStatus: str
    auditAgeDays: Optional[int] = None
    auditTimestamp: Optional[str] = None
    severitySummary: SeveritySummarySchema = Field(default_factory=SeveritySummarySchema)
    factors: List[ScoringFactorSchema] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    recommendedActions: List[str] = Field(default_factory=list)

class ProspectResponse(ProspectBase):
    id: str
    lastActivity: str = "Just now"
    auditCount: int = 0
    latestAuditId: Optional[str] = None
    scoring: Optional[ProspectScoringSchema] = None

    model_config = ConfigDict(from_attributes=True)

def format_scoring_result_for_schema(scoring_result: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to convert raw snake_case scoring dictionary to camelCase schema matching frontend."""
    return {
        "opportunityScore": scoring_result["opportunity_score"],
        "scoreVersion": scoring_result["score_version"],
        "confidenceScore": scoring_result["confidence_score"],
        "priorityLabel": scoring_result["priority_label"],
        "contactReadiness": scoring_result["contact_readiness"],
        "contactTrust": scoring_result.get("contact_trust"),
        "identityStatus": scoring_result.get("identity_status"),
        "auditStatus": scoring_result["audit_status"],
        "auditAgeDays": scoring_result["audit_age_days"],
        "auditTimestamp": scoring_result["audit_timestamp"],
        "severitySummary": scoring_result["severity_summary"],
        "factors": [
            {
                "key": f["key"],
                "label": f["label"],
                "contribution": f["contribution"],
                "maxContribution": f["max_contribution"],
                "status": f["status"],
                "nature": f.get("nature", "informational"),
                "summary": f["summary"],
                "evidence": [
                    {
                        "findingId": ev.get("finding_id"),
                        "title": ev.get("title", ""),
                        "severity": ev.get("severity", "medium"),
                        "category": ev.get("category"),
                        "observed": ev.get("observed"),
                        "contribution": ev.get("contribution", 0)
                    } for ev in f.get("evidence", [])
                ]
            } for f in f_list
        ] if (f_list := scoring_result.get("factors")) else [],
        "limitations": scoring_result.get("limitations", []),
        "recommendedActions": scoring_result.get("recommended_actions", [])
    }

def db_prospect_to_schema(model, scoring_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Helper to convert ProspectModel to dictionary matching frontend Prospect schema"""
    tags_list = []
    if model.tags:
        try:
            tags_list = json.loads(model.tags)
        except Exception:
            tags_list = [model.tags]

    # If no scoring_result was provided, compute on-the-fly without audit
    opp_score = getattr(model, "opportunity_score", None)
    if opp_score is None:
        opp_score = scoring_result["opportunity_score"] if scoring_result else 70

    formatted_scoring = format_scoring_result_for_schema(scoring_result) if scoring_result else None
    if formatted_scoring and opp_score is not None:
        formatted_scoring["opportunityScore"] = opp_score

    # Safe JSON parsing helper for model text columns
    def _parse_json_field(val: Any) -> Optional[Dict[str, Any]]:
        if isinstance(val, dict):
            return val
        if isinstance(val, str) and val.strip():
            try:
                return json.loads(val)
            except Exception:
                return None
        return None

    identity_status = getattr(model, "identity_status", None) or "not_checked"
    identity_evidence = _parse_json_field(getattr(model, "identity_evidence", None))
    contact_provenance = _parse_json_field(getattr(model, "contact_provenance", None))
    social_profiles = _parse_json_field(getattr(model, "social_profiles", None))

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
        "opportunityScore": opp_score,
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
        "identityStatus": identity_status,
        "identityEvidence": identity_evidence,
        "contactProvenance": contact_provenance,
        "socialProfiles": social_profiles,
        "discoveredAt": model.discovered_at.isoformat() if getattr(model, "discovered_at", None) else None,
        "lastVerifiedAt": model.last_verified_at.isoformat() if getattr(model, "last_verified_at", None) else None,
        "scoring": formatted_scoring
    }
