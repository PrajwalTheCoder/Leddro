# Leddro

> **Discover prospects. Audit websites. Prepare evidence-based outreach. Keep control of your workflow.**

[![MIT License](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB.svg)](https://react.dev/)
[![SQLite Local](https://img.shields.io/badge/Database-SQLite%20(Default)-blueviolet.svg)](https://www.sqlite.org/)

Leddro is an open-source, local-first intelligence platform for finding local commercial businesses, performing technical diagnostic audits on their websites, and generating factual, evidence-backed outreach proposals.

Unlike conventional mass-scraping or generic email blast tools, Leddro anchors every outreach suggestion directly to deterministic technical findings—such as expired SSL/TLS certificates, DNS misconfigurations, slow server responses, broken links, or missing mobile viewport declarations.

---

## Table of Contents

- [What Is Leddro?](#what-is-leddro)
- [Why Leddro?](#why-leddro)
- [Features](#features)
- [Screenshots & Interface Tour](#screenshots--interface-tour)
- [System Requirements](#system-requirements)
- [Installation: Quick Start](#installation-quick-start)
- [Running the Application](#running-the-application)
- [First-Run Experience: Try This First](#first-run-experience-try-this-first)
- [Using Leddro Without AI](#using-leddro-without-ai)
- [Configuring AI Providers](#configuring-ai-providers)
- [Google OAuth & Gmail Setup (Optional)](#google-oauth--gmail-setup-optional)
- [Configuration Reference (.env)](#configuration-reference-env)
- [Database & Data Storage](#database--data-storage)
- [Privacy, Security & Responsible Use](#privacy-security--responsible-use)
- [Troubleshooting](#troubleshooting)
- [Updating Leddro](#updating-leddro)
- [Testing & Development](#testing--development)
- [Project Architecture](#project-architecture)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security Disclosures](#security-disclosures)
- [License & Acknowledgments](#license--acknowledgments)

---

## What Is Leddro?

Leddro connects discovery, technical verification, and outreach preparation into a unified desktop workspace:

```
[1. Discover / Import] ──► [2. Technical Audit] ──► [3. Evidence-Backed AI Draft] ──► [4. Human Review & Dispatch]
     OpenStreetMap              DNS Resolution              Factual Claim Mapping                  Zero Bulk Send
      CSV Upload               TLS / SSL Validity             Anti-Hallucination               Explicit Confirmation
   Manual Additions           HTTP & DOM Telemetry           Provider Choice                    Suppression Defense
```

### The 8-Step Workflow

1. **Discover or import prospects**: Search local businesses via OpenStreetMap (Overpass & Nominatim) or import existing contacts via structured CSV.
2. **Review business profiles**: View business location, categorized trade, registered web address, and phone details.
3. **Audit the website**: Run real server-side diagnostic probes checking DNS zone records, TLS certificates, HTTP response status, TTFB latency, and HTML DOM metadata.
4. **Inspect deterministic findings**: Review classified severity levels (Critical, Warning, Info) backed by exact timestamps, HTTP dumps, and rationale.
5. **Generate an outreach draft**: Request a personalized proposal from a configured AI engine (Google Gemini, OpenAI, Anthropic Claude, or local Ollama). Every technical claim is strictly cross-referenced against audit findings in your local database.
6. **Review and edit the draft**: Tweak the subject line, body text, and tone directly in the visual Draft Studio.
7. **Send an individual email**: If Google OAuth is connected, dispatch a single personalized consultation email via the Gmail API after explicit review. (Bulk sending and automated loops are strictly prevented).
8. **Track history and preserve records**: Maintain complete local audit logs, send histories, and suppression lists in your local database.

---

## Why Leddro?

Traditional B2B outreach tools rely on generic scraped email lists, automated cold spamming, and hallucinated personalization snippets. Leddro takes the opposite approach:

| Feature / Philosophy | Conventional Outreach Tools | Leddro Approach |
| :--- | :--- | :--- |
| **Data Storage** | Cloud database owned by vendor | **Local-First SQLite** stored on your device by default |
| **Outreach Personalization** | Generic AI templates ("I noticed your website...") | **Deterministic Evidence** citing exact DNS, SSL, or DOM findings |
| **Anti-Hallucination** | None; AI models invent claims | **Claim Verification**: Unverified claims are flagged for manual review |
| **Email Dispatch** | Bulk sequence automation & auto-dialers | **Strictly Single-Message**: Human approval required for every send |
| **Cost & Subscriptions** | High recurring monthly SaaS fees | **100% Free & Open Source** (runs on free-tier APIs or local Ollama) |
| **Privacy Scope** | Vendor inspects and logs your database | **Zero Third-Party Database Tracking**: Code is open and inspectable |

---

## Features

### 🔍 Prospect Discovery
- **OpenStreetMap Integration**: Query real local businesses using Overpass API and Nominatim geocoding with zero API keys required.
- **CSV Batch Import**: Import existing CSV prospect datasets with automatic column mapping, duplicate detection, and formula injection defenses.
- **Manual Additions**: Add targeted individual prospects with instant domain normalization.
- **Opportunity Scoring**: Automatically prioritize prospects based on technical urgency, commercial intent, and resolution ease.

### 🛡️ Website Auditing & Telemetry
- **DNS Zone Inspection**: Query A, AAAA, MX, and NS records with millisecond resolution timing.
- **TLS / SSL Certificate Verification**: Inspect certificate authority, expiry countdown, protocol version (TLSv1.2/TLSv1.3), and cipher suites.
- **HTTP Reachability & TTFB**: Measure raw socket connect latency, Time To First Byte (TTFB), status codes (200, 301, 404, 503), and server headers.
- **HTML DOM Diagnostics**: Detect responsive mobile viewport declarations, `<title>` tags, meta descriptions, and OpenGraph snippet cards.
- **SSRF Network Security**: Outbound audit crawlers strictly block loopback (`127.0.0.1`), private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud metadata IP endpoints (`169.254.169.254`).

### 🤖 Evidence-Aware AI Drafting
- **Multi-Provider Architecture**: Use Google Gemini (free tier via Google AI Studio), OpenAI, Anthropic Claude, or local Ollama with zero code changes.
- **In-Modal Provider Switcher**: Toggle engines directly inside the draft generation modal.
- **Factual Claim Mapping**: Every technical assertion is matched to a real database finding ID. If a claim lacks authentic evidence, it is automatically downgraded and flagged for operator review.
- **Prompt-Injection Containment**: Untrusted HTML crawl contents and business tags are enclosed in isolated `<untrusted_prospect_data>` delimiters.
- **Custom Operator Guidance**: Provide up to 500 characters of custom guidance, select outreach purposes (Website Improvement, Modernization, Maintenance), and adjust writing tones (Professional, Friendly, Concise, Consultative).

### ✉️ Gmail Integration & Safe Dispatch
- **Google OAuth 2.0 with PKCE**: Authorize directly with Google using Proof Key for Code Exchange and cryptographic CSRF state verification.
- **Fernet Token Encryption**: Sensitive OAuth refresh tokens are encrypted at rest using AES-128-CBC + HMAC-SHA256 (`.leddro_encryption_key`).
- **Individual Dispatch Only**: No background loops or bulk-send operations.
- **Suppression Registry**: Automatically blocks dispatches to opted-out addresses or blocked domains.
- **State Reconciliation**: Network timeouts mark send attempts as `uncertain` to prevent accidental duplicate dispatches.

### 💾 Data Safety & Infrastructure
- **Local-First SQLite**: Everything runs locally in `leddro.db` out of the box.
- **Atomic Online Backups**: Native SQLite backup API (`sqlite3_backup`) creates consistent snapshot backups without locking active writes.
- **Integrity Validation**: Automated `PRAGMA integrity_check` before any database restoration.
- **Optional Neon PostgreSQL**: Switch to cloud auto-scaling serverless PostgreSQL simply by updating `DATABASE_URL`.

---

## Screenshots & Interface Tour

The following genuine screenshots were captured from a live Leddro workspace:

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
| **Disk Space** | ~500 MB (codebase, virtualenv & dependencies) | 1 GB free |
| **Network** | Internet access for audits & external APIs | Active broadband connection |

### Verify Your Installed Versions

Run these commands in your terminal:

```bash
git --version
python --version   # (On macOS/Linux, use python3 --version)
node --version
npm --version
```

---

## Installation: Quick Start

Follow these verified steps to set up Leddro from scratch:

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

*(Out of the box, `.env` is preconfigured to use SQLite locally at `leddro.db`. You do not need an API key or cloud database to run the app).*

### 4. Frontend Setup (React & Vite)

In the same repository root:

```bash
npm install
```

---

## Running the Application

Leddro consists of two processes running concurrently: the **FastAPI backend** on port `8000` and the **Vite dev server** on port `5173`.

### Terminal 1: Start Backend API

Activate your virtual environment and launch Uvicorn:

#### Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### macOS / Linux:
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

*Expected output:*
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Initializing Leddro SQLite database schema...
INFO:     Database already contains prospects.
INFO:     Leddro backend engine initialized successfully.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### Terminal 2: Start Frontend Application

In a separate terminal window at the project root:

```bash
npm run dev
```

*Expected output:*
```
  VITE v8.3.4  ready in 450 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

Open your browser and navigate to **`http://localhost:5173`**. The Vite dev server automatically proxies all `/api/*` calls to the FastAPI backend.

---

## First-Run Experience: Try This First

Follow this zero-credential quick path to experience the core workflow in under 2 minutes:

1. **Open the Dashboard**: Navigate to `http://localhost:5173`. You will see the Command Center populated with 5 initial demonstration prospects.
2. **Execute an Audit**:
   - Go to **Prospects** in the sidebar.
   - Locate **Northstar Interiors** or **Willow Studio**.
   - Click the **Audit** button.
   - Watch the real-time probe check DNS, inspect TLS certificates, and analyze DOM structure.
3. **Inspect Findings**:
   - Navigate to **Technical Audits** to view the findings (e.g., certificate validity, mobile viewport declarations, missing meta description).
4. **Draft Outreach**:
   - Click **Generate Draft** on the audited prospect.
   - If an AI provider is configured (such as free Google Gemini), click **Generate Email Draft**.
   - The AI will compose a polite letter quoting the observed audit evidence.
5. **Edit the Draft**:
   - Navigate to **Draft Studio** (`/drafts`) to refine the email copy and review alternative subject lines.

---

## Using Leddro Without AI

**You do NOT need an AI API key to use Leddro.** 

Without an AI provider configured:
- ✅ **Prospect Discovery**: Fully functional using OpenStreetMap and CSV imports.
- ✅ **Website Auditing**: Fully functional. Performs live DNS queries, TLS handshakes, HTTP crawl checks, and DOM evaluations.
- ✅ **Record Management**: Fully functional. Track prospect statuses, opportunity scores, and notes in your local SQLite database.
- ✅ **Manual Outreach Drafting**: Fully functional. Write and save drafts manually in Draft Studio.
- ❌ **Automated AI Synthesis**: Requires at least one configured AI provider (Google Gemini free tier, OpenAI, Anthropic, or local Ollama).

---

## Configuring AI Providers

Leddro supports 4 interchangeable AI providers. You only need to configure **one**:

| Provider | Pricing / Tier | Default Model | Data Transmission Scope |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | **100% Free Tier Available** via Google AI Studio | `gemini-3.5-flash-lite` | Minimal business & audit finding titles sent to Google API servers |
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
3. Or configure it directly in the app UI at **Integrations** (`/integrations`).

### 2. Local Ollama (Zero External Transfer)
1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull a model in your terminal: `ollama run llama3`.
3. Set in `.env`:
   ```env
   AI_PROVIDER="compatible"
   COMPATIBLE_BASE_URL="http://localhost:11434/v1"
   COMPATIBLE_MODEL="llama3"
   ```
4. No API key is required. All processing remains on your machine.

---

## Google OAuth & Gmail Setup (Optional)

> **Advanced & Optional**: You can use discovery, auditing, and AI drafting without configuring Google OAuth. Only configure Gmail if you intend to send real individual consultation emails directly from the app.

### 11-Step Setup Guide

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

## Configuration Reference (.env)

| Variable | Required? | Purpose | Safe Example / Default |
| :--- | :---: | :--- | :--- |
| `DATABASE_URL` | **Yes** | Database connection string | `sqlite:///./leddro.db` |
| `AI_PROVIDER` | No | Active engine (`gemini`, `openai`, `anthropic`, `compatible`) | `gemini` |
| `GEMINI_API_KEY` | No | API key for Google Gemini | `replace_with_your_gemini_key` |
| `GEMINI_MODEL` | No | Gemini model identifier | `gemini-3.5-flash-lite` |
| `OPENAI_API_KEY` | No | API key for OpenAI GPT models | `replace_with_your_openai_key` |
| `OPENAI_MODEL` | No | OpenAI model identifier | `gpt-4o-mini` |
| `ANTHROPIC_API_KEY` | No | API key for Anthropic Claude models | `replace_with_your_anthropic_key` |
| `ANTHROPIC_MODEL` | No | Anthropic model identifier | `claude-3-5-haiku-20241022` |
| `COMPATIBLE_BASE_URL`| No | REST URL for local Ollama / vLLM | `http://localhost:11434/v1` |
| `COMPATIBLE_MODEL` | No | Model name for local Ollama | `llama3` |
| `GOOGLE_CLIENT_ID` | No | OAuth 2.0 Web Client ID | `replace_with_client_id.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET`| No | OAuth 2.0 Web Client Secret | `replace_with_client_secret` |
| `GOOGLE_REDIRECT_URI` | No | Callback endpoint matching Google Console | `http://localhost:8000/api/google/callback` |
| `FRONTEND_URL` | No | Frontend origin allowed by CORS | `http://localhost:5173` |
| `CREDENTIAL_ENCRYPTION_KEY` | No | 32-urlsafe base64 key for token encryption | `(Auto-generated in .leddro_encryption_key if blank)` |
| `OSM_OVERPASS_URL` | No | Public endpoint for Overpass API | `https://overpass-api.de/api/interpreter` |
| `OSM_NOMINATIM_URL`| No | Public endpoint for Nominatim search | `https://nominatim.openstreetmap.org/search` |

---

## Database & Data Storage

### SQLite (Default)
By default, Leddro creates and maintains an SQLite database file at `leddro.db` in the repository root. All prospects, audit findings, draft emails, and history records persist automatically across server reboots.

### Atomic Backup & Recovery
Leddro includes a native Python backup engine in [backend/app/core/backup.py](backend/app/core/backup.py) utilizing the atomic SQLite online backup API (`sqlite3_backup`). This ensures zero corrupted bytes even while background writes occur.

#### Create a Backup:
```powershell
# Windows PowerShell:
.\.venv\Scripts\python.exe -c "from backend.app.core.backup import backup_sqlite_database; print('Backup saved:', backup_sqlite_database())"

# macOS / Linux:
python3 -c "from backend.app.core.backup import backup_sqlite_database; print('Backup saved:', backup_sqlite_database())"
```
Backups are saved to the `backups/` directory with UTC timestamps (e.g., `backups/leddro_backup_20261018_120000.db`).

#### Restore from Backup:
```powershell
# Validates PRAGMA integrity_check and takes a safety snapshot before overwriting
.\.venv\Scripts\python.exe -c "from pathlib import Path; from backend.app.core.backup import restore_sqlite_database; restore_sqlite_database(Path('backups/your_backup_file.db'))"
```

### Optional Neon Serverless PostgreSQL
To use cloud-hosted PostgreSQL with Neon:
1. Copy your pooled connection string from the [Neon Console](https://console.neon.tech).
2. Set in `.env`:
   ```env
   DATABASE_URL="postgresql://user:password@ep-...neon.tech/neondb?sslmode=require"
   ```
3. Restart the backend. Leddro automatically applies table migrations and column checks.

---

## Privacy, Security & Responsible Use

- **Local-First Boundary**: Secrets (`.env`, encryption keys, SQLite database) are never committed to version control and are ignored by `.gitignore`.
- **SSRF Defenses**: The audit crawler validates every target domain against DNS rebinding, private IP subnets (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`), and cloud metadata (`169.254.169.254`).
- **Prompt-Injection Defense**: Model prompts enclose untrusted crawl pages and business names in strict `<untrusted_prospect_data>` and `<untrusted_audit_data>` tags.
- **Strictly Single-Message Dispatch**: Leddro contains zero mass-mail sequences or automated dispatch triggers. Approving an email draft updates review status in SQLite only; dispatch requires explicit confirmation.
- **Suppression Registry**: Recipient emails and domains are verified against `suppression_records` to prevent messaging unsubscribed contacts.

---

## Troubleshooting

| Problem | Likely Cause | Diagnosis & Solution |
| :--- | :--- | :--- |
| **`python: command not found`** | Python not installed or not in PATH | Use `python3` on Linux/macOS or verify Python was installed with the "Add Python to PATH" option checked on Windows. |
| **`pip install -r backend/requirements.txt` fails** | Outdated pip or missing C compiler for psycopg2 | Run `python -m pip install --upgrade pip`. `psycopg2-binary` provides precompiled wheels. |
| **`npm run dev` fails with module error** | Incomplete npm installation | Run `npm install` or `npm ci` in the repository root. Ensure Node.js is version 20+. |
| **Frontend displays "Backend Offline"** | FastAPI server not running on port 8000 | Verify Terminal 1 is running `uvicorn backend.app.main:app --port 8000`. Test `http://127.0.0.1:8000/api/health` directly in your browser. |
| **Port 8000 or 5173 already in use** | A previous instance is still running | Find and terminate the dangling process, or start Uvicorn on another port (e.g., `--port 8001`) and update `vite.config.ts`. |
| **AI Draft displays "Missing Configuration"** | Active engine has no API key in `.env` | Select **Google Gemini (Flash & Pro)** in the in-modal dropdown if you have a Gemini key, or add your key to `.env` or the **Integrations** page. |
| **Google OAuth Redirect URI Mismatch** | Redirect URL doesn't match Google Cloud Console | Ensure Google Console contains the exact URI: `http://localhost:8000/api/google/callback` (check port, scheme, and trailing slashes). |
| **SSRF Policy URL Rejected** | Target URL resolves to localhost or private IP | Auditing localhost or private RFC1918 IPs is blocked by design for security. Test with public URLs (e.g., `https://example.com`). |

---

## Updating Leddro

To pull the latest updates from GitHub without losing your local configuration:

```bash
# 1. Back up your local database first
.\.venv\Scripts\python.exe -c "from backend.app.core.backup import backup_sqlite_database; backup_sqlite_database()"

# 2. Pull updates
git pull origin main

# 3. Update dependencies
pip install -r backend/requirements.txt
npm install

# 4. Restart backend and frontend servers
```

*(Your local `.env` and `leddro.db` files are ignored by Git and will not be overwritten by `git pull`).*

---

## Testing & Development

Leddro maintains a comprehensive automated test suite:

```bash
# Run complete backend pytest suite (88 automated tests)
pytest backend/tests/ -v

# Run frontend TypeScript typecheck
npx tsc --noEmit

# Test production bundle compilation
npm run build

# Run frontend linter
npm run lint
```

### Test Coverage Highlights
- `test_ai_drafting.py`: Fact-checking validation, prompt-injection defense, and fallback routing.
- `test_audit_engine.py`: HTTP status codes, malformed HTML, and response timeouts.
- `test_ssrf_validator.py`: Private IP blocking, cloud metadata blocks, and DNS rebinding prevention.
- `test_google_oauth_and_email.py`: Token encryption, PKCE verification, and duplicate-send prevention.
- `test_backup_and_recovery.py`: SQLite online backup, corruption recovery, and restoration.

---

## Project Architecture

```mermaid
flowchart TD
    User([Operator / Consultant]) <--> UI[React 19 + Vite Frontend]
    UI <--> API[FastAPI Backend Engine]
    API <--> DB[(SQLite Database\nleddro.db)]
    API <--> Audits[Website Audit Crawler\nSSRF Protected]
    API <--> Discovery[OpenStreetMap\nOverpass & Nominatim]
    API <--> AI[AI Engines\nGemini / OpenAI / Ollama]
    API <--> Gmail[Gmail API Gateway\nSingle Send with Confirmation]
```

### Directory Structure
```
Leddro/
├── backend/
│   ├── app/
│   │   ├── ai/             # AI providers, prompts & claim validation
│   │   ├── api/            # FastAPI REST routers (/prospects, /audits, /drafts)
│   │   ├── core/           # Config, database engine, security & backup
│   │   ├── discovery/      # OSM Overpass, Google Places & CSV normalization
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Audit engine, SSRF validator & Gmail client
│   │   └── main.py         # FastAPI application entry point
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # 88 automated pytest test cases
├── docs/
│   └── screenshots/        # Verified application screenshots
├── public/                 # Static assets & SVG icons
├── src/
│   ├── components/         # Modals, buttons, badges, navigation
│   ├── context/            # React AppContext global state
│   ├── pages/              # Overview, Prospects, Audits, Drafts, Integrations
│   └── App.tsx             # Application routing
├── .env.example            # Sanitized configuration template
├── package.json            # Node.js dependencies & scripts
├── vite.config.ts          # Vite configuration & backend proxy
└── README.md               # Product documentation
```

---

## Roadmap

- [x] **Phase 1-4**: Core architecture, website audit engine, UI system & prospect discovery.
- [x] **Phase 5**: Evidence-based AI drafting with anti-hallucination verification.
- [x] **Phase 6**: Secure Google OAuth 2.0 with Fernet token encryption & safe email dispatch.
- [x] **Phase 7**: Production readiness, SQLite backup/recovery, Neon PostgreSQL compatibility & CI pipeline.
- [ ] **Phase 8 (Planned)**: Scheduled recurring website re-audits with diff notifications.
- [ ] **Phase 9 (Planned)**: Local LLM one-click packaging via bundled llama.cpp sidecar.

---

## Contributing

We welcome community contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on setting up your local environment, coding standards, and submitting pull requests.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feat/my-improvement`).
3. Commit your changes (`git commit -m 'feat: add my improvement'`).
4. Ensure all tests pass (`pytest backend/tests/` and `npm run build`).
5. Open a Pull Request.

---

## Security Disclosures

Please review our [SECURITY.md](SECURITY.md) for vulnerability reporting guidelines. If you discover a security issue or potential vulnerability, please report it responsibly by opening a confidential advisory or contacting the maintainers directly. Do **not** disclose security vulnerabilities in public GitHub issues.

---

## License & Acknowledgments

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

- OpenStreetMap data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), licensed under ODbL 1.0.
- Icons by [Lucide](https://lucide.dev/).
- Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), and [Tailwind CSS](https://tailwindcss.com/).
