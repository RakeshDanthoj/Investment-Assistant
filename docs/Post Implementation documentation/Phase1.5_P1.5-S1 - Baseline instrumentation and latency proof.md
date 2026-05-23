# Post Implementation Detailed Document — P1.5-S1

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P1.5-S1 (Phase 1.5, Story 1)  
**Reference plan:** `docs/plans/finnwise-phase1.5-implementation-tasks.md`

---

## Narrative style

Production Lighthouse traces (May 2026) showed **Pulse** and **Thread** delivering meaningful content at **~9 seconds** on mobile, even though HTML arrived in tens of milliseconds. The bottleneck was not the React shell—it was a **client-fetch-after-hydration waterfall** combined with **~8 second API latency** through the Vercel `/backend` proxy to Render. Before changing architecture (connection pooling, query consolidation, SSR), the team needed **measured proof** of where time was spent: TCP/TLS connect vs SQL execution vs proxy hop.

**P1.5-S1** adds that measurement layer without changing product behaviour. Every warm **`GET /api/feed`** and **`GET /api/cards/{id}`** response now exposes **`Server-Timing`** and **`X-FinnWise-Timing`** headers with **`db_connect_ms`**, **`db_query_ms`**, **`total_ms`**, and **`connection_count`**. The shared **`connection()`** context manager records connect and query durations into a request-scoped accumulator when a route wraps work in **`DbRequestTimer`**. **`GET /health/db`** returns the same breakdown in JSON for quick ops checks. A repo script, **`scripts/bench_api_latency.mjs`**, runs five warm iterations against Render direct and the Vercel proxy and reports wall-clock and server-timing p50/p95.

The first baseline run (local backend, direct Supabase `:5432`, **no pool**) validated the hypothesis from the plan: **`db_connect_ms` dominates `db_query_ms`**, and each request opens **3 connections (feed)** or **4 (card detail)**. Proxy paths on production still show multi-second wall times until this backend ships and subsequent stories (S2 pool, S3 consolidation) land. This story is **diagnostics only**—no MMJ, SEBI, bias-flag, or track-record logic changed.

If you only remember **three anchors**: (1) **measure before optimizing**—timing headers prove connect churn; (2) **`DbRequestTimer` + `connection()` hooks** are the single instrumentation path; (3) **re-run `bench_api_latency.mjs` after every Phase 1.5 deploy** to compare p50/p95.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1.5-S1 |
| **Title** | Baseline instrumentation and latency proof |
| **Category** | **Backend** (API diagnostics, ops scripts, tests; no frontend changes) |

**What this story aimed to achieve (plain language)**

Give the platform owner **evidence** of where ~8s API latency comes from—database connect time, query time, or proxy overhead—so Phase 1.5 fixes target the **validated branch** instead of speculative changes. Add response headers and a health probe breakdown, plus a repeatable bench script and documentation, **before** connection pooling and query consolidation work begins.

**How it fits into the overall application**

Phase 1.5 sits between shipped Phase 1 (Pulse + Thread) and Phase 2 engagement work. **P1.5-S1 is the mandatory first story** in that phase: it establishes the measurement baseline referenced by **P1.5-S2** (pool), **P1.5-S3** (single-connection queries), **P1.5-S9** (Lighthouse CI), and **P1.5-S10** (production sign-off). Without S1 numbers, later stories cannot prove p95 improvements.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **1.5.1.1** | Per-route timing on **`GET /api/feed`** and **`GET /api/cards/{id}`** via **`DbRequestTimer`** wrapping service calls; headers attached on success (404 on card detail includes timing headers). |
| **1.5.1.2** | **`GET /health/db`** extended with **`connect_ms`**, **`query_ms`**, **`total_ms`** (plus existing **`cards`** count). |
| **1.5.1.3** | **`scripts/bench_api_latency.mjs`**: 1 discarded warmup + 5 measured iterations; feed + card detail × direct + Vercel proxy; p50/p95 for wall and server timing. |
| **1.5.1.4** | **`scripts/README.md`**: bench prerequisites, env vars, local vs production run steps, baseline table. |
| **1.5.1.5** | Baseline captured (2026-05-23): connect-dominated latency, 3–4 connections per request; proxy p95 ~6.5–8.6s pre-S1 deploy on production. |

