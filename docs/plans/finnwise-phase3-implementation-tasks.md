# FinnWise — Phase 3 Implementation Tasks (Intelligence Deepening, Months 10–18)

_Source PRD_: `FinnWise_PRD_v3_Final.md` Section 10 / Phase 3, **superseded for intelligence architecture by** `FinnWise_PRD2_Intelligence_Architecture.md` + `FinnWise_PRD2_SSA_Solution_Design.md`  
_PO decisions applied_: G-01 Option B + `unique_publisher_count` + explainability (Phase 3 only) · G-02 narrow MEDIUM (0.55–0.74) · G-03 headline_hash **all categories** · G-13 synthetic seed **Week 1** · G-14 defer P3-S6/P3-S7  
_generated for independent execution without prd-planner_

## Overview

- **Summary**: Phase 3 deepens analytical rigour and prepares FinnWise for a regulated public posture. This plan **merges** the original Phase 3 stories (P3-S1a through P3-S9) with the **PRD2 intelligence gap workstreams** (G-01 through G-15). Week 1 starts with synthetic historical seed (G-13) because live Mirror/Lens data is unavailable. Data-pipeline hardening (dedup, NewsAPI, watchlist, freshness) precedes the rule-based confidence scorer and gate swap. Editorial integrity (hard number gate, checklist, section regen) ships before FoW `is_major` and signal override measurement. NLP filings extraction runs on **GitHub Actions** (Gemini Flash), not Render. **P3-S6 (marketing) and P3-S7 (billing) are formally deferred** per PRD2 G-14 — appendix reference only. P3-S2 interaction model is **gated** until 30 days after synthetic seed is live.
- **Tech stack**: FastAPI backend, Supabase/Postgres (Session pooler for GH Actions), Next.js frontend (Vercel), Gemini Pro (card synthesis), Gemini Flash (NLP extraction), GitHub Actions (NLP nightly + Render keep-alive + monthly FP report), Render free tier API. Config via YAML where noted (`newsapi_keywords.yaml`, `entity_map.yaml`, `confidence_config.py`).
- **Slicing approach**: vertical slices (UI + API + DB minimum per story). Parent task IDs are **global** across this file (`1.0`–`25.0`). Each story has **≤ 6 sub-tasks**. Dedicated **test-gate stories** sit between milestones to verify acceptance before downstream work proceeds.
- **Prerequisite**: Phase 2 shipped and stable; **Phase 2.5 closed** 30 May 2026 ([close-out](../Post%20Implementation%20documentation/Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md) · [S6 handover](../Post%20Implementation%20documentation/Phase2.5_P2.5-S6%20-%20Evidence%20archive%20and%20Phase%20close-out.md); API proxy p95 PO-waived). Factor DB covers all 8 sectors. **Live Mirror/Lens ≥3 months is replaced for Phase 3 build start by synthetic seed (P3-S0).**

## PO decision registry (binding for this plan)

| Gap | PO decision |
|-----|-------------|
| G-01 | Option B + `unique_publisher_count` (10% weight); explainability API + UI in **Phase 3 only** |
| G-02 | Narrow MEDIUM: HIGH ≥ 0.75 · MEDIUM 0.55–0.74 · LOW &lt; 0.55; store `confidence_raw` + `confidence_effective` |
| G-03 | `headline_hash` in dedup key for **all event categories** |
| G-13 | Synthetic seed **Week 1** (first story) |
| G-14 | P3-S6 / P3-S7 **deferred** — no active tasks |

## Performance standards (inherit Phase 1.5 + Phase 2)

Every new route MUST comply with `docs/plans/cross-phase-performance-standards.md`:

| Workstream | Perf requirement |
|------------|------------------|
| Confidence breakdown API | Cache 60s per `event_id`; p95 &lt; 200ms |
| P3-S5 SLOs / k6 | Pulse p95 &lt;800 ms, Thread &lt;1.2 s |
| P3-S9 Public Map | Lighthouse + a11y on sector deep-dives |
| P3-S8 Go/no-go | Cross-phase perf standards + Phase 2.5 evidence |

## Team plan

| Developer | Focus | Total points |
|-----------|-------|---------------|
| Jordan | Synthetic seed, dedup, confidence scorer/gate, FoW `is_major`, NLP job (GH Actions), interaction model, observability | 38 |
| Sam | NewsAPI scheduler, market-facts freshness, confidence explainability UI, section regen, Map public | 25 |
| Riley | Isolation test gate, watchlist, number validator, editorial checklist, signal override, NLP review, SEBI/dossier/gate | 27 |

---

## Phase 3: Intelligence Deepening

_Automate slow review loops, close PRD2 intelligence gaps, harden the platform, complete legal posture, and decide whether to transition from research project to regulated product._ · **Duration estimate:** 36 weeks (9 months); **PRD2 foundation milestones:** Weeks 1–4.

### Milestone map (execution order)

| Order | Story ID | Milestone | Depends on |
|-------|----------|-----------|------------|
| 1 | P3-S0 | Synthetic seed Week 1 | — |
| 2 | P3-T1 | Isolation test gate | P3-S0 |
| 3 | P3-S1c | Dedup (all categories) | P3-S0 |
| 4 | P3-S1d ∥ P3-S1e | NewsAPI ∥ Watchlist | P3-S0 |
| 5 | P3-S1f | Market facts freshness | P3-S1c |
| 6 | P3-T2 | Data pipeline test gate | P3-S1c, S1d, S1e, S1f |
| 7 | P3-S1g | Confidence scorer + gate | P3-T2 |
| 8 | P3-S1h | Explainability UI | P3-S1g |
| 9 | P3-T3 | Confidence test gate | P3-S1g, S1h |
| 10 | P3-S1i | Number validator hard gate | P3-T3 |
| 11 | P3-S1j ∥ P3-S1k | Checklist ∥ Section regen | P3-S1i |
| 12 | P3-T4 | Editorial integrity test gate | P3-S1i, S1j, S1k |
| 13 | P3-S1l | FoW `is_major` + banner | P3-T4 |
| 14 | P3-S1m | Signal override log | P3-S1l |
| 15 | P3-T5 | FoW + signal test gate | P3-S1l, S1m |
| 16 | P3-S1a | NLP filings (GH Actions) | P3-T2 |
| 17 | P3-S1b | NLP proposals review | P3-S1a |
| 18 | P3-S2 | Interaction model | P3-S0 + **30-day soak** |
| 19 | P3-S3 ∥ P3-S5 | SEBI audit ∥ Observability | Phase 2 |
| 20 | P3-S4 | Productisation dossier | P3-S3, P3-S5 |
| 21 | P3-S8 | Go/no-go gate | P3-S3, S4, S5 |
| 22 | P3-S9 | Map public deep-dives | Phase 2 P2-S11 |
| — | P3-S6, P3-S7 | **Deferred** (G-14) | P3-S8 green + RA path |

**Parallel-safe now:** `{P3-S1d, P3-S1e}` · `{P3-S1j, P3-S1k}` · `{P3-S3, P3-S5}` (after Week 4 foundation)

---

### Story P3-S0 — Synthetic historical seed + triple-layer isolation (G-13)

- **Assigned:** Jordan
- **Points:** 5
- **Layers:** DB, Scripts, CI
- **Depends on:** _None — Week 1 start_
- **Parallel with:** _None (blocks calibration / FoW backtest)_
- **Gaps:** G-13

**User story**

> As the solo builder, I want 20 verifiable Indian financial events (Jan–Jun 2025) seeded into production tables with `is_synthetic = TRUE`, so that confidence calibration, FoW backtest, and P3-S2 prerequisites exist without live Mirror/Lens testers.

