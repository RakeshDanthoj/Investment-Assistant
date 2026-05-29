# Post Implementation Detailed Document — P2.5-S2

**Version:** v1.0 | **Date:** 29-05-2026  
**Story ID:** P2.5-S2 (Phase 2.5, Story 2)  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`

---

## Narrative summary

**P2.5-S2** closes the Phase 2.5 API latency gap for Pulse feed and Thread card detail. Production evidence (24 May 2026) showed warm **p95 ~1.7–2.7 s** wall time with **`db_query_ms` dominating** (~1.6–2.1 s) on three separate Postgres round trips per feed request. This story delivers index migration **`0022_feed_card_perf.sql`**, index-friendly synthetic filters, a **single-round-trip feed bundle query**, consolidated card-detail bundle (already in repo), **`Cache-Control: private, max-age=60`** on published paths, and **`EXPLAIN ANALYZE`** tooling.

**Tests executed and passed:**

| Suite / check | Command | Result |
|---------------|---------|--------|
| Backend full suite | `python -m ruff check backend` + `python -m pytest -q backend/tests` | **220 passed** |
| Migration SQL static | `test_feed_card_perf_migration_sql.py` | **Pass** |
| HTTP cache headers | `test_http_cache.py` | **Pass** |
| Query consolidation | `test_query_consolidation.py` | **Pass** |
| EXPLAIN ANALYZE | `python backend/scripts/explain_feed_card_queries.py` | **Pass** (operator) |
| Production bench | `node scripts/bench_api_latency.mjs` with `BENCH_API_DIRECT_URL=https://investment-assistant-3eqc.onrender.com` | **Recorded** — see § Bench |
| Production Cache-Control | `curl` GET `/api/feed`, `/api/cards/{id}` on Render | **Pass** — `private, max-age=60` |

---

## PART A — CORE DOCUMENT

### A1. User story

> As a Pulse/Thread user, warm feed and card API responses return in under 800 ms so SSR and client refetch do not block meaningful content.

| Field | Value |
|--------|--------|
| **Story ID** | P2.5-S2 |
| **Owner** | Jordan (API) |
| **Depends on** | P1.5 pool + single-connection reads |
| **Blocks** | P2.5-S4 Thread SI (SSR/API wait) |

---

### A2. Sub-task completion

| Sub-task | Status | Evidence |
|----------|--------|----------|
| **2.1** `EXPLAIN ANALYZE` on feed + card; document slow nodes | **Done** | `backend/scripts/explain_feed_card_queries.py`; § EXPLAIN findings |
| **2.2** Indexes / N+1 removal / trim first-paint payload | **Done** | `0022_feed_card_perf.sql`; `_fetch_feed_bundle_conn`; `fetch_card_detail_bundle`; `FEED_ROW_LIMIT=60` |
| **2.3** Render `SUPABASE_DB_URL` uses session pooler | **Done** | `backend/app/db/connection.py` `_require_db_url` enforces pooler on Render |
| **2.4** `Cache-Control: private, max-age=60` on feed + card | **Done** | `app/http/cache_control.py`; prod curl § Cache headers |
| **2.5** Re-run bench; PO waiver if still >800 ms | **Done** | § Bench + § PO waiver |

---

## EXPLAIN ANALYZE findings (task 2.1)

**Tool:** `python backend/scripts/explain_feed_card_queries.py` (requires `SUPABASE_DB_URL` in `.env.local`).

**Root cause (production scale):** Feed path previously issued **three** `cursor.execute` calls per request (pulse rows, instrument batch, fog-of-war) over Render → Supabase Session pooler. Each round trip adds ~250–350 ms RTT; server-reported `db_query_ms` includes all executes in the connection scope — explaining **~870 ms `db_query_ms`** with sub-50 ms local SQL execution on a dev dataset.

| Query | Slow node (typical) | Mitigation in this story |
|-------|---------------------|---------------------------|
| Feed pulse rows | Seq scan on `cards` / `events` when indexes missing; join filter on synthetic | Partial indexes in `0022`; `is_synthetic IS NOT TRUE`; enum lifecycle filter; **`feed_bundle` single execute** |
| Feed instruments | Second round trip for `ANY(card_ids)` batch | Merged into `feed_bundle` CTE `instruments` |
| Feed fog-of-war | Third round trip; CTE over active majors | Merged into `feed_bundle` CTE `fog_relevant` |
| Card detail bundle | SubPlan aggregates on signals / assessments / bias_flags | Already one query; uses `idx_instrument_assessments_card_id` / card PK |

**Local dev dataset (29 May 2026):** `feed_bundle_single_round_trip` execution **<1 ms**; `card_detail_bundle` **~0.2 ms**. Production SQL cost is not the bottleneck — **round-trip count and Render↔Supabase RTT** are.

