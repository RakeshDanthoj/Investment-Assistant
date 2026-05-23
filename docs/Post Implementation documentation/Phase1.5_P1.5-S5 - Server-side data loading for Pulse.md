# Post Implementation Detailed Document — P1.5-S5

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P1.5-S5 (Phase 1.5, Story 5)  
**Reference plan:** `docs/plans/finnwise-phase1.5-implementation-tasks.md`

---

## Narrative style

**P1.5-S1–S3** fixed the backend: warm `/api/feed` dropped from multi-second connect churn to **~200 ms p95** with a single pooled connection per request. Pulse still felt slow in production because the page was a **client-only waterfall**—users saw skeleton rows until JavaScript hydrated and the browser called `/backend/api/feed` through the Vercel proxy.

**P1.5-S5** moves the initial feed load to the **Next.js Server Component** layer. `pulse/page.tsx` is now async: it calls `fetchPulseFeed()` from `frontend/lib/api/server.ts`, which hits **`NEXT_PUBLIC_API_BASE_URL` directly** (Render in production, loopback locally)—never the browser `/backend` rewrite. The JSON is passed as `initialData` into `PulseClient`, and `usePulseFeed` skips the mount-time fetch when categories match, so **event cards render in the first HTML response** without waiting for hydration. Category filter changes, retry, and session-profile enrichment still use the existing client hook with `cache: "no-store"` and the browser API path.

Automated coverage: **7/7** Jest tests passed for `usePulseFeed` hydration/refetch and server fetch helpers; TypeScript typecheck passed. **Manual Network-tab verification** on a running dev stack is still required before production sign-off (see B5).

If you only remember **three anchors**: (1) **SSR always uses `getServerApiBaseUrl()`**—never `getApiBaseUrl()` in RSC code; (2) **`usePulseFeed` skips exactly one client fetch** when `initialData` matches `initialCategoryQuery`; (3) **filter changes must still refetch client-side**—do not move filter navigation back to full page SSR without measuring UX.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1.5-S5 |
| **Title** | Server-side data loading for Pulse |
| **Category** | **Frontend** (Next.js RSC, client hydration, API consumer; no backend route changes) |

**What this story aimed to achieve (plain language)**

Show Pulse event cards on **first paint** without waiting for JavaScript to hydrate and fetch the feed. The server loads feed JSON during page render and passes it to the client; users see cards immediately on mobile instead of a multi-second skeleton. Category filters and retry still work in the browser as before.

**How it fits into the overall application**

Phase 1.5 removes the client-fetch-after-hydration waterfall on Pulse and Thread. **P1.5-S3** made `/api/feed` fast enough for SSR to be worthwhile; **P1.5-S5** delivers Pulse SSR. **P1.5-S6** (Thread SSR) reuses the same `frontend/lib/api/server.ts` module. **P1.5-S7** (bundle/font diet) and **P1.5-S9** (Lighthouse CI) depend on S5/S6 pages being ready to benchmark.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **1.5.5.1** | Created **`frontend/lib/api/server.ts`** with **`getServerApiBaseUrl()`** and **`fetchPulseFeed()`** for RSC-safe direct API calls. |
| **1.5.5.2** | Refactored **`pulse/page.tsx`** to async Server Component: reads **`?category=`**, server-fetches feed, passes props to **`PulseClient`**. |
| **1.5.5.3** | Updated **`usePulseFeed`** to accept **`initialData`** + **`initialCategoryQuery`**; hydrates state and skips first client fetch when aligned. |
| **1.5.5.4** | **`PulseClient`** wires SSR props; filter pill changes update URL → hook refetches via **`getApiBaseUrl()`** + **`cache: "no-store"`**. |
| **1.5.5.5** | Jest tests for skip/refetch/fallback; manual Network-tab check documented in B5. |

**Functional breakdown — server render path**

```
GET /pulse[?category=macro,rbi_policy]
└── pulse/page.tsx (async RSC)
    ├── categoryQueryFromSearchParams(searchParams.category)
    ├── fetchPulseFeed({ category })  → GET {NEXT_PUBLIC_API_BASE_URL}/api/feed?...
    └── <PulseClient initialData={...} initialCategoryQuery={...} />
        └── usePulseFeed(categories, { initialData, initialCategoryQuery })
            └── skip first useEffect fetch when queries match
            └── render cards immediately (status === "success", data present)
```

**Functional breakdown — client refetch path (unchanged semantics)**

```
User toggles category pill
└── PulseClient.onCategoriesChange → router.replace(?category=...)
└── usePulseFeed categoryQuery changes
└── load() → fetch(getApiBaseUrl()/api/feed?category=...&session_id=..., { cache: "no-store" })
```

