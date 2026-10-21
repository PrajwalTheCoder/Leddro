import ipaddress
import socket
import ssl
import urllib.parse
from typing import Tuple, List, Optional, Dict, Any, Set
import httpcore
import httpx
from backend.app.core.config import settings

# Explicit IPv4 and IPv6 networks prohibited from access
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network (only valid as source)
    ipaddress.ip_network("10.0.0.0/8"),          # RFC 1918 Private-Use
    ipaddress.ip_network("100.64.0.0/10"),       # RFC 6598 Shared Address Space (CGNAT)
    ipaddress.ip_network("127.0.0.0/8"),         # RFC 1122 Loopback
    ipaddress.ip_network("169.254.0.0/16"),      # RFC 3927 Link-Local / Cloud Metadata
    ipaddress.ip_network("172.16.0.0/12"),       # RFC 1918 Private-Use
    ipaddress.ip_network("192.0.0.0/24"),        # RFC 6890 IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),        # RFC 5737 TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),      # RFC 1918 Private-Use
    ipaddress.ip_network("198.18.0.0/15"),       # RFC 2544 Benchmarking
    ipaddress.ip_network("198.51.100.0/24"),     # RFC 5737 TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),      # RFC 5737 TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),         # RFC 1112 Multicast
    ipaddress.ip_network("240.0.0.0/4"),         # RFC 1112 Reserved
    ipaddress.ip_network("255.255.255.255/32"),  # RFC 919 Limited Broadcast
    
    # IPv6 blocked ranges
    ipaddress.ip_network("::/128"),              # Unspecified
    ipaddress.ip_network("::1/128"),             # Loopback
    ipaddress.ip_network("::ffff:0:0/96"),       # IPv4-mapped
    ipaddress.ip_network("100::/64"),            # Discard prefix
    ipaddress.ip_network("2001:db8::/32"),       # Documentation
    ipaddress.ip_network("fc00::/7"),            # Unique Local (ULA)
    ipaddress.ip_network("fe80::/10"),           # Link-Local
    ipaddress.ip_network("ff00::/8"),            # Multicast
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "instance-data",
    "metadata",
}

def is_ip_allowed(ip_str: str, allow_loopback: bool = False) -> Tuple[bool, Optional[str]]:
    """Check if an IP address is publicly routable and not in private/reserved/cloud-metadata ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False, f"Invalid IP address representation: {ip_str}"

    if allow_loopback and ip.is_loopback:
        return True, None

    # Strict handling for IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        v4_allowed, v4_reason = is_ip_allowed(str(ip.ipv4_mapped), allow_loopback=allow_loopback)
        if not v4_allowed:
            return False, f"IPv4-mapped IPv6 address {ip_str} resolves to prohibited IPv4: {v4_reason}"

    if ip.is_loopback:
        return False, f"Loopback address prohibited: {ip_str}"
    if ip.is_private:
        return False, f"Private RFC 1918/4193 address prohibited: {ip_str}"
    if ip.is_link_local:
        return False, f"Link-local or cloud metadata address prohibited: {ip_str}"
    if ip.is_multicast:
        return False, f"Multicast address prohibited: {ip_str}"
    if ip.is_unspecified:
        return False, f"Unspecified address prohibited: {ip_str}"
    if ip.is_reserved:
        return False, f"Reserved address prohibited: {ip_str}"

    for net in BLOCKED_NETWORKS:
        if ip.version == net.version and ip in net:
            return False, f"Address {ip_str} falls within prohibited network {net}"

    return True, None

def validate_host_and_resolve(hostname: str, allow_loopback: bool = False) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validate a hostname against blocked names and resolve it to ensure all resolved IPs are safe.
    Mitigates DNS rebinding by performing resolution check upfront.
    """
    host_clean = hostname.strip().lower()

    if not allow_loopback and (host_clean in BLOCKED_HOSTNAMES or host_clean.endswith(".internal") or host_clean.endswith(".local")):
        return False, [], f"Prohibited or internal hostname: {hostname}"

    # Check if host is direct IP
    try:
        ip_obj = ipaddress.ip_address(host_clean)
        allowed, reason = is_ip_allowed(str(ip_obj), allow_loopback=allow_loopback)
        if not allowed:
            return False, [], reason
        return True, [str(ip_obj)], None
    except ValueError:
        pass  # It's a domain name, proceed to DNS resolution

    try:
        # Resolve using socket.getaddrinfo to get all IPv4 and IPv6 records
        addr_info = socket.getaddrinfo(host_clean, None)
        resolved_ips = list(set([item[4][0] for item in addr_info]))
    except socket.gaierror:
        # Standard DNS resolution failure (e.g. NXDOMAIN, unregistered domain, or mock prospect host).
        # An unresolvable domain has no IP address and cannot connect to private internal networks,
        # so it poses no SSRF risk. Allow it through so the audit engine can perform DNS zone queries
        # and record reachability/DNS diagnostic findings.
        return True, [], None
    except Exception as e:
        return False, [], f"Error resolving {hostname}: {str(e)}"

    if not resolved_ips:
        return True, [], None

    # Validate EVERY resolved IP
    for ip in resolved_ips:
        allowed, reason = is_ip_allowed(ip, allow_loopback=allow_loopback)
        if not allowed:
            return False, resolved_ips, f"Security violation: {hostname} resolves to prohibited address {ip} ({reason})"

    return True, resolved_ips, None

