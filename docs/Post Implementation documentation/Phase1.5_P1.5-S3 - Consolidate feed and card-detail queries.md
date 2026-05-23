# Post Implementation Detailed Document — P1.5-S3

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P1.5-S3 (Phase 1.5, Story 3)  
**Reference plan:** `docs/plans/finnwise-phase1.5-implementation-tasks.md`

---

## Narrative style

**P1.5-S1** measured the problem: each Pulse feed request opened **3** Postgres connections and each Thread card-detail request opened **4**, with **`db_connect_ms`** dominating wall time. **P1.5-S2** added a shared connection pool so warm checkouts cost sub-millisecond instead of full TCP/TLS handshakes—but the feed and card-detail services still **acquired and released the pool multiple times per HTTP request**, multiplying round-trips and Python overhead.

**P1.5-S3** collapses those multi-connection patterns into **one `with connection()` scope per API call**. The Pulse feed now runs session profile lookup, pulse row fetch, instrument assessments, and Fog-of-War detection on a single acquired connection. The Thread **current** view uses a new **`fetch_card_detail_bundle(card_id)`** that loads card row, signals, instrument assessments, and stored bias flags in one pass; pre-fetched bias rows are passed into **`build_bias_audit`** so no fifth query runs. The **original** (Day-1 track record) view path is **unchanged**—it still uses separate fetches for live card metadata and immutable publish snapshot, by design.

Local verification after S2 + S3 (pool + consolidation, direct Supabase `:5432`) showed **`connection_count: 1`** on both endpoints, warm feed **p95 ~207 ms**, card detail **p95 ~226 ms**—well under the **800 ms** Phase 1.5 target. Production Vercel proxy paths still report 3–4 connections until Render deploys this backend build. All **131** backend pytest tests pass; response JSON shapes are unchanged.

**Tests executed (summary):** 6 new S3-specific tests in **`test_query_consolidation.py`** (all **passed**); 4 updated feed regression tests (**passed**); 2 original-view immutability tests (**passed**); 3 API timing header tests (**passed**); full backend suite **131/131 passed**. Bench script **`scripts/bench_api_latency.mjs`** run locally (**passed** acceptance: p95 **< 800 ms**, **`connection_count: 1`**).

If you only remember **three anchors**: (1) **`build_feed_response` and current-view `build_card_detail` each use exactly one pool acquire**—verify via **`X-FinnWise-Timing.connection_count`**; (2) **do not re-split bundle queries without measuring**—S1 proved connect churn was the bottleneck; (3) **original view is intentionally exempt** from consolidation to preserve immutable track-record semantics.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1.5-S3 |
| **Title** | Consolidate feed and card-detail queries |
| **Category** | **Backend** (services, DB read paths, tests; no frontend changes) |

**What this story aimed to achieve (plain language)**

Make each Pulse feed and Thread card API call use **one database connection** and minimal round-trips, so the S2 connection pool translates into fast end-to-end response times instead of four sequential pool checkouts per request. Keep response JSON identical so Pulse and Thread clients need no changes.

**How it fits into the overall application**

Phase 1.5 remediates ~8s API latency blocking meaningful content on Pulse and Thread. **P1.5-S1** instrumented latency; **P1.5-S2** pooled connections; **P1.5-S3** removes redundant acquire/release cycles and query round-trips. **P1.5-S4** (HTTP caching), **P1.5-S5/S6** (SSR data loading), and production sign-off **P1.5-S10** depend on S3 delivering sub-800 ms warm API p95 before SSR and Lighthouse work can meet phase targets.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **1.5.3.1** | Refactored **`build_feed_response`** to run profile, pulse rows (+ assessments), and Fog-of-War inside **one** **`with connection()`** block via connection-scoped helpers. |
| **1.5.3.2** | Added **`fetch_card_detail_bundle(card_id)`** and **`CardDetailBundle`** dataclass in **`card_repository.py`**. |
| **1.5.3.3** | Wired bundle into **`build_card_detail`** (current view); passes **`bias_rows`** to **`build_bias_audit`**. |
| **1.5.3.4** | Verified **`connection_count: 1`** in **`X-FinnWise-Timing`** on feed and card detail (local bench + unit/integration tests). |
| **1.5.3.5** | Ran **`scripts/bench_api_latency.mjs`** locally: feed p95 **207 ms**, card p95 **226 ms** (both **< 800 ms**). |
| **1.5.3.6** | Full pytest green (**131 passed**); feed filtering and original-view immutability regression tests pass. |

**Functional breakdown — Pulse feed**

Before S3, **`build_feed_response`** called four top-level functions, each opening its own **`connection()`**:

1. **`fetch_session_profile`**
2. **`fetch_pulse_rows`** (which internally called **`_assessments_for_cards`** — a second connection)
3. **`fetch_fog_of_war_flag`**

After S3:

- **`build_feed_response`** holds **one** **`with connection() as conn:`** and delegates to:
  - **`_fetch_session_profile_conn(conn, session_id)`**
  - **`_fetch_pulse_rows_conn(conn, ...)`** — includes **`_assessments_for_cards_conn(conn, card_ids)`** on the same connection
  - **`_fetch_fog_of_war_conn(conn)`**
- Standalone wrappers (**`fetch_session_profile`**, **`fetch_pulse_rows`**, **`fetch_fog_of_war_flag`**, **`_assessments_for_cards`**) remain for any external caller that needs an isolated fetch; each still opens its own connection when called directly.

**Functional breakdown — Thread card detail (current view)**

Before S3, current view opened four connections:

1. **`fetch_card_detail_for_review`**
2. **`fetch_signals_for_card`**
3. **`fetch_instrument_assessments_for_card`**
4. **`build_bias_audit(card_id=...)`** → **`fetch_bias_flag_rows`**

After S3:

- **`fetch_card_detail_bundle(card_id)`** runs four SQL statements on **one** connection (detail, signals, instruments, bias flags).
- **`build_card_detail(..., view="current")`** consumes the bundle and calls **`build_bias_audit(card_id=card_id, bias_rows=bundle.bias_flags)`** — no extra DB read for bias panel.

**Original view (unchanged)**

- Still calls **`fetch_card_detail_for_review`** then **`fetch_track_record_initial_publish`** (two connections).
- ICE content, signals, and bias audit come from the immutable **`track_record`** snapshot, not live tables.
- Acceptance criteria explicitly require this path remain unchanged.

**Edge cases, validations, and error handling**

- **Missing card (current view):** bundle detail query returns no row → **`build_card_detail`** returns **`None`** → route **404** with timing headers (unchanged).
- **Missing original snapshot:** **`fetch_track_record_initial_publish`** returns **`None`** → **404** **`original_view_unavailable`** (unchanged).
- **Empty session_id:** profile fetch skipped inside single connection block (same as before).
- **Empty card list:** assessments query not executed; Fog-of-War still evaluated.
- **Empty bias_flags list:** **`build_bias_audit`** returns empty **`flags`** / **`monitored`** arrays without DB fetch.
- **503 on DB misconfiguration:** unchanged — **`RuntimeError`** with **`SUPABASE_DB_URL`** message from **`connection()`**.

**Business rules enforced**

- Feed JSON shape, card ICE payload, Fog-of-War logic, confidence tiers, bias audit panel shape, and track-record immutability **unchanged**.
- No change to MMJ, SEBI, bias-flag detection algorithms, or publish/snapshot behaviour.
- **`connection_count`** in timing headers is the acceptance signal for this story.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Connection-scoped `_fetch_*_conn` helpers + thin public wrappers** | Consolidates feed in one place while preserving standalone fetch functions for tests and future callers. | **Single mega-SQL with JOINs**: harder to maintain; duplicates ORM-style row shaping already in Python. |
| **`CardDetailBundle` dataclass** | Explicit typed bundle for card + child rows; clear handoff to **`build_card_detail`**. | **Untyped dict**: loses structure; harder to test. |
| **Four sequential queries in bundle (not one JOIN)** | Minimal diff; reuses existing column lists; easy to verify parity with prior fetch functions. | **One large JOIN**: risk of cartesian explosion on signals × instruments; harder regression testing. |
| **`bias_rows` parameter on `build_bias_audit`** | Allows **`card_id`** to remain in signature for API clarity while skipping **`fetch_bias_flag_rows`** when rows already loaded. | **Only `findings=` kwarg**: works but less explicit when both card_id and rows are known. |
| **Original view exempt from bundle** | Snapshot path reads **`track_record.payload`**, not live signals/instruments tables; consolidating would not reduce connections meaningfully without redesigning publish immutability. | **Bundle original + track in one connection**: out of scope; changes snapshot semantics risk. |
| **Keep `fetch_card_detail_for_review` for original view header fields** | **`event_id`**, **`category`**, **`published_at`** still sourced from live card row for envelope metadata. | **Snapshot-only original view**: would break existing tests and metadata fields. |

**Assumptions**

- Sequential queries on one connection are faster than four pool acquire/release cycles even when total SQL time is similar—validated by S1 baseline and S3 bench.
- Local bench on direct `:5432` with pool is representative of **`connection_count`** and relative latency improvement; absolute ms on Render Session pooler may differ.

