# Post Implementation Detailed Document — P1.5-S6

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P1.5-S6 (Phase 1.5, Story 6)  
**Reference plan:** `docs/plans/finnwise-phase1.5-implementation-tasks.md`

---

## Narrative style

**P1.5-S1–S3** fixed the backend: warm `/api/cards/{id}` dropped from multi-second connect churn to **~200 ms p95** with a single pooled connection per request. Thread still felt slow in production because the page was a **client-only waterfall**—users saw a skeleton until JavaScript hydrated and the browser called `/backend/api/cards/{id}` through the Vercel proxy.

**P1.5-S6** moves the initial Thread load to the **Next.js Server Component** layer. `thread/[cardId]/page.tsx` is now async: it calls `fetchCardDetail(cardId, "current")` from `frontend/lib/api/server.ts`, which hits **`NEXT_PUBLIC_API_BASE_URL` directly** (Render in production, loopback locally)—never the browser `/backend` rewrite. The JSON is passed as `initialData` into `ThreadExperience`, and `useCard` skips the mount-time fetch for the **Current** view, so **card title and ICE header render in the first HTML response** without waiting for hydration. The **Current/Original** toggle still client-fetches the alternate view with `cache: "no-store"`; toggling back to **Current** reuses SSR data without a refetch. Unknown card IDs preserve the existing error alert UX (not a Next.js `notFound()` page).

Automated coverage: **8/8** Jest tests passed for `useCard` hydration/toggle behaviour and `fetchCardDetail` server helpers; TypeScript typecheck passed. **Manual Network-tab verification** on a running dev stack is still required before production sign-off (see B5).

If you only remember **three anchors**: (1) **SSR always fetches `view=current` only**—Original is always client-side; (2) **`useCard` restores SSR data when toggling back to Current**—do not refetch unnecessarily; (3) **404 paths pass `initialError` to preserve existing error UI**—do not swap to `notFound()` without a product decision.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1.5-S6 |
| **Title** | Server-side data loading for Thread |
| **Category** | **Frontend** (Next.js RSC, client hydration, API consumer; no backend route changes) |

**What this story aimed to achieve (plain language)**

Show Thread card headline and ICE header on **first paint** without waiting for JavaScript to hydrate and fetch card detail. The server loads `view=current` JSON during page render and passes it to the client; users start reading immediately on mobile instead of an ~8-second skeleton. Current/Original toggle and retry still work in the browser as before.

**How it fits into the overall application**

Phase 1.5 removes the client-fetch-after-hydration waterfall on Pulse and Thread. **P1.5-S3** made `/api/cards/{id}` fast enough for SSR to be worthwhile; **P1.5-S6** delivers Thread SSR using the shared **`frontend/lib/api/server.ts`** module introduced in **P1.5-S5**. **P1.5-S7** (Thread bundle/font diet), **P1.5-S9** (Lighthouse CI), and **P1.5-S10** (production sign-off) depend on S5/S6 pages being ready to benchmark.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **1.5.6.1** | Added **`fetchCardDetail(cardId, view)`** and **`CardDetailFetchError`** to **`frontend/lib/api/server.ts`**. |
| **1.5.6.2** | Refactored **`thread/[cardId]/page.tsx`** to async RSC: server-fetches current view, passes **`initialData`** or **`initialError`**. |
| **1.5.6.3** | Updated **`useCard`** with **`UseCardInitialState`**, SSR hydration, toggle refetch, and Current-view restore via ref-stable effect. |
| **1.5.6.4** | Created **`thread/[cardId]/loading.tsx`** — route-level skeleton for slow SSR edge case. |
| **1.5.6.5** | **`ThreadExperience`** accepts **`initialData`** / **`initialError`**; suppresses skeleton when SSR payload present. |
| **1.5.6.6** | Jest tests for hydration skip, Original toggle fetch, Current restore; manual Network-tab check documented in B5. |

**Functional breakdown — server render path**

