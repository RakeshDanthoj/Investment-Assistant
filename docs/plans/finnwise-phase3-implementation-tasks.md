# FinnWise — Phase 3 Implementation Tasks (Intelligence Deepening, Months 10–18)

_Source PRD_: `FinnWise_PRD_v3_Final.md` — Section 10 / Phase 3, with binding decisions in §6, §7, §11, §12, §14.
_generated for independent execution without prd-planner_

## Overview

- **Summary**: Phase 3 deepens analytical rigour and prepares FinnWise for a regulated public posture. Workstreams: an NLP pipeline that automates factor-DB extraction from quarterly filings (replacing manual weekly review), a compound-event Fog of War model that auto-suppresses confidence on interaction effects, a formal SEBI compliance audit with mandatory tester-briefing flow hardening, a productisation assessment dossier (RA-registration research, pricing model, scalability review), and — only if and when registration is obtained — a public marketing site, multi-tenant onboarding, paywall infrastructure, and the final published version of The Map. Phase 3 is **gated**: marketing, paywall, and public-launch stories cannot ship until the SEBI go/no-go (P3-S8) is green.
- **Tech stack additions** (over Phase 2): NLP toolchain (spaCy + a small LLM extractor running on Railway), background queue (e.g. RQ or Celery on Redis), Stripe-equivalent for India billing (Razorpay or similar — research as part of P3-S7), Sentry/observability for hardening. Single `.env.local` continues.
- **Slicing approach**: vertical slices where stories ship code; for strategic/research stories (SEBI audit, productisation dossier) the deliverable is a written artefact + workflow change, not running code — these are still scoped as parent + sub-tasks. Parent task IDs are **per-phase** — this file uses `1.0`–`9.0`. All PRD §6 / §8.6 / §11 invariants remain in force.
- **Prerequisite**: Phase 2 shipped and stable. Factor DB covers all 8 sectors. Mirror + Lens have ≥3 months of live data.

## Team plan

| Developer | Focus | Total points |
|-----------|-------|---------------|
| Jordan | NLP extraction service, compound-event Fog of War model, scalability + observability hardening | 18 |
| Sam | Public marketing site, paywall + billing infrastructure, final Map experience | 17 |
| Riley | Human-in-loop NLP review tooling, SEBI compliance audit, productisation dossier, Phase 3 go/no-go gate | 14 |

---

## Phase 3: Intelligence Deepening

_Automate the slow Phase 1/2 review loops, harden the platform for higher load, complete the legal posture, and decide (with evidence) whether to transition from research project to regulated product._ · **Duration estimate:** 36 weeks (9 months).

### Story P3-S1a — NLP filings extraction service

- **Assigned:** Jordan
- **Points:** 7
- **Layers:** Services, DB, Scheduled jobs
- **Depends on:** Phase 2 (factor DB across 8 sectors)
- **Parallel with:** P3-S1b, P3-S2

**User story**

> As the platform, I want a scheduled job that ingests recent NSE/BSE quarterly filings and extracts proposed updates to factor sensitivities — each carrying an MMJ tag and source URL — so that the weekly manual review described in PRD §7.3 is replaced by a verified-on-review pipeline.

**Acceptance criteria**

- [ ] Job runs nightly; processes filings published in the last 24 hours.
- [ ] Each extracted sensitivity is a **proposed** row written to `factor_sensitivity_proposals`, never overwriting the live `instrument_factor_sensitivity` (human approval in P3-S1b is required).
- [ ] Every proposal carries: `instrument_id`, `factor_id`, `proposed_sensitivity`, `mmj_tag`, `source_url` (filing PDF or HTML), `source_excerpt`, `confidence`, `extracted_at`.
- [ ] Extraction never invents numbers — extractor is constrained to numbers + qualitative claims present in the filing text (test fixture proves rejection of out-of-source numbers).
- [ ] Job is idempotent over (filing_url, instrument, factor).
- [ ] Performance: processes ≥100 filings/night within Railway free-tier limits.

**Tech notes**

