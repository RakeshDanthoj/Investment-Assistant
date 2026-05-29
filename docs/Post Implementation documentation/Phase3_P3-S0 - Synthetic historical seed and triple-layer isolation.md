# Post Implementation Detailed Document — P3-S0

**Version:** v1.0 | **Date:** 29-05-2026  
**Story ID:** P3-S0 (Phase 3, Story 0)  
**PRD2 gap:** G-13  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md`  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §7.2, `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` WS-0

---

## Narrative style (read this first)

Phase 3 needs **months of historical confidence and major-event data** to calibrate the rule-based scorer, backtest Fog of War, and (later) the P3-S2 interaction model — but there are no live Mirror/Lens testers yet. **P3-S0** solves that by seeding **20 verifiable Indian financial events (Jan–Jun 2025)** into production tables with `is_synthetic = TRUE`, plus **triple-layer isolation** so that data never pollutes user trust metrics.

Layer 1 is **Postgres RLS**: `authenticated` role cannot `SELECT` synthetic rows on `events`, `signals`, `track_record`, `user_predictions`, or `card_confidence_history`. Layer 2 is **`SyntheticFilterMixin`** in the FastAPI service layer (Pulse, Thread, Mirror, market-facts reads) because the API connects via `SUPABASE_DB_URL` as the `postgres` role, which **bypasses RLS**. Layer 3 (CI static/query guards) is **P3-T1**, not this story.

The migration also adds **Phase 3 schema foundations** used by later stories: `confidence_raw`, `confidence_effective`, `is_major`, `dedup_key`, `external_id`, and the `card_confidence_history` table (FoW dampener snapshots in P3-S1l). No frontend or new API routes were added.

**Tests executed and passed (P3-S0–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Migration SQL contract | `python -m pytest tests/test_synthetic_isolation_migration_sql.py -q` | **3 passed** |
| Seed idempotency (integration) | `python -m pytest tests/test_synthetic_seed_idempotent.py -q` | **1 passed** (requires DB; see B5) |
| Regression (feed / FoW / mirror / query consolidation) | `python -m pytest tests/test_feed_filtering.py tests/test_fog_of_war_detector.py tests/test_mirror_routes.py tests/test_query_consolidation.py -q` | **21 passed** |

**Combined P3-S0 + regression run:** 25 passed when dev DB had no prior synthetic seed; if synthetic rows already exist, the idempotency test’s `first["inserted"] == 20` assertion may fail — the **second-run** assertions (`inserted == 0`, `updated == 20`, row counts) remain the contract.

**Three anchors for handover:** (1) **Run migration `0021` once per environment** before seed or deploy; (2) **Deploy backend code** with `SyntheticFilterMixin` — RLS alone does not protect API reads; (3) **Synthetic events are events-only** in this story (no cards/signals/predictions seeded yet).

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S0 |
| **Title** | Synthetic historical seed + triple-layer isolation |
| **Category** | **Backend** (DB migration, seed scripts, service-layer SQL filters; no UI) |
| **Points / owner (plan)** | 5 · Jordan |
| **Depends on** | None (Week 1 Phase 3 entry) |
| **Blocks** | P3-T1, P3-S1c, P3-S1d/e, P3-S2 (after 30-day soak) |

**What this story aimed to achieve (plain language)**

FinnWise needs historical event data to tune confidence scoring and Fog of War without waiting for real users. This story inserts **20 labelled synthetic events** from public 2025 news themes, marks them `is_synthetic = TRUE`, and ensures they **never appear** in Pulse, Thread, Mirror, or track-record surfaces that users trust. Re-running the seed script must not create duplicates.

**How it fits into the overall application**

- **Upstream:** Phase 2 stable (`events`, `cards`, `track_record`, migrations through `0020`).
- **This story:** Data + isolation plumbing for PRD2 intelligence workstreams.
- **Downstream:** P3-T1 (isolation tests), P3-S1c (dedup uses `dedup_key`), P3-S1g (confidence scorer uses `confidence_raw`), P3-S1l (FoW uses `is_major` + `card_confidence_history`), P3-S2 (interaction model after 30 days of synthetic history).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **1.1** | Migration `0021_synthetic_isolation.sql`: columns, indexes, `card_confidence_history` table, RLS policies. |
| **1.2** | `synthetic_events.json` (20 events, 7 `is_major`) + `seed_synthetic_events.py` CLI + `app/db/synthetic_seed.py` core logic. |
| **1.3** | `SyntheticFilterMixin` in `app/db/queries/base.py`; wired into feed, card_repository (Thread), mirror_predictions, market_facts. |
| **1.4** | Seed runnable against dev/staging via `SUPABASE_DB_URL`; verify counts with SQL. |
| **1.5** | `test_synthetic_seed_idempotent.py` — second run inserts zero new rows. |
| **1.6** | `backend/scripts/README.md` documents seed command. |

**Functional breakdown**

1. Operator applies pending migrations (includes `0021`) with `python scripts/apply_migrations.py`.
2. Operator runs `python backend/scripts/seed_synthetic_events.py` (applies migrations by default unless `--skip-migration`).
3. Each fixture row UPSERTs on `external_id` with `event_source = 'synthetic_seed'` and `canonical_url = synthetic://seed/{external_id}` (avoids collision with live `(event_source, canonical_url)` dedupe from `0006`).
4. User-facing API paths append `COALESCE(alias.is_synthetic, FALSE) = FALSE` on `events` (and `user_predictions` / `track_record` where applicable).
5. Authenticated Supabase/PostgREST reads of affected tables cannot see `is_synthetic = TRUE` rows.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Re-run seed | `ON CONFLICT (external_id) DO UPDATE`; no duplicate rows. |
| Fixture count | `seed_events()` raises if not exactly 20 rows or 7 `is_major`. |
| `confidence_score` (legacy smallint) | Derived as `round(confidence_raw * 100)` clamped 0–100 for existing Pulse/FoW heuristics. |
| Missing `SUPABASE_DB_URL` | Seed script / integration tests skip or fail with settings error. |
| Postgres role (API) | Bypasses RLS → **service-layer filter is mandatory**. |
| Events without cards | Synthetic rows exist in `events` only; Pulse still won’t list them until cards are published (future stories may add synthetic cards). |

