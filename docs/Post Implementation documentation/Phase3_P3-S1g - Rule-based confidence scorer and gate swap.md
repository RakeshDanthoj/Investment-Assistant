# Post Implementation Detailed Document — P3-S1g

**Version:** v1.0 | **Date:** 31-05-2026  
**Story ID:** P3-S1g (Phase 3, Story 1g)  
**PRD2 gaps:** G-01 (Option B + `unique_publisher_count`), G-02 (narrow MEDIUM band)  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **8.0**–**8.6**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §3, §6 · `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` WS-2

---

## Narrative style (read this first)

Before P3-S1g, editorial and signal routing leaned on **how many corroborating sources** matched a signal (direct vs partial counts). That was hard to audit and did not use post-dedup event richness or Factor DB overlap. This story replaces that with a **rule-based confidence score from 0.0 to 1.0**: five weighted inputs, stored `confidence_raw` and `confidence_effective`, an append-only **audit trail**, and tier routing (**HIGH** ≥ 0.75 · **MEDIUM** 0.55–0.74 · **LOW** &lt; 0.55).

Every event upsert through dedup now **recomputes** confidence and writes a `confidence_score_audit` row. The **signal monitor** still requires a signal to match market facts, but **which gate** (high / medium / low) is decided from the parent event’s `confidence_effective`, not source counts. **Fog of War** applies a **0.6 dampener** only to the effective score when three or more active `is_major` events exist. **`is_major`** is set automatically when raw ≥ 0.75, at least two macro factors match, and the category is in the qualifying set (unless `is_major_override` is set).

An explainability API is ready for **P3-S1h** (`GET /api/events/{id}/confidence-breakdown`); no frontend shipped in this story.

