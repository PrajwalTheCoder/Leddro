from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

OutreachPurpose = Literal[
    "website_improvement",
    "website_redesign",
    "new_website_proposal",
    "website_maintenance",
    "general_introduction"
]

WritingTone = Literal[
    "professional",
    "friendly",
    "concise",
    "consultative"
]

EvidenceType = Literal[
    "audit_finding",
    "prospect_field",
    "user_profile",
    "none"
]

class ClaimEvidence(BaseModel):
    claim: str = Field(..., description="Specific assertion or observation stated in the email draft")
    evidence_type: EvidenceType = Field(default="none", description="Category of real source backing this claim")
    evidence_reference: Optional[str] = Field(None, description="Audit finding ID, prospect attribute, or null")
    rationale: Optional[str] = Field(None, description="Explanation of why this claim is supported by evidence")

class StructuredDraftOutput(BaseModel):
    subject: str = Field(..., min_length=3, description="Clear, business-specific subject line")
    subject_alternatives: List[str] = Field(default_factory=list, description="2-3 alternative subject line variations")
    body: str = Field(..., min_length=20, description="Full email body with greeting, specific evidence, proposal, CTA, and signature")
    claims: List[ClaimEvidence] = Field(default_factory=list, description="List of factual claims and their backing evidence")
    missing_information: List[str] = Field(default_factory=list, description="Gaps identified during draft generation")
    needs_manual_review: bool = Field(default=False, description="True if any claim is unverified or caution is required")

class DraftGenerationRequest(BaseModel):
    prospect_id: str = Field(..., description="ID of the prospect to draft an email for")
    audit_id: Optional[str] = Field(None, description="Optional specific audit report ID to reference")
    purpose: OutreachPurpose = Field(default="website_improvement", description="Primary goal of the outreach")
    tone: WritingTone = Field(default="professional", description="Tone and writing style")
    custom_instructions: Optional[str] = Field(None, max_length=500, description="Optional brief user guidance")
    privacy_consent: bool = Field(..., description="User explicit consent to transmit minimal necessary prospect/audit context to the configured AI provider")
    provider_override: Optional[str] = Field(None, description="Optional provider override (e.g., openai, anthropic, compatible)")
    model_override: Optional[str] = Field(None, description="Optional model override")

class DraftRegenerationRequest(BaseModel):
    purpose: Optional[OutreachPurpose] = Field(None, description="Updated purpose")
    tone: Optional[WritingTone] = Field(None, description="Updated tone")
    custom_instructions: Optional[str] = Field(None, max_length=500, description="Optional updated instructions")
    privacy_consent: bool = Field(default=True, description="Privacy consent confirmation")
    provider_override: Optional[str] = Field(None, description="Optional provider override")
    model_override: Optional[str] = Field(None, description="Optional model override")

class AIProviderInfo(BaseModel):
    provider_id: str
    name: str
    is_configured: bool
    current_model: str
    available_models: List[str]
    status_message: str
    is_active: bool
    is_local: bool
    is_free_tier: bool = False
    data_transmission_notice: str

class AISettingsResponse(BaseModel):
    active_provider: str
    active_model: str
    request_timeout: float
    max_output_tokens: int
    dev_name: str
    dev_title: str
    dev_services: str
    dev_portfolio_url: str
    dev_email: str
    dev_signature: str
    gemini_configured: bool = False
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_masked_key: str = ""
    openai_configured: bool = False
    openai_model: str = "gpt-4o-mini"
    openai_masked_key: str = ""
    anthropic_configured: bool = False
    anthropic_model: str = "claude-3-5-haiku-20241022"
    anthropic_masked_key: str = ""
    compatible_configured: bool = False
    compatible_model: str = "llama3"
    compatible_base_url: str = "http://localhost:11434/v1"

class AISettingsUpdate(BaseModel):
    active_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    anthropic_model: Optional[str] = None
    compatible_api_key: Optional[str] = None
    compatible_model: Optional[str] = None
    compatible_base_url: Optional[str] = None
    request_timeout: Optional[float] = None
    max_output_tokens: Optional[int] = None
    dev_name: Optional[str] = None
    dev_title: Optional[str] = None
    dev_services: Optional[str] = None
    dev_portfolio_url: Optional[str] = None
    dev_email: Optional[str] = None
    dev_signature: Optional[str] = None

class TestConnectionRequest(BaseModel):
    provider_id: Optional[str] = None

class TestConnectionResponse(BaseModel):
    success: bool
    provider_id: str
    model: str
    message: str
    latency_ms: Optional[float] = None