def validate_target_url(url: str, allow_loopback: bool = False) -> Tuple[bool, Optional[str], Optional[urllib.parse.ParseResult], List[str]]:
    """
    Validates a URL syntax, scheme, port, and hostname/IP safety.
    Returns: (is_valid, error_reason, parsed_url_object, resolved_ips)
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty", None, []

    url = url.strip()
    if "://" in url:
        scheme = url.split("://", 1)[0].lower()
        if scheme not in ("http", "https"):
            return False, f"Unsupported protocol '{scheme}'. Only HTTP and HTTPS are permitted.", None, []
    else:
        url = "https://" + url

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        return False, f"Malformed URL syntax: {str(e)}", None, []

    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported protocol '{parsed.scheme}'. Only HTTP and HTTPS are permitted.", parsed, []

    if not parsed.hostname:
        return False, "URL is missing a valid hostname", parsed, []

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not allow_loopback and port not in settings.AUDIT_ALLOWED_PORTS:
        return False, f"Prohibited port {port}. Allowed ports are: {settings.AUDIT_ALLOWED_PORTS}", parsed, []

    # Validate hostname and DNS resolution against SSRF blocklist
    is_safe, resolved_ips, error_msg = validate_host_and_resolve(parsed.hostname, allow_loopback=allow_loopback)
    if not is_safe:
        return False, error_msg, parsed, resolved_ips

    return True, None, parsed, resolved_ips

class SSRFSecurityError(httpcore.ConnectError):
    """Raised when an outbound connection targets a prohibited IP, scheme, or SSRF vector."""
    pass

def resolve_and_pin_host(host: str, port: int, allow_loopback: bool = False) -> Tuple[str, List[str]]:
    """
    Resolves hostname and strictly validates every returned IP address.
    If ANY returned IP address is prohibited, raises SSRFSecurityError.
    Prevents DNS rebinding and TOCTOU vulnerabilities.
    Returns (selected_pinned_ip, all_resolved_ips).
    """
    host_clean = host.strip().lower()

    if not allow_loopback and (host_clean in BLOCKED_HOSTNAMES or host_clean.endswith(".internal") or host_clean.endswith(".local")):
        raise SSRFSecurityError(f"Security Policy: Host '{host}' is in prohibited internal hostname list")

    # 1. Handle IP Literals directly
    try:
        ip_obj = ipaddress.ip_address(host_clean)
        allowed, reason = is_ip_allowed(str(ip_obj))
        if not allowed and not (allow_loopback and ip_obj.is_loopback):
            raise SSRFSecurityError(f"Security Policy: Target IP literal '{host}' is prohibited: {reason}")
        return str(ip_obj), [str(ip_obj)]
    except ValueError:
        pass  # It's a domain name, proceed to DNS resolution

    # 2. Resolve via socket.getaddrinfo (all A and AAAA records)
    try:
        addr_infos = socket.getaddrinfo(host_clean, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise SSRFSecurityError(f"DNS resolution failed for '{host}': {e}")
    except Exception as e:
        raise SSRFSecurityError(f"DNS lookup error for '{host}': {e}")

    if not addr_infos:
        raise SSRFSecurityError(f"No DNS records found for host '{host}'")

    resolved_ips: List[str] = []
    for info in addr_infos:
        ip_str = info[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            raise SSRFSecurityError(f"DNS for '{host}' returned invalid IP address representation '{ip_str}'")

        allowed, reason = is_ip_allowed(ip_str)
        if not allowed and not (allow_loopback and ip_obj.is_loopback):
            raise SSRFSecurityError(f"Security Policy: DNS for '{host}' returned prohibited IP '{ip_str}': {reason}")

        if ip_str not in resolved_ips:
            resolved_ips.append(ip_str)

    if not resolved_ips:
        raise SSRFSecurityError(f"No valid publicly routable IP addresses resolved for host '{host}'")

    # Policy: Deterministically pin the first valid IPv4 address if available, otherwise first valid IPv6
    v4_ips = [ip for ip in resolved_ips if ":" not in ip]
    pinned_ip = v4_ips[0] if v4_ips else resolved_ips[0]
    return pinned_ip, resolved_ips

class PinnedAsyncNetworkBackend(httpcore.AsyncNetworkBackend):
    """
    Custom httpcore AsyncNetworkBackend enforcing connection-level IP pinning.
    Guarantees the socket is connected exclusively to the pre-validated IP address,
    preventing DNS rebinding / TOCTOU attacks while preserving:
    - TLS certificate verification
    - TLS SNI (Server Name Indication)
    - HTTP Host header
    """
    def __init__(
        self,
        pinned_map: Optional[Dict[Tuple[str, int], str]] = None,
        allow_loopback_for_testing: bool = False,
        real_backend: Optional[httpcore.AsyncNetworkBackend] = None
    ):
        self._pinned_map: Dict[Tuple[str, int], str] = dict(pinned_map or {})
        self.allow_loopback_for_testing = allow_loopback_for_testing
        self._backend = real_backend or httpcore.AnyIOBackend()
        self.last_connected_addr: Optional[Tuple[str, int]] = None

    def pin_destination(self, host: str, port: int, ip: str) -> None:
        """Explicitly pins a destination (host, port) to a validated IP."""
        self._pinned_map[(host.strip().lower(), port)] = ip

    def get_pinned_destination(self, host: str, port: int) -> Optional[str]:
        return self._pinned_map.get((host.strip().lower(), port))

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
        local_address: Optional[str] = None,
        socket_options: Optional[Any] = None,
    ) -> httpcore.AsyncNetworkStream:
        host_key = host.strip().lower()

        # Retrieve pinned IP or resolve and validate on the fly
        if (host_key, port) in self._pinned_map:
            target_ip = self._pinned_map[(host_key, port)]
            # Defense-in-depth: Re-verify pinned IP is safe before socket connect
            ip_obj = ipaddress.ip_address(target_ip)
            allowed, reason = is_ip_allowed(target_ip)
            if not allowed and not (self.allow_loopback_for_testing and ip_obj.is_loopback):
                raise SSRFSecurityError(f"Security Policy: Pinned IP '{target_ip}' is prohibited: {reason}")
        else:
            target_ip, _ = resolve_and_pin_host(host, port, allow_loopback=self.allow_loopback_for_testing)
            self._pinned_map[(host_key, port)] = target_ip

        # Establish TCP socket connection directly to the pinned IP
        stream = await self._backend.connect_tcp(
            target_ip,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options
        )

        # Confirm actual connected socket peer matches the pinned destination
        peer = stream.get_extra_info("server_addr")
        if peer:
            connected_ip = str(peer[0])
            self.last_connected_addr = (connected_ip, peer[1])
            if connected_ip != target_ip:
                await stream.aclose()
                raise SSRFSecurityError(
                    f"Security Policy: Connected peer IP '{connected_ip}' does not match pinned IP '{target_ip}'"
                )

        return stream

    async def connect_unix_socket(self, path: str, timeout=None, socket_options=None):
        raise SSRFSecurityError("Unix domain sockets are prohibited for outbound SSRF requests")

    async def sleep(self, seconds: float) -> None:
        await self._backend.sleep(seconds)

class SSRFProtectedTransport(httpx.AsyncHTTPTransport):
    """
    HTTPX Async Transport with connection-level IP pinning and SSRF defense.
    - Connects TCP sockets only to security-validated destination IPs
    - Preserves TLS SNI, certificate hostname verification, and Host header
    - Prevents DNS rebinding and connection-pool poisoning (max_keepalive_connections=0)
    """
    def __init__(
        self,
        pinned_map: Optional[Dict[Tuple[str, int], str]] = None,
        allow_loopback_for_testing: bool = False,
        verify: Any = True,
        **kwargs
    ):
        self.pinned_backend = PinnedAsyncNetworkBackend(
            pinned_map=pinned_map,
            allow_loopback_for_testing=allow_loopback_for_testing
        )
        kwargs.setdefault("retries", 0)
        super().__init__(verify=verify, **kwargs)
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=self._pool._ssl_context,
            network_backend=self.pinned_backend,
            max_connections=10,
            max_keepalive_connections=0,  # Zero keepalive eliminates cross-request connection reuse poisoning
            keepalive_expiry=0.0,
            retries=0,
            http1=True,
            http2=False
        )

def connect_safe_tls_socket(
    domain: str,
    port: int = 443,
    timeout: float = 5.0,
    ssl_context: Optional[ssl.SSLContext] = None,
    allow_loopback_for_testing: bool = False
) -> Tuple[ssl.SSLSocket, str]:
    """
    Connects a raw TLS socket to a pre-validated, pinned destination IP while
    strictly preserving TLS SNI and certificate verification against the logical domain.
    Used for direct SSL inspection in audit engine.
    """
    pinned_ip, _ = resolve_and_pin_host(domain, port, allow_loopback=allow_loopback_for_testing)

    ctx = ssl_context or ssl.create_default_context()
    raw_sock = socket.create_connection((pinned_ip, port), timeout=timeout)
    try:
        ssock = ctx.wrap_socket(raw_sock, server_hostname=domain)
        return ssock, pinned_ip
    except Exception:
        raw_sock.close()
        raise

class SafeHttpResponse:
    """Wrapper around HTTP response for SSRF-safe requests."""
    def __init__(
        self,
        status_code: int,
        text: str,
        url: str,
        headers: Dict[str, str],
        raw_response: Optional[httpx.Response] = None,
        was_truncated: bool = False,
        pinned_ip: Optional[str] = None
    ):
        self.status_code = status_code
        self.text = text
        self.url = url
        self.headers = headers
        self.raw_response = raw_response
        self.was_truncated = was_truncated
        self.pinned_ip = pinned_ip

async def _do_safe_get(
    client: httpx.AsyncClient,
    initial_url: str,
    headers: Optional[Dict[str, str]],
    timeout: float,
    max_redirects: int,
    max_bytes: int,
    transport: Optional[SSRFProtectedTransport] = None,
    allow_loopback_for_testing: bool = False
) -> Tuple[bool, Optional[SafeHttpResponse], Optional[str]]:
    current_url = initial_url
    redirect_count = 0
    visited_urls: Set[str] = set()

    req_headers = dict(headers or {})

    while True:
        # 1. Pre-flight SSRF validation on current URL before connecting
        is_safe, error_msg, parsed, resolved_ips = validate_target_url(
            current_url,
            allow_loopback=allow_loopback_for_testing
        )
        if not is_safe:
            return False, None, f"SSRF Protection blocked destination '{current_url}': {error_msg}"

        if current_url in visited_urls:
            return False, None, f"SSRF Protection: Redirect loop detected at '{current_url}'"
        visited_urls.add(current_url)

        # Pin validated destination IP in transport if available
        current_port = parsed.port or (443 if parsed.scheme == "https" else 80)
        pinned_ip = resolved_ips[0] if resolved_ips else None
        if transport and pinned_ip:
            transport.pinned_backend.pin_destination(parsed.hostname, current_port, pinned_ip)

        try:
            async with client.stream("GET", current_url, headers=req_headers, follow_redirects=False) as resp:
                if resp.status_code in (301, 302, 303, 307, 308) and "Location" in resp.headers:
                    redirect_count += 1
                    if redirect_count > max_redirects:
                        return False, None, f"SSRF Protection: Maximum redirect limit ({max_redirects}) exceeded"

                    raw_location = resp.headers.get("Location", "")
                    if not raw_location or not raw_location.strip():
                        return False, None, "SSRF Protection: Malformed empty redirect Location header"

                    try:
                        next_url = urllib.parse.urljoin(current_url, raw_location.strip())
                    except Exception as e:
                        return False, None, f"SSRF Protection: Malformed redirect Location header '{raw_location}': {e}"

                    # Explicitly reject non-http(s) schemes on redirect
                    parsed_next = urllib.parse.urlparse(next_url)
                    if parsed_next.scheme.lower() not in ("http", "https"):
                        return False, None, f"SSRF Protection: Redirect to prohibited scheme '{parsed_next.scheme}'"

                    # Cross-origin authorization header stripping
                    next_port = parsed_next.port or (443 if parsed_next.scheme == "https" else 80)
                    if (
                        parsed.hostname.lower() != parsed_next.hostname.lower() or
                        parsed.scheme.lower() != parsed_next.scheme.lower() or
                        current_port != next_port
                    ):
                        req_headers = {k: v for k, v in req_headers.items() if k.lower() not in ("authorization", "cookie")}

                    current_url = next_url
                    continue

                # Stream response body up to max_bytes to prevent memory exhaustion / compression bombs
                downloaded_bytes = bytearray()
                was_truncated = False
                async for chunk in resp.aiter_bytes():
                    downloaded_bytes.extend(chunk)
                    if len(downloaded_bytes) > max_bytes:
                        downloaded_bytes = downloaded_bytes[:max_bytes]
                        was_truncated = True
                        break

                text = downloaded_bytes.decode("utf-8", errors="ignore")
                return True, SafeHttpResponse(
                    status_code=resp.status_code,
                    text=text,
                    url=str(resp.url),
                    headers=dict(resp.headers),
                    raw_response=resp,
                    was_truncated=was_truncated,
                    pinned_ip=pinned_ip
                ), None

        except (SSRFSecurityError, httpx.ConnectError) as e:
            return False, None, f"Connection blocked by SSRF protection for '{current_url}': {str(e)}"
        except httpx.RequestError as e:
            return False, None, f"Network request failed for '{current_url}': {str(e)}"
        except Exception as e:
            return False, None, f"Request error for '{current_url}': {str(e)}"

async def safe_http_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 7.0,
    max_redirects: int = 5,
    max_bytes: int = 5 * 1024 * 1024,
    client: Optional[httpx.AsyncClient] = None,
    allow_loopback_for_testing: bool = False,
    verify: Any = True
) -> Tuple[bool, Optional[SafeHttpResponse], Optional[str]]:
    """
    Executes an SSRF-safe HTTP GET request with:
    - Connection-level IP pinning and DNS rebinding protection
    - Preserved TLS SNI and hostname certificate validation
    - Manual per-hop redirect validation (follow_redirects=False)
    - Cross-origin Authorization header stripping
    - Loop detection (visited URLs tracking)
    - Scheme whitelist validation (http/https only)
    - Safe relative and absolute URL resolution with urljoin
    - Malformed Location header protection
    - Response body streaming with byte caps to prevent memory exhaustion and compression bombs

    Returns: (is_success, safe_http_response, error_message)
    """
    if client is not None:
        return await _do_safe_get(
            client,
            url,
            headers,
            timeout,
            max_redirects,
            max_bytes,
            allow_loopback_for_testing=allow_loopback_for_testing
        )
    else:
        transport = SSRFProtectedTransport(
            allow_loopback_for_testing=allow_loopback_for_testing,
            verify=verify
        )
        async with httpx.AsyncClient(
            transport=transport,
            timeout=timeout,
            follow_redirects=False
        ) as own_client:
            return await _do_safe_get(
                own_client,
                url,
                headers,
                timeout,
                max_redirects,
                max_bytes,
                transport=transport,
                allow_loopback_for_testing=allow_loopback_for_testing
            )
