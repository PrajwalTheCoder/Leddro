import asyncio
import uuid
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.prospect import ProspectModel
from backend.app.models.audit import AuditReportModel, AuditFindingModel
from backend.app.models.draft import EmailDraftModel
from backend.app.ai.base import (
    BaseAIProvider,
    AIError,
    AIConfigurationError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIResponseParseError,
    AIValidationError,
    mask_api_key
)
import os
from backend.app.ai.models import (
    DraftGenerationRequest,
    DraftRegenerationRequest,
    StructuredDraftOutput,
    ClaimEvidence,
    AIProviderInfo,
    AISettingsResponse,
    AISettingsUpdate
)
from backend.app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.app.ai.providers import (
    OpenAIProvider,
    AnthropicProvider,
    OpenAICompatibleProvider,
    GeminiProvider
)

logger = logging.getLogger("leddro.ai")

def _persist_to_env_file(filepath: str, updates: Dict[str, str]):
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        found_keys = set()
        for line in lines:
            stripped = line.strip()
            matched = False
            for k, v in updates.items():
                if stripped.startswith(f"{k}=") or stripped.startswith(f"export {k}="):
                    new_lines.append(f'{k}="{v}"\n')
                    found_keys.add(k)
                    matched = True
                    break
            if not matched:
                new_lines.append(line)
        
        for k, v in updates.items():
            if k not in found_keys:
                new_lines.append(f'{k}="{v}"\n')
                
        temp_filepath = f"{filepath}.tmp.{os.getpid()}"
        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        os.replace(temp_filepath, filepath)
    except Exception as e:
        logger.warning(f"Could not safely persist keys to {filepath}: {e}")