- Use a small LLM extraction step bracketed by deterministic preprocessing (spaCy NER for instruments + factor keywords). LLM constrained to JSON-only outputs validated by Pydantic.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/jobs/nlp_filings_extract.py` | create | Scheduled job entrypoint |
| `backend/app/services/nlp/filings_loader.py` | create | Pulls NSE/BSE filings + caches PDFs |
| `backend/app/services/nlp/preprocess.py` | create | spaCy pipeline for instruments + factor keywords |
| `backend/app/services/nlp/extractor.py` | create | LLM-extraction wrapper, JSON-strict |
| `backend/app/services/nlp/source_guard.py` | create | Rejects numbers not in source excerpt |
| `backend/db/migrations/0016_factor_sensitivity_proposals.sql` | create | Proposals table + indexes |
| `backend/tests/test_extractor_rejects_out_of_source_numbers.py` | create | Hallucination guard |
| `backend/tests/test_filings_extract_idempotent.py` | create | Re-run = zero new rows |
| `backend/tests/test_filings_loader_caching.py` | create | PDF cache hits |

#### Tasks (checkboxes)

- [ ] **1.0** NLP filings extraction service
  - [ ] **1.1** Migration: `factor_sensitivity_proposals` with unique `(filing_url, instrument_id, factor_id)`.
  - [ ] **1.2** `filings_loader.fetch(window)` — caches PDFs/HTML under `backend/.cache/filings/` (gitignored).
  - [ ] **1.3** `preprocess.extract_candidates(text)` — spaCy NER + factor keyword spans + window-of-context excerpts.
  - [ ] **1.4** `extractor.propose(candidate)` — LLM call returning strict JSON `{instrument, factor, sensitivity, mmj_tag, confidence}`.
  - [ ] **1.5** `source_guard.assert_grounded(proposal, excerpt)` — every numeric or claim token must appear (literal or normalised) in the excerpt.
  - [ ] **1.6** Persist proposals; dedupe via unique constraint.
  - [ ] **1.7** Railway nightly cron entry.
  - [ ] **1.8** Test: out-of-source rejection; idempotency; caching test.

---

### Story P3-S1b — Human-in-loop review tooling for NLP proposals

- **Assigned:** Riley
- **Points:** 5
- **Layers:** UI (internal), API, DB
- **Depends on:** P3-S1a
- **Parallel with:** P3-S2, P3-S3

**User story**

> As the Product Owner, I want an internal review screen that lists NLP-proposed factor-sensitivity changes side-by-side with the live values and the cited source excerpt, so that I can approve or reject each proposal in seconds — keeping the human-judgement loop while removing manual collection effort.

**Acceptance criteria**

- [ ] `/admin/factor-db/proposals` lists all `pending` proposals sorted by confidence desc.
- [ ] Each row shows: current live sensitivity, proposed sensitivity, source excerpt with highlighted span, source URL, MMJ tag, confidence.
- [ ] One-click Approve → upserts the live `instrument_factor_sensitivity` row; one-click Reject → marks proposal `rejected` with optional note.
- [ ] Approved upsert preserves the original source URL + retrieved-at + MMJ tag (immutable provenance).
- [ ] Bulk-approve only available for proposals with confidence ≥0.9 and MMJ ∈ {MEASURED, MODELLED} (PRD §6.2 — `JUDGED` always single-review).
- [ ] Review actions logged for later audit (timestamp, user, decision, note).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/admin/factor-db/proposals/page.tsx` | create | Internal review list |
| `frontend/app/admin/factor-db/proposals/_components/ProposalRow.tsx` | create | Row + actions |
| `frontend/app/admin/factor-db/proposals/_components/SourceExcerptViewer.tsx` | create | Highlighted span |
| `backend/app/api/factor_db_proposals.py` | create | List + approve + reject |
| `backend/app/services/factor_db_proposals.py` | create | Workflow service |
| `backend/db/migrations/0017_factor_db_proposal_audit.sql` | create | Decision audit log |
| `backend/tests/test_proposal_approve_upserts_live.py` | create | Approve writes live + preserves provenance |
| `backend/tests/test_bulk_approve_gating.py` | create | Bulk-approve constraint enforced |

#### Tasks (checkboxes)

- [ ] **2.0** Human-in-loop review tooling for NLP proposals
  - [ ] **2.1** Migration: `factor_db_proposal_audit(proposal_id, user_id, action, note, at)`.
  - [ ] **2.2** `GET /api/factor-db/proposals?state=pending` + `POST /api/factor-db/proposals/{id}/approve` + `/reject`.
  - [ ] **2.3** Service: approve upserts live, writes provenance, records audit.
  - [ ] **2.4** Bulk endpoint with the gating constraint.
  - [ ] **2.5** Page UI + `ProposalRow` + `SourceExcerptViewer` with span highlight.
  - [ ] **2.6** Admin allow-list gate (reuse from Phase 1 S5).
  - [ ] **2.7** Test: approve flow; bulk-approve gating; audit row written.

---

### Story P3-S2 — Compound-event Fog of War — interaction model

- **Assigned:** Jordan
- **Points:** 6
- **Layers:** Services, DB, UI integration
- **Depends on:** Phase 2 (Mirror grading history), Phase 1 (Fog of War banner from P1-S9)
- **Parallel with:** P3-S1a, P3-S5

**User story**

