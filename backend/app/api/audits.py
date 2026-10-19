import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.audit import AuditReportModel, AuditFindingModel
from backend.app.models.prospect import ProspectModel
from backend.app.schemas.audit import (
    AuditRunRequest,
    AuditReportResponse,
    AuditCompareRequest,
    AuditComparisonResponse,
    db_audit_to_schema
)
from backend.app.services.ssrf_validator import validate_target_url
from backend.app.services.audit_engine import execute_audit
from backend.app.services.audit_comparison import compare_audits
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/audits", tags=["Audits"])

@router.post("/run", status_code=status.HTTP_201_CREATED)
async def run_audit(payload: AuditRunRequest, db: Session = Depends(get_db)):
    """
    Executes a real server-side website audit with SSRF protection, DNS lookups,
    TLS inspection, HTTP response timing, HTML parsing, and finding classification.
    """
    raw_url = payload.url.strip()
    if not raw_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is required for audit execution."
        )

    # 1. Pre-flight SSRF Validation
    is_safe, reason, parsed_url, _ = validate_target_url(raw_url)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security Policy: URL rejected by SSRF protection — {reason}"
        )
    normalized_url = parsed_url.geturl() if parsed_url else raw_url

    # 2. Execute Real Audit
    audit_data = await execute_audit(normalized_url)

    # 3. Persist Report
    report_id = f"aud_{uuid.uuid4().hex[:8]}"
    report_model = AuditReportModel(
        id=report_id,
        prospect_id=payload.prospectId,
        url=audit_data.get("url", normalized_url),
        timestamp=audit_data.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
        status=audit_data.get("status", "completed"),
        overall_score=audit_data.get("overall_score") or audit_data.get("overallScore") or 65,
        raw_dns=json.dumps(audit_data.get("raw_dns") or audit_data.get("rawDns") or {}),
        raw_ssl=json.dumps(audit_data.get("raw_ssl") or audit_data.get("rawSsl") or {}),
        performance=json.dumps(audit_data.get("performance", {})),
        headers=json.dumps(audit_data.get("headers", {}))
    )
    db.add(report_model)

    # 4. Persist Findings
    findings_models = []
    for f in audit_data.get("findings", []):
        finding_id = f.get("id") or f"f_{uuid.uuid4().hex[:6]}"
        finding_model = AuditFindingModel(
            id=finding_id,
            audit_report_id=report_id,
            title=f.get("title", "Observation"),
            severity=f.get("severity", "medium"),
            check_status=f.get("check_status") or f.get("checkStatus") or "WARNING",
            observed=f.get("observed", ""),
            evidence=f.get("evidence", ""),
            why_it_matters=f.get("why_it_matters") or f.get("whyItMatters") or "",
            recommended_action=f.get("recommended_action") or f.get("recommendedAction") or "",
            confidence=f.get("confidence", 1.0),
            category=f.get("category", "reachability"),
            http_status=f.get("http_status") or f.get("httpStatus"),
            response_time_ms=f.get("response_time_ms") or f.get("responseTimeMs"),
            checked_url=f.get("checked_url") or f.get("checkedUrl") or normalized_url
        )
        db.add(finding_model)
        findings_models.append(finding_model)

    # 5. Link with Prospect if prospectId supplied
    if payload.prospectId:
        prospect = db.query(ProspectModel).filter(ProspectModel.id == payload.prospectId).first()
        if prospect:
            prospect.audit_count = (prospect.audit_count or 0) + 1
            prospect.latest_audit_id = report_id

            audit_score = audit_data.get("overall_score") or audit_data.get("overallScore")
            if audit_score is not None:
                prospect.opportunity_score = audit_score
            else:
                from backend.app.services.prospect_scoring import calculate_prospect_score
                scoring_res = calculate_prospect_score(prospect, report_model)
                prospect.opportunity_score = scoring_res["opportunity_score"]
            prospect.website_status = "active" if audit_data.get("status") == "completed" else "unreachable"
            prospect.last_activity = "Audited just now"

    try:
        db.commit()
        db.refresh(report_model)
    except Exception:
        db.rollback()
        raise

    return db_audit_to_schema(report_model, findings_models)

@router.get("")
def list_audits(db: Session = Depends(get_db)):
    """
    List all executed audit reports.
    """
    reports = db.query(AuditReportModel).order_by(AuditReportModel.created_at.desc()).all()
    results = []
    for r in reports:
        findings = db.query(AuditFindingModel).filter(AuditFindingModel.audit_report_id == r.id).all()
        results.append(db_audit_to_schema(r, findings))
    return results

@router.get("/{report_id}")
def get_audit(report_id: str, db: Session = Depends(get_db)):
    """
    Get audit report details by report ID.
    """
    report = db.query(AuditReportModel).filter(AuditReportModel.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit report with ID '{report_id}' not found"
        )
    findings = db.query(AuditFindingModel).filter(AuditFindingModel.audit_report_id == report.id).all()
    return db_audit_to_schema(report, findings)

@router.get("/prospect/{prospect_id}")
def get_prospect_audits(prospect_id: str, db: Session = Depends(get_db)):
    """
    Get all audit reports for a specific prospect.
    """
    reports = db.query(AuditReportModel).filter(AuditReportModel.prospect_id == prospect_id).order_by(AuditReportModel.created_at.desc()).all()
    results = []
    for r in reports:
        findings = db.query(AuditFindingModel).filter(AuditFindingModel.audit_report_id == r.id).all()
        results.append(db_audit_to_schema(r, findings))
    return results

@router.post("/compare", response_model=AuditComparisonResponse)
def compare_two_audits(payload: AuditCompareRequest, db: Session = Depends(get_db)):
    """
    Deterministically compares two stored audit reports for the same website or prospect.
    Distinguishes resolved, new, persistent, and inconclusive findings without running
    unnecessary audits or external AI calls.
    """
    older_id = payload.get_older_id()
    newer_id = payload.get_newer_id()

    if not older_id or not newer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both older_audit_id and newer_audit_id are required for comparison."
        )

    if older_id == newer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare an audit with itself. Please select two distinct audits."
        )

    # Batch query both reports with joined findings to avoid N+1 queries
    reports = (
        db.query(AuditReportModel)
        .options(joinedload(AuditReportModel.findings))
        .filter(AuditReportModel.id.in_([older_id, newer_id]))
        .all()
    )
    report_map = {r.id: r for r in reports}

    if older_id not in report_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Older audit report with ID '{older_id}' not found."
        )

    if newer_id not in report_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Newer audit report with ID '{newer_id}' not found."
        )

    older_report = report_map[older_id]
    newer_report = report_map[newer_id]

    # Look up prospect if associated
    prospect = None
    target_pid = older_report.prospect_id or newer_report.prospect_id
    if target_pid:
        prospect = db.query(ProspectModel).filter(ProspectModel.id == target_pid).first()

    try:
        comparison_result = compare_audits(
            older_audit=older_report,
            newer_audit=newer_report,
            prospect=prospect
        )
        return comparison_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