**Edge cases, validations, and error handling**

| Scenario | Behaviour |
|----------|-----------|
| **Server fetch succeeds** | `initialData` populated; no skeleton; first card auto-selected |
| **Server fetch fails** (API down, 503) | `initialData = null`; client hook fetches on mount; user may briefly see skeleton then error/retry |
| **Deep link with filters** `/pulse?category=macro` | Server fetches filtered feed; `initialCategoryQuery` matches URL; no duplicate fetch |
| **User changes filter after SSR** | Client refetch runs (verified in Jest) |
| **Empty feed** | Success state with “No events match your filters” copy (unchanged) |
| **Retry button** | Calls **`refetch()`** → client **`load()`** with **`cache: "no-store"`** |
| **SSR without session_id** | Server fetch omits onboarding session; client refetch adds **`session_id`** from **`getStoredSessionId()`** when present |

**Business rules enforced**

- Feed JSON shape unchanged — same **`PulseFeedResponse`** type and card fields.
- Fog-of-War banner, insight panel, mobile → Thread navigation unchanged.
- MMJ, SEBI, bias-flag, and track-record behaviour untouched (read-only feed path).
- Browser production path still uses **`/backend`** proxy via **`getApiBaseUrl()`** for client refetches.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Separate `getServerApiBaseUrl()` from `getApiBaseUrl()`** | Browser helper rewrites to `/backend` on Vercel; RSC must call Render directly to avoid proxy hop + ensure server-side fetch works. | **Reuse `getApiBaseUrl()` in RSC**: would break on Vercel (relative `/backend` invalid on server). |
| **`fetchPulseFeed` uses `cache: "no-store"`** | S4 (HTTP cache headers) not merged yet; avoids stale feed before backend **`Cache-Control`** is wired. | **`next: { revalidate: 60 }`**: planned for S4; can switch once backend cache headers land. |
| **`skipInitialFetchRef` one-shot skip** | Prevents duplicate fetch on hydrate when SSR data matches URL categories; subsequent category changes always refetch. | **Always client-fetch**: defeats SSR purpose. **Full RSC on every filter change**: loses instant pill UX without full navigation. |
| **Swallow server errors → `initialData = null`** | Graceful degradation: client hook retries instead of error page on transient SSR failure. | **RSC error boundary**: harsher UX for recoverable API blips. |
| **Keep `Suspense` around `PulseClient`** | **`useSearchParams()`** requires Suspense boundary in Next.js 14 App Router. | **Remove Suspense**: build/runtime warning or error. |
| **Pattern mirrors `admin/factor-db/page.tsx`** | Established precedent for server **`fetch()`** with direct API base URL. | **New data-fetching library**: out of scope for Phase 1.5. |

**Assumptions**

- **`NEXT_PUBLIC_API_BASE_URL`** is set on Vercel to the Render service URL (HTTPS) so RSC fetch succeeds in production.
- Vercel server can reach Render (no IP allowlist blocking server-side egress).
- Missing **`session_id`** on SSR is acceptable; horizon personalization applies after first client refetch if user completed onboarding.

**⚠️ Critical — do not reverse lightly**

