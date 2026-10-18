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