**Business rules enforced**

- All seeded rows: `is_synthetic = TRUE`.
- Exactly **7** events with `is_major = TRUE` (FoW backtest trigger history per PRD2).
- Historical window: **Jan–Jun 2025** (`occurred_at` → `events.created_at`).
- PRD2 non-negotiable (prepared, not fully used until later stories): `confidence_raw` on events; FoW dampener must not mutate raw in place (history table ready).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Migration `0021`** | Next free slot after `0020_rate_limit_observability.sql`. | `00XX` placeholder numbering: breaks `apply_migrations` ordering. |
| **`external_id` UPSERT key** | Plan AC; stable idempotent seed independent of URL dedupe. | UPSERT on `(event_source, canonical_url)` only: collides with ingest adapters. |
| **`synthetic://seed/{id}` canonical URLs** | Satisfies NOT NULL `canonical_url` + unique `(event_source, canonical_url)`. | Reuse real news URLs: risk collision with live ingest. |
| **Core logic in `app/db/synthetic_seed.py`** | Testable import path; CLI is thin wrapper. | Tests importing `scripts.*` as module: not a package. |
| **`SyntheticFilterMixin` as SQL fragment helpers** | Minimal diff; matches existing inline SQL style in services. | ORM-wide global filter: no ORM in project. |
| **Create `card_confidence_history` now** | RLS list in AC; P3-S1l needs table; empty until FoW story. | Defer table to P3-S1l: would leave RLS AC incomplete. |
| **Enable RLS on `events`, `signals`, `user_predictions`** | PRD2 triple-layer; first SELECT policies on those tables. | RLS-only on `track_record`: incomplete isolation. |
| **Events-only seed (no cards)** | AC specifies 20 events; cards would need LLM/editorial pipeline. | Full ICE bundles in seed: out of scope for S0. |

⚠️ **Do not remove `SyntheticFilterMixin` from API read paths** — the backend DB user bypasses RLS; users could see synthetic data through Pulse/Thread/Mirror without it.

⚠️ **Do not assume RLS protects the FastAPI app** — only JWT/PostgREST `authenticated` clients.

⚠️ **Do not delete synthetic rows in production without a migration plan** — downstream calibration scripts may depend on them.

⚠️ **Enabling RLS on `user_predictions` without INSERT policies** — if the frontend ever writes predictions via Supabase client (not API), INSERT may be denied. Today writes go through FastAPI + postgres role; verify before adding direct client writes.

