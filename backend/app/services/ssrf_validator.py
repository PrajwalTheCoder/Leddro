import ipaddress
import socket
import urllib.parse
from typing import Tuple, List, Optional
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

def is_ip_allowed(ip_str: str) -> Tuple[bool, Optional[str]]:
    """Check if an IP address is publicly routable and not in private/reserved/cloud-metadata ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False, f"Invalid IP address representation: {ip_str}"

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
        if ip in net:
            return False, f"Address {ip_str} falls within prohibited network {net}"

    return True, None

def validate_host_and_resolve(hostname: str) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validate a hostname against blocked names and resolve it to ensure all resolved IPs are safe.
    Mitigates DNS rebinding by performing resolution check upfront.
    """
    host_clean = hostname.strip().lower()

    if host_clean in BLOCKED_HOSTNAMES or host_clean.endswith(".internal") or host_clean.endswith(".local"):
        return False, [], f"Prohibited or internal hostname: {hostname}"

    # Check if host is direct IP
    try:
        ip_obj = ipaddress.ip_address(host_clean)
        allowed, reason = is_ip_allowed(str(ip_obj))
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
        allowed, reason = is_ip_allowed(ip)
        if not allowed:
            return False, resolved_ips, f"Security violation: {hostname} resolves to prohibited address {ip} ({reason})"

    return True, resolved_ips, None

def validate_target_url(url: str) -> Tuple[bool, Optional[str], Optional[urllib.parse.ParseResult], List[str]]:
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
    if port not in settings.AUDIT_ALLOWED_PORTS:
        return False, f"Prohibited port {port}. Allowed ports are: {settings.AUDIT_ALLOWED_PORTS}", parsed, []

    # Validate hostname and DNS resolution against SSRF blocklist
    is_safe, resolved_ips, error_msg = validate_host_and_resolve(parsed.hostname)
    if not is_safe:
        return False, error_msg, parsed, resolved_ips

    return True, None, parsed, resolved_ips