**Functional breakdown**

- **`DbRequestTimer`** (context manager): resets a **`ContextVar`**-backed **`DbTimingAccumulator`**, sets it for the request scope, and on exit produces a snapshot with rounded millisecond fields.
- **`connection()`** hooks: on each enter/exit, if an accumulator is active, adds **`psycopg.connect()`** duration to **`db_connect_ms`** and time while the connection is held to **`db_query_ms`**; increments **`connection_count`** per open.
- **Route handlers**: wrap **`build_feed_response`** / **`build_card_detail`** in **`DbRequestTimer`**, return **`json_response_with_timing()`** which uses **`jsonable_encoder`** so datetime/UUID fields serialize correctly (FastAPI’s default dict return previously handled this implicitly).
- **Bench script**: reads repo-root **`.env.local`** when present; requires explicit **`BENCH_API_DIRECT_URL`** for loopback; compares four URLs (feed/card × direct/proxy).

**Edge cases, validations, and error handling**

- **503 / 422 on feed**: unchanged behaviour; timing headers are **not** attached (timer scope ends before **`HTTPException`** for validation; DB errors raise before response build).
- **404 card detail**: **`HTTPException`** includes **`timing_headers`** so missing cards still expose how expensive the lookup was.
- **Bench script**: fails fast if direct URL missing or loopback used without **`BENCH_API_DIRECT_URL`** / **`BENCH_ALLOW_LOOPBACK=1`**; warmup must return OK or entire target aborts.
- **`/health/db` unconfigured**: still returns error JSON without timing fields (no DB call attempted).

**Business rules enforced**

- **No functional change** to feed filters, Fog of War, card ICE payload, bias audit, or track-record paths—JSON response bodies unchanged.
- Instrumentation is **opt-in per route** via **`DbRequestTimer`**; other routes do not emit timing headers unless wrapped similarly.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Hook `connection()` for DB metrics** | Feed and card detail already use multiple **`with connection()`** blocks in services; one hook captures all opens without refactoring services in S1. | **Per-route manual timing only**: would miss nested service calls and under-count connections. |
| **`ContextVar` accumulator** | Safe under FastAPI thread pool workers; scoped to one request when **`DbRequestTimer`** is active. | **Global mutable counters**: race conditions under concurrency. |
| **Dual headers: `Server-Timing` + `X-FinnWise-Timing`** | Standard header for browser devtools; JSON header for scripts and CI parsing. | **`Server-Timing` only**: harder to parse in Node bench without a parser library. |
| **`jsonable_encoder` + `JSONResponse`** | Explicit response required to set headers; encoder preserves FastAPI serialisation behaviour for datetimes. | **Return dict and middleware**: middleware would not know which routes to measure without path matching duplication. |
| **Bench: 1 warmup + 5 samples** | Matches plan acceptance criteria; reduces cold-start noise on free-tier Render. | **Single request**: conflates cold start with steady state. |
| **Include `connection_count` in JSON header** | Directly supports S3 acceptance (“one connection per request” verification). | **Omit count**: would require log diving to count connects. |

**Assumptions**

- **`db_query_ms`** includes all time the connection is open (queries + Python processing between queries in the same **`with connection()`** block)—acceptable for S1 “where does time go” triage; not a pure SQL profiler.
- Production Render URL is supplied at bench time via env (not committed to repo).

**⚠️ Critical — do not reverse lightly**

