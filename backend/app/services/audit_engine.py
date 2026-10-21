import time
import ssl
import socket
import datetime
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup
import dns.resolver
from typing import Dict, Any, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.services.ssrf_validator import (
    validate_target_url,
    SSRFProtectedTransport,
    connect_safe_tls_socket,
    SSRFSecurityError
)
from backend.app.services.email_scraper import extract_contacts_from_html, verify_email_mx

class AuditEngine:
    """
    Genuine server-side HTTP and HTML inspection engine with robust SSRF protections,
    TLS certificate inspection, DNS zone queries, and deterministic evidence generation.
    """

    async def execute_audit(self, target_url: str) -> Dict[str, Any]:
        audit_start = time.time()
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        findings: List[Dict[str, Any]] = []

        # 1. URL & SSRF Validation
        is_safe, error_msg, parsed_url, resolved_ips = validate_target_url(target_url)
        if not is_safe:
            findings.append({
                "id": f"f-ssrf-{int(time.time()*1000)}",
                "title": "Target address rejected by security filter",
                "severity": "high",
                "check_status": "ERROR",
                "observed": f"URL {target_url} failed pre-flight security validation: {error_msg}",
                "evidence": f"Pre-flight SSRF Validation: FAILED\nReason: {error_msg}\nResolved IPs: {resolved_ips}",
                "why_it_matters": "Prohibiting requests to internal addresses, loopbacks, and cloud metadata is mandatory to prevent Server-Side Request Forgery.",
                "recommended_action": "Provide a publicly routable standard Internet domain or web address.",
                "confidence": 1.0,
                "category": "security",
                "checked_url": target_url
            })
            return {
                "url": target_url,
                "timestamp": timestamp_str,
                "status": "failed",
                "overall_score": 0,
                "findings": findings,
                "raw_dns": {"aRecord": "N/A", "mxRecord": "N/A", "responseMs": 0, "nameservers": []},
                "raw_ssl": {"valid": False, "issuer": "None", "expiresDays": 0, "tlsVersion": "N/A", "cipher": "N/A"},
                "performance": {"ttfbMs": 0, "domReadyMs": 0, "pageSizeKb": 0, "mobileViewportPresent": False},
                "headers": {}
            }

        domain = parsed_url.hostname
        normalized_url = parsed_url.geturl()

        # 2. DNS Zone Inspection (A, AAAA, MX, SPF, DMARC)
        dns_data = self._inspect_dns(domain)
        findings.extend(dns_data["findings"])

        # 3. TLS Certificate & Cryptography Inspection (if HTTPS)
        ssl_data = {"valid": False, "issuer": "None", "expiresDays": 0, "tlsVersion": "N/A", "cipher": "N/A"}
        if parsed_url.scheme == "https":
            ssl_data = self._inspect_tls(domain, parsed_url.port or 443)
            findings.extend(ssl_data.get("findings", []))

        # 4. HTTP Fetching with SSRF-safe redirect following and size limits
        http_data = await self._fetch_http_safely(normalized_url)
        findings.extend(http_data.get("findings", []))

        # 5. HTML Content Inspection (if body retrieved)
        html_findings = []
        html_content = http_data.get("body", "")
        discovered_contacts = {"emails": [], "phones": []}
        if html_content:
            html_findings = self._inspect_html(html_content, http_data.get("final_url", normalized_url))
            findings.extend(html_findings)

            # 5.1 Extract Public Contact Info (Emails and Phone numbers)
            raw_contacts = extract_contacts_from_html(html_content, http_data.get("final_url", normalized_url))
            verified_emails = [em for em in raw_contacts.get("emails", []) if verify_email_mx(em)]
            discovered_contacts = {
                "emails": verified_emails,
                "phones": raw_contacts.get("phones", [])
            }
            if verified_emails:
                findings.append({
                    "id": f"f-contact-email-{int(time.time()*1000)}",
                    "title": f"Public business email verified: {verified_emails[0]}",
                    "severity": "info",
                    "check_status": "PASS",
                    "observed": f"Discovered verified public business email '{verified_emails[0]}' with active MX routing.",
                    "evidence": f"Found on: {http_data.get('final_url', normalized_url)}\nStatus: MX Records Active\nAll candidates: {', '.join(verified_emails[:3])}",
                    "why_it_matters": "Authentic public email enables high-deliverability technical correspondence without guessing.",
                    "recommended_action": "Target verified business email for technical audit briefing.",
                    "confidence": 1.0,
                    "category": "reachability",
                    "checked_url": http_data.get("final_url", normalized_url)
                })

        # 6. Calculate Opportunity Score (Higher technical deficits = higher outreach opportunity score)
        high_count = sum(1 for f in findings if f["severity"] == "high")
        med_count = sum(1 for f in findings if f["severity"] == "medium")
        low_count = sum(1 for f in findings if f["severity"] == "low")

        # Opportunity score calculation
        urgency = min(40, high_count * 20 + med_count * 10)
        intent = 25  # standard commercial baseline
        ease = max(15, 30 - high_count * 5)
        overall_score = min(98, max(45, 50 + urgency))

        total_duration_ms = int((time.time() - audit_start) * 1000)

        return {
            "url": http_data.get("final_url", normalized_url),
            "timestamp": timestamp_str,
            "status": "completed" if http_data.get("status_code") else "failed",
            "overall_score": overall_score,
            "score_breakdown": {
                "technicalUrgency": urgency,
                "commercialIntent": intent,
                "resolutionEase": ease
            },
            "findings": findings,
            "raw_dns": dns_data["details"],
            "raw_ssl": ssl_data,
            "performance": {
                "ttfbMs": http_data.get("ttfb_ms", 0),
                "domReadyMs": total_duration_ms,
                "pageSizeKb": round(len(html_content.encode("utf-8")) / 1024, 1),
                "mobileViewportPresent": http_data.get("viewport_present", False)
            },
            "headers": http_data.get("headers", {}),
            "discovered_contacts": discovered_contacts
        }

    def _inspect_dns(self, domain: str) -> Dict[str, Any]:
        """Performs genuine DNS queries for A, MX, SPF, and DMARC."""
        dns_start = time.time()
        findings = []
        a_records = []
        mx_records = []
        nameservers = []
        spf_found = False
        dmarc_found = False

        resolver = dns.resolver.Resolver()
        resolver.timeout = 4.0
        resolver.lifetime = 4.0

        # Query A records
        try:
            answers = resolver.resolve(domain, "A")
            a_records = [str(rdata) for rdata in answers]
        except Exception:
            pass

        # Query MX records
        try:
            mx_answers = resolver.resolve(domain, "MX")
            mx_records = [f"{rdata.exchange.to_text().rstrip('.')} (pri {rdata.preference})" for rdata in mx_answers]
        except Exception:
            pass

        # Query TXT records for SPF
        try:
            txt_answers = resolver.resolve(domain, "TXT")
            for rdata in txt_answers:
                txt_str = "".join([part.decode("utf-8", errors="ignore") for part in rdata.strings])
                if "v=spf1" in txt_str.lower():
                    spf_found = True
                    break
        except Exception:
            pass

        # Query _dmarc record
        try:
            dmarc_answers = resolver.resolve(f"_dmarc.{domain}", "TXT")
            for rdata in dmarc_answers:
                dmarc_str = "".join([part.decode("utf-8", errors="ignore") for part in rdata.strings])
                if "v=dmarc1" in dmarc_str.lower():
                    dmarc_found = True
                    break
        except Exception:
            pass

        # Subdomain fallback: If SPF or DMARC not on subdomain (e.g. www.domain.com),
        # query organizational / apex domain per RFC 7489 Section 6.6.3
        parts = domain.split(".")
        base_domain = None
        if len(parts) > 2 and parts[0].lower() == "www":
            base_domain = ".".join(parts[1:])
        elif len(parts) > 2:
            base_domain = ".".join(parts[-2:])

        if base_domain and base_domain != domain:
            if not spf_found:
                try:
                    base_txt = resolver.resolve(base_domain, "TXT")
                    for rdata in base_txt:
                        txt_str = "".join([part.decode("utf-8", errors="ignore") for part in rdata.strings])
                        if "v=spf1" in txt_str.lower():
                            spf_found = True
                            break
                except Exception:
                    pass

            if not dmarc_found:
                try:
                    base_dmarc = resolver.resolve(f"_dmarc.{base_domain}", "TXT")
                    for rdata in base_dmarc:
                        dmarc_str = "".join([part.decode("utf-8", errors="ignore") for part in rdata.strings])
                        if "v=dmarc1" in dmarc_str.lower():
                            dmarc_found = True
                            break
                except Exception:
                    pass

        query_ms = int((time.time() - dns_start) * 1000)

        # Evidence evaluation
        if not a_records:
            findings.append({
                "id": f"f-dns-a-{int(time.time()*1000)}",
                "title": "No DNS A/IPv4 records discovered",
                "severity": "high",
                "check_status": "FAIL",
                "observed": f"DNS zone lookup for domain '{domain}' returned no valid IPv4 address records.",
                "evidence": f"DNS Query: A {domain}\nStatus: NXDOMAIN / NO_DATA\nQuery Duration: {query_ms}ms",
                "why_it_matters": "Browsers cannot resolve the web server IP address, resulting in site reachability failure.",
                "recommended_action": "Configure an A record pointing to your production web server IP address in domain DNS manager.",
                "confidence": 1.0,
                "category": "reachability",
                "checked_url": f"http://{domain}"
            })
        else:
            findings.append({
                "id": f"f-dns-a-pass-{int(time.time()*1000)}",
                "title": "DNS A/IPv4 resolution verified",
                "severity": "info",
                "check_status": "PASS",
                "observed": f"Domain resolved to {len(a_records)} IPv4 address(es): {', '.join(a_records[:3])}.",
                "evidence": f"DNS Query: A {domain}\nResolved: {', '.join(a_records)}\nQuery Time: {query_ms}ms",
                "why_it_matters": "Domain correctly routes client traffic to host infrastructure.",
                "recommended_action": "DNS A resolution is operational.",
                "confidence": 1.0,
                "category": "reachability",
                "checked_url": f"http://{domain}"
            })

        if mx_records:
            findings.append({
                "id": f"f-dns-mx-pass-{int(time.time()*1000)}",
                "title": "Mail Exchange (MX) records verified",
                "severity": "info",
                "check_status": "PASS",
                "observed": f"Discovered {len(mx_records)} MX mail gateway server(s).",
                "evidence": f"DNS Query: MX {domain}\nGateways: {', '.join(mx_records[:2])}",
                "why_it_matters": "Commercial email deliverability requires verified MX destination routers.",
                "recommended_action": "Mail exchanger routing is active.",
                "confidence": 1.0,
                "category": "reachability",
                "checked_url": f"https://{domain}"
            })

        if not spf_found:
            findings.append({
                "id": f"f-dns-spf-{int(time.time()*1000)}",
                "title": "Missing Sender Policy Framework (SPF) DNS record",
                "severity": "medium",
                "check_status": "WARNING",
                "observed": f"No SPF 'v=spf1' TXT declaration discovered in DNS zone for '{domain}'.",
                "evidence": f"DNS Query: TXT {domain}\nSPF Tag: [NOT FOUND]\nEvaluated records: {len(a_records)} A records",
                "why_it_matters": "Inbound corporate mail servers may flag legitimate company emails as untrusted or route them to spam filters.",
                "recommended_action": "Add a TXT record with authorized outgoing mail server definitions (e.g., 'v=spf1 include:_spf.google.com ~all').",
                "confidence": 0.95,
                "category": "seo_meta",
                "checked_url": f"https://{domain}"
            })

        if not dmarc_found:
            findings.append({
                "id": f"f-dns-dmarc-{int(time.time()*1000)}",
                "title": "Missing DMARC email authentication policy",
                "severity": "low",
                "check_status": "WARNING",
                "observed": f"Domain does not have an active DMARC policy defined at _dmarc.{domain}.",
                "evidence": f"DNS Query: TXT _dmarc.{domain}\nStatus: NXDOMAIN / NO_DATA",
                "why_it_matters": "Leaves the domain vulnerable to spoofing and unauthorized email sender impersonation.",
                "recommended_action": "Publish a DMARC policy TXT record at _dmarc with at least 'v=DMARC1; p=none;'.",
                "confidence": 0.95,
                "category": "security",
                "checked_url": f"https://{domain}"
            })

        return {
            "details": {
                "aRecord": ", ".join(a_records) if a_records else "None",
                "mxRecord": ", ".join(mx_records) if mx_records else "None",
                "responseMs": query_ms,
                "nameservers": nameservers
            },
            "findings": findings
        }

    def _inspect_tls(self, domain: str, port: int = 443) -> Dict[str, Any]:
        """Connects via SSL socket to evaluate certificate validity, cipher, and expiration."""
        findings = []
        try:
            ssock, pinned_ip = connect_safe_tls_socket(domain, port=port, timeout=settings.AUDIT_CONNECT_TIMEOUT)
            with ssock:
                cert = ssock.getpeercert()
                tls_version = ssock.version()
                cipher_tuple = ssock.cipher()
                cipher_name = cipher_tuple[0] if cipher_tuple else "Unknown"

                # Parse expiration date
                not_after_str = cert.get("notAfter", "")
                # Format: 'Apr 18 23:59:59 2026 GMT'
                not_after_dt = datetime.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                days_remaining = (not_after_dt - now_dt).days

                # Extract Issuer
                issuer_dict = dict(x[0] for x in cert.get("issuer", ()))
                issuer_name = issuer_dict.get("organizationName") or issuer_dict.get("commonName") or "Unknown CA"

                if days_remaining < 0:
                    findings.append({
                        "id": f"f-ssl-exp-{int(time.time()*1000)}",
                        "title": "SSL/TLS certificate has expired",
                        "severity": "high",
                        "check_status": "FAIL",
                        "observed": f"The TLS certificate expired {abs(days_remaining)} days ago on {not_after_str}.",
                        "evidence": f"Certificate Expiry: {not_after_str}\nCurrent Audit Time: {now_dt.strftime('%b %d %Y')}\nDays Remaining: {days_remaining}\nIssuer: {issuer_name}",
                        "why_it_matters": "Browsers reject the connection with intimidating warning screens, preventing customers from accessing the site.",
                        "recommended_action": "Renew the SSL/TLS certificate immediately via your hosting control panel or ACME bot.",
                        "confidence": 1.0,
                        "category": "security",
                        "checked_url": f"https://{domain}"
                    })
                elif days_remaining <= 14:
                    findings.append({
                        "id": f"f-ssl-warn-{int(time.time()*1000)}",
                        "title": "SSL/TLS certificate expiring soon",
                        "severity": "medium",
                        "check_status": "WARNING",
                        "observed": f"The TLS certificate expires in {days_remaining} days on {not_after_str}.",
                        "evidence": f"Certificate Expiry: {not_after_str}\nDays Remaining: {days_remaining}",
                        "why_it_matters": "Risk of unexpected outage if automated renewal triggers fail.",
                        "recommended_action": "Verify automated renewal automation status before certificate reaches expiration.",
                        "confidence": 0.98,
                        "category": "security",
                        "checked_url": f"https://{domain}"
                    })
                else:
                    findings.append({
                        "id": f"f-ssl-pass-{int(time.time()*1000)}",
                        "title": "Valid SSL/TLS certificate verified",
                        "severity": "info",
                        "check_status": "PASS",
                        "observed": f"Valid TLS certificate issued by {issuer_name} with {days_remaining} days remaining.",
                        "evidence": f"Issuer: {issuer_name}\nTLS Version: {tls_version}\nCipher: {cipher_name}\nDays Remaining: {days_remaining}",
                        "why_it_matters": "Encryption protects customer data in transit and satisfies browser security requirements.",
                        "recommended_action": "Certificate is healthy. No action required.",
                        "confidence": 1.0,
                        "category": "security",
                        "checked_url": f"https://{domain}"
                    })

                return {
                    "valid": days_remaining >= 0,
                    "issuer": issuer_name,
                    "expiresDays": days_remaining,
                    "tlsVersion": tls_version,
                    "cipher": cipher_name,
                    "findings": findings
                }
        except Exception as e:
            err_msg = str(e)
            findings.append({
                "id": f"f-ssl-err-{int(time.time()*1000)}",
                "title": "TLS connection handshake failed",
                "severity": "high",
                "check_status": "FAIL",
                "observed": f"Failed to negotiate secure TLS connection on port {port}: {err_msg}",
                "evidence": f"Port: {port}\nTLS Handshake Error: {err_msg}",
                "why_it_matters": "Visitors connecting over HTTPS will receive connection refusal or protocol error.",
                "recommended_action": "Verify web server SSL bindings and listening ports.",
                "confidence": 0.98,
                "category": "security",
                "checked_url": f"https://{domain}"
            })
            return {
                "valid": False,
                "issuer": "Connection Failed",
                "expiresDays": 0,
                "tlsVersion": "None",
                "cipher": "None",
                "findings": findings
            }

    async def _fetch_http_safely(self, initial_url: str) -> Dict[str, Any]:
        """
        Fetches the root web document with SSRF protection on every redirect hop,
        streamed download limits, and TTFB measurement.
        """
        current_url = initial_url
        redirect_hops = 0
        findings = []
        ttfb_ms = 0
        final_response = None
        body_content = ""

        transport = SSRFProtectedTransport()
        headers = {
            "User-Agent": settings.AUDIT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        async with httpx.AsyncClient(transport=transport, follow_redirects=False, timeout=settings.AUDIT_READ_TIMEOUT) as client:
            while redirect_hops <= settings.AUDIT_MAX_REDIRECTS:
                # SSRF validation before every hop
                is_safe, error_msg, parsed_hop, resolved_ips = validate_target_url(current_url)
                if not is_safe:
                    findings.append({
                        "id": f"f-ssrf-hop-{int(time.time()*1000)}",
                        "title": "Redirect hop targeted prohibited IP address",
                        "severity": "high",
                        "check_status": "FAIL",
                        "observed": f"Redirect hop {redirect_hops} to '{current_url}' was blocked: {error_msg}",
                        "evidence": f"Redirect Target: {current_url}\nBlocked By: SSRF Protection Validator\nReason: {error_msg}",
                        "why_it_matters": "Web servers must not redirect automated crawlers to private or cloud infrastructure endpoints.",
                        "recommended_action": "Fix redirect rules to only route to public URLs.",
                        "confidence": 1.0,
                        "category": "security",
                        "checked_url": current_url
                    })
                    break

                hop_port = parsed_hop.port or (443 if parsed_hop.scheme == "https" else 80)
                if resolved_ips:
                    transport.pinned_backend.pin_destination(parsed_hop.hostname, hop_port, resolved_ips[0])

                req_start = time.time()
                try:
                    # Stream response to enforce size limits
                    async with client.stream("GET", current_url, headers=headers) as resp:
                        ttfb_ms = int((time.time() - req_start) * 1000)
                        status_code = resp.status_code
                        final_response = resp

                        # Read stream with size limit
                        downloaded_bytes = bytearray()
                        async for chunk in resp.aiter_bytes():
                            downloaded_bytes.extend(chunk)
                            if len(downloaded_bytes) > settings.AUDIT_MAX_RESPONSE_BYTES:
                                findings.append({
                                    "id": f"f-size-{int(time.time()*1000)}",
                                    "title": "Response exceeded maximum download size limit",
                                    "severity": "medium",
                                    "check_status": "WARNING",
                                    "observed": f"Response payload exceeded 5MB cap (truncated at {len(downloaded_bytes)} bytes).",
                                    "evidence": f"Size: {len(downloaded_bytes)} bytes\nStatus: {status_code}",
                                    "why_it_matters": "Oversized initial HTML documents degrade mobile load times and waste bandwidth.",
                                    "recommended_action": "Reduce initial document payload and lazy-load non-essential resources.",
                                    "confidence": 0.95,
                                    "category": "performance",
                                    "checked_url": current_url
                                })
                                break

                        body_content = downloaded_bytes.decode("utf-8", errors="ignore")

                        # Check for redirect status
                        if resp.is_redirect and "Location" in resp.headers:
                            redirect_hops += 1
                            target_loc = resp.headers["Location"].strip()
                            if not target_loc:
                                break
                            target_url = urljoin(current_url, target_loc)
                            parsed_next = urlparse(target_url)
                            if parsed_next.scheme.lower() not in ("http", "https"):
                                findings.append({
                                    "id": f"f-ssrf-scheme-{int(time.time()*1000)}",
                                    "title": "Redirect hop targeted prohibited URI scheme",
                                    "severity": "high",
                                    "check_status": "FAIL",
                                    "observed": f"Redirect to prohibited scheme '{parsed_next.scheme}' was blocked: {target_url}",
                                    "evidence": f"Redirect Target: {target_url}\nBlocked By: SSRF Scheme Validator",
                                    "why_it_matters": "Web servers must not redirect crawlers to non-HTTP protocols.",
                                    "recommended_action": "Fix redirect rules to only route to public HTTP/HTTPS URLs.",
                                    "confidence": 1.0,
                                    "category": "security",
                                    "checked_url": current_url
                                })
                                break

                            # Cross-origin sensitive header stripping
                            next_port = parsed_next.port or (443 if parsed_next.scheme == "https" else 80)
                            if (
                                parsed_hop.hostname.lower() != parsed_next.hostname.lower() or
                                parsed_hop.scheme.lower() != parsed_next.scheme.lower() or
                                hop_port != next_port
                            ):
                                headers = {k: v for k, v in headers.items() if k.lower() not in ("authorization", "cookie")}

                            current_url = target_url
                            continue
                        else:
                            # Not a redirect, finished
                            break
                except httpx.ConnectTimeout:
                    findings.append({
                        "id": f"f-timeout-{int(time.time()*1000)}",
                        "title": "Connection to target web server timed out",
                        "severity": "high",
                        "check_status": "ERROR",
                        "observed": f"Connection attempt to {current_url} timed out after {settings.AUDIT_CONNECT_TIMEOUT} seconds.",
                        "evidence": f"URL: {current_url}\nTimeout Limit: {settings.AUDIT_CONNECT_TIMEOUT}s\nError: Connection timed out",
                        "why_it_matters": "The server failed to accept connections within standard network thresholds, causing visitor drop-off.",
                        "recommended_action": "Check web server load, firewall rules, and host uptime.",
                        "confidence": 0.99,
                        "category": "reachability",
                        "checked_url": current_url
                    })
                    break
                except (SSRFSecurityError, httpx.ConnectError) as e:
                    err_str = str(e)
                    is_ssrf_block = isinstance(e, SSRFSecurityError) or any(term in err_str.lower() for term in ["prohibited", "ssrf", "loopback", "security"])
                    if is_ssrf_block:
                        findings.append({
                            "id": f"f-ssrf-block-{int(time.time()*1000)}",
                            "title": "Outbound connection blocked by connection-level SSRF protection",
                            "severity": "high",
                            "check_status": "FAIL",
                            "observed": f"SSRF transport blocked connection to {current_url}: {err_str}",
                            "evidence": f"URL: {current_url}\nSSRF Defense: {err_str}",
                            "why_it_matters": "Outbound traffic to private, internal, or prohibited destinations is strictly denied.",
                            "recommended_action": "Ensure target host resolves to publicly routable IP addresses.",
                            "confidence": 1.0,
                            "category": "security",
                            "checked_url": current_url
                        })
                    else:
                        findings.append({
                            "id": f"f-conn-err-{int(time.time()*1000)}",
                            "title": "TCP Connection refused or unreachable",
                            "severity": "high",
                            "check_status": "ERROR",
                            "observed": f"Network error connecting to {current_url}: {err_str}",
                            "evidence": f"URL: {current_url}\nSocket Error: {err_str}",
                            "why_it_matters": "The target web server is offline or rejecting incoming HTTP traffic.",
                            "recommended_action": "Verify web server process status (nginx/apache) and network connectivity.",
                            "confidence": 1.0,
                            "category": "reachability",
                            "checked_url": current_url
                        })
                    break
                except Exception as e:
                    findings.append({
                        "id": f"f-http-err-{int(time.time()*1000)}",
                        "title": "HTTP request failed unexpectedly",
                        "severity": "high",
                        "check_status": "ERROR",
                        "observed": f"Failed to retrieve {current_url}: {str(e)}",
                        "evidence": f"Error: {str(e)}",
                        "why_it_matters": "Audit engine could not complete document retrieval.",
                        "recommended_action": "Inspect target server network and DNS availability.",
                        "confidence": 0.95,
                        "category": "reachability",
                        "checked_url": current_url
                    })
                    break

        if final_response:
            status = final_response.status_code
            resp_headers = dict(final_response.headers)

            if status == 404:
                findings.append({
                    "id": f"f-http-404-{int(time.time()*1000)}",
                    "title": "Target page returned HTTP 404 Not Found",
                    "severity": "high",
                    "check_status": "FAIL",
                    "observed": f"The target URL returned HTTP status code 404 during live crawl.",
                    "evidence": f"GET {current_url} HTTP/1.1\n\nHTTP/1.1 404 Not Found\nServer: {resp_headers.get('server', 'unknown')}\nContent-Length: {len(body_content)}",
                    "why_it_matters": "Visitors navigating to this page receive a dead end error, causing complete lead abandonment.",
                    "recommended_action": "Verify URL routing and ensure root page publishes active content.",
                    "confidence": 1.0,
                    "category": "reachability",
                    "http_status": 404,
                    "response_time_ms": ttfb_ms,
                    "checked_url": current_url
                })
            elif status >= 500:
                findings.append({
                    "id": f"f-http-500-{int(time.time()*1000)}",
                    "title": f"Web server returned HTTP {status} Internal Error",
                    "severity": "high",
                    "check_status": "FAIL",
                    "observed": f"Target server returned a 5xx server-side failure status code: HTTP {status}.",
                    "evidence": f"GET {current_url} HTTP/1.1\n\nHTTP/1.1 {status} Server Error\nHeaders: {list(resp_headers.keys())}",
                    "why_it_matters": "Back-end application error crashing user requests.",
                    "recommended_action": "Inspect server error logs and application crash dumps.",
                    "confidence": 1.0,
                    "category": "reachability",
                    "http_status": status,
                    "response_time_ms": ttfb_ms,
                    "checked_url": current_url
                })
            elif 200 <= status < 400:
                findings.append({
                    "id": f"f-http-pass-{int(time.time()*1000)}",
                    "title": f"HTTP status {status} OK verified",
                    "severity": "info",
                    "check_status": "PASS",
                    "observed": f"Target server returned successful HTTP response code {status} in {ttfb_ms} ms.",
                    "evidence": f"GET {current_url}\nHTTP/1.1 {status}\nServer: {resp_headers.get('server', 'standard')}\nPayload: {len(body_content)} bytes",
                    "why_it_matters": "Active HTTP response verifies host availability and connectivity.",
                    "recommended_action": "Target page is reachable. Maintain current server configuration.",
                    "confidence": 1.0,
                    "category": "reachability",
                    "http_status": status,
                    "response_time_ms": ttfb_ms,
                    "checked_url": current_url
                })

            if ttfb_ms > 2000:
                findings.append({
                    "id": f"f-ttfb-{int(time.time()*1000)}",
                    "title": "Slow Time to First Byte (TTFB > 2.0s)",
                    "severity": "medium",
                    "check_status": "WARNING",
                    "observed": f"The initial server response took {ttfb_ms} ms to begin sending bytes.",
                    "evidence": f"TTFB: {ttfb_ms} ms (Recommended threshold: < 800 ms)",
                    "why_it_matters": "High latency before first byte triggers high bounce rates and penalizes Google Search ranking.",
                    "recommended_action": "Deploy edge caching or CDN (e.g. Cloudflare) and optimize backend database queries.",
                    "confidence": 0.95,
                    "category": "performance",
                    "response_time_ms": ttfb_ms,
                    "checked_url": current_url
                })

            return {
                "status_code": status,
                "final_url": current_url,
                "ttfb_ms": ttfb_ms,
                "headers": resp_headers,
                "body": body_content,
                "findings": findings
            }

        return {
            "status_code": 0,
            "final_url": current_url,
            "ttfb_ms": ttfb_ms,
            "headers": {},
            "body": "",
            "findings": findings
        }

    def _inspect_html(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Inspects HTML DOM for title, viewport, meta description, and internal critical links."""
        findings = []
        soup = BeautifulSoup(html, "html.parser")

        # 1. Viewport check
        viewport = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "viewport"})
        if not viewport:
            findings.append({
                "id": f"f-html-vp-{int(time.time()*1000)}",
                "title": "Missing mobile viewport meta declaration",
                "severity": "medium",
                "check_status": "FAIL",
                "observed": "The HTML document <head> does not contain a standard responsive <meta name='viewport'> tag.",
                "evidence": "<!-- HTML Document Head -->\nMissing: <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
                "why_it_matters": "Mobile browsers default to standard desktop scaling (980px), making fonts and buttons tiny on smartphones.",
                "recommended_action": "Add '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">' to the document header.",
                "confidence": 1.0,
                "category": "performance",
                "checked_url": url
            })
        else:
            findings.append({
                "id": f"f-html-vp-pass-{int(time.time()*1000)}",
                "title": "Mobile viewport meta declaration verified",
                "severity": "info",
                "check_status": "PASS",
                "observed": f"Responsive viewport tag verified: {viewport.get('content', '')}.",
                "evidence": f"<meta name=\"viewport\" content=\"{viewport.get('content', '')}\">",
                "why_it_matters": "Ensures document renders responsively across mobile, tablet, and desktop viewports.",
                "recommended_action": "Responsive viewport is correctly configured.",
                "confidence": 1.0,
                "category": "performance",
                "checked_url": url
            })

        # 2. Page Title Check
        title_tag = soup.find("title")
        title_text = title_tag.get_text().strip() if title_tag else ""
        if not title_text:
            findings.append({
                "id": f"f-html-title-{int(time.time()*1000)}",
                "title": "Missing or empty HTML page title tag",
                "severity": "medium",
                "check_status": "FAIL",
                "observed": "The HTML document has no <title> element or the title tag is completely blank.",
                "evidence": "<title></title> [Empty or Not Found]",
                "why_it_matters": "Title tags are the single most important on-page SEO signal and define the bookmark/tab title in browsers.",
                "recommended_action": "Define a descriptive page title between 30 and 60 characters.",
                "confidence": 1.0,
                "category": "seo_meta",
                "checked_url": url
            })
        else:
            findings.append({
                "id": f"f-html-title-pass-{int(time.time()*1000)}",
                "title": "HTML page title verified",
                "severity": "info",
                "check_status": "PASS",
                "observed": f"Page title tag present: '{title_text[:60]}'.",
                "evidence": f"<title>{title_text}</title>\nLength: {len(title_text)} characters",
                "why_it_matters": "Provides search engine crawlers and browser tabs with descriptive page identity.",
                "recommended_action": "Title tag is properly defined.",
                "confidence": 1.0,
                "category": "seo_meta",
                "checked_url": url
            })

        # 3. Meta Description Check
        desc = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "description"})
        desc_content = desc.get("content", "").strip() if desc else ""
        if not desc_content:
            findings.append({
                "id": f"f-html-desc-{int(time.time()*1000)}",
                "title": "Missing meta description for search snippets",
                "severity": "low",
                "check_status": "WARNING",
                "observed": "No <meta name='description'> tag discovered in document head.",
                "evidence": "Meta description tag: [NOT FOUND]",
                "why_it_matters": "Search engines will auto-generate arbitrary snippet text instead of curated commercial messaging.",
                "recommended_action": "Add an informative 120-160 character meta description summarizing your value proposition.",
                "confidence": 0.95,
                "category": "seo_meta",
                "checked_url": url
            })
        else:
            findings.append({
                "id": f"f-html-desc-pass-{int(time.time()*1000)}",
                "title": "Meta description tag verified",
                "severity": "info",
                "check_status": "PASS",
                "observed": f"Discovered curated meta description ({len(desc_content)} characters).",
                "evidence": f"<meta name=\"description\" content=\"{desc_content[:80]}...\">",
                "why_it_matters": "Curated search snippet improves click-through rate from search result pages.",
                "recommended_action": "Meta description is active.",
                "confidence": 1.0,
                "category": "seo_meta",
                "checked_url": url
            })

        # 4. Critical internal route inspection (e.g. contact link)
        all_links = soup.find_all("a", href=True)
        contact_links = [
            a["href"] for a in all_links
            if any(term in a["href"].lower() for term in ["contact", "inquiry", "reach-us", "get-in-touch"])
        ]
        
        if not contact_links and len(all_links) > 3:
            findings.append({
                "id": f"f-html-nocontact-{int(time.time()*1000)}",
                "title": "No contact or inquiry link detected in navigation",
                "severity": "low",
                "check_status": "WARNING",
                "observed": f"Out of {len(all_links)} internal links, none reference a contact or inquiry page.",
                "evidence": f"Total document links evaluated: {len(all_links)}\nContact link candidates: 0",
                "why_it_matters": "Prospective clients finding the portfolio or service page have no clear call-to-action path to get in touch.",
                "recommended_action": "Add a prominent 'Contact Us' or inquiry button to the main navigation menu.",
                "confidence": 0.9,
                "category": "conversion",
                "checked_url": url
            })
        elif contact_links:
            findings.append({
                "id": f"f-html-contact-pass-{int(time.time()*1000)}",
                "title": "Internal contact pathway detected",
                "severity": "info",
                "check_status": "PASS",
                "observed": f"Found {len(contact_links)} contact/inquiry navigation link(s).",
                "evidence": f"Contact routes: {', '.join(contact_links[:2])}",
                "why_it_matters": "Enables site visitors to initiate inquiries and convert to sales leads.",
                "recommended_action": "Lead capture pathways are active.",
                "confidence": 1.0,
                "category": "conversion",
                "checked_url": url
            })

        return findings

audit_engine = AuditEngine()
execute_audit = audit_engine.execute_audit