**Tests executed and passed (P3-S1g–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Scorer + calibration + FoW dampener | `python -m pytest backend/tests/test_confidence_scorer.py -q` | **7 passed** |
| Gate tiers (narrow MEDIUM) | `python -m pytest backend/tests/test_confidence_gate.py -q` | **4 passed** |
| Audit migration SQL contract | `python -m pytest backend/tests/test_confidence_audit_migration_sql.py -q` | **1 passed** |
| Breakdown API | `python -m pytest backend/tests/test_confidence_breakdown_api.py -q` | **2 passed** |
| Dedup + interim raw helper | `python -m pytest backend/tests/test_event_dedup.py -q` | **Pass** (regression) |
| Signal monitor + new gate | `python -m pytest backend/tests/test_signal_monitor_logs_override_decisions.py -q` | **3 passed** |
| Data pipeline integration | `python -m pytest backend/tests/test_data_pipeline_integration.py -q` | **Pass** (regression) |
| **Full backend CI** | `python -m ruff check backend` + `python -m pytest -q backend/tests` | **292 passed**, ruff clean |

**Three anchors for handover:** (1) **Apply migration `0027_confidence_audit.sql`** on every environment before expecting audit rows or `factor_db_match_count`. (2) **Do not restore source-count routing in `confidence_gate.route()`** — P3-S1h and FoW (P3-S1l) depend on float tiers and stored raw/effective columns. (3) **`confidence_raw` is never mutated by FoW** — only `confidence_effective` is dampened; full FoW banner work remains P3-S1l.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S1g |
| **Title** | Rule-based confidence scorer + gate swap |
| **Category** | **Backend** (API endpoint for explainability; UI in **P3-S1h**) |
| **Points / owner (plan)** | 8 · Jordan |
| **Depends on** | P3-T2 (data pipeline integration test gate) |
| **Parallel with** | _None_ |
| **Blocks** | P3-S1h (explainability UI), P3-T3 (confidence test gate) |

**What this story aimed to achieve (plain language)**

Give every editorial routing decision a **debuggable numeric basis**: a weighted score from post-dedup sources, source quality, Factor DB keyword match, recency, and unique publisher domains. Store both undampened and dampened scores, log inputs for reproducibility, and route HIGH / MEDIUM / LOW from **effective** score thresholds agreed with the PO (narrow MEDIUM band).

**How it fits into the overall application**

- **Upstream:** P3-S0 (columns `confidence_raw`, `confidence_effective`, `is_major`), P3-S1c (dedup merges `source_count` / `sources[]`), P3-T2 (pipeline gate proved clean event rows).
- **This story:** Replaces interim `recompute_confidence_raw()` SQL blend with the full scorer; swaps `confidence_gate` from corroboration counts to float tiers; exposes breakdown JSON for Thread UI.
- **Downstream:** **P3-S1h** wires `ConfidenceComposition` to the breakdown API; **P3-S1l** uses `is_major` + `card_confidence_history` for FoW banner; **P3-S2** interaction model needs 30-day soak on synthetic/historical scores.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **8.1** | `confidence_config.py` — PO weights, thresholds, `FOG_DAMPENER`, `calibration_status: provisional`, source quality maps. |
| **8.2** | `confidence_scorer.py` + `event_factor_match.py` — weighted sum, unique publishers (domain-level), factor match strength, `is_major` computation. |
| **8.3** | Migration `0027_confidence_audit.sql` — audit table + `events.factor_db_match_count`; audit write on every upsert. |
| **8.4** | `confidence_gate.route(confidence_effective)`; wired in `event_dedup`, `signal_monitor_runner`, `card_pipeline`. |
| **8.5** | `GET /api/events/{event_id}/confidence-breakdown` — inputs, sources, tier, FoW flag; 60s cache. |
| **8.6** | Tests: narrow MEDIUM boundaries; ≥80% tier match on 20 synthetic calibration fixtures. |

**Functional breakdown**

1. **Build inputs:** From event title, category, `event_source`, `canonical_url`, post-dedup `source_count`, `sources` JSON, and `created_at` (first seen).
2. **Factor match:** Keyword scan across 8 macro factor slugs; category defaults when no keyword hit; strength 1.0 (2+ keyword hits) / 0.7 (1) / 0.4 (category-only) / 0.0.
3. **Weighted raw:**  
   `raw = Σ(component × weight)` with weights 30% / 30% / 25% / 5% / 10% (source_count, quality, factor_db_match, recency, unique_publisher).
4. **FoW dampener:** If `COUNT(is_major AND lifecycle IN active/signal_triggered) >= 3`, `effective = raw × 0.6`; else `effective = raw`.
5. **Persist:** Update `events.confidence_raw`, `confidence_effective`, `factor_db_match_count`, `is_major` (respecting `is_major_override`), `force_editorial_review` when `source_count > 5`.
6. **Audit:** Insert into `confidence_score_audit` with full `inputs_json` and `scorer_version`.
7. **Gate:** `route(effective)` → high / medium / low for signal monitor paths after signal evaluation is non-`none`.

**Scoring components (PO weights — G-01 / G-02)**

| Input | Weight | Normalisation |
|-------|--------|----------------|
| `source_count` | 30% | `min(source_count / 3, 1.0)` post-dedup |
| `source_quality` | 30% | Adapter + domain map (RBI/NSE 1.0, wires 0.8, press 0.65, NewsAPI 0.5 default) |
| `factor_db_match` | 25% | Match strength 0.0–1.0 from keyword/category rules |
| `recency` | 5% | ≤4h → 1.0; ≤12h → 0.7; ≤24h → 0.4; else 0.1 |
| `unique_publisher` | 10% | `min(unique_domains / 3, 1.0)` from `sources[]` URLs |

**Routing thresholds (effective score)**

| Tier | Threshold | System action (via signal monitor / future card routing) |
|------|-----------|----------------------------------------------------------|
| **HIGH** | ≥ 0.75 | Auto-update path, override window (existing P1-S11 behaviour) |
| **MEDIUM** | 0.55–0.74 | Editorial signal queue |
| **LOW** | &lt; 0.55 | Digest log |

**`is_major` rules (auto unless overridden)**

All must be true:

1. `confidence_raw >= 0.75`
2. `factor_db_match_count >= 2`
3. `category IN {rbi_policy, geopolitical, budget, macro}`

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Dedup merge increases `source_count` | Scorer re-run in same transaction; audit row appended |
| `is_major_override` set on event | Scorer still updates raw/effective; `is_major` column keeps override value |
| No DB URL configured | `apply_confidence_to_event` logs warning, returns `None`; dedup still inserts with interim `confidence_raw` on INSERT only |
| Event missing for breakdown API | HTTP **404** `event_not_found` |
| Signal matches facts but effective &lt; 0.55 | **Low** gate (score-driven), not source-count low |
| Signal matches facts but effective ≥ 0.75 | **High** gate even with only one direct fact |
| FoW active (≥3 major events) | New events get lower **effective** tier; **raw** unchanged |
| `source_count > 5` | `force_editorial_review = true` on event row |

**Business rules enforced**

- **G-01 Option B:** Rule-based scorer (not LLM); `unique_publisher_count` at 10% weight (post-dedup domains).
- **G-02:** Narrow MEDIUM band 0.55–0.74 inclusive at lower bound; HIGH at ≥ 0.75.
- **PRD2 non-negotiable:** FoW dampener applies to **effective** only; raw stored for calibration and `is_major`.
- **Reproducibility:** Every scorer run → `confidence_score_audit` with `scorer_version = confidence_scorer.v1`.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Keyword-based factor match** (not live Factor DB SQL per event) | Fast, no extra DB round-trip on hot dedup path; aligns with PRD2 “match strength” tiers | Per-event sensitivity matrix lookup: heavy for ingest volume |
| **Gate uses `confidence_effective` only** | PO G-02 routing is tier-on-score; signal check still decides *if* signal fired | Combined score + corroboration matrix: reintroduces opaque dual logic |
| **Signal monitor unchanged for “did it fire?”** | P1-S11 `evaluate()` / Jaccard on `MarketFact` still valid | Drop fact check and use score only: would fire without corroboration |
| **Audit append-only table** | G-01 reproducibility; no update-in-place on events for history | Only store latest on `events` row: loses calibration trail |
| **Config in Python module** | Matches PRD2 `confidence_config.py` name; tunable constants with deploy | YAML for weights: plan specified `.py` for thresholds |
| **Breakdown API recomputes live** | Always consistent with current config; cache 60s per perf standard | Serve only last audit row: stale if config changes mid-cache |
| **`recompute_confidence_raw()` kept** | Dedup INSERT placeholder + unit test monotonicity; superseded after `apply_confidence_to_event_row` in transaction | Remove helper: breaks `test_event_dedup` contract |

⚠️ **Do not revert `confidence_gate.route()` to `SignalEvalResult` source counts** — tests, signal monitor, and P3-S1h copy assume float tiers.

⚠️ **Do not apply FoW dampener to `confidence_raw`** — P3-S1l FoW banner and `card_confidence_history` depend on raw vs effective split.

⚠️ **Respect `is_major_override`** when updating events — editorial PO override must not be clobbered on rescoring.

**Assumptions**

- Factor keyword lists in `event_factor_match.py` are **provisional** until Day-30 calibration review (`calibration_status: provisional`).
- Synthetic seed `confidence_raw` values in JSON remain hand-grade references; live scorer may differ slightly but tier match target is ≥80% on calibration fixtures.
- FoW “active major” count uses `lifecycle_state IN ('active', 'signal_triggered')` and `COALESCE(is_major_override, is_major)` — full feed FoW banner rewrite is **P3-S1l**, not this story.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S0** schema (`confidence_raw`, `confidence_effective`, `is_major`); **P3-S1c** dedup (`source_count`, `sources[]`); **P3-T2** integration gate green |
| **Parallel** | None |
| **Downstream** | **P3-S1h** explainability UI; **P3-T3** confidence test gate; **P3-S1l** FoW `is_major` banner; **P3-S2** interaction model (30-day soak) |

**Shared components touched**

| Component | Role |
|-----------|------|
| `event_dedup.py` | Post-upsert scorer + audit |
| `confidence_gate.py` | Tier routing |
| `signal_monitor_runner.py` | Joins `events.confidence_effective` for gate |
| `card_pipeline.py` | `apply_confidence_to_event()` before LLM draft |
| `events` table | Stores raw, effective, `factor_db_match_count`, `is_major` |
| `confidence_gate_log` | Unchanged schema; `reason` now `score_gte_075` etc. |

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Pure functions** for scoring (`build_scorer_input`, `compute_confidence`, `tier_from_score`) — easy to test without DB.
- **Row-level apply** (`apply_confidence_to_event_row`) for transactional dedup; **standalone** `apply_confidence_to_event` for pipeline refresh.
- **Thin API router** (`events.py`) delegating to `build_confidence_breakdown_payload`.
- **Separation:** `event_factor_match.py` (keywords) vs `confidence_scorer.py` (weights + persistence).

**Database schema**

| Object | Change |
|--------|--------|
| `events.factor_db_match_count` | `smallint NOT NULL DEFAULT 0` |
| `confidence_score_audit` | New append-only table (see B1) |

**API contracts**

| Method | Route | Auth | Cache |
|--------|-------|------|-------|
| GET | `/api/events/{event_id}/confidence-breakdown` | None (same as feed read pattern today) | `private, max-age=60, stale-while-revalidate=300` |

**UI/UX**

- **None in P3-S1g** — breakdown API only. P3-S1h adds Thread `ConfidenceComposition`.

**Libraries / tools**

| Library | Purpose |
|---------|---------|
| stdlib `urllib.parse` | Publisher domain extraction |
| Existing `psycopg` | Audit insert + event update |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `confidence_config.py` | `backend/app/core/confidence_config.py` | Weights, thresholds, FoW dampener, source quality maps, major categories |
| `confidence_scorer.py` | `backend/app/services/confidence_scorer.py` | Scorer, persistence, audit write, breakdown payload |
| `event_factor_match.py` | `backend/app/services/event_factor_match.py` | 8-factor keyword match + strength |
| `events.py` | `backend/app/api/events.py` | Breakdown HTTP handler |
| `0027_confidence_audit.sql` | `backend/db/migrations/0027_confidence_audit.sql` | Audit table + `factor_db_match_count` |
| `test_confidence_scorer.py` | `backend/tests/test_confidence_scorer.py` | Weights, FoW, is_major, calibration ≥80% |
| `test_confidence_gate.py` | `backend/tests/test_confidence_gate.py` | Narrow MEDIUM boundary tests |
| `test_confidence_audit_migration_sql.py` | `backend/tests/test_confidence_audit_migration_sql.py` | Static SQL contract |
| `test_confidence_breakdown_api.py` | `backend/tests/test_confidence_breakdown_api.py` | API shape + 404 + Cache-Control |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `confidence_gate.py` | `backend/app/services/confidence_gate.py` | **Replaced** source-count routing with `route(confidence_effective: float)` |
| `event_dedup.py` | `backend/app/services/event_dedup.py` | Removed inline SQL confidence blend on merge; calls `apply_confidence_to_event_row` after upsert |
| `signal_monitor_runner.py` | `backend/app/services/signal_monitor_runner.py` | Joins `events`; gates on `confidence_effective` |
| `card_pipeline.py` | `backend/app/services/card_pipeline.py` | `apply_confidence_to_event()` at start of `draft_card_from_event` |
| `migrate.py` | `backend/app/db/migrate.py` | Registers `0027_confidence_audit.sql` |
| `main.py` | `backend/app/main.py` | Registers `events_router` at `/api` |
| `test_signal_monitor_logs_override_decisions.py` | `backend/tests/test_signal_monitor_logs_override_decisions.py` | Events seeded with `confidence_raw` / `confidence_effective` per expected tier |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S1g AC + tasks **8.0**–**8.6** marked complete |
| `intelligence-pipeline-overview.md` | `docs/intelligence-pipeline-overview.md` | Notes `factor_db_match` implemented in S1g |

**Not modified (intentionally)**

| File | Note |
|------|------|
| `feed.py` `detect_fog_of_war` | Still card-count heuristic until **P3-S1l** |
| `frontend/**` | Explainability UI is **P3-S1h** |
| `synthetic_events.json` | Hand-grade `confidence_raw` unchanged; scorer calibrates against tiers |

---

### A8. TESTS EXECUTED

| Test file | Test function / group | Status | What it verifies |
|-----------|----------------------|--------|------------------|
| `test_confidence_scorer.py` | `test_tier_boundaries_narrow_medium_band` | **Pass** | HIGH / MEDIUM / LOW at 0.75 and 0.55 edges |
| `test_confidence_scorer.py` | `test_gate_matches_tier_thresholds` | **Pass** | Gate aligns with `tier_from_score` |
| `test_confidence_scorer.py` | `test_fog_dampener_applies_to_effective_only` | **Pass** | `effective = raw × 0.6` when FoW on; raw unchanged |
| `test_confidence_scorer.py` | `test_is_major_requires_raw_factors_and_category` | **Pass** | All three conditions for `is_major` |
| `test_confidence_scorer.py` | `test_unique_publisher_cap_at_three` | **Pass** | Domain cap normalisation |
| `test_confidence_scorer.py` | `test_factor_match_strength_two_keyword_hits` | **Pass** | Strength 1.0 with 2+ keyword factors |
| `test_confidence_scorer.py` | `test_synthetic_calibration_at_least_eighty_percent_match` | **Pass** | ≥80% of 20 synthetic fixtures tier-match hand-grade |
| `test_confidence_gate.py` | `test_gate_high_at_threshold` | **Pass** | `score_gte_075` reason |
| `test_confidence_gate.py` | `test_gate_medium_narrow_band` | **Pass** | 0.60 → medium |
| `test_confidence_gate.py` | `test_gate_low_below_medium` | **Pass** | Below 0.55 → low |
| `test_confidence_gate.py` | `test_gate_boundary_medium_low` | **Pass** | Exactly 0.55 → medium |
| `test_confidence_audit_migration_sql.py` | `test_confidence_audit_migration_schema` | **Pass** | Table + column DDL present |
| `test_confidence_breakdown_api.py` | `test_confidence_breakdown_shape` | **Pass** | JSON shape + `Cache-Control` max-age=60 |
| `test_confidence_breakdown_api.py` | `test_confidence_breakdown_not_found` | **Pass** | 404 for unknown event |
| `test_signal_monitor_logs_override_decisions.py` | `test_signal_monitor_routes_and_logs_gate` (×3) | **Pass** | High/medium/low from seeded effective scores |
| `test_event_dedup.py` | (all) | **Pass** | Dedup regression with scorer hook |
| `test_data_pipeline_integration.py` | (all) | **Pass** | Cross-pipeline regression |

**Commands used (full backend CI)**

```powershell
cd c:\Projects\InvestmentAssistant
python -m ruff check backend
python -m pytest -q backend/tests
```

**Result:** **292 passed**, ruff clean (31-05-2026 implementation run).

**Frontend:** No frontend changes in P3-S1g — **not run** for this story.

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Migration:** `backend/db/migrations/0027_confidence_audit.sql`  
**Sequence:** After `0026_pipeline_runs_held_status.sql` (registered in `backend/app/db/migrate.py`).

**`events` column added**

| Column | Type | Purpose |
|--------|------|---------|
| `factor_db_match_count` | `smallint NOT NULL DEFAULT 0` | Number of macro factors matched (keyword + category rules) |

**New table: `confidence_score_audit`**

| Column | Type | Notes |
|--------|------|-------|
| `id` | `uuid` PK | `gen_random_uuid()` |
| `event_id` | `uuid` FK → `events(id)` ON DELETE CASCADE | |
| `confidence_raw` | `numeric(4,3)` | Undampened weighted score |
| `confidence_effective` | `numeric(4,3)` | After FoW dampener |
| `inputs_json` | `jsonb` | Full scorer inputs + breakdown snapshot |
| `scorer_version` | `text` | e.g. `confidence_scorer.v1` |
| `created_at` | `timestamptz` | Append-only |

**Index:** `idx_confidence_score_audit_event_id (event_id, created_at DESC)`

**Pre-existing columns used (P3-S0):** `confidence_raw`, `confidence_effective`, `is_major`, `is_major_override`, `force_editorial_review`, `source_count`, `sources`.

**Seed data:** No new seed script. Synthetic events in `backend/scripts/seed_data/synthetic_events.json` retain hand-set `confidence_raw` for historical calibration reference.

**Apply migration**

```powershell
# Via project migrate helper (uses SUPABASE_DB_URL)
python -c "from app.db.connection import connection; from app.db.migrate import apply_migrations; apply_migrations(connection())"
```

Or run SQL in Supabase SQL editor on target environment.

---

### B2. API / INTEGRATION CONTRACTS

**Confidence breakdown (public read)**

```http
GET /api/events/{event_id}/confidence-breakdown
```

**Success (200)** — example shape:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "confidence_raw": 0.82,
  "confidence_effective": 0.492,
  "tier": "low",
  "fog_active": true,
  "fog_dampener": 0.6,
  "calibration_status": "provisional",
  "scorer_version": "confidence_scorer.v1",
  "is_major": true,
  "force_editorial_review": false,
  "inputs": {
    "source_count": { "value": 0.67, "weight": 0.30, "detail": "2 sources post-dedup" },
    "source_quality": { "value": 1.0, "weight": 0.30, "detail": "primary_source=rbi_rss" },
    "factor_db_match": { "value": 1.0, "weight": 0.25, "detail": "2 factors (domestic_interest_rates, ...)" },
    "recency": { "value": 1.0, "weight": 0.05, "detail": "first_seen=..." },
    "unique_publisher": { "value": 0.67, "weight": 0.10, "detail": "2 publishers (domain-level)" }
  },
  "sources": [
    { "name": "rbi_rss", "url": "https://www.rbi.org.in/...", "retrieved_at": "2025-06-06T06:00:00+00:00" }
  ]
}
```

**Not found (404)**

```json
{
  "detail": {
    "code": "event_not_found",
    "message": "Event not found"
  }
}
```

**Auth:** No JWT required on this route today (matches feed read pattern). Revisit if synthetic events must be hidden from anonymous breakdown reads — RLS hides synthetic from `authenticated` role on direct Postgres reads; API uses service role via `SUPABASE_DB_URL`.

**Cache:** `Cache-Control: private, max-age=60, stale-while-revalidate=300`

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Weighted raw score**

```
raw = round(clamp(
  W_src * min(source_count/3, 1) +
  W_qual * source_quality +
  W_fac * factor_match_strength +
  W_rec * recency_score(first_seen_at) +
  W_pub * min(unique_publishers/3, 1)
, 0, 1), 3)
```

**FoW dampener**

```
fog_active = (COUNT events WHERE is_major AND lifecycle IN (active, signal_triggered)
              AND COALESCE(is_major_override, is_major)) >= 3