**Acceptance criteria**

- [x] Migration adds `is_synthetic`, `confidence_raw`, `confidence_effective`, `is_major`, `dedup_key` columns where missing.
- [x] 20 events seeded; 7 with `is_major = TRUE`; idempotent re-run (UPSERT on `external_id`).
- [x] RLS policies hide synthetic rows from `authenticated` role on `events`, `signals`, `track_record`, `user_predictions`, `card_confidence_history`.
- [x] Service-layer `SyntheticFilterMixin` applied to all user-facing read paths.
- [x] Seed script runnable: `python backend/scripts/seed_synthetic_events.py`.

**Tech notes**

- DB: `00XX_synthetic_isolation.sql` | Script: `seed_synthetic_events.py` + `synthetic_events.json` | No UI

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/0021_synthetic_isolation.sql` | create | Columns + RLS |
| `backend/scripts/seed_synthetic_events.py` | create | Idempotent seed |
| `backend/scripts/seed_data/synthetic_events.json` | create | 20 event definitions |
| `backend/app/db/queries/base.py` | modify | `SyntheticFilterMixin` |
| `backend/tests/test_synthetic_seed_idempotent.py` | create | Re-run produces zero dupes |

#### Tasks (checkboxes)

- [x] **1.0** Synthetic historical seed + triple-layer isolation
  - [x] **1.1** Migration: `is_synthetic` + confidence/is_major/dedup columns + RLS on all affected tables.
  - [x] **1.2** `seed_synthetic_events.py` + JSON fixture (20 events, 7 `is_major`).
  - [x] **1.3** `SyntheticFilterMixin` wired into feed, thread, mirror query modules.
  - [x] **1.4** Run seed against dev/staging; verify 20 rows via service role.
  - [x] **1.5** Idempotency test: second run inserts zero new rows.
  - [x] **1.6** Document seed command in `backend/scripts/README.md`.

---

### Story P3-T1 — Synthetic isolation verification gate

- **Assigned:** Riley
- **Points:** 2
- **Layers:** Tests, CI
- **Depends on:** P3-S0
- **Parallel with:** P3-S1c (may start after 1.1 migration lands)
- **Gaps:** G-13

**User story**

> As the platform, I want automated proof that synthetic rows never leak into Pulse, Thread, or Mirror responses, so that Week 1 seed data cannot corrupt user-facing trust metrics.

**Acceptance criteria**

- [x] `test_synthetic_isolation.py`: Pulse feed, Thread detail, Mirror list return zero synthetic rows when seeded data exists.
- [x] `test_query_synthetic_filter.py`: CI grep/assertion that user-facing query modules import or apply synthetic filter.
- [x] Failing test blocks merge (added to existing CI workflow).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/tests/test_synthetic_isolation.py` | create | API integration |
| `backend/tests/test_query_synthetic_filter.py` | create | Static/query guard |
| `.github/workflows/ci.yml` | modify | Run new tests |

#### Tasks (checkboxes)

- [x] **2.0** Synthetic isolation verification gate
  - [x] **2.1** Integration tests: Pulse, Thread, Mirror exclude `is_synthetic = TRUE`.
  - [x] **2.2** Query-path guard test: fail if known read modules omit synthetic filter.
  - [x] **2.3** Wire tests into CI; verify red/green locally with seed present.
  - [x] **2.4** Add negative test: service-role admin query *can* read synthetic (smoke).
  - [x] **2.5** Document isolation contract in `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` cross-ref note (one paragraph).

---

### Story P3-S1c — Event de-duplication pipeline (G-03)

- **Assigned:** Jordan
- **Points:** 5
- **Layers:** DB, Services, Jobs
- **Depends on:** P3-S0 (migration baseline)
- **Parallel with:** P3-S1d, P3-S1e (after 1.1)
- **Gaps:** G-03

**User story**

> As the platform, I want the same real-world event from multiple sources to merge into one queue row with accumulating `source_count`, so that confidence scoring and editorial review are not duplicated.

**Acceptance criteria**

- [x] `dedup_key = sha256(category + normalised_entity + 4h_window + headline_hash)` for **all categories** (`headline_hash` = normalised first 100 chars).
- [x] `ON CONFLICT (dedup_key) DO UPDATE` increments `source_count`, appends `sources[]`, recomputes `confidence_raw`.
- [x] `dedup_review_queue` captures cross-category same-window collisions for Sunday review.
- [x] `entity_map.yaml` holds top 30+ entities (editable without deploy).
- [x] `source_count > 5` sets `force_editorial_review` flag on event.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/event_dedup.py` | create | Key computation + upsert |
| `backend/app/config/entity_map.yaml` | create | Entity normalisation |
| `backend/db/migrations/00XX_dedup_key_review_queue.sql` | create | `dedup_key` unique + review queue |
| `backend/tests/test_event_dedup.py` | create | Merge + headline_hash all categories |
| `backend/tests/test_dedup_review_queue.py` | create | Cross-category flag |

#### Tasks (checkboxes)

- [x] **3.0** Event de-duplication pipeline
  - [x] **3.1** Migration: `dedup_key` unique index, `dedup_review_queue`, `force_editorial_review` on `events`.
  - [x] **3.2** `event_dedup.py`: key for all categories includes `headline_hash`; entity map from YAML.
  - [x] **3.3** Upsert path integrated into event detection job (post-ingest).
  - [x] **3.4** Cross-category collision → `dedup_review_queue` row (no auto-merge).
  - [x] **3.5** `source_count > 5` guardrail flag.
  - [x] **3.6** Unit tests: same wire across outlets merges; different headlines same entity do not false-merge.

---

### Story P3-S1d — NewsAPI factor keyword scheduler (G-04)

- **Assigned:** Sam
- **Points:** 3
- **Layers:** Config, Services
- **Depends on:** P3-S0
- **Parallel with:** P3-S1c, P3-S1e
- **Gaps:** G-04

**User story**

> As the platform, I want NewsAPI calls allocated across 8 Factor DB macro factors within the 100 calls/day cap, so that ingestion targets Indian financial signal, not generic noise.

**Acceptance criteria**

- [x] `newsapi_keywords.yaml`: 8 factor sets, 100 calls/day total per PRD2 Section 4.2.
- [x] Round-robin scheduler: one factor per detection cron tick; logs `poll_status` (`ok` | `empty` | `error`).
- [x] 429 rate-limit → RSS fallback (ET Markets, Mint) per PRD2 fallback chain.
- [x] `factor_poll_log` records `factor_id`, `polled_at`, `status`, `article_count`.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/config/newsapi_keywords.yaml` | create | Keywords + allocation |
| `backend/app/sources/newsapi_adapter.py` | modify | Round-robin + logging |
| `backend/db/migrations/00XX_factor_poll_log.sql` | create | Poll audit |
| `backend/tests/test_newsapi_scheduler.py` | create | 100/day cap + rotation |

#### Tasks (checkboxes)

- [x] **4.0** NewsAPI factor keyword scheduler
  - [x] **4.1** `newsapi_keywords.yaml` with PRD2 keyword sets and daily call budgets.
  - [x] **4.2** Round-robin scheduler in adapter; respect 100 calls/day hard cap.
  - [x] **4.3** Migration + write `factor_poll_log` on each poll.
  - [x] **4.4** Distinguish empty (200, zero articles) vs error (429/5xx); trigger RSS fallback on 429.
  - [x] **4.5** Surface last-poll summary in editorial digest email template (log-only fields).
  - [x] **4.6** Tests: cap not exceeded; rotation order; empty vs error classification.

