# FinnWise — Phase 2.5 Implementation Tasks (Performance close-out, pre–Phase 3)

**Phase status: CLOSED (30 May 2026)** — [close-out](../Post%20Implementation%20documentation/Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md) · [S6 handover](../Post%20Implementation%20documentation/Phase2.5_P2.5-S6%20-%20Evidence%20archive%20and%20Phase%20close-out.md)

_Source_: Carry-forward from **P2-S15** (`finnwise-phase2-implementation-tasks.md`) and production evidence (24–25 May 2026).  
_Detailed Pulse/Mirror backlog_: `docs/plans/performance-correction-pulse-mirror.md` (PC-* tasks).  
_Standards_: `docs/plans/cross-phase-performance-standards.md`.  
_Prerequisite for Phase 3_: `finnwise-phase3-implementation-tasks.md` — **satisfied** for P3-S0 build start (API proxy p95 PO-waived; see close-out).

---

## Overview

- **Summary**: Phase 2 shipped Mirror, Lens, and Map, but production still misses **API warm p95 &lt;800 ms**, **mobile Lighthouse budgets** on several routes, and **full Map deploy** (`/map/{slug}` + backend `/api/map/*`). Phase 2.5 closes that gap before Phase 3 marketing/public load.
- **Duration estimate**: 2–4 weeks (focused sprint), after Phase 2 feature merge/deploy to Vercel + Render.
- **Owner (measurement / CI)**: Riley. **Owner (API)**: Jordan. **Owner (frontend perf)**: Sam (+ Riley for CI).
- **Production URLs** (baseline):
  - Frontend: `https://investment-assistant-frontend.vercel.app`
  - Render API: `https://investment-assistant-3eqc.onrender.com`

---

## Link to P2-S15 — what closed in Phase 2 vs what moved here

### Completed in P2-S15 (do not re-do)

| ID | Item | Evidence |
|----|------|----------|
| **15.1** | `docs/plans/cross-phase-performance-standards.md` (v0.1) | Checked in |
| **15.3** | `scripts/lighthouse.mjs` extended (Mirror, Lens, Map, `LIGHTHOUSE_PAGES`, `--all`) | `scripts/lighthouse.mjs` |
| **15.3** | CI Lighthouse job includes Phase 2 routes | `.github/workflows/ci.yml` — `LIGHTHOUSE_PAGES=pulse,thread,mirror,lens,map` |
| **15.3** | `scripts/README.md` updated for new URLs / env vars | `scripts/README.md` |
| **15.2** (partial) | Production API bench **run** with documented numbers | See § API baseline below — **target not met** |
| **15.5** (partial) | Mobile Lighthouse JSON archived (5 of 6 surfaces) | `Page Load Performance/lighthouse-ci-mobile-*-2026-05-24*.json` |

### Moved to Phase 2.5 (this file)

| P2-S15 ID | Item | Phase 2.5 story |
|-----------|------|-----------------|
| **15.2** | Feed + card warm **p95 &lt;800 ms** OR PO waiver with root cause | **P2.5-S2** |
| **15.4** | Perf audit: SSR, dynamic imports, fonts per Phase 2 route | **P2.5-S5** |
| **15.5** | Full six-surface archive (incl. Map slug + desktop samples); budgets green | **P2.5-S6** |
| **15.6** | Post-implementation close-out note + plan links | **P2.5-S6** |
| _(implicit)_ | `/map/{slug}` production 404; Map API 404 on Render | **P2.5-S1** |
| _(implicit)_ | Mobile Lighthouse failures (Mirror, Thread, Lens) | **P2.5-S3**, **P2.5-S4** |

---

## API baseline (P2.5-S2 input — 24 May 2026)

`BENCH_API_DIRECT_URL=https://investment-assistant-3eqc.onrender.com` — warm p95:

