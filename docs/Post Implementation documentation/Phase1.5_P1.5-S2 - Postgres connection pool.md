# Post Implementation Detailed Document — P1.5-S2

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P1.5-S2 (Phase 1.5, Story 2)  
**Reference plan:** `docs/plans/finnwise-phase1.5-implementation-tasks.md`

---

## Narrative style

**P1.5-S1** proved that Pulse and Thread API latency was dominated by **database connect time**, not SQL complexity—each request opened **3–4 new TCP/TLS sessions** via `psycopg.connect()` inside every `with connection()` block. On warm production paths that pattern alone could account for multi-second waits before any query ran.

**P1.5-S2** fixes the connect churn without changing any service or route signatures. The backend now maintains a shared **`psycopg_pool.ConnectionPool`** (min 1, max 10 connections) that opens on FastAPI **lifespan startup** and closes on shutdown. The existing **`connection()`** context manager acquires from the pool and returns connections on exit—every feed, card-detail, factor-DB, and admin code path benefits automatically. S1 timing hooks remain in place: **`db_connect_ms`** on warm requests now reflects **pool checkout** (sub-millisecond locally) instead of full handshake cost.

Local verification after implementation showed **`/health/db`** warm **`connect_ms`** of **0.02–0.08 ms** versus S1 local **`db_connect_ms` p95 of ~794–1029 ms** per request. End-to-end API p95 will still be high until **P1.5-S3** collapses feed and card detail to a single connection per request—but the pool removes the largest per-connect penalty. All **118** backend pytest tests pass; test isolation was hardened so settings-cache and pool state do not leak between modules.

If you only remember **three anchors**: (1) **never call `psycopg.connect()` directly in services**—use **`connection()`** so pooling applies; (2) **lifespan owns pool lifecycle**—do not create ad-hoc pools per route; (3) **re-run `scripts/bench_api_latency.mjs` after Render deploy** to capture production before/after **`db_connect_ms`**.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1.5-S2 |
| **Title** | Postgres connection pool |
| **Category** | **Backend** (DB layer, FastAPI lifespan, tests; no frontend changes) |

**What this story aimed to achieve (plain language)**

Stop opening a new Postgres TCP/TLS session on every database call. Reuse connections through a shared pool so warm API responses return in sub-second time instead of paying ~8 seconds of connect overhead across multiple opens per request. Preserve all existing caller APIs and S1 timing instrumentation so later stories can prove further gains.

**How it fits into the overall application**

Phase 1.5 remediates Pulse and Thread load performance. **P1.5-S1** measured connect-dominated latency; **P1.5-S2** removes that waste at the infrastructure layer. **P1.5-S3** (query consolidation) depends on S2—pooling alone does not reduce **`connection_count`** from 3–4 to 1. SSR stories (S5/S6) and Lighthouse sign-off (S9/S10) benefit indirectly once the backend path is fast enough to deploy.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **1.5.2.1** | Added **`psycopg-pool>=3.2.0`** to **`backend/pyproject.toml`**; backend reinstalled editable with dev deps. |
| **1.5.2.2** | **`init_db_pool()`** / **`close_db_pool()`** singleton; FastAPI **`lifespan`** hook in **`main.py`** opens pool on startup, closes on shutdown. |
| **1.5.2.3** | **`connection()`** refactored to **`pool.connection()`** acquire/release; call-site signatures unchanged across all services. |
| **1.5.2.4** | Local warm **`/health/db`** bench: **`connect_ms`** **0.02–0.08 ms** (vs S1 multi-hundred-ms connect per request). Production bench pending Render deploy. |
| **1.5.2.5** | Full **`pytest -q`**: **118 passed**; pool lifecycle and **`prepare_threshold`** tests added. |

**Functional breakdown**