---

### Story P3-S1e — Slow-burn watchlist (G-05)

- **Assigned:** Riley
- **Points:** 3
- **Layers:** DB, API, UI
- **Depends on:** P3-S0
- **Parallel with:** P3-S1c, P3-S1d
- **Gaps:** G-05

**User story**

> As the Product Owner, I want a DB-backed watchlist for slow-burn events (monsoon, budget cycle, regulatory reviews) with a simple review UI, so that long-lead risks are not lost as a solo builder.

**Acceptance criteria**

- [x] `watchlist_items` table per PRD2 schema; 5 seed rows via migration.
- [x] `/editor/watchlist` lists items; status `watching|escalated|closed`.
- [x] One-click **Escalate** creates `events` row with `source='watchlist'` (manual only — no auto-escalation in Phase 3).
- [x] Sunday digest section lists pending watchlist + `dedup_review_queue` (max 10 items).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/00XX_watchlist_items.sql` | create | Table + seeds |
| `backend/app/routes/editor_watchlist.py` | create | CRUD + escalate |
| `frontend/app/(app)/editor/watchlist/page.tsx` | create | Review UI |
| `backend/tests/test_watchlist_escalate.py` | create | Escalate → event row |

#### Tasks (checkboxes)

- [x] **5.0** Slow-burn watchlist
  - [x] **5.1** Migration: `watchlist_items` + 5 seed categories.
  - [x] **5.2** API: list, patch status, `POST .../escalate` → `events` insert.
  - [x] **5.3** `/editor/watchlist` page (table, status dropdown, Escalate button).
  - [x] **5.4** Admin allow-list gate (reuse Phase 1 pattern).
  - [x] **5.5** Digest email template: watchlist + dedup queue section (cap 10).
  - [x] **5.6** Test: escalate creates event with correct category and source.

---

### Story P3-S1f — Market facts freshness + fallback chain (G-06)

- **Assigned:** Sam
- **Points:** 3
- **Layers:** Services, UI
- **Depends on:** P3-S1c
- **Parallel with:** _None until dedup lands_
- **Gaps:** G-06

**User story**

> As a user, I want market fact chips to show freshness (green/amber/red) and the editorial pipeline to pause when critical facts are unavailable, so that stale or missing data never silently drives cards.

**Acceptance criteria**

- [x] Freshness tristate: `fresh` | `stale` | `unavailable` per fact row.
- [x] Revised fallback chains (no investing.com scrape): yfinance → Open Exchange Rates → RBI ref (INR/USD); NSE CSV → CDSL → stale flag.
- [x] `critical_facts.yaml` (≤5 facts): if `unavailable`, card generation held in queue.
- [x] Pulse/Thread chips show freshness dot (existing pattern extended).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/config/critical_facts.yaml` | create | Critical fact IDs |
| `backend/app/services/market_facts_adapters.py` | modify | Tristate + fallbacks |
| `backend/app/services/card_pipeline.py` | modify | Critical-fact hold |
| `backend/tests/test_market_facts_freshness.py` | create | Tristate + hold |
| `frontend/components/market-facts/FreshnessDot.tsx` | modify | Red/amber/green |

#### Tasks (checkboxes)

- [x] **6.0** Market facts freshness + fallback chain
  - [x] **6.1** `critical_facts.yaml` + adapter fallback order per PRD2 (no investing.com).
  - [x] **6.2** Tristate freshness on merged fact stream; staleness thresholds documented.
  - [x] **6.3** Card pipeline: hold queue when any critical fact is `unavailable`.
  - [x] **6.4** `FreshnessDot` on Pulse/Thread market fact chips.
  - [x] **6.5** Loading/error states when facts degraded (editorial queue banner).
  - [x] **6.6** Tests: unavailable critical fact blocks publish path; stale allows with flag.

---

### Story P3-T2 — Data pipeline integration test gate

- **Assigned:** Jordan
- **Points:** 2
- **Layers:** Tests
- **Depends on:** P3-S1c, P3-S1d, P3-S1e, P3-S1f
- **Parallel with:** _None_
- **Gaps:** G-03, G-04, G-05, G-06

**User story**

> As the platform, I want an integration test gate proving dedup, NewsAPI scheduling, watchlist escalation, and freshness gates work together, before confidence scoring depends on clean event rows.

**Acceptance criteria**

- [x] End-to-end fixture: 3 duplicate ingests → 1 event row, `source_count = 3`.
- [x] NewsAPI mock: 8-factor rotation completes without exceeding daily cap.
- [x] Watchlist escalate → event visible in editorial queue.
- [x] Critical fact `unavailable` → card remains `held` in pipeline.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/tests/test_data_pipeline_integration.py` | create | Cross-service E2E |

#### Tasks (checkboxes)

- [x] **7.0** Data pipeline integration test gate
  - [x] **7.1** Fixture ingests for dedup merge assertion.
  - [x] **7.2** Mock NewsAPI rotation + cap test in integration module.
  - [x] **7.3** Watchlist escalate → editorial queue visibility assertion.
  - [x] **7.4** Critical-fact hold assertion on card pipeline.
  - [x] **7.5** CI green required before P3-S1g branch merges.

---

### Story P3-S1g — Rule-based confidence scorer + gate swap (G-01, G-02)

- **Assigned:** Jordan
- **Points:** 8
- **Layers:** Services, DB, Config
- **Depends on:** P3-T2
- **Parallel with:** _None_
- **Gaps:** G-01, G-02

**User story**

> As the platform, I want a debuggable rule-based confidence score (0–1) driving HIGH/MEDIUM/LOW routing, replacing the Phase 1 source-count gate, so that every editorial routing decision has an auditable numeric basis.

**Acceptance criteria**

- [x] `confidence_scorer.py`: weights — source_count 30%, source_quality 30%, factor_db_match 25%, recency 5%, **unique_publisher 10%** (post-dedup counts).
- [x] `confidence_raw` and `confidence_effective` stored; FoW applies `FOG_DAMPENER = 0.6` to effective only.
- [x] Thresholds: HIGH ≥ 0.75 · MEDIUM 0.55–0.74 · LOW &lt; 0.55 (`confidence_config.py`, `calibration_status: provisional`).
- [x] `confidence_score_audit` row per computation (inputs JSON, `scorer_version`).
- [x] `is_major` auto-set when raw ≥ 0.75 AND factor_match ≥ 2 AND category in qualifying set.
- [x] `confidence_gate.route()` replaced — old direct/partial source-count logic removed.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/core/confidence_config.py` | create | Weights, thresholds, dampener |
| `backend/app/services/confidence_scorer.py` | create | Scorer + is_major |
| `backend/app/services/confidence_gate.py` | modify | Float-tier routing |
| `backend/db/migrations/00XX_confidence_audit.sql` | create | Audit table |
| `backend/app/routes/events.py` | modify | `GET .../confidence-breakdown` |
| `backend/tests/test_confidence_scorer.py` | create | Weights + synthetic fixtures |
| `backend/tests/test_confidence_gate.py` | modify | Narrow band tiers |

#### Tasks (checkboxes)

- [x] **8.0** Rule-based confidence scorer + gate swap
  - [x] **8.1** `confidence_config.py` with PO weights/thresholds; `calibration_status: provisional`.
  - [x] **8.2** `confidence_scorer.py` including `unique_publisher_count` (post-dedup, domain-level).
  - [x] **8.3** Migration `confidence_score_audit`; write audit on every upsert.
  - [x] **8.4** Replace `confidence_gate.route()`; wire into signal monitoring + card pipeline.
  - [x] **8.5** `GET /api/events/{id}/confidence-breakdown` JSON (inputs + sources).
  - [x] **8.6** Tests: 20 synthetic events ≥80% tier match hand-grade; narrow MEDIUM band boundaries.

