# Performance correction — Pulse, Mirror, and shared shell

**Version:** v1.0 | **Date:** 24-05-2026  
**Status:** Ready to execute  
**Owner:** Feature devs + Riley (measurement/CI)  
**Related:** `docs/plans/cross-phase-performance-standards.md`, `docs/Post Implementation documentation/Phase1_P1.5 - Performance remediation Pulse and Thread.md`

---

## Purpose

Close the gap between **good Lighthouse paint scores** and **slow time-to-useful-content** on production (`investment-assistant-frontend.vercel.app`). Pulse already uses SSR from Phase 1.5; Mirror was still on a client-fetch waterfall until the SSR patch in this repo. This plan orders work **high impact + low effort → lower impact + higher effort** and targets every area identified in desktop Lighthouse traces (24-05-2026).

---

## Evidence baseline (desktop, 24-05-2026)

| Route | JSON archive | Perf score | FCP | LCP | Speed Index | Useful content (filmstrip) | Notes |
|-------|----------------|-------------|-----|-----|-------------|----------------------------|--------|
| `/pulse` | `Page Load Performance/investment-assistant-frontend.vercel.app-20260524T164004-desktop-pulse.json` | 98 | 0.4 s | 0.5 s | 1.7 s | ~2.7–3.1 s | No client `/api/feed`; document ~2 s (SSR waits on API). React hydration errors #422/#425 in console. Duplicate `/api/notifications` ~3–5 s. |
| `/mirror` | `Page Load Performance/investment-assistant-frontend.vercel.app-20260524T163039-desktop-mirror.json` | 94 | 0.6 s | 0.7 s | 2.4 s | ~3.7–7.5 s | Four client mirror APIs after JS (~3.4–7 s). Pre-SSR deploy trace. |
| `/thread` | `Page Load Performance/investment-assistant-frontend.vercel.app-20260524T163039-desktop-Thread.json` | (see file) | ~1.0 s | ~1.0 s | ~2.4 s | ~7.9 s | Reference only; Thread remediated in P1.5 — re-verify if regressions suspected. |

**Interpretation:** FCP/LCP measure chrome/skeleton, not the feed or prediction list. Optimize for **filmstrip time to cards** and **document TTFB**, not FCP alone.

---

## Targets (definition of done)