- **Do not call `getApiBaseUrl()` from Server Components** — production SSR will fail or hit wrong host.
- **Do not remove `initialCategoryQuery` matching** — without it, SSR data and URL filters can desync and skip needed refetches or show wrong cards.
- **Do not remove client refetch on filter change** — acceptance criteria require interactive filter pills without full page reload.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Dependency |
|-----------|------------|
| **Upstream** | **P1.5-S3** (fast `/api/feed`), **P1-S9** feed API + **`PulseFeedResponse`** shape, **`frontend/lib/api.ts`** (client base URL), **`admin/factor-db/page.tsx`** SSR precedent. |
| **Downstream** | **P1.5-S6** (Thread SSR — shares **`server.ts`**), **P1.5-S4** (may switch SSR fetch to **`revalidate: 60`** + backend **`Cache-Control`**), **P1.5-S7** (Pulse CLS skeleton fix), **P1.5-S9/S10** (Lighthouse + production sign-off). |
| **Shared** | **`frontend/lib/api/server.ts`**, **`frontend/lib/cards/usePulseFeed.ts`**, **`frontend/lib/cards/pulseTypes.ts`**, **`backend/app/api/feed.py`** (unchanged contract). |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Next.js 14 **async RSC** for initial data; **client component** for interactivity (filters, selection, insight panel). |
| **Database** | **None** — consumes existing **`GET /api/feed`**. |
| **API** | Server: direct **`GET {API_BASE}/api/feed?category=`**; Client: **`GET /backend/api/feed`** (prod) or loopback (local) with **`session_id`** when stored. |
| **UI/UX** | No skeleton when SSR data present; skeleton only on client loading without cached data; error + Retry unchanged. |
| **Libraries** | **None added** — native **`fetch`**, existing Next.js App Router patterns. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `server.ts` | `frontend/lib/api/server.ts` | RSC helpers: **`getServerApiBaseUrl`**, **`fetchPulseFeed`** (shared module; **`fetchCardDetail`** added for S6 in same file) |
| `server.test.ts` | `frontend/lib/api/server.test.ts` | Unit tests for server API helpers |
| `usePulseFeed.test.ts` | `frontend/lib/cards/usePulseFeed.test.ts` | SSR hydration skip, filter refetch, fallback fetch tests |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `page.tsx` | `frontend/app/(app)/pulse/page.tsx` | Async RSC; server **`fetchPulseFeed`**; passes **`initialData`** / **`initialCategoryQuery`** to client |
| `PulseClient.tsx` | `frontend/app/(app)/pulse/_components/PulseClient.tsx` | Accepts SSR props; passes options into **`usePulseFeed`** |
| `usePulseFeed.ts` | `frontend/lib/cards/usePulseFeed.ts` | **`UsePulseFeedOptions`**, hydrated initial state, one-shot skip of mount fetch |
| `finnwise-phase1.5-implementation-tasks.md` | `docs/plans/finnwise-phase1.5-implementation-tasks.md` | P1.5-S5 acceptance criteria and tasks marked complete |

---

### A8. TESTS EXECUTED

**Summary**

| Suite / script | Command | Result | Date |
|----------------|---------|--------|------|
| S5-focused Jest | `npm test -- --testPathPattern="usePulseFeed\|server.test" --forceExit` (from `frontend/`) | **7/7 passed** | 23-05-2026 |
| TypeScript | `npm run typecheck` (from `frontend/`) | **Passed** | 23-05-2026 |
| Backend pytest | Not run for S5 (no backend changes) | N/A | — |

**`frontend/lib/cards/usePulseFeed.test.ts`**

| Test | What it verifies | Status |
|------|------------------|--------|
| `skips the initial client fetch when hydrated from SSR data` | With **`initialData`**, **`fetch`** not called; status **`success`** | ✅ Passed |
| `refetches when category filters change after SSR hydration` | After rerender with new categories, **`fetch`** called with **`category=macro`** | ✅ Passed |
| `fetches on mount when SSR data is unavailable` | No **`initialData`** → client fetch on mount | ✅ Passed |

**`frontend/lib/api/server.test.ts`**

| Test | What it verifies | Status |
|------|------------------|--------|
| Server API helper tests | Direct base URL usage, **`fetchCardDetail`** parsing/errors (shared module; card tests support S6) | ✅ Passed |

**Manual / script validation (required before production sign-off)**

| Check | What to verify | Status |
|-------|----------------|--------|
| Network tab — first `/pulse` load | **No** `/api/feed` or `/backend/api/feed` request before hydration | ⏳ **Manual — see B5** |
| View page source | Card headlines present in HTML | ⏳ Manual |
| Filter pill change | Client fetch fires with updated **`category`** param | ⏳ Manual |
| Production Vercel deploy | **`NEXT_PUBLIC_API_BASE_URL`** → Render HTTPS URL | ⏳ Manual at deploy |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- **None.** SSR consumes existing published feed rows via **`GET /api/feed`**.

### B2. API / INTEGRATION CONTRACTS

**Server-side fetch (RSC)**

```
GET {NEXT_PUBLIC_API_BASE_URL}/api/feed[?category=comma,separated]
Cache: no-store (until P1.5-S4)
Auth: none (public published feed)
```

**Client-side refetch (browser — unchanged)**

```
GET {getApiBaseUrl()}/api/feed?category=...&session_id=...
  → production browser: /backend/api/feed?...
Cache: no-store
```

**Response:** existing **`PulseFeedResponse`** JSON — no contract change.

### B3. BUSINESS LOGIC & RULES (Detailed)

**SSR vs client URL resolution**

| Context | Base URL helper | Production behaviour |
|---------|-----------------|-------------------|
| Server Component | **`getServerApiBaseUrl()`** | `https://<render-service>.onrender.com` |
| Browser client | **`getApiBaseUrl()`** | `/backend` (Vercel rewrite → Render) |
| Local dev (both) | Configured or `http://127.0.0.1:8000` | Direct loopback |

**Hydration skip logic**

