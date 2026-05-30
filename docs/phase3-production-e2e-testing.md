# Phase 3 — Production End-to-End Testing Guide

**Version:** v1.0  
**Date:** 31-05-2026  
**Scope:** First **14** Phase 3 deliverables (tasks **1.0**–**14.0** in `docs/plans/finnwise-phase3-implementation-tasks.md`)  
**Out of scope:** P3-S1l (FoW named banner), P3-S1m (signal override log), P3-T5 — not yet in this pause window  
**Parent plan:** `docs/plans/finnwise-phase3-implementation-tasks.md`  
**Go/no-go template:** `docs/plans/phase3-go-no-go.md`

---

## How to use this document

You are validating **production behaviour**, not re-running CI. CI already proved unit/integration contracts; this guide proves **deployed config, migrations, cron, UI, and operator workflows** work together on live infrastructure.

For each scenario:

| Column | Meaning |
|--------|---------|
| **ID** | Traceable reference (e.g. `P3-S0-01`) |
| **Where** | URL, API, SQL console, or Render/Vercel dashboard |
| **Role in the app** | Why this matters to users or editorial trust |
| **Steps** | Keystroke-level procedure |
| **Expected** | Pass criteria |
| **Edge / regression** | Non-happy paths and Phase 1/2 surfaces that must not break |

**Pass rule:** Record screenshot or curl output + timestamp. Mark **PASS / FAIL / BLOCKED** in the evidence table at the end.

---

## 0. Pre-flight — run once before scenario testing

Complete this checklist **after** you commit and deploy, **before** opening user-facing scenarios.

### 0.1 Deploy and migration order

| Step | Where | Action | Expected |
|------|-------|--------|----------|
| PF-01 | Local / CI | `python -m ruff check backend` && `python -m pytest -q backend/tests` | Green (baseline before deploy) |
| PF-02 | Render dashboard → **investment-assistant** service | Confirm latest commit deployed; note deploy timestamp | Status **Live**; build succeeded |
| PF-03 | Vercel dashboard → **investment-assistant-frontend** | Confirm latest commit deployed | Production deployment **Ready** |
| PF-04 | Supabase SQL editor (service role) | `SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 10;` (or your migrate tracker) | Versions **0021** through **0028** present: `0021_synthetic_isolation`, `0023_dedup_key_review_queue`, `0024_factor_poll_log`, `0025_watchlist_items`, `0026_pipeline_runs_held_status`, `0027_confidence_audit`, `0028_card_regen_history` |
| PF-05 | Render shell / local with prod `SUPABASE_DB_URL` | `python backend/scripts/seed_synthetic_events.py` (once per environment) | Log: 20 upserted; **second run** inserts 0 new rows |
| PF-06 | Render + Vercel env | `ADMIN_EMAILS` identical on both (comma-separated PO emails) | Watchlist + admin-gated APIs work for your login |
| PF-07 | Render env | `SUPABASE_DB_URL`, `NEWSAPI_KEY`, `GEMINI_API_KEY` set | Cron ingest and card draft not `skipped_no_config` |

### 0.2 Production URLs (reference)

| Surface | URL |
|---------|-----|
| Frontend (Vercel) | `https://investment-assistant-frontend.vercel.app` |
| API (Render direct) | `https://investment-assistant-3eqc.onrender.com` |
| Browser API proxy | `https://investment-assistant-frontend.vercel.app/backend/...` |

Use the **browser proxy** for UI-driven tests (same-origin cookies/CORS). Use **Render direct** for operator curl when debugging upstream vs proxy.

### 0.3 Test accounts

| Persona | Requirement |
|---------|-------------|
| **Editor / PO** | Email in `ADMIN_EMAILS`; signed into Supabase auth on Vercel |
| **Regular user** | Any authenticated tester **not** on admin allow-list (optional, for 403 checks) |
| **SQL operator** | Supabase dashboard with service role (synthetic row verification only — never expose to users) |

---

## 1. Master decision trees

Use these when a scenario has **multiple valid outcomes**. Link scenario IDs to the branch you observed.

### 1.1 Synthetic data visibility (P3-S0, P3-T1)

