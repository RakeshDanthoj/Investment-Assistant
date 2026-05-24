# Post Implementation Detailed Document — P2-S5

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S5 (Phase 2, Story 5)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P2-S2** writes `mechanism_accuracy`, `business_accuracy`, and `market_accuracy` on `user_predictions` when a card resolves. **P2-S5** turns that data into a visual learning pattern: a **14-cell streak grid** in The Mirror right panel plus a **plain-English summary** that compares mechanism accuracy to market reaction match.

The grid shows the user’s **last 14 logged predictions**, ordered **most recent on the left**. Each filled cell encodes the **mechanism** grade only (not business or market per cell): green `M` (correct), amber `P` (partial), red `✗` (incorrect), grey `·` (monitoring or not yet graded), transparent `–` (no prediction in that slot). The summary paragraph uses **`mirror_stats.compute()`** over **all** predictions for the percentage figures (same basis as the four-stat strip), while the grid is a rolling window of 14.

The frontend loads streak data in parallel with stats and predictions inside `MirrorClient`. No new database migration was required — the story reads existing `user_predictions` columns.

**Tests executed and passed:** 4 pytest cases in `test_mirror_streak.py`; 3 Jest cases in `StreakTracker.test.tsx`.

**Three anchors:** (1) **Cell letter/colour map is mechanism-only** — market comparison is in the summary text, not per-cell letters; (2) **14 slots always returned** — pad with `grade: "empty"` / `letter: "–"`; (3) **Summary %s match stats strip** — both call `compute()` on full history, not last-14 only.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S5 |
| **Title** | Streak tracker grid + summary |
| **Category** | **Full Stack** (read API + Mirror UI components) |

**What this story aimed to achieve**

Give learners a quick visual of their recent prediction outcomes and explain, in plain language, why mechanism accuracy often runs ahead of market reaction match — without showing rupee figures or portfolio performance.

**How it fits into the overall application**

The streak tracker is the third card in The Mirror right panel (below Ready to Grade from P2-S3). It reinforces the PRD’s three-level accuracy model: users see mechanism patterns in the grid and the mechanism-vs-market gap in the summary, complementing P2-S1’s stats strip and per-card accuracy meters.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **5.1** | `GET /api/mirror/streak` — authenticated read; returns 14 cells + aggregate %s + summary string |
| **5.2** | `StreakTracker` — 7×2 / 14-column responsive grid; PRD §8.3 colour tokens on cells |
| **5.3** | `StreakSummary` + `build_streak_summary()` — templated paragraph from mechanism vs market % |
| **5.4** | Legend row under grid (Correct / Partial / Incorrect / Monitoring / No prediction) |
| **5.5** | Automated tests for cell ordering, transparent padding, colour classes, summary numerics |

**Functional breakdown**

1. Backend loads last 14 `user_predictions` rows for the user (`ORDER BY logged_at DESC LIMIT 14`).
2. Each row’s `mechanism_accuracy` maps to a `StreakCell` via `cell_from_mechanism_grade()`.
3. `build_streak_cells()` pads to exactly 14 cells with `empty` / `–` on the right when fewer predictions exist.
4. All user predictions are loaded for `compute()` → `mechanism_accuracy_pct`, `market_accuracy_pct`.
5. `build_streak_summary()` picks a template based on gap size (≥15 pt spread, ≤−15, close, or insufficient data).
6. Frontend renders `StreakTrackerPanel` in the Mirror aside; fetches on every Mirror load (with stats/predictions).

**Edge cases and error handling**

| Case | Behaviour |
|------|-----------|
| Zero predictions | 14 transparent cells; summary explains logging predictions on Thread |
| Only ungraded predictions | Grey `·` cells; summary may mention waiting for resolution |
| `SUPABASE_DB_URL` missing | HTTP 503 `db_unavailable` (same pattern as other Mirror routes) |
| Unauthenticated request | 401 via `CurrentUser` dependency |
| Mechanism graded, market still `monitoring` | Grid shows mechanism letter; summary uses partial % logic from `compute()` |

**Business rules enforced**

- PRD §5 Screen 4 colour/letter map for streak cells.
- Most recent prediction = leftmost cell (index 0).
- No `₹` or portfolio figures on this surface (inherits Mirror constraint).
- Summary must name both % figures when both are available and explain that a mechanism–market gap is normal when mechanism leads by ≥15 points.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Grid = mechanism grade only** | PRD letters `M/P/✗/·/–` align with mechanism outcomes; market is compared in summary % |
| **Summary % = full history** | Matches stats strip; avoids confusing users with different denominators |
| **Separate `mirror_streak` router file** | Matches implementation plan; mounted at `/api` alongside `mirror` router |
| **`null` mechanism → monitoring cell** | Active/ungraded predictions show grey `·` until P2-S2 grading runs |
| **Client fetch, not RSC** | Consistent with P2-S1 Mirror load pattern; streak fetched in `Promise.all` |