```
skipInitialFetch = (initialData != null) AND (initialCategoryQuery === categoryQuery)
on mount: if skipInitialFetch → do not call load(); else load()
on categoryQuery change: always load()
```

### B4. KNOWN CONSTRAINTS & TECH DEBT

- **SSR omits `session_id`** — horizon from onboarding profile applies only after client refetch; brief mismatch possible on first paint for returning users.
- **`fetchPulseFeed` uses `no-store`** — full SSR fetch every navigation until **P1.5-S4** adds ISR/cache headers.
- **`frontend/lib/api/server.ts` is shared with S6** — **`fetchCardDetail`** lives in the same module; coordinate changes across Pulse and Thread SSR stories.
- ⚠️ **Production requires `NEXT_PUBLIC_API_BASE_URL` on Vercel** — if unset, SSR falls back to loopback and feed will fail on Vercel build/runtime.
- No automated E2E/Playwright test for “zero client fetch on first load” — Network tab remains the acceptance check for **1.5.5.5**.

### B5. TESTING NOTES

**Manual checklist (run locally before merge/deploy)**

1. **Start stack**
   - Backend: `uvicorn` on port 8000 with valid **`SUPABASE_DB_URL`**
   - Frontend: `pnpm dev` from `frontend/` with root **`.env.local`** loaded (**`NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`**)

2. **First load — no client feed fetch**
   - Open DevTools → **Network** → disable cache
   - Navigate to **`http://localhost:3000/pulse`**
   - **Expect:** feed cards visible without skeleton flash
   - **Expect:** **no** request to **`/api/feed`** or **`/backend/api/feed`** triggered by the client bundle on initial load
   - **Optional:** **View Page Source** — search for a known card headline; should appear in HTML

3. **Filtered deep link**
   - Open **`/pulse?category=macro`** (or any valid category slug)
   - **Expect:** filtered cards on first paint; no duplicate fetch if categories unchanged

4. **Filter pill interaction**
   - Toggle a category pill
   - **Expect:** URL updates with **`?category=`**
   - **Expect:** **one** new client fetch to **`/api/feed`** (local: direct; prod: **`/backend/api/feed`**)
   - **Expect:** brief loading state acceptable; cards update

5. **SSR failure fallback**
   - Stop backend; hard-refresh **`/pulse`**
   - **Expect:** skeleton or error; **Retry** triggers client fetch when API returns

6. **Production (after deploy)**
   - Confirm Vercel env **`NEXT_PUBLIC_API_BASE_URL`** = Render HTTPS URL
   - Repeat Network check on production **`/pulse`**
   - Run Lighthouse mobile on Pulse (target **P1.5-S9/S10**)

| Area | Automated | Manual |
|------|-----------|--------|
| Hydration skip / filter refetch | ✅ Jest | — |
| Zero client fetch first paint | — | ⏳ Network tab |
| Production env + Render reachability | — | ⏳ Deploy smoke |

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| `NEXT_PUBLIC_API_BASE_URL` | **Required for SSR** — direct Render URL in production; loopback locally |
| `SUPABASE_DB_URL` | Backend only — feed API must be warm/fast (S2+S3 deployed) |
| `CORS_ORIGINS` | Applies to **browser** refetch paths only; SSR server-to-server fetch does not use CORS |

**Deploy sequencing:** deploy backend (S2+S3) to Render first, then frontend with correct **`NEXT_PUBLIC_API_BASE_URL`**. SSR latency equals direct Render API latency—no Vercel proxy on first paint.

**Local dev commands:**

```powershell
# Terminal 1 — backend (from repo root, .env.local loaded)
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
pnpm dev
```

### B7. HANDOVER NOTES FOR DEVELOPERS

- **Start here:** `frontend/app/(app)/pulse/page.tsx`, `frontend/lib/api/server.ts`, `frontend/lib/cards/usePulseFeed.ts`
- **Client vs server API:** RSC → **`getServerApiBaseUrl()`**; browser → **`getApiBaseUrl()`**
- **Common mistake:** using **`getApiBaseUrl()`** in Server Components — breaks Vercel SSR
- **Common mistake:** removing **`initialCategoryQuery`** — causes stale SSR data after filter URL changes
- **Common mistake:** expecting **`session_id`** on SSR — only client refetch reads **`localStorage`**
- **S4 owner:** when backend **`Cache-Control`** lands, consider **`next: { revalidate: 60 }`** in **`fetchPulseFeed`**
- **S6 owner:** extend **`server.ts`** for Thread; do not duplicate base URL logic
- **Ops / platform:** verify Vercel → Render connectivity and env var on every frontend deploy
