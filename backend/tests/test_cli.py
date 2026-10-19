import sys
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.app.cli import run_audit_command, main, format_score_badge, format_severity

@pytest.mark.asyncio
async def test_run_audit_command_human_readable(capsys):
    mock_result = {
        "url": "https://test-business.example.com",
        "timestamp": "2026-10-19 12:00:00 UTC",
        "status": "completed",
        "overall_score": 82,
        "raw_dns": {"aRecord": "192.0.2.1", "mxRecord": "mail.example.com", "responseMs": 45},
        "raw_ssl": {"valid": True, "tlsVersion": "TLSv1.3", "expiresDays": 12, "issuer": "Let's Encrypt"},
        "performance": {"ttfbMs": 240, "domReadyMs": 450, "pageSizeKb": 12.5, "mobileViewportPresent": True},
        "contacts": {"emails": ["info@test-business.example.com"], "phones": ["+1 555-0199"]},
        "findings": [
            {
                "severity": "high",
                "title": "SSL Certificate Expiry Imminent",
                "observed": "Certificate expires in 12 days.",
                "recommended_action": "Renew TLS certificate immediately."
            }
        ]
    }

    with patch("backend.app.cli.AuditEngine.execute_audit", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_result
        exit_code = await run_audit_command("https://test-business.example.com", as_json=False, no_color=True)

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "LEDDRO WEBSITE AUDIT REPORT" in captured.out
    assert "https://test-business.example.com" in captured.out
    assert "82/100 (High Opportunity)" in captured.out
    assert "info@test-business.example.com" in captured.out
    assert "+1 555-0199" in captured.out
    assert "[CRITICAL] SSL Certificate Expiry Imminent" in captured.out

@pytest.mark.asyncio
async def test_run_audit_command_json_output(capsys):
    mock_result = {
        "url": "https://test-business.example.com",
        "status": "completed",
        "overall_score": 60,
        "findings": []
    }

    with patch("backend.app.cli.AuditEngine.execute_audit", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_result
        exit_code = await run_audit_command("https://test-business.example.com", as_json=True)

    assert exit_code == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["url"] == "https://test-business.example.com"
    assert parsed["overall_score"] == 60

def test_cli_version_flag(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["backend.app.cli", "version"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Leddro Website Audit" in captured.out

def test_format_helpers():
    assert "85/100" in format_score_badge(85, no_color=True)
    assert "60/100" in format_score_badge(60, no_color=True)
    assert "30/100" in format_score_badge(30, no_color=True)
    assert format_severity("high", no_color=True) == "[CRITICAL]"
    assert format_severity("medium", no_color=True) == "[WARNING]"
    assert format_severity("low", no_color=True) == "[LOW]"
    assert format_severity("info", no_color=True) == "[INFO]"
