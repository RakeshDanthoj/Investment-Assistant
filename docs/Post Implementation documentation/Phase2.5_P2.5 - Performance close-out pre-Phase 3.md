# Post Implementation — Phase 2.5 Performance close-out (pre–Phase 3)

**Version:** v1.1 | **Date:** 30-05-2026  
**Story ID:** P2.5-S6 (P2-S15 §15.5–15.6)  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`  
**Handover:** [Phase2.5_P2.5-S6 - Evidence archive and Phase close-out.md](./Phase2.5_P2.5-S6%20-%20Evidence%20archive%20and%20Phase%20close-out.md)  
**Scope:** Evidence archive + Phase 3 prerequisite sign-off for performance carry-forward from Phase 2 / P2-S15.

**Phase status:** **CLOSED**

---

## Product Owner sign-off

| Field | Value |
|--------|--------|
| **Decision** | **Phase 2.5 closed** — proceed with **P3-S0** (synthetic seed) and Phase 3 foundation milestones |
| **Date** | 30-05-2026 |
| **Authority** | Product Owner (project review) |

**Accepted with documented exception (Phase 3 engineering target, not blocking P3-S0):**

1. **Warm API proxy wall p95** — feed **1298–1958 ms**, card **1148–1350 ms** vs target **&lt;800 ms** — feed proxy improved **~44%** from May baseline (**2339 ms**); server `db_query_ms` p95 **~470–490 ms**, `connection_count: 1`. Waiver follows **Phase 1.5** precedent.

**Met without waiver:**

- Map production deploy — [P2.5-S1](./Phase2.5_P2.5-S1%20-%20Map%20production%20deploy.md)
- Mobile Lighthouse **all six routes** pass (post–P2.5-S4 Vercel deploy, 29 May 2026)
- Desktop Lighthouse all six routes pass
- Phase 2 route perf audit **v1.0** — [P2.5-S5](./Phase2.5_P2.5-S5%20-%20Phase%202%20route%20perf%20audit.md)
- Evidence JSON under `Page Load Performance/`

---

## Narrative summary

Phase 2.5 closed the gap between Phase 2 feature ship and Phase 3 load. **S1** deployed Map; **S2** feed bundle + API timing; **S3** Mirror dashboard SSR/streaming; **S4** Thread/Lens streaming and deferrals; **S5** standards audit; **S6** archived evidence and PO sign-off.

**Phase 3 prerequisite:** satisfied for build start. **P3-S5** / **P3-S8** continue to track **&lt;800 ms** API and perf gates for public surfaces.

---

## API bench

Command:

```powershell
$env:BENCH_API_DIRECT_URL="https://investment-assistant-3eqc.onrender.com"
$env:BENCH_VERCEL_URL="https://investment-assistant-frontend.vercel.app"
node scripts/bench_api_latency.mjs
```

| Endpoint | Proxy wall p95 (30 May) | Proxy wall p95 (post–S4) | `db_query_ms` p95 | vs May baseline proxy |
|----------|-------------------------|---------------------------|-------------------|------------------------|
| `/api/feed` | 1298 ms | 1958 ms | ~475 ms | was 2339 ms |
| `/api/cards/{id}` | 1350 ms | **1148 ms** | ~470 ms | was 1265 ms |

**PO waiver** on strict **&lt;800 ms** proxy p95. Detail: [P2.5-S2](./Phase2.5_P2.5-S2%20-%20API%20latency%20feed%20and%20card.md).

---

## Lighthouse — mobile (final, post–P2.5-S4 deploy)

Budgets: perf **≥90**, TBT **&lt;200 ms**, SI **&lt;3400 ms**.

| Route | Perf | TBT | SI | Status |
|-------|------|-----|-----|--------|
| `/pulse` | 95 | 25 ms | 2273 ms | Pass |
| `/thread/{cardId}` | 95 | 25 ms | 2929 ms | Pass (2/2) |
| `/mirror` | 94 | 9 ms | 2569 ms | Pass |
| `/lens` | 94 | 28 ms | 2488 ms | Pass (2/2) |
| `/map` | 100 | 7 ms | 998 ms | Pass |
| `/map/it` | 100 | 9 ms | 1167 ms | Pass |

**vs 24 May baseline:** Mirror SI **4137 → 2569 ms**; Lens TBT **272 → 28 ms**; Thread SI **4172 → 2929 ms**.

Archive: `Page Load Performance/lighthouse-ci-mobile-*-2026-05-29T1859-*`, `*1900-*`

---

## Lighthouse — desktop (29 May 2026)

All six surfaces pass. Archive: `Page Load Performance/lighthouse-ci-desktop-*-2026-05-29T1850-*`, `*1851-*`

| Route | Perf | TBT | SI |
|-------|------|-----|-----|
| Pulse | 100 | 0 ms | 571 ms |
| Thread | 95 | 0 ms | 1862 ms |
| Mirror | 100 | 0 ms | 577 ms |
| Lens | 94 | 0 ms | 2008 ms |
| Map | 100 | 0 ms | 471 ms |
| Map slug | 95 | 0 ms | 1539 ms |

---

## Phase 2.5 exit criteria rollup

| Criterion | Status |
|-----------|--------|
| Map `/map/{slug}` + API | **Met** |
| API feed/card p95 &lt;800 ms | **Waiver** (documented) |
| Lighthouse CI mobile + desktop | **Met** (post–S4 production run) |
| Cross-phase standards | **Met** (v1.0) |
| JSON archive | **Met** |

---

## Phase 2.5 story handovers

| Story | Document |
|-------|----------|
| S1 Map deploy | [Phase2.5_P2.5-S1](./Phase2.5_P2.5-S1%20-%20Map%20production%20deploy.md) |
| S2 API latency | [Phase2.5_P2.5-S2](./Phase2.5_P2.5-S2%20-%20API%20latency%20feed%20and%20card.md) |
| S3 Mirror | [Phase2.5_P2.5-S3](./Phase2.5_P2.5-S3%20-%20Mobile%20Lighthouse%20Mirror.md) |
| S4 Thread + Lens | [Phase2.5_P2.5-S4](./Phase2.5_P2.5-S4%20-%20Mobile%20Lighthouse%20Thread%20and%20Lens.md) |
| S5 Audit | [Phase2.5_P2.5-S5](./Phase2.5_P2.5-S5%20-%20Phase%202%20route%20perf%20audit.md) |
| S6 Evidence | [Phase2.5_P2.5-S6](./Phase2.5_P2.5-S6%20-%20Evidence%20archive%20and%20Phase%20close-out.md) |

---

## Phase 3 carry-forward

| Item | Owner | Where |
|------|-------|-------|
| API proxy p95 &lt;800 ms | Jordan | P3-S5 SLOs |
| Public route Lighthouse | Sam + Riley | P3-S9, P3-S8 |

---

## References

| Doc / script | Role |
|--------------|------|
| `docs/plans/finnwise-phase2.5-implementation-tasks.md` | Phase 2.5 plan |
| `docs/plans/finnwise-phase3-implementation-tasks.md` | Phase 3 |
| `docs/plans/cross-phase-performance-standards.md` | v1.0 |
| `scripts/lighthouse.mjs` | CI runner |
| `scripts/bench_api_latency.mjs` | API bench |