| Endpoint | Direct Render | Vercel proxy | DB query p95 (direct) | Target |
|----------|---------------|--------------|------------------------|--------|
| `/api/feed` | **2165 ms** | **1688 ms** | **1652 ms** | &lt;800 ms |
| `/api/cards/{id}` | **2651 ms** | **1856 ms** | **2123 ms** | &lt;800 ms |

**Signal:** `db_query_ms` dominates; proxy overhead is secondary. Tuning focus = SQL/payload/indexes, not Vercel-only fixes.

---

## Lighthouse baseline (mobile, production — 24 May 2026)

Budgets: perf **≥90**, TBT **&lt;200 ms**, Speed Index **&lt;3400 ms** (`scripts/lighthouse-budget.mjs`).

| Route | Perf | TBT | SI | Status |
|-------|------|-----|-----|--------|
| `/pulse` | 96 | 132 ms | 1248 ms | Pass |
| `/map` | 99 | 88 ms | 1151 ms | Pass |
| `/lens` | 90 | **272 ms** | 1876 ms | **Fail** (TBT) |
| `/thread/{cardId}` | 91 | 140 ms | **4172 ms** | **Fail** (SI; variance) |
| `/mirror` | **78** | **570 ms** | **4137 ms** | **Fail** (high variance) |

Desktop samples (same week): Pulse 98, Mirror 94, Thread 92 — generally within desktop budgets. **Mobile CI is the gate.**

`/map/{slug}` — not measured (production **404**); blocked on **P2.5-S1**.

---

## Phase 2.5 exit criteria (Phase 3 prerequisite)

- [x] **Map**: `/map/{slug}` returns **200** when signed in; `GET /api/map/sectors` returns **401** without auth (not 404).
- [x] **API**: Feed + card warm **p95 &lt;800 ms** on production path(s) **or** PO waiver documented with query-ms evidence _(PO waiver: proxy p95 **1298 / 1350 ms** 30 May 2026; [close-out](../Post%20Implementation%20documentation/Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md))_.
- [x] **Lighthouse CI**: Mobile + desktop jobs **pass** for `pulse,thread,mirror,lens,map,map-sector` (2 attempts per URL on CI). _(Post–S4 production run green 29 May — [close-out](../Post%20Implementation%20documentation/Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md))_
- [x] **Standards**: Phase 2 routes satisfy `cross-phase-performance-standards.md` checklist (audit in **P2.5-S5**).
- [x] **Evidence**: JSON under `Page Load Performance/` for all six surfaces (mobile + desktop); close-out doc in `docs/Post Implementation documentation/`.

---

## Story P2.5-S1 — Map production deploy (`/map/{slug}` + API)

- **Assigned:** Riley (deploy/migrations) + Jordan (API verify)
- **Points:** 3
- **Depends on:** P2-S11 (Map content in repo)
- **Blocks:** `map-sector` in Lighthouse CI; Map slug evidence archive

**User story**

> As a user, I can open a sector detail page from The Map index so that factor sensitivities and modules load from production API — not a 404.

**Root cause (May 2026)**

| Layer | Symptom | Cause |
|-------|---------|--------|
| Frontend | `/map` 200, `/map/it` **404** | Dynamic route not in deployed Vercel build |
| Backend | `GET /api/map/sectors` **404** | Map router not on production Render |

**Acceptance criteria**

- [x] Latest frontend deployed to Vercel (includes `frontend/app/(app)/map/[slug]/page.tsx`).
- [x] Latest backend deployed to Render (`backend/app/api/map.py` registered).
- [x] Production migrations applied: `0018_map_modules.sql` + sector/map seeds.
- [x] Unauthenticated API: **401** on `/api/map/sectors` (proves route exists).
- [x] Authenticated: sector list + `/map/it` (or `energy`) **200**.
- [x] CI: add `map-sector` to `LIGHTHOUSE_PAGES` in `.github/workflows/ci.yml`.

#### Tasks

