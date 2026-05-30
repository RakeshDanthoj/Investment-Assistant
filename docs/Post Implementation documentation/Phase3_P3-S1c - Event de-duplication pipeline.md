# Post Implementation Detailed Document — P3-S1c

**Version:** v1.0 | **Date:** 30-05-2026  
**Story ID:** P3-S1c (Phase 3, Story 1c)  
**PRD2 gap:** G-03  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **3.0**–**3.6**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §4.1, `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` WS-1 / G-03

---

## Narrative style (read this first)

When the same real-world story hits NewsAPI, RBI RSS, and NSE within hours, Phase 1 ingest treated each outlet as a **separate** `events` row (unique on `event_source + canonical_url`). That inflates editorial workload and will poison the Phase 3 confidence scorer’s `source_count` input. **P3-S1c** fixes that by merging ingest into **one row per real-world event**, keyed by a composite `dedup_key`, while accumulating provenance in `sources[]` and `source_count`.

The dedup key is `sha256(category | normalised_entity | 4h_window | headline_hash)` for **all** event categories — including `headline_hash` everywhere was a binding PO decision (G-03), not only for RBI/REGULATORY. Same headline + entity + window from two outlets **merges**; two distinct RBI stories the same afternoon **do not** merge because the headline component differs. Cross-category collisions (same entity/window/headline but different `category`) stay as **two event rows** and are flagged in `dedup_review_queue` for Sunday review — no auto-merge across categories.

The **4-hour event-detection cron** (`python -m app.jobs.event_detection`) now calls `persist_deduped_event` (Postgres upsert via `SUPABASE_DB_URL`) instead of `persist_draft_event` (Supabase REST + URL dedupe). `confidence_raw` is updated on merge using an **interim** blend until **P3-S1g** ships the full rule-based scorer. When `source_count > 5`, `force_editorial_review` is set regardless of score (defensive guardrail from PRD2 brainstorm).

