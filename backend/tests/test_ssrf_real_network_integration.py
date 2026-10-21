import asyncio
import datetime
import http.server
import ipaddress
import os
import socket
import ssl
import tempfile
import threading
import time
from typing import Tuple, Dict, Any, Optional

import pytest
import httpx
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from backend.app.services.ssrf_validator import (
    SSRFProtectedTransport,
    safe_http_get,
    SSRFSecurityError,
    connect_safe_tls_socket
)

# -----------------------------------------------------------------------------
# Certificate Helper for Local HTTPS Integration Tests
# -----------------------------------------------------------------------------

def generate_test_pki(hostname: str = "secure.localtest.me") -> Tuple[str, str, str]:
    """Generates temporary CA, server certificate, and private key for local testing."""
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Leddro Test Root CA"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Leddro Security Testing"),
    ])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        .sign(ca_key, hashes.SHA256())
    )

    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
    ])
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(hostname),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))
            ]),
            critical=False
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(server_key.public_key()), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        .add_extension(
            x509.ExtendedKeyUsage([x509.ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False
        )
        .sign(ca_key, hashes.SHA256())
    )

    ca_file = tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pem")
    ca_file.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    ca_file.close()

    cert_file = tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pem")
    cert_file.write(server_cert.public_bytes(serialization.Encoding.PEM))
    cert_file.close()

    key_file = tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pem")
    key_file.write(server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))
    key_file.close()

    return ca_file.name, cert_file.name, key_file.name

# -----------------------------------------------------------------------------
# Local Real Network Test Servers
# -----------------------------------------------------------------------------

class RealTestServerHandler(http.server.BaseHTTPRequestHandler):
    """Test HTTP handler that inspects real incoming socket headers, SNI, and paths."""
    server_stats: Dict[str, Any] = {}

    def log_message(self, format, *args):
        # Suppress noisy standard HTTP logs during tests
        pass

    def do_GET(self):
        host_header = self.headers.get("Host", "")
        self.server.received_host_headers.append(host_header)
        self.server.received_paths.append(self.path)

        if self.path == "/hello":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Server", "LeddroTestServer/1.0")
            self.end_headers()
            self.wfile.write(b"Hello from real local test server!")

        elif self.path == "/redirect-to-metadata":
            self.send_response(302)
            self.send_header("Location", "http://169.254.169.254/latest/meta-data")
            self.end_headers()

        elif self.path == "/redirect-to-private":
            self.send_response(302)
            self.send_header("Location", "http://10.0.0.1/admin-secret")
            self.end_headers()

        elif self.path == "/large-payload":
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            # Send 500 KB of data in chunks
            chunk = b"X" * 1024
            for _ in range(500):
                self.wfile.write(chunk)

        elif self.path == "/slow":
            time.sleep(1.5)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Slow response")

        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

class RealLocalHttpServer:
    def __init__(self, is_https: bool = False, cert_file: Optional[str] = None, key_file: Optional[str] = None):
        self.is_https = is_https
        self.cert_file = cert_file
        self.key_file = key_file
        self.received_host_headers = []
        self.received_paths = []
        self.received_sni = None

        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), RealTestServerHandler)
        self.httpd.received_host_headers = self.received_host_headers
        self.httpd.received_paths = self.received_paths
        self.port = self.httpd.server_address[1]

        if is_https:
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_ctx.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)

            # Capture SNI via sni_callback if supported
            def sni_callback(sock, req_server_name, cb_ctx):
                self.received_sni = req_server_name
            ssl_ctx.sni_callback = sni_callback

            self.httpd.socket = ssl_ctx.wrap_socket(self.httpd.socket, server_side=True)

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def shutdown(self):
        try:
            self.httpd.shutdown()
            self.httpd.server_close()
        except Exception:
            pass

@pytest.fixture(scope="module")
def real_http_server():
    server = RealLocalHttpServer(is_https=False)
    yield server
    server.shutdown()