```
GET /thread/{cardId}
└── thread/[cardId]/page.tsx (async RSC)
    ├── fetchCardDetail(cardId, "current")
    │     → GET {NEXT_PUBLIC_API_BASE_URL}/api/cards/{cardId}?view=current
    ├── success → <ThreadExperience initialData={...} />
    └── failure → <ThreadExperience initialError={message} />
        └── useCard(cardId, "current", { data | error })
            └── skip mount fetch when Current view hydrated
            └── render title + ICE header immediately
```

**Functional breakdown — client refetch path (toggle + retry)**

```
User toggles to Original
└── useCard view = "original"
└── load() → fetch(getApiBaseUrl()/api/cards/{id}?view=original, { cache: "no-store" })

User toggles back to Current (SSR data present)
└── useCard restores initialData from ref — no fetch

User clicks Retry on error
└── refetch() → load() always runs (client path)
```

**Edge cases, validations, and error handling**

| Scenario | Behaviour |
|----------|-----------|
| **Server fetch succeeds** | `initialData` populated; no skeleton; title + ICE header visible on first paint |
| **404 unknown card** | Server catch → `initialError`; same destructive Alert + Retry UX as before (not Next.js 404 page) |
| **503 / API down on SSR** | `initialError` passed; error UI without skeleton flash |
| **Toggle to Original** | Client fetch with `view=original`; brief loading state acceptable |
| **Toggle back to Current** | Restores SSR `initialData` without refetch |
| **Slow SSR** | Next.js shows **`loading.tsx`** skeleton until RSC resolves |
| **Retry button** | Calls **`refetch()`** → client **`load()`** with **`cache: "no-store"`** |

**Business rules enforced**

- Card detail JSON shape unchanged — same **`CardDetailResponse`** type and ICE fields.
- Original (Day-1 track record) view semantics unchanged — only fetched client-side on toggle.
- MMJ, SEBI, bias-flag, and track-record behaviour untouched (read-only card path).
- Browser production path still uses **`/backend`** proxy via **`getApiBaseUrl()`** for client refetches.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **SSR fetches `view=current` only** | Acceptance criteria; Original is alternate editorial snapshot loaded on demand. | **SSR both views**: doubles server work; Original often unused. |
| **`initialError` instead of `notFound()`** | Plan requires 404/error paths unchanged — existing Alert + Retry UX. | **`notFound()`**: would change UX to Next.js default 404 page. |
| **`initialRef` in `useCard` effect** | Parent passes `{ data, error }` object; ref prevents infinite refetch loops from unstable object identity. | **Put `initial` in effect deps**: caused 12+ fetch calls in tests. |
| **Restore SSR data on Current toggle-back** | Avoids unnecessary API call; Original fetch may be stale vs live Current. | **Always refetch Current**: wastes bandwidth; slower toggle UX. |
| **`fetchCardDetail` uses `cache: "no-store"`** | S4 HTTP cache headers may land separately; avoids stale card before backend **`Cache-Control`**. | **`next: { revalidate: 60 }`**: planned for S4 coordination. |
| **`CardDetailFetchError` with HTTP status** | Typed server-side errors; page can distinguish 404 from 503 if needed later. | **Generic `Error` only**: loses status for future handling. |
| **Shared `server.ts` with S5** | Single module for RSC fetch helpers and base URL logic. | **Duplicate Thread-only server module**: DRY violation. |

**Assumptions**

- **`NEXT_PUBLIC_API_BASE_URL`** is set on Vercel to the Render service URL (HTTPS) so RSC fetch succeeds in production.
- Vercel server can reach Render (no IP allowlist blocking server-side egress).
- Card IDs in Pulse links are valid published UUIDs for happy-path SSR.

**⚠️ Critical — do not reverse lightly**

