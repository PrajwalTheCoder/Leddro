from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json

class FindingSchema(BaseModel):
    id: str
    prospectId: Optional[str] = None
    title: str
    severity: str  # high, medium, low, info
    checkStatus: str = "WARNING"  # PASS, WARNING, FAIL, ERROR, NOT_CHECKED
    observed: str
    evidence: str
    whyItMatters: str = ""
    recommendedAction: str = ""
    confidence: float = 1.0
    category: str = "reachability"  # security, reachability, performance, seo_meta, conversion
    httpStatus: Optional[int] = None
    responseTimeMs: Optional[int] = None
    checkedUrl: Optional[str] = None

class RawDnsSchema(BaseModel):
    aRecord: str = "Unresolved"
    mxRecord: str = "None"
    responseMs: int = 0
    nameservers: List[str] = Field(default_factory=list)

class RawSslSchema(BaseModel):
    valid: bool = False
    issuer: str = "None"
    expiresDays: int = 0
    tlsVersion: str = "N/A"
    cipher: str = "N/A"

class PerformanceSchema(BaseModel):
    ttfbMs: int = 0
    domReadyMs: int = 0
    pageSizeKb: int = 0
    mobileViewportPresent: bool = False

class AuditReportResponse(BaseModel):
    id: str
    prospectId: Optional[str] = None
    url: str
    timestamp: str
    status: str = "completed"
    overallScore: int = 70
    findings: List[FindingSchema] = Field(default_factory=list)
    rawDns: RawDnsSchema = Field(default_factory=RawDnsSchema)
    rawSsl: RawSslSchema = Field(default_factory=RawSslSchema)
    performance: PerformanceSchema = Field(default_factory=PerformanceSchema)
    headers: Dict[str, str] = Field(default_factory=dict)

class AuditRunRequest(BaseModel):
    url: str
    prospectId: Optional[str] = None

def db_audit_to_schema(report_model, findings_models=None) -> Dict[str, Any]:
    findings_list = []
    items = findings_models if findings_models is not None else report_model.findings
    for f in items:
        findings_list.append({
            "id": f.id,
            "prospectId": report_model.prospect_id,
            "title": f.title,
            "severity": f.severity,
            "checkStatus": f.check_status,
            "observed": f.observed,
            "evidence": f.evidence,
            "whyItMatters": f.why_it_matters or "",
            "recommendedAction": f.recommended_action or "",
            "confidence": f.confidence,
            "category": f.category,
            "httpStatus": f.http_status,
            "responseTimeMs": f.response_time_ms,
            "checkedUrl": f.checked_url
        })

    def safe_json(val, default):
        if not val:
            return default
        if isinstance(val, dict):
            return val
        try:
            return json.loads(val)
        except Exception:
            return default

    return {
        "id": report_model.id,
        "prospectId": report_model.prospect_id,
        "url": report_model.url,
        "timestamp": report_model.timestamp,
        "status": report_model.status,
        "overallScore": report_model.overall_score,
        "findings": findings_list,
        "rawDns": safe_json(report_model.raw_dns, {"aRecord": "N/A", "mxRecord": "N/A", "responseMs": 0, "nameservers": []}),
        "rawSsl": safe_json(report_model.raw_ssl, {"valid": False, "issuer": "None", "expiresDays": 0, "tlsVersion": "N/A", "cipher": "N/A"}),
        "performance": safe_json(report_model.performance, {"ttfbMs": 0, "domReadyMs": 0, "pageSizeKb": 0, "mobileViewportPresent": False}),
        "headers": safe_json(report_model.headers, {})
    }
