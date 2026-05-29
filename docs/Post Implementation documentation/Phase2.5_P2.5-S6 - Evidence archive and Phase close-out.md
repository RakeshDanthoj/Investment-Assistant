# Post Implementation Detailed Document — P2.5-S6

**Version:** v1.0 | **Date:** 30-05-2026  
**Story ID:** P2.5-S6 (Phase 2.5, Story 6 — P2-S15 §15.5–15.6)  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`  
**Phase rollup:** [Phase2.5_P2.5 - Performance close-out pre-Phase 3.md](./Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md)

---

## Narrative style (read this first)

**P2-S15** extended Lighthouse CI to Phase 2 routes but left production evidence incomplete: Map slug **404**, mobile budgets failing on Mirror/Thread/Lens, and API feed/card proxy p95 above **800 ms**. **Phase 2.5** (stories **S1–S6**) closed that gap before Phase 3 public load.

**P2.5-S6** is the **ops / docs** finale: archive mobile + desktop Lighthouse JSON for all six surfaces, run final `bench_api_latency.mjs`, author the phase close-out with PO sign-off, and wire the Phase 3 prerequisite. It depends on **S1** (Map deploy), **S2** (API tuning), **S3/S4** (mobile perf code + Vercel deploy), and **S5** (standards audit v1.0).

**Tests executed and passed (this story):**

| Suite / check | Command or method | Result |
|---------------|-------------------|--------|
| Lighthouse mobile (six surfaces) | `pnpm perf:lighthouse` with `LIGHTHOUSE_PAGES=pulse,thread,mirror,lens,map,map-sector` | **Pass** post–P2.5-S4 deploy (`*1859-*`, `*1900-*` JSON) |
| Lighthouse desktop (six surfaces) | `pnpm perf:lighthouse:desktop` | **Pass** (`*1850-*`, `*1851-*` JSON) |
| API latency bench | `node scripts/bench_api_latency.mjs` | **Recorded** — PO waiver on proxy p95 (see § API) |
| Budget smoke | `pnpm perf:lighthouse:budget-test` | Pass (via S5/S4 CI runs) |

**Three anchors:** (1) **Saved Lighthouse JSON under `Page Load Performance/`** is canonical evidence — not ad-hoc DevTools; (2) **API sign-off uses proxy p95 OR PO waiver** with `db_query_ms` + `connection_count` evidence (P1.5 precedent); (3) **`LIGHTHOUSE_CI_ATTEMPTS=2`** on CI — Thread/Lens may need attempt 2 for Speed Index variance.

---

## Product Owner sign-off (Phase 2.5 closed)

| Field | Value |
|--------|--------|
| **Decision** | **Phase 2.5 closed** — Phase 3 build may proceed (**P3-S0** synthetic seed Week 1) |
| **Date** | 30-05-2026 |
| **Authority** | Product Owner |

**Accepted with documented exception (carried to Phase 3 SLO work, not blocking P3-S0):**

- **Warm API proxy wall p95** feed/card **&gt;800 ms** on production samples — server `db_query_ms` p95 **~470–490 ms**, `connection_count: 1`; see [P2.5-S2](./Phase2.5_P2.5-S2%20-%20API%20latency%20feed%20and%20card.md).

**Met without waiver (final, post–S4 deploy):**

- Mobile Lighthouse **all six routes** pass budgets on production Vercel
- Desktop Lighthouse all six routes pass
- Map deploy + standards audit v1.0
- Evidence JSON archived

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2.5-S6 |
| **Title** | Evidence archive + Phase 2.5 close-out |
| **Category** | **Ops / Docs** (measurement harness + PO gate) |

**What this story aimed to achieve**

Archive defensible production performance evidence for Pulse, Thread, Mirror, Lens, Map index, and one Map slug (mobile + desktop), record final API bench numbers, and sign off Phase 2.5 so Phase 3 planning can start without re-litigating Phase 2 perf debt.

**How it fits into the overall application**

- **Upstream:** P2.5-S1–S5 (deploy, API, frontend perf, audit).
- **Downstream:** `finnwise-phase3-implementation-tasks.md` prerequisite; **P3-S5** SLOs; **P3-S8** go/no-go.
- **Parent:** P2-S15 partial close in Phase 2 plan.

**Production URLs**

| Layer | URL |
|-------|-----|
| Frontend | `https://investment-assistant-frontend.vercel.app` |
| API | `https://investment-assistant-3eqc.onrender.com` |

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **6.1** | Run `pnpm perf:lighthouse` + `pnpm perf:lighthouse:desktop` for `pulse,thread,mirror,lens,map,map-sector`; save JSON to `Page Load Performance/`. |
| **6.2** | Run `node scripts/bench_api_latency.mjs` against Render + Vercel proxy; paste p50/p95 in close-out. |
| **6.3** | Author `Phase2.5_P2.5 - Performance close-out pre-Phase 3.md` and this handover. |
| **6.4** | PO sign-off on exit criteria (waivers documented). |

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Treat post–S4 Lighthouse run as mobile gate** | P2.5-S4 deploy fixed Thread/Lens/Mirror blockers; full six-surface run **passed** with CI 2-attempt behaviour. |
| **PO waiver for API proxy p95** | `db_query_ms` ~475 ms with single connection; proxy RTT dominates wall clock — same pattern as Phase 1.5. |
| **Keep mobile budgets strict** | Do not relax TBT/SI thresholds; use `LIGHTHOUSE_CI_ATTEMPTS=2` for variance. |
| **Close-out + S6 handover split** | Close-out = rollup tables + PO decision; S6 handover = operator playbook (this file). |

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | P2.5-S1–S5; P2.5-S4 Vercel deploy for final mobile green |
| **Enables** | Phase 3 **P3-S0** start; **P3-S8** evidence pack |
| **References** | `cross-phase-performance-standards.md` v1.0 |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Evidence storage** | Committed JSON under `Page Load Performance/` (not CI artifacts) |
| **Runner** | `scripts/lighthouse.mjs` — same config as `.github/workflows/ci.yml` |
| **Map slug** | `LIGHTHOUSE_MAP_SLUG=it` (CI default) |
| **Thread card** | `e708b82c-f7c7-45e7-a59b-6b66dac8927a` (default published card) |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| Phase close-out | `docs/Post Implementation documentation/Phase2.5_P2.5 - Performance close-out pre-Phase 3.md` | PO rollup + bench/Lighthouse tables |
| S6 handover | `docs/Post Implementation documentation/Phase2.5_P2.5-S6 - Evidence archive and Phase close-out.md` | This document |
| Lighthouse JSON (mobile) | `Page Load Performance/lighthouse-ci-mobile-*-2026-05-29T1849-*` | Pre–S4 archive |
| Lighthouse JSON (mobile, final) | `Page Load Performance/lighthouse-ci-mobile-*-2026-05-29T1859-*`, `*1900-*` | Post–S4 green run |
| Lighthouse JSON (desktop) | `Page Load Performance/lighthouse-ci-desktop-*-2026-05-29T1850-*`, `*1851-*` | Desktop archive |