> As the platform, I want a model that detects interaction effects between simultaneously active events (e.g. a crude shock + an RBI policy meeting) and automatically suppresses card confidence in the affected window, so that Fog of War is triggered by structural reasoning, not a fixed "≥3 active majors" heuristic.

**Acceptance criteria**

- [ ] `interaction_detector.analyse(active_events)` returns a list of detected interaction pairs/triples with: factor overlap, evidence strength, suggested confidence dampener (0–0.5).
- [ ] When triggered, card-level direction and magnitude confidence are dampened by the suggested factor; original values preserved in `track_record`.
- [ ] Fog of War banner now shows the *reason* (e.g. "crude price + RBI policy interaction — confidence dampened 30%"), not a generic banner.
- [ ] The Phase 1 ≥3 heuristic stays as a fallback when the model abstains.
- [ ] Backtest: replay 6 months of historical events; emit a report comparing model-driven vs heuristic Fog of War triggers (`notes/fog-of-war-backtest.md`).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/interaction_detector.py` | create | Factor-overlap detector |
| `backend/app/services/confidence_dampener.py` | create | Apply suggested dampener |
| `backend/app/jobs/recompute_active_card_confidence.py` | create | Triggered when a new event activates |
| `backend/db/migrations/0018_card_confidence_history.sql` | create | History table for replay |
| `backend/app/api/feed.py` | modify | Banner reason string passthrough |
| `frontend/app/(app)/pulse/_components/FogOfWarBanner.tsx` | modify | Render reason |
| `backend/tests/test_interaction_detector.py` | create | Fixture event sets → expected interactions |
| `scripts/fog_of_war_backtest.py` | create | 6-month replay → markdown report |
| `notes/fog-of-war-backtest.md` | create | Output (gitignored) |

#### Tasks (checkboxes)

- [ ] **3.0** Compound-event Fog of War — interaction model
  - [ ] **3.1** Migration: `card_confidence_history` for non-destructive dampener record.
  - [ ] **3.2** `interaction_detector.analyse()` — factor-overlap, sector-overlap, time-window heuristics.
  - [ ] **3.3** `confidence_dampener.apply(card, suggestion)` writes new history row, never mutates original.
  - [ ] **3.4** `recompute_active_card_confidence` job on every new active event.
  - [ ] **3.5** API + UI updates so banner displays the structured reason.
  - [ ] **3.6** Backtest script: replay 6 months, emit comparative report.
  - [ ] **3.7** Test: per-fixture detection; dampener non-destruction; banner reason rendered.

---

### Story P3-S3 — SEBI compliance audit + mandatory legal-review tracker

- **Assigned:** Riley
- **Points:** 4
- **Layers:** Compliance, UI (admin), Docs
- **Depends on:** Phase 1 (P1-S14 tester acceptance), Phase 2 (no new financial data persistence)
- **Parallel with:** P3-S1, P3-S2

**User story**

> As the Product Owner, I want a formal SEBI legal review of all UI copy + the editorial pipeline + the bias audit log, captured in a tracker with sign-off lines, so that no public launch (P3-S6, P3-S7) can ship without explicit legal approval per PRD §11.1.

**Acceptance criteria**

- [ ] `notes/sebi-legal-review-tracker.md` (gitignored) lists every screen and every editorial promise with reviewer sign-off lines.
- [ ] A SEBI-specialised lawyer reviews all UI copy (PRD §11.1 mandatory caveat); their notes + responses logged.
- [ ] Any required copy changes captured as PRs labelled `compliance` and gated behind reviewer approval.
- [ ] Mandatory tester-briefing flow hardened: explicit text on educational scope, signed checkbox, server-side timestamp + IP, optional PDF download of briefing.
- [ ] In-app "About this analysis" page (`/about-this-analysis`) consolidates the SEBI framing into a single linkable artefact.
- [ ] All Phase 3 public-launch stories (P3-S6, P3-S7) must reference this story's sign-off as a precondition.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `notes/sebi-legal-review-tracker.md` | create | Tracker (gitignored) |
| `frontend/app/about-this-analysis/page.tsx` | create | Public about page |
| `frontend/app/(app)/tester-briefing/page.tsx` | modify | Add PDF download + IP+timestamp |
| `backend/app/api/tester_briefing.py` | modify | Capture IP + timestamp; serve PDF |
| `backend/tests/test_tester_briefing_capture.py` | create | Asserts IP + timestamp stored |

#### Tasks (checkboxes)

- [ ] **4.0** SEBI compliance audit + mandatory legal-review tracker
  - [ ] **4.1** Draft `notes/sebi-legal-review-tracker.md` listing every screen + editorial promise.
  - [ ] **4.2** Schedule + complete review with SEBI-specialised lawyer.
  - [ ] **4.3** Log lawyer notes and responses inline in the tracker.
  - [ ] **4.4** Open `compliance`-labelled PRs for any required copy changes.
  - [ ] **4.5** Build `/about-this-analysis` consolidating the SEBI framing.
  - [ ] **4.6** Harden tester-briefing: IP + timestamp + PDF download.
  - [ ] **4.7** Test: briefing capture; about page link present on every protected page footer.

---

### Story P3-S4 — Productisation assessment + RA registration research dossier

- **Assigned:** Riley
- **Points:** 3
- **Layers:** Strategy, Docs
- **Depends on:** P3-S3
- **Parallel with:** P3-S5

**User story**

> As the Product Owner, I want a single dossier that captures the RA-registration research, the scalability review headline numbers, candidate pricing models, and a clear go/no-go decision on transitioning from research project to regulated product, so that Phase 3 ends with an explicit, evidence-backed direction.

**Acceptance criteria**

- [ ] `notes/productisation-assessment.md` (gitignored) contains: SEBI Research Analyst registration prerequisites, costs, timelines; FinnWise current-state gap analysis; recommended target user segment; pricing-model options (free / paid subscription / freemium / sponsored research); scalability headline (from P3-S5).
- [ ] Three pricing models drafted with revenue scenarios.
- [ ] A single go / wait / no-go recommendation with named conditions.
- [ ] All claims source-linked (SEBI circulars, comparable products, market sizing references).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `notes/productisation-assessment.md` | create | Dossier (gitignored) |

#### Tasks (checkboxes)

- [ ] **5.0** Productisation assessment + RA registration research dossier
  - [ ] **5.1** Research SEBI RA-registration prerequisites + costs.
  - [ ] **5.2** Map current FinnWise to RA-compliance gaps.
  - [ ] **5.3** Draft three pricing models + revenue scenarios.
  - [ ] **5.4** Incorporate scalability headline numbers from P3-S5.
  - [ ] **5.5** Write the go / wait / no-go recommendation with explicit named conditions.
  - [ ] **5.6** Review with at least one external practitioner (mentor, lawyer, or operator) and capture their dissent.

---

### Story P3-S5 — Scalability + observability hardening

- **Assigned:** Jordan
- **Points:** 5
- **Layers:** Ops, Infra, Tests
- **Depends on:** Phase 2 (P2-S13 baseline metrics endpoint)
- **Parallel with:** P3-S1, P3-S3

**User story**

> As the platform owner, I want load-tested SLOs, structured logs and traces wired to a hosted observability provider, error budgets, and alerting, so that any public-launch decision (P3-S6/S7) rests on hard performance evidence rather than gut feel.

**Acceptance criteria**

- [ ] Load test simulates 200 concurrent users browsing Pulse + Thread + Lens; capture p95 latency, error rates, cost per hour.
- [ ] SLOs defined in `docs/plans/phase3-slos.md`: Pulse p95 < 800ms; Thread p95 < 1.2s; Lens p95 generation time < 90s; error rate <1%.
- [ ] Sentry (or equivalent free-tier) wired to frontend + backend; release tags on every deploy.
- [ ] Structured request logs (already from P2-S13) shipped to a hosted log store (free-tier-acceptable).
- [ ] Alerting: error budget burn-rate alert + p95 SLO violation alert.
- [ ] Performance baseline numbers fed into P3-S4 dossier.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `scripts/load_test_pulse.k6.js` | create | k6 scenarios |
| `scripts/load_test_thread.k6.js` | create | k6 scenarios |
| `scripts/load_test_lens.k6.js` | create | k6 scenarios |
| `docs/plans/phase3-slos.md` | create | SLO doc |
| `backend/app/core/logging.py` | modify | Ship logs to provider |
| `frontend/instrumentation.ts` | create | Sentry init |
| `backend/app/core/sentry.py` | create | Sentry init |
| `.github/workflows/load-tests.yml` | create | Weekly load test in CI |

#### Tasks (checkboxes)

- [ ] **6.0** Scalability + observability hardening
  - [ ] **6.1** Author SLOs in `docs/plans/phase3-slos.md`.
  - [ ] **6.2** Sentry projects + DSNs in `.env.local`; frontend + backend init.
  - [ ] **6.3** Logger ships JSON logs to chosen provider.
  - [ ] **6.4** k6 scripts for the three surfaces.
  - [ ] **6.5** Weekly load-test workflow on GH Actions (or scheduled Railway job).
  - [ ] **6.6** Burn-rate alert + p95 SLO violation alert configured.
  - [ ] **6.7** Capture baseline numbers; hand over to Riley for P3-S4 dossier.

---

### Story P3-S6 — Public marketing site + waitlist + multi-tenant onboarding

- **Assigned:** Sam
- **Points:** 6
- **Layers:** UI (public), API, DB
- **Depends on:** P3-S3 sign-off (gated), P3-S8 go decision
- **Parallel with:** P3-S7 (after S8 green), P3-S9

> **Gate:** This story cannot start UI shipping until P3-S8 returns a "go" decision.

**User story**

> As a prospective user discovering FinnWise from outside the invited tester circle, I want a public marketing site that clearly explains what FinnWise is and is not (research / education, not advice), a waitlist for access, and a self-serve onboarding for approved users, so that growth beyond Phase 1/2 testers is possible while staying inside SEBI safe harbour.

**Acceptance criteria**

- [ ] Public site under `(marketing)` route group: home, manifesto, three-pillars page, transparency report (live bias log + track record summary), about-this-analysis, contact.
- [ ] Waitlist form persists `email + optional referral` to `waitlist` table.
- [ ] Approved users receive a magic-link invite that lands on `/tester-briefing` (reuse Phase 1) and only then routes into the app.
- [ ] SEBI footer present on every marketing page.
- [ ] All marketing copy passes the P3-S3 legal review.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(marketing)/page.tsx` | create | Home |
| `frontend/app/(marketing)/manifesto/page.tsx` | create | Manifesto |
| `frontend/app/(marketing)/pillars/page.tsx` | create | Three pillars |
| `frontend/app/(marketing)/transparency/page.tsx` | create | Public bias + track record snapshot |
| `frontend/app/(marketing)/waitlist/page.tsx` | create | Waitlist form |
| `backend/app/api/waitlist.py` | create | `POST /api/waitlist` |
| `backend/db/migrations/0019_waitlist.sql` | create | Waitlist + invites |
| `backend/app/services/waitlist_invite.py` | create | Approval → magic-link invite |
| `backend/tests/test_waitlist_invite_flow.py` | create | Approval flow test |
| `frontend/app/(marketing)/transparency/page.test.tsx` | create | Asserts SEBI footer present |

