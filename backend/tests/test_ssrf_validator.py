import pytest
from unittest.mock import patch
from backend.app.services.ssrf_validator import (
    validate_target_url,
    is_ip_allowed,
    validate_host_and_resolve
)

def test_localhost_ip_is_blocked():
    is_safe, reason, _, _ = validate_target_url("http://127.0.0.1")
    assert not is_safe
    assert "Loopback" in reason or "Prohibited" in reason or "prohibited" in reason

def test_localhost_domain_is_blocked():
    is_safe, reason, _, _ = validate_target_url("http://localhost:8080")
    assert not is_safe
    assert "Prohibited" in reason or "Loopback" in reason or "prohibited" in reason

def test_cloud_metadata_ip_is_blocked():
    is_safe, reason, _, _ = validate_target_url("http://169.254.169.254/latest/meta-data")
    assert not is_safe
    assert "prohibited" in reason.lower() or "metadata" in reason.lower() or "link-local" in reason.lower()

def test_cloud_metadata_hostname_is_blocked():
    is_safe, reason, _, _ = validate_target_url("http://metadata.google.internal")
    assert not is_safe
    assert "metadata" in reason.lower() or "internal" in reason.lower()

def test_private_rfc1918_ips_are_blocked():
    # 10.x.x.x
    safe, reason, _, _ = validate_target_url("http://10.0.0.1")
    assert not safe
    assert "prohibited" in reason.lower() or "private" in reason.lower()

    # 192.168.x.x
    safe, reason, _, _ = validate_target_url("http://192.168.1.1")
    assert not safe
    assert "prohibited" in reason.lower() or "private" in reason.lower()

    # 172.16.x.x
    safe, reason, _, _ = validate_target_url("http://172.16.10.20")
    assert not safe
    assert "prohibited" in reason.lower() or "private" in reason.lower()

def test_ipv6_loopback_and_link_local_blocked():
    safe, reason, _, _ = validate_target_url("http://[::1]")
    assert not safe

    safe, reason, _, _ = validate_target_url("http://[fe80::1]")
    assert not safe

def test_disallowed_schemes_blocked():
    for url in ["file:///etc/passwd", "ftp://ftp.example.com", "gopher://127.0.0.1", "ssh://git.internal"]:
        safe, reason, _, _ = validate_target_url(url)
        assert not safe
        assert "protocol" in reason.lower() or "scheme" in reason.lower()

def test_disallowed_ports_blocked():
    # SSH port 22
    safe, reason, _, _ = validate_target_url("http://example.com:22")
    assert not safe
    assert "Port 22" in reason or "22" in reason

    # Redis port 6379
    safe, reason, _, _ = validate_target_url("http://example.com:6379")
    assert not safe
    assert "6379" in reason

    # MySQL port 3306
    safe, reason, _, _ = validate_target_url("http://example.com:3306")
    assert not safe
    assert "3306" in reason

def test_dns_rebinding_to_private_ip():
    """Mock DNS resolution returning a private IP for an innocent-looking domain."""
    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("10.20.30.40", 80))]):
        safe, reason, _, _ = validate_target_url("http://internal-attack-domain.com")
        assert not safe
        assert "prohibited address" in reason.lower()

def test_valid_public_domain():
    """Valid public domain with public IP resolution."""
    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
        safe, reason, parsed, ips = validate_target_url("example.com")
        assert safe
        assert reason is None
        assert parsed.scheme == "https"
        assert parsed.hostname == "example.com"
        assert "93.184.216.34" in ips

def test_unresolvable_public_domain_is_safe_from_ssrf():
    """Domains that fail DNS resolution pose no SSRF risk and should proceed to reachability audits."""
    import socket
    with patch("socket.getaddrinfo", side_effect=socket.gaierror(11001, "getaddrinfo failed")):
        safe, reason, parsed, ips = validate_target_url("nonexistent-prospect-domain.xyz")
        assert safe
        assert reason is None
        assert parsed.hostname == "nonexistent-prospect-domain.xyz"
        assert ips == []