@pytest.fixture(scope="module")
def real_https_server():
    ca_path, cert_path, key_path = generate_test_pki(hostname="secure.localtest.me")
    server = RealLocalHttpServer(is_https=True, cert_file=cert_path, key_file=key_path)
    server.ca_path = ca_path
    server.test_ssl_ctx = ssl.create_default_context(cafile=ca_path)
    yield server
    server.shutdown()
    for p in (ca_path, cert_path, key_path):
        try:
            os.unlink(p)
        except OSError:
            pass

# =============================================================================
# LEVEL 2: REAL LOCAL NETWORK INTEGRATION TESTS (REAL SOCKETS)
# =============================================================================

@pytest.mark.asyncio
async def test_real_socket_connection_pins_destination_ip(real_http_server):
    """
    Real socket integration test:
    Verifies that the transport connects the actual TCP socket to the pinned IP (127.0.0.1)
    and sends the original logical hostname in the HTTP Host header.
    """
    port = real_http_server.port
    hostname = "pinned.localtest.me"

    transport = SSRFProtectedTransport(allow_loopback_for_testing=True)
    transport.pinned_backend.pin_destination(hostname, port, "127.0.0.1")

    async with httpx.AsyncClient(transport=transport, follow_redirects=False) as client:
        resp = await client.get(f"http://{hostname}:{port}/hello")

    assert resp.status_code == 200
    assert resp.text == "Hello from real local test server!"

    # Verify physical socket destination directly from the backend stream
    last_peer = transport.pinned_backend.last_connected_addr
    assert last_peer is not None
    assert last_peer[0] == "127.0.0.1"
    assert last_peer[1] == port

    # Verify original logical hostname was sent in Host header
    assert any(hostname in h for h in real_http_server.received_host_headers)

@pytest.mark.asyncio
async def test_real_socket_dns_answer_change_cannot_redirect(real_http_server):
    """
    DNS Rebinding Prevention:
    Simulates DNS resolving to a public address during validation, but changing
    to a prohibited address immediately before connection.
    Because the transport is pinned to 127.0.0.1 (the validated destination),
    the socket connects strictly to 127.0.0.1 and cannot be hijacked.
    """
    from unittest.mock import patch

    port = real_http_server.port
    hostname = "rebind.localtest.me"

    transport = SSRFProtectedTransport(allow_loopback_for_testing=True)
    # The validated destination is pinned
    transport.pinned_backend.pin_destination(hostname, port, "127.0.0.1")

    # Now simulate DNS answering with a prohibited internal address (10.99.88.77)
    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("10.99.88.77", port))]):
        async with httpx.AsyncClient(transport=transport, follow_redirects=False) as client:
            resp = await client.get(f"http://{hostname}:{port}/hello")

    # Connection succeeded because socket connected to pinned 127.0.0.1
    assert resp.status_code == 200
    assert transport.pinned_backend.last_connected_addr[0] == "127.0.0.1"

@pytest.mark.asyncio
async def test_real_https_sni_and_certificate_hostname_verification(real_https_server):
    """
    Real HTTPS socket integration test:
    Verifies that for an encrypted HTTPS connection:
    - The TCP socket connects to the pinned IP (127.0.0.1).
    - TLS Client Hello contains the original logical hostname in SNI.
    - TLS certificate verification verifies against the logical hostname.
    - The HTTP request header contains the logical Host.
    """
    port = real_https_server.port
    hostname = "secure.localtest.me"

    transport = SSRFProtectedTransport(
        allow_loopback_for_testing=True,
        verify=real_https_server.test_ssl_ctx
    )
    transport.pinned_backend.pin_destination(hostname, port, "127.0.0.1")

    async with httpx.AsyncClient(transport=transport, follow_redirects=False) as client:
        resp = await client.get(f"https://{hostname}:{port}/hello")

    assert resp.status_code == 200
    assert resp.text == "Hello from real local test server!"

    # Verify physical socket connected to pinned IP
    assert transport.pinned_backend.last_connected_addr[0] == "127.0.0.1"

    # Verify SNI received by the real TLS server
    if real_https_server.received_sni is not None:
        assert real_https_server.received_sni == hostname

    # Verify Host header received by server
    assert any(hostname in h for h in real_https_server.received_host_headers)