---

### Story P3-S1h — Confidence explainability UI (G-01 Phase 3)

- **Assigned:** Sam
- **Points:** 3
- **Layers:** UI
- **Depends on:** P3-S1g
- **Parallel with:** _None_
- **Gaps:** G-01

**User story**

> As a user reviewing a card, I want to see *why* the system assigned this confidence tier, so that I trust routing decisions when they look surprising.

**Acceptance criteria**

- [x] Thread aside **ConfidenceComposition** loads breakdown API; shows 5 input bars + source list with `retrieved_at`.
- [x] Displays `confidence_raw`, `confidence_effective`, tier label, FoW dampener when active.
- [x] Loading and error states; no layout shift on Pulse/Thread (perf: breakdown fetched on expand only).
- [x] `source_count > 5` shows editorial escalation badge.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/thread/_components/aside/ConfidenceComposition.tsx` | modify | Breakdown UI |
| `frontend/lib/api/confidenceBreakdown.ts` | create | API client |
| `frontend/lib/api/confidenceBreakdown.test.ts` | create | Client + shape test |

#### Tasks (checkboxes)

- [x] **9.0** Confidence explainability UI
  - [x] **9.1** API client for `confidence-breakdown` endpoint.
  - [x] **9.2** Expandable panel: five weighted inputs + tier explanation copy.
  - [x] **9.3** Source list with timestamps; FoW dampener callout when effective &lt; raw.
  - [x] **9.4** Fetch on expand only (lazy); skeleton loading state.
  - [x] **9.5** Escalation badge when `force_editorial_review`.
  - [x] **9.6** Component test: renders breakdown fixture; error state on 404.

---

### Story P3-T3 — Confidence scoring verification gate

- **Assigned:** Riley
- **Points:** 2
- **Layers:** Tests
- **Depends on:** P3-S1g, P3-S1h
- **Parallel with:** _None_
- **Gaps:** G-01, G-02

**User story**

> As the platform, I want proof that the new scorer, narrow thresholds, and explainability API agree before editorial hard gates depend on scores.

**Acceptance criteria**

- [x] API test: breakdown sums match stored `confidence_raw` within epsilon.
- [x] FoW active: effective score = raw × 0.6; tier derived from effective.
- [x] UI test (RTL): expanded panel shows all five inputs from fixture.
- [x] Regression: signal monitor uses new gate tiers (no Phase 1 count heuristic).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/tests/test_confidence_breakdown_api.py` | create | API contract |
| `backend/tests/test_confidence_scoring_gate.py` | create | P3-T3 verification gate |
| `frontend/app/(app)/thread/_components/aside/ConfidenceComposition.test.tsx` | create | UI fixture |
| `docs/plans/phase3-calibration.md` | create | Day 30/60 ritual |

#### Tasks (checkboxes)

- [x] **10.0** Confidence scoring verification gate
  - [x] **10.1** API test: breakdown vs stored scores + FoW dampener.
  - [x] **10.2** Signal monitor integration test with tier fixtures.
  - [x] **10.3** RTL test: ConfidenceComposition expand/collapse + five inputs.
  - [x] **10.4** Document Day 30/60 recalibration ritual in `docs/plans/phase3-calibration.md`.
  - [x] **10.5** CI required green before P3-S1i starts.

---

### Story P3-S1i — Number validator hard publish gate (G-07)

- **Assigned:** Riley
- **Points:** 5
- **Layers:** API, UI, Services
- **Depends on:** P3-T3
- **Parallel with:** _None_
- **Gaps:** G-07

**User story**

> As the editor, I cannot publish a card until every numeric token in Insight/Context appears in Evidence, so that the LLM-never-invents-numbers invariant is enforced in software, not habit.

**Acceptance criteria**

- [x] `number_validator.check()` returns structured `FAIL` with ungrounded numbers by sentence.
- [x] `POST /api/cards/{id}/publish` returns **422** on FAIL (no override endpoint).
- [x] Publish button disabled on card load when validator ≠ PASS.
- [x] Comparative quantifiers ("doubled", "record high") logged as soft warnings only.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/number_validator.py` | modify | Structured FAIL |
| `backend/app/routes/cards.py` | modify | 422 on publish |
| `frontend/app/(app)/editor/cards/[id]/PublishGate.tsx` | create | Disabled + diff UI |
| `backend/tests/test_number_validator.py` | extend | Ungrounded cases |
| `backend/tests/test_publish_gate.py` | create | 422 + PASS paths |

#### Tasks (checkboxes)

- [x] **11.0** Number validator hard publish gate
  - [x] **11.1** Extend validator: structured `ungrounded[]` + `missing_provenance[]`.
  - [x] **11.2** Publish route returns 422 with diff payload on FAIL.
  - [x] **11.3** `PublishGate.tsx`: disable Publish; render sentence-level diff list.
  - [x] **11.4** Soft-warning log for comparative quantifiers (non-blocking).
  - [x] **11.5** Loading/error on card load when validator service unavailable.
  - [x] **11.6** Tests: publish blocked with ungrounded number; passes when Evidence added.

---

### Story P3-S1j — Editorial checklist — 4 automated + 1 manual (G-15)

- **Assigned:** Riley
- **Points:** 3
- **Layers:** Services, UI
- **Depends on:** P3-S1i
- **Parallel with:** P3-S1k
- **Gaps:** G-15

**User story**

> As the editor, I want five checklist items with four automated PASS checks before Publish activates, so that solo-builder fatigue cannot skip SEBI-critical steps.

**Acceptance criteria**

- [x] Auto: (1) number validator PASS, (2) dissent len &gt; 100, (3) max Evidence age ≤ 18 months, (4) SEBI keyword scan PASS with allowlist (`repo rate hold` allowed).
- [x] Manual: (5) plain English — editor tick required.
- [x] All five PASS → Publish enabled (still requires number validator PASS).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/editorial_checklist.py` | create | Orchestrator |
| `backend/app/services/sebi_compliance_scan.py` | create | Pattern scan |
| `backend/app/config/sebi_compliance_patterns.yaml` | create | Blocked terms + allowlist |
| `frontend/app/admin/review/_components/ChecklistPanel.tsx` | modify | 4 auto + 1 manual |
| `backend/tests/test_editorial_checklist.py` | create | All five gates |

#### Tasks (checkboxes)

- [x] **12.0** Editorial checklist — 4 automated + 1 manual
  - [x] **12.1** `editorial_checklist.py` runs four automated checks on card load.
  - [x] **12.2** `sebi_compliance_scan.py` + YAML allowlist patterns.
  - [x] **12.3** Evidence freshness auto-check (18-month max age).
  - [x] **12.4** `ChecklistPanel.tsx`: PASS/FAIL per item; manual tick for plain English.
  - [x] **12.5** PublishGate integrates checklist — all PASS required.
  - [x] **12.6** Tests: SEBI false positive on "hold rate"; block on "buy"; dissent length.

---

### Story P3-S1k — Targeted section regen (G-09)

- **Assigned:** Sam
- **Points:** 3
- **Layers:** API, UI
- **Depends on:** P3-S1i
- **Parallel with:** P3-S1j
- **Gaps:** G-09

**User story**

> As the editor, when I reject one ICE section I want only that section regenerated with my annotation, so that approved sections and LLM cost are preserved.

**Acceptance criteria**

