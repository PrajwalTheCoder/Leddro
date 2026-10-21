# Leddro Reality Check 3.0 — Report

Date: 2026-10-22 (local). Repository: `PrajwalTheCoder/Leddro`, branch `main`.

> **Reading guide.** Everything marked **[measured]** was actually run and observed in this session.
> **[heuristic]** means produced by Leddro's own classifier with no independent ground truth.
> **[fixture]** means synthetic test data. **[not done]** means not performed, stated honestly in §12.

## 1. Executive Summary

**Fixed (code + regression tests):**

- Business↔website identity is now an explicit, evidence-bearing status (`verified`, `likely_match`, `uncertain`, `conflicting`, `not_found`, `not_checked`), persisted and migrated backward-compatibly.
- Directory/aggregator domains (e.g. a justdial-style domain) and discontinued `*.business.site` domains are flagged `conflicting`. Name similarity alone can reach only `likely_match`, never `verified`.
- Contact provenance (`official_source`, `corroborated`, `provider_verified`, `third_party_candidate`, `unverified`, `conflicting`) is stored per prospect. MX records are never treated as mailbox confirmation (`mailbox_confirmed` is always `false` today).
- Blogger and aggregator-helpdesk emails are `conflicting`. Search-snippet emails remain `unverified`. CSV/manual imports are no longer labelled as official-website sourced. Drafts only auto-receive an address when its provenance is trustworthy.
- Social-profile matching module added (`reciprocal_match`/`strong_match`/`uncertain_match`/`incorrect_match`/`not_found`). A failed search is no longer expressed as 90%-confidence "absence".
- Scoring: audit findings are excluded when website identity is `conflicting`/`uncertain`. Contact trust levels are treated differently in confidence. Transient resolver failures are not counted as DNS defects. A create-vs-detail scoring inconsistency was found and fixed.
- TTFB is now a median of up to 3 sequential, SSRF-validated probes. A single slow probe produces only a low-severity "incomplete measurement" note.
- AI prompt now receives structured identity/contact/social evidence. It withholds the website URL and audit findings when identity is `conflicting`/`uncertain`. It labels the email trust level and lists only confirmed social profiles.
- UI: new "Evidence & Trust" panel in the prospect dossier (identity, email source vs. trust, social matches, reasons for uncertainty, expandable evidence). Misleading copy removed ("Discovered verified email", "Verified via Deep Search", "DNS MX Deliverable"). Deep-search API errors now explain what happened.

**Not fixed / not done:** see §12. Most importantly: no independent ground-truth verification of a 30-business live sample was performed; reciprocal social links are not auto-detected in production paths; discovery coverage metrics were not added.

## 2. Environment and Git State

| Item | Value |
|---|---|
| Starting commit | `53e45c9` (matched the expected commit; `HEAD...origin/main` = 0/0 at start) |
| Branch | `main` (no other branches / PRs created) |
| Final commit / push | see §13 and the final chat message (a file cannot contain its own commit hash) |
| Python | 3.13.7 |
| Node | v22.19.0 |
| Working tree at validation time | only intended files modified (listed in §13); `leddro.db` untouched/untracked |

## 3. Business Identity Accuracy

**Sample actually used: 32 prospects in the local `leddro.db`, read-only. This is not an independently verified 30-business sample. [heuristic]**

- Locations: Navi Mumbai 8, Thane 4, Panvel 4, Mumbai 4, Vasai-Virar 1, Pune 1, Fort 2, A Ward 2, plus 6 US-city rows that are seeded **[fixture]** data.
- Categories: Restaurant 18, Cafe 4, others 10 (interior design, architecture, manufacturing, etc.).
- 15 of 32 have a website URL. Several of those are `*.example.com` or `example.com` **fixtures**.

Classifier output on the 32 records (post-fix) **[heuristic, measured]**:

| Status | Count |
|---|---|
| `not_found` (no website returned by discovery; absence **not** confirmed) | 17 |
| `likely_match` | 5 |
| `uncertain` | 8 |
| `conflicting` | 2 |
| `verified` | 0 (by design, name similarity alone cannot verify) |

Concrete cases:

- `Sarvi Restaurant` → `justdail.com`: `conflicting` (directory-style domain).
- `Cafe Universal` → `*.business.site`: `conflicting` (platform discontinued).
- `Krabi Multi-cuisine Restaurant` → `silveroakuran.com`: `uncertain` (zero name tokens in common; flagged for review, **not** proven wrong).
- `Cafe Leopold`, `Cafe Mondegar`, `Creeda Board Game Cafe`, `Triospice`, `Aura Spatial Consultants`: `likely_match` (domain tokens match the name; ownership **not** independently confirmed).