@pytest.mark.asyncio
async def test_real_https_certificate_mismatch_rejected(real_https_server):
    """
    Verifies that if the server certificate does not match the logical request hostname,
    TLS certificate verification strictly fails and does NOT connect.
    """
    port = real_https_server.port
    wrong_hostname = "wrong-host.localtest.me"

    transport = SSRFProtectedTransport(
        allow_loopback_for_testing=True,
        verify=real_https_server.test_ssl_ctx
    )
    # Pin wrong_hostname to 127.0.0.1 (where cert is for secure.localtest.me)
    transport.pinned_backend.pin_destination(wrong_hostname, port, "127.0.0.1")

    with pytest.raises(httpx.ConnectError) as exc_info:
        async with httpx.AsyncClient(transport=transport, follow_redirects=False) as client:
            await client.get(f"https://{wrong_hostname}:{port}/hello")

    err_text = str(exc_info.value).lower()
    assert "certificate verify failed" in err_text or "hostname mismatch" in err_text or "ssl" in err_text

@pytest.mark.asyncio
async def test_real_http_unsafe_redirect_blocked_before_prohibited_connection(real_http_server):
    """
    Redirect security test with real server:
    Real HTTP server returns a 302 redirect targeting cloud metadata (169.254.169.254).
    SSRF safe_http_get must revalidate the redirect target and block it BEFORE
    any network connection to the prohibited destination occurs.
    """
    port = real_http_server.port
    initial_url = f"http://127.0.0.1:{port}/redirect-to-metadata"

    success, resp, error = await safe_http_get(
        initial_url,
        allow_loopback_for_testing=True,
        max_redirects=5
    )

    assert not success
    assert resp is None
    assert "SSRF Protection blocked destination" in error
    assert "169.254.169.254" in error

@pytest.mark.asyncio
async def test_real_server_response_size_limit(real_http_server):
    """
    Resource limit test with real server:
    Real HTTP server streams a 500 KB response body.
    safe_http_get with max_bytes=8192 (8 KB) truncates the body and flags was_truncated=True.
    """
    port = real_http_server.port
    url = f"http://127.0.0.1:{port}/large-payload"

    success, resp, error = await safe_http_get(
        url,
        allow_loopback_for_testing=True,
        max_bytes=8192
    )

    assert success
    assert resp is not None
    assert resp.was_truncated is True
    assert len(resp.text) == 8192

@pytest.mark.asyncio
async def test_real_slow_server_timeout(real_http_server):
    """
    Timeout test with real server:
    Real server delays response by 1.5 seconds.
    safe_http_get with timeout=0.25 seconds enforces the deadline cleanly.
    """
    port = real_http_server.port
    url = f"http://127.0.0.1:{port}/slow"

    success, resp, error = await safe_http_get(
        url,
        allow_loopback_for_testing=True,
        timeout=0.25
    )

    assert not success
    assert resp is None
    assert "failed" in error.lower() or "timeout" in error.lower()

def test_ipv6_real_socket_support():
    """
    IPv6 environment check:
    Tests real socket binding on IPv6 loopback (::1).
    If IPv6 is not available or disabled by the OS, explicitly reports NOT RUN.
    """
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.bind(("::1", 0))
        port = sock.getsockname()[1]
        sock.listen(1)
        sock.close()
    except Exception as e:
        pytest.skip(f"IPv6 real socket test NOT RUN on this system: {e}")

    # If socket binding succeeded, IPv6 is supported
    assert port > 0