- [x] `POST /api/cards/{id}/regenerate-section` with `section` + `editor_note` (max 500 chars).
- [x] Full regen available but confirm if `full_regen_count >= 1`; blocked at ≥2 without PO flag clear.
- [x] `regen_history` JSONB on card records each regen.
- [x] Post-regen: number_validator + consistency check (entity names vs approved sections).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/card_regen.py` | create | Section + full regen |
| `backend/app/services/consistency_check.py` | create | Post-regen validation |
| `backend/app/routes/cards.py` | extend | Regen endpoints |
| `frontend/app/(app)/editor/cards/[id]/RegenSection.tsx` | create | Section picker + note |
| `backend/tests/test_card_regen.py` | create | Section-only regen |

#### Tasks (checkboxes)

- [x] **13.0** Targeted section regen
  - [x] **13.1** `card_regen.py`: single-section LLM call with approved sections as read-only context.
  - [x] **13.2** `regen_history` JSONB migration + write on each regen.
  - [x] **13.3** Full regen tiered confirm + `full_regen_count` guard.
  - [x] **13.4** `RegenSection.tsx`: section select, note field, submit + loading/error.
  - [x] **13.5** Post-regen validator + consistency check hook.
  - [x] **13.6** Tests: only target section hash changes; full regen count enforced.

---

### Story P3-T4 — Editorial integrity verification gate

- **Assigned:** Jordan
- **Points:** 2
- **Layers:** Tests
- **Depends on:** P3-S1i, P3-S1j, P3-S1k
- **Parallel with:** _None_
- **Gaps:** G-07, G-09, G-15

**User story**

> As the platform, I want end-to-end proof that publish is impossible until number validation and checklist pass, before FoW changes confidence routing.

**Acceptance criteria**

- [x] E2E: card with ungrounded number → Publish 422 + button disabled.
- [x] E2E: fix Evidence → validator PASS → checklist auto items PASS → manual tick → publish 200.
- [x] Section regen does not bypass validator.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/tests/test_editorial_integrity_e2e.py` | create | Publish gate E2E |

#### Tasks (checkboxes)

- [x] **14.0** Editorial integrity verification gate
  - [x] **14.1** E2E fixture card: fail publish without Evidence.
  - [x] **14.2** E2E: full happy path through checklist + publish.
  - [x] **14.3** Regen section then fail validator → publish still blocked.
  - [x] **14.4** CI gate before P3-S1l branch merges.
  - [x] **14.5** Link test evidence in Phase 3 go/no-go checklist template (P3-S8 prep).

---

### Story P3-S1l — Fog of War `is_major` model + named banner (G-10)

- **Assigned:** Jordan
- **Points:** 5
- **Layers:** Services, DB, UI
- **Depends on:** P3-T4
- **Parallel with:** _None_
- **Gaps:** G-10

**User story**

> As a user, when three or more major events are active I want Fog of War to activate with named reasons, and confidence dampening applied via `confidence_effective`, not opaque heuristics.

**Acceptance criteria**

- [ ] FoW when `COUNT(is_major AND active) >= 3` (configurable threshold default 3).
- [ ] `is_major` from scorer unless `is_major_override` set (audit: who/when).
- [ ] Feed returns `fog_of_war_reason.active_major_events[]` for banner.
- [ ] `FOG_MODEL=heuristic` feature flag (default); P3-S2 switches to `interaction` later.
- [ ] Never mutate `confidence_raw` in place; dampener writes `card_confidence_history` only.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/fog_of_war.py` | create | Extract + detect |
| `backend/app/services/feed.py` | modify | Named reason payload |
| `backend/app/core/feature_flags.py` | create | `FOG_MODEL` |
| `frontend/app/(app)/pulse/_components/FogOfWarBanner.tsx` | modify | Named events |
| `backend/tests/test_fog_of_war_detector.py` | rewrite | `is_major` based |

#### Tasks (checkboxes)

- [ ] **15.0** Fog of War `is_major` model + named banner
  - [ ] **15.1** `fog_of_war.py`: detection on `is_major` events; override columns migration if missing.
  - [ ] **15.2** Feed API: `fog_of_war` + `fog_of_war_reason` structured payload.
  - [ ] **15.3** `FogOfWarBanner.tsx`: list active major headlines + factor overlap summary.
  - [ ] **15.4** `feature_flags.py`: `FOG_MODEL` env; heuristic path only in this story.
  - [ ] **15.5** Verify dampener uses `confidence_effective`; history table writes on dampen.
  - [ ] **15.6** Tests: 3 majors → fog true; override respected; banner JSON contract.

---

### Story P3-S1m — Signal override log + FP measurement (G-11)

- **Assigned:** Riley
- **Points:** 3
- **Layers:** DB, API, UI, CI
- **Depends on:** P3-S1l
- **Parallel with:** _None_
- **Gaps:** G-11

**User story**

> As the Product Owner, I want every dismissed auto-signal to record a structured outcome so that false-positive rate is measurable and feeds threshold recalibration.

**Acceptance criteria**

- [ ] `signal_override_log` table per PRD2 Section 6.4.
- [ ] Dismiss modal: mandatory `final_outcome` ∈ {confirmed, incorrect, ambiguous}.
- [ ] Monthly GH Action writes `docs/notes/signal-override-log-YYYY-MM.md`; opens issue if FP &gt; 10%.
- [ ] FP rate formula documented in note; links to `confidence_config.py` for recalibration.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/00XX_signal_override_log.sql` | create | Schema |
| `backend/app/routes/signals.py` | modify | Mandatory override |
| `frontend/app/(app)/editor/signals/OverrideModal.tsx` | create | Structured dismiss |
| `.github/workflows/signal_fp_monthly.yml` | create | Monthly report |
| `backend/tests/test_signal_override_log.py` | create | FP formula unit |

#### Tasks (checkboxes)

- [ ] **16.0** Signal override log + FP measurement
  - [ ] **16.1** Migration `signal_override_log` + indexes.
  - [ ] **16.2** API: dismiss requires `final_outcome`; no silent dismiss.
  - [ ] **16.3** `OverrideModal.tsx` integrated into signal queue UI.
  - [ ] **16.4** `signal_fp_monthly.yml` report + issue creation on &gt;10%.
  - [ ] **16.5** `docs/plans/phase3-calibration.md`: tie FP rate to Day 30/60 threshold review.
  - [ ] **16.6** Tests: FP rate calculation on fixture overrides.

---

### Story P3-T5 — Fog of War + signal measurement test gate

- **Assigned:** Sam
- **Points:** 2
- **Layers:** Tests
- **Depends on:** P3-S1l, P3-S1m
- **Parallel with:** P3-S1a (may start after P3-T2)
- **Gaps:** G-10, G-11

**User story**

> As the platform, I want verification that FoW banner, dampener, and override logging work together before the NLP batch job adds load.

**Acceptance criteria**