#### Tasks (checkboxes)

- [ ] **7.0** Public marketing site + waitlist + multi-tenant onboarding
  - [ ] **7.1** `(marketing)` route group with shared layout + SEBI footer.
  - [ ] **7.2** Author home + manifesto + pillars copy; legal-review pass.
  - [ ] **7.3** Public transparency page reading from `track_record` aggregates and `card_bias_flags` summary.
  - [ ] **7.4** Migration: `waitlist` + `waitlist_invites`.
  - [ ] **7.5** `POST /api/waitlist` + admin approval action.
  - [ ] **7.6** Magic-link invite that routes through `/tester-briefing` then into the app.
  - [ ] **7.7** Test: approval flow; SEBI footer on every marketing page; transparency page renders aggregates.

---

### Story P3-S7 — Pricing + paywall infrastructure (gated)

- **Assigned:** Sam (with Jordan on backend)
- **Points:** 5
- **Layers:** Billing, API, UI
- **Depends on:** P3-S8 go decision + RA-registration condition from P3-S4 dossier
- **Parallel with:** P3-S6 (post-gate)

> **Gate:** This story cannot start until P3-S4 recommends "go" and P3-S8 returns green. If RA registration is not obtained, this story stays out of scope per PRD §14.

**User story**

> As the Product Owner — only if and when SEBI Research Analyst registration is in place — I want a paywall + subscription billing flow integrated with an India-friendly payment provider, so that FinnWise can transition from research project to a sustainable regulated product.