@pytest.mark.asyncio
async def test_safe_http_get_redirect_to_loopback_blocked():
    """
    Regression test for Finding 2:
    Public URL redirects to 127.0.0.1.
    Must block the redirect and NEVER issue an HTTP request to loopback.
    """
    import httpx
    from backend.app.services.ssrf_validator import safe_http_get

    requested_urls = []
    def handler(request: httpx.Request):
        url_str = str(request.url)
        requested_urls.append(url_str)
        if "example.com" in url_str:
            return httpx.Response(302, headers={"Location": "http://127.0.0.1:8000/internal-secret"})
        return httpx.Response(200, text="SECRET_EXPOSED")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]):
            success, resp, error = await safe_http_get("http://example.com/test", client=client)

    assert not success
    assert resp is None
    assert "SSRF Protection blocked destination" in error
    assert "127.0.0.1" in error
    assert "http://127.0.0.1:8000/internal-secret" not in requested_urls

@pytest.mark.asyncio
async def test_safe_http_get_redirect_to_private_ipv4_blocked():
    """Public URL redirects to RFC 1918 private network (10.0.0.1, 192.168.1.1)."""
    import httpx
    from backend.app.services.ssrf_validator import safe_http_get

    requested_urls = []
    def handler(request: httpx.Request):
        requested_urls.append(str(request.url))
        return httpx.Response(302, headers={"Location": "http://10.0.0.1/admin"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]):
            success, resp, error = await safe_http_get("http://example.com/login", client=client)

    assert not success
    assert "10.0.0.1" in error
    assert "http://10.0.0.1/admin" not in requested_urls

@pytest.mark.asyncio
async def test_safe_http_get_redirect_to_ipv6_loopback_or_private_blocked():
    """Public URL redirects to IPv6 loopback ([::1]) or ULA ([fc00::1])."""
    import httpx
    from backend.app.services.ssrf_validator import safe_http_get

    requested_urls = []
    def handler(request: httpx.Request):
        requested_urls.append(str(request.url))
        return httpx.Response(302, headers={"Location": "http://[::1]:8080/metrics"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]):
            success, resp, error = await safe_http_get("http://example.com/stats", client=client)

    assert not success
    assert "::1" in error
    assert "http://[::1]:8080/metrics" not in requested_urls

@pytest.mark.asyncio
async def test_safe_http_get_multiple_redirect_hops_and_limit():
    """Allows safe multiple hops up to max_redirects, but halts if exceeded."""
    import httpx
    from backend.app.services.ssrf_validator import safe_http_get

    hops = []
    def handler(request: httpx.Request):
        hops.append(str(request.url))
        idx = int(request.url.path.strip("/").split("-")[-1])
        if idx < 10:
            return httpx.Response(302, headers={"Location": f"http://example.com/hop-{idx + 1}"})
        return httpx.Response(200, text="FINISH")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]):
            success, resp, error = await safe_http_get("http://example.com/hop-1", client=client, max_redirects=3)

    assert not success
    assert "Maximum redirect limit (3) exceeded" in error
    assert len(hops) == 4  # hop-1, hop-2, hop-3, hop-4 (4th hop triggers limit check)

@pytest.mark.asyncio
async def test_safe_http_get_redirect_loop_detected():
    """Detects and prevents infinite redirect loops (A -> B -> A)."""
    import httpx
    from backend.app.services.ssrf_validator import safe_http_get

    hops = []
    def handler(request: httpx.Request):
        url_str = str(request.url)
        hops.append(url_str)
        if "loop-a" in url_str:
            return httpx.Response(302, headers={"Location": "http://example.com/loop-b"})
        else:
            return httpx.Response(302, headers={"Location": "http://example.com/loop-a"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]):
            success, resp, error = await safe_http_get("http://example.com/loop-a", client=client)

    assert not success
    assert "Redirect loop detected" in error
    assert len(hops) <= 3

