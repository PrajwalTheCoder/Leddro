<div align="center">
  <img src="public/logo.png" alt="Leddro Logo Mark" width="88" />
  <br />
  <img src="public/leddro-name-logo.png" alt="Leddro" width="280" />
  <br /><br />
  <p><strong>Discover prospects. Audit websites. Understand opportunities. Prepare evidence-based outreach.</strong></p>
  <p>🌐 <strong>Live Interactive Showcase &amp; Demo Sandbox:</strong> <a href="https://prajwalthecoder.github.io/Leddro/">https://prajwalthecoder.github.io/Leddro/</a></p>
  <p>📺 <strong>YouTube Full Walkthrough Video:</strong> <a href="https://youtu.be/5XIetvU-NII">https://youtu.be/5XIetvU-NII</a></p>
</div>

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Interactive%20Sandbox-D2F824?style=flat&logo=googlechrome&logoColor=black)](https://prajwalthecoder.github.io/Leddro/)
[![YouTube Walkthrough](https://img.shields.io/badge/YouTube-Video%20Demo-FF0000?style=flat&logo=youtube&logoColor=white)](https://youtu.be/5XIetvU-NII)
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

[Overview](#overview) • [Screenshots](#screenshots-interface-tour) • [Quick Start](#quick-start) • [Workflow](#workflow-overview) • [Features](#features-technical-depth) • [Architecture](#project-architecture) • [Testing](#testing-and-development)

---

## Table of Contents

- [⚡ Overview](#overview)
- [Why Leddro?](#why-leddro)
- [📸 Screenshots & Interface Tour](#screenshots-interface-tour)
- [🔄 Workflow Overview](#workflow-overview)
- [🚀 Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Step 1: Clone the Repository](#step-1-clone-the-repository)
  - [Step 2: Backend Setup (Python)](#step-2-backend-setup-python)
  - [Step 3: Initialize Configuration](#step-3-initialize-configuration)
  - [Step 4: Frontend Setup (React & Vite)](#step-4-frontend-setup-react-vite)
  - [Running the Application](#running-the-application)
  - [Interactive Terminal CLI Audit Mode](#interactive-terminal-cli-audit-mode)
  - [First-Run Experience (2 Minutes)](#first-run-experience-2-minutes)
  - [Using Leddro Without AI](#using-leddro-without-ai)
- [🔍 Features & Technical Depth](#features-technical-depth)
  - [1. Prospect Discovery & Management](#1-prospect-discovery-management)
  - [2. Diagnostic Website Auditing & Telemetry](#2-diagnostic-website-auditing-telemetry)
  - [3. Prospect Intelligence & Explainable Scoring](#3-prospect-intelligence-explainable-scoring)
  - [4. Website Audit Comparison & Change Detection](#4-website-audit-comparison-change-detection)
  - [5. Contact Intelligence & Email Discovery](#5-contact-intelligence-email-discovery)
    - [Zero-Website Multi-Channel Footprint Discovery](#zero-website-multi-channel-footprint-discovery)
  - [6. Evidence-Aware AI Outreach Drafting](#6-evidence-aware-ai-outreach-drafting)
  - [7. Safe Email Dispatch](#7-safe-email-dispatch)
- [⚙️ Configuration Reference (.env)](#configuration-reference-env)
- [💾 Database, Backup & Recovery](#database-backup-recovery)
- [🛡️ Privacy, Security, and Responsible Use](#privacy-security-and-responsible-use)
- [🔧 Troubleshooting](#troubleshooting)
- [🔄 Updating Leddro](#updating-leddro)
- [🧪 Testing and Development](#testing-and-development)
- [🏗️ Project Architecture](#project-architecture)
- [📁 Directory Structure](#directory-structure)
- [🗺️ Roadmap](#roadmap)
- [🤝 Contributing](#contributing)
- [🔒 Security Disclosures](#security-disclosures)
- [📄 License and Acknowledgements](#license-and-acknowledgements)

---

## ⚡ Overview

Independent developers and digital consultants often struggle with client acquisition. Traditional sales automation tools treat outreach as a volume game: they scrape thousands of unverified email addresses and blast generic templates that damage sender reputation and yield near-zero response rates.

Leddro provides an evidence-based alternative:

1. **Local Business Discovery**: Find commercial businesses in any geographical region via OpenStreetMap or structured CSV imports without recurring data fees.
2. **Deep Technical Diagnostics**: Audit prospect websites with non-destructive server-side probes checking DNS zones, TLS certificates, HTTP response latency, and DOM structure.
3. **Transparent Opportunity Scoring**: Prioritize prospects using an explainable 0–100 heuristic based entirely on observable technical defects and data confidence.
4. **Verified Contact Intelligence**: Autonomously discover authentic contact details directly from websites, check domain MX mail exchangers, and integrate B2B directory lookups (Hunter.io, Google Places) with a strict **Zero Fake Emails** policy.
5. **Evidence-Grounded AI Synthesis**: Generate factual, respectful consultation proposals where every technical assertion is linked to stored audit evidence, preventing AI hallucinations.
6. **Controlled Single-Message Dispatch**: Review, customize, and dispatch personalized emails individually via Gmail SMTP or Google Cloud OAuth with strict suppression enforcement and zero bulk automation.

---

### Why Leddro?

| Dimension | Conventional Outreach Platforms | Leddro Developer Workspace |
| :--- | :--- | :--- |
| **Data Architecture** | Closed SaaS database; vendor controls your data | **Local-First SQLite**; complete ownership on your machine |
| **Outreach Grounding** | Vague flattery (*"I loved your website..."*) | **Deterministic Evidence** (*"Your SSL certificate expires in 4 days..."*) |
| **Contact Integrity** | Fabricates guessed emails (`contact@company.com`) | **Zero Fake Emails Policy**; MX checks and direct Phone/WhatsApp actions |
| **Email Dispatch** | Bulk sequence automation & auto-dialers | **Strictly Single-Message Dispatch**; human approval required for every send |
| **AI Transparency** | Black-box prompts with unchecked hallucinations | **Factual Claim Mapping**; assertions verified against audit finding IDs |
| **Cost & Licensing** | $80–$300/month subscription lock-in | **100% Free & Open Source (MIT)**; runs with free-tier APIs or offline LLMs |
| **Network Security** | Unrestricted external crawling | **Hardened SSRF Defenses**; blocks loopback, private subnets, and metadata IPs |

---

## 📸 Screenshots & Interface Tour

[![Leddro Full Walkthrough Demo](https://img.youtube.com/vi/5XIetvU-NII/maxresdefault.jpg)](https://youtu.be/5XIetvU-NII)

> 📺 **[Watch the full Leddro video walkthrough and live architecture demo on YouTube](https://youtu.be/5XIetvU-NII)**

All screenshots below represent the live Leddro application interface:

### 1. Command Center & Tactical Radar Overview
Comprehensive mission dashboard featuring real-time health gauges, interactive prospect radar, telemetry stream, and quick-audit controls.
![Command Center Overview](docs/screenshots/overview-command-center.png)

### 2. Relationship Graph & Force Simulation
Interactive D3 force-directed topological network visualization mapping live links between target prospects, DNS servers, AI engines, email gateways, and diagnostic audit findings with physics-driven dragging and real-time edge telemetry.
![Relationship Graph & Force Simulation](docs/screenshots/relationship-graph.png)

### 3. Autonomous Business Discovery Engine & Registry Provenance
Query live geographic registries (OpenStreetMap Overpass API) and web indices by commercial category, city, and radius to pinpoint local businesses with real-time website condition detection and zero-website footprint tracking.
![Autonomous Business Discovery](docs/screenshots/autonomous-discovery.png)

*Deep inspection modal displaying authenticated OpenStreetMap entity IDs, precise geocoordinates, contact verification, and one-click pipeline ingestion:*
![Autonomous Discovery Inspection Modal](docs/screenshots/autonomous-discovery-detail.png)

### 4. Prospect Management & Pipeline
Organized registry of target businesses with real-time opportunity scores, website conditions, and direct audit/draft triggers.
![Prospect Management](docs/screenshots/prospect-management.png)

### 5. AI Evidence-Based Draft Generation Modal
In-modal AI engine selector with automatic provider routing, free-tier Gemini integration, and privacy disclosure.
![AI Draft Generation Modal](docs/screenshots/ai-draft-generation-modal.png)

### 6. Website Audit & Technical Findings
Detailed diagnostic report presenting DNS zone records, TLS handshake ciphers, and classified severity findings.
![Technical Audits](docs/screenshots/technical-audits.png)

### 7. Email Draft Studio & Evidence Inspector
Split-view editor featuring alternative subject lines, claim evidence citations, and one-click review controls.
![AI Draft Studio](docs/screenshots/ai-draft-studio.png)

### 8. Integrations & Credential Settings
Manage AI engine keys, select default models, test connectivity latencies, and monitor Google OAuth authorization status.
![Integrations Settings](docs/screenshots/integrations-settings.png)

---

## 🔄 Workflow Overview

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

## 🚀 Quick Start

Get Leddro installed and running locally in under 3 minutes:

### Prerequisites

| Component | Minimum Requirement | Verified Version | Check Command |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11 or higher | 3.11, 3.12, 3.13 | `python --version` *(or `python3 --version`)* |
| **Node.js** | 20.0.0 or higher | Node.js 20 or 22 LTS | `node --version` |
| **Package Managers** | `pip` and `npm` | Latest stable | `npm --version` |
| **Operating System** | Windows 10/11, macOS 12+, Ubuntu 20.04+ | 64-bit OS | `git --version` |

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/PrajwalTheCoder/Leddro.git
cd Leddro
```

---

### Step 2: Backend Setup (Python)

#### On Windows (PowerShell):
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip & install dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### On macOS / Linux:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip & install dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

### Step 3: Initialize Configuration

Copy the sanitized template file to `.env`:

```bash
# Windows PowerShell:
Copy-Item .env.example .env

# macOS / Linux:
cp .env.example .env
```

*(By default, `.env` is preconfigured to use local SQLite at `leddro.db`. You do **not** need an API key or cloud database to run the app).*

---

### Step 4: Frontend Setup (React & Vite)

In the same repository root:

```bash
npm install
```

---

### Running the Application

#### Method 1: Single-Command Development Launcher (Recommended)

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

Open your browser and navigate to **`http://localhost:5173`**.

---

#### Method 2: Run in Separate Terminals (Troubleshooting Fallback)

If you prefer separate processes:

**Terminal 1 (Backend API):**
```bash
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# macOS / Linux:
source .venv/bin/activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

**Terminal 2 (Frontend):**
```bash
npm run dev
```
Navigate to **`http://localhost:5173`**.

---

### Interactive Terminal CLI Audit Mode

You can also run instant, non-destructive website audits directly from your terminal without opening the web interface:

```bash
# Human-readable colored report with telemetry and findings
python -m backend.app.cli audit https://example.com

# Raw JSON output (for scripting and CI pipelines)
python -m backend.app.cli audit https://example.com --json
```

---

### First-Run Experience (2 Minutes)

Follow this zero-credential path to experience the core workflow right away:

1. **Open Dashboard**: Go to `http://localhost:5173` to see your Command Center with initial demonstration prospects.
2. **Execute an Audit**:
   - Navigate to **Prospects** in the sidebar.
   - Click **Audit** on any target business (e.g., **Northstar Interiors**).
   - Watch the real-time probe test DNS, TLS certificates, HTTP status, and DOM layout.
3. **Inspect Findings**:
   - Navigate to **Technical Audits** to view the findings (certificate validity, mobile viewport declarations, missing meta description).
4. **Inspect Contact Information**:
   - Notice the extracted website contact details, verified MX status, and direct `📞 Call` / `💬 WhatsApp` action buttons.
5. **Draft Outreach**:
   - Click **Generate Draft** on the audited prospect.
   - If an AI provider is configured (such as free Google Gemini), click **Generate Email Draft**.
   - The AI will compose a polite letter quoting the observed audit evidence.

---

### Using Leddro Without AI

**You do NOT need an AI API key to use Leddro.**

Without an AI provider configured:
- ✅ **Prospect Discovery**: Fully functional using OpenStreetMap and CSV imports.
- ✅ **Website Auditing**: Fully functional. Performs live DNS queries, TLS handshakes, HTTP crawl checks, and DOM evaluations.
- ✅ **Contact Extraction**: Fully functional. Scrapes websites, validates MX records, and provides phone and WhatsApp actions.
- ✅ **Record Management**: Fully functional. Track prospect statuses, opportunity scores, and notes in your local SQLite database.
- ✅ **Manual Outreach Drafting**: Fully functional. Write and save drafts manually in Draft Studio.
- ❌ **Automated AI Synthesis**: Requires at least one configured AI provider (Google Gemini free tier, OpenAI, Anthropic, or local Ollama).

---

## 🔍 Features & Technical Depth

### 1. Prospect Discovery & Management
- **OpenStreetMap Integration**: Query local businesses by city, state, or postal code via Overpass API and Nominatim geocoding with zero API keys required.
- **CSV Batch Import**: Ingest existing lead lists with automatic column detection, duplicate identification, and formula injection protection (`=`, `+`, `-`, `@`). Includes an annotated sample template at [docs/sample_import.csv](docs/sample_import.csv).
- **Interactive Terminal CLI Mode**: Perform rapid non-destructive audits directly from your shell using `python -m backend.app.cli audit <url>` with rich ANSI color telemetry or raw `--json` machine output.
- **Google Places API (New)**: Optional integration for high-accuracy business lookups, official websites, and phone numbers using Google Cloud's $200 free monthly credit.
- **Deterministic Deduplication**: Cross-references source provider IDs, canonical registered web domains (`extract_registered_domain`), and normalized business names + locality to prevent duplicate records.

---

### 2. Diagnostic Website Auditing & Telemetry
- **DNS Zone Analysis**: Queries A, AAAA, MX, and NS records with millisecond resolution timing. Identifies missing records, zone misconfigurations, and mail host routing.
- **TLS / SSL Verification**: Inspects certificate authorities, validity dates, protocol support (TLSv1.2, TLSv1.3), and cipher configurations.
- **HTTP & Server Telemetry**: Evaluates socket connection latency, Time To First Byte (TTFB), HTTP status codes (200, 301, 404, 500), and security response headers (`Strict-Transport-Security`, `X-Content-Type-Options`).
- **DOM & Mobile Evaluation**: Checks for mobile responsive `<meta name="viewport">` tags, document `<title>`, meta descriptions, and OpenGraph social cards.
- **SSRF Network Security**: Outbound crawler strictly blocks loopback addresses (`127.0.0.0/8`), RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud instance metadata endpoints (`169.254.169.254`).

---

### 3. Prospect Intelligence & Explainable Scoring

Leddro provides an explainable heuristic to prioritize prospects based on verified technical need. Every score is directly traceable to observed website issues and discovery metadata.

> [!NOTE]
> **What the Opportunity Score Means**: A transparent 0–100 heuristic ranking prospects based on observable technical deficiencies (such as DNS errors, server failures, missing HTTPS, or security headers). Higher scores indicate stronger technical room for improvement.
>
> **What It Does NOT Mean**: It does **NOT** predict whether a business will buy, convert, or reply. It is not an opaque machine learning probability score.

#### Four Decoupled Dimensions
1. **Opportunity Score (0–100)**: Heuristic of technical need / room for improvement based on observed website evidence.
2. **Data Confidence (0–100)**: Measure of how complete, fresh, and reliable the diagnostic evidence is.
3. **Audit Severity**: Exact count of high, medium, low, and informational findings from real audit probes.
4. **Contact Readiness**: Verification state of communication channels (`verified`, `unverified`, `absent`, `unknown`).

#### Scoring Factors and Weights (Sum: 100 Points)

| Factor | Max Pts | Contribution Rules |
| :--- | :---: | :--- |
| **1. Website Accessibility** | 25 pts | • DNS resolution failure (NXDOMAIN / missing A records): +25 pts<br>• Confirmed HTTP server error (4xx/5xx): +20 pts<br>• No website registered: +15 pts (potential opportunity for web presence creation)<br>• Confirmed reachable (HTTP 200/3xx): +0 pts<br>• Diagnostic error / timeout: +0 pts (marked inconclusive; lowers confidence) |
| **2. Technical Findings & Severity** | 55 pts | • High-severity findings: +15 pts each (capped at 35 pts)<br>• Medium-severity findings: +5 pts each (capped at 20 pts)<br>• Low-severity findings: +1 pt each (capped at 5 pts)<br>• Informational notices: +0 pts<br>• Duplicate findings sharing category and title are deduplicated automatically |
| **3. HTTPS & Transport Security** | 20 pts | • Invalid, expired, or untrusted certificate: +20 pts<br>• HTTP-only website with no HTTPS: +15 pts<br>• Valid TLS certificate (v1.2/v1.3): +0 pts<br>• Unchecked or diagnostic connection failure: +0 pts (marked unconfirmed) |
| **4. Contact Readiness & Completeness** | 0 pts | • Direct contact readiness is tracked separately and **never inflates Opportunity Score**.<br>• Unverified contact or incomplete profile details penalize Data Confidence (-8 to -15 pts) and populate explicit limitations. |

- **Diagnostic Failures**: An audit that fails due to a network timeout or runner connection error is **never** penalized as a website defect. The factor is marked `check_failed` (nature: `failed_diagnostic`) and data confidence is reduced.
- **Audit Recency Decay**: Audits older than 30 days decay confidence (-15 pts), and audits older than 90 days decay confidence further (-30 pts).
- **Full Evidence Traceability**: Every displayed evidence item links directly to an authentic stored audit finding ID and recorded HTTP/DNS evidence.

---

### 4. Website Audit Comparison & Change Detection

Leddro includes a deterministic before/after comparison engine allowing operators to evaluate changes between two audits of the same website over time.

> [!IMPORTANT]
> **Resolution Rule**: A missing finding in a newer audit does **NOT** automatically mean an issue was fixed. Leddro requires explicit positive proof of a passing check to classify any issue as resolved.

| Classification | Meaning | Rule & Evidence Requirement |
| :--- | :--- | :--- |
| **RESOLVED** | Issue confirmed fixed | A finding was confirmed in the older audit, and the newer audit provides positive evidence that the relevant check completed successfully and passed. |
| **NEW** | Newly detected issue | An issue was not present in the older audit, and the newer audit confirms a new defect with evidence. The older check must have run successfully or baseline evidence must be complete. |
| **PERSISTENT** | Issue confirmed in both | The same underlying defect is confirmed in both audits with ongoing evidence. |
| **INCONCLUSIVE** | Evidence insufficient | Evidence cannot establish whether an issue was fixed, appeared, or persisted. Occurs if the newer audit failed, timed out, skipped the check, or omitted the finding without pass evidence. |

- **Telemetry Deltas**: Directional deltas for TTFB latency (ms and %), DOM ready latency, payload size (KB), responsive viewport state, and TLS protocol upgrades.
- **Cross-Domain Guard**: Comparisons are strictly enforced against identical prospect records or canonical website domain identities (`extract_registered_domain`).

---

### 5. Contact Intelligence & Email Discovery

```
[Target Website] ──► [SSRF Check] ──► [Page Scraper (/, /contact, /about)] ──► [Filter Junk] ──► [DNS MX Check] ──► [Verified Contacts]
                                                                                                          ▲
                                      [Hunter.io API (B2B Directory)] ─────────────────────────────────────┤
                                      [Google Places API (Phone & Web)] ───────────────────────────────────┘
```

- **Autonomous Contact Crawler**: Scans the homepage and contact subpages (`/contact`, `/about`, `/reach-us`, `/location`) for public emails and phone numbers.
- **DNS MX Mailbox Verification**: Validates that discovered email domains maintain active, responsive mail exchange records before saving.
- **Zero Fake Emails Policy**: Never fabricates placeholder email addresses like `contact@{domain}.com`. If no email is discovered, the address remains empty with clear visual warnings.
- **Direct Phone & WhatsApp Actions**: Click-to-call (`tel:`) and 1-click WhatsApp web chat (`https://wa.me/`) with pre-filled technical audit outreach messages.
- **Hunter.io B2B Email Finder**: Search verified professional emails, executive names, positions, and confidence scores (25 free monthly searches).
- **Quick-Fill Email Pills**: 1-click `+ info@{domain}` and `+ contact@{domain}` pills in the draft editor when the operator knows the address.

#### Zero-Website Multi-Channel Footprint Discovery

Many local establishments (cafes, restaurants, boutique retail, service professionals) never register a custom `.com` domain—instead treating social profiles and local directories as their digital storefronts. Leddro incorporates a dedicated 5-pillar discovery engine to track down verified emails, WhatsApp lines, and verified presence across the deep web:

```
[Business Without Website]
             │
             ├──► [Pillar 1: Social Storefronts] ────► Facebook Page "About" & Instagram Bios
             ├──► [Pillar 2: Search Dorking] ────────► Google / Regional Bing with TLS Anti-Bot Camouflage
             ├──► [Pillar 3: WhatsApp Business] ─────► 10-Digit Mobile Dorking & 1-Click wa.me Chat
             ├──► [Pillar 4: Local Directories] ─────► Justdial, Zomato, Swiggy, IndiaMART Schema.org
             └──► [Pillar 5: Public Filings] ────────► FSSAI 14-Digit Food Licenses & 15-Char GSTIN Records
                         │
                         ▼
             [Aggregator Blacklist Filter] ──► [DNS MX Deliverability Probe] ──► [Auto-Sync to Database]
```

1. **Facebook Pages & Instagram Bios**: Queries search indexes to discover the business's official social storefronts and extracts public contact emails from the bio/about metadata without login walls.
2. **Search Engine Dorking with Anti-Bot Camouflage**: Queries DuckDuckGo and regional Bing (`cc=IN&setlang=en-IN`) using targeted commercial inquiry dorks (`"table bookings"`, `"catering inquiries"`, `email OR "@gmail.com"`). Utilizes TLS/JA3 client impersonation via `primp` to bypass automated bot challenges.
3. **WhatsApp Business Profile Metadata**: Dorks registered mobile numbers for published email addresses and automatically formats active `https://wa.me/<E164>` direct chat links for friction-free outreach.
4. **Local Business Directories**: Scrapes structured Schema.org JSON-LD metadata from Justdial, Zomato, Swiggy, and IndiaMART partner profiles to extract verified phone numbers and location coordinates.
5. **Government & Regulatory Registrations**: Identifies statutory government food licenses (FSSAI 14-digit license numbers) and tax IDs (15-character GSTIN numbers) embedded in public inspection filings.
- **Aggregator Exclusion Filtering**: Explicitly purges third-party aggregator platform emails (e.g., `pulled.coffee`, `slurrp`, `zomato`, `swiggy`, `justdial`, `magicpin`) so that developer or corporate helpdesk emails are never mistakenly saved.
- **Operator Workflow**: Trigger one-click **Deep Search** directly from the Prospects table or inspect the full **Multi-Channel Social & Deep Web Intelligence** dossier inside the Prospect Detail Modal.

---

### 6. Evidence-Aware AI Outreach Drafting

Leddro supports 4 interchangeable AI providers:

| Provider | Pricing / Tier | Default Model | Data Transmission Scope |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | **Free Tier Available** via Google AI Studio | `gemini-3.5-flash-lite` | Minimal business & audit finding titles sent to Google API servers |
| **Local Ollama** | **100% Free & Local** (Zero external network) | `llama3` | 100% on-device inference; zero external data transfer |
| **OpenAI** | Commercial pay-per-token API | `gpt-4o-mini` | Minimal business & audit finding titles sent to OpenAI API servers |
| **Anthropic** | Commercial pay-per-token API | `claude-3-5-haiku-20241022` | Minimal business & audit finding titles sent to Anthropic API servers |

- **Anti-Hallucination Claim Validation**: Automatically parses generated drafts, cross-references technical assertions with stored audit finding IDs in SQLite, and flags unverified claims with warning badges.
- **Prompt Injection Containment**: Crawled page content and untrusted business metadata are encapsulated within `<untrusted_prospect_data>` XML delimiters.
- **In-Modal Provider Switcher**: Toggle engines directly inside the draft generation dialog without navigating away.

---

### 7. Safe Email Dispatch

Leddro prioritizes sender reputation, deliverability, and human oversight.

#### Two Supported Delivery Gateways

```
                          ┌──► [Option A: Direct SMTP Gateway] ────► smtp.gmail.com:587 (App Password)
[Draft Studio] ──► [Send] ┤
                          └──► [Option B: Google Cloud OAuth 2.0] ─► Gmail REST API (PKCE + Token Encryption)
```

1. **Option A: Direct Gmail SMTP (Preferred & Recommended)**: Connect directly to `smtp.gmail.com:587` with STARTTLS using a 16-character Google App Password. Instant setup with zero Google Cloud Console configuration:
   ```env
   SMTP_HOST="smtp.gmail.com"
   SMTP_PORT=587
   SMTP_USER="your_email@gmail.com"
   SMTP_PASSWORD="your_16_char_app_password"
   SMTP_USE_TLS=True
   ```
2. **Option B: Google Cloud OAuth 2.0**: Connect via Gmail REST API using Proof Key for Code Exchange (PKCE) and Fernet token encryption at rest (`.leddro_encryption_key`). Send-only scope (`gmail.send`); never reads or indexes your inbox.

#### Delivery Safeguards
- **Strictly Single-Message Dispatch**: Zero bulk automation, no drip campaigns, and no automated dispatch triggers. Every send requires explicit human review and confirmation.
- **Header Injection Defenses**: Rejects any recipient, sender, or subject string containing carriage returns (`\r`), newlines (`\n`), or null bytes (`\0`).
- **Suppression Registry**: Automatically verifies target addresses against local `suppression_records` to prevent messaging unsubscribed contacts or blocked domains.
- **Uncertain State Handling**: Network timeouts during dispatch mark attempts as `uncertain` to prevent accidental duplicate sending.

---

## ⚙️ Configuration Reference (.env)

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

## 💾 Database, Backup & Recovery

### SQLite (Default)
Leddro maintains an SQLite database file at `leddro.db` in the repository root. All prospects, audit findings, draft emails, and history records persist automatically across server reboots. The database utilizes WAL (Write-Ahead Logging) mode for enhanced concurrency and durability.

### Atomic Backup & Recovery
Leddro includes a native Python backup engine in [backend/app/core/backup.py](backend/app/core/backup.py) utilizing the atomic SQLite online backup API (`sqlite3_backup`). This ensures zero corrupted bytes even while background writes occur.

```bash
# Create an atomic backup snapshot
npm run backup
# or via Python:
python -m backend.app.core.backup --backup

# Verify an existing backup integrity
python -m backend.app.core.backup --verify backups/your_backup_file.db

# Safe restore (validates PRAGMA integrity_check and takes a safety snapshot before restore)
python -m backend.app.core.backup --restore backups/your_backup_file.db
```

### Optional Neon Serverless PostgreSQL
To use cloud-hosted serverless PostgreSQL with Neon:
1. Copy your pooled connection string from the [Neon Console](https://console.neon.tech).
2. Set in `.env`:
   ```env
   DATABASE_URL="postgresql://user:password@ep-...neon.tech/neondb?sslmode=require"
   ```
3. Restart the backend. Leddro automatically applies table migrations and column checks.

---

## 🛡️ Privacy, Security, and Responsible Use

- **Local-First Boundary**: Secrets (`.env`, encryption keys, SQLite database) are never committed to version control and are ignored by `.gitignore`.
- **SSRF Defenses**: The audit crawler validates every target domain against DNS rebinding, private IP subnets (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`), and cloud metadata endpoints (`169.254.169.254`).
- **Prompt-Injection Defense**: Model prompts enclose untrusted crawled pages and business names in strict `<untrusted_prospect_data>` XML tags.
- **Strictly Single-Message Dispatch**: Leddro contains zero mass-mail sequences or automated dispatch triggers. Approving an email draft updates review status in SQLite only; dispatch requires explicit confirmation.
- **Suppression Registry**: Recipient emails and domains are verified against `suppression_records` to prevent messaging unsubscribed contacts.
- **Single-User Development Disclaimer**: Leddro is built for single-operator local use and does not contain multi-tenant user authentication. Do **not** expose the development server to untrusted public networks without reverse proxy authentication (e.g., HTTP Basic Auth or VPN).
- **Vulnerability Reporting**: See [SECURITY.md](SECURITY.md) for our coordinated vulnerability disclosure policy.

---

## 🔧 Troubleshooting

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

## 🔄 Updating Leddro

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

## 🧪 Testing and Development

Leddro maintains a comprehensive automated test suite with **206 passing tests** across backend services, CLI tools, and security layers:

```bash
# Run complete backend pytest suite (206 automated tests)
python -m pytest backend/tests/ -v

# Run zero-website deep search & multi-channel discovery test suite
python -m pytest backend/tests/test_deep_search_enrichment.py -v

# Run interactive CLI test suite
python -m pytest backend/tests/test_cli.py -v

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

# Run documentation integrity & anchor linter
npm run lint:readme
# or directly with Python:
python scripts/check_readme.py

# Run interactive terminal audit via CLI
python -m backend.app.cli audit https://example.com

# Run frontend TypeScript typecheck
npx tsc --noEmit

# Test production bundle compilation
npm run build

# Run frontend linter
npm run lint
```

### Test Suite Highlights
- `test_deep_search_enrichment.py`: 5-pillar zero-website discovery, DNS MX deliverability validation, aggregator domain filtering, FSSAI/GSTIN regex extractors, and mock multi-engine responses.
- `test_cli.py`: Terminal report generation, ANSI color styling, uncolored mode, `--json` serialization, score badge heuristics, and version flags.
- `test_prospect_scoring.py`: Determinism, score bounds [0, 100], no-audit handling, diagnostic failure handling, HTTPS status distinctions, finding severity weighting, duplicate findings deduplication, audit recency decay, contact readiness verification, evidence traceability, and query performance (N+1 elimination).
- `test_audit_comparison.py`: Four-way finding classification (RESOLVED, NEW, PERSISTENT, INCONCLUSIVE), positive-evidence rule enforcement, telemetry deltas, and cross-domain protection.
- `test_email_scraper.py`: Contact extraction, junk extension rejection, placeholder domain filtering, and DNS MX deliverability verification.
- `test_ai_drafting.py`: Fact-checking validation, prompt-injection defense, and fallback provider routing.
- `test_audit_engine.py`: HTTP status codes, malformed HTML, and response timeouts.
- `test_ssrf_validator.py`: Private IP blocking, cloud metadata blocks, and DNS rebinding prevention.
- `test_google_oauth_and_email.py`: Token encryption, PKCE verification, SMTP dispatch, header injection protection, uncertain delivery states, and duplicate-send prevention.
- `test_backup_and_recovery.py`: SQLite online backup, corruption recovery, and restoration.

---

## 🏗️ Project Architecture

```mermaid
flowchart TD
    User["Operator / Consultant"] <--> UI["React 19 + Vite Frontend"]
    User <--> CLI["Terminal CLI (python -m backend.app.cli)"]
    UI <--> API["FastAPI Backend Engine"]
    CLI <--> Audits["Website Audit Crawler (SSRF Protected)"]
    API <--> DB[("SQLite Database (leddro.db)")]
    API <--> Audits
    API <--> Contacts["Contact Crawler & DNS MX Verifier"]
    API <--> DeepSearch["Zero-Website Deep Search (Social, Dorking, WhatsApp, FSSAI)"]
    API <--> Discovery["OpenStreetMap & Google Places"]
    API <--> Hunter["Hunter.io B2B Email Finder"]
    API <--> AI["AI Engines (Gemini, OpenAI, Claude, Ollama)"]
    API <--> SMTP["Direct Gmail SMTP Gateway"]
    API <--> Gmail["Gmail API OAuth Gateway (Safe Single Send)"]
```

---

## 📁 Directory Structure

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
│   │   ├── services/       # Audit engine, comparison, contact scraper, deep search, SSRF & Gmail client
│   │   ├── cli.py          # Terminal CLI audit and diagnostic tool
│   │   └── main.py         # FastAPI application entry point
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # 206 automated pytest test cases
├── docs/
│   ├── screenshots/        # Verified application screenshots
│   └── sample_import.csv   # Annotated sample CSV import dataset
├── public/                 # Static assets & SVG icons
├── scripts/
│   └── check_readme.py     # Automated README anchor & asset link linter
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

## 🗺️ Roadmap

### Completed
- [x] **Phase 1-4**: Core architecture, diagnostic website audit engine, UI system & prospect discovery.
- [x] **Phase 5**: Evidence-based AI drafting with anti-hallucination verification.
- [x] **Phase 6**: Secure Google OAuth 2.0 with Fernet token encryption & safe email dispatch.
- [x] **Phase 7**: Production readiness, atomic SQLite backup/recovery, Neon PostgreSQL compatibility & CI pipeline.
- [x] **Phase 8.1-8.2**: Explainable heuristic scoring (Opportunity & Data Confidence) with full evidence traceability.
- [x] **Phase 8.3**: Website audit comparison & change detection engine with directional telemetry deltas.
- [x] **Contact Intelligence & Verification**: Autonomous website contact scraper, DNS MX mail verification, Hunter.io integration, Google Places API, Zero Fake Emails policy, and direct Phone/WhatsApp actions.
- [x] **Multi-Channel Zero-Website Discovery**: 5-pillar footprint scanner (Facebook, Instagram, Search Dorking, WhatsApp Business, Justdial/Zomato/Swiggy, FSSAI/GSTIN) with DNS MX deliverability verification.
- [x] **Terminal CLI Audit Engine**: Interactive command line interface (`python -m backend.app.cli audit`) with colored telemetry and `--json` support.
- [x] **CI Documentation & Asset Linter**: Automated anchor and relative asset validation in CI (`python scripts/check_readme.py`).
- [x] **Annotated CSV Import Dataset**: Standardized sample spreadsheet at [docs/sample_import.csv](docs/sample_import.csv).

### In Progress
- [ ] **Phase 9**: Premium documentation, developer onboarding excellence, and open-source release readiness.

### Planned
- [ ] **Scheduled Recurring Re-Audits**: Background periodic re-auditing with automated change diffs and email notifications.
- [ ] **Local LLM Sidecar**: Bundled `llama.cpp` sidecar for zero-dependency offline AI inference without requiring manual Ollama installation.

---

## 🤝 Contributing

We welcome community contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on setting up your local environment, coding standards, and submitting pull requests.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feat/my-improvement`).
3. Commit your changes (`git commit -m 'feat: add my improvement'`).
4. Ensure all tests pass (`python -m pytest backend/tests/` and `npm run build`).
5. Open a Pull Request.

---

## 🔒 Security Disclosures

Please review our [SECURITY.md](SECURITY.md) for vulnerability reporting guidelines. If you discover a security issue or potential vulnerability, please report it responsibly by opening a confidential advisory or contacting the maintainers directly. Do **not** disclose security vulnerabilities in public GitHub issues.

Automated security checks and secret scanning run on every pull request via Gitleaks in our GitHub Actions CI pipeline.

---

## 📄 License and Acknowledgements

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

- OpenStreetMap data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), licensed under ODbL 1.0.
- Icons by [Lucide](https://lucide.dev/).
- Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), and [Tailwind CSS](https://tailwindcss.com/).