- **Do not call `getApiBaseUrl()` from Server Components** — production SSR will fail or hit wrong host.
- **Do not put unstable `initial` objects in `useCard` effect dependencies** — causes refetch loops.
- **Do not SSR-fetch Original view by default** — breaks toggle acceptance criteria and track-record lazy-load pattern.
- **Do not swap 404 to `notFound()` without product sign-off** — changes user-visible error UX.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Dependency |
|-----------|------------|
| **Upstream** | **P1.5-S3** (fast `/api/cards/{id}`), **P1-S10** card detail API + **`CardDetailResponse`** shape, **P1.5-S5** (shared **`server.ts`** / **`getServerApiBaseUrl`**), **`frontend/lib/api.ts`** (client base URL). |
| **Downstream** | **P1.5-S7** (Thread dynamic imports + fonts — components now SSR-first), **P1.5-S4** (may switch SSR fetch to **`revalidate: 60`** + backend **`Cache-Control`**), **P1.5-S9/S10** (Lighthouse + production sign-off on Thread). |
| **Shared** | **`frontend/lib/api/server.ts`**, **`frontend/lib/cards/useCard.ts`**, **`frontend/lib/cards/threadTypes.ts`**, **`backend/app/api/cards_detail.py`** (unchanged contract). |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Next.js 14 **async RSC** for initial Current view; **client component** for ICE tabs, toggle, and aside widgets. |
| **Database** | **None** — consumes existing **`GET /api/cards/{id}`**. |
| **API** | Server: direct **`GET {API_BASE}/api/cards/{id}?view=current`**; Client toggle: **`GET /backend/api/cards/{id}?view=original|current`** (prod) or loopback (local). |
| **UI/UX** | No skeleton when SSR data/error present; **`loading.tsx`** for slow SSR only; error Alert + Retry unchanged. |
| **Libraries** | **None added** — native **`fetch`**, existing Next.js App Router patterns. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `loading.tsx` | `frontend/app/(app)/thread/[cardId]/loading.tsx` | Route-level Thread skeleton for slow SSR fallback |
| `useCard.test.ts` | `frontend/lib/cards/useCard.test.ts` | SSR hydration, Original toggle fetch, Current restore tests |

**Note:** `frontend/lib/api/server.ts` and `frontend/lib/api/server.test.ts` were created in **P1.5-S5**; S6 extended them with **`fetchCardDetail`** and **`CardDetailFetchError`**.

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `server.ts` | `frontend/lib/api/server.ts` | Added **`fetchCardDetail`**, **`CardDetailFetchError`** (S6); shares module with S5 **`fetchPulseFeed`** |
| `server.test.ts` | `frontend/lib/api/server.test.ts` | Added **`fetchCardDetail`** parsing and 404 error tests |
| `page.tsx` | `frontend/app/(app)/thread/[cardId]/page.tsx` | Async RSC; server fetch; passes **`initialData`** / **`initialError`** |
| `ThreadExperience.tsx` | `frontend/app/(app)/thread/_components/ThreadExperience.tsx` | Accepts SSR props; memoized initial state; suppresses skeleton when hydrated |
| `useCard.ts` | `frontend/lib/cards/useCard.ts` | SSR hydration, toggle refetch, Current restore, ref-stable effect |
| `finnwise-phase1.5-implementation-tasks.md` | `docs/plans/finnwise-phase1.5-implementation-tasks.md` | P1.5-S6 acceptance criteria and tasks marked complete |

---

### A8. TESTS EXECUTED

**Summary**

| Suite / script | Command | Result | Date |
|----------------|---------|--------|------|
| S6-focused Jest | `npm test -- lib/cards/useCard.test.ts lib/api/server.test.ts --forceExit` (from `frontend/`) | **8/8 passed** | 23-05-2026 |
| TypeScript | `npm run typecheck` (from `frontend/`) | **Passed** | 23-05-2026 |
| Backend pytest | Not run for S6 (no backend changes) | N/A | — |

**`frontend/lib/cards/useCard.test.ts`**