- [ ] Feed integration test: 3 synthetic `is_major` events → `fog_of_war: true` + named list.
- [ ] Effective scores dampened; `confidence_raw` unchanged on event row.
- [ ] Override dismiss without outcome → 400; with `incorrect` → appears in FP query.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/tests/test_fog_signal_integration.py` | create | FoW + override E2E |

#### Tasks (checkboxes)

- [ ] **17.0** Fog of War + signal measurement test gate
  - [ ] **17.1** Feed test with synthetic majors seed fixture.
  - [ ] **17.2** Assert raw vs effective scores under FoW.
  - [ ] **17.3** Override API mandatory field tests.
  - [ ] **17.4** CI green before P3-S1a NLP workflow merges.
  - [ ] **17.5** Export fixture IDs for P3-S2 backtest script (prep).

---

### Story P3-S1a — NLP filings extraction service (G-08, G-12)

- **Assigned:** Jordan
- **Points:** 7
- **Layers:** Services, DB, GitHub Actions
- **Depends on:** P3-T2 (data pipeline stable)
- **Parallel with:** P3-T5, P3-S3
- **Gaps:** G-08, G-12

**User story**

> As the platform, I want a **GitHub Actions** nightly job that ingests NSE/BSE filings and proposes factor-sensitivity updates via **Gemini Flash**, with grounded extraction only, so that manual weekly review is replaced by a verify-on-approve pipeline without Render cold-start failures.

**Acceptance criteria**

- [ ] Workflow `nlp_filings_extract.yml` runs 1am IST; `workflow_dispatch` for manual runs; 50-min timeout.
- [ ] `render_keepalive.yml` pings `/health` every 10 min during market hours (weekdays).
- [ ] Model from `NLP_EXTRACTION_MODEL` env (default active Gemini Flash); health check step before batch.
- [ ] Proposals → `factor_sensitivity_proposals`; never overwrites live sensitivities.
- [ ] `source_guard`: every extracted value must appear in source excerpt.
- [ ] `job_runs` table records success/failure; failure opens GitHub Issue `nlp-job-failure`.
- [ ] Idempotent on `(filing_url, instrument_id, factor_id)`.

**Tech notes**

- GH Actions uses Session pooler `SUPABASE_DB_URL`. spaCy model cached via Actions cache. Card synthesis remains Gemini Pro on Render.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `.github/workflows/nlp_filings_extract.yml` | create | Nightly job |
| `.github/workflows/render_keepalive.yml` | create | Keep-alive |
| `backend/app/jobs/nlp_filings_extract.py` | create | Job entrypoint |
| `backend/app/services/nlp/filings_loader.py` | create | NSE/BSE fetch + cache |
| `backend/app/services/nlp/preprocess.py` | create | spaCy candidates |
| `backend/app/services/nlp/extractor.py` | create | Gemini Flash JSON |
| `backend/app/services/nlp/source_guard.py` | create | Grounding check |
| `backend/db/migrations/00XX_factor_sensitivity_proposals.sql` | create | Proposals table |
| `backend/db/migrations/00XX_job_runs.sql` | create | Job observability |
| `backend/requirements-nlp.txt` | create | NLP deps |
| `backend/tests/test_extractor_rejects_out_of_source_numbers.py` | create | Hallucination guard |
| `backend/tests/test_filings_extract_idempotent.py` | create | Idempotency |

#### Tasks (checkboxes)

- [ ] **18.0** NLP filings extraction service (GH Actions + Gemini Flash)
  - [ ] **18.1** Migrations: `factor_sensitivity_proposals` + `job_runs`.
  - [ ] **18.2** `filings_loader` + local cache; `preprocess` + `extractor` (Flash, JSON-strict).
  - [ ] **18.3** `source_guard` + persist proposals; idempotent unique constraint.
  - [ ] **18.4** `nlp_filings_extract.yml` + `render_keepalive.yml`; secrets documented in `scripts/README.md`.
  - [ ] **18.5** Failure → GitHub Issue; success/failure written to `job_runs`.
  - [ ] **18.6** Tests: out-of-source rejection; idempotency; mock workflow env health check.

---

### Story P3-S1b — Human-in-loop review tooling for NLP proposals

- **Assigned:** Riley
- **Points:** 5
- **Layers:** UI, API, DB
- **Depends on:** P3-S1a
- **Parallel with:** P3-S2 (spec only until soak complete), P3-S3
- **Gaps:** _(original P3-S1b)_

**User story**

> As the Product Owner, I want an internal review screen listing NLP-proposed factor-sensitivity changes beside live values and source excerpts, so that I can approve or reject in seconds.

**Acceptance criteria**

- [ ] `/admin/factor-db/proposals` lists `pending` proposals sorted by confidence desc.
- [ ] Approve → upserts live `instrument_factor_sensitivity` preserving provenance; Reject → `rejected` + note.
- [ ] Bulk-approve only when confidence ≥0.9 and MMJ ∈ {MEASURED, MODELLED}.
- [ ] Digest shows last NLP `job_runs` status (success/failure + timestamp).
- [ ] Audit log per decision.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/admin/factor-db/proposals/page.tsx` | create | Review list |
| `frontend/app/admin/factor-db/proposals/_components/ProposalRow.tsx` | create | Row actions |
| `backend/app/api/factor_db_proposals.py` | create | List/approve/reject |
| `backend/app/services/factor_db_proposals.py` | create | Workflow |
| `backend/db/migrations/00XX_factor_db_proposal_audit.sql` | create | Audit |
| `backend/tests/test_proposal_approve_upserts_live.py` | create | Approve path |

#### Tasks (checkboxes)

- [ ] **19.0** Human-in-loop review tooling for NLP proposals
  - [ ] **19.1** Migration: `factor_db_proposal_audit`.
  - [ ] **19.2** APIs: list pending, approve, reject, bulk-approve with gating.
  - [ ] **19.3** Approve service: upsert live row + immutable provenance fields.
  - [ ] **19.4** Admin UI: `ProposalRow` + source excerpt highlight.
  - [ ] **19.5** Digest integration: last `job_runs` NLP status line.
  - [ ] **19.6** Tests: approve upsert; bulk gate; audit row written.

---

### Story P3-S2 — Compound-event Fog of War — interaction model

- **Assigned:** Jordan
- **Points:** 6
- **Layers:** Services, DB, UI
- **Depends on:** P3-S0 + **30 days synthetic live** + P3-S1l
- **Parallel with:** P3-S1b, P3-S5
- **Gaps:** G-10 (Phase 3 model), original P3-S2

> **Gate:** Do not start implementation until synthetic seed has been live ≥30 days and `card_confidence_history` has accumulated.

**User story**

> As the platform, I want interaction detection between simultaneously active events to dampen confidence structurally, replacing the fixed ≥3 majors heuristic when the model is confident.

**Acceptance criteria**