**⚠️ Critical — do not reverse lightly**

- **Do not reintroduce separate `connection()` calls inside `build_feed_response` or current-view `build_card_detail`** without re-measuring **`connection_count`**—regression directly restores multi-second warm latency on Render.
- **Do not fold original-view fetches into `fetch_card_detail_bundle`** without product/architecture review—track-record immutability is a Phase 1 contract.
- **When extending card detail with new child tables**, add the query to **`fetch_card_detail_bundle`** (same connection), not a new standalone fetch in **`build_card_detail`**.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Dependency |
|-----------|------------|
| **Upstream** | **P1.5-S1** (timing headers, **`connection_count`**), **P1.5-S2** (pool—S3 benefits require warm pool checkout), **P1-S9** feed service, **P1-S10** card detail + track record, **P1-S13** bias flags table. |
| **Downstream** | **P1.5-S4** (HTTP caching on fast read paths), **P1.5-S5** (Pulse SSR), **P1.5-S6** (Thread SSR), **P1.5-S9** (Lighthouse CI), **P1.5-S10** (production sign-off bench). |
| **Shared** | **`backend/app/services/feed.py`**, **`card_detail.py`**, **`card_repository.py`**, **`bias_detector.py`**, **`backend/app/db/connection.py`**, **`scripts/bench_api_latency.mjs`**. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Single-connection orchestration at **service build** layer; repository bundle for card detail reads; S1 timing hooks unchanged. |
| **Database** | **No schema changes**, no migrations. Read-only query consolidation only. |
| **API** | **No route or payload changes**—same **`GET /api/feed`** and **`GET /api/cards/{id}`** JSON; timing headers now show **`connection_count: 1`**. |
| **UI/UX** | **None**—frontend consumes same JSON; perf improvement is transparent until SSR (S5/S6). |
| **Libraries** | **None added**—uses existing **`psycopg`**, pool from S2, stdlib **`dataclasses`**. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `test_query_consolidation.py` | `backend/tests/test_query_consolidation.py` | Connection-count tests, bundle wiring, bias pre-fetch, live DB integration checks |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `feed.py` | `backend/app/services/feed.py` | Added `_fetch_*_conn` helpers; **`build_feed_response`** uses single **`connection()`** block |
| `card_repository.py` | `backend/app/services/card_repository.py` | Added **`CardDetailBundle`**, **`fetch_card_detail_bundle()`** |
| `card_detail.py` | `backend/app/services/card_detail.py` | Current view uses bundle; passes **`bias_rows`** to **`build_bias_audit`** |
| `bias_detector.py` | `backend/app/services/bias_detector.py` | **`build_bias_audit`** accepts optional **`bias_rows`** to skip DB fetch |
| `test_feed_filtering.py` | `backend/tests/test_feed_filtering.py` | Mocks updated for `_fetch_*_conn` + **`connection`** pattern |
| `README.md` | `scripts/README.md` | P1.5-S3 post-consolidation bench table |
| `finnwise-phase1.5-implementation-tasks.md` | `docs/plans/finnwise-phase1.5-implementation-tasks.md` | P1.5-S3 acceptance criteria and tasks marked complete |

---

### A8. TESTS EXECUTED

**Summary**

| Suite / script | Command | Result | Date |
|----------------|---------|--------|------|
| S3-focused pytest | `pytest tests/test_query_consolidation.py tests/test_feed_filtering.py tests/test_card_detail_original_immutable.py tests/test_api_timing.py -v` | **15/15 passed** | 23-05-2026 |
| Full backend pytest | `pytest -q` (from `backend/`) | **131/131 passed** | 23-05-2026 |
| API latency bench | `node scripts/bench_api_latency.mjs` with `BENCH_API_DIRECT_URL=http://127.0.0.1:8000` | **Passed** — feed p95 **207 ms**, card p95 **226 ms**, **`connection_count: 1`** on direct paths | 23-05-2026 |

**New tests — `backend/tests/test_query_consolidation.py` (P1.5-S3)**

| Test | What it verifies | Status |
|------|------------------|--------|
| `test_build_feed_uses_single_connection` | **`build_feed_response`** acquires pool once; **`DbRequestTimer.connection_count == 1`** | ✅ Passed |
| `test_fetch_card_detail_bundle_uses_single_connection` | Bundle runs 4 SQL executes on one connection; **`connection_count == 1`** | ✅ Passed |
| `test_build_card_detail_current_uses_bundle_not_piecemeal_fetches` | Current view calls **`fetch_card_detail_bundle`** once (no separate signal/instrument/bias fetches) | ✅ Passed |
| `test_build_bias_audit_uses_prefetched_rows_without_db` | **`build_bias_audit(card_id=…, bias_rows=…)`** skips **`fetch_bias_flag_rows`** | ✅ Passed |
| `test_build_feed_live_connection_count` | Integration: real Postgres feed build reports **`connection_count == 1`** | ✅ Passed |
| `test_build_card_detail_current_live_connection_count` | Integration: real Postgres current card detail reports **`connection_count == 1`** | ✅ Passed |