---

### A7. FILES MODIFIED

| File Path | What Changed |
|-----------|--------------|
| `docs/plans/finnwise-phase2.5-implementation-tasks.md` | Phase 2.5 exit criteria + S6 tasks marked complete |
| `docs/plans/cross-phase-performance-standards.md` | Exit checklist + open gaps updated |
| `docs/plans/finnwise-phase3-implementation-tasks.md` | Prerequisite links to close-out |
| Story handovers S1–S5, S4 | Cross-links to final evidence |

---

### A8. TESTS EXECUTED

**Lighthouse mobile (final — post–P2.5-S4 deploy, 29 May 2026)**

```powershell
$env:LIGHTHOUSE_PAGES="pulse,thread,mirror,lens,map,map-sector"
$env:LIGHTHOUSE_MAP_SLUG="it"
pnpm perf:lighthouse
```

| Route | Perf | TBT | SI | Status |
|-------|------|-----|-----|--------|
| `/pulse` | 95 | 25 ms | 2273 ms | Pass |
| `/thread/{cardId}` | 95 | 25 ms | 2929 ms | Pass (attempt 2/2) |
| `/mirror` | 94 | 9 ms | 2569 ms | Pass |
| `/lens` | 94 | 28 ms | 2488 ms | Pass (attempt 2/2) |
| `/map` | 100 | 7 ms | 998 ms | Pass |
| `/map/it` | 100 | 9 ms | 1167 ms | Pass |

**vs 24 May baseline:** Mirror SI **4137 → 2569 ms**; Lens TBT **272 → 28 ms**; Thread SI **4172 → 2929 ms** (pass).

**Lighthouse desktop (29 May 2026):** all six surfaces pass — see close-out doc.

**API bench (30 May + post–S4 sample)**