- [ ] `interaction_detector.analyse(active_events)` returns pairs/triples with factor overlap + suggested dampener.
- [ ] `FOG_MODEL=interaction` enables model path; `heuristic` remains fallback when model abstains.
- [ ] Dampener writes `card_confidence_history` only; never mutates original values.
- [ ] Backtest script replays synthetic + accumulated history → `notes/fog-of-war-backtest.md`.
- [ ] Ship behind feature flag; revert to heuristic if FP &gt;10% in first month.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/interaction_detector.py` | create | Factor-overlap model |
| `backend/app/services/confidence_dampener.py` | create | Apply dampener |
| `backend/db/migrations/00XX_card_confidence_history.sql` | create | History |
| `scripts/fog_of_war_backtest.py` | create | Replay report |
| `backend/tests/test_interaction_detector.py` | create | Fixture pairs |

#### Tasks (checkboxes)

- [ ] **20.0** Compound-event Fog of War — interaction model
  - [ ] **20.1** Migration `card_confidence_history` if not present from P3-S1l.
  - [ ] **20.2** `interaction_detector.analyse()` + abstain path to heuristic.
  - [ ] **20.3** `confidence_dampener.apply()` + recompute job on new active event.
  - [ ] **20.4** Feature flag switch `FOG_MODEL`; banner shows interaction reason string.
  - [ ] **20.5** Backtest script + markdown report template.
  - [ ] **20.6** Tests: detection fixtures; non-destructive dampener; flag fallback.

---

### Story P3-S3 — SEBI compliance audit + mandatory legal-review tracker

- **Assigned:** Riley
- **Points:** 4
- **Layers:** Compliance, UI, Docs
- **Depends on:** Phase 1 P1-S14
- **Parallel with:** P3-S1a, P3-S5
- **Gaps:** _(original P3-S3)_

**User story**

> As the Product Owner, I want a formal SEBI legal review captured in a tracker with sign-off lines, so that any future public launch cannot ship without explicit legal approval.

**Acceptance criteria**

- [ ] `notes/sebi-legal-review-tracker.md` lists every screen + editorial promise with sign-off lines.
- [ ] Lawyer review completed; notes logged.
- [ ] `/about-this-analysis` consolidates SEBI framing.
- [ ] Tester briefing hardened: IP + timestamp + optional PDF.
- [ ] PRD2 intelligence UI (confidence breakdown, FoW banner) included in review scope.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `notes/sebi-legal-review-tracker.md` | create | Tracker (gitignored) |
| `frontend/app/about-this-analysis/page.tsx` | create | Public about |
| `frontend/app/(app)/tester-briefing/page.tsx` | modify | PDF + capture |
| `backend/app/api/tester_briefing.py` | modify | IP + timestamp |
| `backend/tests/test_tester_briefing_capture.py` | create | Capture test |

#### Tasks (checkboxes)

- [ ] **21.0** SEBI compliance audit + mandatory legal-review tracker
  - [ ] **21.1** Draft tracker including PRD2 UI surfaces (confidence breakdown, FoW, checklist).
  - [ ] **21.2** Complete lawyer review; log notes inline.
  - [ ] **21.3** Open `compliance`-labelled PRs for required copy changes.
  - [ ] **21.4** Build `/about-this-analysis`.
  - [ ] **21.5** Harden tester-briefing: IP + timestamp + PDF download.
  - [ ] **21.6** Tests: briefing capture; about link in app footer.

---

### Story P3-S4 — Productisation assessment + RA registration research dossier

- **Assigned:** Riley
- **Points:** 3
- **Layers:** Strategy, Docs
- **Depends on:** P3-S3, P3-S5
- **Parallel with:** _None_
- **Gaps:** _(original P3-S4)_

**User story**

> As the Product Owner, I want a dossier with RA-registration research, pricing options, and go/wait/no-go recommendation, so Phase 3 ends with an evidence-backed direction (without assuming P3-S6/S7 ship).

**Acceptance criteria**

- [ ] `notes/productisation-assessment.md`: RA prerequisites, costs, timelines, gap analysis, 3 pricing models, scalability headline from P3-S5.
- [ ] Explicit note: P3-S6/S7 deferred per PRD2 G-14 unless gate green + RA path confirmed.
- [ ] External practitioner dissent captured.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `notes/productisation-assessment.md` | create | Dossier (gitignored) |

#### Tasks (checkboxes)

- [ ] **22.0** Productisation assessment + RA registration research dossier
  - [ ] **22.1** Research SEBI RA prerequisites + costs.
  - [ ] **22.2** Map FinnWise gaps including PRD2 intelligence controls.
  - [ ] **22.3** Draft three pricing models (for hypothetical post-registration future).
  - [ ] **22.4** Incorporate P3-S5 scalability headline numbers.
  - [ ] **22.5** Go/wait/no-go recommendation with named conditions.
  - [ ] **22.6** External practitioner dissent captured.

---

### Story P3-S5 — Scalability + observability hardening

- **Assigned:** Jordan
- **Points:** 5
- **Layers:** Ops, Infra, Tests
- **Depends on:** Phase 2 P2-S13
- **Parallel with:** P3-S1a, P3-S3
- **Gaps:** _(original P3-S5)_

**User story**

> As the platform owner, I want load-tested SLOs and hosted observability, so that scaling decisions rest on evidence.

**Acceptance criteria**

- [ ] k6 load tests: 200 concurrent users on Pulse, Thread, Lens.
- [ ] `docs/plans/phase3-slos.md` documents SLOs aligned with cross-phase standards.
- [ ] Sentry on frontend + backend; structured logs to free-tier provider.
- [ ] Confidence breakdown API included in Pulse p95 budget.
- [ ] Baseline numbers handed to P3-S4.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `scripts/load_test_pulse.k6.js` | create | k6 |
| `scripts/load_test_thread.k6.js` | create | k6 |
| `scripts/load_test_lens.k6.js` | create | k6 |
| `docs/plans/phase3-slos.md` | create | SLO doc |
| `backend/app/core/sentry.py` | create | Sentry |
| `frontend/instrumentation.ts` | create | Sentry |
| `.github/workflows/load-tests.yml` | create | Weekly |

#### Tasks (checkboxes)

- [ ] **23.0** Scalability + observability hardening
  - [ ] **23.1** Author `phase3-slos.md` including confidence breakdown latency budget.
  - [ ] **23.2** Sentry init frontend + backend; DSNs in `.env.local`.
  - [ ] **23.3** k6 scripts for Pulse, Thread, Lens.
  - [ ] **23.4** Weekly load-test workflow; capture p95 + error rate.
  - [ ] **23.5** Alerts: error budget burn + p95 violation.
  - [ ] **23.6** Hand baseline summary to Riley for P3-S4.

---

### Story P3-S8 — Phase 3 launch-readiness gate + go/no-go checklist

- **Assigned:** Riley
- **Points:** 2
- **Layers:** Governance
- **Depends on:** P3-S3, P3-S4, P3-S5, P3-T4, P3-T5
- **Parallel with:** _None_
- **Gaps:** _(original P3-S8)_

**User story**

> As the Product Owner, I want an explicit go/no-go checklist with evidence links, so that deferred stories (P3-S6/S7) only activate after a documented green light.

**Acceptance criteria**

- [ ] `docs/plans/phase3-go-no-go.md` covers: legal sign-off (P3-S3); SLOs (P3-S5); productisation (P3-S4); PRD2 intelligence gates (T1–T5 evidence); synthetic isolation; FP rate ≤10% or remediation plan.
- [ ] P3-S6/S7 listed as **deferred** with activation conditions.
- [ ] Decision logged with timestamp.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `docs/plans/phase3-go-no-go.md` | create | Checklist |

#### Tasks (checkboxes)

- [ ] **24.0** Phase 3 launch-readiness gate + go/no-go checklist
  - [ ] **24.1** Draft checklist with PRD2 test-gate evidence links.
  - [ ] **24.2** Walk items with owners; capture status.
  - [ ] **24.3** Hold review; log go/wait/no-go + conditions for P3-S6/S7.
  - [ ] **24.4** Update PR template: `phase3-gate: green` for any future public-launch work.

---

### Story P3-S9 — The Map — final public version + sector deep-dive interactives

- **Assigned:** Sam
- **Points:** 6
- **Layers:** UI, API
- **Depends on:** Phase 2 P2-S11
- **Parallel with:** P3-S3, P3-S5 (no P3-S6 marketing dependency — G-14 deferral)
- **Gaps:** _(original P3-S9, adjusted)_

**User story**

> As a signed-in user (and future public visitor when marketing ships), I want polished Map sector deep-dives with interactive sensitivity matrices, reinforcing the educational research posture.

**Acceptance criteria**

- [ ] Map reachable from `(app)` route group; structure allows future `(marketing)` shell without refactor.
- [ ] Sector deep-dive: sensitivity matrix (keyboard + hover), event-history strip from `track_record` (synthetic excluded).
- [ ] A11y: keyboard nav, screen-reader labels, contrast.
- [ ] Language audit: no buy/sell/hold; passes P3-S3 vocabulary.
- [ ] Lighthouse mobile budgets per cross-phase standards.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/map/[slug]/page.tsx` | modify | Deep-dive |
| `frontend/components/Map/SensitivityMatrix.tsx` | create | Shared matrix |
| `frontend/components/Map/EventHistoryStrip.tsx` | create | Track record strip |
| `frontend/components/Map/SensitivityMatrix.test.tsx` | create | a11y |
| `frontend/components/Map/EventHistoryStrip.test.tsx` | create | Data binding |