effective = raw * (FOG_DAMPENER if fog_active else 1.0)   # FOG_DAMPENER = 0.6
tier = tier_from_score(effective)
```

**Signal monitor flow (simplified)**

```
for each pending signal on published/active card:
  eval = evaluate(signal_text, market_facts)
  if eval.status == "none": continue
  decision = route(card.event.confidence_effective)
  log confidence_gate_log + high/medium/low path
```

**Dedup flow (simplified)**

```
UPSERT event by dedup_key
→ apply_confidence_to_event_row (same transaction)
→ optional cross_category review queue on insert
→ commit
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Detail |
|------|--------|
| **Keyword factor match** | Not a full Factor DB graph; may mis-tag edge headlines until calibration |
| **FoW detection for dampener** | Uses `is_major` event count, not P3-S1l feed banner model |
| **Feed FoW still legacy** | `feed.py` uses card confidence_score ≥ 70 heuristic — **P3-S1l** rewrites |
| **Calibration `provisional`** | Weights/thresholds not validated on live editor overrides yet (G-11, Day 30) |
| **Breakdown vs audit** | API recomputes; may differ slightly from last audit row if config changed |
| **No RLS on `confidence_score_audit`** | Service-role only today; add policies if exposed via PostgREST |
| **`recompute_confidence_raw` interim** | Still used for initial INSERT placeholder before scorer runs in txn |