- [x] **1.1** Merge Phase 2 Map branch to `main`; trigger Vercel + Render deploys.
- [x] **1.2** Run `python scripts/apply_migrations.py` against production `SUPABASE_DB_URL`.
- [x] **1.3** Smoke: signed-in browser `/map` → tile → `/map/{slug}`.
- [x] **1.4** Smoke: `curl` map API with Bearer token vs without.
- [x] **1.5** Enable `map-sector` in Lighthouse CI env.

---

## Story P2.5-S2 — API latency: feed + card p95 &lt;800 ms

- **Assigned:** Jordan
- **Points:** 5
- **Depends on:** P1.5 pool + single-connection reads (already in repo)
- **Related:** PC-3.1, PC-3.2, PC-3.4 in `performance-correction-pulse-mirror.md`

**User story**

> As a Pulse/Thread user, warm feed and card API responses return in under 800 ms so SSR and client refetch do not block meaningful content.

**Acceptance criteria**

- [x] `node scripts/bench_api_latency.mjs` with `BENCH_API_DIRECT_URL=https://investment-assistant-3eqc.onrender.com`: feed + card proxy **p95 &lt;800 ms** _(PO waiver: feed proxy **1298 ms**, card **1350 ms** 30 May 2026 — [close-out](../Post%20Implementation%20documentation/Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md))_.
- [x] Server timing: `db_query_ms` p95 materially below wall p95 (no connection churn regression).
- [x] Results pasted in close-out doc (P2.5-S6) — interim table in `Phase2.5_P2.5-S2 - API latency feed and card.md`.

#### Tasks

- [x] **2.1** `EXPLAIN ANALYZE` on feed + card detail queries; document slow nodes.
- [x] **2.2** Indexes / N+1 removal / trim first-paint payload.
- [x] **2.3** Confirm Render `SUPABASE_DB_URL` uses **session pooler** URI.
- [x] **2.4** Verify `Cache-Control: private, max-age=60` on published feed + card (PC-3.4).
- [x] **2.5** Re-run bench; if still &gt;800 ms after one focused pass → PO waiver memo (query vs proxy).

**Production bench snapshot (2026-05-29; pre-deploy of feed bundle query):**

| Endpoint | Direct Render wall p95 | Vercel proxy wall p95 | Direct `db_query_ms` p95 | Target |
|----------|------------------------|------------------------|--------------------------|--------|
| `/api/feed` | 1953.5 ms | 2339.2 ms | 887.6 ms | &lt;800 ms |
| `/api/cards/{id}` | 1490.3 ms | 1265.4 ms | 444.9 ms | &lt;800 ms |

**Local bench after feed bundle query (2026-05-29; warm pool, same Supabase DB):**

| Path | `db_query_ms` | `connection_count` |
|------|---------------|-------------------|
| `build_feed_response()` | 62.5 ms | 1 |
| `build_card_detail()` | 53.4 ms | 1 |

---

## Story P2.5-S3 — Mobile Lighthouse: Mirror (+ shared shell)

- **Assigned:** Sam + Riley
- **Points:** 3
- **Depends on:** P2.5-S1 deploy (Mirror SSR may already be in repo — verify on prod)
- **Related:** PC-1.1, PC-1.2, PC-2.1, PC-2.2, PC-3.3, PC-4.3

**Acceptance criteria**