- **`init_db_pool()`**: reads **`SUPABASE_DB_URL`** via **`get_settings()`**; skips silently if URL empty or not a **`postgresql://`** URI (invalid bare project refs do not crash lifespan); creates **`ConnectionPool`** with **`open=True`**, **`name="finnwise"`**, **`min_size=1`**, **`max_size=10`**, and **`kwargs`** from **`_connect_kwargs()`**.
- **`close_db_pool()`**: calls **`pool.close()`** and clears module singleton.
- **`_get_pool()`**: lazy init if lifespan did not run (e.g. some test paths); raises **`RuntimeError("SUPABASE_DB_URL is not configured")`** if pool cannot be created.
- **`connection()`**: validates URL via **`_require_db_url()`** (unchanged error messages for misconfiguration); acquires from pool; records S1 **`record_db_connect`** / **`record_db_query`** timings; maps **`PsycopgError`** to **`RuntimeError`** with same message pattern as before.
- **`_connect_kwargs()`**: unchanged semantics—**`connect_timeout=10`**; **`prepare_threshold=None`** when port is **6543** (Supabase transaction pooler).

**Edge cases, validations, and error handling**

- **Empty or invalid `SUPABASE_DB_URL` at startup**: lifespan **`init_db_pool()`** returns without creating a pool; **`/health/db`** still returns **`db_unconfigured`**; feed/card routes still return **`503`** with existing error codes when DB is used.
- **Bare Supabase project ref** (e.g. `coqihzykxemmyewakasj`): pool not created at startup; **`connection()`** still raises **`RuntimeError`** with full URI hint when invoked.
- **Transaction pooler port 6543**: **`prepare_threshold=None`** passed into pool **`kwargs`**—required because prepared statements are incompatible with PgBouncer transaction mode.
- **Pool exhaustion**: **`max_size=10`** with blocking acquire (psycopg-pool default); no custom timeout added in S2.
- **TestClient with lifespan**: pool init runs on context-manager entry; tests patch **`get_settings`** on both **`app.main`** and **`app.db.connection`** when simulating unconfigured DB.

**Business rules enforced**

- **No change** to feed JSON shape, card ICE payload, MMJ/SEBI validation, bias flags, track-record immutability, or Fog of War logic.
- **No change** to public API routes or request/response contracts—pooling is transparent to callers.
- S1 **`db_connect_ms`** semantics preserved: now measures pool checkout time on warm requests, not TCP/TLS handshake.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **`psycopg_pool.ConnectionPool`** (official psycopg3 companion) | Same vendor stack as existing **`psycopg[binary]`**; supports **`prepare_threshold`** in pool **`kwargs`**. | **SQLAlchemy pool**: heavier dependency; services use raw psycopg cursors. **Manual singleton list**: reinvents pool checkout, health, and concurrency handling. |
| **FastAPI lifespan for init/close** | Pool ready before first request on Render; clean shutdown releases server connections. | **Lazy-only init**: first production request pays cold pool + first connect; acceptable as fallback but not primary. |
| **Keep `connection()` context manager API** | ~15+ service modules import it; zero call-site churn. | **Inject pool via FastAPI Depends**: large refactor across jobs and services. |
| **Soft validation in `init_db_pool()`** | Prevents lifespan crash when env is misconfigured (matches pre-S2 behaviour where app still boots). | **Hard fail on startup**: would take down Render service when **`SUPABASE_DB_URL`** temporarily wrong. |
| **`min_size=1`, `max_size=10`** | Matches plan tech notes; sufficient for current single-worker Render footprint. | **Higher min_size**: more idle connections against Supabase limits on free tier. |
| **Autouse pytest fixture resetting pool + settings cache** | **`test_feed_route_db_errors`** mutated env and cleared cache; stale cached bare ref broke later integration tests. | **Per-test manual cleanup**: easy to miss in new tests. |

**Assumptions**

- Render continues to use **Session pooler** URI (`…pooler.supabase.com:5432`) per **`scripts/README.md`**—client-side pool sits **above** Supabase pooler, which is acceptable for S2.
- Single uvicorn worker per Render instance—**`max_size=10`** is adequate until horizontal scaling review.

**⚠️ Critical — do not reverse lightly**