I did **not** independently confirm any of these against live sources (official-site contact page, registries, search results). No WHOIS/registry ownership claims are made. A real-world precision/recall figure for identity cannot be given.

Design decisions on honesty:

- Zero-similarity domains were initially `conflicting` in my first implementation. I downgraded them to `uncertain`, because brands legitimately use unrelated domains (parent groups), and that was an over-claim.
- "No website returned" is stored as `not_found` with `claim: no_website_discovered` and low confidence (0.3). It explicitly states it does not confirm absence.

## 4. Contact Discovery Accuracy

**[measured, test fixtures]** — no live contact discovery sweep was run, and no email was sent.

- Provenance classification logic verified by tests: blogger address → `conflicting`; `support@` aggregator → `conflicting`; search-snippet → `unverified`; directory → `third_party_candidate`; imported → never `official_source`; official-website source with `conflicting`/`uncertain` site identity → downgraded to `unverified`; MX true but `mailbox_confirmed` false.
- Bug found and fixed: `classify` was called from discovery with `official_website` for non-OSM providers (so CSV/manual emails were labelled "official"); the website-scraper path auto-filled draft recipients regardless of provenance; "Verified email already on file" was claimed for any stored email.
- Keyword false positive fixed: `seats@…` matched the blogger keyword `eats`; `eats`/`bites`/`tales` were removed from the list. (This heuristic is still keyword-based and imperfect.)
- Hunter.io: path records `provider_verified` + provider score; Hunter was **not queried live** in this session (not configured/verified here), so provider coverage is **[not done]**.
- Provenance persistence is JSON in a new `contact_provenance` column. It is covered by an API create→re-read test and a migration test. A real backend-process restart was not performed; persistence is via the SQLite column read back through a fresh request.

## 5. Social Profile Matching

- New `social_matcher.py` with statuses `reciprocal_match`, `strong_match`, `uncertain_match`, `incorrect_match`, `not_found`.
- **[measured]** unit tests: fan-page handle → `incorrect_match`; unrelated handle → `uncertain_match`; failed search → `not_found` with confidence ≤ 0.5 and wording "does not prove"; a business that legitimately has "Club" in its name is no longer flagged as a fan page.
- **Gap:** `reciprocal_link_found` is only set by callers/tests. No production path currently fetches a website or profile to detect reciprocal links, so `reciprocal_match` never occurs in real use today. Handle-vs-name matching yields at most `strong_match`, which is circumstantial.
- Profiles discovered/matched counts on real businesses: **[not done]**.
- The UI shows platform, URL, status, evidence, contradicting info, last-checked time, with uncertain/wrong matches visually distinct from confirmed matches.

## 6. Website Audit Accuracy

- Existing audit regression tests (HTTP 404/5xx handling, apex DMARC domain, single-probe TTFB caveat, redirect/SSRF limits) all pass **[measured]** (`test_audit_engine.py` 14 tests, within full suite).
- Existing code review: 403/429 produce no site-defect finding (confirmed by reading); HTML inspection is guarded on HTTP errors (commit `53e45c9`).
- New: 3-probe median TTFB with per-probe SSRF re-validation; incomplete measurement is reported as a low-severity note; failures are recorded as error strings. Test: a probe blocked by SSRF validation records an error and makes no request. The full multi-probe happy path is **not** covered by an automated test, and **no live TTFB measurements were taken**.
- **[not done]:** the independently-checked 10-website live audit sample, TP/FP/FN counts, TLS expired/hostname-mismatch live tests, public-suffix handling review beyond what the existing tests cover. No precision/recall is claimed.

## 7. Scoring Validation

Tests added **[measured, pass]** for the invariants:

- Conflicting identity excludes findings (opportunity 0) and lowers confidence; uncertain lowers confidence.
- Missing audit adds no defect points (`Needs Audit`).
- Missing contact never raises opportunity; it lowers confidence.
- Transient DNS resolver failure is not a confirmed `dns_failure`.
- Contact trust: official > unverified > conflicting for confidence.
- Duplicate findings don't inflate; scores stay in 0–100 / confidence in 10–100.
- Create and detail endpoints now agree (previously a mismatch, which was a real defect).

Example breakdown (fixture "Test Bistro", same findings: 1 high "missing viewport" + 1 HTTP 500):

| Identity | Opportunity | Confidence | Why |
|---|---|---|---|
| verified | > 0 | higher | findings attributed to the business |
| conflicting | 0 | lower (−30) | domain ownership unconfirmed, findings excluded |

Known design caveat: with no website at all, 15 opportunity points are still awarded ("no website discovered"). This was preserved for backward compatibility, but it is an *unconfirmed* opportunity, and is flagged in limitations.