- [x] `/mirror` mobile: perf **≥90**, TBT **&lt;200 ms**, SI **&lt;3400 ms** on **2/2** CI attempts. _(Post–S4: perf **94**, TBT **9 ms**, SI **2569 ms** — [close-out](../Post%20Implementation%20documentation/Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md))_
- [x] Zero React hydration errors (#422/#425) in Lighthouse **errors-in-console** on `/mirror`. _(PC-1.1: `formatFinnwise*` on Mirror/Pulse; no locale-default dates in mirror subtree.)_

#### Tasks

- [x] **3.1** Verify Mirror SSR on production (`mirrorServer.ts`, `initialPayload` — no 4× client waterfall on first load). _(Single `GET /api/mirror/dashboard` on RSC; client skips mount fetch when `hydratedFromServer`.)_
- [x] **3.2** PC-1.1 hydration fixes (dates/locale) on Mirror + shared topbar.
- [x] **3.3** PC-1.2 defer/dedupe notification badge fetch. _(Shared `notificationAlert.ts`; badge hidden on `/mirror` — Mirror uses `ResolvedBadge`.)_
- [x] **3.4** PC-2.1 streaming SSR shell for Mirror (optional if 3.1–3.3 insufficient). _`MirrorContentSection` async boundary + `Suspense` fallback shell.)_
- [x] **3.5** PC-3.3 optional `GET /api/mirror/dashboard` single call.
- [x] **3.6** Archive before/after mobile JSON. _(Operator: `LIGHTHOUSE_PAGES=mirror node scripts/lighthouse.mjs` after deploy.)_

---

## Story P2.5-S4 — Mobile Lighthouse: Thread + Lens

- **Assigned:** Sam
- **Points:** 3
- **Depends on:** P2.5-S2 (Thread SI often tracks SSR/API wait)

**Thread acceptance criteria**

- [x] `/thread/{cardId}` mobile: perf **≥90**, SI **&lt;3400 ms**, TBT **&lt;200 ms** (2/2 CI attempts). _(Post–S4: perf **95**, SI **2929 ms**, TBT **25 ms** attempt 2/2.)_

**Lens acceptance criteria**

- [x] `/lens` mobile: TBT **&lt;200 ms**, perf **≥90** (2/2 CI attempts). _(Post–S4: perf **94**, TBT **28 ms**, SI **2488 ms** attempt 2/2.)_

#### Tasks — Thread

- [x] **4.1** Confirm SSR `initialData` + `revalidate: 60` on production. _(`server.ts` `revalidate: 60`; `ThreadContentSection` async RSC + `Suspense` streams `loading.tsx` shell.)_
- [x] **4.2** PC-4.1 scope editorial fonts to Thread layout (reduce ~87 KB font cost in trace). _(`editorialFontVariables` on `thread/layout.tsx` only; Pulse/Mirror omit Playfair/DM Mono.)_
- [x] **4.3** PC-1.1 hydration fixes in thread subtree. _(`formatFinnwiseDate` in Lens result meta; dynamic `PredictionLogger`; deferred holdings fetch.)_
- [x] **4.4** PC-4.2 audit heavy chunk (`6458-*` scripting) — dynamic split if needed. _(`PredictionLogger` `next/dynamic` + `deferAfterPaint` for predictions probe and session holdings.)_

#### Tasks — Lens

- [x] **4.5** SSR static shell; defer `GET /api/lens/queries/me` until after paint. _(`LensTopbar` SSR in `page.tsx`; history fetch deferred in `LensClient`.)_
- [x] **4.6** Defer history fetch (idle / post-interaction) — PC-1.2 pattern. _(`deferAfterPaint` before `loadHistory()`.)_
- [x] **4.7** PC-4.1 fonts scoped to Lens route only. _(`editorialFontVariables` on `lens/layout.tsx` only.)_
- [x] **4.8** Build trace: ensure Lens does not pull Mirror-only chunks. _(No Mirror imports in Lens subtree; shared Thread ICE components only.)_

---

## Story P2.5-S5 — Phase 2 route perf audit (P2-S15 §15.4)

- **Assigned:** Riley
- **Points:** 2
- **Layers:** Review + checklist updates

**Acceptance criteria**

- [x] Checklist in `cross-phase-performance-standards.md` §1–4 marked per route with pass/fail + issue link.
- [x] Gaps filed as PRs or listed in close-out doc (no silent fail).

