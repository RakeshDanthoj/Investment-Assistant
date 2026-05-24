# Cross-phase performance standards (Phase 1.5 → Phase 2 → Phase 3)

**Version:** v0.1 (draft — finalize in Phase 2.5) | **Date:** 23-05-2026  
**Source:** Phase 1.5 remediation (`Phase1_P1.5 - Performance remediation Pulse and Thread.md`, `finnwise-phase1.5-implementation-tasks.md`)  
**Owner:** Riley (harness + CI); all feature devs apply on every user-facing route  
**Exit gate:** `docs/plans/finnwise-phase2.5-implementation-tasks.md` (carries forward open items from **P2-S15**)

---

## Purpose

FinnWise adds many routes in Phase 2 (Mirror, Lens, Map) and Phase 3 (marketing, public Map, billing). This checklist prevents repeating the Phase 1 **client-fetch waterfall** and **~8 s API** failure mode. **P2-S15** authored this doc and extended Lighthouse CI; **Phase 2.5** closes deferred P1.5 benchmarks and green budgets.

---

## Mandatory practices — new or changed routes

### 1. First paint (SSR / RSC)

- [ ] Initial list/detail data fetched in **Server Component** `page.tsx` via `frontend/lib/api/server.ts` (server-to-server; no browser CORS).
- [ ] Pass `initialData` (and `initialError` if needed) into client hooks; hooks **skip first client fetch** when `initialData` matches URL state (see `usePulseFeed`, `useCard`).
- [ ] Use `loading.tsx` + skeleton only when SSR cannot run (missing id, etc.).

### 2. Client refetch only when necessary

- [ ] Filters, view toggles (Current/Original), retry: `fetch(..., { cache: "no-store" })`.
- [ ] Verify `Access-Control-Allow-Origin` for browser calls to `/backend/api/...` (Vercel origin allowed in `backend/app/main.py`).
- [ ] Do not refetch on mount when SSR already hydrated the same query.

### 3. Bundles and fonts

- [ ] `next/dynamic` for heavy below-fold panels, ICE layers, aside widgets (Thread pattern).
- [ ] Scope Playfair/editorial fonts to routes that need them (`frontend/lib/fonts/editorial.ts` + route layout).
- [ ] Avoid pulling full Radix/admin trees into Pulse/Thread/Mirror critical path.

### 4. Backend read paths

- [ ] One pooled DB connection per HTTP request (`backend/app/db/connection.py`).
- [ ] Published feed + card detail: `Cache-Control: private, max-age=60, stale-while-revalidate=300`.
- [ ] Draft/admin/editorial: `no-store` unchanged.

### 5. Measurement (do not fool yourself)

- [ ] **Never** use `next dev` Lighthouse scores for sign-off or PR evidence.
- [ ] Local parity: `cd frontend && pnpm build && pnpm start`, then `pnpm perf:lighthouse` from repo root.
- [ ] CI/production audits use `LIGHTHOUSE_BASE_URL` (Vercel production or agreed preview).

### 6. Automated budgets (CI)

| Profile | Performance | TBT | Speed Index |
|---------|-------------|-----|-------------|
| Mobile | ≥ 90 | &lt; 200 ms | &lt; 3400 ms |
| Desktop | ≥ 90 | &lt; 150 ms | &lt; 2400 ms |

- [ ] Extend `scripts/lighthouse.mjs` when adding a primary `(app)` route (Pulse, Thread, Mirror, Lens, Map, …).
- [ ] Run `pnpm perf:lighthouse:budget-test` when changing `scripts/lighthouse-budget.mjs`.

### 7. API latency (warm)

- [ ] `scripts/bench_api_latency.mjs`: feed + card detail **p95 &lt; 800 ms** on production path(s) documented in PR.
- [ ] Set `BENCH_API_DIRECT_URL` to Render origin for direct vs proxy comparison (`scripts/README.md`).

---

## Phase 2.5 exit criteria (pre–Phase 3; from P2-S15 carry-forward)

See **`docs/plans/finnwise-phase2.5-implementation-tasks.md`** for full stories. Summary:

- [ ] All practices above reflected in Mirror, Lens, Map implementations (audit **P2.5-S5**).
- [ ] Lighthouse JSON archived under `Page Load Performance/` for Pulse, Thread, Mirror, Lens, Map index, Map slug (mobile + desktop).
- [ ] Production bench shows **p95 &lt; 800 ms** OR documented PO re-waiver with root cause (**P2.5-S2**).
- [ ] CI Lighthouse job passes on all Phase 2 routes including `/map/{slug}` when deployed.

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
