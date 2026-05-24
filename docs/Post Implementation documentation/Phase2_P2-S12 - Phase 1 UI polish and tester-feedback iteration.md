# Post Implementation Detailed Document — P2-S12

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S12 (Phase 2, Story 12)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`  
**Related plans:** `docs/plans/performance-correction-pulse-mirror.md`, `docs/plans/cross-phase-performance-standards.md`

---

## Narrative style

**P2-S12** is a **Frontend** polish story: it closes Phase 1 tester-facing rough edges before Phase 2 engagement features land on a clean base. Work fell into four tracks: **(1)** capture and triage feedback in a gitignored backlog; **(2)** close all **P0** performance/UX items (hydration, duplicate notification fetches, Mirror filter skeleton); **(3)** add automated **WCAG** checks with `jest-axe` on Pulse, Thread, Mirror, and Lens surfaces plus PRD §8.3 palette pairs; **(4)** improve copy on the Pulse **Insight Panel** and Thread **Instrument Card** reasoning blocks.

No backend routes or database migrations were added. Lighthouse budgets for **Pulse** and **Thread** remain enforced by the existing **P1.5-S9** CI job; extending the runner to Mirror, Lens, and Map is explicitly deferred to **P2-S15**.

**Tests executed and passed (P2-S12 scope):**

| Area | Command / suite | Result |
|------|-----------------|--------|
| A11y — palette | `tests/a11y/palette.test.tsx` | **11 passed** — PRD §8.3 fg/bg pairs, `color-contrast` rule |
| A11y — Pulse | `tests/a11y/pulse.test.tsx` | **3 passed** — EventCard, InsightPanel, Topbar |
| A11y — Thread | `tests/a11y/thread.test.tsx` | **1 passed** — InstrumentCard |
| A11y — Mirror | `tests/a11y/mirror.test.tsx` | **2 passed** — StatsStrip, PredictionCard |
| A11y — Lens | `tests/a11y/lens.test.tsx` | **1 passed** — QueryInput |
| Date formatting | `lib/format/dateTime.test.ts` | **2 passed** — stable UTC/`en-IN`, null → em dash |
| Notification dedupe | `lib/api/notificationAlert.test.ts` | **1 passed** — single in-flight fetch |
| Instrument copy | `InstrumentCard.test.tsx` | **1 passed** — SEBI guard + new reasoning label |
| **Combined** | `pnpm test -- tests/a11y lib/format/dateTime lib/api/notificationAlert InstrumentCard.test` | **22 passed**, 8 suites |
| Typecheck | `pnpm typecheck` (frontend) | **Passed** |

**Not in scope for this story’s test run:** full `pnpm test` (pre-existing failures in `lib/personalisation/sessionHoldings.test.ts`). **Lighthouse live audit** was not re-run locally as part of doc generation; CI job **Lighthouse budgets** still targets production Pulse + Thread per P1.5-S9.

**Operator follow-up:** deploy frontend to Vercel, then smoke-test Pulse/Mirror console (no hydration warnings) and Network tab (one deferred notifications request). See B6 and B7.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S12 |
| **Title** | Phase 1 UI polish + tester-feedback iteration |
| **Category** | **Frontend** (UI, accessibility, performance UX; no backend) |

**What this story aimed to achieve**

Phase 1 testers flagged visible rough edges—hydration flashes, redundant API calls, unclear empty states, and missing automated contrast checks. This story triaged that feedback, closed every **P0** item, added `axe`-based regression tests on core surfaces, and tightened copy on high-traffic analysis UI so Phase 2 features (Lens, Mirror engagement, email, etc.) ship on a stable, readable base.

**How it fits into the overall application**

FinnWise’s trust model depends on calm, predictable UI (PRD §8.3 palette, SEBI-safe copy). **P1.5-S9** guards performance on Pulse/Thread; **P2-S12** adds accessibility automation and fixes issues that Lighthouse scores alone did not catch (e.g. hydration re-renders, duplicate fetches). It runs **in parallel** with other Phase 2 stories and unblocks confident tester expansion without waiting for **P2-S15** (Lighthouse extension to Mirror/Lens/Map).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | Delivered |
|----------|-----------|
| **12.1** | `notes/phase1-feedback-backlog.md` — gitignored backlog with P0/P1/P2 triage (F-01–F-10) |
| **12.2** | All **P0** items closed (see table below) |
| **12.3** | `frontend/tests/a11y/*.test.tsx` — `jest-axe` on Pulse, Thread, Mirror, Lens + palette contrast suite |
| **12.4** | Pulse/Thread Lighthouse CI unchanged (P1.5-S9); Mirror/Lens/Map extension noted for **P2-S15** |
| **12.5** | Copy clarity on `InsightPanel` and `InstrumentCard` |
| **12.6** | A11y suite green; typecheck green; Lighthouse still enforced in CI for Pulse/Thread |

**P0 closure summary**

| ID | Problem | Implementation |
|----|---------|----------------|
| F-01 | Locale-dependent `toLocaleString` / `toLocaleTimeString` caused React #422/#425 on Pulse | `frontend/lib/format/dateTime.ts` — fixed `en-IN` locale + `UTC` timezone; wired into Pulse/Mirror date displays |
| F-02 | Two `GET /api/notifications` on Pulse load | `frontend/lib/api/notificationAlert.ts` — module-level cache + in-flight dedupe; `requestIdleCallback` (or `setTimeout(0)`) deferral; `NotificationBadge` uses shared helper |
| F-03 | Mirror filter change triggered full-page skeleton | `MirrorClient` — `loadPredictionsOnly()` on status change; `listLoading` for list-only skeleton; stats/sidebar stay visible |
| F-04 | Mirror client-only API waterfall | Already addressed pre–P2-S12 via `mirrorServer.ts` + SSR `mirror/page.tsx` (performance-correction PC-2.2); marked closed in backlog |

**Functional breakdown — date formatting**

- `formatFinnwiseTime`, `formatFinnwiseDateTime`, `formatFinnwiseDate` return `"—"` for null/invalid input.
- All call sites that previously used environment-default locale now use the shared module so server HTML matches client hydration.

**Functional breakdown — notifications**

- First caller wins; concurrent mounts share one promise.
- Result cached for the session (`cachedCardId`) so remounts do not refetch.
- `resetNotificationAlertCacheForTests()` exposed for unit tests only.

**Functional breakdown — Mirror filter**

- `initialLoadDoneRef` + `prevStatusFilterRef` separate first load from filter changes.
- SSR-hydrated first paint skips client `loadData` when `initialPayload` matches `statusFilter`.
- Filter change: only `GET /api/mirror/predictions?status=…`; stats/streak/unread unchanged.

**Copy changes (12.5)**

| Surface | Before | After |
|---------|--------|--------|
| InsightPanel empty | “Select an event to preview analysis.” | “Select an event card to preview direction, magnitude, and linked instruments.” |
| InsightPanel context | Italic paragraph only | “Event context” label + paragraph |
| InstrumentCard subhead | “Instrument assessment” | “How this event affects this name” |
| InstrumentCard reasoning | Bare paragraph | “Why we labelled it this way” label + `text-slate-700` body |

**Validations and error handling**

| Case | Behaviour |
|------|-----------|
| Invalid ISO date | Formatter returns original string or `"—"` (no throw) |
| Notifications API failure | Badge hidden; no user-facing error |
| Mirror predictions-only fetch failure | `describeFetchFailure` message; list skeleton clears |
| A11y violation in CI | Jest fails with `toHaveNoViolations` diff |

**Business rules**

- SEBI guard on InstrumentCard unchanged (`InstrumentCard.test.tsx` — no buy/sell/hold or ₹ price targets in rendered copy).
- Open backlog items **F-05** (streaming SSR / API latency), **F-09** (Lighthouse Mirror/Lens/Map), **F-10** (Lens step copy) remain for later stories.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **UTC + `en-IN` for all display timestamps** | Eliminates server (Vercel UTC) vs browser locale mismatch; single source in `dateTime.ts` |
| **Defer notification fetch with idle callback** | Reduces competition with feed SSR critical path (PC-1.2) |
| **Module-level dedupe cache for notifications** | Strict Mode double-mount and duplicate Topbar trees caused twin requests |
| **Mirror: predictions-only refetch on filter** | Stats/streak do not depend on `status` query param |
| **`jest-axe` on isolated components, not full pages** | Faster, stable CI; avoids auth/RSC setup; still catches real markup a11y issues |
| **Separate `palette.test.tsx` for PRD hex pairs** | Documents §8.3 contrast contract independent of component churn |
| **Backlog gitignored under `notes/`** | Matches P1-S13/P1-S14 pattern for operational PO artifacts |
| **No `lighthouse.mjs` changes in S12** | Plan assigns Mirror/Lens/Map URLs to **P2-S15** |

⚠️ **Do not revert to `toLocaleString(undefined, …)` on Pulse/Mirror surfaces** without re-validating hydration on production Lighthouse `errors-in-console`.

⚠️ **Do not remove notification dedupe** without confirming a single mount point for the badge fetch.

⚠️ **Do not restore full `loadData()` on Mirror filter change** — it regresses F-03 and full-page skeleton UX.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / modules |
|-----------|-------------------|
| **Upstream** | Phase 1 tester feedback; **P1.5-S9** Lighthouse CI (Pulse/Thread); **P1.5-S5/S6** SSR patterns; performance-correction plan PC-1.x / PC-2.2 |
| **Downstream** | **P2-S15** — extend `scripts/lighthouse.mjs` to Mirror, Lens, Map; `cross-phase-performance-standards.md` enforcement |
| | **P2-S7/S8** Lens — benefits from stable base; F-10 copy still open |
| | All Phase 2 tester-facing stories — assume P0 polish complete |
| **Shared** | `NotificationBadge`, `InsightPanel`, `InstrumentCard`, `MirrorClient`, PRD §8.3 Tailwind tokens |

---

### A5. DESIGN CHOICES

**Architecture**

- Small pure utilities (`dateTime`, `notificationAlert`) instead of React context for cross-cutting concerns.
- Mirror filter logic uses refs to distinguish SSR skip vs filter navigation vs initial client load.

**Database**

- None.

**API contracts**

- No new or modified endpoints. Existing consumers:
  - `GET /api/notifications?limit=50` (deduped client access)
  - `GET /api/mirror/predictions?status=` (partial refetch only)

**UI/UX**

- Copy follows PRD tone: descriptive labels, no advisory language on Instrument Card.
- Insight panel empty state sets expectation (direction, magnitude, instruments).

**Libraries**

| Package | Role |
|---------|------|
| `jest-axe` + `axe-core` | Automated a11y in Jest |
| `@types/jest-axe` | TypeScript for `toHaveNoViolations` matcher |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| phase1-feedback-backlog.md | `notes/phase1-feedback-backlog.md` | Gitignored triaged tester backlog (P0/P1/P2) |
| dateTime.ts | `frontend/lib/format/dateTime.ts` | Stable SSR-safe date/time formatters |
| dateTime.test.ts | `frontend/lib/format/dateTime.test.ts` | Formatter unit tests |
| notificationAlert.ts | `frontend/lib/api/notificationAlert.ts` | Deduped deferred notification fetch |
| notificationAlert.test.ts | `frontend/lib/api/notificationAlert.test.ts` | Concurrent fetch dedupe test |
| pulse.test.tsx | `frontend/tests/a11y/pulse.test.tsx` | Axe: EventCard, InsightPanel, Topbar |
| thread.test.tsx | `frontend/tests/a11y/thread.test.tsx` | Axe: InstrumentCard |
| mirror.test.tsx | `frontend/tests/a11y/mirror.test.tsx` | Axe: StatsStrip, PredictionCard |
| lens.test.tsx | `frontend/tests/a11y/lens.test.tsx` | Axe: QueryInput |
| palette.test.tsx | `frontend/tests/a11y/palette.test.tsx` | Axe: PRD §8.3 contrast pairs |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| Topbar.tsx | `frontend/app/(app)/pulse/_components/Topbar.tsx` | Uses `formatFinnwiseTime` |
| InsightPanel.tsx | `frontend/app/(app)/pulse/_components/InsightPanel.tsx` | `formatFinnwiseDateTime`; empty state + “Event context” label |
| NotificationBadge.tsx | `frontend/components/Topbar/NotificationBadge.tsx` | Uses `fetchSignalFiredCardId` helper |
| InstrumentCard.tsx | `frontend/app/(app)/thread/_components/InstrumentCard.tsx` | Clearer subhead + reasoning label |
| InstrumentCard.test.tsx | `frontend/app/(app)/thread/_components/InstrumentCard.test.tsx` | Asserts “Why we labelled it this way” |
| PredictionCard.tsx | `frontend/app/(app)/mirror/_components/PredictionCard.tsx` | Uses `formatFinnwiseDate` |
| ReadyToGradePanel.tsx | `frontend/app/(app)/mirror/_components/ReadyToGradePanel.tsx` | Uses `formatFinnwiseDate` |
| MirrorClient.tsx | `frontend/app/(app)/mirror/_components/MirrorClient.tsx` | Predictions-only filter refetch; `listLoading` |
| jest.setup.ts | `frontend/jest.setup.ts` | `expect.extend(toHaveNoViolations)` |
| package.json | `frontend/package.json` | DevDeps: `jest-axe`, `axe-core`, `@types/jest-axe` |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S12 acceptance criteria + tasks marked complete |

---

### A8. TESTS EXECUTED

**Backend:** None (no backend changes in P2-S12).

**Frontend — automated**

| Test file | Status | What it covers |
|-----------|--------|----------------|
| `tests/a11y/palette.test.tsx` | **Passed (11)** | Each PRD §8.3 fg/bg pair — `color-contrast` only |
| `tests/a11y/pulse.test.tsx` | **Passed (3)** | EventCard, InsightPanel (with card), Topbar axe clean |
| `tests/a11y/thread.test.tsx` | **Passed (1)** | InstrumentCard with reasoning + entry/exit blocks |
| `tests/a11y/mirror.test.tsx` | **Passed (2)** | StatsStrip with sample stats; PredictionCard collapsed |
| `tests/a11y/lens.test.tsx` | **Passed (1)** | QueryInput default empty state |
| `lib/format/dateTime.test.ts` | **Passed (2)** | Deterministic formatting; null → `—` |
| `lib/api/notificationAlert.test.ts` | **Passed (1)** | Parallel `fetchSignalFiredCardId` → one HTTP call |
| `InstrumentCard.test.tsx` | **Passed (1)** | SEBI forbidden patterns + new label present |

**Commands used**

```bash
cd frontend
pnpm test -- tests/a11y lib/format/dateTime lib/api/notificationAlert InstrumentCard.test
pnpm typecheck
```

**CI (unchanged, still applies)**

| Job | What it runs |
|-----|----------------|
| Frontend | `pnpm test` (full suite — note sessionHoldings pre-existing failures) |
| Lighthouse budgets | `pnpm perf:lighthouse` mobile + desktop on Pulse + Thread (P1.5-S9) |

**Manual testing recommended (not automated in S12)**

| Check | Expected |
|-------|----------|
| Hard refresh `/pulse` | No React hydration errors in console |
| Pulse Network | ≤1 notifications request, deferred after paint |
| Mirror filter pills | List skeleton only; stats strip stays populated |
| Deployed Lighthouse | Pulse/Thread perf ≥90 in CI against production URL |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

None.

---

### B2. API / INTEGRATION CONTRACTS

No endpoints added or modified. Client behaviour changes only:

| Existing endpoint | Client change |
|-------------------|---------------|
| `GET /api/notifications?limit=50` | At most one deduped, deferred fetch per session |
| `GET /api/mirror/predictions` | Optional `?status=` refetch without reloading stats/streak |

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Date display**

```
ISO string → Intl.DateTimeFormat("en-IN", { timeZone: "UTC", … })
null / invalid → "—" (or raw string on parse failure for date-only helpers)
```

**Notification badge**

```
Session start → (idle defer) → single fetch → cache card_id | null
Subsequent mounts → return cache, no fetch
kind === "signal_fired" → show pulsing button → navigate /thread/{card_id}
```

**Mirror filter**

```
URL ?status= changes
  IF initialLoadDone AND stats+streak loaded
    → loadPredictionsOnly (listLoading=true)
  ELSE
    → loadData (full page loading)
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **F-05 open** | Pulse/Thread “useful content” still 3–8 s in filmstrip — needs streaming SSR (PC-2.1) and API work (PC-3.x) |
| **F-09 open** | Mirror/Lens/Map not in Lighthouse CI until **P2-S15** |
| **F-10 open** | Lens pipeline step labels not revised in S12 |
| **Component-level axe only** | Does not catch full-page landmark/nav issues; future story may add route-level tests |
| **`sessionHoldings.test.ts`** | Pre-existing failures in full `pnpm test` — unrelated to S12 |
| **Gitignored backlog** | `notes/phase1-feedback-backlog.md` not in repo; copy manually for other machines |

---

### B5. TESTING NOTES

**Automated happy paths:** All P2-S12 Jest files listed in A8 pass.

**Automated edge cases:** Null dates; concurrent notification fetch; axe on empty InsightPanel not tested (only populated card).

**Manual vs automated:** Hydration and Network dedupe require production or `pnpm build && pnpm start` — not asserted in Jest.

**Coverage gaps:** No axe test for full `PulseClient`/`LensClient` pages; no E2E Playwright; Lighthouse Mirror not in CI.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Item | Notes |
|------|--------|
| **New env vars** | None |
| **Deploy** | Frontend-only deploy to Vercel (or equivalent) |
| **Vercel `API_BASE_URL`** | Verify full Render URL if SSR TTFB still high (F-05 / PC-1.4) — not changed in S12 |
| **Lighthouse CI** | `LIGHTHOUSE_BASE_URL`, `LIGHTHOUSE_THREAD_CARD_ID` — unchanged from P1.5-S9 |
| **Benchmarking** | Do not use `next dev` for Lighthouse comparisons (`scripts/README.md`) |

**Deployment sequencing**

1. Merge/deploy frontend.
2. Smoke-test Pulse + Mirror on production.
3. Confirm GitHub **Lighthouse budgets** job green on `main` (Pulse SI budget has failed historically — monitor).

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read `notes/phase1-feedback-backlog.md` locally for open F-05, F-09, F-10.
2. Use `frontend/lib/format/dateTime.ts` for any new timestamp on SSR surfaces.
3. Route notification badge fetches through `notificationAlert.ts` if adding second consumer.
4. Mirror filter changes must keep `loadPredictionsOnly` path — see refs in `MirrorClient.tsx`.

**Common mistakes**

- Reintroducing `toLocaleString(undefined)` → hydration regressions.
- Calling `loadData()` on every `searchParams` change → full-page skeleton (F-03).
- Adding axe rules globally without scoping — palette test intentionally limits to `color-contrast`.

**Where to find related code**

| Concern | Path |
|---------|------|
| Date formatters | `frontend/lib/format/dateTime.ts` |
| Notification dedupe | `frontend/lib/api/notificationAlert.ts` |
| A11y tests | `frontend/tests/a11y/` |
| Performance backlog | `docs/plans/performance-correction-pulse-mirror.md` |
| Lighthouse runner | `scripts/lighthouse.mjs`, `scripts/lighthouse-budget.mjs` |
| CI workflow | `.github/workflows/ci.yml` |

**Context by role**

- **Product / PO** — update gitignored backlog; open items F-05, F-09, F-10.
- **Platform / perf** — P2-S15 for Lighthouse URL extension; PC-2.1 streaming SSR for F-05.
- **Frontend** — maintain axe suite when changing Pulse/Thread/Mirror/Lens markup.

---

_End of document._
