# Post Implementation Detailed Document — P1.5-S4

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P1.5-S4 (Phase 1.5, Story 4)  
**Reference plan:** `docs/plans/finnwise-phase1.5-implementation-tasks.md`

---

## Narrative style

**P1.5-S1–S3** reduced warm API latency to sub-800 ms p95 by instrumenting timing, pooling Postgres connections, and consolidating feed/card-detail queries to one connection per request. **P1.5-S4** adds safe HTTP caching on published read paths so repeat Pulse and Thread navigation can reuse JSON for up to 60 seconds without serving stale editorial drafts.

Published feed and card detail responses now return **`Cache-Control: private, max-age=60, stale-while-revalidate=300`**. Draft lifecycle cards, 404 responses, and all **`/api/admin/*`** and **`/admin/*`** routes use **`Cache-Control: no-store`**. Client refetch paths (**`usePulseFeed`**, **`useCard`**) intentionally keep **`fetch(..., { cache: "no-store" })`** for category filter changes, Current/Original view toggles, and retries — so interactive updates always bypass cache even though the backend allows caching on published reads.

**Tests executed (summary):** 7 new S4-specific tests in **`test_http_cache.py`** (all **passed**); 3 existing API timing header tests (**passed**); S4-focused pytest **10/10 passed**. Full backend suite **129 passed, 2 failed** — failures are in **`test_signal_monitor_logs_override_decisions.py`** due to local DB pool DNS resolution (`getaddrinfo failed`), unrelated to S4 cache changes.

If you only remember **three anchors**: (1) **feed is always cacheable** — it only surfaces published lifecycle cards; (2) **card detail cache depends on lifecycle** — **`view=original`** is always cacheable; current view checks **`lifecycle_state`**; (3) **admin middleware enforces no-store** — editorial paths never pick up published-read cache headers.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1.5-S4 |
| **Title** | HTTP caching for published read paths |
| **Category** | **Backend** (API response headers, middleware, tests; no frontend changes) |

**What this story aimed to achieve (plain language)**

Let returning users navigating between Pulse cards benefit from browser/private cache on safe read paths, while draft and admin editorial data always bypasses cache. Repeat views of the same feed or published card can feel instant within a 60-second freshness window without exposing unpublished editorial content.

**How it fits into the overall application**

Phase 1.5 remediates production load performance on Pulse and Thread. **P1.5-S1–S3** made the API fast enough to cache meaningfully. **P1.5-S4** adds cache headers on published reads. **P1.5-S5/S6** (SSR data loading) can align server fetches with **`revalidate: 60`**. Lighthouse bf-cache warnings from client **`no-store`** refetches are documented as an acceptable freshness trade-off.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **1.5.4.1** | Added **`backend/app/http/cache_control.py`** — lifecycle-keyed helper functions and cache constants. |
| **1.5.4.2** | Applied cache headers to **`GET /api/feed`** and **`GET /api/cards/{id}`** via extended **`json_response_with_timing`**. |
| **1.5.4.3** | Added **`AdminNoStoreCacheMiddleware`** in **`main.py`** for **`/api/admin/*`** and **`/admin/*`**; confirmed draft lifecycle cards return **`no-store`**. |
| **1.5.4.4** | Added **`test_http_cache.py`** (7 tests) and documented verification steps + bf-cache trade-off in **`scripts/README.md`**. |

**Functional breakdown — cache header helper**

**`cache_control_for_feed()`** always returns the published-read cache directive because the feed query filters to **`VISIBLE_CARD_STATES`** only (published, active, signal_triggered, thesis_confirmed, thesis_weakened, resolved).

**`cache_control_for_card_detail(view, lifecycle_state)`** logic:

| Condition | Cache-Control |
|-----------|---------------|
| **`view=original`** | **`private, max-age=60, stale-while-revalidate=300`** (immutable Day-1 snapshot) |
| **`view=current`** + lifecycle in **`CACHEABLE_LIFECYCLE_STATES`** | same published-read directive |
| **`view=current`** + draft / unknown lifecycle | **`no-store`** |
| **404 (card not found / original unavailable)** | **`no-store`** |

**Functional breakdown — route wiring**

- **`feed.py`**: passes **`cache_control=cache_control_for_feed()`** to **`json_response_with_timing`**.
- **`cards_detail.py`**: after successful build, passes lifecycle from payload to **`cache_control_for_card_detail`**; 404 responses attach **`no-store`** alongside timing headers.
- **`timing.py`**: **`json_response_with_timing`** accepts optional **`cache_control`** and merges into response headers with existing **`Server-Timing`** / **`X-FinnWise-Timing`**.
- **`main.py`**: **`AdminNoStoreCacheMiddleware`** runs after route handlers and sets **`no-store`** on admin path prefixes.