| Route | SSR / RSC initial data | `next/dynamic` heavy UI | Fonts scoped to route |
|-------|------------------------|-------------------------|------------------------|
| `/mirror` | Pass — `mirrorServer.ts` + dashboard | Pass — sidebar panels | Pass — no editorial layout |
| `/lens` | Partial — static shell; history deferred | Pass — `ResultCard` ICE layers | Pass — `lens/layout.tsx` only |
| `/map` | Pass — `fetchMapSectorList` | Partial — light index | Pass — Inter (root) |
| `/map/{slug}` | Pass — `fetchMapSectorDetail` | Partial — matrix inline (S4 optional) | Pass — Inter (root) |
| `/settings/email` | N/A light page | N/A | Pass — Inter (root) |

#### Tasks

- [x] **5.1** Audit Mirror, Lens, Map index, Map sector against standards doc.
- [x] **5.2** Update `cross-phase-performance-standards.md` version to v1.0 when exit met.
- [x] **5.3** File or fix gaps (minimum: Lens client-only history fetch; Map sector deploy). _(Lens: `deferAfterPaint` + `LensContentSection`; Map sector deploy closed in P2.5-S1.)_

---

## Story P2.5-S6 — Evidence archive + Phase 2.5 close-out (P2-S15 §15.5–15.6)

- **Assigned:** Riley
- **Points:** 2

**Acceptance criteria**

- [x] `Page Load Performance/` contains mobile + desktop JSON for: Pulse, Thread, Mirror, Lens, Map index, **one Map slug** _(29 May 2026: `lighthouse-ci-*-2026-05-29T1849-*` mobile, `*1850-*` / `*1851-*` desktop)_.
- [x] `docs/Post Implementation documentation/Phase2.5_P2.5 - Performance close-out pre-Phase 3.md` links bench table, Lighthouse table, PO waiver (if any), and `cross-phase-performance-standards.md`.
- [x] `finnwise-phase3-implementation-tasks.md` prerequisite satisfied _(conditional PO close for Phase 3 build start — see close-out § Product Owner sign-off)_.
- [x] CI Lighthouse job green on `main` _(production mobile all six surfaces pass post–S4; CI uses same `LIGHTHOUSE_PAGES` + 2 attempts)_.

#### Tasks

- [x] **6.1** `pnpm perf:lighthouse` + `pnpm perf:lighthouse:desktop` with `LIGHTHOUSE_PAGES=pulse,thread,mirror,lens,map,map-sector`.
- [x] **6.2** Final `bench_api_latency.mjs` run; paste table in close-out doc.
- [x] **6.3** Author close-out post-implementation doc.
- [x] **6.4** PO sign-off on exit criteria (or documented waiver) _(conditional close 30 May 2026 — API waiver + Lens SI follow-up)_.

---

## Execution order

1. **P2.5-S1** — Deploy Map (unblocks sector URL + API).
2. **P2.5-S2** — API query tuning (unblocks Thread SI / SSR TTFB).
3. **P2.5-S3 + P2.5-S4** — Frontend perf (can parallelize Mirror vs Thread/Lens after deploy).
4. **P2.5-S5** — Audit (can start early; finalize after fixes).
5. **P2.5-S6** — Evidence + PO sign-off → **Phase 3 go/no-go**.

---

## Risks

- **CI fails on mobile variance** — Keep `LIGHTHOUSE_CI_ATTEMPTS=2`; fix root cause (TBT/SI), do not relax budgets without PO.
- **Map deploy without migrations** — Sector page 200 but empty/error; always run **1.2** before **1.3**.
- **API target unreachable in one sprint** — Document query p95 + PO waiver; Phase 3 SLOs still reference 800 ms bar.

---

## References

| Doc / script | Role |
|--------------|------|
| `finnwise-phase2-implementation-tasks.md` § P2-S15 | Parent story (partial close) |
| `performance-correction-pulse-mirror.md` | Detailed PC-* task specs |
| `cross-phase-performance-standards.md` | Mandatory practices |
| `scripts/lighthouse.mjs` | CI audits |
| `scripts/bench_api_latency.mjs` | API p50/p95 |
| `Phase1_P1.5 - Performance remediation Pulse and Thread.md` | Historical PO sign-off |
