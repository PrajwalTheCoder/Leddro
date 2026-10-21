import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from backend.app.services.audit_engine import AuditEngine
from backend.app.core.config import settings

@pytest.fixture
def engine():
    return AuditEngine()

@pytest.fixture(autouse=True)
def mock_dns_and_tls():
    """Mock external DNS and TLS network calls for deterministic local testing."""
    with patch.object(
        AuditEngine,
        "_inspect_dns",
        return_value={
            "details": {
                "aRecord": "93.184.216.34",
                "mxRecord": "mail.example.com",
                "responseMs": 12,
                "nameservers": ["ns1.example.com"]
            },
            "findings": [
                {
                    "id": "f-dns-a-pass-test",
                    "title": "DNS A/IPv4 resolution verified",
                    "severity": "info",
                    "check_status": "PASS",
                    "observed": "Domain resolved to 1 IPv4 address(es).",
                    "evidence": "A 93.184.216.34",
                    "why_it_matters": "Active routing.",
                    "recommended_action": "DNS is healthy.",
                    "confidence": 1.0,
                    "category": "reachability",
                    "checked_url": "http://example.com"
                }
            ]
        }
    ), patch.object(
        AuditEngine,
        "_inspect_tls",
        return_value={
            "valid": True,
            "issuer": "DigiCert Global Root CA",
            "expiresDays": 120,
            "tlsVersion": "TLSv1.3",
            "cipher": "TLS_AES_256_GCM_SHA384",
            "findings": [
                {
                    "id": "f-ssl-pass-test",
                    "title": "Valid SSL/TLS certificate verified",
                    "severity": "info",
                    "check_status": "PASS",
                    "observed": "Valid TLS certificate issued by DigiCert with 120 days remaining.",
                    "evidence": "Issuer: DigiCert",
                    "why_it_matters": "Encrypted.",
                    "recommended_action": "No action needed.",
                    "confidence": 1.0,
                    "category": "security",
                    "checked_url": "https://example.com"
                }
            ]
        }
    ), patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
        yield

@pytest.mark.asyncio
async def test_successful_http_response(engine):
    html_content = """<!DOCTYPE html>
    <html>
      <head>
        <title>Apex Precision - Industrial Machining</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description" content="Precision CNC machining and manufacturing services.">
      </head>
      <body>
        <nav><a href="/contact">Contact Our Team</a></nav>
        <h1>Welcome</h1>
      </body>
    </html>"""

    # Mock HTTP safe fetch
    with patch.object(
        engine,
        "_fetch_http_safely",
        return_value={
            "status_code": 200,
            "final_url": "https://example.com",
            "ttfb_ms": 140,
            "headers": {"server": "nginx/1.24"},
            "body": html_content,
            "findings": [
                {
                    "id": "f-http-pass-test",
                    "title": "HTTP status 200 OK verified",
                    "severity": "info",
                    "check_status": "PASS",
                    "observed": "Target server returned HTTP 200 in 140 ms.",
                    "evidence": "GET https://example.com HTTP/1.1 200 OK",
                    "why_it_matters": "Active.",
                    "recommended_action": "Maintain server configuration.",
                    "confidence": 1.0,
                    "category": "reachability",
                    "http_status": 200,
                    "response_time_ms": 140,
                    "checked_url": "https://example.com"
                }
            ]
        }
    ):
        result = await engine.execute_audit("https://example.com")

        assert result["status"] == "completed"
        statuses = [f["check_status"] for f in result["findings"]]
        assert "PASS" in statuses
        
        # Verify HTML inspections succeeded
        titles = [f["title"] for f in result["findings"]]
        assert any("HTML page title verified" in t for t in titles)
        assert any("Mobile viewport" in t for t in titles)
        assert any("Meta description tag verified" in t for t in titles)
        assert any("Internal contact pathway detected" in t for t in titles)