| Endpoint | Proxy wall p95 (30 May) | Proxy wall p95 (post–S4) |
|----------|-------------------------|---------------------------|
| `/api/feed` | 1298 ms | 1958 ms (variance) |
| `/api/cards/{id}` | 1350 ms | **1148 ms** |

`db_query_ms` p95 **~470–488 ms**; `connection_count: 1`. **PO waiver** for strict **&lt;800 ms** proxy target.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing perf CI or claiming Phase 3 perf gate**

1. Read phase close-out: [Phase2.5_P2.5 - Performance close-out pre-Phase 3.md](./Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md).
2. Read upstream story handovers: [S1](./Phase2.5_P2.5-S1%20-%20Map%20production%20deploy.md), [S2](./Phase2.5_P2.5-S2%20-%20API%20latency%20feed%20and%20card.md), [S3](./Phase2.5_P2.5-S3%20-%20Mobile%20Lighthouse%20Mirror.md), [S4](./Phase2.5_P2.5-S4%20-%20Mobile%20Lighthouse%20Thread%20and%20Lens.md), [S5](./Phase2.5_P2.5-S5%20-%20Phase%202%20route%20perf%20audit.md).
3. Re-run evidence only against **production** (`next build` + `next start` locally is OK for dev; not for sign-off).

**Operator commands (copy-paste)**

```powershell
# Mobile + desktop archive
$env:LIGHTHOUSE_PAGES="pulse,thread,mirror,lens,map,map-sector"
$env:LIGHTHOUSE_MAP_SLUG="it"
pnpm perf:lighthouse
pnpm perf:lighthouse:desktop

# API bench
$env:BENCH_API_DIRECT_URL="https://investment-assistant-3eqc.onrender.com"
$env:BENCH_VERCEL_URL="https://investment-assistant-frontend.vercel.app"
node scripts/bench_api_latency.mjs
```

**Common mistakes**

- Using `next dev` Lighthouse scores for sign-off (dev bundle inflates TBT/SI).
- Removing `map-sector` from CI while Phase 2.5 evidence requires six surfaces.
- Treating a single failed SI attempt as regression without `LIGHTHOUSE_CI_ATTEMPTS=2`.

**Where to find code**

| Concern | Path |
|---------|------|
| Lighthouse runner | `scripts/lighthouse.mjs` |
| Budgets | `scripts/lighthouse-budget.mjs` |
| API bench | `scripts/bench_api_latency.mjs` |
| CI env | `.github/workflows/ci.yml` → `LIGHTHOUSE_PAGES` |
| Standards | `docs/plans/cross-phase-performance-standards.md` |
| Phase 3 plan | `docs/plans/finnwise-phase3-implementation-tasks.md` |

**Contact by role**

| Role | Responsibility |
|------|----------------|
| Riley | Lighthouse CI, JSON archive, close-out docs |
| Jordan | API bench, Render pooler, feed bundle |
| Sam | Thread/Lens/Mirror frontend perf (S3/S4) |

---

## Phase 2.5 story index (all closed)

| Story | Handover |
|-------|----------|
| P2.5-S1 Map deploy | [Phase2.5_P2.5-S1](./Phase2.5_P2.5-S1%20-%20Map%20production%20deploy.md) |
| P2.5-S2 API latency | [Phase2.5_P2.5-S2](./Phase2.5_P2.5-S2%20-%20API%20latency%20feed%20and%20card.md) |
| P2.5-S3 Mirror mobile | [Phase2.5_P2.5-S3](./Phase2.5_P2.5-S3%20-%20Mobile%20Lighthouse%20Mirror.md) |
| P2.5-S4 Thread + Lens mobile | [Phase2.5_P2.5-S4](./Phase2.5_P2.5-S4%20-%20Mobile%20Lighthouse%20Thread%20and%20Lens.md) |
| P2.5-S5 Route audit | [Phase2.5_P2.5-S5](./Phase2.5_P2.5-S5%20-%20Phase%202%20route%20perf%20audit.md) |
| P2.5-S6 Evidence + close-out | This file |

---

## References

| Doc / script | Role |
|--------------|------|
| `docs/plans/finnwise-phase2.5-implementation-tasks.md` | Phase 2.5 plan (closed) |
| `docs/plans/finnwise-phase3-implementation-tasks.md` | Next phase |
| `scripts/README.md` | Bench + Lighthouse operator guide |
| `Phase1_P1.5 - Performance remediation Pulse and Thread.md` | PO waiver precedent |