#### Tasks (checkboxes)

- [ ] **25.0** The Map — final version + sector deep-dive interactives
  - [ ] **25.1** Extract `components/Map/*` shared components.
  - [ ] **25.2** `SensitivityMatrix` interactive + MMJ-coloured cells.
  - [ ] **25.3** `EventHistoryStrip` from `track_record` (synthetic filtered).
  - [ ] **25.4** App routes wired; marketing shell stub commented for post-gate.
  - [ ] **25.5** A11y pass + Lighthouse on representative sector page.
  - [ ] **25.6** Tests: keyboard nav; event strip binding; synthetic exclusion.

---

### Deferred — P3-S6 / P3-S7 (G-14 appendix only)

> **No active tasks.** Revisit only when P3-S8 returns **go** AND SEBI RA registration path is confirmed per P3-S4 dossier. Original story definitions remain in git history; do not create `(marketing)` routes or billing tables until then.

| Story | Original scope | Points (reference) |
|-------|----------------|-------------------|
| P3-S6 | Public marketing + waitlist | 6 (deferred) |
| P3-S7 | Pricing + paywall | 5 (deferred) |

---

## Risks

- **Dedup false merge (G-03 all-category headline_hash)** — Sunday `dedup_review_queue` review; cap 10 items/week.
- **Synthetic data leak** — P3-T1 triple-layer tests must stay green in CI.
- **Confidence bootstrap arbitrariness** — Label `provisional`; Day 30/60 recalibration tied to P3-S1m FP rate.
- **NLP on GH Actions secrets exposure** — Repository secrets only; never log filing content or API keys.
- **FoW interaction model too aggressive (P3-S2)** — Feature flag + 30-day soak + backtest mandatory.
- **Solo builder skips manual checklist tick** — 4/5 automated; only plain English remains manual.
- **P3-S6/S7 scope creep** — Explicitly removed from active board per G-14.

## Recommendations

- **Week 1:** Jordan P3-S0 → Riley P3-T1 → Jordan P3-S1c; Sam P3-S1d; Riley P3-S1e in parallel.
- **Week 2:** Sam P3-S1f → Jordan P3-T2 → Jordan P3-S1g → Sam P3-S1h → Riley P3-T3 → Riley P3-S1i.
- **Week 3:** Riley P3-S1j ∥ Sam P3-S1k → Jordan P3-T4 → Jordan P3-S1l → Riley P3-S1m → Sam P3-T5 → Jordan P3-S1a.
- **Week 4+:** Riley P3-S1b; parallel Riley P3-S3 + Jordan P3-S5; Sam P3-S9.
- **Day 30 after P3-S0:** Begin P3-S2 interaction model only if synthetic history sufficient.
- **Do not** create P3-S6/S7 tasks until P3-S8 green + RA path confirmed.

---

## How to execute Phase 3

**PRD2 foundation (Weeks 1–4):**

1. P3-S0 → P3-T1 → `{P3-S1c, P3-S1d, P3-S1e}` → P3-S1f → P3-T2  
2. P3-S1g → P3-S1h → P3-T3 → P3-S1i → `{P3-S1j, P3-S1k}` → P3-T4  
3. P3-S1l → P3-S1m → P3-T5 → P3-S1a → P3-S1b  
4. P3-S0 + 30 days → P3-S2  

**Strategic track (Months 10–18, parallel after Week 4):**

5. `{P3-S3, P3-S5}` → P3-S4 → P3-S8  
6. P3-S9 anytime after Week 2 (independent of gate)  
7. P3-S6/S7 **only if** P3-S8 go + RA path  

**Parallel pairs:** `{S1d, S1e}` · `{S1j, S1k}` · `{S1a, S3, S5}` · `{S9, S5}`

---

## Appendix — Taskmaster-style export (per developer)

### Notes

- Backend tests: `cd backend && pytest [path]`
- Frontend tests: `cd frontend && pnpm test [path]`
- New env keys: `NLP_EXTRACTION_MODEL`, `FOG_MODEL`, `SENTRY_DSN_*` (P3-S5)
- PRD2 invariants: no buy/sell/hold; MMJ on every quantitative claim; `confidence_raw` never mutated by FoW dampener

### Relevant Files (rollup)

- `backend/app/core/confidence_config.py`, `feature_flags.py`
- `backend/app/services/confidence_scorer.py`, `event_dedup.py`, `fog_of_war.py`, `card_regen.py`, `editorial_checklist.py`, `sebi_compliance_scan.py`, `nlp/**`
- `backend/app/config/*.yaml` — entity_map, newsapi_keywords, critical_facts, sebi_compliance_patterns
- `backend/scripts/seed_synthetic_events.py`, `seed_data/synthetic_events.json`
- `backend/db/migrations/00XX_*.sql` — synthetic, dedup, watchlist, confidence, proposals, override log, job_runs
- `.github/workflows/nlp_filings_extract.yml`, `render_keepalive.yml`, `signal_fp_monthly.yml`, `load-tests.yml`
- `frontend/app/(app)/editor/**`, `thread/.../ConfidenceComposition.tsx`, `pulse/.../FogOfWarBanner.tsx`
- `frontend/app/admin/factor-db/proposals/**`, `components/Map/**`
- `docs/plans/phase3-calibration.md`, `phase3-slos.md`, `phase3-go-no-go.md`
- `docs/notes/signal-override-log-*.md`

### Tasks by developer — Jordan

- [ ] **1.0** Synthetic historical seed + triple-layer isolation
- [ ] **3.0** Event de-duplication pipeline
- [x] **7.0** Data pipeline integration test gate
- [x] **8.0** Rule-based confidence scorer + gate swap
- [ ] **14.0** Editorial integrity verification gate
- [ ] **15.0** Fog of War `is_major` model + named banner
- [ ] **18.0** NLP filings extraction service (GH Actions + Gemini Flash)
- [ ] **20.0** Compound-event Fog of War — interaction model
- [ ] **23.0** Scalability + observability hardening

### Tasks by developer — Sam

- [x] **4.0** NewsAPI factor keyword scheduler
- [ ] **6.0** Market facts freshness + fallback chain
- [x] **9.0** Confidence explainability UI
- [x] **13.0** Targeted section regen
- [ ] **17.0** Fog of War + signal measurement test gate
- [ ] **25.0** The Map — final version + sector deep-dive interactives

### Tasks by developer — Riley

- [ ] **2.0** Synthetic isolation verification gate
- [ ] **5.0** Slow-burn watchlist
- [x] **10.0** Confidence scoring verification gate
- [ ] **11.0** Number validator hard publish gate
- [ ] **12.0** Editorial checklist — 4 automated + 1 manual
- [ ] **16.0** Signal override log + FP measurement
- [ ] **19.0** Human-in-loop review tooling for NLP proposals
- [ ] **21.0** SEBI compliance audit + mandatory legal-review tracker
- [ ] **22.0** Productisation assessment + RA registration research dossier
- [ ] **24.0** Phase 3 launch-readiness gate + go/no-go checklist

---

_Plan version: PRD2 merged · PO decisions 25 May 2026 · Parent tasks 1.0–25.0 global numbering_