**Tests executed and passed (P3-S1c–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Dedup unit + integration | `python -m pytest backend/tests/test_event_dedup.py -q` | **10 passed** |
| Review queue integration | `python -m pytest backend/tests/test_dedup_review_queue.py -q` | **2 passed** |
| Migration SQL contract | `python -m pytest backend/tests/test_dedup_migration_sql.py -q` | **3 passed** |
| Event detection persist signature | `python -m pytest backend/tests/test_event_detection_idempotent.py -q` | **1 passed** |
| **Combined P3-S1c slice** | `python -m pytest backend/tests/test_event_dedup.py backend/tests/test_dedup_review_queue.py backend/tests/test_dedup_migration_sql.py backend/tests/test_event_detection_idempotent.py -q` | **16 passed** |
| Lint | `python -m ruff check backend` | **All checks passed** |

Integration tests require `SUPABASE_DB_URL` in `.env.local`; CI skips them when unset (same pattern as other DB tests).

**Three anchors for handover:** (1) **Apply migration `0023` once per environment** before cron ingest uses merge columns; (2) **Cron must have `SUPABASE_DB_URL`** — without it ingest returns `skipped_no_config`; (3) **Do not remove `headline_hash` from the key for “all categories”** without PO sign-off — it was an explicit Phase 3 decision.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S1c |
| **Title** | Event de-duplication pipeline |
| **Category** | **Backend** (DB migration, dedup service, event-detection job wiring; no UI) |
| **Points / owner (plan)** | 5 · Jordan |
| **Depends on** | P3-S0 (`dedup_key` column + unique partial index from `0021`) |
| **Blocks** | P3-S1f (market facts freshness), P3-T2 (data pipeline test gate), P3-S1g (confidence scorer — hard dependency on post-dedup `source_count`) |

**What this story aimed to achieve (plain language)**

Multiple news outlets often report the same RBI move or budget headline within hours. This story merges those into **one editorial queue row**, tracks how many sources contributed (`source_count`), stores each outlet in a `sources` JSON array, and bumps `confidence_raw` as sources accumulate. It also flags suspicious volume (`source_count > 5`) and queues cross-category “maybe same story” pairs for human review without auto-merging them.

**How it fits into the overall application**

- **Upstream:** P3-S0 added `dedup_key`, `confidence_raw`, and synthetic isolation; P1-S6 added `(event_source, canonical_url)` dedupe and the 4-hour cron.
- **This story:** Replaces URL-level dedupe on the ingest path with **semantic/event-level** dedupe; foundation for honest confidence scoring (G-01).
- **Downstream:** P3-S1g reads post-dedup `source_count`; P3-S1e Sunday digest will list `dedup_review_queue` (max 10 items); P3-T2 verifies the data pipeline gate.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **3.1** | Migration `0023_dedup_key_review_queue.sql`: `source_count`, `sources`, `force_editorial_review`, `collision_fingerprint`, `dedup_review_queue` table. |
| **3.2** | `event_dedup.py`: key computation, entity YAML map, headline normalisation, upsert SQL. |
| **3.3** | `event_detection.py` default persist → `persist_deduped_event`. |
| **3.4** | On **new** insert only: if `collision_fingerprint` matches another row with different `category`, insert `dedup_review_queue` row (`cross_category_same_window`). |
| **3.5** | `source_count > 5` → `force_editorial_review = true` on upsert conflict path. |
| **3.6** | Tests: merge same story, no false merge on different headlines, all-category headline in key, review queue, guardrail. |

**Functional breakdown**

1. Adapter fetches `RawEvent` (title, canonical_url, published_at, excerpt).
2. `infer_event_category` + `score` (unchanged heuristics from P1-S6).
3. `persist_deduped_event` computes `dedup_key` and `collision_fingerprint`, then `INSERT … ON CONFLICT (dedup_key) DO UPDATE`.
4. **Insert:** one row, `source_count = 1`, `sources` = single JSON object; optional cross-category queue rows.
5. **Conflict (same dedup_key):** increment `source_count`, append to `sources`, recompute `confidence_raw` in SQL, `confidence_score = GREATEST(...)`, set `force_editorial_review` if count > 5.
6. Job summary: first persist → `inserted`; merge → `duplicate` (same counter name as before, semantics now dedup-key merge).

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Missing `SUPABASE_DB_URL` | Returns `skipped_no_config`; no DB write. |
| Empty `canonical_url` | Returns `skipped_no_config`. |
| Same dedup_key, different URLs | Merges into one row (by design). |
| Same entity, different headlines in 4h window | Different `dedup_key` → separate rows. |
| Same headline/entity/window, different category | Two rows + `dedup_review_queue` entry; not merged. |
| Duplicate queue pair | Skips insert if pending row already exists for same `event_ids` set. |
| `detected_at` | Uses `published_at` from raw, else `utc_now()`. |
| Legacy rows without `dedup_key` | Unchanged; only **new** cron ingest gets keys (no backfill in S1c). |
| Synthetic seed rows | Unaffected; seed uses `external_id` UPSERT, not dedup path. |

**Business rules enforced**

- **G-03 PO:** `headline_hash` (normalised first 100 chars) in dedup key for **all** categories.
- **Entity map:** longest alias match in headline + body; default slug `unknown`.
- **4h window:** UTC epoch floored to 4-hour buckets (aligned with cron window).
- **Guardrail:** `source_count > 5` → `force_editorial_review` even if confidence is LOW.
- **Cross-category:** detect only; human Sunday review (P3-S1e digest) — no automatic merge.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Postgres upsert via `connection()`** | Atomic merge + `source_count`; needs `SUPABASE_DB_URL` on cron. | Keep REST `persist_draft_event`: cannot do `ON CONFLICT (dedup_key)` cleanly. |
| **`headline_hash` for all categories** | Phase 3 plan PO registry (G-03). | RBI/REGULATORY only (SSA doc draft): rejected for Phase 3 build. |
| **`collision_fingerprint` without category** | Cross-category probe separate from merge key. | Merge across categories: risks false merges (workshop). |
| **Interim `confidence_raw` formula** | Unblocks merge behaviour before P3-S1g scorer. | Call future scorer from ingest: circular dependency. |
| **`entity_map.yaml` + PyYAML** | Editable without deploy; 50 aliases / 30+ slugs. | Hard-coded `ENTITY_MAP` in Python: requires deploy to extend. |
| **Queue only on `inserted`** | Merges do not re-scan peers. | Queue on every persist: duplicate noise. |
| **Retain `0006` URL unique index** | Legacy rows and non-dedup paths; new rows still have unique URLs per source. | Drop URL index: breaks existing assumptions. |

⚠️ **Do not revert event detection to REST-only persist** without providing equivalent `dedup_key` upsert — scorer and editorial queue will double-count wire copies.

⚠️ **Do not narrow `headline_hash` to RBI/REGULATORY only** without PO approval — plan and acceptance criteria require all categories.

⚠️ **Do not auto-merge cross-category collisions** — `dedup_review_queue` exists precisely to keep categories separate until a human decides.

⚠️ **Cron job must have `SUPABASE_DB_URL`** — Render `finnwise-event-detection` service; `SUPABASE_URL` + service role alone is insufficient for this path.

**Assumptions**

- Editorial UI for `force_editorial_review` and review queue is **later** (P3-S1e digest / admin).
- Full `recompute_score(events.id)` from PRD2 ships in **P3-S1g**, replacing interim SQL blend.
- Existing production `events` without `dedup_key` remain until naturally replaced or a future backfill story runs.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S0** (`dedup_key` column, index `idx_events_dedup_key`); **P1-S6** (`event_detection` job, adapters, `0006` URL dedupe). |
| **Parallel** | P3-S1d (NewsAPI scheduler), P3-S1e (watchlist + Sunday digest for `dedup_review_queue`). |
| **Downstream — immediate** | **P3-S1f** market facts freshness; **P3-T2** pipeline test gate. |
| **Downstream — intelligence** | **P3-S1g** confidence scorer + gate (requires post-dedup `source_count`); **P3-S1h** explainability UI. |

**Shared components touched**

- `public.events` (columns + upsert logic)
- `public.dedup_review_queue` (new)
- `app/jobs/event_detection.py`
- `app/services/event_dedup.py` (new)
- `app/services/event_persistence.py` (retained for reads/admin; not default ingest)
- `app/config/entity_map.yaml` (new)

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Idempotent ingest merge** via partial unique index on `dedup_key` (`WHERE dedup_key IS NOT NULL`).
- **Config-driven entity normalisation** (YAML loaded once, `@lru_cache`).
- **Separation of merge key vs collision fingerprint** (category in merge key only).

**Database schema (summary)**

| Object | Change |
|--------|--------|
| `events` | `source_count`, `sources` (jsonb), `force_editorial_review`, `collision_fingerprint`; check `source_count >= 1`. |
| `dedup_review_queue` | New: `event_ids uuid[]`, `reason`, `status` (`pending` \| `merged` \| `dismissed`). |
| `events.dedup_key` | Column from **0021**; used by upsert in S1c. |

**API contracts**

- **No new or modified HTTP routes** in P3-S1c.
- Ingest is internal: cron → `run_event_detection` → `persist_deduped_event`.

**UI/UX**

- None in this story. Review queue surfacing planned in **P3-S1e**.

**Libraries / tools**

| Library | Purpose |
|---------|---------|
| `pyyaml>=6.0.2` | Load `entity_map.yaml` |
| `psycopg` (existing) | Upsert + review queue inserts |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0023_dedup_key_review_queue.sql` | `backend/db/migrations/0023_dedup_key_review_queue.sql` | Merge columns, review queue table, indexes |
| `event_dedup.py` | `backend/app/services/event_dedup.py` | Key computation, upsert, cross-category queue |
| `entity_map.yaml` | `backend/app/config/entity_map.yaml` | Entity alias → slug map (30+ entities) |
| `test_event_dedup.py` | `backend/tests/test_event_dedup.py` | Key logic, merge, guardrail tests |
| `test_dedup_review_queue.py` | `backend/tests/test_dedup_review_queue.py` | Cross-category queue + no auto-merge |
| `test_dedup_migration_sql.py` | `backend/tests/test_dedup_migration_sql.py` | Static migration contract (CI without DB) |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `migrate.py` | `backend/app/db/migrate.py` | Registered `0023_dedup_key_review_queue.sql` |
| `event_detection.py` | `backend/app/jobs/event_detection.py` | Default `persist` → `persist_deduped_event`; passes `raw` into persist |
| `pyproject.toml` | `backend/pyproject.toml` | Added `pyyaml` dependency |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S1c AC + tasks **3.0**–**3.6** marked complete |

**Not modified (intentionally)**

| File | Note |
|------|------|
| `event_persistence.py` | Still used for PostgREST **reads** (`fetch_events_filtered`); ingest default moved to dedup |
| `0006_events_dedupe_newsapi_quota.sql` | `(event_source, canonical_url)` unique index remains |

---

### A8. TESTS EXECUTED

| Test file | Test function | Status | What it verifies |
|-----------|---------------|--------|------------------|
| `test_dedup_migration_sql.py` | `test_dedup_migration_adds_merge_columns` | **Pass** | SQL contains `source_count`, `sources`, `force_editorial_review`, `collision_fingerprint` |
| `test_dedup_migration_sql.py` | `test_dedup_migration_creates_review_queue` | **Pass** | `dedup_review_queue` DDL with `event_ids`, `status` |
| `test_dedup_migration_sql.py` | `test_dedup_migration_source_count_guardrail_comment` | **Pass** | Documents `source_count > 5` guardrail in migration comments |
| `test_event_dedup.py` | `test_entity_map_has_at_least_thirty_entries` | **Pass** | YAML map ≥ 30 canonical slugs |
| `test_event_dedup.py` | `test_headline_hash_is_normalised_first_100_chars` | **Pass** | Lowercase, whitespace collapse, punctuation strip, cap 100 |
| `test_event_dedup.py` | `test_same_wire_across_outlets_shares_dedup_key` | **Pass** | Same headline → same key (body text may differ) |
| `test_event_dedup.py` | `test_different_headlines_same_entity_do_not_merge` | **Pass** | Repo vs CRR headlines → different keys |
| `test_event_dedup.py` | `test_headline_hash_in_key_for_all_categories` | **Pass** | All six `event_category` values differ when headline differs |
| `test_event_dedup.py` | `test_normalise_entity_resolves_rbi_alias` | **Pass** | `RBI` / `Reserve Bank of India` → `rbi` |
| `test_event_dedup.py` | `test_recompute_confidence_raw_increases_with_source_count` | **Pass** | Interim raw score rises with `source_count` |
| `test_event_dedup.py` | `test_collision_fingerprint_ignores_category` | **Pass** | Fingerprint stable for same headline/window |
| `test_event_dedup.py` | `test_persist_deduped_event_merges_same_story` | **Pass** (integration) | Second ingest `duplicate`; `source_count=2`, two `sources` |
| `test_event_dedup.py` | `test_source_count_above_five_sets_force_editorial_review` | **Pass** (integration) | Six merges → `force_editorial_review=true` |
| `test_dedup_review_queue.py` | `test_cross_category_collision_queues_review` | **Pass** (integration) | RBI_POLICY + REGULATORY → pending queue row with 2 IDs |
| `test_dedup_review_queue.py` | `test_cross_category_events_are_not_auto_merged` | **Pass** (integration) | Two categories → two `events` rows |
| `test_event_detection_idempotent.py` | `test_second_detection_run_is_duplicate` | **Pass** | Mock persist API accepts `raw`; job still idempotent with inject |

**Commands used**

```bash
python -m ruff check backend
python -m pytest backend/tests/test_event_dedup.py backend/tests/test_dedup_review_queue.py backend/tests/test_dedup_migration_sql.py backend/tests/test_event_detection_idempotent.py -q
```

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**`events` (altered in `0023`)**

| Column | Type | Notes |
|--------|------|--------|
| `source_count` | `integer NOT NULL DEFAULT 1` | Incremented on dedup merge |
| `sources` | `jsonb NOT NULL DEFAULT '[]'` | Array of `{event_source, canonical_url, title, retrieved_at}` |
| `force_editorial_review` | `boolean NOT NULL DEFAULT false` | Set when `source_count > 5` after merge |
| `collision_fingerprint` | `text` | Category-agnostic; indexed partially |

**`dedup_review_queue` (new)**

| Column | Type | Notes |
|--------|------|--------|
| `id` | `uuid PK` | |
| `event_ids` | `uuid[] NOT NULL` | Pair (or set) under review |
| `reason` | `text NOT NULL` | e.g. `cross_category_same_window` |
| `status` | `text` | `pending` \| `merged` \| `dismissed` |
| `created_at` | `timestamptz` | Default `now()` |

**From `0021` (P3-S0, used by S1c)**

| Column | Notes |
|--------|--------|
| `dedup_key` | `text`; unique index `idx_events_dedup_key` where not null |

**Migration sequencing:** Apply after `0022`. Registered in `backend/app/db/migrate.py` → `python scripts/apply_migrations.py`.

**No seed data** in S1c (runtime ingest only).

**Verification SQL (after cron or manual job)**

```sql
SELECT dedup_key, source_count, jsonb_array_length(sources) AS srcs,
       force_editorial_review, category::text
FROM public.events
WHERE dedup_key IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;

SELECT id, event_ids, reason, status, created_at
FROM public.dedup_review_queue
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 10;
```

---

### B2. API / INTEGRATION CONTRACTS

**No new HTTP endpoints.**

**Internal persist contract (`persist_deduped_event`)**

| Parameter | Role |
|-----------|------|
| `raw` | `RawEvent` (title, url, published_at, excerpt) |
| `title`, `category`, `event_source`, `canonical_url`, `confidence_score` | Same as former REST persist |
| `detected_at` | Optional override for window floor |

**Returns:** `inserted` \| `duplicate` \| `skipped_no_config` \| `error`

**Auth:** Service DB connection (postgres pool); not exposed to clients.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Dedup key**

```text
entity     = longest_match(entity_map, headline + body) or "unknown"
window     = floor_utc_4h(detected_at)
headline_h = normalise(headline)[:100]   # lower, collapse space, strip punctuation
dedup_key  = sha256(category | entity | window.isoformat() | headline_h)
```

**Collision fingerprint (cross-category only)**

```text
collision_fingerprint = sha256(entity | window.isoformat() | headline_h)
```

**Upsert on conflict**

```text
source_count       += 1
sources            ||= new_source_json
confidence_raw     = 0.35 * min(source_count/3, 1) + 0.65 * max(confidence_score)/100  (in SQL)
confidence_score   = GREATEST(existing, new)
force_editorial_review = (source_count + 1) > 5
```

**Cross-category queue (on new insert only)**

```text
IF EXISTS event WHERE collision_fingerprint = new.fp AND category <> new.category
  INSERT dedup_review_queue (event_ids, reason='cross_category_same_window')
  UNLESS pending row already exists for same event_ids set
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Detail |
|------|--------|
| **No backfill** | Existing `events` rows lack `dedup_key` until re-ingested or a future migration job runs. |
| **Interim `confidence_raw`** | Not the P3-S1g four-weight scorer; replace in S1g without changing dedup key. |
| **Dual dedupe indexes** | `dedup_key` (semantic) and `(event_source, canonical_url)` (legacy) both apply to new rows with URLs. |
| **Sunday digest UI** | **P3-S1e** — queue populated but not yet in editorial email/UI. |
| **`persist_draft_event` still in repo** | Admin/legacy paths; default cron path is dedup only. |
| **Entity `unknown`** | Headlines with no map match bucket together — monitor false merges via review queue. |
| **Wire same headline** | Outlets with identical headline text merge (intended); outlet suffix in title prevents merge (also intended). |

---

### B5. TESTING NOTES

| Type | Coverage |
|------|----------|
| **Automated — static** | `test_dedup_migration_sql.py` (no DB) |
| **Automated — unit** | Key, entity, headline, confidence helper |
| **Automated — integration** | Merge, guardrail, review queue (needs `SUPABASE_DB_URL`) |
| **Automated — job** | `test_event_detection_idempotent` with mock persist (signature only) |
| **Manual** | `apply_migrations` → deploy cron → `python -m app.jobs.event_detection` → SQL checks |
| **Gap** | No end-to-end cron test against live NewsAPI/RBI adapters with dedup |
| **Gap** | No backfill migration test |
| **Gap** | No test that `force_editorial_review` surfaces in `/admin/queue` (future UI) |

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required | Notes |
|----------|----------|--------|
| `SUPABASE_DB_URL` | **Yes** for dedup ingest | Session pooler on Render; cron service `finnwise-event-detection` |
| `NEWSAPI_KEY` | For NewsAPI adapter | Unchanged from P1-S6 |
| `SUPABASE_URL` + service role | Not sufficient alone | REST persist no longer default for cron |

**No new feature flags.**

**Deployment sequencing (per environment)**

1. Deploy backend containing `event_dedup.py`, updated `event_detection.py`, and `pyyaml` in `pyproject.toml`.  
2. `python scripts/apply_migrations.py` (applies through `0023`).  
3. Confirm Render cron `finnwise-event-detection` has `SUPABASE_DB_URL`.  
4. Optional smoke: `cd backend && python -m app.jobs.event_detection`  
5. Verify SQL (see B1).

Migrations are **not** run automatically on Render web service startup.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read PRD2 G-03 and Phase 3 plan PO registry (`headline_hash` all categories).  
2. Read `event_dedup.py` `UPSERT_SQL` before changing merge semantics.  
3. Any change to dedup key components requires re-evaluating false merge / false split rates and review queue volume.

**Common mistakes**

- Deploying code without migration `0023` → upsert references missing columns.  
- Cron without `SUPABASE_DB_URL` → silent `skipped_no_config`, no new events.  
- Expecting cross-category rows to merge — they must not.  
- Editing `entity_map.yaml` without restarting process (cache: `@lru_cache` on `load_entity_map` — call `clear_entity_map_cache()` in tests or restart workers).  
- Removing `headline_hash` from key for “simplicity” without PO sign-off.

**Where to look**

| Concern | Location |
|---------|----------|
| Dedup logic | `backend/app/services/event_dedup.py` |
| Entity aliases | `backend/app/config/entity_map.yaml` |
| Cron entry | `backend/app/jobs/event_detection.py` |
| Migration | `backend/db/migrations/0023_dedup_key_review_queue.sql` |
| Legacy REST persist | `backend/app/services/event_persistence.py` |
| Render cron | `render.yaml` → `finnwise-event-detection` |
| Plan / AC | `docs/plans/finnwise-phase3-implementation-tasks.md` § P3-S1c |

**Next stories**

- **P3-S1f** — market facts freshness (depends on S1c).  
- **P3-T2** — data pipeline test gate.  
- **P3-S1g** — replace interim `confidence_raw` with full scorer.  
- **P3-S1e** — Sunday digest lists `dedup_review_queue` (max 10).

**Context owner (role):** Platform/backend engineer owning Phase 3 data pipeline (Jordan per plan).

---

_End of document — P3-S1c v1.0_