**Acceptance criteria**

- [ ] Payment provider integrated (research candidates: Razorpay, Stripe India, Cashfree) with subscription support.
- [ ] Plans defined in DB; one free tier and one paid tier minimum (final shape from P3-S4 dossier).
- [ ] Paywall middleware on `(app)` routes for non-free features (final list approved by legal review).
- [ ] Webhooks signed + verified; subscription state mirrored to `user_subscriptions` table.
- [ ] No paywall message uses recommendation framing; copy passes P3-S3 review.
- [ ] All financial transactions logged immutably for audit.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/billing/provider.py` | create | Provider abstraction |
| `backend/app/services/billing/razorpay.py` | create | Provider impl (example) |
| `backend/app/api/billing.py` | create | Checkout + webhooks |
| `backend/db/migrations/0020_plans_and_subscriptions.sql` | create | Plans + subs + ledger |
| `frontend/app/(app)/settings/billing/page.tsx` | create | Billing UI |
| `frontend/components/Paywall/Paywall.tsx` | create | Gating component |
| `backend/tests/test_billing_webhook_verification.py` | create | Signed webhook test |
| `backend/tests/test_subscription_state_mirroring.py` | create | DB mirror test |

#### Tasks (checkboxes)

- [ ] **8.0** Pricing + paywall infrastructure (gated)
  - [ ] **8.1** Provider selection RFC in `notes/billing-provider-rfc.md` (gitignored).
  - [ ] **8.2** Provider creds in `.env.local`.
  - [ ] **8.3** Migration: plans + user_subscriptions + billing_ledger (append-only).
  - [ ] **8.4** Checkout API + webhook handler with signature verification.
  - [ ] **8.5** Sub-state mirror service; idempotent on duplicate webhooks.
  - [ ] **8.6** Paywall middleware on configured route patterns.
  - [ ] **8.7** Billing settings page + Paywall component.
  - [ ] **8.8** Compliance-reviewed paywall copy.
  - [ ] **8.9** Test: webhook signature verification; subscription mirror; paywall gating behaviour.

---

### Story P3-S8 — Phase 3 launch-readiness gate + go/no-go checklist

- **Assigned:** Riley
- **Points:** 2
- **Layers:** Governance
- **Depends on:** P3-S3, P3-S4, P3-S5
- **Parallel with:** _None — final gate before P3-S6 and P3-S7 ship_

**User story**

> As the Product Owner, I want an explicit `docs/plans/phase3-go-no-go.md` checklist that captures legal sign-off, SLOs met, productisation recommendation, and named-conditions for proceeding, so that no public-launch story ships without an auditable green light.

**Acceptance criteria**

- [ ] Checklist covers: legal sign-off captured (P3-S3); SLOs met under load (P3-S5); productisation recommendation logged (P3-S4); tester satisfaction baseline; bias-audit health; track-record health (direction prediction accuracy ≥60% per PRD §13).
- [ ] Each item has owner + status + evidence link.
- [ ] Decision logged in the doc with timestamp and signatures.
- [ ] P3-S6 and P3-S7 carry a `phase3-gate: green` precondition in their PR descriptions.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `docs/plans/phase3-go-no-go.md` | create | Checklist (gitignored under existing rule) |

#### Tasks (checkboxes)

- [ ] **9.0** Phase 3 launch-readiness gate + go/no-go checklist
  - [ ] **9.1** Draft the checklist with all items + owners + evidence-link slots.
  - [ ] **9.2** Walk each item with its owner; capture status + link.
  - [ ] **9.3** Hold the go/no-go review; log decision + signatures.
  - [ ] **9.4** Update PR template to require `phase3-gate: green` for public-facing stories.

---

### Story P3-S9 — The Map — final public version + sector deep-dive interactives

- **Assigned:** Sam
- **Points:** 6
- **Layers:** UI, API
- **Depends on:** Phase 2 (P2-S11 Map modules), P3-S6 marketing-site shell
- **Parallel with:** P3-S7 (post-gate)

**User story**

> As any visitor or signed-in user, I want a public-facing, polished version of The Map with sector deep-dives and interactive sensitivity visualisations, so that the educational layer of FinnWise stands as a product in its own right (and reinforces the editorial brand).

**Acceptance criteria**

- [ ] Map fully reachable from both `(marketing)` and `(app)` route groups (different shells, same data).
- [ ] Each sector has a deep-dive page: factor sensitivity matrix (interactive hover), event-history strip drawing from `track_record`, links to relevant Map modules, "how this sector tends to react" educational module.
- [ ] All interactive visualisations are accessible (keyboard navigation + screen-reader labels).
- [ ] No recommendation framing — every sector page passes the P3-S3 language audit.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(marketing)/map/page.tsx` | create | Public index |
| `frontend/app/(marketing)/map/[slug]/page.tsx` | create | Public sector deep-dive |
| `frontend/app/(app)/map/[slug]/page.tsx` | modify | Use shared Map components |
| `frontend/components/Map/SensitivityMatrix.tsx` | create | Shared interactive matrix |
| `frontend/components/Map/EventHistoryStrip.tsx` | create | Pulls from `track_record` |
| `frontend/components/Map/SensitivityMatrix.test.tsx` | create | Keyboard nav test |
| `frontend/components/Map/EventHistoryStrip.test.tsx` | create | Data binding test |