**Assumptions**

- Dev/staging/production each get migration + seed **once** per environment (manual ops).
- `confidence_raw` / `confidence_effective` on seeded events are **representative placeholders**, not scorer output (scorer ships in P3-S1g).
- P3-T1 will add API-level isolation tests and CI grep guards.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | `0004_core_tables` (events), `0006` (canonical dedupe), `0008` (cards), `0005` (track_record RLS), Phase 2 complete. |
| **Downstream — immediate** | **P3-T1** isolation verification gate; **P3-S1c** dedup (`dedup_key` column exists). |
| **Downstream — Phase 3** | **P3-S1g** scorer + gate; **P3-S1l** FoW `is_major` + `card_confidence_history` writes; **P3-S2** interaction model (30-day soak after seed). |
| **Parallel (after 1.1)** | P3-S1d (NewsAPI), P3-S1e (watchlist) per milestone map. |

**Shared components touched**

- `public.events` (primary seed target)
- `public.signals`, `public.track_record`, `public.user_predictions` (columns + RLS only)
- `public.card_confidence_history` (new)
- Services: `feed.py`, `card_repository.py`, `mirror_predictions.py`, `market_facts.py`

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Triple-layer isolation** (RLS + service SQL + future CI) per PRD2 G-13.
- **Idempotent operational seed** (UPSERT + JSON fixture), same family as factor DB seeds.
- **Vertical slice boundary:** DB + scripts only; no new HTTP routes.

**Database schema (summary)**

| Object | Change |
|--------|--------|
| `events` | `is_synthetic`, `confidence_raw`, `confidence_effective`, `is_major`, override cols, `dedup_key`, `external_id`; partial unique indexes on `external_id`, `dedup_key`. |
| `signals`, `track_record`, `user_predictions` | `is_synthetic boolean DEFAULT false`. |
| `card_confidence_history` | New table for effective-score snapshots (P3-S1l). |

**API contracts**

- **No new or modified HTTP routes** in P3-S0.
- Existing Pulse/Thread/Mirror behaviour unchanged for real data; synthetic events excluded at SQL level when joined on `events`.

**UI/UX**

- None.

**Libraries / tools**

