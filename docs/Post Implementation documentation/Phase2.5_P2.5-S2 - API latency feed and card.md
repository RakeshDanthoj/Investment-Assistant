# Post Implementation Detailed Document — P2.5-S2

**Version:** v1.1 | **Date:** 29-05-2026  
**Story ID:** P2.5-S2 (Phase 2.5, Story 2)  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`

---

## Narrative style (read this first)

**P2-S15** and production benches (24 May 2026) showed Pulse feed and Thread card APIs missing the **warm p95 &lt;800 ms** bar: feed direct **`db_query_ms` ~1.6 s**, card ~2.1 s, with **`connection_count` already 1** (pooling from P1.5 was not the bottleneck). Analysis traced feed latency to **three separate Postgres round trips** per request (pulse rows → instrument batch → fog-of-war) over Render → Supabase Session pooler, plus large first-paint payload (100-row feed cap).

**P2.5-S2** is a **Backend** performance story. It adds migration **`0022_feed_card_perf.sql`** (partial indexes), collapses the feed into a **single SQL round trip** (`_fetch_feed_bundle_conn`), aligns synthetic filters with those indexes (`is_synthetic IS NOT TRUE`), keeps card detail on the existing **one-query bundle** (`fetch_card_detail_bundle`), verifies **`Cache-Control: private, max-age=60`** on published read paths, and ships **`explain_feed_card_queries.py`** for operator `EXPLAIN ANALYZE`. No frontend or Vercel changes are required for this story.

**Tests executed and passed:**

| Suite / check | Command or method | Result |
|---------------|-------------------|--------|
| Ruff lint | `python -m ruff check backend` | **Pass** |
| Backend full suite | `python -m pytest -q backend/tests` | **220 passed** |
| Feed/card perf migration SQL | `tests/test_feed_card_perf_migration_sql.py` | **Pass** |
| HTTP Cache-Control | `tests/test_http_cache.py` | **Pass** |
| Single-connection feed/card | `tests/test_query_consolidation.py` | **Pass** |
| Feed filtering / bundle mocks | `tests/test_feed_filtering.py` | **Pass** |
| EXPLAIN ANALYZE harness | `python backend/scripts/explain_feed_card_queries.py` | **Pass** (operator, requires `SUPABASE_DB_URL`) |
| Production migrations | `python scripts/apply_migrations.py` | **Pass** (operator) |
| Production Cache-Control | `curl` GET `/api/feed`, `/api/cards/{id}` on Render | **Pass** — `private, max-age=60` |
| Production timing (post-deploy) | `curl` GET `/api/feed` → `x-finnwise-timing` | **Pass** — `db_query_ms` **449 ms**, `total_ms` **668 ms** |
| Production bench | `node scripts/bench_api_latency.mjs` | **Recorded** — see § Production evidence |

**Three anchors:** (1) **`db_query_ms` ~880–900 ms on feed with `connection_count: 1`** means multi-**execute** round trips, not pool churn — fix is query shape + deploy, not more connections; (2) **migrations without Render deploy** leave the old 3-query Python path live; (3) **proxy wall p95** can stay **&gt;800 ms** when server `total_ms` is green — document for P2.5-S6 / PO waiver (P1.5 precedent).

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2.5-S2 |
| **Title** | API latency: feed + card p95 &lt;800 ms |
| **Category** | **Backend** (SQL, indexes, HTTP cache, bench tooling; no frontend) |
| **Owner (plan)** | Jordan (API) |

**What this story aimed to achieve (plain language)**

Pulse and Thread depend on `GET /api/feed` and `GET /api/cards/{id}` for SSR and client refetch. Users were waiting **1.5–2.5+ seconds** on warm production requests because the backend spent most of that time in the database layer across **multiple network round trips** to Supabase. This story reduces feed to **one** Postgres execute per request, adds indexes for feed sort/filter paths, trims first-paint payload (**60** cards, truncated insight text), and documents production evidence for Phase 2.5 exit (or a PO waiver on proxy wall time).

**How it fits into the overall application**

- **Upstream:** P1.5 connection pool, single-connection reads, `DbRequestTimer` / `x-finnwise-timing`, `scripts/bench_api_latency.mjs`.
- **Moved from:** P2-S15 §15.2 (feed + card warm p95 target).
- **Enables:** **P2.5-S4** Thread mobile SI (often tracks API wait); **P2.5-S6** final bench table and Phase 3 prerequisite.
- **Does not require:** Vercel redeploy (backend-only).

**Production URLs (baseline)**

| Layer | URL |
|-------|-----|
| Frontend | `https://investment-assistant-frontend.vercel.app` |
| API (Render) | `https://investment-assistant-3eqc.onrender.com` |

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **2.1** | `EXPLAIN ANALYZE` on feed + card paths; document slow nodes (`explain_feed_card_queries.py`). |
| **2.2** | Indexes (`0022`), N+1 removal (feed bundle + card bundle), payload trim (`FEED_ROW_LIMIT=60`, SQL `LEFT(insight…, 400)`). |
| **2.3** | Confirm Render uses Supabase **Session pooler** URI (`connection.py` guard). |
| **2.4** | Verify `Cache-Control: private, max-age=60` on published feed + card (PC-3.4). |
| **2.5** | Re-run bench; PO waiver memo if proxy wall p95 still &gt;800 ms after deploy. |

