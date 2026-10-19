# Changelog

All notable changes to **Leddro** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-10-19 - Phase 8: Prospect Intelligence, Audit Comparison & Release Hardening

### Added
- **Explainable Prospect Opportunity Scoring (Phase 8.2)**: Deterministic, pure calculation engine (`prospect_scoring.py`) separating opportunity score [0-100], data confidence score [0-100], contact readiness, and audit recency decay. Interactive explanation modal (`ProspectScoringModal.tsx`) with transparent factor breakdowns and traceable evidence.
- **Website Audit Comparison & Change Detection (Phase 8.3 & 8.3.1)**: Deterministic comparison engine (`audit_comparison.py`) classifying website findings into `RESOLVED`, `NEW`, `PERSISTENT`, or `INCONCLUSIVE` states without external AI dependencies. Interactive comparison workspace (`AuditComparisonModal.tsx`) with telemetry delta metrics and cross-domain protection.
- **Direct Gmail SMTP & App Password Gateway (Phase 8.5)**: Instant email dispatch with zero Google Cloud Console configuration using standard TLS and 16-character Google App Passwords. Includes backend connection testing and status reporting.
- **Uncertain Delivery State & Retry Protection**: Network timeouts during dispatch now durably mark send attempts as `uncertain` instead of failed, blocking duplicate retries and safeguarding client relationships.
- **Database Reliability & Cascade Safeguards (Phase 8.4)**: Enforced SQLite `PRAGMA foreign_keys=ON` on all connections. Clean prospect deletion logic nulls associated audit report references (preserving audit history) and disassociates email history while cascading draft deletion.
- **CSV Intra-Batch Deduplication**: Extended CSV preview and commit pipelines to reject duplicates within the same batch while preserving multi-location records across generic hosts.
- **Unified Dev Launcher (`run_dev.py`)**: One-command development runner (`npm run dev:all`) that checks port conflicts, auto-detects virtual environments, multiplexes color-coded logs, and ensures graceful termination of both FastAPI and Vite.

### Security & Hardening
- **Header Injection Defense at API Boundary**: Unified recipient, subject, and body validation at the top of the dispatch handler to strictly reject CRLF (`\r`, `\n`) and null bytes prior to account or draft evaluation.
- **Atomic File Persistence**: Replaced direct `.env` updates with temporary file writing and atomic `os.replace` to prevent corrupted environment configuration.
- **Clean-Install Independence**: Verified that the entire backend test suite (190 tests) and production build succeed in a fresh environment without pre-configured secrets or third-party accounts.

---

## [1.0.0] - 2026-10-18 - Phase 7: Production Readiness & Open-Source Release

### Added
- **Neon Serverless PostgreSQL Support**: Native connection pooling, auto-scaling support, and dynamic schema migration compatibility across both SQLite and PostgreSQL.
- **Database Backup & Recovery Engine**: Atomic, SQLite-safe online backup (`sqlite3_backup`), pre-restore PRAGMA integrity verification, and pre-restore rollback safety snapshots.
- **Automated Backup & Recovery Test Suite**: Validates database backup creation, verification, corruption simulation, and recovery.
- **Google Gemini Provider & Fast Models**: Added native Gemini integration with `gemini-3.5-flash-lite`, sub-second draft generation, and dynamic model discovery.
- **Interactive Provider Configuration**: Inline key management UI with password visibility toggles and real-time backend persistence.
- **GitHub Actions CI Workflow**: Multi-job automated pipeline running backend pytest tests, frontend TypeScript validation, Vite production build, and security scans.
- **Open-Source Documentation Suite**: Comprehensive `README.md`, `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md`, and sanitized `.env.example`.

### Security & Hardening
- **Safe Secret Scanning**: Scanned all codebase files, logs, and Git tracking to ensure zero credentials are tracked.
- **Rigid .gitignore Rules**: Enforced pattern rules preventing any `.env`, `.env.*`, `*.db`, certificates, or private keys from entering version control.
- **Sanitized Error Disclosures**: Replaced raw exception strings in API health endpoints and global exception handlers to prevent credential exposure in logs or responses.
- **SSRF Validation**: Preserved strict RFC 1918 private network and loopback blocks for website audit crawling.

---

## [0.6.0] - Phase 6: Gmail Integration & Dispatch Safeguards
- Google OAuth 2.0 integration with PKCE and token encryption.
- Explicit human approval required before sending; approval and dispatch strictly separated.
- Suppression list enforcement and duplicate-send safeguards.
- Provider message ID tracking and durable audit history.

---

## [0.5.0] - Phase 5: Evidence-Aware AI Drafting
- Multi-provider AI drafting: Gemini, OpenAI, Anthropic, and local Ollama models.
- Evidence-linked rationale mapping audit findings directly to email sentences.
- Tone and purpose customization.

---

## [0.4.0] - Phase 4: Prospect Discovery & Enrichment
- OpenStreetMap Overpass API and Nominatim integration for local business discovery.
- CSV import with schema validation and prospect deduplication.

---

## [0.3.0] - Phase 3: Core UI & Design System
- Dark charcoal surfaces, restrained lime accents, compact typography.
- Dashboard, Prospects table, Website Audit viewer, and Drafts manager.

---

## [0.2.0] - Phase 2: High-Precision Audit Engine
- Technical audit checks: SSL expiry, DNS configuration, HTTP performance, broken links, OpenGraph metadata.
- SSRF and loopback network protections.

---

## [0.1.0] - Phase 1: Core Architecture
- Initial FastAPI backend with SQLAlchemy ORM and SQLite.
- Vite + React + TypeScript frontend foundation.