---

### B5. TESTING NOTES

- **Automated:** All scorer/gate/API tests use fixtures or DB with migrations; no live external APIs.
- **Calibration test:** `_calibration_inputs()` derives synthetic fixture inputs from hand-grade `confidence_raw` bands — documents expected ≥80% tier agreement, not exact raw score equality.
- **Not automated:** Browser Thread panel (P3-S1h); production calibration workshop on live ingest.
- **Manual smoke (recommended post-deploy):**
  1. Apply migration `0027`.
  2. Ingest or merge an event via dedup; confirm `confidence_score_audit` row exists.
  3. `GET /api/events/{id}/confidence-breakdown` returns five input bars + sources.
  4. Fire signal monitor on card with known `confidence_effective`; confirm `confidence_gate_log.reason` starts with `score_`.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required | Purpose |
|----------|----------|---------|
| `SUPABASE_DB_URL` | Yes | Dedup, audit writes, breakdown API |

**No new env vars** for P3-S1g.

**Tuning without structural code change:** Edit `backend/app/core/confidence_config.py` (weights, thresholds, `FOG_DAMPENER`, domain quality map). Redeploy backend; bump `SCORER_VERSION` when logic changes materially for audit clarity.

**Deployment sequencing**

1. Apply **0027** migration.
2. Deploy backend (scorer + gate + API).
3. Optional: backfill — run a one-off script to `apply_confidence_to_event(id)` for existing rows (not shipped in S1g; consider before P3-S1h if breakdown shows stale zeros).

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read **G-01** and **G-02** in `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §3.
2. Understand **raw vs effective** — FoW and explainability UI must show both (P3-S1h).
3. Signal monitor: **two steps** — (a) did facts match? (`evaluate`), (b) which tier? (`route(effective)`).

**Common mistakes**

- Restoring **three direct sources → high** gate logic.
- Writing dampened score into **`confidence_raw`**.
- Ignoring **`is_major_override`** on UPDATE.
- Expecting **`factor_db_match`** to query `instrument_factor_sensitivity` on every ingest (it does not in S1g).

**Key file paths**

| Concern | Path |
|---------|------|
| Weights / thresholds | `backend/app/core/confidence_config.py` |
| Scorer + audit | `backend/app/services/confidence_scorer.py` |
| Factor keywords | `backend/app/services/event_factor_match.py` |
| Gate | `backend/app/services/confidence_gate.py` |
| Dedup hook | `backend/app/services/event_dedup.py` |
| Signal monitor | `backend/app/services/signal_monitor_runner.py` |
| Card draft refresh | `backend/app/services/card_pipeline.py` |
| Breakdown API | `backend/app/api/events.py` |
| Migration | `backend/db/migrations/0027_confidence_audit.sql` |

**Contact for product context:** Product Owner — weight split (10% unique publisher), narrow MEDIUM band, and `is_major` category list.

---

## Quick operator checklist

| Step | Action |
|------|--------|
| 1 | Apply migration `0027_confidence_audit.sql` on dev/staging/prod |
| 2 | Deploy backend |
| 3 | Verify dedup ingest creates `confidence_score_audit` rows |
| 4 | `GET /api/events/{uuid}/confidence-breakdown` — 200 + five inputs |
| 5 | Confirm signal monitor logs `score_gte_075` / `score_055_074` / `score_lt_055` reasons |
| 6 | Proceed to **P3-S1h** (Confidence explainability UI) |

---

## Key information highlight (executive summary)

| Topic | Key fact |
|-------|----------|
| **Story** | P3-S1g — rule-based confidence scorer + gate swap |
| **Category** | Backend (+ breakdown API for upcoming UI) |
| **PO gaps closed** | G-01 Option B (10% unique publisher), G-02 narrow MEDIUM |
| **Score range** | 0.0–1.0 raw; effective = raw × 0.6 when FoW active |
| **Tiers (effective)** | HIGH ≥ 0.75 · MEDIUM 0.55–0.74 · LOW &lt; 0.55 |
| **Weights** | 30% source count · 30% quality · 25% factor match · 5% recency · 10% unique publisher |
| **Migration** | **0027** — `confidence_score_audit` + `factor_db_match_count` |
| **API** | `GET /api/events/{id}/confidence-breakdown` (60s cache) |
| **Gate change** | `route(confidence_effective)` replaces source-count routing |
| **Tests** | **292** backend tests pass; ruff clean |
| **Next** | P3-S1h UI → P3-T3 gate → P3-S1l FoW banner on `is_major` |