**Functional breakdown**

1. `GET /api/feed` → `build_feed_response()` → one `connection()` scope → optional session profile lookup → **`_fetch_feed_bundle_conn`** (pulse CTE + instruments JSON agg + fog CTE) → in-process `rerank` + `build_card_payload` per row.
2. `GET /api/cards/{id}` → `build_card_detail()` → **`fetch_card_detail_bundle`** (card + event + signals + instruments + bias_flags in one query for `view=current`).
3. Response includes **`x-finnwise-timing`** JSON: `db_connect_ms`, `db_query_ms`, `total_ms`, `connection_count`.
4. Published lifecycle states get **`Cache-Control: private, max-age=60, stale-while-revalidate=300`** via `cache_control_for_feed()` / `cache_control_for_card_detail()`.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Missing `SUPABASE_DB_URL` | **503** `db_unavailable` on feed/card routes. |
| Bare Supabase project ref (not full URI) | **503** with hint (settings validation). |
| Render + direct `db.*.supabase.co` host | **RuntimeError** at connection — must use pooler (see B6). |
| Invalid `horizon` query param on feed | **422** `invalid_horizon`. |
| Card not found (`view=current`) | **404** + `Cache-Control: no-store`. |
| Card draft (`view=current`) | **200** + `Cache-Control: no-store`. |
| Empty feed (no visible cards) | **200**, `cards: []`, fog flag still computed in SQL. |
| Synthetic events | Excluded via `e.is_synthetic IS NOT TRUE` (index-friendly). |

**Business rules enforced**

- Feed only returns cards in **visible** lifecycle states (`published` … `resolved`).
- Fog-of-war flag unchanged in meaning: ≥3 major active/signal_triggered cards and category overlap (now computed in SQL inside bundle).
- Personalisation token still applied **after** SQL fetch (`feed_ranker.rerank`).
- Card detail **original** view still uses track-record snapshot path (separate queries — not part of bundle hot path).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Single CTE bundle for feed** | Cuts Render↔Supabase round trips from 3→1; `db_query_ms` dropped ~50% on prod smoke (887→449 ms sample). | Keep 3 executes with indexes only: still ~3× RTT. |
| **`is_synthetic IS NOT TRUE`** | Matches partial indexes in `0022` (`WHERE is_synthetic IS NOT TRUE`). | `COALESCE(is_synthetic, FALSE) = FALSE`: prevents index use. |
| **Enum `lifecycle_state[]` filter** | Avoids `lifecycle_state::text` cast on indexed column. | Text cast + `ANY(%s::text[])`: planner-friendly indexes harder. |
| **`FEED_ROW_LIMIT = 60`** | Aligns with Pulse UI; reduces payload vs 100. | Raise limit without perf proof: regresses TTFB. |
| **PO waiver on proxy wall p95** | Server `total_ms` can be &lt;800 ms while Vercel proxy wall &gt;800 ms (RTT hop). | Relax budgets in CI without PO: rejected per plan. |
| **No Vercel deploy** | All changes are FastAPI + Postgres. | Proxy-only tuning: does not fix `db_query_ms`. |

