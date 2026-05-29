# Post Implementation — P2.5-S4 (Mobile Lighthouse: Thread + Lens)

**Version:** v1.0 | **Date:** 30-05-2026  
**Story ID:** P2.5-S4  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`

---

## Summary

Production mobile Lighthouse (24 May 2026 baseline) failed on **Thread** (SI **4172 ms**) and **Lens** (TBT **272 ms**). Thread was blocked on a full-document SSR wait for `fetchCardDetail()`; Lens ran `GET /api/lens/queries/me` on mount and loaded editorial fonts on both Thread and Lens route layouts. Thread also pulled `PredictionLogger` and session-holdings work onto the critical path.

This story ships frontend perf fixes aligned with Mirror (P2.5-S3). **Lighthouse budget sign-off remains operator-owned** after Vercel deploy.

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

## Operator follow-up (acceptance not complete until done)

1. **Deploy** frontend to Vercel (Thread streaming + Lens deferral).
2. **Smoke Thread:** signed-in `/thread/{cardId}` — Network tab should show card data via RSC (no client refetch on first paint when SSR succeeds).
3. **Smoke Lens:** signed-in `/lens` — `GET /api/lens/queries/me` should start **after** FCP (idle/deferred), not in the first network burst.
4. **Lighthouse mobile** (2 attempts each):
   ```powershell
   $env:LIGHTHOUSE_PAGES="thread,lens"
   node scripts/lighthouse.mjs
   ```
   Targets: Thread perf ≥90, SI <3400 ms, TBT <200 ms; Lens perf ≥90, TBT <200 ms.
5. Mark plan story acceptance checkboxes when budgets are green.

---

## Baseline vs target

| Route | Metric | 24 May 2026 (mobile prod) | Target |
|-------|--------|---------------------------|--------|
| `/thread/{cardId}` | Speed Index | 4172 ms | <3400 ms |
| `/thread/{cardId}` | Performance | 91 | ≥90 |
| `/lens` | TBT | 272 ms | <200 ms |
| `/lens` | Performance | 90 | ≥90 |

---

## References

- `docs/plans/performance-correction-pulse-mirror.md` (PC-1.1, PC-1.2, PC-4.1, PC-4.2)
- `docs/Post Implementation documentation/Phase2.5_P2.5-S3 - Mobile Lighthouse Mirror.md` (streaming SSR pattern)