@pytest.mark.asyncio
async def test_safe_http_get_malformed_location_header():
    """Handles malformed or empty Location headers gracefully."""
    import httpx
    from backend.app.services.ssrf_validator import safe_http_get

    def handler(request: httpx.Request):
        return httpx.Response(302, headers={"Location": ""})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]):
            success, resp, error = await safe_http_get("http://example.com/malformed", client=client)

    assert not success
    assert "Malformed empty redirect Location" in error

@pytest.mark.asyncio
async def test_safe_http_get_redirect_to_prohibited_scheme():
    """Rejects redirects to prohibited schemes (file://, javascript:, gopher://)."""
    import httpx
    from backend.app.services.ssrf_validator import safe_http_get

    for bad_scheme in ["file:///etc/passwd", "javascript:alert(1)", "gopher://127.0.0.1"]:
        def handler(request: httpx.Request, loc=bad_scheme):
            return httpx.Response(302, headers={"Location": loc})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]):
                success, resp, error = await safe_http_get("http://example.com/exploit", client=client)

        assert not success
        assert any(term in error.lower() for term in ["prohibited scheme", "unsupported protocol", "invalidurl", "for absolute urls"])

@pytest.mark.asyncio
async def test_email_scraper_with_ssrf_redirect_protection():
    """
    Regression test for Finding 2:
    scrape_website_contacts crawls homepage that redirects to cloud metadata.
    Must block the redirect and never expose internal metadata.
    """
    import httpx
    from backend.app.services.email_scraper import scrape_website_contacts

    requested_urls = []
    def handler(request: httpx.Request):
        url_str = str(request.url)
        requested_urls.append(url_str)
        if "innocent-looking-site.com" in url_str:
            return httpx.Response(302, headers={"Location": "http://169.254.169.254/latest/meta-data"})
        return httpx.Response(200, text="IAM_ROLE_CREDENTIALS")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]):
        res = await scrape_website_contacts("https://innocent-looking-site.com")

    assert "http://169.254.169.254/latest/meta-data" not in requested_urls
    assert res["emails"] == []

# =========================================================================
# LEVEL 1: COMPREHENSIVE ADVERSARIAL AND CONNECTION-PINNING UNIT TESTS
# =========================================================================

def test_mixed_public_and_private_dns_answers_rejected():
    """
    Adversarial test:
    DNS returns a mix of a valid public IP and a prohibited private IP.
    Policy: Reject the entire answer set to prevent attacker-directed fallback.
    """
    from backend.app.services.ssrf_validator import resolve_and_pin_host, SSRFSecurityError
    with patch("socket.getaddrinfo", return_value=[
        (None, None, None, None, ("93.184.216.34", 80)),
        (None, None, None, None, ("10.0.0.1", 80))
    ]):
        with pytest.raises(SSRFSecurityError) as exc_info:
            resolve_and_pin_host("dual-homed-attack.com", 80)
        assert "prohibited ip" in str(exc_info.value).lower() or "security policy" in str(exc_info.value).lower()

def test_ipv4_mapped_ipv6_addresses_prohibited():
    """
    Adversarial test:
    Attackers often encode prohibited IPv4 addresses inside IPv6 mapped prefixes (::ffff:...).
    Must extract the mapped IPv4 and enforce private/loopback/cloud-metadata rules.
    """
    from backend.app.services.ssrf_validator import is_ip_allowed, validate_target_url

    # IPv4 loopback mapped into IPv6
    allowed, reason = is_ip_allowed("::ffff:127.0.0.1")
    assert not allowed
    assert "prohibited" in reason.lower() or "loopback" in reason.lower()

    # AWS metadata mapped into IPv6
    allowed, reason = is_ip_allowed("::ffff:169.254.169.254")
    assert not allowed
    assert "prohibited" in reason.lower() or "metadata" in reason.lower() or "link-local" in reason.lower()

    # RFC 1918 10.x mapped into IPv6
    allowed, reason = is_ip_allowed("::ffff:10.50.1.1")
    assert not allowed
    assert "prohibited" in reason.lower() or "private" in reason.lower()

    # Direct URL validation
    is_safe, reason, _, _ = validate_target_url("http://[::ffff:127.0.0.1]/")
    assert not is_safe