#### Tasks (checkboxes)

- [ ] **10.0** The Map — final public version + sector deep-dive interactives
  - [ ] **10.1** Extract Map components into `components/Map/` shared between marketing + app.
  - [ ] **10.2** `SensitivityMatrix` interactive (hover + keyboard) with MMJ-coloured cells.
  - [ ] **10.3** `EventHistoryStrip` drawing from `track_record` aggregates.
  - [ ] **10.4** Public + app routes; identical content, different shells.
  - [ ] **10.5** A11y pass: keyboard nav, screen-reader labels, contrast.
  - [ ] **10.6** Language audit against PRD §11.1.
  - [ ] **10.7** Test: keyboard nav across matrix; event-history binding.

---

## Risks

- **NLP extractor hallucinates sensitivities** — P3-S1a `source_guard` rejects out-of-source numbers; P3-S1b keeps human-in-loop for every approve. Re-test after every prompt change.
- **Interaction model triggers Fog of War too aggressively, killing trust** — P3-S2 backtest is mandatory; ship behind a feature flag and fall back to Phase 1 heuristic if false-positive rate >10%.
- **SEBI review surfaces deep copy issues late** — P3-S3 happens before P3-S6/S7 by gate; budget for at least one full re-write pass.
- **Productisation dossier becomes wishful thinking** — P3-S4 requires an external practitioner dissent capture; mitigates own-bias.
- **Hosted observability provider costs unexpectedly** — P3-S5 should pick a free-tier-acceptable provider; review monthly bills.
- **Paywall code ships before RA registration** — P3-S7 is double-gated by P3-S4 recommendation **and** P3-S8 green. Build with explicit feature flag default-off if PR review approves earlier wiring.