- **Do not remove timing hooks from `connection()` without replacing equivalent measurement**—S2/S3 acceptance criteria depend on **`db_connect_ms`** dropping on warm requests.
- **Do not return raw dicts from feed/card routes again** without ensuring headers and **`jsonable_encoder`** behaviour remain—regression caused 500s on datetime fields during S1 implementation.
- **Do not interpret proxy-only slowness as query complexity** until **`X-FinnWise-Timing`** is present on production—pre-S1 proxy responses lacked server breakdown.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Dependency |
|-----------|------------|
| **Upstream** | **P1-S9** (`GET /api/feed`), **P1-S10** (`GET /api/cards/{id}`), **`connection()`** pattern from Phase 1 DB reads, deployed Pulse/Thread on Vercel/Render. |
| **Downstream** | **P1.5-S2** (pool—expects S1 baseline), **P1.5-S3** (query consolidation—uses **`connection_count`**), **P1.5-S9** (Lighthouse CI—complementary), **P1.5-S10** (sign-off doc attaches post-S1 bench results). |
| **Shared** | **`backend/app/db/connection.py`**, **`backend/app/main.py`** health routes, **`scripts/`** automation folder. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Request-scoped **`ContextVar`** + thin diagnostics module; routes opt in with **`DbRequestTimer`**. |
| **Database** | **No schema changes**, no migrations. |
| **API** | Response **headers** added to existing JSON contracts; **`/health/db`** JSON extended with timing fields. |
| **UI/UX** | **None**—browser may surface **`Server-Timing`** in Network tab only. |
| **Libraries** | **None added**—uses stdlib **`time`**, **`contextvars`**, existing FastAPI/Starlette responses. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `timing.py` | `backend/app/diagnostics/timing.py` | **`DbRequestTimer`**, accumulator, header formatting, **`json_response_with_timing`** |
| `__init__.py` | `backend/app/diagnostics/__init__.py` | Package marker for diagnostics module |
| `bench_api_latency.mjs` | `scripts/bench_api_latency.mjs` | Warm-request latency bench (direct + proxy, p50/p95) |
| `test_api_timing.py` | `backend/tests/test_api_timing.py` | Asserts timing headers on feed/card and health breakdown |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `connection.py` | `backend/app/db/connection.py` | Records **`connect_ms`** / **`query_ms`** into active **`DbRequestTimer`** accumulator |
| `feed.py` | `backend/app/api/feed.py` | Wraps feed build in timer; returns **`JSONResponse`** with timing headers |
| `cards_detail.py` | `backend/app/api/cards_detail.py` | Same pattern; 404 includes timing headers |
| `main.py` | `backend/app/main.py` | **`/health/db`** returns **`connect_ms`**, **`query_ms`**, **`total_ms`** |
| `test_health_db.py` | `backend/tests/test_health_db.py` | Asserts new health JSON fields |
| `README.md` | `scripts/README.md` | P1.5-S1 bench docs + baseline table |
| `finnwise-phase1.5-implementation-tasks.md` | `docs/plans/finnwise-phase1.5-implementation-tasks.md` | P1.5-S1 checkboxes marked complete |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- **None.** Instrumentation wraps existing read paths only.

### B2. API / INTEGRATION CONTRACTS

**Modified: `GET /api/feed`**

- **Request:** unchanged (optional `category`, `horizon`, `session_id`).
- **Response body:** unchanged JSON shape.
- **New response headers:**

```
Server-Timing: db_connect;dur=794.79, db_query;dur=182.62, total;dur=982.27
X-FinnWise-Timing: {"db_connect_ms":794.79,"db_query_ms":182.62,"total_ms":982.27,"connection_count":3}
```

**Modified: `GET /api/cards/{card_id}`**

- **Request:** unchanged (`view=current|original`).
- **Response body:** unchanged.
- **Headers:** same pattern as feed (example **`connection_count`: 4** for current view pre-S3).

**Modified: `GET /health/db`**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `ok` or `error` |
| `cards` | int | Row count when ok |
| `connect_ms` | float | Sum of connect time for the probe (one connection) |
| `query_ms` | float | Time connection held for query |
| `total_ms` | float | End-to-end handler time |

**Example (ok):**

```json
{
  "status": "ok",
  "cards": 8,
  "connect_ms": 300.74,
  "query_ms": 92.84,
  "total_ms": 394.58
}
```

**Auth:** unchanged—no new auth requirements.

### B3. BUSINESS LOGIC & RULES (Detailed)

**Timing semantics**

| Metric | Definition |
|--------|------------|
| **`db_connect_ms`** | Sum of **`psycopg.connect()`** durations for all **`connection()`** calls during the timed request |
| **`db_query_ms`** | Sum of time from post-connect yield to **`connection()`** finally (includes SQL + row processing in that scope) |
| **`total_ms`** | Wall time of route handler from **`DbRequestTimer`** enter to snapshot (includes Python service logic) |
| **`connection_count`** | Number of **`connection()`** opens during the request |

**Baseline interpretation (2026-05-23, local direct, no pool)**