⚠️ **Do not revert feed to three separate `execute()` calls** without measuring `db_query_ms` on Render — production evidence shows ~900 ms with one connection and three executes.

⚠️ **Do not change synthetic filter back to `COALESCE`** without updating migration partial index predicates — plans will diverge.

⚠️ **Do not treat migration-only apply as “story done”** — bundle code must be on the Render image (`_fetch_feed_bundle_conn` in `feed.py`).

**Assumptions**

- P1.5 pool and timing headers remain enabled on production Render.
- Bench card id `e708b82c-f7c7-45e7-a59b-6b66dac8927a` (or `BENCH_CARD_ID`) exists in production DB.
- Phase 2.5 strict gate is **proxy wall p95** unless PO waives with server timing evidence (P2.5-S6).

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1.5-S2** pool, **P1.5-S3** query consolidation pattern, **P1.5-S4** cache headers, **P1-S9** feed API, **P1-S10** card detail. |
| **Moved from** | **P2-S15** §15.2 feed + card p95 target. |
| **Related** | `performance-correction-pulse-mirror.md` — PC-3.2, PC-3.4. |
| **Enables** | **P2.5-S4** Thread SI; **P2.5-S6** evidence archive and Phase 3 prerequisite. |
| **Shared** | `public.cards`, `public.events`, `public.instrument_assessments`, `public.signals`, `public.card_bias_flags`, `DbRequestTimer`, `scripts/bench_api_latency.mjs`. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Service-layer SQL consolidation; no new microservices or caches. |
| **Schema** | Migration `0022` — partial indexes on cards (visible feed sort, fog lifecycle), events (not synthetic, category), instrument_assessments (card_id where version=1). |
| **API** | Unchanged routes: `GET /api/feed`, `GET /api/cards/{card_id}`; added timing + cache headers unchanged from P1.5. |
| **Auth** | Feed: optional `session_id` query param for profile; card: no auth change in this story. |
| **UI** | None. |
| **Tooling** | `explain_feed_card_queries.py`, existing `bench_api_latency.mjs`. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| 0022_feed_card_perf.sql | `backend/db/migrations/0022_feed_card_perf.sql` | Partial indexes for feed sort, fog scan, synthetic category, v1 instruments |
| explain_feed_card_queries.py | `backend/scripts/explain_feed_card_queries.py` | Operator `EXPLAIN (ANALYZE, BUFFERS)` for feed bundle + card detail |
| test_feed_card_perf_migration_sql.py | `backend/tests/test_feed_card_perf_migration_sql.py` | Static SQL assertions for migration `0022` (CI without live DB) |
| Phase2.5_P2.5-S2 - API latency feed and card.md | `docs/Post Implementation documentation/Phase2.5_P2.5-S2 - API latency feed and card.md` | This handover document |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| feed.py | `backend/app/services/feed.py` | `_fetch_feed_bundle_conn`; enum lifecycle filter; `build_feed_response` uses bundle |
| base.py | `backend/app/db/queries/base.py` | `SyntheticFilterMixin`: `IS NOT TRUE` for index alignment |
| migrate.py | `backend/app/db/migrate.py` | Registers `0022_feed_card_perf.sql` |
| test_feed_filtering.py | `backend/tests/test_feed_filtering.py` | Mocks updated for `_fetch_feed_bundle_conn` |
| test_query_consolidation.py | `backend/tests/test_query_consolidation.py` | Single-connection tests use bundle mock |
| finnwise-phase2.5-implementation-tasks.md | `docs/plans/finnwise-phase2.5-implementation-tasks.md` | P2.5-S2 tasks/acceptance marked; bench tables updated |

**Relied upon (not modified in P2.5-S2)**

| File Path | Role |
|-----------|------|
| `backend/app/services/card_repository.py` | `fetch_card_detail_bundle` — one-query card detail |
| `backend/app/services/card_detail.py` | Thread payload assembly |
| `backend/app/api/feed.py` | Feed route + timing + cache headers |
| `backend/app/api/cards_detail.py` | Card route + timing + cache headers |
| `backend/app/http/cache_control.py` | `PUBLISHED_READ_CACHE` policy |
| `backend/app/db/connection.py` | Pool + Render pooler enforcement |
| `scripts/bench_api_latency.mjs` | Warm p50/p95 production bench |