- `psycopg` (existing) for seed + tests.
- No new pip dependencies.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0021_synthetic_isolation.sql` | `backend/db/migrations/0021_synthetic_isolation.sql` | Schema columns, `card_confidence_history`, RLS policies |
| `synthetic_events.json` | `backend/scripts/seed_data/synthetic_events.json` | 20 event definitions (7 `is_major`) |
| `seed_synthetic_events.py` | `backend/scripts/seed_synthetic_events.py` | CLI entrypoint for seed |
| `synthetic_seed.py` | `backend/app/db/synthetic_seed.py` | Idempotent UPSERT logic + fixture validation |
| `base.py` | `backend/app/db/queries/base.py` | `SyntheticFilterMixin` SQL helpers |
| `__init__.py` | `backend/app/db/queries/__init__.py` | Package export for mixin |
| `README.md` | `backend/scripts/README.md` | Operator docs for seed (and sector generator ref) |
| `test_synthetic_isolation_migration_sql.py` | `backend/tests/test_synthetic_isolation_migration_sql.py` | Static migration contract tests |
| `test_synthetic_seed_idempotent.py` | `backend/tests/test_synthetic_seed_idempotent.py` | Integration: idempotent seed |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `migrate.py` | `backend/app/db/migrate.py` | Registered `0021_synthetic_isolation.sql` in `MIGRATION_FILES` |
| `feed.py` | `backend/app/services/feed.py` | Synthetic filter on Pulse rows + FoW query |
| `card_repository.py` | `backend/app/services/card_repository.py` | Synthetic filter on Thread/detail + track_record read |
| `mirror_predictions.py` | `backend/app/services/mirror_predictions.py` | Synthetic filter on list + stats queries |
| `market_facts.py` | `backend/app/services/market_facts.py` | Synthetic filter on recent event facts |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S0 acceptance criteria and tasks marked complete |

---

### A8. TESTS EXECUTED

| Test file | Tests | Status | What it verifies |
|-----------|-------|--------|----------------|
| `test_synthetic_isolation_migration_sql.py` | 3 | **Pass** | Migration contains required columns, RLS policy names, `card_confidence_history` DDL |
| `test_synthetic_seed_idempotent.py` | 1 | **Pass** (integration; see note) | Second `seed_events()` call: `inserted=0`, `updated=20`, DB counts 20 / 7 major |
| `test_feed_filtering.py` | (suite) | **Pass** | Pulse filtering unchanged for real cards |
| `test_fog_of_war_detector.py` | (suite) | **Pass** | FoW heuristic still valid after feed SQL change |
| `test_mirror_routes.py` | (suite) | **Pass** | Mirror API routes after prediction SQL change |
| `test_query_consolidation.py` | (suite) | **Pass** | Single-connection feed/detail patterns intact |

**Commands used**

```bash
cd backend
python -m pytest tests/test_synthetic_isolation_migration_sql.py tests/test_synthetic_seed_idempotent.py -q
python -m pytest tests/test_feed_filtering.py tests/test_fog_of_war_detector.py tests/test_mirror_routes.py tests/test_query_consolidation.py -q
```

**Note:** `test_synthetic_seed_idempotent` patches `connection()` to use the pytest `db_connection` fixture. First-run `inserted == 20` only holds on a DB with **no prior synthetic seed**; after seeding once, first call reports `updated=20`. Prefer asserting second-run idempotency and final counts for CI stability (improvement candidate for P3-T1).

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**`events` (altered)**

| Column | Type | Notes |
|--------|------|--------|
| `is_synthetic` | `boolean NOT NULL DEFAULT false` | Seed sets `TRUE` |
| `confidence_raw` | `numeric(4,3)` | 0.000–0.999 style scores |
| `confidence_effective` | `numeric(4,3)` | Same as raw until FoW dampener (P3-S1l) |
| `is_major` | `boolean NOT NULL DEFAULT false` | 7 seeded `TRUE` |
| `is_major_override` | `boolean` | Nullable; P3-S1l editorial override |
| `is_major_override_by` | `uuid` | Nullable |
| `is_major_override_at` | `timestamptz` | Nullable |
| `dedup_key` | `text` | Unique partial index; populated in P3-S1c |
| `external_id` | `text` | Unique partial index; seed UPSERT key |

**`card_confidence_history` (new)**

| Column | Type | Notes |
|--------|------|--------|
| `id` | `uuid PK` | |
| `card_id` | `uuid FK → cards` | CASCADE delete |
| `confidence_raw` | `numeric(4,3)` | Snapshot |
| `confidence_effective` | `numeric(4,3)` | After dampener |
| `fog_active` | `boolean` | Whether FoW applied |
| `recorded_at` | `timestamptz` | Default `now()` |
| `is_synthetic` | `boolean` | RLS filter |

**Migration sequencing:** Apply after `0020`. Registered in `backend/app/db/migrate.py` → run via `python scripts/apply_migrations.py`.

**Seed data:** `backend/scripts/seed_data/synthetic_events.json` — 20 publicly verifiable 2025 India market themes (RBI MPC, Budget, FII flows, geopolitical shocks, sector results, etc.). Categories use existing `event_category` enum values.

**Verification SQL**

```sql
SELECT count(*) FROM public.events WHERE is_synthetic = TRUE;
-- expect 20

SELECT count(*) FROM public.events WHERE is_synthetic = TRUE AND is_major = TRUE;
-- expect 7
```

---

### B2. API / INTEGRATION CONTRACTS

**No new endpoints.**

**Behavioural change (internal SQL only)**

| Surface | Module | Filter |
|---------|--------|--------|
| Pulse feed | `feed._fetch_pulse_rows_conn` | `events` alias `e` |
| Fog of War flag | `feed._fetch_fog_of_war_conn` | `events` alias `e` |
| Thread card detail | `card_repository.fetch_card_detail_*` | `events` alias `e` |
| Original view snapshot | `card_repository.fetch_track_record_initial_publish` | `track_record` |
| Mirror list / stats | `mirror_predictions` | `user_predictions` + `events` |
| Signal corroboration facts | `market_facts.fetch_recent_event_facts` | `events` |

Auth unchanged: existing JWT/session rules per route.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Seed UPSERT flow**

```
load JSON → validate 20 rows, 7 is_major
  → for each row:
       external_id, title, category, source_url
       canonical_url = synthetic://seed/{external_id}
       event_source = synthetic_seed
       confidence_score = round(confidence_raw * 100)
       is_synthetic = TRUE (INSERT only; UPDATE forces TRUE)
       ON CONFLICT (external_id) DO UPDATE
