# Leddro

> **Discover prospects. Audit websites. Understand opportunities. Prepare evidence-based outreach.**

[![MIT License](https://img.shields.io/github/license/PrajwalTheCoder/Leddro?style=flat&color=10b981)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-339933.svg?logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/Frontend-React%2019-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20%28Default%29-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![CI](https://github.com/PrajwalTheCoder/Leddro/actions/workflows/ci.yml/badge.svg)](https://github.com/PrajwalTheCoder/Leddro/actions/workflows/ci.yml)
[![GitHub Stars](https://img.shields.io/github/stars/PrajwalTheCoder/Leddro?style=flat&color=f59e0b)](https://github.com/PrajwalTheCoder/Leddro/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/PrajwalTheCoder/Leddro?style=flat&color=6366f1)](https://github.com/PrajwalTheCoder/Leddro/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/PrajwalTheCoder/Leddro?style=flat&color=8b5cf6)](https://github.com/PrajwalTheCoder/Leddro/pulls)

**Leddro** is an open-source, local-first prospect intelligence and website auditing workspace designed for web developers, digital freelancers, and technical agencies.

Instead of relying on generic mass-scraped email blasts and hallucinated AI flattery, Leddro anchors your outreach directly to **deterministic technical evidence**—such as expired TLS/SSL certificates, DNS misconfigurations, slow server response times (TTFB), broken headers, or missing mobile viewport declarations.

[Features](#features) • [Screenshots](#screenshots-and-interface-tour) • [Quick Start](#installation-quick-start) • [Architecture](#project-architecture) • [Testing](#testing-and-development) • [Contributing](#contributing) • [Security](#security-disclosures)

---

## Table of Contents

- [What Is Leddro?](#what-is-leddro)
- [Workflow Overview](#workflow-overview)
- [Why Leddro?](#why-leddro)
- [Features](#features)
- [Prospect Intelligence and Explainable Scoring](#prospect-intelligence-and-explainable-scoring)
- [Website Auditing and Telemetry](#website-auditing-and-telemetry)
- [Website Audit Comparison and Change Detection](#website-audit-comparison-and-change-detection)
- [Contact Intelligence and Email Discovery](#contact-intelligence-and-email-discovery)
- [Evidence-Aware AI Drafting](#evidence-aware-ai-drafting)
- [Email Integration and Safe Dispatch](#email-integration-and-safe-dispatch)
- [Data Safety and Infrastructure](#data-safety-and-infrastructure)
- [Screenshots and Interface Tour](#screenshots-and-interface-tour)
- [System Requirements](#system-requirements)
- [Installation: Quick Start](#installation-quick-start)
- [Running the Application](#running-the-application)
- [First-Run Experience](#first-run-experience)
- [Using Leddro Without AI](#using-leddro-without-ai)
- [Configuring AI Providers](#configuring-ai-providers)
- [Contact Discovery Provider Setup](#contact-discovery-provider-setup)
- [Email Integration Setup](#email-integration-setup)
- [Configuration Reference](#configuration-reference)
- [Database and Data Storage](#database-and-data-storage)
- [Backup and Recovery](#backup-and-recovery)
- [Privacy, Security, and Responsible Use](#privacy-security-and-responsible-use)
- [Troubleshooting](#troubleshooting)
- [Updating Leddro](#updating-leddro)
- [Testing and Development](#testing-and-development)
- [Project Architecture](#project-architecture)
- [Directory Structure](#directory-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security Disclosures](#security-disclosures)
- [License and Acknowledgements](#license-and-acknowledgements)

---

## What Is Leddro?

Independent developers and digital consultants often struggle with client acquisition. Traditional sales automation tools treat outreach as a volume game: they scrape thousands of unverified email addresses and blast generic templates that damage sender reputation and yield near-zero response rates.

Leddro provides an evidence-based alternative:

1. **Local Business Discovery**: Find commercial businesses in any geographical region via OpenStreetMap or structured CSV imports without recurring data fees.
2. **Deep Technical Diagnostics**: Audit prospect websites with non-destructive server-side probes checking DNS zones, TLS certificates, HTTP response latency, and DOM structure.
3. **Transparent Opportunity Scoring**: Prioritize prospects using an explainable 0–100 heuristic based entirely on observable technical defects and data confidence.
4. **Verified Contact Intelligence**: Autonomously discover authentic contact details directly from websites, check domain MX mail exchangers, and integrate B2B directory lookups (Hunter.io, Google Places) with a strict **Zero Fake Emails** policy.
5. **Evidence-Grounded AI Synthesis**: Generate factual, respectful consultation proposals where every technical assertion is linked to stored audit evidence, preventing AI hallucinations.
6. **Controlled Single-Message Dispatch**: Review, customize, and dispatch personalized emails individually via Gmail SMTP or Google Cloud OAuth with strict suppression enforcement and zero bulk automation.

---

## Workflow Overview

Leddro integrates discovery, diagnostics, contact extraction, and outreach into a unified, operator-supervised pipeline:

```mermaid
flowchart LR
    A["1. Discovery<br>(OSM / CSV / Places)"] --> B["2. Diagnostic Audit<br>(DNS / TLS / HTTP / DOM)"]
    B --> C["3. Scoring Engine<br>(Opportunity & Confidence)"]
    C --> D["4. Contact Crawler<br>(MX Verified & Phone/WA)"]
    D --> E["5. Evidence AI Draft<br>(Gemini / Ollama / Claude)"]
    E --> F["6. Human Review<br>& Safe Dispatch (SMTP / Gmail)"]
```

### The 6-Stage Operator Lifecycle

1. **Discover & Ingest**: Query local businesses via OpenStreetMap (Overpass & Nominatim), search via Google Places API, or import CSV lead files. Leddro applies domain and phone normalization with deduplication.
2. **Execute Diagnostic Audits**: Run server-side probes against target domains. Leddro inspects DNS records (A, AAAA, MX, NS), TLS certificate chains, HTTP status codes, socket TTFB latency, and DOM elements (mobile viewport, meta descriptions).
3. **Evaluate Opportunities**: Review the deterministic **Opportunity Score** (0–100) and decoupled **Data Confidence Score** (0–100) with complete evidence traceability.
4. **Extract Verified Contacts**: The crawler scans the homepage and contact subpages for authentic public emails and phone numbers, validating active DNS MX mail records before saving. When no email exists, Leddro provides direct click-to-call and WhatsApp actions.
5. **Draft Fact-Checked Proposals**: Select an AI provider (Google Gemini free tier, local Ollama, OpenAI, or Anthropic). Leddro generates proposals citing authentic audit finding IDs and flags any ungrounded assertions.
6. **Review & Dispatch Safely**: Polish subject lines and copy in the split-pane Draft Studio. Dispatch individually through your preferred Gmail SMTP or Google Cloud OAuth gateway.

---

## Why Leddro?

| Dimension | Conventional Outreach Platforms | Leddro Developer Workspace |
| :--- | :--- | :--- |
| **Data Architecture** | Closed SaaS database; vendor controls your data | **Local-First SQLite**; complete ownership on your machine |
| **Outreach Grounding** | Vague flattery (*"I loved your website..."*) | **Deterministic Evidence** (*"Your SSL certificate expires in 4 days..."*) |
| **Contact Integrity** | Fabricates guessed emails (`contact@company.com`) | **Zero Fake Emails Policy**; MX checks and direct Phone/WhatsApp actions |
| **Email Dispatch** | Automated sequence blasts and cold drip campaigns | **Strictly Single-Message Dispatch**; operator review required for every email |
| **AI Transparency** | Black-box prompts with unchecked hallucinations | **Factual Claim Mapping**; assertions verified against audit finding IDs |
| **Cost & Licensing** | $80–$300/month subscription lock-in | **100% Free & Open Source (MIT)**; runs with free-tier APIs or offline LLMs |
| **Network Security** | Unrestricted external crawling | **Hardened SSRF Defenses**; blocks loopback, private subnets, and metadata IPs |

---

## Features

### 🔍 Prospect Discovery
- **OpenStreetMap Integration**: Query local businesses by city, state, or postal code via Overpass API and Nominatim geocoding with zero API keys required.
- **CSV Batch Import**: Ingest existing lead lists with automatic column detection, duplicate identification, and formula injection protection (`=`, `+`, `-`, `@`).
- **Google Places API (New)**: Optional integration for high-accuracy business lookups, official websites, and phone numbers using Google Cloud's $200 free monthly credit.
- **Deterministic Deduplication**: Cross-references source provider IDs, canonical registered web domains (`extract_registered_domain`), and normalized business names + locality to prevent duplicate records.

### 🛡️ Diagnostic Website Auditing
- **DNS Zone Analysis**: Queries A, AAAA, MX, and NS records with millisecond resolution timing.
- **TLS / SSL Verification**: Inspects certificate authorities, validity dates, protocol support (TLSv1.2, TLSv1.3), and cipher configurations.
- **HTTP & Server Telemetry**: Evaluates socket connection latency, Time To First Byte (TTFB), HTTP status codes (200, 301, 404, 500), and security response headers.
- **DOM & Mobile Evaluation**: Checks for mobile responsive `<meta name="viewport">` tags, document `<title>`, meta descriptions, and OpenGraph social cards.
- **SSRF Network Security**: Outbound crawler strictly blocks loopback addresses (`127.0.0.0/8`), RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud instance metadata endpoints (`169.254.169.254`).

### 📊 Explainable Opportunity & Confidence Scoring
- **Heuristic Opportunity Score (0–100)**: Transparent point-based assessment of observable technical room for improvement across 4 decoupled dimensions.
- **Data Confidence Score (0–100)**: Reflects audit completeness and recency, applying deterministic decay penalties for stale data (>30 days: -15 pts; >90 days: -30 pts).
- **Diagnostic Failure Isolation**: Network timeouts and runner errors are classified as `failed_diagnostic` and reduce confidence rather than penalizing the prospect's score.
- **Full Evidence Traceability**: Every score links directly to stored audit finding IDs and raw network telemetry dumps.

### 🔄 Audit Comparison & Change Detection
- **Before/After Analysis**: Compare older and newer audits for the same website to monitor remediation or regressions.
- **Positive-Evidence Rule**: Issues are only classified as resolved if the newer audit provides positive evidence that the check passed.
- **Four-Way Classification**: Categorizes findings into `RESOLVED`, `NEW`, `PERSISTENT`, or `INCONCLUSIVE`.
- **Telemetry Deltas**: Directional deltas for TTFB latency (ms and %), DOM ready latency, payload size (KB), responsive viewport state, and TLS protocol upgrades.

### 📬 Contact Intelligence & Verification
- **Autonomous Contact Crawler**: Scans the homepage and contact subpages (`/contact`, `/about`, `/reach-us`, `/location`) for public emails and phone numbers.
- **DNS MX Mailbox Verification**: Validates that discovered email domains maintain active, responsive mail exchange records before saving.
- **Zero Fake Emails Policy**: Never fabricates placeholder email addresses. If no email is discovered, the address remains empty with clear visual warnings.
- **Direct Phone & WhatsApp Actions**: Click-to-call (`tel:`) and 1-click WhatsApp web chat (`https://wa.me/`) with pre-filled technical audit outreach messages.
- **Hunter.io B2B Email Finder**: Search verified professional emails, executive names, positions, and confidence scores (25 free monthly searches).
- **Quick-Fill Email Pills**: 1-click `+ info@{domain}` and `+ contact@{domain}` pills in the draft editor when the operator knows the address.

### ✍️ Evidence-Aware AI Outreach Drafting
- **Multi-Provider Architecture**: Toggle between Google Gemini (Free tier via Google AI Studio), OpenAI (`gpt-4o-mini`), Anthropic Claude (`claude-3-5-haiku-20241022`), or local Ollama (`llama3`).
- **In-Modal Provider Switcher**: Change AI engines directly inside the draft generation dialog without navigating away.
- **Factual Claim Mapping**: Automatically parses generated drafts, cross-references technical assertions with stored audit finding IDs, and flags unverified claims.
- **Prompt Injection Containment**: Crawled page content and untrusted business metadata are encapsulated within strict `<untrusted_prospect_data>` XML delimiters.
- **Operator Customization**: Select specific outreach purposes (Modernization, Performance, Security), adjust tone (Professional, Friendly, Concise, Consultative), and provide up to 500 characters of custom guidance.

### ✉️ Safe Email Dispatch
- **Direct Gmail SMTP (Preferred)**: Connect using a 16-character Google App Password with STARTTLS (`smtp.gmail.com:587`). Requires zero Google Cloud Console configuration.
- **Google Cloud OAuth 2.0**: Connect via Gmail REST API using Proof Key for Code Exchange (PKCE) and Fernet token encryption at rest (`.leddro_encryption_key`).
- **Human-Confirmed Single Sends**: Strict 1-by-1 sending requiring human confirmation. Zero bulk automation or background loops.
- **Header Injection Defenses**: Rejects carriage returns (`\r`), newlines (`\n`), and null bytes (`\0`) in recipient, sender, and subject headers.
- **Suppression Registry**: Automatically blocks dispatch to unsubscribed addresses or blacklisted domains.
- **Uncertain State Handling**: Network timeouts during dispatch mark attempts as `uncertain` to prevent accidental duplicate sending.

### 💾 Data Safety & Infrastructure
- **Local-First SQLite**: Zero setup required; all data persists in `leddro.db`.
- **Atomic Online Backups**: Native SQLite backup engine (`sqlite3_backup`) creates consistent snapshots without locking active database writes.
- **Integrity Validation**: Automated `PRAGMA integrity_check` before any backup restoration with automatic safety snapshots.
- **Optional Neon PostgreSQL**: Seamlessly connect to cloud serverless PostgreSQL simply by updating `DATABASE_URL`.

---

## Prospect Intelligence and Explainable Scoring

Leddro provides an explainable heuristic to rank prospects based on verified technical need. Every score is directly traceable to observed website issues and discovery metadata.

> [!NOTE]
> **What the Opportunity Score Means**: A transparent 0–100 heuristic ranking prospects based on observable technical deficiencies (such as DNS errors, server failures, missing HTTPS, or security headers). Higher scores indicate stronger technical room for improvement.
>
> **What It Does NOT Mean**: It does **NOT** predict whether a business will buy, convert, or reply. It is not an opaque machine learning probability score.

### Four Decoupled Dimensions

1. **Opportunity Score (0–100)**: Heuristic of technical need and room for improvement based on observed website evidence.
2. **Data Confidence (0–100)**: Measure of how complete, fresh, and reliable the diagnostic evidence is.
3. **Audit Severity**: Exact count of high, medium, low, and informational findings from real audit probes.
4. **Contact Readiness**: Verification state of communication channels (`verified`, `unverified`, `absent`, `unknown`).

### Scoring Factors and Weights (Sum: 100 Points)

| Factor | Max Pts | Contribution Rules |
| :--- | :---: | :--- |
| **1. Website Accessibility** | 25 pts | • DNS resolution failure (NXDOMAIN / missing A records): +25 pts<br>• Confirmed HTTP server error (4xx/5xx): +20 pts<br>• No website registered: +15 pts (opportunity for initial web presence)<br>• Confirmed reachable (HTTP 200/3xx): +0 pts<br>• Diagnostic error / timeout: +0 pts (marked inconclusive; lowers confidence) |
| **2. Technical Findings & Severity** | 55 pts | • High-severity findings: +15 pts each (capped at 35 pts)<br>• Medium-severity findings: +5 pts each (capped at 20 pts)<br>• Low-severity findings: +1 pt each (capped at 5 pts)<br>• Informational notices: +0 pts<br>• Duplicate findings sharing category and title are deduplicated automatically |
| **3. HTTPS & Transport Security** | 20 pts | • Invalid, expired, or untrusted certificate: +20 pts<br>• HTTP-only website with no HTTPS: +15 pts<br>• Valid TLS certificate (v1.2/v1.3): +0 pts<br>• Unchecked or diagnostic connection failure: +0 pts (marked unconfirmed) |
| **4. Contact Readiness & Completeness** | 0 pts | • Direct contact readiness is tracked separately and **never inflates Opportunity Score**.<br>• Unverified contact or incomplete profile details penalize Data Confidence (-8 to -15 pts) and populate explicit limitations. |

### Evidence Quality, Recency & Diagnostic Failures

- **Diagnostic Failures**: An audit that fails due to a network timeout or runner connection error is **never** penalized as a website defect. The factor is marked `check_failed` (nature: `failed_diagnostic`) and data confidence is reduced.
- **Audit Recency Decay**: Audits older than 30 days decay confidence (-15 pts), and audits older than 90 days decay confidence further (-30 pts). Stale audits do **not** artificially inflate opportunity score.
- **Contact Verification**: Contact addresses in the database are labeled `unverified` unless explicitly verified. Leddro does not perform unsolicited SMTP handshakes or test sends to verify contacts.
- **Traceability**: Every displayed evidence item links directly to an authentic stored audit finding ID and recorded HTTP/DNS evidence.

---

## Website Auditing and Telemetry

Leddro executes non-destructive diagnostic probes directly from your local machine.

```
[Target URL] ──► [SSRF Security Check] ──► [DNS Probe] ──► [TLS Handshake] ──► [HTTP / TTFB] ──► [DOM Parser]
```

### Audit Capabilities

- **DNS Zone Inspection**: Queries A, AAAA, MX, and NS records with millisecond resolution timing. Identifies missing records, zone misconfigurations, and mail host routing.
- **TLS / SSL Certificate Verification**: Connects via SSL socket to evaluate certificate authority trust, expiry countdown, protocol versions (TLSv1.2, TLSv1.3), and cipher suites.
- **HTTP Reachability & TTFB**: Measures socket connect latency, Time To First Byte (TTFB), status codes (200, 301, 404, 500), and response headers (`Strict-Transport-Security`, `X-Content-Type-Options`).
- **HTML DOM Diagnostics**: Parses the initial HTML payload to detect mobile viewport declarations (`<meta name="viewport">`), document `<title>`, meta descriptions, and OpenGraph social preview tags.
- **SSRF Network Security**: Outbound audit crawlers strictly block loopback (`127.0.0.1`), private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud metadata IP endpoints (`169.254.169.254`).

---

## Website Audit Comparison and Change Detection

Leddro includes a deterministic before/after comparison engine allowing operators to evaluate changes between two audits of the same website over time.

> [!IMPORTANT]
> **Resolution Rule**: A missing finding in a newer audit does **NOT** automatically mean an issue was fixed. Leddro requires explicit positive proof of a passing check to classify any issue as resolved.

### 1. The Four Finding Classifications

| Classification | Meaning | Rule & Evidence Requirement |
| :--- | :--- | :--- |
| **RESOLVED** | Issue confirmed fixed | A finding was confirmed in the older audit, and the newer audit provides positive evidence that the relevant check completed successfully and passed. |
| **NEW** | Newly detected issue | An issue was not present in the older audit, and the newer audit confirms a new defect with evidence. The older check must have run successfully or baseline evidence must be complete. |
| **PERSISTENT** | Issue confirmed in both | The same underlying defect is confirmed in both audits with ongoing evidence. |
| **INCONCLUSIVE** | Evidence insufficient | Evidence cannot establish whether an issue was fixed, appeared, or persisted. Occurs if the newer audit failed, timed out, skipped the check, or omitted the finding without pass evidence. |

### 2. Technical Telemetry Comparison

Leddro compares raw observations only when both sides contain valid, comparable values:
- **HTTP Response Latency (TTFB)**: Measures latency delta (ms) and percentage change without division-by-zero errors.
- **Document Processing Time**: Evaluates DOM ready and crawl latency changes.
- **HTML Document Payload Size**: Tracks document weight differences in KB.
- **Mobile Responsive Viewport**: Compares before/after presence of mobile viewport declarations.
- **DNS Resolution Time**: Evaluates DNS query latency deltas.
- **TLS Certificate Validity & Expiration**: Distinguishes valid, invalid, expired, and renewed certificates.
- **TLS Protocol Version**: Evaluates protocol version upgrades/downgrades categorically (TLSv1.3 > TLSv1.2 > TLSv1.1) rather than treating versions as continuous numbers.
- **HTTP Response Status**: Evaluates HTTP status transitions semantically (e.g., 500 → 200 is an improvement, not an arithmetic difference of -300).

### 3. Reliability and Execution Status
- **Both Completed**: Full comparison with high confidence across all completed checks.
- **Partial / Newer Failed**: Disappeared findings are retained as inconclusive rather than falsely declared resolved.
- **Cross-Website Guard**: Comparisons are strictly enforced against identical prospect records or canonical website domain identities (`extract_registered_domain`). Accidental comparisons across different websites are rejected.

---

## Contact Intelligence and Email Discovery

Finding legitimate decision-maker contact information is essential for ethical, effective outreach. Leddro provides an autonomous, multi-tiered contact discovery architecture:

```
[Target Website] ──► [SSRF Check] ──► [Page Scraper (/, /contact, /about)] ──► [Filter Junk] ──► [DNS MX Check] ──► [Verified Contacts]
                                                                                                          ▲
                                      [Hunter.io API (B2B Directory)] ─────────────────────────────────────┤
                                      [Google Places API (Phone & Web)] ───────────────────────────────────┘
```

### Autonomous Website Contact Crawler
- **Targeted Crawling**: Fetches the homepage and up to 2 high-probability contact subpages (e.g., `/contact`, `/contact-us`, `/about`, `/about-us`, `/location`) with SSRF validation.
- **Multi-Source Extraction**: Scans HTML `mailto:` anchors, click-to-call `tel:` links, body text regex patterns, and footer attributes.
- **Junk & Template Filtering**: Automatically filters out image file extensions (`.png`, `.svg`, `.jpg`), code assets (`.js`, `.css`), and placeholder domains (`example.com`, `sentry.io`, `wixpress.com`, `wordpress.org`).
- **DNS MX Mailbox Verification**: Performs live DNS lookups for MX mail exchangers (`dns.resolver.resolve(domain, "MX")`) to verify the domain is configured to receive incoming mail before saving.
- **Domain Affinity Ranking**: Prioritizes corporate domain emails (`info@business.com`) above generic webmail addresses.

### Zero Fake Emails Policy
- **Never Guesses**: Leddro **never** synthesizes fake emails like `contact@{domain}.com` or `admin@{domain}.com`. Fabricating unverified addresses damages sender domain reputation with Google and Microsoft mail filters.
- **Amber Warning State**: If no email address can be discovered, the recipient field remains empty and displays an amber alert:
  `⚠️ No verified email found — use phone or enter email manually.`
- **Quick-Fill Pills**: Provides convenient `+ info@{domain}` and `+ contact@{domain}` quick-fill pills in the draft editor when the operator knows the address.

### Direct Phone & WhatsApp Actions
- **Click-to-Call**: Extracted and normalized phone numbers render as clickable `📞 Call` links (`tel:+...`) for instant dialing via desktop softphones or paired mobile devices.
- **WhatsApp Web Integration**: Includes a 1-click `💬 WhatsApp` button linking to `https://wa.me/{phone}` with a pre-filled, professional technical audit summary ready to send.

### Third-Party Provider Enrichments
- **Hunter.io B2B Email Search**: Free tier provides 25 monthly searches for verified corporate emails, department tags, executive names, and deliverability confidence scores.
- **Google Places API (New)**: Enriches discovery with official business telephone numbers, formatted street addresses, and verified websites using Google Cloud's $200 free monthly credit.

---

## Evidence-Aware AI Drafting

Leddro turns dry technical audit data into polite, consultative business proposals.

### Multi-Provider Engine Architecture
Use any of 4 supported AI engines with zero code changes:
- **Google Gemini**: Recommended free tier via [Google AI Studio](https://aistudio.google.com/app/apikey) (`gemini-3.5-flash-lite`).
- **Local Ollama**: 100% private, on-device inference (`llama3`) with zero external network transmission.
- **OpenAI**: Commercial API integration (`gpt-4o-mini`).
- **Anthropic Claude**: Commercial API integration (`claude-3-5-haiku-20241022`).

### Anti-Hallucination Claim Validation
Unlike generic AI tools, Leddro prevents models from inventing false claims:
1. The AI engine is provided only verified findings from your local SQLite database.
2. The draft response is parsed to identify all technical claims.
3. Every claim is cross-referenced with stored audit finding IDs.
4. If a claim cannot be verified against stored evidence, Leddro marks it with an **Unverified Claim** warning badge in the Draft Studio.

### Prompt-Injection Containment
Untrusted crawled text, business descriptions, and OpenStreetMap tags are strictly sanitized and enclosed within `<untrusted_prospect_data>` XML boundaries in the prompt, preventing malicious websites from manipulating the AI output.

---

## Email Integration and Safe Dispatch

Leddro prioritizes sender reputation, deliverability, and human oversight.

### Two Supported Delivery Gateways

```
                          ┌──► [Option A: Direct SMTP Gateway] ────► smtp.gmail.com:587 (App Password)
[Draft Studio] ──► [Send] ┤
                          └──► [Option B: Google Cloud OAuth 2.0] ─► Gmail REST API (PKCE + Token Encryption)
```

1. **Direct SMTP Gateway (Preferred & Recommended)**: Connect directly to `smtp.gmail.com:587` with STARTTLS using a 16-character Google App Password. Instant setup with zero Google Cloud Console configuration.
2. **Google Cloud OAuth 2.0 (Gmail API Gateway)**: Authorize via Google Cloud OAuth with Proof Key for Code Exchange (PKCE) and CSRF verification. Refresh tokens are encrypted at rest using AES-128-CBC via Fernet (`.leddro_encryption_key`). Uses send-only scope (`gmail.send`) and never reads or indexes your inbox.

### Delivery Safeguards

- **Strictly Single-Message Dispatch**: Leddro has zero bulk-send sequences, no drip campaigns, and no automated dispatch triggers. Every send requires explicit human review and confirmation.
- **Header Injection Defenses**: Rejects any recipient, sender, or subject string containing carriage returns (`\r`), newlines (`\n`), or null bytes (`\0`).
- **Suppression Registry**: Automatically verifies target addresses against local `suppression_records` to prevent messaging unsubscribed contacts or blocked domains.
- **Uncertain State Handling**: If a network timeout occurs during dispatch, the attempt is marked `uncertain` with error code `SMTP_TIMEOUT` or `NETWORK_TIMEOUT`. Leddro prevents accidental re-sends and advises the operator to check their Sent folder.

---

## Data Safety and Infrastructure

Leddro is designed from the ground up as a local-first application.

- **Local-First SQLite**: All prospects, audit findings, draft emails, and history records persist automatically in `leddro.db` in the repository root.
- **Atomic Online Backups**: Leddro utilizes the native SQLite online backup API (`sqlite3_backup`) to create consistent snapshot backups without locking active writes.
- **Integrity Validation**: Automated `PRAGMA integrity_check` runs before any database restoration, accompanied by an automatic safety snapshot of the active database.
- **Optional Neon Serverless PostgreSQL**: Seamlessly transition to cloud auto-scaling serverless PostgreSQL simply by updating `DATABASE_URL`.

---

## Screenshots and Interface Tour

All screenshots below represent the live Leddro application interface:

### 1. Command Center & Tactical Radar Overview
Comprehensive mission dashboard featuring real-time health gauges, interactive prospect radar, telemetry stream, and quick-audit controls.
![Command Center Overview](docs/screenshots/overview-command-center.png)

### 2. Prospect Management & Pipeline
Organized registry of target businesses with real-time opportunity scores, website conditions, and direct audit/draft triggers.
![Prospect Management](docs/screenshots/prospect-management.png)

### 3. Website Audit & Technical Findings
Detailed diagnostic report presenting DNS zone records, TLS handshake ciphers, and classified severity findings.
![Technical Audits](docs/screenshots/technical-audits.png)

### 4. AI Evidence-Based Draft Generation Modal
In-modal AI engine selector with automatic provider routing, free-tier Gemini integration, and privacy disclosure.
![AI Draft Generation Modal](docs/screenshots/ai-draft-generation-modal.png)

### 5. Email Draft Studio & Evidence Inspector
Split-view editor featuring alternative subject lines, claim evidence citations, and one-click review controls.
![AI Draft Studio](docs/screenshots/ai-draft-studio.png)

### 6. Integrations & Credential Settings
Manage AI engine keys, select default models, test connectivity latencies, and monitor Google OAuth authorization status.
![Integrations Settings](docs/screenshots/integrations-settings.png)

---

## System Requirements

| Component | Minimum Requirement | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11, macOS 12+, or Ubuntu 20.04+ | Any modern 64-bit OS |
| **Python** | 3.11 or higher | 3.11, 3.12, or 3.13 |
| **Node.js** | 20.0.0 or higher | Node.js 22 LTS |
| **Package Managers** | `pip` (Python) and `npm` (Node) | Latest `npm` and `pip` |
| **Disk Space** | ~500 MB (codebase, virtual environment, dependencies) | 1 GB free |
| **Network** | Active internet connection for audits and API calls | Broadband connection |

### Verify Your Installed Versions

Run these commands in your terminal:

```bash
git --version
python --version   # (On macOS/Linux, use: python3 --version)
node --version
npm --version
```

---

## Installation: Quick Start

Follow these verified steps to set up Leddro on your system:

### 1. Clone the Repository

```bash
git clone https://github.com/PrajwalTheCoder/Leddro.git
cd Leddro
```

### 2. Backend Setup (FastAPI & Python)

#### On Windows (PowerShell):
```powershell
# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install backend dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### On macOS / Linux:
```bash
# Create Python virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install backend dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 3. Initialize Configuration

Copy the sanitized template file to `.env`:

```bash
# Windows PowerShell:
Copy-Item .env.example .env

# macOS / Linux:
cp .env.example .env
```

*(By default, `.env` is preconfigured to use local SQLite at `leddro.db`. You do not need any API keys or cloud databases to run the application).*

### 4. Frontend Setup (React & Vite)

In the same repository root:

```bash
npm install
```

---

## Running the Application

### Method 1: One-Command Development Launcher (Recommended)

Run both the FastAPI backend and Vite frontend together in a single terminal with automated port conflict checks and multiplexed logs:

```bash
npm run dev:all
# or directly with Python:
python run_dev.py
```

*Expected output:*
```
=== Leddro Development Workspace Launcher ===

[launcher] Starting FastAPI Backend on http://127.0.0.1:8000...
[launcher] Starting Vite Frontend on http://localhost:5173...

[OK] Both services launched successfully!
  * Frontend:  http://localhost:5173
  * API Docs:  http://127.0.0.1:8000/docs
  * Health:    http://127.0.0.1:8000/api/health

Press CTRL+C at any time to cleanly stop both services.
```

---

### Method 2: Run in Separate Terminals (Troubleshooting Fallback)

If you prefer separate processes or are debugging a specific service:

#### Terminal 1: Start Backend API

Activate your virtual environment and launch Uvicorn:

##### Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

##### macOS / Linux:
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

#### Terminal 2: Start Frontend Application

In a separate terminal window at the project root:

```bash
npm run dev
```

Open your browser and navigate to **`http://localhost:5173`**. The Vite dev server automatically proxies all `/api/*` calls to the FastAPI backend.

---

## First-Run Experience

Follow this zero-credential quick path to experience the core workflow in under 2 minutes:

1. **Open the Dashboard**: Navigate to `http://localhost:5173`. You will see the Command Center populated with your initial demonstration prospects.
2. **Execute an Audit**:
   - Go to **Prospects** in the sidebar.
   - Locate any target business (e.g., **Northstar Interiors** or **Willow Studio**).
   - Click the **Audit** button.
   - Watch the real-time probe check DNS, inspect TLS certificates, and analyze DOM structure.
3. **Inspect Findings**:
   - Navigate to **Technical Audits** to view the findings (e.g., certificate validity, mobile viewport declarations, missing meta description).
4. **Inspect Contact Information**:
   - Notice the extracted website contact details, verified MX status, and direct `📞 Call` / `💬 WhatsApp` action buttons.
5. **Draft Outreach**:
   - Click **Generate Draft** on the audited prospect.
   - If an AI provider is configured (such as free Google Gemini), click **Generate Email Draft**.
   - The AI will compose a polite letter quoting the observed audit evidence.
6. **Edit the Draft**:
   - Navigate to **Draft Studio** (`/drafts`) to refine the email copy and review alternative subject lines.

---

## Using Leddro Without AI

**You do NOT need an AI API key to use Leddro.**

Without an AI provider configured:
- ✅ **Prospect Discovery**: Fully functional using OpenStreetMap and CSV imports.
- ✅ **Website Auditing**: Fully functional. Performs live DNS queries, TLS handshakes, HTTP crawl checks, and DOM evaluations.
- ✅ **Contact Extraction**: Fully functional. Scrapes websites, validates MX records, and provides phone and WhatsApp actions.
- ✅ **Record Management**: Fully functional. Track prospect statuses, opportunity scores, and notes in your local SQLite database.
- ✅ **Manual Outreach Drafting**: Fully functional. Write and save drafts manually in Draft Studio.
- ❌ **Automated AI Synthesis**: Requires at least one configured AI provider (Google Gemini free tier, OpenAI, Anthropic, or local Ollama).

---

## Configuring AI Providers

Leddro supports 4 interchangeable AI providers. You only need to configure **one**:

| Provider | Pricing / Tier | Default Model | Data Transmission Scope |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | **Free Tier Available** via Google AI Studio | `gemini-3.5-flash-lite` | Minimal business & audit finding titles sent to Google API servers |
| **Local Ollama** | **100% Free & Local** (Zero external network) | `llama3` | 100% on-device inference; zero external data transfer |
| **OpenAI** | Commercial pay-per-token API | `gpt-4o-mini` | Minimal business & audit finding titles sent to OpenAI API servers |
| **Anthropic** | Commercial pay-per-token API | `claude-3-5-haiku-20241022` | Minimal business & audit finding titles sent to Anthropic API servers |

### 1. Google Gemini (Recommended Free Tier)
1. Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Set the key in your `.env` file:
   ```env
   AI_PROVIDER="gemini"
   GEMINI_API_KEY="your_gemini_api_key_here"
   GEMINI_MODEL="gemini-3.5-flash-lite"
   ```
3. Or configure it directly in the application UI at **Integrations** (`/integrations`).

### 2. Local Ollama (Zero External Transfer)
1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull a model in your terminal: `ollama run llama3`.
3. Set in `.env`:
   ```env
   AI_PROVIDER="compatible"
   COMPATIBLE_BASE_URL="http://localhost:11434/v1"
   COMPATIBLE_MODEL="llama3"
   ```
4. No API key is required. All processing remains strictly on your machine.

### 3. OpenAI
1. Generate an API key at [OpenAI Platform](https://platform.openai.com/api-keys).
2. Set in `.env`:
   ```env
   AI_PROVIDER="openai"
   OPENAI_API_KEY="your_openai_api_key_here"
   OPENAI_MODEL="gpt-4o-mini"
   ```

### 4. Anthropic Claude
1. Generate an API key at [Anthropic Console](https://console.anthropic.com/).
2. Set in `.env`:
   ```env
   AI_PROVIDER="anthropic"
   ANTHROPIC_API_KEY="your_anthropic_api_key_here"
   ANTHROPIC_MODEL="claude-3-5-haiku-20241022"
   ```

---

## Contact Discovery Provider Setup

### 1. Built-in Website Crawler (Zero Configuration)
- Works automatically out of the box with zero setup.
- Crawls the prospect website homepage and contact subpages for emails and phones.
- Automatically executes DNS MX record verification on discovered email addresses.

### 2. Hunter.io B2B Email Finder (Optional)
1. Create a free account at [hunter.io](https://hunter.io/api) (includes 25 free monthly searches).
2. Copy your API key from the Hunter dashboard.
3. Add to `.env`:
   ```env
   HUNTER_API_KEY="your_hunter_api_key_here"
   ```
4. Test the integration on the **Integrations** page to view available search credits.

### 3. Google Places API (New) (Optional)
1. Open the [Google Cloud Console](https://console.cloud.google.com).
2. Enable the **Places API (New)**.
3. Create an API key with Places API restrictions.
4. Add to `.env`:
   ```env
   GOOGLE_PLACES_API_KEY="your_google_places_api_key_here"
   ```
*(Google Cloud provides a recurring $200 free monthly credit for Maps Platform services).*

### 4. OpenStreetMap Discovery (Zero Configuration)
- Uses public Overpass and Nominatim endpoints by default (`https://overpass-api.de/api/interpreter`).
- No API keys or registration required.

---

## Email Integration Setup

> **Optional**: You can use discovery, auditing, and AI drafting without setting up email dispatch. Configure an email option only if you intend to send real individual consultation emails directly from the app.

### Option A: Direct Gmail SMTP (Preferred & Recommended)

This is the fastest, completely free way to send emails with **zero Google Cloud Console configuration**:

1. Go to your Google Account security settings: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
2. Type an App name (e.g., `Leddro`) and click **Create**.
3. Google generates a 16-character password (e.g., `abcd efgh ijkl mnop`).
4. Add to your `.env` file:
   ```env
   SMTP_HOST="smtp.gmail.com"
   SMTP_PORT=587
   SMTP_USER="your_email@gmail.com"
   SMTP_PASSWORD="your_16_char_app_password"
   SMTP_USE_TLS=True
   ```
5. Restart your backend (`npm run dev:all`). You can now dispatch emails directly!

---

### Option B: Google Cloud OAuth 2.0 (Advanced)

If you prefer OAuth 2.0 token authorization through Google Cloud:

1. Open the [Google Cloud Console](https://console.cloud.google.com).
2. Create a new project (e.g., `leddro-local-outreach`).
3. Enable the **Gmail API** in **APIs & Services > Library**.
4. Configure the **OAuth consent screen** (User Type: **External**).
5. Add minimal scopes:
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/gmail.send`
   *(Security Note: Leddro strictly uses send-only scope. It never reads or indexes your inbox).*
6. Add your personal email address under **Test users** (required while app status is "Testing").
7. Go to **Credentials > Create Credentials > OAuth client ID** (Application type: **Web application**).
8. Add the exact authorized redirect URI:
   `http://localhost:8000/api/google/callback`
9. Copy your **Client ID** and **Client Secret**.
10. Add them to `.env`:
    ```env
    GOOGLE_CLIENT_ID="your_client_id.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET="your_client_secret"
    GOOGLE_REDIRECT_URI="http://localhost:8000/api/google/callback"
    ```
11. Restart the backend, open `http://localhost:5173/integrations`, and click **Connect Google Account**.

---

## Configuration Reference

All settings are managed through environment variables in `.env` (derived from `.env.example`):

| Variable | Required? | Purpose | Default / Safe Example | Affected Feature |
| :--- | :---: | :--- | :--- | :--- |
| `APP_NAME` | No | Application branding title | `"Leddro Website Audit & Prospect Intelligence Engine"` | General |
| `APP_VERSION` | No | Semantic application version | `"1.0.0"` | General |
| `DATABASE_URL` | **Yes** | Connection string for database | `sqlite:///./leddro.db` | Data Storage |
| `AI_PROVIDER` | No | Active engine (`gemini`, `openai`, `anthropic`, `compatible`) | `gemini` | AI Drafting |
| `GEMINI_API_KEY` | No | API key for Google Gemini | `""` *(Get free at AI Studio)* | AI Drafting |
| `GEMINI_MODEL` | No | Gemini model identifier | `gemini-3.5-flash-lite` | AI Drafting |
| `GEMINI_BASE_URL` | No | Gemini REST endpoint base | `https://generativelanguage.googleapis.com/v1beta` | AI Drafting |
| `OPENAI_API_KEY` | No | API key for OpenAI GPT models | `""` | AI Drafting |
| `OPENAI_MODEL` | No | OpenAI model identifier | `gpt-4o-mini` | AI Drafting |
| `OPENAI_BASE_URL` | No | OpenAI REST endpoint base | `https://api.openai.com/v1` | AI Drafting |
| `ANTHROPIC_API_KEY` | No | API key for Anthropic Claude | `""` | AI Drafting |
| `ANTHROPIC_MODEL` | No | Anthropic model identifier | `claude-3-5-haiku-20241022` | AI Drafting |
| `ANTHROPIC_BASE_URL` | No | Anthropic REST endpoint base | `https://api.anthropic.com/v1` | AI Drafting |
| `COMPATIBLE_API_KEY` | No | Optional API key for local LLMs | `""` | AI Drafting |
| `COMPATIBLE_MODEL` | No | Model name for Ollama / vLLM | `llama3` | AI Drafting |
| `COMPATIBLE_BASE_URL`| No | REST URL for local Ollama / vLLM | `http://localhost:11434/v1` | AI Drafting |
| `AI_REQUEST_TIMEOUT` | No | Timeout for AI inference in seconds | `30.0` | AI Drafting |
| `AI_MAX_OUTPUT_TOKENS` | No | Maximum tokens in generated draft | `1000` | AI Drafting |
| `DEV_NAME` | No | Consultant name for email signature | `"Alex Morgan"` | Draft Studio |
| `DEV_TITLE` | No | Consultant professional title | `"Independent Web Consultant"` | Draft Studio |
| `DEV_SERVICES` | No | Summary of offered technical services | `"Website performance tuning, SSL/DNS remediation"` | Draft Studio |
| `DEV_PORTFOLIO_URL` | No | Consultant portfolio web address | `""` | Draft Studio |
| `DEV_EMAIL` | No | Default sender email address | `"consultant@example.com"` | Email Dispatch |
| `DEV_SIGNATURE` | No | Plain text email sign-off signature | `"Best regards,\nAlex Morgan"` | Draft Studio |
| `SMTP_HOST` | No | SMTP server hostname | `smtp.gmail.com` | Email Dispatch (SMTP) |
| `SMTP_PORT` | No | SMTP server port | `587` | Email Dispatch (SMTP) |
| `SMTP_USER` | No | SMTP account username / email | `""` | Email Dispatch (SMTP) |
| `SMTP_PASSWORD` | No | 16-character Google App Password | `""` | Email Dispatch (SMTP) |
| `SMTP_USE_TLS` | No | Enable STARTTLS transport security | `True` | Email Dispatch (SMTP) |
| `GOOGLE_CLIENT_ID` | No | OAuth 2.0 Web Client ID | `""` | Email Dispatch (OAuth) |
| `GOOGLE_CLIENT_SECRET` | No | OAuth 2.0 Web Client Secret | `""` | Email Dispatch (OAuth) |
| `GOOGLE_REDIRECT_URI` | No | Callback endpoint for OAuth | `http://localhost:8000/api/google/callback` | Email Dispatch (OAuth) |
| `GOOGLE_OAUTH_SCOPES` | No | OAuth permissions requested | `https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/gmail.send` | Email Dispatch (OAuth) |
| `FRONTEND_URL` | No | Frontend origin allowed by CORS | `http://localhost:5173` | Security |
| `CREDENTIAL_ENCRYPTION_KEY` | No | Fernet 32-urlsafe base64 token key | `""` *(Auto-generated in .leddro_encryption_key if blank)* | Security |
| `OSM_OVERPASS_URL` | No | Endpoint for Overpass OSM search | `https://overpass-api.de/api/interpreter` | Discovery |
| `OSM_NOMINATIM_URL` | No | Endpoint for Nominatim geocoding | `https://nominatim.openstreetmap.org/search` | Discovery |
| `OSM_USER_AGENT` | No | HTTP User-Agent header for OSM | `"LeddroBusinessDiscovery/1.0 (+https://github.com/leddro/leddro)"` | Discovery |
| `GOOGLE_PLACES_API_KEY` | No | Google Places API (New) key | `""` | Discovery (Places) |
| `HUNTER_API_KEY` | No | Hunter.io B2B email search key | `""` | Contact Intelligence |

---

## Database and Data Storage

### SQLite (Default)
Leddro maintains an SQLite database file at `leddro.db` in the repository root. All prospects, audit findings, draft emails, and history records persist automatically across server reboots. The database utilizes WAL (Write-Ahead Logging) mode for enhanced concurrency and durability.

### Optional Neon Serverless PostgreSQL
To use cloud-hosted serverless PostgreSQL with Neon:
1. Copy your pooled connection string from the [Neon Console](https://console.neon.tech).
2. Set in `.env`:
   ```env
   DATABASE_URL="postgresql://user:password@ep-...neon.tech/neondb?sslmode=require"
   ```
3. Restart the backend. Leddro automatically applies table migrations and column checks.

---

## Backup and Recovery

Leddro includes a native Python backup engine in [backend/app/core/backup.py](backend/app/core/backup.py) utilizing the atomic SQLite online backup API (`sqlite3_backup`). This ensures zero corrupted bytes even while background writes occur.

### Create an Atomic Backup
```bash
npm run backup
# or via Python:
python -m backend.app.core.backup --backup
```
Backups are validated using `PRAGMA integrity_check` and saved to `backups/` with UTC timestamps (e.g., `backups/leddro_backup_20261019_120000.db`).

### Verify an Existing Backup
```bash
python -m backend.app.core.backup --verify backups/your_backup_file.db
```

### Restore from Backup
```bash
# Validates PRAGMA integrity_check and automatically creates a safety snapshot before overwriting
python -m backend.app.core.backup --restore backups/your_backup_file.db
```

---

## Privacy, Security, and Responsible Use

- **Local-First Boundary**: Secrets (`.env`, encryption keys, SQLite database) are never committed to version control and are ignored by `.gitignore`.
- **SSRF Defenses**: The audit crawler validates every target domain against DNS rebinding, private IP subnets (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`), and cloud metadata endpoints (`169.254.169.254`).
- **Prompt-Injection Defense**: Model prompts enclose untrusted crawled pages and business names in strict `<untrusted_prospect_data>` XML tags.
- **Strictly Single-Message Dispatch**: Leddro contains zero mass-mail sequences or automated dispatch triggers. Approving an email draft updates review status in SQLite only; dispatch requires explicit confirmation.
- **Suppression Registry**: Recipient emails and domains are verified against `suppression_records` to prevent messaging unsubscribed contacts.
- **Single-User Development Disclaimer**: Leddro is built for single-operator local use and does not contain multi-tenant user authentication. Do **not** expose the development server to untrusted public networks without reverse proxy authentication (e.g., HTTP Basic Auth or VPN).
- **Vulnerability Reporting**: See [SECURITY.md](SECURITY.md) for our coordinated vulnerability disclosure policy.

---

## Troubleshooting

| Problem | Likely Cause | Diagnosis & Solution |
| :--- | :--- | :--- |
| **`python: command not found`** | Python not installed or not in PATH | Use `python3` on Linux/macOS or verify Python was installed with "Add Python to PATH" checked on Windows. |
| **`pip install` fails on psycopg2** | Missing C compiler for PostgreSQL | Run `python -m pip install --upgrade pip`. `psycopg2-binary` provides precompiled wheels that require no compiler. |
| **`npm run dev` fails with module error** | Incomplete npm dependency install | Run `npm install` in the repository root. Ensure Node.js is version 20 or higher. |
| **Frontend displays "Backend Offline"** | FastAPI server not running on port 8000 | Verify Terminal 1 is running `uvicorn backend.app.main:app --port 8000`. Test `http://127.0.0.1:8000/api/health` directly in your browser. |
| **Port 8000 or 5173 already in use** | A previous instance is still running | Terminate dangling processes, or start Uvicorn on another port (e.g., `--port 8001`) and update `vite.config.ts`. |
| **AI Draft displays "Missing Configuration"** | Active engine has no API key in `.env` | Configure your free Google Gemini key in `.env` or select an engine on the **Integrations** page (`/integrations`). |
| **Hunter.io API returns 401 or 429** | Invalid key or monthly quota reached | Verify your key in `.env`. Free accounts include 25 monthly searches. If exhausted, rely on the built-in website scraper. |
| **Google Places returns NOT_CONFIGURED** | Missing `GOOGLE_PLACES_API_KEY` | Add your API key to `.env` or continue using OpenStreetMap discovery with zero API keys required. |
| **SMTP Authentication Fails (535 error)** | Using regular Google password instead of App Password | Google accounts with 2FA require a 16-character App Password generated at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords). |
| **Google OAuth Redirect URI Mismatch** | Redirect URL doesn't match Google Cloud Console | Ensure Google Console contains the exact URI: `http://localhost:8000/api/google/callback` (check port, scheme, and trailing slash). |
| **SSRF Policy URL Rejected** | Target URL resolves to localhost or private IP | Auditing localhost or private RFC1918 IPs is blocked by design for security. Test with public URLs (e.g., `https://example.com`). |

---

## Updating Leddro

To pull the latest updates from GitHub without losing your local configuration:

```bash
# 1. Back up your local database first
npm run backup

# 2. Pull updates
git pull origin main

# 3. Update dependencies
pip install -r backend/requirements.txt
npm install

# 4. Restart development workspace
npm run dev:all
```

*(Your local `.env` and `leddro.db` files are ignored by Git and will not be overwritten by `git pull`).*

---

## Testing and Development

Leddro maintains a comprehensive automated test suite with **196 passing tests** across backend services and security layers:

```bash
# Run complete backend pytest suite (196 automated tests)
python -m pytest backend/tests/ -v

# Run audit comparison & change detection test suite (21 tests)
python -m pytest backend/tests/test_audit_comparison.py -v

# Run prospect intelligence & scoring test suite (23 tests)
python -m pytest backend/tests/test_prospect_scoring.py -v

# Run email scraper & contact intelligence test suite
python -m pytest backend/tests/test_email_scraper.py -v

# Run Google OAuth & SMTP dispatch test suite
python -m pytest backend/tests/test_google_oauth_and_email.py -v

# Run SSRF security validation test suite
python -m pytest backend/tests/test_ssrf_validator.py -v

# Run SQLite backup and recovery test suite
python -m pytest backend/tests/test_backup_and_recovery.py -v

# Run frontend TypeScript typecheck
npx tsc --noEmit

# Test production bundle compilation
npm run build

# Run frontend linter
npm run lint
```

### Test Suite Highlights
- `test_prospect_scoring.py`: Determinism, score bounds [0, 100], no-audit handling, diagnostic failure handling, HTTPS status distinctions, finding severity weighting, duplicate findings deduplication, audit recency decay, contact readiness verification, evidence traceability, and query performance (N+1 elimination).
- `test_audit_comparison.py`: Four-way finding classification (RESOLVED, NEW, PERSISTENT, INCONCLUSIVE), positive-evidence rule enforcement, telemetry deltas, and cross-domain protection.
- `test_email_scraper.py`: Contact extraction, junk extension rejection, placeholder domain filtering, and DNS MX deliverability verification.
- `test_ai_drafting.py`: Fact-checking validation, prompt-injection defense, and fallback provider routing.
- `test_audit_engine.py`: HTTP status codes, malformed HTML, and response timeouts.
- `test_ssrf_validator.py`: Private IP blocking, cloud metadata blocks, and DNS rebinding prevention.
- `test_google_oauth_and_email.py`: Token encryption, PKCE verification, SMTP dispatch, header injection protection, uncertain delivery states, and duplicate-send prevention.
- `test_backup_and_recovery.py`: SQLite online backup, corruption recovery, and restoration.

---

## Project Architecture

```mermaid
flowchart TD
    User["Operator / Consultant"] <--> UI["React 19 + Vite Frontend"]
    UI <--> API["FastAPI Backend Engine"]
    API <--> DB[("SQLite Database (leddro.db)")]
    API <--> Audits["Website Audit Crawler (SSRF Protected)"]
    API <--> Contacts["Contact Crawler & DNS MX Verifier"]
    API <--> Discovery["OpenStreetMap & Google Places"]
    API <--> Hunter["Hunter.io B2B Email Finder"]
    API <--> AI["AI Engines (Gemini, OpenAI, Claude, Ollama)"]
    API <--> SMTP["Direct Gmail SMTP Gateway"]
    API <--> Gmail["Gmail API OAuth Gateway (Safe Single Send)"]
```

---

## Directory Structure

```
Leddro/
├── backend/
│   ├── app/
│   │   ├── ai/             # AI providers, prompts & claim validation
│   │   ├── api/            # FastAPI REST routers (/prospects, /audits, /drafts, /integrations)
│   │   ├── core/           # Config, database engine, security & backup
│   │   ├── discovery/      # OSM Overpass, Google Places & CSV normalization
│   │   │   └── providers/  # Modular discovery providers (OSM, Places, CSV)
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Audit engine, comparison, contact scraper, SSRF & Gmail client
│   │   └── main.py         # FastAPI application entry point
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # 196 automated pytest test cases
├── docs/
│   └── screenshots/        # Verified application screenshots
├── public/                 # Static assets & SVG icons
├── src/
│   ├── components/         # Modals, buttons, badges, navigation
│   ├── context/            # React AppContext global state
│   ├── data/               # Seed demonstration data
│   ├── pages/              # Overview, Prospects, Audits, Drafts, Integrations
│   └── App.tsx             # Application routing
├── .env.example            # Sanitized configuration template
├── package.json            # Node.js dependencies & scripts
├── run_dev.py              # Multiplexed development launcher
├── vite.config.ts          # Vite configuration & backend proxy
└── README.md               # Product documentation
```

---

## Roadmap

### Completed
- [x] **Phase 1-4**: Core architecture, diagnostic website audit engine, UI system & prospect discovery.
- [x] **Phase 5**: Evidence-based AI drafting with anti-hallucination verification.
- [x] **Phase 6**: Secure Google OAuth 2.0 with Fernet token encryption & safe email dispatch.
- [x] **Phase 7**: Production readiness, atomic SQLite backup/recovery, Neon PostgreSQL compatibility & CI pipeline.
- [x] **Phase 8.1-8.2**: Explainable heuristic scoring (Opportunity & Data Confidence) with full evidence traceability.
- [x] **Phase 8.3**: Website audit comparison & change detection engine with directional telemetry deltas.
- [x] **Contact Intelligence & Verification**: Autonomous website contact scraper, DNS MX mail verification, Hunter.io integration, Google Places API, Zero Fake Emails policy, and direct Phone/WhatsApp actions.

### In Progress
- [ ] **Phase 9**: Premium documentation, developer onboarding excellence, and open-source release readiness.

### Planned
- [ ] **Scheduled Recurring Re-Audits**: Background periodic re-auditing with automated change diffs and email notifications.
- [ ] **Headless CLI Audit Mode**: Run single or batch audits directly from the command line for CI/CD pipeline integration.
- [ ] **Local LLM Sidecar**: Bundled `llama.cpp` sidecar for zero-dependency offline AI inference without requiring manual Ollama installation.

---

## Contributing

We welcome community contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on setting up your local environment, coding standards, and submitting pull requests.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feat/my-improvement`).
3. Commit your changes (`git commit -m 'feat: add my improvement'`).
4. Ensure all tests pass (`python -m pytest backend/tests/` and `npm run build`).
5. Open a Pull Request.

---

## Security Disclosures

Please review our [SECURITY.md](SECURITY.md) for vulnerability reporting guidelines. If you discover a security issue or potential vulnerability, please report it responsibly by opening a confidential advisory or contacting the maintainers directly. Do **not** disclose security vulnerabilities in public GitHub issues.

Automated security checks and secret scanning run on every pull request via Gitleaks in our GitHub Actions CI pipeline.

---

## License and Acknowledgements

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

- OpenStreetMap data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), licensed under ODbL 1.0.
- Icons by [Lucide](https://lucide.dev/).
- Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), and [Tailwind CSS](https://tailwindcss.com/).