def test_multiple_public_dns_answers_deterministic_pinning():
    """
    When DNS returns multiple legitimate public IP addresses (both IPv4 and IPv6),
    the validator deterministically pins a valid public address without failing.
    """
    from backend.app.services.ssrf_validator import resolve_and_pin_host
    with patch("socket.getaddrinfo", return_value=[
        (None, None, None, None, ("2606:2800:220:1:248:1893:25c8:1946", 443)),
        (None, None, None, None, ("93.184.216.34", 443)),
        (None, None, None, None, ("93.184.216.35", 443))
    ]):
        pinned_ip, resolved = resolve_and_pin_host("example.com", 443)
        assert pinned_ip == "93.184.216.34"  # Deterministic IPv4 preference
        assert len(resolved) == 3

def test_dns_resolution_failure_handling():
    """DNS resolution errors raise predictable SSRFSecurityError in resolve_and_pin_host."""
    import socket
    from backend.app.services.ssrf_validator import resolve_and_pin_host, SSRFSecurityError
    with patch("socket.getaddrinfo", side_effect=socket.gaierror(11001, "getaddrinfo failed")):
        with pytest.raises(SSRFSecurityError) as exc_info:
            resolve_and_pin_host("unregistered-bogus-domain.invalid", 80)
        assert "dns resolution failed" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_cross_origin_authorization_header_stripping():
    """
    Redirect security:
    When redirecting across different origins (e.g. source.com -> other-host.com),
    sensitive Authorization and Cookie headers must be stripped to prevent credential leakage.
    """
    import httpx
    from backend.app.services.ssrf_validator import safe_http_get

    captured_headers = {}
    def handler(request: httpx.Request):
        url_str = str(request.url)
        if "source.com" in url_str:
            return httpx.Response(302, headers={"Location": "https://other-domain.com/landing"})
        captured_headers["auth"] = request.headers.get("Authorization")
        captured_headers["cookie"] = request.headers.get("Cookie")
        return httpx.Response(200, text="OK")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
        headers = {"Authorization": "Bearer SECRET_TOKEN", "Cookie": "session=ABC"}
        success, resp, _ = await safe_http_get("https://source.com/start", headers=headers, client=client)

    assert success
    assert captured_headers.get("auth") is None
    assert captured_headers.get("cookie") is None

@pytest.mark.asyncio
async def test_response_size_limit_truncation():
    """
    Resource limits:
    Oversized responses or compression bombs exceeding max_bytes are truncated,
    flagged as was_truncated=True, and do not exhaust application memory.
    """
    import httpx
    from backend.app.services.ssrf_validator import safe_http_get

    def handler(request: httpx.Request):
        # 100 KB payload
        return httpx.Response(200, text="A" * 102400)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]):
        # Cap at 10 KB
        success, resp, _ = await safe_http_get("http://example.com/large", max_bytes=10240, client=client)

    assert success
    assert resp.was_truncated is True
    assert len(resp.text) <= 10240 + 8192  # bounded by chunk size

def test_unix_domain_sockets_explicitly_blocked():
    """Connection backend strictly rejects Unix domain socket connections."""
    import pytest
    from backend.app.services.ssrf_validator import PinnedAsyncNetworkBackend, SSRFSecurityError
    backend = PinnedAsyncNetworkBackend()
    with pytest.raises(SSRFSecurityError) as exc_info:
        import asyncio
        asyncio.run(backend.connect_unix_socket("/var/run/docker.sock"))
    assert "unix domain sockets are prohibited" in str(exc_info.value).lower()

