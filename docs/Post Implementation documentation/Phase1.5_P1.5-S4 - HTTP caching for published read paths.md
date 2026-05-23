# Post Implementation Detailed Document — P1.5-S4

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P1.5-S4 (Phase 1.5, Story 4)  
**Reference plan:** `docs/plans/finnwise-phase1.5-implementation-tasks.md`

---

## Narrative style

**P1.5-S1–S3** brought warm API latency under 800 ms p95. **P1.5-S4** adds safe HTTP caching on published read paths so repeat Pulse/Thread navigation can reuse JSON for up to 60 seconds without serving stale editorial drafts.

Published feed and card detail responses now return `Cache-Control: private, max-age=60, stale-while-revalidate=300`. Draft lifecycle cards, 404 responses, and all `/api/admin/*` and `/admin/*` routes use `Cache-Control: no-store`. Client refetch paths (`usePulseFeed`, `useCard`) intentionally keep `fetch(..., { cache: "no-store" })` for filter changes, view toggles, and retries.

If you only remember **three anchors**: (1) **feed is always cacheable** — it only surfaces published lifecycle cards; (2) **card detail cache depends on lifecycle** — `view=original` is always cacheable; current view checks `lifecycle_state`; (3) **admin middleware enforces no-store** — editorial paths never pick up published-read cache headers.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1.5-S4 |
| **Title** | HTTP caching for published read paths |
| **Category** | **Backend** (API response headers, middleware, tests) |

**What this story aimed to achieve (plain language)**

Let returning users navigating between Pulse cards benefit from browser/private cache on safe read paths, while draft and admin editorial data always bypasses cache.

**How it fits into the overall application**

Depends on **P1.5-S3** (fast API). Enables **P1.5-S5/S6** SSR fetches to use `revalidate: 60` aligned with backend cache headers. Lighthouse bf-cache warnings from client `no-store` refetches are documented as an acceptable freshness trade-off.

---

### A2. IMPLEMENTATION SUMMARY

| Sub-task | Deliverable |
|----------|-------------|
| **1.5.4.1** | `backend/app/http/cache_control.py` — lifecycle-keyed helper |
| **1.5.4.2** | `feed.py` + `cards_detail.py` attach cache headers via `json_response_with_timing` |
| **1.5.4.3** | `AdminNoStoreCacheMiddleware` in `main.py` for `/api/admin/*` and `/admin/*` |
| **1.5.4.4** | `backend/tests/test_http_cache.py` (7 tests) + `scripts/README.md` verification steps |

**Cache policy**

| Path | Cache-Control |
|------|---------------|
| `GET /api/feed` | `private, max-age=60, stale-while-revalidate=300` |
| `GET /api/cards/{id}` (published/active lifecycle) | same |
| `GET /api/cards/{id}?view=original` | same |
| `GET /api/cards/{id}` (draft lifecycle) | `no-store` |
| `GET /api/cards/{id}` (404) | `no-store` |
| `/api/admin/*`, `/admin/*` | `no-store` (middleware) |

**Frontend unchanged**

- `frontend/lib/cards/usePulseFeed.ts` — `cache: "no-store"` on filter/refetch
- `frontend/lib/cards/useCard.ts` — `cache: "no-store"` on view toggle/refetch

---

### A3. VERIFICATION

```powershell
cd backend
python -m pytest tests/test_http_cache.py tests/test_api_timing.py -q
```

Local header check:

```powershell
curl -i http://127.0.0.1:8000/api/feed
```

Expect `Cache-Control: private, max-age=60, stale-while-revalidate=300`.

---

### A4. HANDOVER NOTES

- **S5/S6 owner:** SSR helpers in `frontend/lib/api/server.ts` should use `next: { revalidate: 60 }` — not `no-store` — for first-paint fetches.
- **bf-cache:** Lighthouse may still flag bf-cache due to client refetch `no-store`; documented in `scripts/README.md` as acceptable.
- **Do not cache admin or draft paths** — middleware + lifecycle helper enforce this.