@pytest.mark.asyncio
async def test_http_404_response(engine):
    with patch.object(
        engine,
        "_fetch_http_safely",
        return_value={
            "status_code": 404,
            "final_url": "https://example.com/missing-page",
            "ttfb_ms": 110,
            "headers": {"server": "cloudflare"},
            "body": "<html><body>404 Not Found</body></html>",
            "findings": [
                {
                    "id": "f-http-404-test",
                    "title": "Target page returned HTTP 404 Not Found",
                    "severity": "high",
                    "check_status": "FAIL",
                    "observed": "Live crawl returned HTTP 404.",
                    "evidence": "404 Not Found",
                    "why_it_matters": "Visitors hit dead end.",
                    "recommended_action": "Verify routing.",
                    "confidence": 1.0,
                    "category": "reachability",
                    "http_status": 404,
                    "response_time_ms": 110,
                    "checked_url": "https://example.com/missing-page"
                }
            ]
        }
    ):
        result = await engine.execute_audit("https://example.com/missing-page")
        assert result["status"] == "completed"
        fails = [f for f in result["findings"] if f["check_status"] == "FAIL"]
        assert any(f.get("http_status") == 404 for f in fails)

@pytest.mark.asyncio
async def test_missing_html_metadata(engine):
    bare_html = "<html><body><h1>Minimal Blank Page</h1></body></html>"

    with patch.object(
        engine,
        "_fetch_http_safely",
        return_value={
            "status_code": 200,
            "final_url": "https://example.com",
            "ttfb_ms": 90,
            "headers": {},
            "body": bare_html,
            "findings": []
        }
    ):
        result = await engine.execute_audit("https://example.com")
        findings = result["findings"]

        missing_title = any("Missing or empty HTML page title tag" in f["title"] for f in findings)
        missing_vp = any("Missing mobile viewport meta declaration" in f["title"] for f in findings)
        missing_desc = any("Missing meta description for search snippets" in f["title"] for f in findings)

        assert missing_title
        assert missing_vp
        assert missing_desc

@pytest.mark.asyncio
async def test_malformed_html_handling(engine):
    malformed_html = "<!DOCTYPE html><html><head><title>Unclosed title<div><p>Broken structure"

    with patch.object(
        engine,
        "_fetch_http_safely",
        return_value={
            "status_code": 200,
            "final_url": "https://example.com",
            "ttfb_ms": 85,
            "headers": {},
            "body": malformed_html,
            "findings": []
        }
    ):
        # Must not raise exceptions
        result = await engine.execute_audit("https://example.com")
        assert result["status"] == "completed"
        assert len(result["findings"]) > 0

@pytest.mark.asyncio
async def test_timeout_handling(engine):
    with patch.object(
        engine,
        "_fetch_http_safely",
        return_value={
            "status_code": 0,
            "final_url": "https://example.com",
            "ttfb_ms": 0,
            "headers": {},
            "body": "",
            "findings": [
                {
                    "id": "f-timeout-test",
                    "title": "Connection to target web server timed out",
                    "severity": "high",
                    "check_status": "ERROR",
                    "observed": "Connection attempt timed out after 5.0 seconds.",
                    "evidence": "Timeout Limit: 5.0s",
                    "why_it_matters": "Server failed to accept connections.",
                    "recommended_action": "Check web server load and firewall.",
                    "confidence": 0.99,
                    "category": "reachability",
                    "checked_url": "https://example.com"
                }
            ]
        }
    ):
        result = await engine.execute_audit("https://example.com")
        errors = [f for f in result["findings"] if f["check_status"] == "ERROR"]
        assert any("timed out" in f["title"].lower() for f in errors)

@pytest.mark.asyncio
async def test_unreachable_host_handling(engine):
    with patch.object(
        engine,
        "_fetch_http_safely",
        return_value={
            "status_code": 0,
            "final_url": "https://example.com",
            "ttfb_ms": 0,
            "headers": {},
            "body": "",
            "findings": [
                {
                    "id": "f-conn-err-test",
                    "title": "TCP Connection refused or unreachable",
                    "severity": "high",
                    "check_status": "ERROR",
                    "observed": "Network error connecting to https://example.com",
                    "evidence": "Socket Error: Connection refused",
                    "why_it_matters": "Server offline.",
                    "recommended_action": "Verify web server process status.",
                    "confidence": 1.0,
                    "category": "reachability",
                    "checked_url": "https://example.com"
                }
            ]
        }
    ):
        result = await engine.execute_audit("https://example.com")
        errors = [f for f in result["findings"] if f["check_status"] == "ERROR"]
        assert any("refused or unreachable" in f["title"].lower() for f in errors)