```
Query events (service role SQL)
├── is_synthetic = TRUE  → 20 rows expected after seed
└── User-facing API (Pulse / Thread / Mirror)
    ├── Returns only is_synthetic = FALSE cards/events
    │   └── PASS (isolation)
    └── Synthetic title/url appears in JSON
        └── FAIL — SyntheticFilterMixin or RLS regression
```

**Meaning:** Synthetic rows exist for calibration but must **never** affect user trust metrics.

### 1.2 Event ingest dedup (P3-S1c)

```
Same story from 2+ outlets within 4h window, same category + entity + headline_hash
├── Single events row, source_count incremented, sources[] appended
│   └── PASS — merge path
├── Two rows with same headline, different category
│   └── PASS — no auto-merge; dedup_review_queue row may exist
└── Two rows, same entity, different headlines
    └── PASS — distinct dedup_key; no false merge
```

### 1.3 NewsAPI poll outcome (P3-S1d)

```
One event-detection cron tick
├── factor_poll_log row inserted
│   ├── status = ok, article_count > 0  → NewsAPI returned articles
│   ├── status = empty, article_count = 0  → 200 but no matches (not an error)
│   └── status = error  → 429/5xx; check Render logs for RSS fallback
├── No row + log "global_budget_exhausted"
│   └── Expected after 100 UTC calls/day — wait next UTC day or verify cap math
└── No row + no GET to newsapi.org
    └── FAIL — budget RPC or cron misconfig (see P3-S1d post-impl B7)
```

### 1.4 Market facts freshness (P3-S1f)

```
GET /api/market-facts
├── All critical facts fresh or stale
│   ├── Card draft-from-event → 200 / proceeds
│   └── Chips show green (fresh) or amber (stale) dots
└── Any critical fact unavailable
    ├── Card draft-from-event → 423 critical_facts_held
    ├── /admin/queue banner warns unavailable critical facts
    └── PASS — gate working (do not bypass in prod)
```

### 1.5 Confidence tier routing (P3-S1g, P3-S1h)

```
Event confidence_effective (0–1)
├── ≥ 0.75  → tier HIGH (direct editorial path / high signal gate)
├── 0.55–0.74  → tier MEDIUM (narrow band — PO G-02)
└── < 0.55  → tier LOW

FoW dampener (≥3 active is_major events)
├── confidence_effective ≈ confidence_raw × 0.6
└── Thread aside "Why this confidence tier?" shows FoW callout
    └── If no callout but 3+ majors active → investigate before P3-S1l
```

### 1.6 Publish gate stack (P3-S1i, P3-S1j, P3-S1k, P3-T4)

```
Editor clicks Publish on /admin/review/[draftId]
├── number_validation ≠ PASS
│   └── 422 number_validator_failed — button disabled; sentence diff shown
├── editorial_checklist automated item FAIL
│   └── 422 editorial_checklist_failed
├── plain_english_confirmed = false
│   └── 422 publish_rejected
└── All pass
    └── 200 — card published; appears on Pulse

After section regen
├── Post-regen number_validation FAIL
│   └── Publish still blocked (P3-T4 contract)
└── Post-regen PASS + checklist PASS + manual tick
    └── Publish allowed
```

---

## 2. Story-by-story test scenarios

### P3-S0 — Synthetic historical seed + triple-layer isolation

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S0-01** | Supabase SQL (service role) | Calibration data exists | Run: `SELECT COUNT(*) FROM events WHERE is_synthetic = TRUE;` | Count = **20** | If 0, re-run seed script (PF-05) |
| **P3-S0-02** | Supabase SQL | Major-event FoW prep | `SELECT COUNT(*) FROM events WHERE is_synthetic = TRUE AND is_major = TRUE;` | Count = **7** | — |
| **P3-S0-03** | Supabase SQL | Idempotent seed | Re-run `seed_synthetic_events.py`; repeat count query | Still **20** rows; no duplicates on `external_id` | — |
| **P3-S0-04** | Browser → `/pulse` | User feed must exclude synthetic | 1. Open `https://investment-assistant-frontend.vercel.app/pulse` 2. Sign in if prompted 3. Scroll full feed 4. Open DevTools → Network → filter `feed` 5. Inspect JSON response bodies | No `canonical_url` containing `synthetic://seed/`; no Jan–Jun 2025 synthetic fixture titles | Compare against `backend/scripts/seed_data/synthetic_events.json` offline |
| **P3-S0-05** | Browser → `/mirror` | Mirror predictions isolation | 1. Navigate to `/mirror` 2. Load prediction list 3. Inspect network response for `/api/mirror/...` | Zero rows tied to synthetic events | Phase 2 Mirror must still load |
| **P3-S0-06** | curl (Render direct) | API layer filter | `curl -s "https://investment-assistant-3eqc.onrender.com/api/feed?limit=50" \| jq '.items[].event_id'` then spot-check titles via card detail | No synthetic event titles | Service role DB can still `SELECT` synthetic — that is correct |