**Edge cases, validations, and error handling**

- **Invalid horizon on feed:** **422** unchanged — no cache header added (FastAPI default error response).
- **503 DB unavailable:** unchanged — error response without published-read cache.
- **Draft card accessed via public `/api/cards/{id}`:** returns **200** with **`no-store`** (card exists but lifecycle is draft).
- **Admin draft review:** middleware forces **`no-store`** regardless of response body lifecycle.
- **422 horizon validation on feed:** no cache header (validation error before handler builds response).

**Business rules enforced**

- Published/active lifecycle content may be cached privately for **60s** with **300s stale-while-revalidate**.
- Editorial drafts, admin routes, and error responses must never be cached.
- Client refetch semantics unchanged — filter changes, view toggles, and retries still use **`cache: "no-store"`**.
- Response JSON shapes, MMJ, SEBI, bias-flag, and track-record behaviour **unchanged**.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Dedicated `cache_control.py` module** | Single source of truth for cache constants and lifecycle rules; easy to test and extend. | **Inline headers in each route**: duplicates lifecycle logic. |
| **`private` not `public` cache** | Feed/card data is user-session-aware (horizon via session profile); private cache avoids shared CDN caching of personalised responses. | **`public, max-age=60`**: risk of cross-user cache bleed on session-scoped feed. |
| **Middleware for admin `no-store`** | Covers all admin routes without editing each handler; guarantees editorial paths never accidentally inherit cache headers. | **Per-route headers only**: easy to miss new admin endpoints. |
| **Feed always cacheable (no per-response check)** | Feed SQL already filters to published lifecycle states only — no draft cards in feed payload. | **Inspect response cards for lifecycle**: unnecessary; feed contract guarantees visibility filter. |
| **`view=original` always cacheable** | Immutable track-record snapshot; safe to cache even if live card lifecycle changes. | **Check live lifecycle for original view**: would reduce cache hit rate without freshness benefit. |
| **Keep client refetch on `no-store`** | Filter pills, view toggle, and retry must always fetch fresh data; documented bf-cache Lighthouse warning is acceptable. | **Remove client `no-store`**: faster repeat nav but stale filter/toggle state. |
| **Extend `json_response_with_timing` not separate helper** | Timing + cache headers co-located on same JSONResponse; minimal route diff. | **Response middleware for all routes**: harder to lifecycle-key card detail. |

**Assumptions**

- 60-second max-age aligns with Phase 1.5 SSR plan (**`revalidate: 60`** in S5/S6).
- Browsers and Next.js fetch will honour backend **`Cache-Control`** on direct API calls; Vercel `/backend` proxy forwards response headers unchanged.

**⚠️ Critical — do not reverse lightly**

- **Do not remove admin `no-store` middleware** — editorial draft review must never be served from cache.
- **Do not change client refetch paths to default cache** without product sign-off — filter/view toggle freshness depends on **`cache: "no-store"`**.
- **Do not use `public` cache on feed** — session horizon personalisation makes shared caching unsafe.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Dependency |
|-----------|------------|
| **Upstream** | **P1.5-S3** (fast read paths make caching worthwhile), **P1-S9** feed API, **P1-S10** card detail API, **P1.5-S1** timing headers (unchanged alongside cache headers). |
| **Downstream** | **P1.5-S5** (Pulse SSR — use **`revalidate: 60`**), **P1.5-S6** (Thread SSR), **P1.5-S9** (Lighthouse — bf-cache warning expected), **P1.5-S10** (production sign-off). |
| **Shared** | **`backend/app/api/feed.py`**, **`cards_detail.py`**, **`diagnostics/timing.py`**, **`main.py`**, **`frontend/lib/cards/usePulseFeed.ts`**, **`frontend/lib/cards/useCard.ts`**. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Lifecycle-keyed cache helper + route-level header injection + admin path middleware. |
| **Database** | **No schema changes**, no migrations. |
| **API** | Same routes and JSON payloads; new **`Cache-Control`** response header on feed and card detail. |
| **UI/UX** | **None in S4** — frontend unchanged; cache benefit visible on repeat navigation and future SSR fetches. |
| **Libraries** | **None added** — uses existing FastAPI/Starlette middleware and response headers. |

**Cache directive**