## 8. AI Draft Integrity

- **7 scenarios tested at the prompt-construction level [measured]**: verified+findings; incomplete audit; no website; conflicting website (URL and audit withheld); uncertain email (labelled unverified, mailbox unconfirmed); uncertain social (not listed as the business's); no contact info.
- These tests verify what evidence is *given to* the model. **No live AI provider was called**, so actual model compliance is not measured. Existing `validate_and_filter_claims` (post-generation fact-check) is unchanged and its existing tests pass.
- No draft was sent; send paths were not exercised. AI-provider availability: **[not done]**.

## 9. Security and Safety Regression

All existing security suites pass within the full run **[measured]**: `test_ssrf_validator.py` (26), `test_ssrf_real_network_integration.py` (8), `test_google_oauth_and_email.py` (26: header injection, recipients, suppression, duplicates, confirmation), `test_reliability_phase84.py` (31), `test_integration_phase85.py` (11).

- New TTFB probes reuse `validate_target_url` + `SSRFProtectedTransport` + pinned IP, with no redirect following. A test confirms a blocked target is not requested.
- No security control was weakened. No credentials were printed or committed. No email was sent.
- I did not write additional new redirect/rebinding tests beyond the existing suites.

## 10. Test Suite Results (all **[measured]**)

| Check | Result |
|---|---|
| Backend `pytest` (full) | **276 passed, 0 failed, 0 skipped**, exit 0 (baseline before changes: 239 passed) |
| New `test_reality_check_3.py` | 37 passed |
| Integration (`test_ssrf_real_network_integration`, `test_integration_phase85`) | passed as part of the full suite |
| TypeScript (`tsc --noEmit`) | exit 0 |
| Frontend lint (`npm run lint`) | exit 0: **0 errors, 116 warnings** (warnings not compared against a pre-change count) |
| Production build (`npm run build`) | exit 0 (chunk-size warning only) |
| Migration test (temp SQLite, legacy table, idempotent) | passed |
| Live provider tests | **not run** |

An intermediate run during development showed 1 failure (`test_api_list_and_detail_consistency`); it exposed the create-vs-detail scoring bug, fixed before the final run.

## 11. Before-and-After Comparison

- Test counts: 239 → 276 passing (+37 new). This is coverage, not accuracy.
- Local-DB classification: **before** there was no identity status (all `not_checked`); **after** the distribution is in §3. This shows that the classifier flags 2 conflicting + 8 uncertain websites for operator review. It does **not** show improved accuracy, because there is no ground truth.
- No accuracy improvement is claimed.

## 12. Remaining Limitations (by severity)

1. **High:** No independent ground-truth verification of a live 30-business sample, or of 10 live websites. Identity and audit accuracy are unmeasured.
2. **High:** `likely_match` still rests on domain/name token similarity only. There is no content fetch (address/phone/menu on the site), so `verified` is effectively unreachable except via operator override.
3. **High:** Reciprocal social-link detection is not wired into production paths.
4. **Medium:** Phase 7 discovery coverage metrics (raw vs verified volume, per-provider failures) were not added. The existing provider tests (`test_discovery_providers.py`, 15) pass, but I didn't extend them to all listed failure modes (403/429/5xx/malformed) or add a coverage report.
5. **Medium:** Blogger/aggregator email detection is keyword-based.
6. **Medium:** `mailbox_confirmed` is always `false`. There is no SMTP-level or provider confirmation flow.
7. **Medium:** AI compliance with the new prompt gating is untested against live models.
8. **Low:** The 15-point "no website discovered" opportunity remains; the frontend list views (Prospects table) were not updated to show identity status, only the dossier.
9. **Low:** Lint has 116 pre-existing-style warnings; browser/UI behavior (refresh, loading/empty states) was validated only by build/type-check, not a manual browser run.

## 13. Commit and Remote Verification

Files changed (intended set):

- Backend: `ai/prompts.py`, `ai/service.py`, `api/enrichment.py`, `api/prospects.py`, `core/database.py`, `discovery/service.py`, `models/prospect.py`, `schemas/prospect.py`, `services/audit_engine.py`, `services/deep_search_enrichment.py`, `services/email_scraper.py`, `services/prospect_scoring.py`
- New backend: `services/contact_provenance.py`, `services/domain_utils.py`, `services/identity_verifier.py`, `services/social_matcher.py`, `tests/test_reality_check_3.py`
- Frontend: `src/types/index.ts`, `src/components/common/ProspectDetailModal.tsx`, new `src/components/common/EvidenceTrustPanel.tsx`
- Docs: `docs/reports/reality_check_3_report.md`

Commit hash, push result and final working-tree status are reported in the final chat message after `git push` is verified.