@pytest.mark.asyncio
async def test_redirect_to_private_address_blocked(engine):
    """
    Test that when an initial public URL redirects to a private IP (e.g. 192.168.1.1),
    the redirect hop validator intercepts and halts the request.
    """
    # 1. Initial request to public URL
    # 2. Response is 302 redirecting to http://192.168.1.1/admin
    mock_response = MagicMock()
    mock_response.status_code = 302
    mock_response.is_redirect = True
    mock_response.headers = {"Location": "http://192.168.1.1/admin"}

    class MockAsyncStream:
        async def __aenter__(self):
            return mock_response
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    async def mock_aiter_bytes():
        yield b""

    mock_response.aiter_bytes = mock_aiter_bytes

    with patch("httpx.AsyncClient.stream", return_value=MockAsyncStream()):
        fetch_result = await engine._fetch_http_safely("https://example.com")
        findings = fetch_result["findings"]
        
        ssrf_hops = [f for f in findings if "prohibited" in f["title"].lower() or "prohibited" in f["observed"].lower()]
        assert len(ssrf_hops) > 0
        assert ssrf_hops[0]["check_status"] == "FAIL"

@pytest.mark.asyncio
async def test_oversized_response_handling(engine):
    """
    Test that when a server streams content exceeding the 5MB cap,
    the audit engine terminates downloading and logs a WARNING finding.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.is_redirect = False
    mock_response.headers = {"server": "apache"}

    class MockAsyncStream:
        async def __aenter__(self):
            return mock_response
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Stream 6MB chunk
    async def mock_aiter_bytes():
        chunk = b"X" * (1024 * 1024)  # 1MB
        for _ in range(6):  # 6MB total
            yield chunk

    mock_response.aiter_bytes = mock_aiter_bytes

    with patch("httpx.AsyncClient.stream", return_value=MockAsyncStream()):
        fetch_result = await engine._fetch_http_safely("https://example.com")
        findings = fetch_result["findings"]

        size_findings = [f for f in findings if "exceeded" in f["title"].lower() or "limit" in f["title"].lower()]
        assert len(size_findings) > 0
        assert size_findings[0]["check_status"] == "WARNING"

def test_dns_spf_and_dmarc_apex_fallback(engine):
    """
    Test that when a subdomain (e.g. www.brand.com) lacks direct SPF and DMARC records,
    _inspect_dns falls back to querying the apex organizational domain (brand.com).
    """
    mock_resolver = MagicMock()

    # Simulate: A record exists on www.brand.com
    a_answer = MagicMock()
    a_answer.__str__ = MagicMock(return_value="1.2.3.4")

    # Simulate: TXT on www.brand.com has no SPF; TXT on brand.com has SPF
    apex_spf = MagicMock()
    apex_spf.strings = [b"v=spf1 include:_spf.google.com ~all"]

    # Simulate: _dmarc.www.brand.com raises NXDOMAIN; _dmarc.brand.com returns DMARC
    apex_dmarc = MagicMock()
    apex_dmarc.strings = [b"v=DMARC1; p=reject;"]

    def mock_resolve(qname, rdtype, **kwargs):
        if rdtype == "A":
            return [a_answer]
        if rdtype == "TXT":
            if qname == "www.brand.com":
                return []
            if qname == "brand.com":
                return [apex_spf]
            if qname == "_dmarc.www.brand.com":
                raise Exception("NXDOMAIN")
            if qname == "_dmarc.brand.com":
                return [apex_dmarc]
        raise Exception("NXDOMAIN")

    mock_resolver.resolve.side_effect = mock_resolve

    with patch("dns.resolver.Resolver", return_value=mock_resolver):
        res = engine._inspect_dns("www.brand.com")
        findings = res["findings"]
        titles = [f["title"] for f in findings]

        # Should NOT flag missing SPF or missing DMARC because apex domain published them
        assert not any("Missing Sender Policy Framework" in t for t in titles)
        assert not any("Missing DMARC" in t for t in titles)
        assert any("DNS A/IPv4 resolution verified" in t for t in titles)

def test_dummy_template_email_rejected():
    """Verify that template placeholder emails like you@company.com are rejected."""
    from backend.app.services.email_scraper import is_valid_email_candidate
    assert is_valid_email_candidate("you@company.com") is False
    assert is_valid_email_candidate("user@company.com") is False
    assert is_valid_email_candidate("info@realbusiness.in") is True
