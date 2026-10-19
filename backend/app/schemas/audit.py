from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
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

class AuditCompareRequest(BaseModel):
    older_audit_id: Optional[str] = None
    newer_audit_id: Optional[str] = None
    olderAuditId: Optional[str] = None
    newerAuditId: Optional[str] = None

    def get_older_id(self) -> str:
        return (self.older_audit_id or self.olderAuditId or "").strip()

    def get_newer_id(self) -> str:
        return (self.newer_audit_id or self.newerAuditId or "").strip()

class FindingComparisonItem(BaseModel):
    state: str  # "resolved" | "new" | "persistent" | "inconclusive"
    checkKey: str
    title: str
    category: str
    severity: str
    olderFindingId: Optional[str] = None
    newerFindingId: Optional[str] = None
    olderEvidence: Optional[str] = None
    newerEvidence: Optional[str] = None
    olderObserved: Optional[str] = None
    newerObserved: Optional[str] = None
    reason: str

class MeasurementComparisonItem(BaseModel):
    key: str
    label: str
    before: Any
    after: Any
    unit: Optional[str] = None
    change: Optional[Union[int, float]] = None
    changePercent: Optional[float] = None
    direction: str  # "improved" | "degraded" | "unchanged" | "neutral" | "unknown"
    status: str     # "comparable" | "inconclusive" | "not_comparable"
    reason: Optional[str] = None

class ComparisonSummarySchema(BaseModel):
    resolvedCount: int = 0
    newCount: int = 0
    persistentCount: int = 0
    inconclusiveCount: int = 0
    comparableMeasurementsCount: int = 0
    totalFindingsEvaluated: int = 0
    isReliable: bool = True
    executionStatus: str = "both_completed"

class AuditComparisonResponse(BaseModel):
    olderAuditId: str
    newerAuditId: str
    olderTimestamp: str
    newerTimestamp: str
    url: str
    prospectId: Optional[str] = None
    prospectName: Optional[str] = None
    executionStatus: str
    isReliable: bool
    summary: ComparisonSummarySchema
    resolvedFindings: List[FindingComparisonItem] = Field(default_factory=list)
    newFindings: List[FindingComparisonItem] = Field(default_factory=list)
    persistentFindings: List[FindingComparisonItem] = Field(default_factory=list)
    inconclusiveFindings: List[FindingComparisonItem] = Field(default_factory=list)
    measurements: List[MeasurementComparisonItem] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

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
