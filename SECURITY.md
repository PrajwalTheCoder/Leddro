# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

We take the security of Leddro seriously. If you believe you have discovered a vulnerability, please report it responsibly:

1. **Email**: Send detailed information to the project maintainer or open a confidential advisory on GitHub.
2. **Details to include**:
   - Severity and type of vulnerability (e.g., SSRF, credential leakage, SQL injection)
   - Step-by-step reproduction instructions or proof-of-concept
   - Potential impact
3. **Response Timeline**:
   - Initial acknowledgement: within 48 hours
   - Patch release: prioritized based on severity

Please do **NOT** submit public GitHub issues for undisclosed security vulnerabilities.

---

## Security Architecture & Best Practices

Leddro follows a strict local-first, privacy-conscious security architecture:

### 1. API Key & Credential Management
- **Never committed to version control**: All `.env` and credential files are strictly ignored by `.gitignore`.
- **Masked in responses**: Backend endpoints never return unmasked API keys or OAuth secrets.
- **Redacted in logs**: Log handlers and error handlers strip or mask sensitive tokens.
- **No client-side exposure**: API keys are never bundled into the Vite frontend JavaScript artifact.

### 2. Website Auditing & SSRF Protections
- **Network Boundaries**: Outbound audit crawlers prohibit connections to loopback (`127.0.0.1`), private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud metadata IP addresses (`169.254.169.254`).
- **Redirect Validation**: Every HTTP redirect is validated prior to fetching.
- **Resource Constraints**: Network requests enforce strict 10-second timeouts and response payload limits.

### 3. Email Dispatch Safeguards
- **Explicit Human Approval**: No email is ever sent automatically. Approving a draft does not send it. Sending requires explicit user confirmation.
- **Suppression Enforcement**: All recipient addresses are checked against the suppression database prior to dispatch.
- **Durable Audit Trail**: Every dispatch attempt records provider message IDs and timestamps.

### 4. Database & Backups
- SQLite backups utilize the atomic `sqlite3_backup` online backup API to prevent corruption during active writes.
- Backup integrity is validated using `PRAGMA integrity_check` before any restore operation.