---

### P3-T1 — Synthetic isolation verification gate (production spot-check)

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-T1-01** | Manual repeat of P3-S0-04, P3-S0-05 | CI gate manual confirmation | Execute S0-04 and S0-05; document screenshots | PASS on both | This is the **P3-S8 go/no-go** "synthetic isolation spot-check in production" item |
| **P3-T1-02** | `/thread/[publishedCardId]` | Thread detail path | Open any **published** card from Pulse → inspect aside | Card loads; confidence composition renders; no 500 | Phase 2 Thread perf baseline |

---

### P3-S1c — Event de-duplication pipeline

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1c-01** | Supabase SQL | Schema | `SELECT column_name FROM information_schema.columns WHERE table_name='events' AND column_name IN ('dedup_key','source_count','sources','force_editorial_review');` | All columns present | — |
| **P3-S1c-02** | Render → Logs → event_detection cron | Live merge behaviour | 1. Note UTC time before next 4h cron 2. After cron, query: `SELECT id, title, source_count, dedup_key, force_editorial_review FROM events WHERE created_at > NOW() - INTERVAL '6 hours' ORDER BY source_count DESC LIMIT 10;` | Recent real ingests show `source_count ≥ 1`; high-volume stories show `source_count > 1` after multi-outlet coverage | Empty cron → check `SUPABASE_DB_URL` |
| **P3-S1c-03** | Supabase SQL | Cross-category queue | `SELECT COUNT(*), status FROM dedup_review_queue GROUP BY status;` | Table exists; pending rows acceptable | Zero rows is OK if no collisions yet |
| **P3-S1c-04** | Supabase SQL | Editorial escalation flag | `SELECT id, title, source_count, force_editorial_review FROM events WHERE force_editorial_review = TRUE LIMIT 5;` | Any row with `source_count > 5` has flag **true** | — |
| **P3-S1c-05** | `/admin/queue` | Editorial sees merged rows | 1. Open `/admin/queue` 2. Sort by confidence 3. Click row with highest `source_count` (if any) | Single queue row (not duplicate titles for same story) | Phase 1 queue sort/filter still works |

---

### P3-S1d — NewsAPI factor keyword scheduler

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1d-01** | Supabase SQL | Poll audit trail | `SELECT factor_id, status, article_count, polled_at FROM factor_poll_log ORDER BY polled_at DESC LIMIT 8;` | Rows exist after at least one cron since deploy; `status` ∈ {`ok`,`empty`,`error`} | No rows → see decision tree §1.3 |
| **P3-S1d-02** | Render logs | Round-robin | Search logs for `newsapi.poll_status` across **two consecutive** cron runs | `factor_id` (or slug) **changes** between runs | Same factor twice → rotation bug |
| **P3-S1d-03** | Supabase SQL | Daily cap | `SELECT COUNT(*) FROM factor_poll_log WHERE polled_at::date = CURRENT_DATE AT TIME ZONE 'UTC';` | Count ≤ **100** | — |
| **P3-S1d-04** | Render logs (optional) | RSS fallback on 429 | If `status=error` rows exist, grep log for `rss_fallback` or ET Markets/Mint adapter | 429 path attempted RSS without extra NewsAPI GET | — |
| **P3-S1d-05** | Local/script or manual | Digest template | Run editorial digest preview if you have a script; else skip and mark BLOCKED | HTML includes NewsAPI poll summary table | Full send not required — template exists per S1d |

---