| Area | Target |
|------|--------|
| Perceived load | Feed cards / mirror list visible **< 1.5 s** desktop, **< 2.5 s** mobile (filmstrip) |
| Document TTFB | **< 800 ms** warm when SSR includes feed/mirror data |
| API | `GET /api/feed` and mirror read paths **p95 < 800 ms** on production path (or PO-documented waiver with root cause) |
| Stability | **Zero** React hydration errors (#422/#425) in Lighthouse **errors-in-console** on Pulse and Mirror |
| Lighthouse budgets | Desktop perf **≥ 90**, SI **< 2400 ms**; mobile perf **≥ 90**, SI **< 3400 ms**, TBT **< 200 ms** (`scripts/lighthouse-budget.mjs`) |
| CI | `scripts/lighthouse.mjs` audits **Pulse, Thread, Mirror** |
| Standards | All items in `docs/plans/cross-phase-performance-standards.md` satisfied for Pulse and Mirror |

---

## Execution order (master backlog)

Work top to bottom. Do not skip verification gates between phases.

| # | ID | Task | Impact | Effort | Phase |
|---|-----|------|--------|--------|-------|
| 1 | PC-1.1 | Fix React hydration mismatches | High | Low | 1 |
| 2 | PC-1.4 | Verify Vercel `API_BASE_URL` and URL normalization on server paths | High | Low | 1 |
| 3 | PC-1.2 | Defer and dedupe notification badge fetches | Med–High | Low | 1 |
| 4 | PC-2.2 | Deploy and verify Mirror SSR (`mirrorServer.ts`, `page.tsx`, `MirrorClient`) | High | Low–Med | 2 |
| 5 | PC-1.3 | Mirror: partial refetch on filter change (predictions only) | Med | Low | 1 |
| 6 | PC-3.1 | API bench: direct Render vs Vercel `/backend` proxy | High | Low | 3 |
| 7 | PC-2.1 | Streaming SSR shell (Pulse + Mirror) | High | Med | 2 |
| 8 | PC-2.3 | SSR failure: `initialError` + retry (no silent `null` waterfall) | Med | Low | 2 |
| 9 | PC-3.2 | Feed query / payload optimization | High | Med–High | 3 |
| 10 | PC-3.3 | Mirror combined dashboard API (optional, strong) | High | Med | 3 |
| 11 | PC-3.4 | `Cache-Control` on published read paths | Med | Low | 3 |
| 12 | PC-2.4 | Pulse: single feed render path (reduce duplicate hydration) | Med | Med | 2 |
| 13 | PC-4.1 | Scope editorial fonts per route | Med | Med | 4 |
| 14 | PC-4.2 | Trim unused JS on Pulse critical path | Med | Med | 4 |
| 15 | PC-4.3 | Mirror: `next/dynamic` for below-fold panels | Low–Med | Low | 4 |
| 16 | PC-5.3 | Prefetch policy audit (feed links, RSC) | Low–Med | Low | 5 |
| 17 | PC-6.1 | Extend Lighthouse CI to Mirror | Governance | Low | 6 |
| 18 | PC-6.2 | Archive before/after JSON per milestone | Governance | Low | 6 |
| 19 | PC-6.3 | Document filmstrip “meaningful content” in `scripts/README.md` | Governance | Low | 6 |
| 20 | PC-5.1 | Edge / ISR caching for public feed (if product-safe) | Med | High | 5 |
| 21 | PC-5.2 | Regional colocation (Vercel ↔ Render RTT) | High | High | 5 |

---

## Phase 1 — Quick wins (high impact, low effort)

### PC-1.1 — Fix React hydration mismatches

**Problem:** Pulse Lighthouse shows minified React **#422** / **#425** (text mismatch / hydration failure) → client re-render, flash, wasted work.

**Likely causes:** Locale-dependent dates (`toLocaleTimeString`, `toLocaleString`) differing between server (UTC on Vercel) and browser.

**Files to inspect**

- [ ] `frontend/app/(app)/pulse/_components/Topbar.tsx`
- [ ] `frontend/app/(app)/pulse/_components/InsightPanel.tsx`
- [ ] `frontend/app/(app)/thread/_components/*` (dates)
- [ ] `frontend/app/(app)/mirror/_components/*` (dates)
- [ ] Any `typeof window` branches that change initial HTML

**Implementation options (pick one pattern per surface)**

- [ ] Format timestamps in **UTC** with explicit locale on server and client, or
- [ ] Show “Updated …” **after mount** (placeholder `—` on server), or
- [ ] `suppressHydrationWarning` only on the specific text node (last resort)

**Verification**

- [ ] Lighthouse **errors-in-console** = pass on `/pulse` and `/mirror` (production or `pnpm build && pnpm start`)
- [ ] Manual: hard refresh, no hydration warning in DevTools console

---

### PC-1.2 — Defer and dedupe notification badge fetches

**Problem:** Pulse trace: **two** `GET /backend/api/notifications?limit=50` (~3–5 s), non-blocking but competes right after load.

**Files**

- [ ] `frontend/components/Topbar/NotificationBadge.tsx`
- [ ] Any duplicate callers / strict mode double-mount

**Tasks**

- [ ] Single data source (context or shared hook) with in-flight dedupe
- [ ] Defer first fetch: `requestIdleCallback` or post-`useEffect` tick after paint
- [ ] Skip on routes that hide the badge

**Verification**

- [ ] Network: **one** notifications request per navigation, starts after FCP
- [ ] Badge still updates within acceptable delay (< 2 s after paint)

---

### PC-1.3 — Mirror: partial refetch on filter change

**Problem:** `loadData()` sets full-page `loading` when `?status=` changes → stats and sidebar skeleton unnecessarily.

**Files**

- [ ] `frontend/app/(app)/mirror/_components/MirrorClient.tsx`

**Tasks**

- [ ] On filter change: refetch **predictions only**; keep stats, streak, unread panel visible
- [ ] Optional lightweight row skeleton in list only

**Verification**

- [ ] Toggle filter pills: no full-page skeleton; list updates < 300 ms perceived when API warm

---

### PC-1.4 — Verify server API env and URL normalization

**Problem:** SSR document ~2 s often equals **server waiting on backend**; wrong env adds proxy hop or broken host on one path only.

**Tasks**

- [ ] Confirm Vercel **`API_BASE_URL`** = full Render origin (not bare Supabase ref)
- [ ] Grep: `getServerApiBaseUrl()` used for all RSC fetches (`server.ts`, `mirrorServer.ts`)
- [ ] Compare with `.cursor/rules/incident-triage-decision-tree.md` — partial normalization across paths

**Verification**

- [ ] Log or `Server-Timing` once: feed fetch host + `total_ms` on production
- [ ] `scripts/bench_api_latency.mjs` with `BENCH_API_DIRECT_URL` set (see PC-3.1)

---

## Phase 2 — Perceived load (high impact, medium effort)

### PC-2.1 — Streaming SSR shell (Pulse + Mirror)

**Problem:** Entire HTML blocked until `fetchPulseFeed()` / `fetchMirrorInitialData()` completes → blank filmstrip until ~2–7 s.

**Files**

- [ ] `frontend/app/(app)/pulse/page.tsx`
- [ ] `frontend/app/(app)/mirror/page.tsx`
- [ ] Optional: route-level `loading.tsx` for inner boundary only

**Tasks**

- [ ] Extract async server component: `PulseFeedSection` / `MirrorContentSection` inside `Suspense`
- [ ] Immediate shell: `AppShell` children = topbar + filter UI + skeleton rows (no API)
- [ ] Stream feed/mirror payload when ready

**Verification**

- [ ] Filmstrip: chrome + skeletons **< 500 ms**; cards when API returns
- [ ] No regression to `initialData` skip logic in `usePulseFeed` / `MirrorClient`

---

### PC-2.2 — Mirror SSR (deploy + verify)

**Problem:** Pre-deploy Mirror used client-only waterfall (four APIs after ~3.4 s JS).

**Files (already in repo — verify deployed)**

- [ ] `frontend/lib/api/mirrorServer.ts`
- [ ] `frontend/app/(app)/mirror/page.tsx`
- [ ] `frontend/app/(app)/mirror/_components/MirrorClient.tsx`

**Tasks**

- [ ] Deploy to Vercel
- [ ] Confirm no client calls to `/api/mirror/stats|predictions|streak|notifications/unread` on first load when session present
- [ ] Re-run desktop + mobile Lighthouse; archive JSON

**Verification**

- [ ] Mirror filmstrip useful content **< 4 s** desktop (stretch **< 3 s**)
- [ ] Matches `cross-phase-performance-standards.md` §1 (SSR first paint)

---

### PC-2.3 — SSR failure handling

**Problem:** `catch { initialData = null }` forces client refetch → second waterfall.

**Files**

- [ ] `frontend/app/(app)/pulse/page.tsx`
- [ ] `frontend/app/(app)/mirror/page.tsx`
- [ ] `PulseClient.tsx`, `MirrorClient.tsx`

**Tasks**

- [ ] Pass `initialError` prop; show inline error + retry in shell
- [ ] Do not mount client hook in `loading` state when error is authoritative

**Verification**

- [ ] Simulated 503 from API: shell visible, retry works, no 3 s blank loop

---

### PC-2.4 — Pulse: single feed render path

**Problem:** Mobile uses server `PulseFeedList`; desktop re-renders cards in client — duplicate hydration surface.

**Files**

- [ ] `frontend/app/(app)/pulse/_components/PulseClient.tsx`
- [ ] `frontend/app/(app)/pulse/_components/PulseFeedList.tsx`
- [ ] `frontend/app/(app)/pulse/_components/EventCard.tsx`

**Tasks**

- [ ] Shared presentational `EventCardSurface` only; align server/client markup
- [ ] Avoid hydrating duplicate card text between hidden mobile list and desktop list

**Verification**

- [ ] No hydration warnings on `/pulse` desktop
- [ ] Smaller RSC/hydration payload (optional: compare build trace)

---

## Phase 3 — Backend / API (high impact, medium–high effort)

### PC-3.1 — Benchmark baseline

**Tasks**

- [ ] Run `node scripts/bench_api_latency.mjs` with `LIGHTHOUSE_BASE_URL` and `BENCH_API_DIRECT_URL` (Render)
- [ ] Record p50/p95 for: `/api/feed`, `/api/mirror/predictions`, `/api/cards/{id}`

**Endpoints**

| Endpoint | Direct Render | Vercel `/backend` |
|----------|---------------|-------------------|
| `/api/feed` | | |
| `/api/mirror/predictions` | | |
| `/api/cards/{id}` | | |

**Verification**

- [ ] Numbers pasted in PR or milestone note under `Page Load Performance/`

---

### PC-3.2 — Feed query optimization

**Owner:** Backend / Jordan pattern from P1.5

**Tasks**

- [ ] `EXPLAIN ANALYZE` on feed query path
- [ ] Indexes for filter/sort; eliminate N+1
- [ ] Trim first-paint payload (field selection, sensible default limit)

**Verification**

- [ ] Warm direct Render p95 **< 800 ms** for `/api/feed`
- [ ] Pulse document `networkEndTime` drops proportionally in Lighthouse

---

### PC-3.3 — Mirror dashboard API (optional)

**Problem:** Four parallel mirror calls ≈ wall-clock of slowest (~7 s on proxy trace).

**Tasks**

- [ ] Add `GET /api/mirror/dashboard?status=` → stats + predictions + streak + unread count
- [ ] Single DB session / consolidated queries where possible
- [ ] Update `fetchMirrorInitialData()` to one HTTP call

**Files**

- [ ] `backend/app/api/mirror.py` (or new router)
- [ ] `backend/app/services/mirror_*.py`
- [ ] `frontend/lib/api/mirrorServer.ts`

**Verification**

- [ ] One server fetch on mirror load; p95 < 800 ms warm or documented

---

### PC-3.4 — HTTP caching on read paths

**Tasks**

- [ ] FastAPI: `Cache-Control: private, max-age=60, stale-while-revalidate=300` on published feed + mirror reads
- [ ] Align with `fetch(..., { next: { revalidate: 60 } })` in `server.ts` / `mirrorServer.ts`

**Verification**

- [ ] Response headers present on production `curl -I`
- [ ] Repeat navigation faster (optional WebPageTest)

---

## Phase 4 — Bundle and fonts (medium impact, medium effort)

### PC-4.1 — Scope editorial fonts

**Tasks**

- [ ] Restrict `frontend/lib/fonts/editorial.ts` to Thread / marketing layouts
- [ ] Pulse/Mirror: system or single subset font

**Verification**

- [ ] Fewer woff2 preloads on `/pulse` network waterfall

---

### PC-4.2 — Trim unused JavaScript (Pulse)

**Tasks**

- [ ] Bundle analyzer on production build
- [ ] Keep `next/dynamic` on `InsightPanel`, `FogOfWarBanner`
- [ ] Exclude admin/Radix trees from Pulse graph

**Verification**

- [ ] Lighthouse unused-javascript savings reduced or acceptable

---

### PC-4.3 — Mirror dynamic imports

**Tasks**

- [ ] `next/dynamic` for `ReadyToGradePanel`, `StreakTrackerPanel`, heavy expanded card content

**Verification**

- [ ] Smaller initial JS chunk for `/mirror` route

---

## Phase 5 — Infrastructure (medium–lower impact, higher effort)

### PC-5.1 — Edge / ISR for public feed

**Caution:** Do not cache authenticated mirror data at edge without auth.

**Tasks**

- [ ] Product sign-off on public feed caching
- [ ] Vercel ISR or short TTL edge cache for `/api/feed` equivalent server fetch

---

### PC-5.2 — Regional colocation

**Tasks**

- [ ] Document RTT Vercel region ↔ Render region
- [ ] Evaluate Render region move, or edge read path for feed

---

### PC-5.3 — Prefetch policy audit

**Tasks**

- [ ] Audit `Link prefetch` on `PulseFeedList` (currently `prefetch={false}` — keep unless changed deliberately)
- [ ] Reduce RSC prefetch storm on visible thread links

---

## Phase 6 — Measurement and governance

### PC-6.1 — Lighthouse CI: add Mirror

**Files**

- [ ] `scripts/lighthouse.mjs` — add `mirror` to default `pages`
- [ ] `scripts/lighthouse-budget.mjs` — confirm budgets unchanged unless PO adjusts

**Verification**

- [ ] `pnpm perf:lighthouse` passes Pulse, Thread, Mirror (mobile + desktop)

---

### PC-6.2 — Archive evidence

After each milestone, save:

- [ ] `Page Load Performance/*-{date}-desktop-pulse.json`
- [ ] `Page Load Performance/*-{date}-desktop-mirror.json`
- [ ] Mobile runner JSON from CI

---

### PC-6.3 — Meaningful content in runbook

**Files**

- [ ] `scripts/README.md`

**Content**

- [ ] Do not sign off on `next dev` Lighthouse
- [ ] Record filmstrip time to first card row, not only FCP/LCP
- [ ] Use `pnpm build && pnpm start` before local audits

---

## Milestones

### Milestone A — Stability week (~1 week)

**Includes:** PC-1.1, PC-1.2, PC-1.3, PC-1.4, PC-2.2 deploy, PC-3.1

**Exit checklist**

- [ ] No hydration errors on Pulse/Mirror
- [ ] Mirror SSR live; no client mirror quartet on first load
- [ ] API bench table filled in
- [ ] Notifications: single deferred fetch

---

### Milestone B — Perceived load (~2 weeks)

**Includes:** PC-2.1, PC-2.3, PC-3.2, PC-2.4

**Exit checklist**

- [ ] Streaming shell on Pulse and Mirror
- [ ] Feed p95 trending toward 800 ms or waiver documented
- [ ] Filmstrip targets met on desktop Pulse/Mirror

---

### Milestone C — Polish and governance (~ongoing)

**Includes:** PC-3.3, PC-3.4, PC-4.x, PC-6.x, PC-5.x as needed

**Exit checklist**

- [ ] Lighthouse CI includes Mirror
- [ ] All `cross-phase-performance-standards.md` checkboxes satisfied for Pulse + Mirror

---

## Per-task verification (always)

```bash
cd frontend && pnpm build && pnpm start
# separate terminal, from repo root:
pnpm perf:lighthouse
# optional:
node scripts/bench_api_latency.mjs
```

- [ ] **errors-in-console** audit clean on `/pulse` and `/mirror`
- [ ] No client `/api/feed` on Pulse first load when SSR succeeded
- [ ] No client `/api/mirror/*` quartet on Mirror first load when SSR succeeded
- [ ] pytest + mirror/pulse Jest green

---

## References

| Doc / script | Role |
|--------------|------|
| `docs/plans/cross-phase-performance-standards.md` | Mandatory practices for all routes |
| `docs/Post Implementation documentation/Phase1_P1.5 - Performance remediation Pulse and Thread.md` | P1.5 evidence and PO sign-off |
| `scripts/lighthouse.mjs` | CI runner |
| `scripts/lighthouse-budget.mjs` | Budget thresholds |
| `scripts/bench_api_latency.mjs` | API p50/p95 |
| `scripts/README.md` | Operator guide |
| `.cursor/rules/incident-triage-decision-tree.md` | Env URL format / partial normalization |

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 24-05-2026 | v1.0 | Initial plan from Lighthouse 24-05-2026 Pulse/Mirror traces + P1.5 standards |