| Test | What it verifies | Status |
|------|------------------|--------|
| `hydrates current view from initialData without calling fetch` | With **`initialData`**, **`fetch`** not called; status **`success`**; title present | ✅ Passed |
| `hydrates current view error from initialError without calling fetch` | With **`initialError`**, no fetch; status **`error`** | ✅ Passed |
| `client-fetches when toggling to original view` | Toggle to Original → one client fetch with **`cache: "no-store"`** | ✅ Passed |
| `reuses initialData when toggling back to current without refetching` | Original → Current restores SSR title; **`fetch`** called only once | ✅ Passed |

**`frontend/lib/api/server.test.ts`**

| Test | What it verifies | Status |
|------|------------------|--------|
| `uses direct API base URL on the server` | **`getServerApiBaseUrl()`** reads **`NEXT_PUBLIC_API_BASE_URL`** | ✅ Passed |
| `returns parsed card detail for current view` | **`fetchCardDetail`** URL + JSON parsing | ✅ Passed |
| `throws CardDetailFetchError on 404` | Typed error with **`status: 404`** | ✅ Passed |
| `preserves HTTP status` | **`CardDetailFetchError.status`** field | ✅ Passed |

**Manual / script validation (required before production sign-off)**

| Check | What to verify | Status |
|-------|----------------|--------|
| Network tab — first Thread load | **No** `/api/cards/{id}` or `/backend/api/cards/{id}` client request before hydration | ⏳ **Manual — see B5** |
| View page source | Card title present in HTML | ⏳ Manual |
| Current/Original toggle | Original triggers client fetch; Current restores without refetch | ⏳ Manual |
| Unknown card ID | Error Alert + Retry (not Next.js 404 page) | ⏳ Manual |
| Production Vercel deploy | **`NEXT_PUBLIC_API_BASE_URL`** → Render HTTPS URL | ⏳ Manual at deploy |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- **None.** SSR consumes existing published card rows via **`GET /api/cards/{id}?view=current`**.

### B2. API / INTEGRATION CONTRACTS

**Server-side fetch (RSC)**

```
GET {NEXT_PUBLIC_API_BASE_URL}/api/cards/{cardId}?view=current
Cache: no-store (until P1.5-S4)
Auth: none (public published card)
```

**Client-side refetch (browser — toggle / retry)**

```
GET {getApiBaseUrl()}/api/cards/{cardId}?view=current|original
  → production browser: /backend/api/cards/{id}?...
Cache: no-store
```

**Response:** existing **`CardDetailResponse`** JSON — no contract change.

**404 response (unchanged backend contract)**

```json
{
  "detail": {
    "code": "card_not_found",
    "message": "Card not found"
  }
}
```

SSR surfaces the raw error text via **`initialError`** → same Alert UX as client-only path.

### B3. BUSINESS LOGIC & RULES (Detailed)

**SSR vs client URL resolution**

| Context | Base URL helper | Production behaviour |
|---------|-----------------|-------------------|
| Server Component | **`getServerApiBaseUrl()`** | `https://<render-service>.onrender.com` |
| Browser client | **`getApiBaseUrl()`** | `/backend` (Vercel rewrite → Render) |
| Local dev (both) | Configured or `http://127.0.0.1:8000` | Direct loopback |

**Hydration skip logic (`useCard`)**

```
On mount / view change:
  IF view === "current" AND initial.data matches cardId → restore SSR data, skip fetch
  ELSE IF view === "current" AND initial.error → show error, skip fetch
  ELSE → load() client fetch

Toggle Original → load()
Toggle back Current → restore initial.data (no fetch)
refetch() → always load()
```

### B4. KNOWN CONSTRAINTS & TECH DEBT

- **`fetchCardDetail` uses `no-store`** — full SSR fetch every navigation until **P1.5-S4** adds ISR/cache headers.
- **Original view never SSR'd** — first toggle to Original always waits on client fetch (acceptable per acceptance criteria).
- **No automated E2E for “zero client fetch on first load”** — Network tab remains the acceptance check for **1.5.6.6**.
- ⚠️ **Production requires `NEXT_PUBLIC_API_BASE_URL` on Vercel** — if unset, SSR falls back to loopback and Thread will error on Vercel.
- **`loading.tsx` only visible when SSR exceeds Next.js streaming threshold** — fast API (S3) may make it rarely seen in production.

