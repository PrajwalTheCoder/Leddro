from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class ClaimRationaleSchema(BaseModel):
    claim: str
    findingId: str
    rationale: str
    evidenceType: Optional[str] = "audit_finding"

class EmailDraftBase(BaseModel):
    prospectId: str
    auditId: Optional[str] = None
    recipientEmail: str
    recipientName: str
    subject: str
    subjectAlternatives: List[str] = Field(default_factory=list)
    body: str
    findingsReferenced: List[str] = Field(default_factory=list)
    aiClaimsRationale: List[ClaimRationaleSchema] = Field(default_factory=list)
    outreachPurpose: Optional[str] = "website_improvement"
    writingTone: Optional[str] = "professional"
    aiProvider: Optional[str] = None
    aiModel: Optional[str] = None
    generationMetadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: str = "draft"

class EmailDraftCreate(EmailDraftBase):
    pass

class EmailDraftUpdate(BaseModel):
    recipientEmail: Optional[str] = None
    recipientName: Optional[str] = None
    subject: Optional[str] = None
    subjectAlternatives: Optional[List[str]] = None
    body: Optional[str] = None
    outreachPurpose: Optional[str] = None
    writingTone: Optional[str] = None
    status: Optional[str] = None

class EmailDraftResponse(EmailDraftBase):
    id: str
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True)

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    database: str
    engine: str
    uptimeSeconds: float
    prospectsCount: int
    auditsCount: int
