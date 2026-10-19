"""
Leddro Command Line Interface (CLI)
Allows operators and developers to perform individual website diagnostic audits,
extract telemetry and verified contacts, and inspect technical deficits directly
from the terminal without launching the full web UI.

Usage:
  python -m backend.app.cli audit https://example.com
  python -m backend.app.cli audit https://example.com --json
  python -m backend.app.cli version
"""

import sys
import json
import asyncio
import argparse
from typing import Dict, Any, List

# Ensure utf-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.app.core.config import settings
from backend.app.services.audit_engine import AuditEngine

# ANSI color codes with automatic fallback
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"

def format_score_badge(score: int, no_color: bool = False) -> str:
    if score >= 75:
        label = "High Opportunity"
        color = Style.RED
    elif score >= 50:
        label = "Moderate Opportunity"
        color = Style.YELLOW
    else:
        label = "Low Opportunity"
        color = Style.GREEN

    if no_color:
        return f"{score}/100 ({label})"
    return f"{color}{Style.BOLD}{score}/100 ({label}){Style.RESET}"

def format_severity(severity: str, no_color: bool = False) -> str:
    s = severity.lower()
    if s in ("high", "critical"):
        label = "CRITICAL"
        color = Style.RED
    elif s in ("medium", "warning"):
        label = "WARNING"
        color = Style.YELLOW
    elif s == "low":
        label = "LOW"
        color = Style.BLUE
    else:
        label = "INFO"
        color = Style.DIM

    if no_color:
        return f"[{label}]"
    return f"{color}{Style.BOLD}[{label}]{Style.RESET}"

def print_audit_report(result: Dict[str, Any], no_color: bool = False) -> None:
    c = not no_color
    cyan = Style.CYAN if c else ""
    bold = Style.BOLD if c else ""
    reset = Style.RESET if c else ""
    dim = Style.DIM if c else ""
    green = Style.GREEN if c else ""
    yellow = Style.YELLOW if c else ""
    red = Style.RED if c else ""

    print()
    print(f"{cyan}{bold}======================================================================{reset}")
    print(f"{cyan}{bold}  LEDDRO WEBSITE AUDIT REPORT & PROSPECT INTELLIGENCE{reset}")
    print(f"{cyan}{bold}======================================================================{reset}")
    print(f"  {bold}Target URL:{reset}       {result.get('url')}")
    print(f"  {bold}Audit Timestamp:{reset}  {result.get('timestamp')}")
    print(f"  {bold}Audit Status:{reset}     {green if result.get('status') == 'completed' else red}{result.get('status', '').upper()}{reset}")
    print(f"  {bold}Opportunity Score:{reset} {format_score_badge(result.get('overall_score', 0), no_color)}")
    print()

    # Telemetry Section
    dns = result.get("raw_dns", {})
    ssl_info = result.get("raw_ssl", {})
    perf = result.get("performance", {})

    print(f"{bold}--- TECHNICAL TELEMETRY ---{reset}")
    a_rec = dns.get("aRecord", "N/A")
    mx_rec = dns.get("mxRecord", "N/A")
    dns_time = dns.get("responseMs", 0)
    print(f"  * DNS Resolution:   A: {a_rec} | MX: {mx_rec} ({dns_time} ms)")

    tls_valid = ssl_info.get("valid", False)
    tls_ver = ssl_info.get("tlsVersion", "N/A")
    tls_exp = ssl_info.get("expiresDays", 0)
    tls_status_str = f"{green}Valid{reset} ({tls_exp} days remaining)" if tls_valid else f"{red}Invalid / Expired{reset}"
    print(f"  * TLS / SSL:        {tls_status_str} | Protocol: {tls_ver} | Issuer: {ssl_info.get('issuer', 'N/A')}")

    ttfb = perf.get("ttfbMs", 0)
    dom_ms = perf.get("domReadyMs", 0)
    size_kb = perf.get("pageSizeKb", 0)
    viewport = perf.get("mobileViewportPresent", False)
    vp_str = f"{green}Present{reset}" if viewport else f"{red}MISSING (Not Mobile Responsive){reset}"
    print(f"  * HTTP Latency:     TTFB: {ttfb} ms | DOM Ready: {dom_ms} ms | Payload: {size_kb} KB")
    print(f"  * Mobile Viewport:  {vp_str}")
    print()

    # Discovered Contacts
    contacts = result.get("contacts", {})
    emails: List[str] = contacts.get("emails", [])
    phones: List[str] = contacts.get("phones", [])
    
    print(f"{bold}--- DISCOVERED CONTACT INTELLIGENCE ---{reset}")
    if emails:
        print(f"  * Verified Email(s): {green}{', '.join(emails)}{reset} (DNS MX Active)")
    else:
        print(f"  * Email(s):          {yellow}None discovered on website (Zero Fake Emails Policy applies){reset}")

    if phones:
        print(f"  * Telephone(s):      {green}{', '.join(phones)}{reset}")
    else:
        print(f"  * Telephone(s):      {dim}None detected in DOM{reset}")
    print()

    # Classified Findings
    findings: List[Dict[str, Any]] = result.get("findings", [])
    print(f"{bold}--- AUDIT FINDINGS ({len(findings)} Total) ---{reset}")
    if not findings:
        print(f"  {green}No significant technical deficits detected.{reset}")
    else:
        for idx, f in enumerate(findings, 1):
            sev_badge = format_severity(f.get("severity", "info"), no_color)
            title = f.get("title", "Untitled finding")
            observed = f.get("observed", "")
            action = f.get("recommended_action", "")

            print(f"  {idx}. {sev_badge} {bold}{title}{reset}")
            if observed:
                print(f"     {dim}Observed:{reset} {observed}")
            if action:
                print(f"     {cyan}Remedy:{reset}   {action}")
            print()

    print(f"{cyan}======================================================================{reset}")
    print()

async def run_audit_command(url: str, as_json: bool = False, no_color: bool = False) -> int:
    engine = AuditEngine()
    result = await engine.execute_audit(url)

    if as_json:
        print(json.dumps(result, indent=2))
        return 0

    print_audit_report(result, no_color=no_color)
    return 0

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m backend.app.cli",
        description="Leddro CLI — Terminal Diagnostic Website Audits and Prospect Intelligence"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Audit subcommand
    audit_parser = subparsers.add_parser("audit", help="Run a non-destructive diagnostic audit on a target website")
    audit_parser.add_argument("url", type=str, help="Target URL or domain (e.g., https://example.com)")
    audit_parser.add_argument("--json", action="store_true", help="Output raw JSON instead of human-readable report")
    audit_parser.add_argument("--no-color", action="store_true", help="Disable ANSI color output in terminal")

    # Version subcommand
    subparsers.add_parser("version", help="Print application version")

    args = parser.parse_args()

    if args.subcommand == "audit":
        exit_code = asyncio.run(run_audit_command(args.url, as_json=args.json, no_color=args.no_color))
        sys.exit(exit_code)
    elif args.subcommand == "version":
        print(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