| Endpoint | wall p95 | db_connect p95 | db_query p95 | connections |
|----------|----------|----------------|--------------|-------------|
| Feed | ~999 ms | ~794 ms | ~195 ms | 3 |
| Card detail | ~1285 ms | ~1029 ms | ~249 ms | 4 |
| Feed proxy (prod, pre-S1 deploy) | ~6501 ms | — | — | — |
| Card proxy (prod, pre-S1 deploy) | ~8599 ms | — | — | — |

**Conclusion for S2/S3:** optimising SQL alone will not fix ~8s proxy experience until connect churn and multi-connection patterns are addressed.

### B4. KNOWN CONSTRAINTS & TECH DEBT

- **Production Render backend** had not deployed S1 at baseline capture—proxy bench rows lack **`X-FinnWise-Timing`** until next deploy.
- **`db_query_ms`** is not a Postgres **`EXPLAIN`** metric—it includes ORM/cursor iteration time in the connection scope.
- **Loopback bench** uses direct Supabase `:5432` from local **`.env.local`**, not Render Session pooler—absolute ms differ from production, but **connect vs query ratio** and **connection_count** remain valid signals.
- ⚠️ **`HEAD` on `/backend/api/feed`** via Vercel returns **405** (GET-only route)—bench and monitoring must use **GET**.
- ⚠️ **Port 8000** may already be occupied locally; use another port (e.g. 8001) with **`BENCH_API_DIRECT_URL`** when running bench during dev.

### B5. TESTING NOTES

| Area | Coverage |
|------|----------|
| **`test_api_timing.py`** | Feed/card headers; health breakdown (mocked DB via side_effect recording) |
| **`test_health_db.py`** | Updated ok response shape with timing fields |
| **Manual** | Local **`curl`** on `/api/feed` and `/health/db`; full **`node scripts/bench_api_latency.mjs`** run |
| **Automated bench** | Not in CI yet—that is **P1.5-S9** |

**Gaps:** no integration test hitting real Postgres for timing header values; no assertion on production proxy headers in CI.

**Pytest note:** running the full suite after **`test_feed_route_db_errors.py`** can leave **`SUPABASE_DB_URL`** as a bare project ref in process env and fail unrelated DB tests—run timing/health tests in isolation or clear **`get_settings.cache_clear()`** between modules when debugging.

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| `SUPABASE_DB_URL` | Required for real timing values (backend); Session pooler on Render per **`scripts/README.md`** |
| `BENCH_API_DIRECT_URL` | Render (or local) origin for direct bench paths |
| `BENCH_VERCEL_URL` | Frontend origin for `/backend/...` proxy paths (default: production Vercel app) |
| `BENCH_CARD_ID` | Published card UUID for card detail bench (default: Lighthouse trace card) |
| `BENCH_ALLOW_LOOPBACK` | Set to `1` to allow fallback loopback from **`NEXT_PUBLIC_API_BASE_URL`** |
| `LIGHTHOUSE_THREAD_CARD_ID` | Alternate name accepted for **`BENCH_CARD_ID`** (forward-compatible with S9) |

**Deploy sequencing:** ship backend to Render before expecting timing headers on production proxy paths.

**Run bench (production):**

```bash
BENCH_API_DIRECT_URL=https://<render-service>.onrender.com \
node scripts/bench_api_latency.mjs
```

### B7. HANDOVER NOTES FOR DEVELOPERS

- **Start here:** `backend/app/diagnostics/timing.py` (timer + headers), `backend/app/db/connection.py` (hooks), `scripts/bench_api_latency.mjs` (validation loop).
- **Common mistake:** removing **`jsonable_encoder`** when adding headers—causes **500** on feed/card JSON with datetime fields.
- **Common mistake:** assuming **`total_ms ≈ db_connect_ms + db_query_ms`**—**`total_ms`** includes non-DB Python work; **`db_*`** sums can exceed **`total_ms`** when connections overlap sequentially (they add, wall clock does not double-count parallel work—here connections are sequential).
- **S2 owner:** compare warm **`connect_ms`** on **`/health/db`** and **`db_connect_ms`** in headers before/after pool.
- **S3 owner:** watch **`connection_count`** drop to **1** on feed and card detail.
- **Ops / platform:** attach bench output to PR or **`scripts/README.md`** baseline table after each Phase 1.5 deploy.