---

### A8. TESTS EXECUTED

| Test / check | Status | What it covers |
|--------------|--------|----------------|
| `test_feed_card_perf_migration_defines_expected_indexes` | **Passed** | All six index names present in `0022` SQL |
| `test_feed_card_perf_migration_avoids_non_immutable_predicates` | **Passed** | No `COALESCE(` / `lifecycle_state::text` in migration |
| `test_feed_sets_published_read_cache_control` | **Passed** | Feed returns `private, max-age=60, stale-while-revalidate=300` |
| `test_card_detail_current_published_is_cacheable` | **Passed** | Published card cacheable |
| `test_card_detail_current_draft_is_no_store` | **Passed** | Draft not cached |
| `test_build_feed_uses_single_connection` | **Passed** | One pool checkout per feed build |
| `test_fetch_card_detail_bundle_uses_single_connection` | **Passed** | One execute for card bundle |
| `test_build_feed_splits_category_param` | **Passed** | Category CSV → list passed to bundle |
| `test_build_feed_loads_session_profile` | **Passed** | Session profile join before bundle |
| `test_build_feed_live_connection_count` | **Passed** (integration, skips if no DB) | Live DB: `connection_count == 1` |
| `test_build_card_detail_current_live_connection_count` | **Passed** (integration, skips if no DB) | Live card path: one connection |

**Backend commands**

```text
python -m ruff check backend
python -m pytest -q backend/tests
```

→ **All checks passed; 220 tests passed** (29-05-2026).

**Operator commands**

```text
python scripts/apply_migrations.py
python backend/scripts/explain_feed_card_queries.py
BENCH_API_DIRECT_URL=https://investment-assistant-3eqc.onrender.com node scripts/bench_api_latency.mjs
```

**Frontend automated tests**

None in P2.5-S2 (backend-only story).

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Migration `0022_feed_card_perf.sql`** (idempotent `CREATE INDEX IF NOT EXISTS`):

| Index | Table | Purpose |
|-------|-------|---------|
| `idx_cards_visible_feed_created` | `cards` | Partial: visible lifecycles, `created_at DESC` |
| `idx_cards_lifecycle_created` | `cards` | `(lifecycle_state, created_at DESC)` |
| `idx_cards_fog_lifecycle` | `cards` | Partial: `active`, `signal_triggered` + `event_id` |
| `idx_events_not_synthetic_category` | `events` | Category filter where not synthetic |
| `idx_events_major_not_synthetic` | `events` | Confidence ≥70 majors for fog scan |
| `idx_instrument_assessments_card_v1` | `instrument_assessments` | `card_id` where `version = 1` |

**No new tables or columns.** Apply via:

```text
python scripts/apply_migrations.py
```

**Confirm applied:**

```sql
SELECT filename FROM public.schema_migrations
WHERE filename = '0022_feed_card_perf.sql';
```

---

### B2. API / INTEGRATION CONTRACTS

| Method | Route | Auth | Cache (published) | Timing header |
|--------|-------|------|-------------------|---------------|
| GET | `/api/feed` | None (optional `session_id`) | `private, max-age=60, stale-while-revalidate=300` | `x-finnwise-timing` |
| GET | `/api/cards/{card_id}?view=current` | None | Lifecycle-dependent; published → max-age 60 | `x-finnwise-timing` |
| GET | `/api/cards/{card_id}?view=original` | None | Always cacheable (snapshot) | `x-finnwise-timing` |

**Example timing header (post-deploy, operator curl 29-05-2026):**

```http
GET https://investment-assistant-3eqc.onrender.com/api/feed

x-finnwise-timing: {"db_connect_ms":0.03,"db_query_ms":449.46,"total_ms":668.05,"connection_count":1}
Cache-Control: private, max-age=60, stale-while-revalidate=300
```

**Feed query params (unchanged):** `category`, `horizon`, `session_id`, `personalisation_token`.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

```
GET /api/feed
  → validate horizon enum (if present)
  → DbRequestTimer start
  → connection() once
      → optional session_profiles row
      → _fetch_feed_bundle_conn
          → CTE pulse_rows (visible cards + non-synthetic events + sort/limit 60)
          → CTE instruments (json_agg per card, version=1)
          → CTE fog_relevant + fog boolean
      → rerank(cards, personalisation_token)
      → build_card_payload per row
  → JSONResponse + cache_control_for_feed() + timing headers

GET /api/cards/{id}?view=current
  → fetch_card_detail_bundle (single SELECT + json subqueries)
  → build_card_detail → bias_audit from prefetched rows
  → cache by lifecycle_state
```

