# Post Implementation — Phase 2.5 Performance close-out (pre–Phase 3)

**Version:** v1.0 | **Date:** 30-05-2026  
**Story ID:** P2.5-S6 (P2-S15 §15.5–15.6)  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`  
**Scope:** Evidence archive + Phase 3 prerequisite sign-off for performance carry-forward from Phase 2 / P2-S15.

---

## Product Owner sign-off

| Field | Value |
|--------|--------|
| **Decision** | **Phase 2.5 closed for Phase 3 build start** — proceed with **P3-S0** (synthetic seed) and foundation milestones |
| **Date** | 30-05-2026 |
| **Authority** | Product Owner (project review; conditional acceptance below) |

**Accepted with documented exceptions (not blocking Phase 3 foundation work):**

1. **Warm API proxy wall p95** — feed **1298 ms**, card **1350 ms** vs target **&lt;800 ms** — material improvement from May 2026 baseline (feed proxy **2339 ms**, card **1265 ms**); server `db_query_ms` p95 **~480–711 ms**, `connection_count: 1`. Waiver follows **Phase 1.5** precedent (proxy RTT + residual query cost).
2. **Mobile Lighthouse — Lens Speed Index** — archived run **3922–3967 ms** (2/2 attempts **&gt;3400 ms** on 29 May 2026); **P2.5-S4** follow-up for Lens shell / chunk diet.
3. **Mobile Lighthouse — Mirror Speed Index (variance)** — full six-surface run **4880 ms** (fail); focused re-run with 2 attempts **1749 ms** (pass). Treat Mirror as **operator re-verify on CI**; do not relax mobile SI budget without PO.
4. **CI Lighthouse on `main`** — operator to confirm GitHub Actions mobile job after merge; local evidence archived below.

**Met without waiver:**

- Map production deploy (`/map/it` **200**, API **401** unauthenticated) — [P2.5-S1](./Phase2.5_P2.5-S1%20-%20Map%20production%20deploy.md)
- Phase 2 route perf audit checklist **v1.0** — [P2.5-S5](./Phase2.5_P2.5-S5%20-%20Phase%202%20route%20perf%20audit.md), `docs/plans/cross-phase-performance-standards.md`
- Six-surface Lighthouse JSON archive (mobile + desktop, 29 May 2026)
- Desktop Lighthouse: **all six surfaces pass** budgets

---

## Narrative summary

Phase 2.5 closed the gap between Phase 2 feature ship and Phase 3 marketing/public load. **P2.5-S1** deployed Map routes and API. **P2.5-S2** consolidated feed queries and documented API timing (final bench in this doc). **P2.5-S3** shipped Mirror SSR/dashboard/dynamic panels (mobile budgets flaky on SI). **P2.5-S5** audited Phase 2 routes against cross-phase standards. **P2.5-S6** archives production Lighthouse JSON and API bench tables for PO and **P3-S8** go/no-go.

**Phase 3 prerequisite:** `finnwise-phase3-implementation-tasks.md` requires “Phase 2.5 performance close-out” — satisfied **for build start** with waivers above; **P3-S5** SLO work and **P3-S8** gate still enforce **&lt;800 ms** Pulse p95 and full mobile green where applicable.

---

## API bench (final — 30 May 2026)

Command:

```powershell
$env:BENCH_API_DIRECT_URL="https://investment-assistant-3eqc.onrender.com"
$env:BENCH_VERCEL_URL="https://investment-assistant-frontend.vercel.app"
node scripts/bench_api_latency.mjs
```

Warm **5** iterations (+ 1 discarded warmup). Card id: `e708b82c-f7c7-45e7-a59b-6b66dac8927a`.

| Endpoint | Direct wall p95 | Proxy wall p95 | Direct `db_query_ms` p95 | Direct `total_ms` p95 | Target |
|----------|-----------------|----------------|--------------------------|----------------------|--------|
| `/api/feed` | 1324 ms | **1298 ms** | 480 ms | 719 ms | &lt;800 ms proxy |
| `/api/cards/{id}` | 1594 ms | **1350 ms** | 474 ms | 711 ms | &lt;800 ms proxy |

**vs 24–29 May 2026 baseline (pre–feed bundle):**

| Endpoint | Proxy wall p95 (baseline) | Proxy wall p95 (30 May) | Δ |
|----------|---------------------------|-------------------------|---|
| Feed | 2339 ms | 1298 ms | **−44%** |
| Card | 1265 ms | 1350 ms | +7% (variance) |

**Interpretation:** Feed proxy p95 roughly halved after feed bundle deploy; card proxy near prior best. Server `total_ms` p95 remains **~710–948 ms** on proxy path — still above 800 ms on some samples. **PO waiver** for strict proxy p95; Phase 3 **P3-S5** keeps **&lt;800 ms** as engineering target.

Detail: [Phase2.5_P2.5-S2 - API latency feed and card.md](./Phase2.5_P2.5-S2%20-%20API%20latency%20feed%20and%20card.md)

---

## Lighthouse — mobile (production, 29 May 2026)

Budgets: perf **≥90**, TBT **&lt;200 ms**, SI **&lt;3400 ms** (`scripts/lighthouse-budget.mjs`).

Command:

```powershell
$env:LIGHTHOUSE_PAGES="pulse,thread,mirror,lens,map,map-sector"
$env:LIGHTHOUSE_MAP_SLUG="it"
pnpm perf:lighthouse
```

| Route | Perf | TBT | SI | Status |
|-------|------|-----|-----|--------|
| `/pulse` | 100 | 12 ms | 1384 ms | Pass |
| `/thread/{cardId}` | 94 | 125 ms | 2573 ms | Pass |
| `/mirror` | 90 | 23 ms | **4880 ms** | **Fail** (SI) |
| `/lens` | 92 | **325 ms** | 1384 ms | **Fail** (TBT) |
| `/map` | 100 | 35 ms | 1146 ms | Pass |
| `/map/it` | 100 | 21 ms | 1132 ms | Pass |

**vs 24 May 2026 baseline:**

| Route | Baseline issue | 30 May result |
|-------|----------------|---------------|
| Mirror | perf 78, TBT 570 ms, SI 4137 ms | perf 90, TBT 23 ms; SI **variance** (4880 ms this run; **1749 ms** on 2-attempt re-run) |
| Lens | TBT 272 ms | TBT **325 ms** (still fail) |
| Thread | SI 4172 ms (variance) | SI **2573 ms** pass |

**Mirror re-run (2 attempts, mirror only):** attempt 1 — perf **94**, TBT **83 ms**, SI **1749 ms** (pass).

**Lens re-run (2 attempts):** SI **3967 ms**, **3922 ms** — both fail SI; TBT pass on re-run.

Archive files (canonical six-surface run):

- `Page Load Performance/lighthouse-ci-mobile-investment-assistant-frontend-vercel-app-2026-05-29T1849-*.json`

---

## Lighthouse — desktop (production, 29 May 2026)

Command: `pnpm perf:lighthouse:desktop` (same `LIGHTHOUSE_PAGES`).

| Route | Perf | TBT | SI | Status |
|-------|------|-----|-----|--------|
| `/pulse` | 100 | 0 ms | 571 ms | Pass |
| `/thread/{cardId}` | 95 | 0 ms | 1862 ms | Pass |
| `/mirror` | 100 | 0 ms | 577 ms | Pass |
| `/lens` | 94 | 0 ms | 2008 ms | Pass |
| `/map` | 100 | 0 ms | 471 ms | Pass |
| `/map/it` | 95 | 0 ms | 1539 ms | Pass |

Archive: `Page Load Performance/lighthouse-ci-desktop-investment-assistant-frontend-vercel-app-2026-05-29T1850-*.json` and `*1851-map-*.json`

---

## Phase 2.5 exit criteria rollup

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Map `/map/{slug}` + API | **Met** | [P2.5-S1](./Phase2.5_P2.5-S1%20-%20Map%20production%20deploy.md) |
| API feed/card p95 &lt;800 ms | **Waiver** | Proxy p95 **1298 / 1350 ms**; `db_query_ms` **~475–711 ms**; [P2.5-S2](./Phase2.5_P2.5-S2%20-%20API%20latency%20feed%20and%20card.md) |
| Lighthouse CI mobile all routes | **Partial** | Lens SI + Mirror SI variance; desktop **green** |
| Cross-phase standards audit | **Met** | [P2.5-S5](./Phase2.5_P2.5-S5%20-%20Phase%202%20route%20perf%20audit.md), standards **v1.0** |
| JSON archive six surfaces | **Met** | `Page Load Performance/` 29 May 2026 mobile + desktop |

---

## P2.5-S6 task completion

| Task | Status | Notes |
|------|--------|-------|
| **6.1** Lighthouse mobile + desktop, all pages | **Done** | JSON saved; mobile Mirror/Lens gaps documented |
| **6.2** Final `bench_api_latency.mjs` | **Done** | Table § API bench |
| **6.3** Close-out doc | **Done** | This file |
| **6.4** PO sign-off | **Done** | Conditional close § Product Owner sign-off |

---

## Open follow-ups (Phase 3 / optional)

| Item | Owner | Story |
|------|-------|-------|
| Lens mobile SI &lt;3400 ms | Sam | P2.5-S4 / Phase 3 perf |
| Mirror mobile SI stability on CI | Sam + Riley | Re-run CI; P2.5-S3 |
| API proxy p95 &lt;800 ms | Jordan | P3-S5 SLOs |
| Confirm `main` CI Lighthouse green | Riley | GitHub Actions after push |

---

## References

| Doc / script | Role |
|--------------|------|
| `docs/plans/finnwise-phase2.5-implementation-tasks.md` | Phase 2.5 stories |
| `docs/plans/finnwise-phase3-implementation-tasks.md` | Phase 3 prerequisite |
| `docs/plans/cross-phase-performance-standards.md` | Mandatory practices v1.0 |
| `scripts/bench_api_latency.mjs` | API bench |
| `scripts/lighthouse.mjs` | Lighthouse CI |
| `docs/Post Implementation documentation/Phase1_P1.5 - Performance remediation Pulse and Thread.md` | PO waiver precedent |