**Updated regression tests — `backend/tests/test_feed_filtering.py`**

| Test | What it verifies | Status |
|------|------------------|--------|
| `test_confidence_tier_buckets` | Confidence tier bucketing unchanged after feed refactor | ✅ Passed |
| `test_build_card_payload_direction_and_magnitude_differ` | Feed card payload shape unchanged (direction vs magnitude tiers, excerpt length) | ✅ Passed |
| `test_build_feed_splits_category_param` | Comma-separated **`category`** query still parsed; **`_fetch_pulse_rows_conn`** receives category list | ✅ Passed |
| `test_build_feed_loads_session_profile` | Session profile loaded via **`_fetch_session_profile_conn(conn, sid)`** inside single connection | ✅ Passed |

**Regression tests — card detail & API timing**

| Test file | Test | What it verifies | Status |
|-----------|------|------------------|--------|
| `test_card_detail_original_immutable.py` | `test_original_view_keeps_day_one_copy_while_current_mutates` | Original view immutability after card edit (S3 did not break track-record path) | ✅ Passed |
| `test_card_detail_original_immutable.py` | `test_original_view_missing_returns_none` | Missing snapshot returns **`None`** for original view | ✅ Passed |
| `test_api_timing.py` | `test_feed_includes_timing_headers` | Feed route still emits **`X-FinnWise-Timing`** | ✅ Passed |
| `test_api_timing.py` | `test_card_detail_includes_timing_headers` | Card detail route still emits timing headers | ✅ Passed |
| `test_api_timing.py` | `test_health_db_returns_connect_and_query_breakdown` | **`/health/db`** timing breakdown intact (S1/S2) | ✅ Passed |

**Manual / script validation**

| Script | What was tested | Result |
|--------|-----------------|--------|
| `scripts/bench_api_latency.mjs` | 1 warmup + 5 warm iterations on feed and card detail (direct local) | ✅ p95 **< 800 ms**; **`connection_count: 1`** |
| `curl -i http://127.0.0.1:8000/api/feed` | Timing header includes **`connection_count":1`** | ✅ Verified during S3 implementation |

**Not yet run (requires manual deploy — see below)**

| Script / check | Why pending |
|----------------|-------------|
| Bench against **Render direct** URL | Backend with S3 not deployed to production yet |
| Bench against **Vercel `/backend/...` proxy** | Proxy still serves pre-S3 Render build (**`connection_count` 3–4** observed) |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- **None.** All queries target existing tables:
  - Feed: **`session_profiles`**, **`cards`**, **`events`**, **`instrument_assessments`**
  - Card bundle: **`cards`**, **`events`**, **`signals`**, **`instrument_assessments`**, **`card_bias_flags`**
  - Original view: **`track_record`** (unchanged)

### B2. API / INTEGRATION CONTRACTS

**Unchanged routes**

| Method | Route | Change |
|--------|-------|--------|
| `GET` | `/api/feed` | Response body identical; **`connection_count`** now **1** |
| `GET` | `/api/cards/{card_id}?view=current` | Response body identical; **`connection_count`** now **1** |
| `GET` | `/api/cards/{card_id}?view=original` | Unchanged behaviour; **`connection_count`** still **2** (detail + track_record) |

**Example timing header (feed, post-S3, warm pool):**

```
Server-Timing: db_connect;dur=0.05, db_query;dur=173.08, total;dur=202.42
X-FinnWise-Timing: {"db_connect_ms":0.05,"db_query_ms":173.08,"total_ms":202.42,"connection_count":1}
```

**Auth:** unchanged—no new auth requirements.

### B3. BUSINESS LOGIC & RULES (Detailed)

**Feed single-connection flow**

```
build_feed_response
└── with connection() as conn
    ├── _fetch_session_profile_conn(conn)     [if session_id set]
    ├── _fetch_pulse_rows_conn(conn)
    │   ├── SELECT cards JOIN events …
    │   └── _assessments_for_cards_conn(conn, card_ids)
    └── _fetch_fog_of_war_conn(conn)
└── build_card_payload (Python, no DB)
```

**Card detail current-view flow**

