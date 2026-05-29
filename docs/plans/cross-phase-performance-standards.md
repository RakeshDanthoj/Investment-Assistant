# Cross-phase performance standards (Phase 1.5 → Phase 2 → Phase 3)

**Version:** v1.0 | **Date:** 30-05-2026  
**Source:** Phase 1.5 remediation (`Phase1_P1.5 - Performance remediation Pulse and Thread.md`, `finnwise-phase1.5-implementation-tasks.md`)  
**Owner:** Riley (harness + CI); all feature devs apply on every user-facing route  
**Exit gate:** `docs/plans/finnwise-phase2.5-implementation-tasks.md` (carries forward open items from **P2-S15**)

---

## Purpose

FinnWise adds many routes in Phase 2 (Mirror, Lens, Map) and Phase 3 (marketing, public Map, billing). This checklist prevents repeating the Phase 1 **client-fetch waterfall** and **~8 s API** failure mode. **P2-S15** authored this doc and extended Lighthouse CI; **Phase 2.5** closes deferred P1.5 benchmarks and green budgets.

---

## Mandatory practices — new or changed routes

### 1. First paint (SSR / RSC)

- [x] Initial list/detail data fetched in **Server Component** `page.tsx` via `frontend/lib/api/server.ts` (server-to-server; no browser CORS).
- [x] Pass `initialData` (and `initialError` if needed) into client hooks; hooks **skip first client fetch** when `initialData` matches URL state (see `usePulseFeed`, `useCard`).
- [x] Use `loading.tsx` + skeleton only when SSR cannot run (missing id, etc.).

### 2. Client refetch only when necessary

- [x] Filters, view toggles (Current/Original), retry: `fetch(..., { cache: "no-store" })`.
- [x] Verify `Access-Control-Allow-Origin` for browser calls to `/backend/api/...` (Vercel origin allowed in `backend/app/main.py`).
- [x] Do not refetch on mount when SSR already hydrated the same query.

### 3. Bundles and fonts

- [x] `next/dynamic` for heavy below-fold panels, ICE layers, aside widgets (Thread pattern).
- [x] Scope Playfair/editorial fonts to routes that need them (`frontend/lib/fonts/editorial.ts` + route layout).
- [x] Avoid pulling full Radix/admin trees into Pulse/Thread/Mirror critical path.

### 4. Backend read paths

- [x] One pooled DB connection per HTTP request (`backend/app/db/connection.py`).
- [x] Published feed + card detail: `Cache-Control: private, max-age=60, stale-while-revalidate=300`.
- [x] Draft/admin/editorial: `no-store` unchanged.

### 5. Measurement (do not fool yourself)

- [x] **Never** use `next dev` Lighthouse scores for sign-off or PR evidence.
- [x] Local parity: `cd frontend && pnpm build && pnpm start`, then `pnpm perf:lighthouse` from repo root.
- [x] CI/production audits use `LIGHTHOUSE_BASE_URL` (Vercel production or agreed preview).

### 6. Automated budgets (CI)

| Profile | Performance | TBT | Speed Index |
|---------|-------------|-----|-------------|
| Mobile | ≥ 90 | &lt; 200 ms | &lt; 3400 ms |
| Desktop | ≥ 90 | &lt; 150 ms | &lt; 2400 ms |

- [x] Extend `scripts/lighthouse.mjs` when adding a primary `(app)` route (Pulse, Thread, Mirror, Lens, Map, …).
- [x] Run `pnpm perf:lighthouse:budget-test` when changing `scripts/lighthouse-budget.mjs`.

### 7. API latency (warm)

- [x] `scripts/bench_api_latency.mjs`: feed + card detail **p95 &lt; 800 ms** on production path(s) documented in PR — **PO waiver** (30 May 2026 proxy p95 **1298 / 1350 ms**); see [P2.5-S6 close-out](../Post%20Implementation%20documentation/Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md) and [P2.5-S2](../Post%20Implementation%20documentation/Phase2.5_P2.5-S2%20-%20API%20latency%20feed%20and%20card.md).
- [x] Set `BENCH_API_DIRECT_URL` to Render origin for direct vs proxy comparison (`scripts/README.md`).

---

## Phase 2 route audit (P2.5-S5 — 30 May 2026)

Audit scope: §1–§4 per route. **Pass** = meets standard; **Partial** = acceptable exception documented; **Fail** = gap filed or fixed in Phase 2.5.