**Fog-of-war (unchanged semantics):** true when ≥3 cards in `active`/`signal_triggered` with event `confidence_score >= 70` and max per-category count ≥2.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Notes |
|------------|-------|
| **Proxy wall p95 &gt;800 ms** | May persist when server `total_ms` &lt;800 ms — Vercel ↔ Render RTT; PO waiver path in P2.5-S6. |
| **Bench p95 vs single curl** | One warm curl showed `db_query_ms` 449 ms; full bench p95 may still spike on cold Render instances — re-bench for S6. |
| **Large production datasets** | Dev EXPLAIN shows seq scans on tiny data; prod may need `ANALYZE` after `0022` if planner lags. |
| **Card original view** | Still multi-query path — not optimized in this story (cold path). |
| **Mirror dashboard API** | PC-3.3 optional combined endpoint — out of scope for P2.5-S2. |

---

### B5. TESTING NOTES

| Area | Automated | Manual / operator |
|------|-----------|-------------------|
| Migration SQL shape | `test_feed_card_perf_migration_sql.py` | — |
| Cache headers | `test_http_cache.py` | `curl` production headers |
| Connection count | `test_query_consolidation.py` | `bench_api_latency.mjs` → `connection_count` min/max |
| Query plans | — | `explain_feed_card_queries.py` |
| Production latency | — | `bench_api_latency.mjs`, `x-finnwise-timing` curl |

**Failure triage**

| Symptom | Likely cause |
|---------|----------------|
| Feed `db_query_ms` still ~900 ms | Old 3-query code on Render — redeploy backend |
| Feed `db_query_ms` ~450 ms but wall &gt;1.5 s | Render cold start or network — not SQL |
| Indexes not used | `0022` not applied; run `apply_migrations.py` |
| **503** on Render | `SUPABASE_DB_URL` missing or direct host instead of pooler |
| Proxy slow, direct fast | Expected — document for waiver |

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Where | Purpose |
|----------|-------|---------|
| `SUPABASE_DB_URL` | Render / `.env.local` | Must be **Session pooler** URI on Render (`…pooler.supabase.com:5432`) |
| `BENCH_API_DIRECT_URL` | Bench script | Render origin (e.g. `https://investment-assistant-3eqc.onrender.com`) |
| `BENCH_VERCEL_URL` | Bench script | Default production frontend |
| `BENCH_CARD_ID` | Bench script | Card UUID for card detail bench |
| `RENDER` / `RENDER_SERVICE_ID` | Render runtime | Triggers pooler URL enforcement in `connection.py` |

**Deployment sequencing**

1. Merge P2.5-S2 backend to `main`.
2. **Render deploy** (required for feed bundle code).
3. `python scripts/apply_migrations.py` on production DB (`0022`).
4. Smoke: `curl` feed → confirm `db_query_ms` **&lt;~500 ms** warm (not ~900 ms).
5. `node scripts/bench_api_latency.mjs` — paste table into **P2.5-S6** close-out.
6. **No Vercel deploy** required for this story.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing feed or card read paths**

1. Read P1.5 handover: `docs/Post Implementation documentation/Phase1.5_P1.5-S1 - Baseline instrumentation and latency proof.md`.
2. Run `bench_api_latency.mjs` before and after changes; compare **`db_query_ms`**, not wall time alone.
3. Use `explain_feed_card_queries.py` after SQL edits.

**Common mistakes**

- Applying migration without Render deploy → indexes exist but **3-query feed** still live.
- Reverting `IS NOT TRUE` synthetic filter → partial indexes on `events` less effective.
- Optimizing Vercel only when `x-finnwise-timing` shows high `db_query_ms`.
- Using `lifecycle_state::text` in feed WHERE → avoids enum-friendly plans.

**Where to find code**