```http
Cache-Control: private, max-age=60, stale-while-revalidate=300
```

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `__init__.py` | `backend/app/http/__init__.py` | HTTP helpers package marker |
| `cache_control.py` | `backend/app/http/cache_control.py` | Lifecycle-keyed cache header helpers and constants |
| `test_http_cache.py` | `backend/tests/test_http_cache.py` | Unit tests for feed, card detail, admin, and 404 cache headers |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `timing.py` | `backend/app/diagnostics/timing.py` | **`json_response_with_timing`** accepts optional **`cache_control`** parameter |
| `feed.py` | `backend/app/api/feed.py` | Attaches published-read **`Cache-Control`** on feed responses |
| `cards_detail.py` | `backend/app/api/cards_detail.py` | Lifecycle/view-keyed cache headers; **`no-store`** on 404 |
| `main.py` | `backend/app/main.py` | Added **`AdminNoStoreCacheMiddleware`** for admin routes |
| `README.md` | `scripts/README.md` | P1.5-S4 cache verification steps and bf-cache trade-off note |
| `finnwise-phase1.5-implementation-tasks.md` | `docs/plans/finnwise-phase1.5-implementation-tasks.md` | P1.5-S4 acceptance criteria and tasks marked complete |

---

### A8. TESTS EXECUTED

**Summary**

| Suite / script | Command | Result | Date |
|----------------|---------|--------|------|
| S4-focused pytest | `pytest tests/test_http_cache.py tests/test_api_timing.py -v` | **10/10 passed** | 23-05-2026 |
| Full backend pytest | `pytest -q` (from `backend/`) | **129 passed, 2 failed** | 23-05-2026 |

The 2 failures are in **`test_signal_monitor_logs_override_decisions.py`** — local DB pool DNS resolution (`getaddrinfo failed`), **unrelated to S4**.

**New tests — `backend/tests/test_http_cache.py` (P1.5-S4)**

| Test | What it verifies | Status |
|------|------------------|--------|
| `test_feed_sets_published_read_cache_control` | **`GET /api/feed`** returns published-read **`Cache-Control`** | ✅ Passed |
| `test_card_detail_current_published_is_cacheable` | Current view with **`active`** lifecycle is cacheable | ✅ Passed |
| `test_card_detail_current_draft_is_no_store` | Current view with **`draft`** lifecycle returns **`no-store`** | ✅ Passed |
| `test_card_detail_original_view_is_cacheable` | **`view=original`** always cacheable | ✅ Passed |
| `test_card_detail_not_found_is_no_store` | **404** card detail returns **`no-store`** | ✅ Passed |
| `test_admin_card_review_is_no_store` | **`GET /api/admin/cards/{id}`** returns **`no-store`** via middleware | ✅ Passed |
| `test_feed_cache_header_is_stable_on_repeat_requests` | Repeat feed requests consistently emit same cache header | ✅ Passed |

**Regression tests — API timing (unchanged by S4)**

| Test file | Test | What it verifies | Status |
|-----------|------|------------------|--------|
| `test_api_timing.py` | `test_feed_includes_timing_headers` | Feed route still emits **`X-FinnWise-Timing`** alongside cache header | ✅ Passed |
| `test_api_timing.py` | `test_card_detail_includes_timing_headers` | Card detail route still emits timing headers | ✅ Passed |
| `test_api_timing.py` | `test_health_db_returns_connect_and_query_breakdown` | **`/health/db`** timing breakdown intact | ✅ Passed |

**Manual / script validation**

| Check | What was tested | Result |
|-------|-----------------|--------|
| `curl -i http://127.0.0.1:8000/api/feed` | Response includes **`Cache-Control: private, max-age=60, stale-while-revalidate=300`** | ✅ Documented in **`scripts/README.md`** |
| Browser cache hit (DevTools) | Second request within 60s shows disk/memory cache | ⏳ Pending — requires manual check after deploy |

**Not yet run (requires manual deploy — see B6)**

| Script / check | Why pending |
|----------------|-------------|
| Production **`curl`** against Render direct URL | Backend with S4 not deployed to Render yet |
| Production **`curl`** against Vercel `/backend/...` proxy | Proxy serves pre-S4 Render build until deploy |
| Browser cache hit on production Pulse/Thread | Requires deployed backend + manual DevTools check |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- **None.** Cache policy is applied at the HTTP response layer only; no schema, migration, or seed changes.

---

### B2. API / INTEGRATION CONTRACTS

**Modified routes (response headers only — body unchanged)**

| Method | Route | Cache-Control |
|--------|-------|---------------|
| `GET` | `/api/feed` | `private, max-age=60, stale-while-revalidate=300` |
| `GET` | `/api/cards/{card_id}?view=current` | Published-read directive when lifecycle is published/active/etc.; **`no-store`** for draft |
| `GET` | `/api/cards/{card_id}?view=original` | Published-read directive |
| `GET` | `/api/cards/{card_id}` (404) | `no-store` |
| `GET` | `/api/admin/*` | `no-store` (middleware) |
| `GET` | `/admin/*` | `no-store` (middleware) |