```

**Isolation rule (service layer)**

```text
User-facing read  →  COALESCE(table.is_synthetic, FALSE) = FALSE
Admin/backtest    →  service role / postgres (no filter) — intentional
Authenticated JWT →  RLS NOT is_synthetic on SELECT
```

**Seven `is_major` seeded events (external_id)**

1. `syn-2025-02-union-budget-2025-26`  
2. `syn-2025-02-rbi-mpc-rate-hold`  
3. `syn-2025-04-rbi-rate-cut-25bps`  
4. `syn-2025-04-pahalgam-market-reaction`  
5. `syn-2025-04-nifty-bank-circuit`  
6. `syn-2025-05-india-pakistan-tensions`  
7. `syn-2025-06-rbi-mpc-june`

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Detail |
|------|--------|
| **Events only** | No synthetic `cards`, `signals`, `user_predictions`, or `track_record` rows yet — FoW/Pulse backtests on synthetic *cards* need a follow-up or P3-T1+ seed extension. |
| **Legacy `confidence_score`** | Pulse/FoW still use smallint `confidence_score`; `confidence_raw` not yet wired to tier labels (P3-S1g). |
| **RLS INSERT gaps** | `user_predictions` / `events` have SELECT-only synthetic policies; direct Supabase client writes may need extra policies. |
| **Idempotency test brittleness** | `first["inserted"] == 20` fails if seed already ran on shared dev DB. |
| **P3-T1 not done** | No `test_synthetic_isolation.py` API tests or CI grep guard yet. |
| **Pool shutdown noise** | CLI seed may log psycopg pool thread warnings on exit (harmless). |

---

### B5. TESTING NOTES

| Type | Coverage |
|------|----------|
| **Automated — static** | Migration file contains columns, policies, history table |
| **Automated — integration** | Seed idempotency + row counts (needs `SUPABASE_DB_URL`) |
| **Automated — regression** | Feed, FoW, Mirror routes, query consolidation |
| **Manual** | `apply_migrations` + `seed_synthetic_events.py` on staging/prod; SQL count checks |
| **Gap** | No HTTP-level test that Pulse returns zero synthetic cards (P3-T1) |
| **Gap** | No test that authenticated PostgREST cannot read synthetic rows |

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required | Notes |
|----------|----------|--------|
| `SUPABASE_DB_URL` | Yes (seed + integration tests) | Session pooler URI recommended on Render |

**No new feature flags.**

**Deployment sequencing (per environment)**

1. Deploy backend build containing `SyntheticFilterMixin` + migration file.  
2. `python scripts/apply_migrations.py` (applies through `0021`).  
3. `python backend/scripts/seed_synthetic_events.py` (optional on prod until calibration needed).  
4. Verify SQL counts.

Migrations are **not** run automatically on Render app startup (`main.py` lifespan only opens the pool).

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read PRD2 §7.2 (synthetic seed) and §10 (never mutate `confidence_raw` in place).  
2. Any new **user-facing** query that reads `events`, `user_predictions`, `track_record`, or `signals` must use `SyntheticFilterMixin` (or equivalent).  
3. Admin/backtest scripts may intentionally query synthetic rows — do not add the filter there.

**Common mistakes**

- Relying on RLS alone for API safety.  
- Seeding with real `canonical_url` values (ingest dedupe collisions).  
- Removing `external_id` unique index without changing UPSERT logic.  
- Expecting synthetic events in Pulse without published synthetic cards.

**Where to look**

| Concern | Location |
|---------|----------|
| Migration | `backend/db/migrations/0021_synthetic_isolation.sql` |
| Seed logic | `backend/app/db/synthetic_seed.py` |
| Fixture | `backend/scripts/seed_data/synthetic_events.json` |
| SQL filter helpers | `backend/app/db/queries/base.py` |
| Pulse | `backend/app/services/feed.py` |
| Thread | `backend/app/services/card_repository.py` |
| Mirror | `backend/app/services/mirror_predictions.py` |
| Ops docs | `backend/scripts/README.md` |

**Next story:** **P3-T1** — `test_synthetic_isolation.py`, `test_query_synthetic_filter.py`, CI wiring.

**Context owner (role):** Platform/backend engineer owning Phase 3 data pipeline and PRD2 intelligence gaps.

---

_End of document — P3-S0 v1.0_