- **Do not revert to per-request `psycopg.connect()` in `connection()`** without replacing equivalent pooling—S1 baseline proved connect dominates latency.
- **Do not remove `prepare_threshold=None` for port 6543**—transaction pooler will fail on prepared statements.
- **Do not create second pools** in individual services—use the module singleton only.
- **Keep autouse pool/settings reset in `conftest.py`**—without it, full-suite pytest order can poison integration tests.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Dependency |
|-----------|------------|
| **Upstream** | **P1.5-S1** (timing hooks in **`connection()`**, **`db_connect_ms`** baseline), Phase 1 **`connection()`** pattern, **`SUPABASE_DB_URL`** configuration on Render. |
| **Downstream** | **P1.5-S3** (single-connection feed/card bundle—requires pool first), **P1.5-S4–S10** (performance and SSR stories assume fast warm API), **P1.5-S10** sign-off (production bench after deploy). |
| **Shared** | **`backend/app/db/connection.py`** (all DB reads/writes), **`backend/app/main.py`** (lifespan), **`backend/app/diagnostics/timing.py`** (unchanged but consumes new connect timings). |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Module-level pool singleton + FastAPI lifespan; transparent context-manager wrapper. |
| **Database** | **No schema changes**, no migrations. Pool is client-side only. |
| **API** | **No route or payload changes**; **`/health/db`** JSON shape unchanged from S1. |
| **UI/UX** | **None**. |
| **Libraries** | **`psycopg-pool>=3.2.0`** added to **`backend/pyproject.toml`**. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| — | — | **No new production files.** All behaviour added to existing modules. |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `pyproject.toml` | `backend/pyproject.toml` | Added **`psycopg-pool>=3.2.0`** dependency |
| `connection.py` | `backend/app/db/connection.py` | **`ConnectionPool`** singleton; **`init_db_pool`**, **`close_db_pool`**, **`_get_pool`**; **`connection()`** uses pool acquire/release instead of **`psycopg.connect()`** / **`conn.close()`** |
| `main.py` | `backend/app/main.py` | **`lifespan`** context manager calls **`init_db_pool()`** on startup, **`close_db_pool()`** on shutdown |
| `conftest.py` | `backend/tests/conftest.py` | Autouse **`_reset_settings_and_db_pool`** fixture clears **`get_settings`** cache and closes pool before/after each test |
| `test_health_db.py` | `backend/tests/test_health_db.py` | Pool lifecycle tests; lifespan + unconfigured DB test |
| `test_db_connection.py` | `backend/tests/test_db_connection.py` | **`prepare_threshold`** assertions for port 6543 vs 5432 |
| `test_feed_route_db_errors.py` | `backend/tests/test_feed_route_db_errors.py` | Switched env mutation to **`monkeypatch.setenv`** (auto-restore) |
| `finnwise-phase1.5-implementation-tasks.md` | `docs/plans/finnwise-phase1.5-implementation-tasks.md` | P1.5-S2 acceptance criteria and checkboxes marked complete |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- **None.** Connection pooling is entirely in the application process; Postgres schema and Supabase configuration unchanged.

### B2. API / INTEGRATION CONTRACTS

**No new endpoints. No request/response body changes.**

**Observed behaviour change (diagnostic headers only)**

After deploy, warm **`GET /api/feed`** and **`GET /api/cards/{id}`** responses should show sharply lower **`db_connect_ms`** in **`X-FinnWise-Timing`** while **`connection_count`** remains **3 (feed)** and **4 (card detail)** until **P1.5-S3**.

**Example warm `/health/db` (local, post-S2)**

```json
{
  "status": "ok",
  "cards": 8,
  "connect_ms": 0.03,
  "query_ms": 54.34,
  "total_ms": 79.48
}
```

**Auth:** unchanged.

### B3. BUSINESS LOGIC & RULES (Detailed)

**Pool lifecycle**

```
App startup (lifespan)
  └── init_db_pool()
        ├── URL empty / invalid → _pool stays None
        └── valid postgresql:// URI → ConnectionPool(open=True)

Request handling
  └── with connection() as conn:
        ├── _require_db_url() → RuntimeError if misconfigured
        ├── pool.connection() → checkout (timed as db_connect_ms)
        ├── yield conn → queries (timed as db_query_ms)
        └── return to pool (not conn.close())

App shutdown (lifespan)
  └── close_db_pool() → pool.close(), _pool = None
```