**Example response headers (feed, post-S4):**

```http
HTTP/1.1 200 OK
Cache-Control: private, max-age=60, stale-while-revalidate=300
Server-Timing: db_connect;dur=0.05, db_query;dur=173.08, total;dur=202.42
X-FinnWise-Timing: {"db_connect_ms":0.05,"db_query_ms":173.08,"total_ms":202.42,"connection_count":1}
Content-Type: application/json
```

**Auth:** unchanged — no new auth requirements.

**Frontend fetch contracts (unchanged in S4):**

| Consumer | Fetch option | Reason |
|----------|--------------|--------|
| `usePulseFeed.ts` | `cache: "no-store"` | Category filter changes must refetch fresh |
| `useCard.ts` | `cache: "no-store"` | Current/Original toggle must refetch fresh |
| Future `server.ts` (S5/S6) | `next: { revalidate: 60 }` | First-paint SSR aligned with backend cache window |

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Cache decision flow — card detail**

```
GET /api/cards/{id}?view=...
├── build_card_detail returns None → 404 + no-store
└── build_card_detail returns payload
    ├── view == "original" → published-read cache
    └── view == "current"
        ├── lifecycle in CACHEABLE_LIFECYCLE_STATES → published-read cache
        └── else (draft, etc.) → no-store
```

**Cacheable lifecycle states (matches feed visibility)**

- `published`, `active`, `signal_triggered`, `thesis_confirmed`, `thesis_weakened`, `resolved`

**Admin middleware flow**

```
Request → route handler → AdminNoStoreCacheMiddleware
└── if path starts with /api/admin or /admin
    └── response.headers["Cache-Control"] = "no-store"
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

- **Production Render/Vercel** still serves pre-S4 backend until manual deploy — cache headers not live in production yet.
- **Lighthouse bf-cache warning** expected: client refetch paths use **`cache: "no-store"`**, which disables back/forward cache for those requests. Documented as acceptable freshness trade-off in **`scripts/README.md`**.
- **TestClient does not simulate HTTP cache hits** — repeat-request test verifies header stability only; true browser cache hit requires manual DevTools check.
- **Vercel Edge caching** for card JSON is out of scope (per Phase 1.5 plan).
- ⚠️ **Do not assume proxy strips `Cache-Control`** — verify after Render deploy if repeat-nav latency does not improve.

---

### B5. TESTING NOTES

| Area | Coverage |
|------|----------|
| **`test_http_cache.py`** | Feed cache header; card detail published/draft/original/404; admin no-store; repeat header stability |
| **`test_api_timing.py`** | Timing headers still present after cache header addition |
| **Manual / curl** | Documented in **`scripts/README.md`** — not yet run against production |

**Gaps:** no automated test asserting browser disk-cache hit; no CI check for **`Cache-Control`** on deployed Render; production proxy header verification pending deploy.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| *(none new)* | S4 introduces no new environment variables |

**Deploy sequencing (manual — required):**

1. Merge S4 backend changes.
2. **Deploy backend to Render** — cache headers are backend-only; Vercel frontend deploy is **not required** for S4.
3. Verify production headers:

```powershell
curl -i https://<your-render-service>.onrender.com/api/feed
curl -i "https://<your-render-service>.onrender.com/api/cards/<published-card-id>"
curl -i "https://<your-vercel-app>.vercel.app/backend/api/feed"
```

4. Optional: DevTools Network tab — load feed twice within 60s with cache enabled; confirm second response shows `(disk cache)` or `(memory cache)` when fetched without **`cache: "no-store"`**.

**No migrations, no `.env.local` changes, no Supabase dashboard changes required for S4.**

---

### B7. HANDOVER NOTES FOR DEVELOPERS

- **Start here:** `backend/app/http/cache_control.py` (policy), `backend/app/api/feed.py`, `backend/app/api/cards_detail.py`, `backend/app/main.py` (admin middleware).
- **Verify change:** `curl -i http://127.0.0.1:8000/api/feed` → look for **`Cache-Control: private, max-age=60, stale-while-revalidate=300`**.
- **Common mistake:** adding cache headers to admin routes manually while removing middleware — middleware is the safety net for all admin paths.
- **Common mistake:** changing **`usePulseFeed`** / **`useCard`** to default cache — breaks filter and view-toggle freshness.
- **S5/S6 owner:** create **`frontend/lib/api/server.ts`** with **`next: { revalidate: 60 }`** for SSR first paint; keep client hooks on **`no-store`** for interactive refetch.
- **Ops / platform:** after Render deploy, attach production **`curl`** output to **P1.5-S10** sign-off doc.