### P3-S1e — Slow-burn watchlist

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1e-01** | Browser → `/editor/watchlist` | Long-lead risk tracking | 1. Sign in with **ADMIN_EMAILS** account 2. Navigate to `https://investment-assistant-frontend.vercel.app/editor/watchlist` | Table loads with **5 seed rows** (monsoon, budget, etc.) | Non-admin → forbidden page |
| **P3-S1e-02** | `/editor/watchlist` | Status update | 1. Pick row **"Monsoon progression"** (or any `watching` row) 2. Open status dropdown 3. Select **closed** 4. Wait for PATCH to complete (network 200) 5. Refresh page | Status persists **closed**; `last_reviewed_at` updated (visible or via API) | — |
| **P3-S1e-03** | `/editor/watchlist` | Escalate to editorial pipeline | 1. Pick a **watching** row (re-open closed seed in SQL if needed) 2. Click **Escalate** 3. Confirm dialog if shown 4. Note escalated state | Row status → **escalated**; button disabled or shows escalated | Second escalate → 409 `already_escalated` |
| **P3-S1e-04** | `/admin/queue` | Escalated event visible | 1. Open `/admin/queue` 2. Filter or scan for `event_source = watchlist` (column or title match) | New **draft** event with title from watchlist item | — |
| **P3-S1e-05** | curl + admin JWT | API auth | `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer <non-admin-token>" https://investment-assistant-3eqc.onrender.com/api/editor/watchlist` | **403** | Admin token → **200** |

---

### P3-S1f — Market facts freshness + fallback chain

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1f-01** | Browser → `/pulse` | User-facing freshness | 1. Open `/pulse` 2. Locate market facts strip (macro chips above/beside feed) 3. Hover or inspect each chip | Coloured dot per chip: **green** = fresh, **amber** = stale | Phase 2 Pulse layout not broken |
| **P3-S1f-02** | Browser → `/thread/[cardId]` | Thread chips | Open published card → same strip in thread header/aside | Dots match `/api/market-facts` freshness | — |
| **P3-S1f-03** | curl | API contract | `curl -s "https://investment-assistant-3eqc.onrender.com/api/market-facts" \| jq '.facts[] \| {id, freshness_status, value}'` | Each critical fact has `freshness_status` ∈ {`fresh`,`stale`,`unavailable`} | — |
| **P3-S1f-04** | `/admin/queue` | Editorial degraded banner | Open `/admin/queue` | If any critical fact stale/unavailable, **MarketFactsBanner** visible with explanation | All fresh → banner absent or informational only |
| **P3-S1f-05** | curl (operator) | Critical-fact hold | 1. Pick `event_id` from `/admin/queue` 2. `curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/cards/draft-from-event" -H "Content-Type: application/json" -d '{"event_id":"<uuid>"}'` | **200** if facts available; **423** with `critical_facts_held` if unavailable (document which branch you hit) | Do not force-unavailable in prod unless you accept failed draft |

---

### P3-T2 — Data pipeline integration gate (production smoke)

CI runs `test_data_pipeline_integration.py`. In production, run this **short cross-check** instead of re-implementing the fixture.

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-T2-01** | Combined | Dedup + queue | Verify **P3-S1c-02** shows merge semantics | `source_count` can exceed 1 | — |
| **P3-T2-02** | Combined | NewsAPI + dedup | Verify **P3-S1d-01** + new events in queue after cron | Ingest pipeline alive | — |
| **P3-T2-03** | Combined | Watchlist → queue | Complete **P3-S1e-03** + **P3-S1e-04** | Escalated event in queue | — |
| **P3-T2-04** | Combined | Facts hold | **P3-S1f-05** branch documented | Either draft proceeds or 423 hold — both valid if explained | — |

---

### P3-S1g — Rule-based confidence scorer + gate swap

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1g-01** | Supabase SQL | Stored scores | `SELECT id, title, confidence_raw, confidence_effective, factor_db_match_count, is_major FROM events WHERE is_synthetic = FALSE ORDER BY created_at DESC LIMIT 5;` | `confidence_raw` and `confidence_effective` populated (0–1 range) | — |
| **P3-S1g-02** | Supabase SQL | Audit trail | `SELECT event_id, scorer_version, created_at FROM confidence_score_audit ORDER BY created_at DESC LIMIT 5;` | Rows exist for recent upserts | Empty → migration 0027 not applied |
| **P3-S1g-03** | curl | Breakdown API | `curl -s "https://investment-assistant-3eqc.onrender.com/api/events/<event_uuid>/confidence-breakdown" \| jq '{tier, confidence_raw, confidence_effective, inputs: .inputs \| keys}'` | JSON with **5 input keys**, tier label, sources array | 404 → bad uuid |
| **P3-S1g-04** | `/admin/signal-queue` | Signal routing uses float tiers | 1. Open `/admin/signal-queue` 2. Inspect medium-confidence hits (if any) | Queue populated; no obvious Phase 1 "source count only" labelling regression | Empty queue OK outside market hours |

