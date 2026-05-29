# Post Implementation — P2.5-S5 (Phase 2 route perf audit, P2-S15 §15.4)

**Version:** v1.0 | **Date:** 30-05-2026  
**Story ID:** P2.5-S5  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`

---

## Summary

Code review audit of Phase 2 routes (Mirror, Lens, Map index, Map sector, settings/email) against `docs/plans/cross-phase-performance-standards.md` §1–§4. Checklist updated to **v1.0** with per-route pass/partial/fail and issue links. One code fix shipped: **Lens query history** no longer blocks first paint (deferred `GET /api/lens/queries/me`).

---

## Audit results (§1–§4)

| Route | SSR / RSC | Client refetch | Bundles / fonts | Backend | Verdict |
|-------|-----------|----------------|-----------------|---------|---------|
| `/mirror` | Dashboard via `mirrorServer.ts` + `MirrorContentSection` | `hydratedFromServer` skips mount load | `next/dynamic` panels; no editorial fonts | `revalidate: 60` on dashboard | **Pass** |
| `/lens` | Static shell: `LensTopbar` (RSC) + `Suspense` body | History deferred (`deferAfterPaint`); submit uses `no-store` | Editorial fonts in `lens/layout.tsx` only; ICE `dynamic` in `ResultCard` | User queries `no-store` (correct) | **Partial** (interactive; history non-SSR by design) |
| `/map` | `fetchMapSectorList` in `page.tsx` | Props-only client | Light index; no dynamic split | Auth reads `no-store` | **Pass** |
| `/map/{slug}` | `fetchMapSectorDetail` in `[slug]/page.tsx` | Props-only client | `SensitivityMatrix` inline — optional split in P2.5-S4 | Auth reads `no-store` | **Pass** (bundle optional) |
| `/settings/email` | Auth redirect in RSC | Form fetch on interaction | Inter only (root layout) | N/A | **Pass** |

---

## What shipped (gap fix)

| Change | File(s) |
|--------|-----------|
| Shared defer helper | `frontend/lib/deferAfterPaint.ts` |
| Notification badge uses shared defer | `frontend/lib/api/notificationAlert.ts` |
| Lens SSR body boundary + signed-in hint | `frontend/app/(app)/lens/LensContentSection.tsx`, `page.tsx` |
| Defer query history until after paint | `frontend/app/(app)/lens/_components/LensClient.tsx` |

---

## Filed follow-ups (not silent)

| Item | Story | Notes |
|------|-------|-------|
| API feed/card p95 &lt; 800 ms | P2.5-S2 / S6 | PO waiver documented; final bench in S6 |
| Mobile Lighthouse Mirror / Thread / Lens | P2.5-S3 / S4 | Re-verify after deploy |
| `SensitivityMatrix` `next/dynamic` | P2.5-S4 | Only if Lighthouse trace shows heavy chunk on `/map/{slug}` |

---

## Standards doc

`docs/plans/cross-phase-performance-standards.md` bumped to **v1.0** with the route audit table and open-gaps table.

---

## Tests (local CI)

| Check | Command | Result |
|-------|---------|--------|
| Frontend lint | `pnpm lint` (from `frontend/`) | Pass |
| Frontend typecheck | `pnpm typecheck` | Pass |
| Frontend tests | `pnpm test` | Pass (after `deferAfterPaint` `Promise.resolve` fix) |
| Frontend build | `pnpm build` | Blocked locally by `ENOSPC` (disk full); code compiles via typecheck |

---

## References

- `docs/plans/cross-phase-performance-standards.md` (v1.0 route audit §)
- `docs/plans/finnwise-phase2.5-implementation-tasks.md` (P2.5-S5)
- `docs/Post Implementation documentation/Phase2.5_P2.5-S3 - Mobile Lighthouse Mirror.md`
