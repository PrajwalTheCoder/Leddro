import pytest
from unittest.mock import patch

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "uptimeSeconds" in data
    assert "prospectsCount" in data
    assert "auditsCount" in data

def test_audit_run_empty_url_rejected(client):
    response = client.post("/api/audits/run", json={"url": "   "})
    assert response.status_code == 400
    assert "URL is required" in response.json()["detail"]

def test_audit_run_ssrf_blocked(client):
    for bad_url in ["http://127.0.0.1", "http://localhost", "http://169.254.169.254", "http://10.0.0.1"]:
        response = client.post("/api/audits/run", json={"url": bad_url})
        assert response.status_code == 400
        assert "SSRF" in response.json()["detail"]

def test_audit_run_and_persistence(client):
    # 1. Create a prospect first
    pros_res = client.post("/api/prospects", json={
        "name": "Audit Target Inc",
        "websiteUrl": "https://audittarget.com",
        "opportunityScore": 50
    })
    prospect_id = pros_res.json()["id"]

    mock_audit_result = {
        "url": "https://audittarget.com",
        "timestamp": "2026-10-18 12:00:00 UTC",
        "status": "completed",
        "overallScore": 88,
        "rawDns": {"aRecord": "93.184.216.34", "mxRecord": "mail.audittarget.com", "responseMs": 15, "nameservers": []},
        "rawSsl": {"valid": True, "issuer": "Let's Encrypt", "expiresDays": 45, "tlsVersion": "TLSv1.3", "cipher": "TLS_AES_256_GCM_SHA384"},
        "performance": {"ttfbMs": 120, "domReadyMs": 450, "pageSizeKb": 320, "mobileViewportPresent": True},
        "headers": {"server": "nginx"},
        "findings": [
            {
                "id": "f-test-1",
                "title": "HTTP status 200 OK verified",
                "severity": "info",
                "checkStatus": "PASS",
                "observed": "Root document retrieved in 120ms.",
                "evidence": "200 OK",
                "whyItMatters": "Active.",
                "recommendedAction": "Maintain config.",
                "confidence": 1.0,
                "category": "reachability",
                "httpStatus": 200,
                "responseTimeMs": 120,
                "checkedUrl": "https://audittarget.com"
            },
            {
                "id": "f-test-2",
                "title": "Missing meta description for search snippets",
                "severity": "low",
                "checkStatus": "WARNING",
                "observed": "No meta description discovered.",
                "evidence": "Meta description: [NOT FOUND]",
                "whyItMatters": "Snippet generation.",
                "recommendedAction": "Add description.",
                "confidence": 0.95,
                "category": "seo_meta",
                "checkedUrl": "https://audittarget.com"
            }
        ]
    }

    # Mock execute_audit and DNS validation
    with patch("backend.app.api.audits.execute_audit", return_value=mock_audit_result), \
         patch("backend.app.services.ssrf_validator.validate_host_and_resolve", return_value=(True, ["93.184.216.34"], None)):

        audit_res = client.post("/api/audits/run", json={
            "url": "https://audittarget.com",
            "prospectId": prospect_id
        })

        assert audit_res.status_code == 201
        report = audit_res.json()
        assert report["id"].startswith("aud_")
        assert report["prospectId"] == prospect_id
        assert report["overallScore"] == 88
        assert len(report["findings"]) == 2

        report_id = report["id"]

        # Verify retrieval by report ID
        get_res = client.get(f"/api/audits/{report_id}")
        assert get_res.status_code == 200
        assert get_res.json()["url"] == "https://audittarget.com"

        # Verify prospect audit history
        history_res = client.get(f"/api/audits/prospect/{prospect_id}")
        assert history_res.status_code == 200
        assert len(history_res.json()) == 1

        # Verify prospect record was updated with new score and audit count
        prospect_check = client.get(f"/api/prospects/{prospect_id}").json()
        assert prospect_check["auditCount"] == 1
        assert prospect_check["latestAuditId"] == report_id
        assert prospect_check["opportunityScore"] == 88
        assert prospect_check["websiteStatus"] == "active"

def test_list_audits_eager_loading_no_n_plus_one(client, db_session):
    """
    Regression test for Finding 4:
    Verify that GET /api/audits and GET /api/audits/prospect/{id} do NOT produce
    N+1 queries when fetching multiple audit reports with findings.
    With selectinload, finding retrieval is batched in a single IN query (O(1) queries).
    """
    from sqlalchemy import event
    from backend.tests.conftest import test_engine
    from backend.app.models.audit import AuditReportModel, AuditFindingModel
    from backend.app.models.prospect import ProspectModel

    # Seed parent prospect first to satisfy FK constraint
    pros = ProspectModel(
        id="pros_test_batch",
        name="Batch Test Prospect",
        website_url="https://example0.com",
        opportunity_score=50
    )
    db_session.add(pros)
    db_session.flush()

    # Seed 5 audits, each with 3 findings
    for i in range(5):
        rep = AuditReportModel(
            id=f"aud_batch_{i}",
            url=f"https://example{i}.com",
            timestamp="2026-10-21 12:00 UTC",
            status="completed",
            overall_score=80 + i,
            prospect_id="pros_test_batch"
        )
        db_session.add(rep)
        for j in range(3):
            finding = AuditFindingModel(
                id=f"f_batch_{i}_{j}",
                audit_report_id=rep.id,
                title=f"Finding {j} for audit {i}",
                severity="medium",
                check_status="WARNING",
                observed="Observed detail",
                evidence="Evidence detail",
                confidence=1.0,
                category="reachability"
            )
            db_session.add(finding)
    db_session.commit()

    queries = []
    def capture_queries(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    event.listen(test_engine, "before_cursor_execute", capture_queries)
    try:
        res = client.get("/api/audits")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 5
        # Ensure all 3 findings per audit report are returned in the response
        batch_reports = [r for r in data if r["id"].startswith("aud_batch_")]
        assert len(batch_reports) == 5
        for rep in batch_reports:
            assert len(rep["findings"]) == 3

        # Exactly 2 SELECT queries should be executed:
        # 1. SELECT audit_reports ...
        # 2. SELECT audit_findings ... WHERE audit_findings.audit_report_id IN (...)
        select_queries = [q for q in queries if q.strip().upper().startswith("SELECT")]
        assert len(select_queries) == 2, f"Expected 2 queries with selectinload, got {len(select_queries)}: {select_queries}"
    finally:
        event.remove(test_engine, "before_cursor_execute", capture_queries)

    # Test prospect-filtered audits also eagerly loads without N+1
    queries.clear()
    event.listen(test_engine, "before_cursor_execute", capture_queries)
    try:
        res = client.get("/api/audits/prospect/pros_test_batch")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 5
        for rep in data:
            assert len(rep["findings"]) == 3
        select_queries = [q for q in queries if q.strip().upper().startswith("SELECT")]
        assert len(select_queries) == 2, f"Expected 2 queries with selectinload, got {len(select_queries)}: {select_queries}"
    finally:
        event.remove(test_engine, "before_cursor_execute", capture_queries)