---

### P3-S1h — Confidence explainability UI

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1h-01** | `/thread/[cardId]` | Lazy-load perf | 1. Open published card with known `event_id` 2. Open DevTools → Network 3. **Before** expanding panel, confirm **no** request to `confidence-breakdown` 4. In aside, click **"Why this confidence tier?"** (or collapsible trigger) 5. Watch network | Single fetch to `/backend/api/events/.../confidence-breakdown` **after** expand only | No layout shift on initial paint |
| **P3-S1h-02** | Thread aside (expanded) | Five inputs + tier | After expand: verify **five** progress bars (source count, source quality, factor match, recency, unique publishers), tier badge (HIGH/MEDIUM/LOW), raw vs effective % | Matches breakdown API when curl same `event_id` | — |
| **P3-S1h-03** | Thread aside | FoW callout | If `confidence_effective` ≪ `confidence_raw` on API, UI shows Fog of War dampener callout | Callout visible when API `fog_active` true | Hidden when equal |
| **P3-S1h-04** | Thread aside | Editorial badge | Find event with `force_editorial_review=true` (SQL or high `source_count`) | Amber **Editorial review** badge in panel | — |
| **P3-S1h-05** | `/lens` → result card | Lens surface | 1. Run a Lens query that returns a card 2. Expand confidence panel same as Thread | Same behaviour as Thread | ICE Measured/Modelled/Judged bar **still present** above panel |

---

### P3-T3 — Confidence scoring verification gate (production spot-check)

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-T3-01** | API + UI | Scores agree | Compare **P3-S1g-03** JSON `confidence_raw` to UI displayed raw % (×100) | Within rounding (±1%) | — |
| **P3-T3-02** | API | Weighted sum | From breakdown JSON, manually verify `sum(input.value × input.weight) ≈ confidence_raw` | Within ε 0.02 | Document arithmetic in evidence |
| **P3-T3-03** | `/thread/[cardId]` | RTL-equivalent manual | Expand panel → all five inputs render with labels | PASS | 404 event → red error alert; ICE bar still visible |

---

### P3-S1i — Number validator hard publish gate

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1i-01** | `/admin/review/[draftId]` | Load-time gate | 1. Open draft card in review workspace 2. Scroll to **Publish** section (`PublishGate`) 3. If validator FAIL: note **Publish** button state | Button **disabled** when `number_validation.status !== PASS` | — |
| **P3-S1i-02** | Review workspace | Sentence-level diff | On FAIL card: inspect ungrounded list | Shows **sentence text** + offending number token | — |
| **P3-S1i-03** | curl | Hard 422 | `curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/admin/cards/<draft_id>/publish" -H "Content-Type: application/json" -d '{"plain_english_confirmed":true}'` on FAIL draft | **422** body includes `number_validator_failed` and `ungrounded[]` | No override endpoint exists |
| **P3-S1i-04** | Review workspace | Comparative soft flags | Find prose with "doubled" or "record high" (if any) | Soft warning shown; **does not** alone block publish | — |

**Creating a FAIL draft for testing:** Use an existing draft or run `draft-from-event` then manually edit Insight in DB **only in staging** — in production prefer a card you already know fails validator.

---