⚠️ **Do not change summary to use last-14-only percentages** without also changing the stats strip — they are intentionally aligned today.

⚠️ **Do not map market_accuracy to grid letters** — PRD spec and letter legend are mechanism-based.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / artifacts |
|-----------|---------------------|
| **Upstream** | P2-S2 (`mechanism_accuracy` etc. on `user_predictions`); P2-S1 (Mirror page, auth, layout); P1-S12 (prediction logger) |
| **Downstream** | P2-S4 (Reasoning Gap Analysis panel — adjacent slot, not yet built); no code depends on streak API yet |
| **Shared** | `mirror_stats.compute()`, `user_predictions` table, `MirrorClient` aside, `frontend/lib/mirror/types.ts` |

---

### A5. DESIGN CHOICES

**Architecture**

- Thin API layer (`mirror_streak.py`) over pure/service logic (`mirror_streak.py` service module).
- Presentation components split: `StreakTracker` (grid + legend), `StreakSummary` (text), `StreakTrackerPanel` (card chrome).

**Database**

- No schema changes. Reads `mechanism_accuracy` (and all grade columns for `compute()`) from existing `user_predictions`.

**API**

| Method | Route | Auth |
|--------|-------|------|
| GET | `/api/mirror/streak` | Bearer JWT (`CurrentUser`) |

**UI/UX**

- 14 cells: `grid-cols-7` on narrow viewports, `grid-cols-14` from 400px+.
- Cell backgrounds: `finnwise-modelled-bg` / `judged-bg` / `#FEE2E2` / `slate-100` / transparent per grade.
- DM Mono 10–11px letters inside cells; legend uses miniature swatches.
- Panel placed in right aside below `ReadyToGradePanel` (`min-[960px]:w-[280px]`).

**Libraries**

- No new dependencies; reuses FastAPI, Pydantic, existing Tailwind `finnwise-*` tokens.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| mirror_streak.py (service) | `backend/app/services/mirror_streak.py` | Cell building, summary templates, DB queries |
| mirror_streak.py (API) | `backend/app/api/mirror_streak.py` | `GET /streak` route + response models |
| test_mirror_streak.py | `backend/tests/test_mirror_streak.py` | Pytest for pure functions + route shape |
| StreakTracker.tsx | `frontend/app/(app)/mirror/_components/StreakTracker.tsx` | 14-cell grid + legend |
| StreakSummary.tsx | `frontend/app/(app)/mirror/_components/StreakSummary.tsx` | Summary paragraph |
| StreakTrackerPanel.tsx | `frontend/app/(app)/mirror/_components/StreakTrackerPanel.tsx` | Panel wrapper |
| StreakTracker.test.tsx | `frontend/app/(app)/mirror/_components/StreakTracker.test.tsx` | RTL tests |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| main.py | `backend/app/main.py` | Register `mirror_streak_router` |
| types.ts | `frontend/lib/mirror/types.ts` | `MirrorStreakResponse`, `StreakCell`, grade/letter types |
| MirrorClient.tsx | `frontend/app/(app)/mirror/_components/MirrorClient.tsx` | Fetch `/api/mirror/streak`; render `StreakTrackerPanel` in aside |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S5 acceptance + task checkboxes marked complete |

---

### A8. TESTS EXECUTED

| Test file | Status | What it covers |
|-----------|--------|----------------|
| `test_mirror_streak.py` | **Passed** | Letter mapping; 14-cell padding order; summary contains %; route returns 14 cells |
| `StreakTracker.test.tsx` | **Passed** | DOM order/grades; colour classes; summary text with numerics |

**Backend command**

```bash
cd backend
python -m pytest tests/test_mirror_streak.py -q
```

**Result:** 4 passed

**Frontend command**

```bash
cd frontend
npm test -- --testPathPattern=StreakTracker
```

**Result:** 3 passed (StreakTracker + StreakSummary describe blocks)

| Test name | Layer | Assertion |
|-----------|-------|-----------|
| `test_cell_from_mechanism_grade_letters` | Backend | M/P/✗/· mapping |
| `test_build_streak_cells_most_recent_first_with_transparent_padding` | Backend | Index 0 = newest; slots 4–13 empty |
| `test_build_streak_summary_includes_both_percentages_when_gap_is_wide` | Backend | Summary contains both % and “normal” |
| `test_mirror_streak_route_returns_fourteen_cells` | Backend | HTTP 200 + 14 cells in JSON |
| `renders 14 cells with most recent grades first...` | Frontend | `data-grade` on cells 0–13 |
| `uses PRD colour tokens for correct and incorrect cells` | Frontend | `finnwise-green` / amber / red / transparent |
| `renders summary with mechanism and market percentages` | Frontend | Summary testid text content |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**None.** P2-S5 is read-only against `public.user_predictions`:

- Grid query: `mechanism_accuracy` for last 14 rows by `logged_at DESC`.
- Stats query: `mechanism_accuracy`, `business_accuracy`, `market_accuracy`, `gap_insight` for all rows for the user.

Columns were added in P2-S2 / `0004_core_tables.sql` (accuracy enums) and `0014` (`gap_insight`).

---

### B2. API / INTEGRATION CONTRACTS

**Endpoint:** `GET /api/mirror/streak`

**Auth:** `Authorization: Bearer <supabase_access_token>`

**Response 200 (example)**

```json
{
  "cells": [
    { "letter": "M", "grade": "correct" },
    { "letter": "P", "grade": "partial" },
    { "letter": "–", "grade": "empty" }
  ],
  "mechanism_accuracy_pct": 75.0,
  "market_accuracy_pct": 50.0,
  "summary": "Your mechanism accuracy (75%) is ahead of market reaction match (50%). That gap is normal — and common for early investors. ..."
}
```

`cells` is always length **14**.

**Errors**

| Status | When |
|--------|------|
| 401 | Missing/invalid JWT |
| 503 | `SUPABASE_DB_URL` not configured or DB unreachable |

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Cell mapping (`cell_from_mechanism_grade`)**

```
mechanism_accuracy → letter / grade
─────────────────────────────────────
correct            → M / correct
partial            → P / partial
incorrect          → ✗ / incorrect
monitoring         → · / monitoring
NULL               → · / monitoring
```

**Summary template selection (`build_streak_summary`)**

```
both % NULL     → onboarding-style copy
mechanism NULL  → market-only copy
market NULL     → mechanism-only copy
mech − market ≥ 15 → “gap is normal” (primary PRD pattern)
market − mech ≥ 15 → prices moved ahead of mechanism
else            → close tracking / divergence is normal
```

**Accuracy % (`compute`)**

- Counts only `correct`, `partial`, `incorrect` (excludes `monitoring`).
- `correct / graded_count * 100`, one decimal place.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|-------|
| **Client-side fetch waterfall** | Streak loads with Mirror client bundle; not server-rendered (same as P2-S1). P2-S15 may SSR Mirror later. |
| **No Lighthouse entry for Mirror** | Mirror not yet in Lighthouse CI matrix (tracked under P2-S15). |
| **Grading required for colour** | Users with only active/ungraded predictions see mostly grey cells until cards resolve via P2-S2. |
| **Summary not i18n** | English templates only. |

---

### B5. TESTING NOTES

| Area | Automated | Manual (recommended) |
|------|-----------|-------------------|
| Cell order / padding | Yes (pytest + RTL) | — |
| Colour tokens | Partial (className assert) | Visual check on `/mirror` |
| Summary copy variants | Partial (wide-gap template) | Log in with mixed graded history |
| Auth / 503 | Route test with mock | curl without token |

**Manual smoke (see B6):** Sign in → `/mirror` → confirm right-panel “Streak tracker” with grid + legend + paragraph.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Item | Required for P2-S5? |
|------|---------------------|
| New env vars | **No** |
| DB migration | **No** |
| `SUPABASE_DB_URL` | **Yes** (existing backend requirement) |
| `GEMINI_API_KEY` | **No** (streak does not call LLM) |

**Deployment sequencing**

1. Deploy backend (new route must be live before frontend that calls it).
2. Deploy frontend.
3. No migration step.

**Local dev:** Restart backend if it was running before this story (`uvicorn` does not always pick up new router modules on reload depending on import order). Refresh the browser on `/mirror`.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing streak behaviour**

1. Read PRD §5 Screen 4 (Streak Tracker row) and §8.3 colour table.
2. Read `backend/app/services/mirror_streak.py` — all mapping logic is there.
3. If changing % semantics, update **both** `mirror_stats.compute()` consumers (stats strip + streak summary).

**Common mistakes**

- Using last-14 rows for summary percentages (wrong — full history only).
- Putting `market_accuracy` on grid letters (wrong — mechanism only).
- Padding empty slots on the left (wrong — newest is index 0 / left).

**Related code paths**

| Concern | Path |
|---------|------|
| Streak API | `backend/app/api/mirror_streak.py` |
| Streak logic | `backend/app/services/mirror_streak.py` |
| Stats % reuse | `backend/app/services/mirror_stats.py` |
| UI panel | `frontend/app/(app)/mirror/_components/StreakTrackerPanel.tsx` |
| Data load | `frontend/app/(app)/mirror/_components/MirrorClient.tsx` |

**Contact:** Sam (Mirror UI) / Jordan (grading data) per phase-2 team plan.