## Recommendations

- Start P3-S1a + P3-S2 + P3-S3 in parallel in Month 10 — they are independent and the long ones.
- Treat P3-S4 dossier as the binding artefact of the phase; everything ladders up to a real go / wait / no-go decision.
- Do not begin P3-S6/S7 until P3-S8 is green. The gate is the point.
- P3-S9 (final Map) is the safest visible improvement to ship regardless of the productisation decision — it strengthens the research-project posture too.

---

## How to execute Phase 3

Suggested order (Months 10–18, 36 weeks):

1. **Month 10:** Jordan P3-S1a + P3-S5 setup. Riley P3-S3 (legal review kickoff) + P3-S1b internal tooling spec. Sam waits for gate; meanwhile contributes a11y / polish backlog tail from Phase 2.
2. **Month 11–12:** Jordan ships P3-S1a + P3-S2. Riley ships P3-S1b + continues P3-S3. Sam starts P3-S9 (Map deep-dive — independent of gate).
3. **Month 13–14:** Jordan ships P3-S5 hardening. Riley closes P3-S3 + opens P3-S4 dossier + drafts P3-S8 checklist.
4. **Month 15:** Hold P3-S8 go/no-go review. Decision documented.
5. **Month 16–18 (if go):** Sam ships P3-S6 (public marketing + waitlist) and — only if RA-registration path is approved — P3-S7 (paywall). Soft-launch waitlist cohort.
6. **Month 16–18 (if wait/no-go):** Defer P3-S6 + P3-S7; iterate the research-project posture; revisit gate quarterly.

Parallel-safe pairs at every month boundary: `{S1a, S2, S3}` in Month 10–11; `{S1b, S5, S9}` in Month 12–13; `{S6, S7, S9}` only after S8 green.

---

## Appendix — Taskmaster-style export (per developer)

### Notes

- Same test placement and commands as earlier phases.
- Add only the new keys to `.env.local`: `SENTRY_DSN_FRONTEND`, `SENTRY_DSN_BACKEND`, `LOG_PROVIDER_KEY`, `PAYMENT_PROVIDER_KEY` (if applicable).
- All earlier phase invariants (SEBI footer, MMJ tags, append-only `track_record`, no buy/sell/hold) continue to apply. Compound Fog of War must **not** mutate the original confidence values in place.

### Relevant Files (rollup)