### P3-S1j — Editorial checklist (4 automated + 1 manual)

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1j-01** | `/admin/review/[draftId]` | Automated items | On card load, locate **ChecklistPanel** | Four items show **PASS/FAIL** badges (numbers, dissent, evidence freshness, SEBI); fifth **Plain English** is manual checkbox only | No manual ticks for auto items |
| **P3-S1j-02** | Checklist | Dissent gate | Open draft with `dissenting_view` ≤ 100 chars (or truncate in staging) | Dissent item **FAIL** | — |
| **P3-S1j-03** | Checklist | SEBI allowlist | Card containing phrase **"repo rate hold"** in macro context | SEBI scan **PASS** | — |
| **P3-S1j-04** | Checklist | SEBI block | Card containing **"buy HDFC Bank"** recommendation language | SEBI **FAIL** with violation detail | — |
| **P3-S1j-05** | Publish flow | Manual tick required | 1. Fix all automated FAILs 2. Leave Plain English **unchecked** 3. Click Publish | Button disabled; API 422 if forced | — |
| **P3-S1j-06** | Publish flow | Full pass | 1. All automated PASS 2. Check **Plain English** 3. Click **Publish** | **200**; redirect or success toast; card appears on Pulse | `track_record` row created (SQL optional) |

---

### P3-S1k — Targeted section regen

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1k-01** | `/admin/review/[draftId]` | Section regen UI | 1. Open draft 2. Locate **RegenSection** in aside 3. Select section **Insight** from dropdown 4. Click note field; type: `Shorten opening paragraph; remove unsourced percentage.` 5. Click **Regenerate section** (or equivalent submit) 6. Wait for loading spinner to finish | Insight updates; Context/Evidence/Dissent/Framework text **unchanged** (hash/compare visually) | Empty note → 422 |
| **P3-S1k-02** | Review workspace | Post-regen validation | After regen completes | `number_validation` and checklist **refresh**; PASS/FAIL badges update | — |
| **P3-S1k-03** | Supabase SQL | Audit trail | `SELECT regen_history, full_regen_count FROM cards WHERE id = '<draft_id>';` | `regen_history` JSON array appended with section, timestamp, note | Migration 0028 required |
| **P3-S1k-04** | RegenSection | Full regen guard | 1. Click **Full regen** (same card) 2. Confirm dialog if `full_regen_count >= 1` | First full regen: succeeds; counter increments | Third without PO flag → 423 blocked |
| **P3-S1k-05** | Review workspace | Legacy send-back | Click **Regenerate draft (new card)** (Phase 1) | Creates **new** draft id; old archived — distinct from in-place section regen | — |

---

### P3-T4 — Editorial integrity verification gate (golden path E2E)

This is the **most important manual regression** for Phase 3 editorial trust. Execute as one continuous session.

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-T4-01** | End-to-end | Ungrounded block | 1. Open draft known to fail number validator **OR** regen Insight with note asking for a specific unsourced `%` (if LLM complies) 2. Confirm Publish disabled 3. `curl -X POST .../publish` | **422** `number_validator_failed` | Matches CI `test_ungrounded_number_blocks_publish_with_422` |
| **P3-T4-02** | End-to-end | Happy path publish | 1. Start from FAIL draft 2. Switch to **Evidence** tab 3. Add/fix evidence so numbers in Insight appear in Evidence (or **Regenerate section → Evidence** to rebuild Factor DB layer) 4. Wait for validator **PASS** 5. Confirm checklist auto items **PASS** 6. Check **Plain English** 7. Click **Publish** 8. Open `/pulse` | Publish **200**; card visible on Pulse; Thread loads | Matches CI happy path test |
| **P3-T4-03** | End-to-end | Regen bypass impossible | 1. From passing draft, regen **Insight** with note that invites a new unsourced number 2. If validator FAIL after regen, attempt Publish | Still **blocked** | Matches CI `test_section_regen_cannot_bypass_validator` |

---

## 3. Cross-cutting regression suite (Phase 1 / 2)

Run after Phase 3 scenarios to ensure nothing regressed.

| ID | Where | Steps | Expected |
|----|-------|-------|----------|
| **REG-01** | `/pulse` | Load feed; click first card | Feed p95 acceptable; Thread opens |
| **REG-02** | `/thread/[id]` | Switch ICE tabs Insight → Context → Evidence → Dissent → Framework | All tabs render; Evidence matrix loads |
| **REG-03** | `/mirror` | Log prediction on published card (if enrolled) | Prediction saves; no synthetic leakage |
| **REG-04** | `/lens` | Submit query; open result | Lazy confidence panel optional; no 500 |
| **REG-05** | `/map` + one sector slug | Open Map index and one deep-dive | 200; Lighthouse not re-run here but page loads |
| **REG-06** | `/admin/queue` | Filter by category; open event row | Queue works without auth (known Phase 1 caveat — document exposure) |
| **REG-07** | Notifications | Publish card (P3-T4-02) | In-app notification for subscribers (if configured) |
| **REG-08** | Signal monitor | During NSE hours, wait 30 min or inspect `confidence_gate_log` | Monitor job runs; uses float tier not source-count heuristic |

