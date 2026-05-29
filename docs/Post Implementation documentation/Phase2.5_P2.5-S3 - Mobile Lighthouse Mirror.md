# Post Implementation — P2.5-S3 (Mobile Lighthouse: Mirror + shared shell)

**Version:** v1.0 | **Date:** 29-05-2026  
**Story ID:** P2.5-S3  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`

---

## Summary

Production mobile Lighthouse for `/mirror` (24 May 2026 baseline) failed budgets: **perf 78**, **TBT 570 ms**, **SI 4137 ms**. Root causes included a blocking SSR wait for five parallel mirror API calls, editorial font preload on the Mirror layout, duplicate global notification fetches competing with the critical path, and a large initial JS bundle for sidebar panels.

This story ships code to address those paths. **Lighthouse budget sign-off remains operator-owned** after Vercel (frontend) and Render (dashboard API) deploy.

---

## What shipped

| Area | Change |
|------|--------|
| **PC-3.3** | `GET /api/mirror/dashboard?status=` — stats, predictions, streak, gaps, unread in one response (`backend/app/api/mirror.py`). |
| **SSR** | `mirrorServer.ts` uses dashboard + `next: { revalidate: 60 }` (aligned with Pulse `server.ts`). |
| **PC-2.1** | `MirrorContentSection.tsx` async RSC inside `Suspense`; `page.tsx` streams fallback shell immediately. |
| **PC-1.2** | `NotificationBadge` not rendered on `/mirror` in `AppShell` / `Sidebar` (Mirror has `ResolvedBadge`). |
| **PC-4.3** | `next/dynamic` for `ReadyToGradePanel`, `ReasoningGapPanel`, `StreakTrackerPanel`. |
| **Fonts** | Removed `editorialFontVariables` from `mirror/layout.tsx` (Playfair/DM Mono not loaded on Mirror). |
| **PC-1.1** | Already in repo via `lib/format/dateTime.ts` on Mirror date surfaces. |

---

## Tests (local CI)

| Check | Command | Result |
|-------|---------|--------|
| Backend | `python -m ruff check backend` | Pass |
| Mirror API | `python -m pytest -q backend/tests/test_mirror_routes.py` | **4 passed** |
| Full backend | `python -m pytest -q backend/tests` | **220 passed** |
| Frontend | `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` | Pass |

---

## Operator follow-up (acceptance not complete until done)

1. **Deploy** frontend to Vercel and backend to Render (`/api/mirror/dashboard` must exist).
2. **Smoke** signed-in `/mirror`: Network tab should show **no** client calls to `/api/mirror/stats`, `/predictions`, `/streak`, `/gaps` on first load when SSR succeeds (only dashboard via RSC or zero client mirror reads).
3. **Lighthouse mobile** (2 attempts):
   ```powershell
   $env:LIGHTHOUSE_PAGES="mirror"
   node scripts/lighthouse.mjs
   ```
   Archive JSON under `Page Load Performance/` and confirm perf ≥90, TBT <200 ms, SI <3400 ms, **errors-in-console** pass.
4. Mark plan task **3.6** and story acceptance checkboxes when budgets are green.

---

## Baseline vs target

| Metric | 24 May 2026 (mobile prod) | Target |
|--------|---------------------------|--------|
| Performance | 78 | ≥90 |
| TBT | 570 ms | <200 ms |
| Speed Index | 4137 ms | <3400 ms |

---

## References

- `docs/plans/performance-correction-pulse-mirror.md` (PC-1.1, PC-1.2, PC-2.1, PC-3.3, PC-4.3)
- `docs/Post Implementation documentation/Phase2_P2-S12 - Phase 1 UI polish and tester-feedback iteration.md` (hydration + notification deferral)