```
build_card_detail(view=current)
└── fetch_card_detail_bundle(card_id)
    └── with connection()
        ├── SELECT card + event detail
        ├── SELECT signals
        ├── SELECT instrument_assessments
        └── SELECT card_bias_flags
└── build_bias_audit(bias_rows=…)  [no DB]
└── assemble ICE payload (Python)
```

**Latency comparison (local direct, 2026-05-23)**

| Stage | Feed connections | Feed wall p95 | Card connections | Card wall p95 |
|-------|------------------|---------------|------------------|---------------|
| S1 baseline (no pool) | 3 | ~999 ms | 4 | ~1285 ms |
| S2 pool only (multi-acquire) | 3–4 | improved connect | 3–4 | improved connect |
| **S2 + S3** | **1** | **~207 ms** | **1** | **~226 ms** |
| Prod proxy (pre-S3 deploy) | 3–4 | ~6200–8050 ms | 3–4 | ~7800–8050 ms |

**Conclusion:** S3 completes the backend read-path remediation for Pulse and Thread **current** views; production proxy gains require Render deploy. Original view and client-side waterfall (SSR) are separate stories.

### B4. KNOWN CONSTRAINTS & TECH DEBT

- **Production Render/Vercel proxy** still serves pre-S3 backend at time of writing—proxy bench shows **`connection_count` 3–4** until deploy.
- **Original view** still uses **2 connections**—acceptable per acceptance criteria; further consolidation would require snapshot-only metadata design.
- **Four round-trip queries in bundle** could be reduced to fewer SQL statements in a future optimization if **`db_query_ms`** becomes the bottleneck (currently ~140–194 ms p95 locally).
- **`detect_sector_concentration`** (used in **`detect_all`**, not read path) still opens its own connection—out of S3 scope.
- ⚠️ **Port 8000 conflicts** during local bench: stale uvicorn process may serve old code without timing headers; kill existing process before bench (see S1 handover notes).

### B5. TESTING NOTES

| Area | Coverage |
|------|----------|
| **`test_query_consolidation.py`** | Single-connection feed (mocked timed connection); bundle single connection (4 executes, 1 acquire); current view uses bundle not piecemeal fetches; **`bias_rows`** skips DB; live DB integration for connection count |
| **`test_feed_filtering.py`** | Category split and session profile wiring via `_fetch_*_conn` mocks |
| **`test_card_detail_original_immutable.py`** | Original vs current immutability after card edit—regression pass |
| **`test_api_timing.py`** | Timing headers still present on routes |
| **Manual / bench** | **`node scripts/bench_api_latency.mjs`** with **`BENCH_API_DIRECT_URL=http://127.0.0.1:8000`** |

**Gaps:** no CI job asserting **`connection_count === 1`** on deployed Render; production proxy bench not re-run post-deploy (pending deploy).

**Pytest:** full suite **131 passed** after S3 (re-run 23-05-2026).

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| `SUPABASE_DB_URL` | Unchanged; Session pooler on Render recommended (S2) |
| `BENCH_API_DIRECT_URL` | Point at local or Render backend for post-S3 bench |
| `BENCH_CARD_ID` | Published card UUID for card detail bench |

**Deploy sequencing:** deploy backend to Render after merging S3; re-run bench on direct Render URL and Vercel proxy to confirm **`connection_count: 1`** and p95 **< 800 ms** on warm paths.

**Run bench (local, after S2+S3):**

```powershell
$env:BENCH_API_DIRECT_URL="http://127.0.0.1:8000"
node scripts/bench_api_latency.mjs
```

### B7. HANDOVER NOTES FOR DEVELOPERS

- **Start here:** `backend/app/services/feed.py` (`build_feed_response`), `backend/app/services/card_repository.py` (`fetch_card_detail_bundle`), `backend/app/services/card_detail.py` (view branching).
- **Verify change:** `curl -i http://127.0.0.1:8000/api/feed` → check **`connection_count":1`** in **`X-FinnWise-Timing`**.
- **Common mistake:** adding a new `fetch_*_for_card()` call inside **`build_card_detail`** current branch instead of extending the bundle—restores multi-connection pattern.
- **Common mistake:** mocking **`fetch_session_profile`** in feed tests after S3—**`build_feed_response`** now calls **`_fetch_session_profile_conn`** inside **`connection()`**; update mocks accordingly.
- **S4 owner:** cache headers safe now that read path is fast; still use **`no-store`** for draft/admin.
- **S5/S6 owner:** SSR can call Render direct; expect sub-second API with S2+S3 deployed.
- **Ops / platform:** attach post-deploy bench table to **`scripts/README.md`** and **P1.5-S10** sign-off doc.
