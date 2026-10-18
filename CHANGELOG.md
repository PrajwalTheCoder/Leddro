# Changelog

All notable changes to **Leddro** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