| Concern | Path |
|---------|------|
| Feed bundle SQL | `backend/app/services/feed.py` → `_fetch_feed_bundle_conn` |
| Card bundle SQL | `backend/app/services/card_repository.py` → `fetch_card_detail_bundle` |
| Synthetic filter | `backend/app/db/queries/base.py` |
| Cache policy | `backend/app/http/cache_control.py` |
| Feed route | `backend/app/api/feed.py` |
| Card route | `backend/app/api/cards_detail.py` |
| Pool / pooler guard | `backend/app/db/connection.py` |
| EXPLAIN script | `backend/scripts/explain_feed_card_queries.py` |
| Production bench | `scripts/bench_api_latency.mjs` |

**Contact by role**

| Role | Responsibility |
|------|----------------|
| Jordan | Feed/card SQL, API timing, Render deploy |
| Riley | Bench archive, P2.5-S6 evidence, CI |
| Sam | Pulse/Thread SSR if API wait still visible after backend green |

---

## Production evidence (operator — 29-05-2026)

### Baseline (pre–feed bundle deploy, 24–29 May 2026)

| Endpoint | Direct wall p95 | Proxy wall p95 | Direct `db_query_ms` p95 |
|----------|-----------------|----------------|---------------------------|
| `/api/feed` | 1953 ms → 1434 ms | 2339 ms → 2356 ms | **887–902 ms** |
| `/api/cards/{id}` | 1490 ms → 1132 ms | 1265 ms → 1177 ms | **443–445 ms** |

### Post-deploy smoke (single warm request)

```http
GET https://investment-assistant-3eqc.onrender.com/api/feed
x-finnwise-timing: db_query_ms=449.46, total_ms=668.05, connection_count=1
```

**Interpretation:** Feed bundle deploy **confirmed** (~50% drop in `db_query_ms` vs ~900 ms). Server `total_ms` **under 800 ms** on this sample. Full **p95** table for Phase 2.5 sign-off belongs in **P2.5-S6** (re-run bench after stable Render warm-up).

### PO / exit criteria status (P2.5-S2)

| Criterion | Status |
|-----------|--------|
| Tasks 2.1–2.5 complete in repo | **Yes** |
| `connection_count` = 1 | **Yes** |
| `db_query_ms` below wall p95 | **Yes** (card; feed after deploy) |
| Proxy wall p95 &lt;800 ms | **PO waiver** — feed **1298 ms**, card **1350 ms** (30 May 2026) |
| Final table in Phase 2.5 close-out | **Done** — [P2.5-S6 close-out](./Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md) |

---

## Manual verification checklist (operator)

### 1. Migrations

```text
python scripts/apply_migrations.py
```

### 2. Render deploy

Confirm latest `main` is live on `investment-assistant-3eqc.onrender.com` (feed bundle in `feed.py`).

### 3. Timing smoke

```text
curl.exe -s -D - -o NUL "https://investment-assistant-3eqc.onrender.com/api/feed" | findstr /i "x-finnwise-timing Cache-Control"
```

Expect: `db_query_ms` typically **&lt;500 ms** warm (not ~900 ms); `Cache-Control: private, max-age=60`.

### 4. Full bench (for P2.5-S6)

```text
$env:BENCH_API_DIRECT_URL="https://investment-assistant-3eqc.onrender.com"
node scripts/bench_api_latency.mjs
```

---

## Summary: what you need to do manually

| Step | Required? | Frequency |
|------|-----------|-----------|
| Merge to `main` + **Render deploy** | **Yes** | Per release with feed changes |
| `apply_migrations.py` (`0022`) | **Yes** | Once per DB env |
| `curl` / bench timing smoke | **Yes** | After deploy |
| Vercel deploy | **No** | — |
| PO sign-off / waiver | **P2.5-S6** | Phase 2.5 close-out |

---

## References

| Doc / script | Role |
|--------------|------|
| `docs/plans/finnwise-phase2.5-implementation-tasks.md` | P2.5-S2 tasks and acceptance |
| `docs/plans/performance-correction-pulse-mirror.md` | PC-3.2, PC-3.4 |
| `docs/Post Implementation documentation/Phase1.5_P1.5 - Performance remediation Pulse and Thread.md` | PO waiver precedent |
| `scripts/bench_api_latency.mjs` | Warm p50/p95 bench |
| `docs/plans/cross-phase-performance-standards.md` | Mandatory perf practices |