---

## 4. Recommended test execution order

Execute in this order to minimize setup duplication:

1. **Pre-flight** (§0)  
2. **P3-S0 / P3-T1** — isolation first (trust foundation)  
3. **P3-S1f** — market facts (blocks draft if broken)  
4. **P3-S1d / P3-S1c** — ingest pipeline (SQL + logs)  
5. **P3-S1e** — watchlist escalate  
6. **P3-T2 smoke** — combined pipeline  
7. **P3-S1g / P3-S1h / P3-T3** — confidence API + UI  
8. **P3-S1i → P3-S1j → P3-S1k → P3-T4** — full editorial golden path (allow 30–60 min; LLM regen consumes budget)  
9. **Regression** (§3)

---

## 5. Evidence capture template

Copy into your test log (Notion, sheet, or `docs/plans/phase3-go-no-go.md` evidence links).

| Scenario ID | Date (UTC) | Tester | Result | Evidence link / notes |
|-------------|------------|--------|--------|------------------------|
| P3-S0-04 | | | PASS/FAIL | |
| P3-T4-02 | | | PASS/FAIL | |
| … | | | | |

**Minimum bar for "Phase 3 pause go":**

- All **P3-T*** spot-checks PASS (T1, T2 smoke, T3, T4 golden path)  
- Zero synthetic leakage in Pulse/Mirror (S0/T1)  
- Publish golden path (T4-02) PASS on production  
- Regression REG-01–REG-06 PASS  

---

## 6. Known production caveats (do not fail wrong branch)

| Topic | Behaviour |
|-------|-----------|
| `/admin/queue` auth | Phase 1 routes may lack RBAC — network perimeter expected until hardened |
| Sunday digest | Template exists; **no Render cron** yet — digest send is manual |
| Draft from event | No UI button on queue — use `POST /api/cards/draft-from-event` |
| FoW banner | Full named banner is **P3-S1l** — dampener + aside callout may work without feed banner |
| LLM caps | Section/full regen counts against daily Gemini budget — sequence tests to avoid 429 |
| API proxy latency | Feed p95 may exceed 800 ms (Phase 2.5 PO waiver) — not a Phase 3 functional fail |

---

## 7. Appendix — operator curl cheatsheet

Replace placeholders before running.

```bash
# Market facts
curl -s "https://investment-assistant-3eqc.onrender.com/api/market-facts" | jq .

# Confidence breakdown
curl -s "https://investment-assistant-3eqc.onrender.com/api/events/<EVENT_UUID>/confidence-breakdown" | jq .

# Draft from event (editorial)
curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/cards/draft-from-event" \
  -H "Content-Type: application/json" \
  -d '{"event_id":"<EVENT_UUID>","editor_notes":null}' | jq .

# Admin publish (requires passing validator + checklist)
curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/admin/cards/<CARD_UUID>/publish" \
  -H "Content-Type: application/json" \
  -d '{"plain_english_confirmed":true}' | jq .

# Section regen
curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/admin/cards/<CARD_UUID>/regenerate-section" \
  -H "Content-Type: application/json" \
  -d '{"section":"insight","editor_note":"Tighten lede; ground all numbers."}' | jq .
```

---

## 8. Related documentation

| Document | Purpose |
|----------|---------|
| `docs/plans/finnwise-phase3-implementation-tasks.md` | Story acceptance criteria |
| `docs/plans/phase3-go-no-go.md` | Launch checklist — fill evidence after this run |
| `docs/intelligence-pipeline-overview.md` | Pipeline mental model |
| `docs/Post Implementation documentation/Phase3_*.md` | Per-story implementation detail |
| `docs/plans/phase3-calibration.md` | Day 30/60 scorer recalibration (after soak) |

---

*After completing this pass, update `docs/plans/phase3-go-no-go.md` T1–T4 evidence with links to your captured results, then proceed to P3-S1l only when editorial golden path is green.*