### B5. TESTING NOTES

**Manual checklist (run locally before merge/deploy)**

1. **Start stack**
   - Backend: `uvicorn` on port 8000 with valid **`SUPABASE_DB_URL`**
   - Frontend: `pnpm dev` from `frontend/` with root **`.env.local`** loaded (**`NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`**)

2. **First load — no client card fetch**
   - Open DevTools → **Network** → disable cache
   - From Pulse, open a card → **`/thread/{cardId}`**
   - **Expect:** card title + ICE header visible without skeleton flash
   - **Expect:** **no** request to **`/api/cards/`** or **`/backend/api/cards/`** from the client bundle on initial load
   - **Optional:** **View Page Source** — search for the card title; should appear in HTML

3. **Current/Original toggle**
   - Click **Original**
   - **Expect:** **one** client fetch with **`view=original`**
   - Click **Current**
   - **Expect:** content restores instantly; **no** second fetch for Current

4. **Unknown card ID**
   - Navigate to **`/thread/00000000-0000-0000-0000-000000000000`** (or invalid UUID)
   - **Expect:** destructive Alert with error message + Retry link (same as pre-S6)
   - **Expect:** **not** the generic Next.js 404 page

5. **SSR failure fallback**
   - Stop backend; hard-refresh a Thread URL
   - **Expect:** error Alert; **Retry** triggers client fetch when API returns

6. **Mobile navigation from Pulse**
   - Resize to mobile width (< 860px); tap a card on Pulse
   - **Expect:** navigates to Thread with SSR content on first paint

7. **Production (after deploy)**
   - Confirm Vercel env **`NEXT_PUBLIC_API_BASE_URL`** = Render HTTPS URL
   - Repeat Network check on production **`/thread/{knownCardId}`**
   - Verify CORS on **Original toggle** refetch (browser → `/backend` → Render)
   - Run Lighthouse mobile on Thread (target **P1.5-S9/S10**)

| Area | Automated | Manual |
|------|-----------|--------|
| Hydration skip / toggle refetch / Current restore | ✅ Jest | — |
| Zero client fetch first paint | — | ⏳ Network tab |
| 404 error UX preserved | — | ⏳ Manual |
| Production env + Render reachability | — | ⏳ Deploy smoke |
| CORS on toggle refetch | — | ⏳ Production only |

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| `NEXT_PUBLIC_API_BASE_URL` | **Required for SSR** — direct Render URL in production; loopback locally |
| `SUPABASE_DB_URL` | Backend only — card API must be warm/fast (S2+S3 deployed) |
| `CORS_ORIGINS` | Applies to **browser** refetch paths (Original toggle, Retry); SSR server-to-server fetch does not use CORS |

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

- **Start here:** `frontend/app/(app)/thread/[cardId]/page.tsx`, `frontend/lib/api/server.ts`, `frontend/lib/cards/useCard.ts`, `frontend/app/(app)/thread/_components/ThreadExperience.tsx`
- **Client vs server API:** RSC → **`getServerApiBaseUrl()`** + **`fetchCardDetail`**; browser → **`getApiBaseUrl()`**
- **Common mistake:** using **`getApiBaseUrl()`** in Server Components — breaks Vercel SSR
- **Common mistake:** unstable **`initial`** object in **`useCard`** effect deps — infinite refetch loop
- **Common mistake:** expecting Original view on SSR — only Current is server-fetched
- **S4 owner:** when backend **`Cache-Control`** lands, consider **`next: { revalidate: 60 }`** in **`fetchCardDetail`**
- **S7 owner:** Thread components are now SSR-first; dynamic imports should preserve hydrated HTML
- **Ops / platform:** verify Vercel → Render connectivity and env var on every frontend deploy