- `backend/app/jobs/**` — nlp_filings_extract, recompute_active_card_confidence
- `backend/app/services/nlp/**` — filings_loader, preprocess, extractor, source_guard
- `backend/app/services/**` — interaction_detector, confidence_dampener, factor_db_proposals, waitlist_invite, billing/*
- `backend/app/api/**` — factor_db_proposals, waitlist, billing, modified feed (banner reason)
- `backend/app/core/**` — sentry, logging (modified)
- `backend/db/migrations/**` — 0016 through 0020
- `frontend/app/admin/factor-db/proposals/**` — Internal review tooling
- `frontend/app/(marketing)/**` — Public site (S6, S9)
- `frontend/app/(app)/settings/billing/**` — Billing UI (S7)
- `frontend/components/Map/**` — Shared Map components (S9)
- `frontend/components/Paywall/**` — Paywall gate (S7)
- `notes/sebi-legal-review-tracker.md`
- `notes/productisation-assessment.md`
- `notes/fog-of-war-backtest.md`
- `notes/billing-provider-rfc.md`
- `docs/plans/phase3-slos.md`
- `docs/plans/phase3-go-no-go.md`
- `scripts/fog_of_war_backtest.py`, `scripts/load_test_*.k6.js`

### Tasks by developer — Jordan

- [ ] **1.0** NLP filings extraction service
  - [ ] **1.1** `factor_sensitivity_proposals` migration
  - [ ] **1.2** Filings loader + cache
  - [ ] **1.3** spaCy preprocess
  - [ ] **1.4** LLM extractor (JSON-strict)
  - [ ] **1.5** `source_guard` hallucination check
  - [ ] **1.6** Persist + dedupe
  - [ ] **1.7** Nightly cron
  - [ ] **1.8** Hallucination + idempotency + cache tests
- [ ] **3.0** Compound-event Fog of War — interaction model
  - [ ] **3.1** `card_confidence_history` migration
  - [ ] **3.2** `interaction_detector.analyse()`
  - [ ] **3.3** `confidence_dampener.apply()`
  - [ ] **3.4** Recompute job on event activation
  - [ ] **3.5** API + Banner reason update
  - [ ] **3.6** 6-month backtest report
  - [ ] **3.7** Detection + non-destruction + banner tests
- [ ] **6.0** Scalability + observability hardening
  - [ ] **6.1** SLO doc
  - [ ] **6.2** Sentry projects + init
  - [ ] **6.3** Log shipping
  - [ ] **6.4** k6 scripts (Pulse / Thread / Lens)
  - [ ] **6.5** Weekly load test in CI
  - [ ] **6.6** Burn-rate + p95 alerts
  - [ ] **6.7** Hand baseline to Riley for P3-S4

### Tasks by developer — Sam

- [ ] **7.0** Public marketing site + waitlist + multi-tenant onboarding
  - [ ] **7.1** `(marketing)` shell + SEBI footer
  - [ ] **7.2** Home + manifesto + pillars copy
  - [ ] **7.3** Transparency page reading aggregates
  - [ ] **7.4** Waitlist migration
  - [ ] **7.5** Waitlist API + admin approval
  - [ ] **7.6** Magic-link invite via tester-briefing
  - [ ] **7.7** Approval + footer + transparency tests
- [ ] **8.0** Pricing + paywall infrastructure (gated)
  - [ ] **8.1** Billing provider RFC
  - [ ] **8.2** Provider creds in `.env.local`
  - [ ] **8.3** Plans + subs + ledger migration
  - [ ] **8.4** Checkout API + webhook verification
  - [ ] **8.5** Subscription state mirror
  - [ ] **8.6** Paywall middleware
  - [ ] **8.7** Billing settings UI + Paywall component
  - [ ] **8.8** Compliance copy review
  - [ ] **8.9** Webhook + mirror + gating tests
- [ ] **10.0** The Map — final public version + sector deep-dive interactives
  - [ ] **10.1** Extract shared `components/Map/*`
  - [ ] **10.2** `SensitivityMatrix` interactive
  - [ ] **10.3** `EventHistoryStrip` from track record
  - [ ] **10.4** Public + app routes wired
  - [ ] **10.5** A11y pass
  - [ ] **10.6** Language audit
  - [ ] **10.7** Keyboard nav + binding tests

### Tasks by developer — Riley

- [ ] **2.0** Human-in-loop review tooling for NLP proposals
  - [ ] **2.1** Audit log migration
  - [ ] **2.2** Proposal list + approve + reject APIs
  - [ ] **2.3** Approve upsert + provenance preserve
  - [ ] **2.4** Bulk-approve gating
  - [ ] **2.5** Internal review UI
  - [ ] **2.6** Admin allow-list gate
  - [ ] **2.7** Approve + bulk-gate + audit tests
- [ ] **4.0** SEBI compliance audit + mandatory legal-review tracker
  - [ ] **4.1** Draft tracker
  - [ ] **4.2** Lawyer review session(s)
  - [ ] **4.3** Capture notes + responses
  - [ ] **4.4** Compliance PRs for required changes
  - [ ] **4.5** `/about-this-analysis` page
  - [ ] **4.6** Tester briefing IP + timestamp + PDF
  - [ ] **4.7** Briefing capture + about-link tests
- [ ] **5.0** Productisation assessment + RA registration research dossier
  - [ ] **5.1** SEBI RA prerequisite research
  - [ ] **5.2** Compliance gap analysis
  - [ ] **5.3** Three pricing models
  - [ ] **5.4** Scalability headline from P3-S5
  - [ ] **5.5** Go / wait / no-go recommendation
  - [ ] **5.6** External-practitioner dissent capture
- [ ] **9.0** Phase 3 launch-readiness gate + go/no-go checklist
  - [ ] **9.1** Draft checklist with owners + evidence slots
  - [ ] **9.2** Walk each item to closure
  - [ ] **9.3** Run go/no-go review + log decision
  - [ ] **9.4** PR template `phase3-gate: green` requirement