**Connect timing comparison (local backend)**

| Phase | Metric | Feed (S1 baseline) | `/health/db` warm (S2) |
|-------|--------|--------------------|-------------------------|
| S1 | **`db_connect_ms` p95** | ~794 ms | ~301 ms (single connect, no pool) |
| S2 | **`connect_ms` warm** | — | **0.02–0.08 ms** (pool checkout) |

**Interpretation:** S2 removes per-checkout TCP/TLS cost. **`connection_count`** per feed/card request is unchanged—total connect time is still **`connection_count × checkout_ms`**, which S3 will reduce to one checkout.

### B4. KNOWN CONSTRAINTS & TECH DEBT

- **Production bench not yet captured post-deploy**—local numbers above validate pool mechanics; attach Render **`bench_api_latency.mjs`** output in **P1.5-S10** sign-off doc.
- **Double pooling**: client **`ConnectionPool`** + Supabase Session pooler is intentional for S2; monitor connection counts against Supabase limits if **`max_size`** or Render workers increase.
- **`max_size=10` not tuned** for future multi-worker or burst traffic—revisit if pool wait times appear in logs.
- ⚠️ **Jobs/scripts importing `app.main`** outside uvicorn lifespan rely on **lazy `_get_pool()`**—ensure long-running workers call **`init_db_pool()`** explicitly if pool errors appear on first DB use.
- ⚠️ **Integration tests using `db_connection` fixture** still use raw **`psycopg.connect()`** (session-scoped)—that path bypasses the app pool by design for test data setup.

### B5. TESTING NOTES

| Area | Coverage |
|------|----------|
| **`test_db_pool_lifecycle_init_and_close`** | Mocked **`ConnectionPool`** creation and **`close()`**; empty URL skips pool |
| **`test_health_db_with_lifespan_skips_pool_when_unconfigured`** | Lifespan + empty settings does not crash app |
| **`test_connect_kwargs_*`** | Port **6543** → **`prepare_threshold=None`**; port **5432** → no override |
| **`test_health_db_ok`** | Existing timing breakdown assertions (mocked **`connection()`**) |
| **Full suite** | **`python -m pytest -q`** → **118 passed** |
| **Manual** | Local uvicorn **`/health/db`** × 6 warm requests; **`connect_ms`** sub-0.1 ms |

**Gaps:** no integration test asserting real pool reuse against live Postgres timing thresholds; no CI bench gate (deferred to **P1.5-S9**).

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| `SUPABASE_DB_URL` | **Unchanged**—must remain full **`postgresql://`** URI; Session pooler on Render (`…pooler.supabase.com:5432`) |
| Port **6543** | Transaction pooler—**`prepare_threshold=None`** applied automatically |

**Deploy sequencing**

1. Merge and deploy backend to Render (installs **`psycopg-pool`** on build).
2. Confirm **`GET /health/db`** returns ok with low warm **`connect_ms`**.
3. Run **`node scripts/bench_api_latency.mjs`** with **`BENCH_API_DIRECT_URL`** set to Render origin.
4. Proceed to **P1.5-S3** query consolidation.

**Local install after pull**

```bash
pip install -e "./backend[dev]"
```

### B7. HANDOVER NOTES FOR DEVELOPERS

- **Start here:** `backend/app/db/connection.py` (pool + **`connection()`**), `backend/app/main.py` (lifespan), `backend/tests/conftest.py` (test isolation).
- **Common mistake:** calling **`psycopg.connect()`** in new code—always use **`with connection() as conn`** so S1 timing and S2 pooling apply.
- **Common mistake:** removing autouse **`_reset_settings_and_db_pool`**—causes flaky full-suite pytest when env-mutating tests run before integration tests.
- **Common mistake:** expecting **`connection_count: 1`** after S2—count drops in **S3**, not S2.
- **S3 owner:** refactor **`build_feed_response`** and **`build_card_detail`** to single **`with connection()`** scope; verify headers show **`connection_count: 1`**.
- **Ops / platform:** compare production **`X-FinnWise-Timing`** **`db_connect_ms`** before/after Render deploy; attach to **P1.5-S10** post-implementation doc.
