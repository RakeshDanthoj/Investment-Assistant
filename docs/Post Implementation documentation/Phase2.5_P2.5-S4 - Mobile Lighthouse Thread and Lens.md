# Post Implementation — P2.5-S4 (Mobile Lighthouse: Thread + Lens)

**Version:** v1.1 | **Date:** 30-05-2026  
**Story ID:** P2.5-S4  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`  
**Phase close-out:** [Phase2.5_P2.5 - Performance close-out pre-Phase 3.md](./Phase2.5_P2.5%20-%20Performance%20close-out%20pre-Phase%203.md)

**Story status: CLOSED** — Vercel deploy verified; mobile budgets green (29 May 2026).

---

## Summary

Production mobile Lighthouse (24 May 2026 baseline) failed on **Thread** (SI **4172 ms**) and **Lens** (TBT **272 ms**). Thread was blocked on a full-document SSR wait for `fetchCardDetail()`; Lens ran `GET /api/lens/queries/me` on mount. This story shipped streaming SSR, `deferAfterPaint`, scoped fonts, and dynamic `PredictionLogger`.

**Post-deploy verification (production Vercel):**

| Route | Perf | TBT | SI | Status |
|-------|------|-----|-----|--------|
| `/thread/{cardId}` | 95 | 25 ms | 2929 ms | Pass (attempt 2/2) |
| `/lens` | 94 | 28 ms | 2488 ms | Pass (attempt 2/2) |

---

## What shipped

| Task | Change |
|------|--------|
| **4.1** | Confirmed `fetchCardDetail(..., { next: { revalidate: 60 } })` in `lib/api/server.ts`; added `ThreadContentSection.tsx` async RSC + `Suspense` in `[cardId]/page.tsx` so `loading.tsx` shell streams before card API completes. |
| **4.2** | Editorial fonts remain scoped to `thread/layout.tsx` only (Playfair/DM Mono not on Pulse/Mirror). |
| **4.3** | `formatGeneratedMeta` uses `formatFinnwiseDate`; `formatRelativeDate` uses fixed `en-IN` locale; `PredictionLogger` dynamically imported (`ssr: false`) in `InsightLayer`. |
| **4.4** | Deferred `PredictionLogger` `/api/predictions/me` probe and `useSessionHoldings` refresh via `deferAfterPaint` (PC-4.2 / trim critical-path JS). |
| **4.5** | `lens/page.tsx` SSR-renders `LensTopbar` server-side; defers client hydration work for history. |
| **4.6** | `LensClient` defers `GET /api/lens/queries/me` with `deferAfterPaint` (PC-1.2 pattern). |
| **4.7** | Editorial fonts scoped to `lens/layout.tsx` (unchanged; not loaded on Pulse/Mirror). |
| **4.8** | Verified Lens subtree has no Mirror imports; shared Thread ICE components only. |

**New utility:** `frontend/lib/deferAfterPaint.ts` — shared idle/post-paint deferral.

---

## Tests (local CI)

| Check | Command | Result |
|-------|---------|--------|
| Frontend lint | `pnpm lint` | Pass |
| Frontend typecheck | `pnpm typecheck` | Pass |
| Frontend unit | `pnpm test` | **121 passed** |
| Frontend build | `pnpm build` | Pass |

---

## Post-deploy results (29 May 2026)

| Route | Metric | 24 May baseline | Post–S4 deploy |
|-------|--------|-----------------|----------------|
| `/thread/{cardId}` | Speed Index | 4172 ms | **2929 ms** |
| `/thread/{cardId}` | TBT | 140 ms | **25 ms** |
| `/lens` | TBT | 272 ms | **28 ms** |
| `/lens` | Speed Index | 1876 ms | **2488 ms** |

Archive: `Page Load Performance/lighthouse-ci-mobile-*-2026-05-29T1859-thread-*`, `*lens-*`

---

## References

- `docs/plans/performance-correction-pulse-mirror.md` (PC-1.1, PC-1.2, PC-4.1, PC-4.2)
- `docs/Post Implementation documentation/Phase2.5_P2.5-S3 - Mobile Lighthouse Mirror.md` (streaming SSR pattern)