| Route | §1 SSR / RSC | §2 Client refetch | §3 Bundles / fonts | §4 Backend reads | Notes / issue link |
|-------|--------------|-------------------|--------------------|------------------|-------------------|
| `/mirror` | **Pass** | **Pass** | **Pass** | **Pass** | `MirrorContentSection` + `fetchMirrorInitialData` (`mirrorServer.ts`); `hydratedFromServer` skips mount fetch; `next/dynamic` sidebar panels; no editorial fonts on layout. [P2.5-S3](../Post%20Implementation%20documentation/Phase2.5_P2.5-S3%20-%20Mobile%20Lighthouse%20Mirror.md) |
| `/lens` | **Partial** | **Pass** | **Pass** | **N/A** | Interactive surface: SSR **static shell** (`LensTopbar` + `LensContentSection` / `Suspense`); query history deferred via `deferAfterPaint` (not blocking first paint). ICE layers `next/dynamic` in `ResultCard`. Editorial fonts scoped in `lens/layout.tsx`. [P2.5-S5](../Post%20Implementation%20documentation/Phase2.5_P2.5-S5%20-%20Phase%202%20route%20perf%20audit.md) |
| `/map` | **Pass** | **Pass** | **Partial** | **Pass** | `fetchMapSectorList` in `page.tsx`; props-only `MapIndexClient`. No `next/dynamic` (light grid); acceptable at index. Auth map reads use `no-store` (correct). |
| `/map/{slug}` | **Pass** | **Pass** | **Partial** | **Pass** | `fetchMapSectorDetail` SSR; `MapSectorClient` no mount refetch. Optional follow-up: `next/dynamic` for `SensitivityMatrix` if mobile TBT regresses — **P2.5-S4**. Deploy verified in [P2.5-S1](../Post%20Implementation%20documentation/Phase2.5_P2.5-S1%20-%20Map%20production%20deploy.md). |
| `/settings/email` | **N/A** (light) | **Pass** | **Pass** | **N/A** | Auth gate in RSC; `EmailPrefsForm` client-only. Root `Inter` only; no editorial font layout. |

**Pulse / Thread** (Phase 1.5 reference implementations): audited in [Phase1_P1.5](../Post%20Implementation%20documentation/Phase1_P1.5%20-%20Performance%20remediation%20Pulse%20and%20Thread.md); remain the patterns for SSR + dynamic ICE.

### Open gaps (not silent)

| Gap | Owner | Status |
|-----|-------|--------|
| API feed/card warm p95 &lt; 800 ms on production | Jordan / P2.5-S2 | **Closed** — PO waiver in [P2.5-S6 close-out](../Post%20Implementation%20documentation/Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md) (30 May bench) |
| Mobile Lighthouse: Mirror, Thread, Lens | Sam / P2.5-S3, S4 | Thread **pass** 29 May; Mirror **variance**; Lens **SI fail** — see close-out |
| Map `SensitivityMatrix` code-split | Sam / P2.5-S4 | Optional if trace shows heavy chunk |

---

## Phase 2.5 exit criteria (pre–Phase 3; from P2-S15 carry-forward)

See **`docs/plans/finnwise-phase2.5-implementation-tasks.md`** for full stories. Summary:

- [x] All practices above reflected in Mirror, Lens, Map implementations (audit **P2.5-S5**).
- [x] Lighthouse JSON archived under `Page Load Performance/` for Pulse, Thread, Mirror, Lens, Map index, Map slug (mobile + desktop) — **P2.5-S6** (29 May 2026).
- [x] Production bench shows **p95 &lt; 800 ms** OR documented PO re-waiver with root cause (**P2.5-S2** — proxy p95 **1298 / 1350 ms**; [close-out](../Post%20Implementation%20documentation/Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md)).
- [ ] CI Lighthouse job passes on all Phase 2 routes including `/map/{slug}` when deployed — **P2.5-S6** (mobile Lens SI + Mirror variance; desktop green).

---

## Phase 3 carry-forward

- [ ] **P3-S5** SLOs (`docs/plans/phase3-slos.md`) align with this doc (Pulse p95 &lt; 800 ms, etc.).
- [ ] **P3-S8** go/no-go checklist includes “cross-phase performance standards satisfied.”
- [ ] New **marketing** and **public Map** routes: Lighthouse + k6 before `phase3-gate: green`.
- [ ] No new surface ships without SSR-first or explicit PO exception.

---

## References

| Doc / script | Role |
|--------------|------|
| `scripts/README.md` | Bench + Lighthouse operator guide |
| `scripts/lighthouse.mjs` | CI runner |
| `scripts/bench_api_latency.mjs` | API p50/p95 |
| `docs/Post Implementation documentation/Phase1_P1.5 - Performance remediation Pulse and Thread.md` | Phase 1.5 evidence + PO sign-off |
| `docs/Post Implementation documentation/Phase2.5_P2.5-S5 - Phase 2 route perf audit.md` | P2.5-S5 audit evidence |