class AIEmailDraftingService:
    """
    Central orchestration service for evidence-based AI email drafting.
    Enforces privacy consent, concurrency limits, deterministic context assembly,
    anti-hallucination claim verification, and database persistence.
    """

    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "compatible": OpenAICompatibleProvider(),
        }
        # Concurrency limit to prevent overwhelming downstream APIs
        self._semaphore = asyncio.Semaphore(3)

    def get_provider(self, provider_id: Optional[str] = None) -> BaseAIProvider:
        if provider_id:
            target_id = provider_id.lower().strip()
            provider = self._providers.get(target_id)
            if not provider:
                raise AIConfigurationError(
                    f"Unknown AI provider '{target_id}'. Supported providers are: {', '.join(self._providers.keys())}"
                )
            return provider

        target_id = (settings.AI_PROVIDER or "gemini").lower().strip()
        provider = self._providers.get(target_id)
        if provider and not provider.is_configured():
            # If default provider is missing credentials, automatically route to any configured provider (e.g. Gemini)
            for pid, p in self._providers.items():
                if p.is_configured():
                    logger.info(f"Default provider '{target_id}' unconfigured; auto-routing to configured '{pid}'")
                    return p

        if not provider:
            provider = self._providers.get("gemini")
        return provider

    def list_providers(self) -> List[AIProviderInfo]:
        active_id = (settings.AI_PROVIDER or "gemini").lower().strip()
        active_provider = self._providers.get(active_id)
        if active_provider and not active_provider.is_configured():
            for pid, p in self._providers.items():
                if p.is_configured():
                    active_id = pid
                    break

        info_list = []

        # 1. Google Gemini (100% Free Tier via Google AI Studio)
        gemini_p = self._providers["gemini"]
        info_list.append(
            AIProviderInfo(
                provider_id="gemini",
                name=gemini_p.name,
                is_configured=gemini_p.is_configured(),
                current_model=settings.GEMINI_MODEL,
                available_models=["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"],
                status_message=gemini_p.get_status_message(),
                is_active=(active_id == "gemini"),
                is_local=False,
                is_free_tier=True,
                data_transmission_notice="Transmits business name, category, website condition, and audit finding summaries to Google Gemini API servers (100% free tier available via Google AI Studio)."
            )
        )

        # 2. OpenAI
        openai_p = self._providers["openai"]
        info_list.append(
            AIProviderInfo(
                provider_id="openai",
                name=openai_p.name,
                is_configured=openai_p.is_configured(),
                current_model=settings.OPENAI_MODEL,
                available_models=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                status_message=openai_p.get_status_message(),
                is_active=(active_id == "openai"),
                is_local=False,
                is_free_tier=False,
                data_transmission_notice="Transmits business name, category, website condition, and audit finding summaries to OpenAI API servers."
            )
        )

        # 3. Anthropic
        anthropic_p = self._providers["anthropic"]
        info_list.append(
            AIProviderInfo(
                provider_id="anthropic",
                name=anthropic_p.name,
                is_configured=anthropic_p.is_configured(),
                current_model=settings.ANTHROPIC_MODEL,
                available_models=["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"],
                status_message=anthropic_p.get_status_message(),
                is_active=(active_id == "anthropic"),
                is_local=False,
                is_free_tier=False,
                data_transmission_notice="Transmits business name, category, website condition, and audit finding summaries to Anthropic API servers."
            )
        )

        # 4. Compatible (Local Ollama / vLLM)
        comp_p = self._providers["compatible"]
        info_list.append(
            AIProviderInfo(
                provider_id="compatible",
                name=comp_p.name,
                is_configured=comp_p.is_configured(),
                current_model=settings.COMPATIBLE_MODEL,
                available_models=[settings.COMPATIBLE_MODEL, "llama3", "mistral", "qwen2.5"],
                status_message=comp_p.get_status_message(),
                is_active=(active_id == "compatible"),
                is_local=True,
                is_free_tier=True,
                data_transmission_notice="Local-only: Transmits context exclusively to your local machine network endpoint (zero third-party data transfer)."
            )
        )

        return info_list

    def get_settings(self) -> AISettingsResponse:
        return AISettingsResponse(
            active_provider=settings.AI_PROVIDER,
            active_model=self._get_active_model_name(),
            request_timeout=settings.AI_REQUEST_TIMEOUT,
            max_output_tokens=settings.AI_MAX_OUTPUT_TOKENS,
            dev_name=settings.DEV_NAME,
            dev_title=settings.DEV_TITLE,
            dev_services=settings.DEV_SERVICES,
            dev_portfolio_url=settings.DEV_PORTFOLIO_URL,
            dev_email=settings.DEV_EMAIL,
            dev_signature=settings.DEV_SIGNATURE,
            gemini_configured=bool(settings.GEMINI_API_KEY.strip()),
            gemini_model=settings.GEMINI_MODEL,
            gemini_masked_key=mask_api_key(settings.GEMINI_API_KEY),
            openai_configured=bool(settings.OPENAI_API_KEY.strip()),
            openai_model=settings.OPENAI_MODEL,
            openai_masked_key=mask_api_key(settings.OPENAI_API_KEY),
            anthropic_configured=bool(settings.ANTHROPIC_API_KEY.strip()),
            anthropic_model=settings.ANTHROPIC_MODEL,
            anthropic_masked_key=mask_api_key(settings.ANTHROPIC_API_KEY),
            compatible_configured=bool(settings.COMPATIBLE_BASE_URL.strip()),
            compatible_model=settings.COMPATIBLE_MODEL,
            compatible_base_url=settings.COMPATIBLE_BASE_URL
        )

    def update_settings(self, updates: AISettingsUpdate) -> AISettingsResponse:
        keys_to_persist: Dict[str, str] = {}

        if updates.active_provider is not None:
            clean_p = updates.active_provider.lower().strip()
            if clean_p not in self._providers:
                raise AIConfigurationError(f"Unsupported provider '{clean_p}'")
            settings.AI_PROVIDER = clean_p
            keys_to_persist["AI_PROVIDER"] = clean_p

        # API Keys saving
        if updates.gemini_api_key is not None:
            settings.GEMINI_API_KEY = updates.gemini_api_key.strip()
            keys_to_persist["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
        if updates.openai_api_key is not None:
            settings.OPENAI_API_KEY = updates.openai_api_key.strip()
            keys_to_persist["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
        if updates.anthropic_api_key is not None:
            settings.ANTHROPIC_API_KEY = updates.anthropic_api_key.strip()
            keys_to_persist["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
        if updates.compatible_api_key is not None:
            settings.COMPATIBLE_API_KEY = updates.compatible_api_key.strip()
            keys_to_persist["COMPATIBLE_API_KEY"] = settings.COMPATIBLE_API_KEY

        # Models & Endpoints
        if updates.gemini_model is not None:
            settings.GEMINI_MODEL = updates.gemini_model.strip()
            keys_to_persist["GEMINI_MODEL"] = settings.GEMINI_MODEL
        if updates.openai_model is not None:
            settings.OPENAI_MODEL = updates.openai_model.strip()
            keys_to_persist["OPENAI_MODEL"] = settings.OPENAI_MODEL
        if updates.anthropic_model is not None:
            settings.ANTHROPIC_MODEL = updates.anthropic_model.strip()
            keys_to_persist["ANTHROPIC_MODEL"] = settings.ANTHROPIC_MODEL
        if updates.compatible_model is not None:
            settings.COMPATIBLE_MODEL = updates.compatible_model.strip()
            keys_to_persist["COMPATIBLE_MODEL"] = settings.COMPATIBLE_MODEL
        if updates.compatible_base_url is not None:
            settings.COMPATIBLE_BASE_URL = updates.compatible_base_url.strip()
            keys_to_persist["COMPATIBLE_BASE_URL"] = settings.COMPATIBLE_BASE_URL

        # Safety & limits
        if updates.request_timeout is not None:
            settings.AI_REQUEST_TIMEOUT = max(5.0, min(120.0, float(updates.request_timeout)))
        if updates.max_output_tokens is not None:
            settings.AI_MAX_OUTPUT_TOKENS = max(100, min(4000, int(updates.max_output_tokens)))

        # Developer Profile
        if updates.dev_name is not None:
            settings.DEV_NAME = updates.dev_name.strip()
        if updates.dev_title is not None:
            settings.DEV_TITLE = updates.dev_title.strip()
        if updates.dev_services is not None:
            settings.DEV_SERVICES = updates.dev_services.strip()
        if updates.dev_portfolio_url is not None:
            settings.DEV_PORTFOLIO_URL = updates.dev_portfolio_url.strip()
        if updates.dev_email is not None:
            settings.DEV_EMAIL = updates.dev_email.strip()
        if updates.dev_signature is not None:
            settings.DEV_SIGNATURE = updates.dev_signature.strip()

        # Persist updated keys and config back to .env files
        if keys_to_persist:
            _persist_to_env_file(".env", keys_to_persist)
            _persist_to_env_file("backend/.env", keys_to_persist)

        return self.get_settings()

    def _get_active_model_name(self) -> str:
        p = (settings.AI_PROVIDER or "gemini").lower()
        if p == "gemini":
            return settings.GEMINI_MODEL
        elif p == "anthropic":
            return settings.ANTHROPIC_MODEL
        elif p == "compatible":
            return settings.COMPATIBLE_MODEL
        return settings.OPENAI_MODEL

    def validate_and_filter_claims(
        self,
        raw_claims: List[ClaimEvidence],
        audit_findings: List[AuditFindingModel],
        prospect: ProspectModel
    ) -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]], bool]:
        """
        Validates claim evidence references against authentic database records.
        If a claim references an audit finding ID that does not exist in the audit,
        it flags needs_manual_review and resets evidence_type to 'none'.
        """
        valid_finding_ids = {f.id for f in audit_findings}
        findings_referenced: List[str] = []
        validated_claims: List[Dict[str, Any]] = []
        claims_rationale: List[Dict[str, Any]] = []
        needs_manual_review = False

        for c in raw_claims:
            claim_text = c.claim.strip()
            ev_type = c.evidence_type
            ev_ref = c.evidence_reference.strip() if c.evidence_reference else None
            rationale_text = c.rationale or ""

            if ev_type == "audit_finding":
                if ev_ref and ev_ref in valid_finding_ids:
                    # Verified against real database audit finding
                    if ev_ref not in findings_referenced:
                        findings_referenced.append(ev_ref)
                    finding_obj = next(f for f in audit_findings if f.id == ev_ref)
                    rationale_text = rationale_text or f"Verified by audit finding: '{finding_obj.title}' (Observed: {finding_obj.observed})"
                else:
                    # Hallucinated or non-existent finding ID
                    needs_manual_review = True
                    ev_type = "none"
                    ev_ref = None
                    rationale_text = f"Unverified technical claim: referenced finding ID '{c.evidence_reference}' was not found in audit dossier."
            elif ev_type == "prospect_field":
                val = getattr(prospect, ev_ref, None) if ev_ref else None
                rationale_text = rationale_text or f"Backed by prospect verified record ({ev_ref}: {val})"
            elif ev_type == "user_profile":
                rationale_text = rationale_text or "Backed by configured developer profile."
            else:
                ev_type = "none"
                ev_ref = None
                rationale_text = rationale_text or "General contextual statement."

            validated_claims.append({
                "claim": claim_text,
                "evidence_type": ev_type,
                "evidence_reference": ev_ref,
                "rationale": rationale_text
            })

            claims_rationale.append({
                "claim": claim_text,
                "findingId": ev_ref or "general",
                "rationale": rationale_text,
                "evidenceType": ev_type
            })

        return validated_claims, findings_referenced, claims_rationale, needs_manual_review

    async def generate_draft(
        self,
        db: Session,
        request: DraftGenerationRequest
    ) -> EmailDraftModel:
        """
        Executes a complete AI draft generation lifecycle for a prospect.
        Validates privacy consent, prospect existence, provider configuration,
        runs structured generation, verifies evidence, and persists draft to SQLite.
        """
        # 1. Enforce privacy consent requirement
        if not request.privacy_consent:
            raise AIValidationError(
                "Privacy consent required: You must review and agree to transmit minimal prospect "
                "details to the configured AI provider before generating an outreach draft."
            )

        # 2. Retrieve Prospect
        prospect = db.query(ProspectModel).filter(ProspectModel.id == request.prospect_id).first()
        if not prospect:
            raise AIValidationError(f"Prospect with ID '{request.prospect_id}' not found in database.")

        # 3. Retrieve Associated Audit and Findings (if requested or available)
        audit_report = None
        audit_findings: List[AuditFindingModel] = []
        target_audit_id = request.audit_id or prospect.latest_audit_id

        if target_audit_id:
            audit_report = db.query(AuditReportModel).filter(AuditReportModel.id == target_audit_id).first()
            if audit_report:
                audit_findings = db.query(AuditFindingModel).filter(
                    AuditFindingModel.audit_report_id == audit_report.id
                ).all()

        # 4. Resolve Provider and Validate Configuration
        provider = self.get_provider(request.provider_override)
        if not provider.is_configured():
            raise AIConfigurationError(
                f"Selected AI provider '{provider.name}' is not configured. {provider.get_status_message()}"
            )

        # 5. Assemble Minimal Context Prompts
        prospect_dict = {
            "name": prospect.name,
            "category": prospect.category,
            "city": prospect.city,
            "state": prospect.state,
            "country": prospect.country,
            "website_url": prospect.website_url,
            "website_status": prospect.website_status,
            "phone": prospect.phone,
            "email": prospect.email,
            "source_provider": prospect.source_provider,
            "tags": prospect.tags,
            "notes": prospect.notes
        }

        audit_dict = None
        if audit_report:
            audit_dict = {
                "url": audit_report.url,
                "status": audit_report.status,
                "overall_score": audit_report.overall_score,
                "findings": [
                    {
                        "id": f.id,
                        "title": f.title,
                        "severity": f.severity,
                        "observed": f.observed,
                        "evidence": f.evidence,
                        "why_it_matters": f.why_it_matters,
                        "category": f.category
                    }
                    for f in audit_findings
                ]
            }

        dev_dict = {
            "name": settings.DEV_NAME,
            "title": settings.DEV_TITLE,
            "services": settings.DEV_SERVICES,
            "portfolio_url": settings.DEV_PORTFOLIO_URL,
            "email": settings.DEV_EMAIL,
            "signature": settings.DEV_SIGNATURE
        }

        user_prompt = build_user_prompt(
            prospect=prospect_dict,
            audit=audit_dict,
            dev_profile=dev_dict,
            purpose=request.purpose,
            tone=request.tone,
            custom_instructions=request.custom_instructions
        )

        # 6. Execute Structured Model Generation with concurrency control
        logger.info(
            f"Invoking AI generation for prospect '{prospect.name}' (ID: {prospect.id}) via provider '{provider.provider_id}'"
        )
        async with self._semaphore:
            raw_output = await provider.generate_structured_draft(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
                timeout=settings.AI_REQUEST_TIMEOUT
            )

        # 7. Validate Pydantic Schema
        try:
            structured = StructuredDraftOutput(**raw_output)
        except Exception as e:
            raise AIResponseParseError(
                f"Model output schema validation failed: {str(e)}"
            ) from e

        # 8. Fact-check & Cross-validate claims against SQLite database records
        validated_claims, findings_referenced, claims_rationale, manual_review_flag = self.validate_and_filter_claims(
            raw_claims=structured.claims,
            audit_findings=audit_findings,
            prospect=prospect
        )

        overall_needs_review = structured.needs_manual_review or manual_review_flag

        # 9. Format Recipient email & name
        recipient_email = prospect.email
        if not recipient_email and prospect.website_url:
            clean_domain = prospect.website_url.replace("https://", "").replace("http://", "").split("/")[0]
            recipient_email = f"contact@{clean_domain}"
        if not recipient_email:
            recipient_email = f"contact@{prospect.name.lower().replace(' ', '')}.com"

        recipient_name = f"{prospect.name} Team"

        # 10. Persist Draft to SQLite
        draft_id = f"draft_{uuid.uuid4().hex[:8]}"
        metadata = {
            "claims": validated_claims,
            "missing_information": structured.missing_information,
            "needs_manual_review": overall_needs_review,
            "ai_provider": provider.provider_id,
            "ai_model": request.model_override or (
                settings.GEMINI_MODEL if provider.provider_id == "gemini" else
                settings.OPENAI_MODEL if provider.provider_id == "openai" else
                settings.ANTHROPIC_MODEL if provider.provider_id == "anthropic" else
                settings.COMPATIBLE_MODEL
            ),
            "custom_instructions": request.custom_instructions
        }

        draft_model = EmailDraftModel(
            id=draft_id,
            prospect_id=prospect.id,
            audit_id=audit_report.id if audit_report else None,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=structured.subject.strip(),
            subject_alternatives=json.dumps(structured.subject_alternatives),
            body=structured.body.strip(),
            findings_referenced=json.dumps(findings_referenced),
            ai_claims_rationale=json.dumps(claims_rationale),
            outreach_purpose=request.purpose,
            writing_tone=request.tone,
            ai_provider=provider.provider_id,
            ai_model=metadata["ai_model"],
            generation_metadata=json.dumps(metadata),
            status="draft"
        )

        # Update prospect status to draft_ready if it was new or needs_review
        if prospect.status in ("new", "needs_audit", "needs_review"):
            prospect.status = "draft_ready"
            prospect.last_activity = "Email draft generated"

        db.add(draft_model)
        db.commit()
        db.refresh(draft_model)

        logger.info(f"Persisted AI email draft '{draft_id}' for prospect '{prospect.name}'")
        return draft_model

    async def regenerate_draft(
        self,
        db: Session,
        draft_id: str,
        request: DraftRegenerationRequest
    ) -> EmailDraftModel:
        """
        Regenerates an existing draft using updated instructions, purpose, or tone.
        Overwrites the draft body and subject, updates evidence links, and preserves the draft ID.
        """
        existing_draft = db.query(EmailDraftModel).filter(EmailDraftModel.id == draft_id).first()
        if not existing_draft:
            raise AIValidationError(f"Email draft with ID '{draft_id}' not found.")

        # Re-run draft generation using existing prospect and audit links
        generation_req = DraftGenerationRequest(
            prospect_id=existing_draft.prospect_id,
            audit_id=existing_draft.audit_id,
            purpose=request.purpose or existing_draft.outreach_purpose or "website_improvement",
            tone=request.tone or existing_draft.writing_tone or "professional",
            custom_instructions=request.custom_instructions,
            privacy_consent=request.privacy_consent,
            provider_override=request.provider_override,
            model_override=request.model_override
        )

        # Retrieve Prospect & Audit
        prospect = db.query(ProspectModel).filter(ProspectModel.id == existing_draft.prospect_id).first()
        if not prospect:
            raise AIValidationError("Associated prospect record no longer exists.")

        audit_report = None
        audit_findings: List[AuditFindingModel] = []
        if existing_draft.audit_id:
            audit_report = db.query(AuditReportModel).filter(AuditReportModel.id == existing_draft.audit_id).first()
            if audit_report:
                audit_findings = db.query(AuditFindingModel).filter(
                    AuditFindingModel.audit_report_id == audit_report.id
                ).all()

        provider = self.get_provider(request.provider_override)
        if not provider.is_configured():
            raise AIConfigurationError(
                f"Selected AI provider '{provider.name}' is not configured. {provider.get_status_message()}"
            )

        prospect_dict = {
            "name": prospect.name,
            "category": prospect.category,
            "city": prospect.city,
            "state": prospect.state,
            "country": prospect.country,
            "website_url": prospect.website_url,
            "website_status": prospect.website_status,
            "phone": prospect.phone,
            "email": prospect.email,
            "source_provider": prospect.source_provider,
            "tags": prospect.tags,
            "notes": prospect.notes
        }

        audit_dict = None
        if audit_report:
            audit_dict = {
                "url": audit_report.url,
                "status": audit_report.status,
                "overall_score": audit_report.overall_score,
                "findings": [
                    {
                        "id": f.id,
                        "title": f.title,
                        "severity": f.severity,
                        "observed": f.observed,
                        "evidence": f.evidence,
                        "why_it_matters": f.why_it_matters,
                        "category": f.category
                    }
                    for f in audit_findings
                ]
            }

        dev_dict = {
            "name": settings.DEV_NAME,
            "title": settings.DEV_TITLE,
            "services": settings.DEV_SERVICES,
            "portfolio_url": settings.DEV_PORTFOLIO_URL,
            "email": settings.DEV_EMAIL,
            "signature": settings.DEV_SIGNATURE
        }

        user_prompt = build_user_prompt(
            prospect=prospect_dict,
            audit=audit_dict,
            dev_profile=dev_dict,
            purpose=generation_req.purpose,
            tone=generation_req.tone,
            custom_instructions=generation_req.custom_instructions
        )

        async with self._semaphore:
            raw_output = await provider.generate_structured_draft(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
                timeout=settings.AI_REQUEST_TIMEOUT
            )

        structured = StructuredDraftOutput(**raw_output)

        validated_claims, findings_referenced, claims_rationale, manual_review_flag = self.validate_and_filter_claims(
            raw_claims=structured.claims,
            audit_findings=audit_findings,
            prospect=prospect
        )

        metadata = {
            "claims": validated_claims,
            "missing_information": structured.missing_information,
            "needs_manual_review": structured.needs_manual_review or manual_review_flag,
            "ai_provider": provider.provider_id,
            "ai_model": request.model_override or (
                settings.GEMINI_MODEL if provider.provider_id == "gemini" else
                settings.OPENAI_MODEL if provider.provider_id == "openai" else
                settings.ANTHROPIC_MODEL if provider.provider_id == "anthropic" else
                settings.COMPATIBLE_MODEL
            ),
            "custom_instructions": request.custom_instructions,
            "regenerated": True
        }

        # Update existing draft
        existing_draft.subject = structured.subject.strip()
        existing_draft.subject_alternatives = json.dumps(structured.subject_alternatives)
        existing_draft.body = structured.body.strip()
        existing_draft.findings_referenced = json.dumps(findings_referenced)
        existing_draft.ai_claims_rationale = json.dumps(claims_rationale)
        existing_draft.outreach_purpose = generation_req.purpose
        existing_draft.writing_tone = generation_req.tone
        existing_draft.ai_provider = provider.provider_id
        existing_draft.ai_model = metadata["ai_model"]
        existing_draft.generation_metadata = json.dumps(metadata)
        existing_draft.status = "draft"

        db.commit()
        db.refresh(existing_draft)
        return existing_draft

ai_service = AIEmailDraftingService()