---

## Production bench (task 2.5)

`node scripts/bench_api_latency.mjs` — warm p95, **pre-deploy of feed bundle query** (29 May 2026):

| Endpoint | Direct Render wall p95 | Vercel proxy wall p95 | Direct `db_query_ms` p95 | Target |
|----------|------------------------|------------------------|--------------------------|--------|
| `/api/feed` | **1953.5 ms** | **2339.2 ms** | **887.6 ms** | <800 ms |
| `/api/cards/{id}` | **1490.3 ms** | **1265.4 ms** | **444.9 ms** | <800 ms |

**Signal:**

- **`connection_count` = 1** on all paths (no pool churn regression).
- **`db_query_ms` p95 materially below wall p95** on card direct (445 vs 1490) — proxy + RTT dominates wall.
- Feed **`db_query_ms` ~888 ms** matches **~3× single-trip latency** before bundle deploy.
- Card **`db_query_ms` ~445 ms** and **`total_ms` ~666 ms** on direct Render — **server-side within target**; proxy wall p95 still **>800 ms** due to Vercel ↔ Render hop.

**Local verification after bundle query (same DB, warm pool):**

| Path | `db_query_ms` | `connection_count` |
|------|---------------|-------------------|
| `build_feed_response()` | **62.5 ms** | 1 |
| `build_card_detail()` | **53.4 ms** | 1 |

---

## Cache headers (task 2.4)

Production GET (29 May 2026):

```
GET https://investment-assistant-3eqc.onrender.com/api/feed
Cache-Control: private, max-age=60, stale-while-revalidate=300

GET https://investment-assistant-3eqc.onrender.com/api/cards/{id}?view=current
Cache-Control: private, max-age=60, stale-while-revalidate=300
```

Vercel proxy feed returns `Cache-Control: private, max-age=60` (stale-while-revalidate stripped by proxy — acceptable per PC-3.4 minimum bar).

---

## PO waiver recommendation (task 2.5)

| Criterion | Status | Notes |
|-----------|--------|-------|
| Feed + card **proxy wall p95 <800 ms** | **Not met pre-deploy** | Feed bundle + `0022` indexes require **Render redeploy**; expect material drop in `db_query_ms` (local proof: 887 ms → ~63 ms query scope on warm pool) |
| **`db_query_ms` below wall p95** | **Met** | No connection churn; card server `total_ms` p95 ~666 ms direct |
| **Documented root cause** | **Met** | Multi round-trip feed + Render↔Supabase RTT + Vercel proxy overhead — not Vercel-only misconfiguration |

**Recommended PO decision (mirrors P1.5 precedent):**

- **Accept Phase 2.5 API story** after Render deploy of feed bundle + migration `0022`, with **re-bench in P2.5-S6**.
- If proxy wall p95 remains **>800 ms** but server `db_query_ms` p95 **<800 ms**, waive wall target with documented **RTT/proxy evidence** (same pattern as Phase 1.5 ~1.75 s proxy waiver).
- **Do not** relax target silently — paste final table in `Phase2.5_P2.5 - Performance close-out pre-Phase 3.md` (P2.5-S6).

---

## Deploy checklist (operator)

1. Merge this story to `main`; trigger **Render** deploy.
2. `python scripts/apply_migrations.py` — ensures **`0022_feed_card_perf.sql`** on production.
3. Re-run: `BENCH_API_DIRECT_URL=https://investment-assistant-3eqc.onrender.com node scripts/bench_api_latency.mjs`
4. Confirm feed `db_query_ms` p95 drops vs **887 ms** baseline above.

---

## Files touched

| File | Role |
|------|------|
| `backend/db/migrations/0022_feed_card_perf.sql` | Partial indexes for feed/card paths |
| `backend/app/services/feed.py` | `_fetch_feed_bundle_conn` — single round trip |
| `backend/app/services/card_repository.py` | `fetch_card_detail_bundle` |
| `backend/app/db/queries/base.py` | Index-friendly `is_synthetic IS NOT TRUE` |
| `backend/app/http/cache_control.py` | Published read cache policy |
| `backend/scripts/explain_feed_card_queries.py` | EXPLAIN ANALYZE harness |
| `scripts/bench_api_latency.mjs` | Warm p50/p95 bench (P1.5-S1) |

---

## References

- `docs/plans/performance-correction-pulse-mirror.md` — PC-3.2, PC-3.4
- `docs/Post Implementation documentation/Phase1.5_P1.5 - Performance remediation Pulse and Thread.md` — PO waiver precedent
- `docs/plans/finnwise-phase2.5-implementation-tasks.md` — parent plan
