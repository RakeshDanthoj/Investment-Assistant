# FinnWise — Phase 2 Implementation Tasks (Engagement Layer, Months 4–9)

_Source PRD_: `FinnWise_PRD_v3_Final.md` — Section 10 / Phase 2, with binding decisions in §5 (Screens 4 & 5), §6, §7, §11, §12.
_generated for independent execution without prd-planner_

## Overview

- **Summary**: Phase 2 introduces the engagement layer on top of the Phase 1 foundation: **The Mirror** (prediction history, three-level accuracy, reasoning-gap analysis, streak tracker), **The Lens** (on-demand ICE card generation with visible six-step pipeline), Portfolio Protector personalisation against session-only holdings, email notifications when signals fire, expansion of the Factor Exposure DB to all eight sectors plus The Map content, **stronger market/macro inputs for the signal-confidence gate** (beyond `events` titles), and a UI polish pass driven by Phase 1 tester feedback.
- **Tech stack**: same as Phase 1 (Next.js + Tailwind, FastAPI, Supabase, Google Gemini, Vercel, Render). New additions: a lightweight email provider (Resend or Postmark free tier) and Server-Sent Events for the Lens pipeline progress stream. Tests: Jest + RTL (frontend), Pytest (backend). Single `.env.local`.
- **Slicing approach**: every story is an end-to-end vertical slice (UI + API + DB minimum) with explicit test step(s). Parent task IDs are **per-phase** — this file uses `1.0`–`14.0`. All PRD §6 / §8.6 / §11 constraints from Phase 1 continue to apply unchanged.
- **Prerequisite**: Phase 1 is fully shipped and stable (Onboarding, Pulse, Thread, LLM pipeline, signal monitor, track record, bias audit); **Phase 1.5 is closed** (performance remediation + Lighthouse CI — see `docs/Post Implementation documentation/Phase1_P1.5 - Performance remediation Pulse and Thread.md`); at least one tester cohort has completed three sessions.

## Performance standards (from Phase 1.5 — apply to every Phase 2 story)

All new and modified **user-facing routes** (Mirror, Lens, Map, settings, etc.) MUST follow these practices established in Phase 1.5. Formal checklist: **`docs/plans/cross-phase-performance-standards.md`** (authored in **P2-S15**).

| Area | Rule | Reference |
|------|------|-----------|
| **First paint** | Server-fetch initial data in RSC/`page.tsx`; pass `initialData` into client hooks; avoid client-only waterfall on load | P1.5-S5/S6 — `frontend/lib/api/server.ts` |
| **Client refetch** | Category filters, view toggles, retry only — keep `fetch(..., { cache: "no-store" })`; verify CORS on `/backend` paths | P1.5-S4/S10 |
| **Bundles** | `next/dynamic` for heavy below-fold or tab panels; scope editorial fonts to routes that need them | P1.5-S7 |
| **Backend reads** | One pool connection per request; published feed/card `Cache-Control: private, max-age=60` | P1.5-S2/S3/S4 |
| **Measurement** | Never treat **`next dev`** Lighthouse as production truth; local parity = `pnpm build && pnpm start` | `scripts/README.md` |
| **CI budgets** | Mobile: perf ≥90, TBT &lt;200 ms, SI &lt;3400 ms; Desktop: TBT &lt;150 ms, SI &lt;2400 ms | `scripts/lighthouse.mjs`, `scripts/lighthouse-budget.mjs` |
| **API latency** | Warm **p95 &lt;800 ms** on `/api/feed` and `/api/cards/{id}` (direct or proxy path used in prod) | `scripts/bench_api_latency.mjs` — **Phase 2.5** (`finnwise-phase2.5-implementation-tasks.md` § P2.5-S2); bench run started in P2-S15 |
| **New routes** | When adding an `(app)` page, extend Lighthouse runner + CI in the **same PR** or track under P2-S15 / Phase 2.5 | P1.5-S9/S9b |

**PR checklist (perf):** SSR initial load → dynamic splits for heavy UI → run `pnpm perf:lighthouse` on production URL (or preview) before merge for touched surfaces.

## Team plan

| Developer | Focus | Total points |
|-----------|-------|---------------|
| Jordan | Mirror grading service, Lens loading stream, Portfolio Protector backend, **signal-monitor fact pipeline**, cost & rate-limit hardening | 24 |
| Sam | Mirror UI (prediction list, streak), Lens UI (query / loading / result states), Phase 1 polish iteration | 24 |
| Riley | Reasoning-gap analysis, resolved-card notification system, email channel, Factor DB expansion to 8 sectors + Map content, **P2-S15 perf close-out** | 23 |

---

## Phase 2: Engagement Layer

_Add the personal learning surface (The Mirror) and the on-demand research surface (The Lens), personalise the existing surfaces to Portfolio Protectors, and complete the Factor Exposure DB across all 8 sectors._ · **Duration estimate:** 24 weeks (6 months).

### Story P2-S1 — The Mirror — prediction history list + stats strip

- **Assigned:** Sam
- **Points:** 6
- **Layers:** UI, API, DB
- **Depends on:** Phase 1 (P1-S12 prediction logger, P1-S4 schema)
- **Parallel with:** P2-S2, P2-S6

**User story**

> As a returning user, I want to see my prediction history with a four-stat strip (Total / Mechanism Accuracy / Market Reaction Match / Reasoning Gaps Found) and expandable per-prediction cards, so that I can see at a glance whether my reasoning is improving.

**Acceptance criteria**

- [x] Route `/(app)/mirror` reachable from sidebar; protected behind auth.
- [x] Topbar: "The Mirror" + subtitle + notification badge slot (filled by P2-S3).
- [x] Stats strip: four cells per PRD §5 Screen 4 — Playfair 28px number + DM Mono 10px label + Inter 11px subtext. Accuracy numbers coloured green (≥70%) or amber (<70%).
- [x] Filter pills above list: All / Resolved / Active / Pending.
- [x] Prediction Card per PRD §5: event tag + headline + "Your call: ..." + status badge + three-level accuracy meter; expandable inline (no navigation) to reveal Gap Insight + Map module link.
- [x] **Zero rupee figures anywhere on this surface** (PRD §5 Screen 4 design decision) — lint test asserts no `₹` substrings in the page subtree.

**Tech notes**

- API: `GET /api/mirror/predictions?status=` returns predictions joined with cards and accuracy grades. Grading itself lives in P2-S2.
- UI: list virtualisation only if >100 items; otherwise plain map.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/mirror/page.tsx` | create | Page |
| `frontend/app/(app)/mirror/_components/StatsStrip.tsx` | create | Four-stat header |
| `frontend/app/(app)/mirror/_components/FilterPills.tsx` | create | All/Resolved/Active/Pending |
| `frontend/app/(app)/mirror/_components/PredictionCard.tsx` | create | Expandable per-prediction card |
| `frontend/app/(app)/mirror/_components/AccuracyMeter.tsx` | create | Three-level mini bars |
| `frontend/app/(app)/mirror/_components/GapInsightExpanded.tsx` | create | Reveal block |
| `backend/app/api/mirror.py` | create | `GET /api/mirror/predictions` + `/stats` |
| `backend/app/services/mirror_stats.py` | create | Stats computation |
| `backend/tests/test_mirror_stats.py` | create | Asserts coloured-by-threshold logic |
| `frontend/app/(app)/mirror/page.test.tsx` | create | Asserts zero `₹` substrings |
| `frontend/app/(app)/mirror/_components/AccuracyMeter.test.tsx` | create | Asserts three independent bars rendered |

#### Tasks (checkboxes)

- [x] **1.0** The Mirror — prediction history list + stats strip
  - [x] **1.1** `GET /api/mirror/predictions` — filter by status, paginated, includes joined card metadata.
  - [x] **1.2** `GET /api/mirror/stats` — total / mechanism % / market % / gaps count.
  - [x] **1.3** `mirror_stats.compute(user_id)` pure function with tested thresholds.
  - [x] **1.4** Page shell + `StatsStrip` reading the stats endpoint.
  - [x] **1.5** `FilterPills` syncing to URL params.
  - [x] **1.6** `PredictionCard` with status badge + three accuracy meter slots.
  - [x] **1.7** `AccuracyMeter` — three labelled bars (Mechanism / Business Impact / Market Reaction) with correct / partial / incorrect / monitoring states.
  - [x] **1.8** `GapInsightExpanded` slot — populated by P2-S4.
  - [x] **1.9** Empty state + loading skeleton + error retry.
  - [x] **1.10** Test: stats threshold colouring; no-rupee assertion; three independent bars; filter URL sync.

---

### Story P2-S2 — The Mirror — three-level accuracy grading service

- **Assigned:** Jordan
- **Points:** 6
- **Layers:** Services, DB, API
- **Depends on:** Phase 1 (P1-S4 track_record, P1-S12 user_predictions), P2-S1 (consumer)
- **Parallel with:** P2-S6, P2-S11

**User story**

> As the platform, I want a grading service that, when a card resolves, scores every user prediction at three levels — Mechanism / Business Impact / Market Reaction — so that the user sees an honest split-rating rather than a single misleading score.

**Acceptance criteria**

- [x] Job runs on every card transition to `resolved`; idempotent per (user, card).
- [x] Three accuracy fields per `user_predictions` row populated: `mechanism_accuracy`, `business_accuracy`, `market_accuracy` each in `{correct, partial, incorrect, monitoring}`.
- [x] Grading inputs are exclusively the immutable Original View (`track_record` Day 1 row) and the final card state — never an interim revision.
- [x] Gap Insight text written to `user_predictions.gap_insight` (consumed by P2-S4).
- [x] Reasoning encoded — never a generic "markets are unpredictable" (PRD §5 Screen 4 design decision).

**Tech notes**

- Grading uses a structured Sonnet call with explicit rubric per level; output validated against the three enum sets.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/prompts/grading.v1.md` | create | Three-level rubric |
| `backend/app/services/prediction_grader.py` | create | Grader |
| `backend/app/jobs/grade_on_resolve.py` | create | Triggered on card resolve |
| `backend/db/migrations/0010_user_predictions_accuracy_cols.sql` | create | Add three accuracy + gap_insight columns |
| `backend/tests/test_prediction_grader.py` | create | Fixture cards + expected grades |
| `backend/tests/test_grader_uses_original_view.py` | create | Asserts inputs are Day 1 snapshot |

#### Tasks (checkboxes)

- [x] **2.0** The Mirror — three-level accuracy grading service
  - [x] **2.1** Migration: add `mechanism_accuracy`, `business_accuracy`, `market_accuracy`, `gap_insight` to `user_predictions`.
  - [x] **2.2** Author `grading.v1.md` with explicit rubric per level + forbid generic gap explanations.
  - [x] **2.3** `prediction_grader.grade(prediction, original_card, final_card)` — three-level output + gap insight.
  - [x] **2.4** `grade_on_resolve` job hooks card state transition to `resolved`.
  - [x] **2.5** Persist three accuracy columns + gap insight + append a row to `track_record` summarising the grade.
  - [x] **2.6** Idempotency: re-running job on already-graded predictions is a no-op.
  - [x] **2.7** Test: fixture-card grading; assert Original View is the source; idempotency test.

---

### Story P2-S3 — Resolved-card notification system + topbar badge

- **Assigned:** Riley
- **Points:** 4
- **Layers:** Services, API, UI
- **Depends on:** P2-S2 (grading writes the notification trigger)
- **Parallel with:** P2-S1, P2-S6

**User story**

> As a returning user, I want a pulsing badge in The Mirror's topbar that says "N cards resolved — ready to grade" so that I am pulled back into the app to close the feedback loop.

**Acceptance criteria**

- [x] Badge visible only when ≥1 of the user's predictions has just transitioned to a graded state and the user has not yet viewed it.
- [x] Tapping the badge scrolls/expands the relevant card in the prediction history (P2-S1 list).
- [x] Dismissal happens only on view, not on tap-away.
- [x] Notifications table reused from Phase 1 (P1-S11) with a new `kind='card_graded'` value.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/0015_notifications_card_graded_read_at.sql` | create | `read_at` + index for unread `card_graded` |
| `backend/app/services/notify_on_grade.py` | create | Fan-out on resolve |
| `backend/app/api/mirror_notifications.py` | create | `GET /api/mirror/notifications/unread` |
| `frontend/app/(app)/mirror/_components/ResolvedBadge.tsx` | create | Pulsing badge |
| `frontend/app/(app)/mirror/_components/ReadyToGradePanel.tsx` | create | Right-panel item list |
| `frontend/app/(app)/mirror/_components/ResolvedBadge.test.tsx` | create | RTL test |
| `backend/tests/test_notify_on_grade.py` | create | Fan-out only to users with logged predictions |

#### Tasks (checkboxes)

- [x] **3.0** Resolved-card notification system + topbar badge
  - [x] **3.1** Add `card_graded` to notification kind enum.
  - [x] **3.2** `notify_on_grade.fan_out(card_id)` — one notification per user with a graded prediction.
  - [x] **3.3** `GET /api/mirror/notifications/unread` returns count + list.
  - [x] **3.4** `ResolvedBadge` with pulsing dot animation (reuses §8.6 keyframe).
  - [x] **3.5** `ReadyToGradePanel` right-panel — green-tinted items, each clickable to scroll/expand the card.
  - [x] **3.6** Mark notification read on viewport-intersection with the corresponding card (not on tap-elsewhere).
  - [x] **3.7** Test: fan-out scope; badge hidden when zero unread; RTL pulsing-class assertion.

---

### Story P2-S4 — Reasoning-gap analysis + Map module linking

- **Assigned:** Riley
- **Points:** 5
- **Layers:** Services, DB, UI
- **Depends on:** P2-S2 (gap_insight values), P2-S11 (Map content)
- **Parallel with:** P2-S5, P2-S7

**User story**

> As a self-aware learner, I want The Mirror to surface three concrete reasoning gaps derived from my prediction history and link each one to a specific Map module that addresses it, so that my next reading is targeted.

**Acceptance criteria**

- [x] `reasoning_gap_detector.analyse(user_id)` returns top-3 gaps with `gap_name`, `pattern_explanation`, `linked_map_module_id`.
- [x] Gaps derived from actual patterns (e.g. consistently correct on mechanism but wrong on market reaction) — not manually assigned.
- [x] Gap items rendered in the right-panel "Reasoning Gap Analysis" with icon + name (Inter 13px bold) + explanation + `🗺 The Map: [module name] →`.
- [x] Map links resolve to real modules created in P2-S11.
- [x] Recomputes on every new resolved prediction (or on demand via "Refresh analysis").

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/reasoning_gap_detector.py` | create | Pattern-mining over user_predictions |
| `backend/app/api/mirror_gaps.py` | create | `GET /api/mirror/gaps` |
| `frontend/app/(app)/mirror/_components/ReasoningGapPanel.tsx` | create | Right-panel block |
| `backend/tests/test_reasoning_gap_detector.py` | create | Fixture histories → expected gaps |
| `frontend/app/(app)/mirror/_components/ReasoningGapPanel.test.tsx` | create | RTL render + link |

#### Tasks (checkboxes)

- [x] **4.0** Reasoning-gap analysis + Map module linking
  - [x] **4.1** Define gap taxonomy (e.g. "Direction-correct, magnitude-wrong", "Anchored on narrative", "Sector concentration in your predictions") with linked Map module IDs.
  - [x] **4.2** `reasoning_gap_detector.analyse(user_id)` — heuristic + LLM-light pattern detection.
  - [x] **4.3** `GET /api/mirror/gaps` returns top-3.
  - [x] **4.4** `ReasoningGapPanel` UI — three items, each linking to `/map?module=[moduleId]` (redirects to sector page when applicable).
  - [x] **4.5** Gap insight inside the expanded PredictionCard (P2-S1 slot) reads `user_predictions.gap_insight` directly.
  - [x] **4.6** Recompute trigger on grade-on-resolve job tail.
  - [x] **4.7** Test: fixture histories yield expected gap names; UI renders the three items.

---

### Story P2-S5 — Streak tracker grid + summary

- **Assigned:** Sam
- **Points:** 4
- **Layers:** UI, API
- **Depends on:** P2-S2 (accuracy values)
- **Parallel with:** P2-S4, P2-S6

**User story**

> As a learner, I want a 14-cell streak grid of my last 14 predictions with a plain-English summary comparing mechanism accuracy to market-reaction accuracy, so that I can see patterns at a glance.

**Acceptance criteria**

- [x] Grid renders 14 cells, each colour-coded green / amber / red / grey / transparent per PRD §5 Screen 4 spec.
- [x] DM Mono letters inside cells: `M / P / ✗ / · / –`.
- [x] Summary paragraph below grid compares mechanism % to market % and explains why a gap is normal.
- [x] Sorted most recent first; missing slots render transparent.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/mirror/_components/StreakTracker.tsx` | create | 14-cell grid |
| `frontend/app/(app)/mirror/_components/StreakSummary.tsx` | create | Plain-English block |
| `backend/app/api/mirror_streak.py` | create | `GET /api/mirror/streak` |
| `backend/tests/test_mirror_streak.py` | create | Cell ordering + transparent slots |
| `frontend/app/(app)/mirror/_components/StreakTracker.test.tsx` | create | RTL test |

#### Tasks (checkboxes)

- [x] **5.0** Streak tracker grid + summary
  - [x] **5.1** `GET /api/mirror/streak` returns last 14 grading events (some may be `monitoring` / transparent).
  - [x] **5.2** `StreakTracker` renders 14 cells, exact colour map from PRD §8.3.
  - [x] **5.3** `StreakSummary` compares mechanism % vs market % and templates the explanation paragraph.
  - [x] **5.4** Legend row below the grid.
  - [x] **5.5** Test: ordering most-recent first; transparent rendering for missing slots; summary numerics.

---

### Story P2-S6 — The Lens — query input + history + examples

- **Assigned:** Sam
- **Points:** 5
- **Layers:** UI, API, DB
- **Depends on:** Phase 1 schema (cards), P1-S3 auth
- **Parallel with:** P2-S2, P2-S11

**User story**

> As a curious user, I want to type a question about any event into The Lens and see a 2×3 example grid plus my recent query history, so that I can either ask my own question or learn what The Lens is capable of.

**Acceptance criteria**

- [x] Route `/(app)/lens` reachable from sidebar; sidebar shows the Phase 2 purple badge in topbar.
- [x] Query text area min 80px, placeholder exactly as PRD §5 Screen 5.
- [x] Sector + Horizon optional dropdowns in the query-box footer.
- [x] "Generate card →" disabled until input >10 chars.
- [x] DM Mono time-estimate note: "Cards take 30–90 seconds to generate."
- [x] 2×3 example query grid with coloured category tags; clicking fills the textarea.
- [x] Recent query history list with relative dates; clicking navigates to result state for that query.
- [x] No page navigation between input / loading / result states.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/lens/page.tsx` | create | Lens shell w/ state machine |
| `frontend/app/(app)/lens/_components/QueryInput.tsx` | create | Textarea + dropdowns + CTA |
| `frontend/app/(app)/lens/_components/ExampleGrid.tsx` | create | 2×3 examples |
| `frontend/app/(app)/lens/_components/QueryHistory.tsx` | create | Recent queries |
| `frontend/app/(app)/lens/_components/PhaseBadge.tsx` | create | Purple Phase 2 pill |
| `frontend/lib/lens/useLensState.ts` | create | Query/Loading/Result state machine |
| `backend/db/migrations/0016_lens_queries.sql` | create | `lens_queries(id, user_id, query, sector, horizon, status, created_at)` |
| `backend/app/api/lens.py` | create | `POST /api/lens/queries` + `GET /api/lens/queries/me` |
| `frontend/lib/lens/useLensState.test.ts` | create | State-machine tests |
| `frontend/app/(app)/lens/_components/QueryInput.test.tsx` | create | CTA disabled <10 chars |

#### Tasks (checkboxes)

- [x] **6.0** The Lens — query input + history + examples
  - [x] **6.1** Migration: `lens_queries` table with `status` enum (`queued`, `running`, `done`, `failed`).
  - [x] **6.2** `POST /api/lens/queries` creates a row, returns id, enqueues for generation.
  - [x] **6.3** `GET /api/lens/queries/me` returns user's recent 20.
  - [x] **6.4** `useLensState` reducer: `idle → submitting → loading → result | error`. URL hash for shareability.
  - [x] **6.5** `QueryInput` with sector + horizon dropdowns; CTA disabled <10 chars.
  - [x] **6.6** Time-estimate note below box (DM Mono 10px slate-400).
  - [x] **6.7** `ExampleGrid` with six static examples covering Macro / RBI / Regulatory / India-specific / Geopolitical / Budget.
  - [x] **6.8** `QueryHistory` list with relative dates.
  - [x] **6.9** `PhaseBadge` purple pill in topbar.
  - [x] **6.10** Test: state-machine transitions; CTA gating; example-tap fills textarea.

---

### Story P2-S7 — The Lens — loading state with live six-step pipeline

- **Assigned:** Jordan
- **Points:** 5
- **Layers:** API (SSE), Services, UI
- **Depends on:** P2-S6 (queries table), Phase 1 (P1-S7 pipeline)
- **Parallel with:** P2-S4, P2-S5

**User story**

> As a Lens user waiting 30–90 seconds, I want to see the six pipeline steps animate live — pending → active (pulsing) → done — so that the wait feels like rigour, not a spinner.

**Acceptance criteria**

- [x] Six steps named exactly per PRD §5 Screen 5: Factor DB queried / Macro signals retrieved / Synthesising ICE layers / Generating dissenting view / Articulating framework / Validating numbers against Evidence.
- [x] Stream is Server-Sent Events at `GET /api/lens/queries/{id}/stream`.
- [x] Each step transitions on real backend milestones — not faked time slices.
- [x] Loading card centred, max 560px, with user query displayed in Playfair italic.
- [x] Bottom disclaimer present verbatim: "Every number is validated against the Evidence layer before display."

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/api/lens_stream.py` | create | SSE endpoint |
| `backend/app/services/lens_pipeline.py` | create | Emits step events from `card_pipeline` |
| `frontend/app/(app)/lens/_components/LoadingCard.tsx` | create | Centred loading UI |
| `frontend/app/(app)/lens/_components/PipelineStep.tsx` | create | Single step row |
| `frontend/lib/lens/useLensStream.ts` | create | EventSource hook |
| `backend/tests/test_lens_stream_six_steps.py` | create | Asserts six named events emitted |
| `frontend/app/(app)/lens/_components/LoadingCard.test.tsx` | create | RTL test |

#### Tasks (checkboxes)

- [x] **7.0** The Lens — loading state with live six-step pipeline
  - [x] **7.1** `lens_pipeline.run(query_id)` instruments `card_pipeline` with six `yield`ed milestones.
  - [x] **7.2** `GET /api/lens/queries/{id}/stream` SSE endpoint that consumes the pipeline iterator.
  - [x] **7.3** `LoadingCard` centred component with query echo in Playfair italic.
  - [x] **7.4** `PipelineStep` with state classes: pending (grey) / active (blue pulsing) / done (green ✓).
  - [x] **7.5** `useLensStream` hook connects EventSource, updates step state in reducer.
  - [x] **7.6** Progress bar component (0→100%) interpolating between milestones.
  - [x] **7.7** Disclaimer text rendered verbatim.
  - [x] **7.8** Test: six events emitted in order; UI transitions pending→active→done correctly.

---

### Story P2-S8 — The Lens — result rendering + Save to Thread

- **Assigned:** Sam
- **Points:** 5
- **Layers:** UI, API, DB
- **Depends on:** Phase 1 (P1-S10 Thread components, P1-S7 pipeline), P2-S7
- **Parallel with:** P2-S9

**User story**

> As a Lens user, I want the generated card to render in the same ICE structure as Thread cards — with a mandatory "Lens limitations" aside — and to be able to Save to Thread so a useful Lens card becomes a persistent Living Card.

**Acceptance criteria**

- [x] Result reuses InsightLayer / ContextLayer / EvidenceLayer / DissentingView / InstrumentCard / FrameworkBehindThis from Phase 1 — no duplication.
- [x] Aside includes Confidence Composition with Lens-specific note (higher Judged proportion) + applicable bias flags + **mandatory** Lens Limitations block with the exact PRD copy.
- [x] "Save to Thread" copies the card to the user's personal Thread collection (a `saved_threads` join table) and surfaces it in sidebar.
- [x] "← New query" returns to query state, preserving textarea content.
- [x] Meta row shows generation time and date.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/lens/_components/ResultCard.tsx` | create | Wraps Phase 1 ICE components |
| `frontend/app/(app)/lens/_components/LensLimitations.tsx` | create | Mandatory aside block |
| `frontend/app/(app)/lens/_components/SaveToThreadButton.tsx` | create | Save action |
| `backend/db/migrations/0019_saved_threads.sql` | create | `saved_threads(user_id, card_id, saved_at)` |
| `backend/app/api/saved_threads.py` | create | `POST /api/saved-threads` + list |
| `frontend/app/(app)/lens/_components/LensLimitations.test.tsx` | create | Asserts block present + exact copy |
| `backend/tests/test_saved_threads.py` | create | Idempotent save per (user, card) |

#### Tasks (checkboxes)

- [x] **8.0** The Lens — result rendering + Save to Thread
  - [x] **8.1** `ResultCard` composes the existing Phase 1 ICE components against the new card payload.
  - [x] **8.2** `LensLimitations` aside block — mandatory, exact PRD §5 Screen 5 copy.
  - [x] **8.3** Confidence Composition aside with the Lens-specific explanatory note.
  - [x] **8.4** Bias Flags aside reading the same `card_bias_flags` mechanism from Phase 1.
  - [x] **8.5** Meta row: event type tag + horizon tag + "Generated in Xs · Date".
  - [x] **8.6** Migration + API: `saved_threads` with unique `(user_id, card_id)`.
  - [x] **8.7** `SaveToThreadButton` with toast confirmation.
  - [x] **8.8** Sidebar surface for saved threads under a "Saved" sub-nav.
  - [x] **8.9** "← New query" — restores textarea content from `useLensState`.
  - [x] **8.10** Test: `LensLimitations` always rendered; save idempotent; "← New query" preserves text.

---

### Story P2-S9 — Portfolio Protector personalisation (session-only holdings)

- **Assigned:** Jordan
- **Points:** 5
- **Layers:** UI, API
- **Depends on:** P1-S2 (mode detection), P1-S9 (Pulse)
- **Parallel with:** P2-S8, P2-S11

**User story**

> As a Portfolio Protector, I want to enter my current holdings into a session-only form so The Pulse and The Thread surface the events that actually affect what I own — without FinnWise ever persisting that financial data.

**Acceptance criteria**

- [x] Holdings collected via a lightweight modal launched from the user chip; persisted **only** in encrypted browser session storage (PRD §11.1 — no user financial data stored beyond session).
- [x] Backend never sees the per-stock list — instead the client sends an opaque `personalisation_token` (hashed list of instrument IDs) per request.
- [x] Pulse feed re-ranks based on the token; top of feed = cards whose instrument assessments intersect the user's holdings.
- [x] Thread shows a per-holding "what this means for your XYZ" callout when intersection is non-empty.
- [x] Modal includes a clear "this data is not stored on our servers" line.

**Tech notes**

- Session-only storage uses `sessionStorage` plus an HMAC keyed by the user session — never persisted in IndexedDB or cookies.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/components/Holdings/HoldingsModal.tsx` | create | Holdings entry UI |
| `frontend/lib/personalisation/sessionHoldings.ts` | create | Session storage + token derivation |
| `backend/app/api/feed.py` | modify | Accept `personalisation_token` |
| `backend/app/services/feed_ranker.py` | create | Re-rank by token-set intersection |
| `frontend/app/(app)/thread/_components/HoldingCallout.tsx` | create | Inline callout |
| `backend/tests/test_feed_personalisation.py` | create | Token intersection re-rank |
| `frontend/lib/personalisation/sessionHoldings.test.ts` | create | Asserts session-only persistence |

#### Tasks (checkboxes)

- [x] **9.0** Portfolio Protector personalisation (session-only holdings)
  - [x] **9.1** `HoldingsModal` triggered from user chip; typeahead from instruments table.
  - [x] **9.2** `sessionHoldings.save/get/clear` — backed by `sessionStorage`, cleared on tab close.
  - [x] **9.3** Derive `personalisation_token` (hashed, salted instrument-id set) on client.
  - [x] **9.4** `GET /api/feed` accepts optional token; `feed_ranker.rerank(cards, token)` reorders.
  - [x] **9.5** `HoldingCallout` rendered on Thread when intersection non-empty.
  - [x] **9.6** Explicit "not stored on our servers" copy in the modal.
  - [x] **9.7** Test: token-based re-rank; session-only persistence; intersection callout visibility.

---

### Story P2-S10 — Email notifications for fired signals

- **Assigned:** Riley
- **Points:** 4
- **Layers:** Services, DB, UI
- **Depends on:** P1-S11 (signal monitor), P1-S12 (predictions)
- **Parallel with:** P2-S9, P2-S11

**User story**

> As a user with logged predictions, I want an email when a signal fires on a card I have predicted on (or saved), so that I can return to the app at the right moment.

**Acceptance criteria**

- [x] Email provider integration (Resend or Postmark) with templates in `backend/email-templates/`.
- [x] Trigger: `signal_state` transitions to `triggered` on a card with a logged prediction or saved-thread row for the user.
- [x] One-click unsubscribe link present in every email (anti-spam compliance).
- [x] `user_email_preferences` table; default opt-in for Phase 2 testers; opt-out preserved.
- [x] Email never contains a recommendation — only "a signal you were watching has fired, view it in FinnWise".

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/0017_user_email_preferences.sql` | create | Prefs + unsubscribe tokens + send log |
| `backend/app/services/email_client.py` | create | Provider abstraction |
| `backend/email-templates/signal_fired.html` | create | Plain HTML template |
| `backend/app/jobs/email_on_signal.py` | create | Trigger on signal transitions |
| `backend/app/api/unsubscribe.py` | create | `GET /unsubscribe?token=` |
| `frontend/app/(app)/settings/email/page.tsx` | create | Manage preferences |
| `backend/tests/test_email_on_signal.py` | create | Fan-out only to opted-in predicting users |
| `backend/tests/test_unsubscribe.py` | create | Token use is single-shot |

#### Tasks (checkboxes)

- [x] **10.0** Email notifications for fired signals
  - [x] **10.1** Provider credentials in `.env.local` (`EMAIL_PROVIDER`, `EMAIL_API_KEY`, `EMAIL_FROM`).
  - [x] **10.2** Migration: `user_email_preferences` + `unsubscribe_tokens`.
  - [x] **10.3** `email_client.send(template, vars, to)` provider-agnostic.
  - [x] **10.4** Template: signal-fired (no buy/sell/hold copy; deep link to Thread).
  - [x] **10.5** `email_on_signal.fan_out(card_id, signal_id)` — only opted-in users with stake (prediction or saved).
  - [x] **10.6** `GET /unsubscribe?token=` flips prefs.
  - [x] **10.7** Settings page to view/change prefs.
  - [x] **10.8** Test: fan-out scope; unsubscribe single-shot; template lints clean of forbidden language.

---

### Story P2-S11 — Factor DB expansion to all 8 sectors + The Map content

- **Assigned:** Riley
- **Points:** 7
- **Layers:** DB, UI
- **Depends on:** Phase 1 (P1-S5 Banking slice tooling)
- **Parallel with:** P2-S2, P2-S4, P2-S9

**User story**

> As any user, I want The Map to cover all eight sectors of the Indian economy with navigable sector pages, so that Portfolio Builders can learn before being routed to event cards and Reasoning Gap links (P2-S4) resolve to real content.

**Acceptance criteria**

- [x] All 8 PRD §7.1 factors fully seeded across the 8 target sectors covering ≥120 of the top 150 NSE stocks.
- [x] `/(app)/map` lists sectors with cover tiles; each sector page documents the sector's factor sensitivities + a "How this sector reacts to events" module.
- [x] At least 1 Reasoning Gap → Map module link exists per gap type defined in P2-S4.
- [x] Every sensitivity row keeps the MMJ + source-URL invariant from Phase 1.
- [x] Sector pages render the Map module content that P2-S4 links to.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/seeds/sectors/*.sql` | create | One seed file per sector (8 files) |
| `backend/db/migrations/0018_map_modules.sql` | create | `map_modules(id, sector, title, body, linked_gap_types[])` |
| `backend/app/api/map.py` | create | `GET /api/map/sectors` + `GET /api/map/sectors/{slug}` |
| `frontend/app/(app)/map/page.tsx` | create | Sector index |
| `frontend/app/(app)/map/[slug]/page.tsx` | create | Sector detail + module list |
| `frontend/app/(app)/map/_components/SectorTile.tsx` | create | Cover tile |
| `frontend/app/(app)/map/_components/MapModule.tsx` | create | Module renderer |
| `backend/tests/test_factor_db_coverage.py` | create | ≥120 instruments × 8 factors, all MMJ-tagged |

#### Tasks (checkboxes)

- [x] **11.0** Factor DB expansion to all 8 sectors + The Map content
  - [x] **11.1** Author seed files: IT / Energy & Oil / Consumer (FMCG) / Auto / Pharma / Metals & Materials / Telecom / Infra & Capital Goods (banking already done in P1-S5).
  - [x] **11.2** Migration + seed: `map_modules` for each sector with the "How this sector reacts" body.
  - [x] **11.3** `GET /api/map/sectors` index + `GET /api/map/sectors/{slug}` detail.
  - [x] **11.4** `/(app)/map` index page rendering `SectorTile`s.
  - [x] **11.5** `/(app)/map/[slug]` rendering the sensitivity matrix subset + modules.
  - [x] **11.6** Cross-link from P2-S4 reasoning gaps to the matching module IDs.
  - [x] **11.7** Test: factor-DB coverage (≥120 instruments × 8 factors, all MMJ-tagged); Map module endpoint returns linked modules for known gap types.

---

### Story P2-S12 — Phase 1 UI polish + tester-feedback iteration

- **Assigned:** Sam
- **Points:** 4
- **Layers:** UI, A11y, Perf
- **Depends on:** Phase 1 tester feedback collected
- **Parallel with:** every other P2 story

**User story**

> As a Phase 1 tester graduating into Phase 2, I want the visible UX rough edges I flagged in Phase 1 polished — accessibility, performance, copy clarity — so that the engagement-layer additions land on a clean base.

**Acceptance criteria**

- [x] Backlog of tester findings captured in `notes/phase1-feedback-backlog.md` (gitignored), each item triaged P0/P1/P2.
- [x] All P0 findings closed before any P2 story ships to testers.
- [x] WCAG AA contrast verified on PRD §8.3 palette; automated check via `axe` in tests.
- [x] Lighthouse score ≥90 on Pulse, Thread (continuous — harness from P1.5-S9); Mirror, Lens, Map budgets enforced after **P2-S15** extends the runner.
- [x] New/changed routes follow **`docs/plans/cross-phase-performance-standards.md`** (SSR, bundle splits, no `next dev` benchmarking).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `notes/phase1-feedback-backlog.md` | create | Triaged backlog (gitignored) |
| `frontend/tests/a11y/*.test.tsx` | create | `axe` automated checks per surface |
| `scripts/lighthouse.mjs` | modify | Extend URLs for new surfaces (**P2-S15**) |
| `docs/plans/cross-phase-performance-standards.md` | create | Cross-phase perf checklist (**P2-S15**) |

#### Tasks (checkboxes)

- [x] **12.0** Phase 1 UI polish + tester-feedback iteration
  - [x] **12.1** Collect + triage Phase 1 tester feedback into `notes/phase1-feedback-backlog.md`.
  - [x] **12.2** Close every P0 item.
  - [x] **12.3** Add `axe` automated a11y check across Pulse, Thread, Mirror, Lens.
  - [x] **12.4** Pulse + Thread remain green on existing P1.5 Lighthouse CI job; Mirror/Lens/Map extension tracked in **P2-S15**.
  - [x] **12.5** Copy clarity pass on Insight Panel + Instrument Card reasoning blocks.
  - [x] **12.6** Test: a11y suite green; Pulse/Thread Lighthouse budgets enforced in CI.

---

### Story P2-S13 — Rate-limit guard + LLM cost ceiling + observability

- **Assigned:** Jordan
- **Points:** 4
- **Layers:** Services, Ops
- **Depends on:** Phase 1 (P1-S7 `cost_guard`), Phase 2 (P2-S7 lens stream)
- **Parallel with:** every other P2 story

**User story**

> As the platform owner, I want explicit per-user rate limits on `/api/lens/queries`, an absolute monthly LLM cost ceiling, and structured logs/metrics on pipeline performance, so that Phase 2's expanded usage cannot blow the ₹20K research budget.

**Acceptance criteria**

- [x] Per-user rate limit: 10 Lens queries/day; 429 with `retry-after` past the limit.
- [x] Monthly cost ceiling: pipeline aborts and surfaces a clear error when projected month cost > ₹X budget threshold (configurable).
- [x] Structured logs (JSON) on every pipeline run with prompt_version + token counts + duration.
- [x] Basic metrics endpoint (`/api/admin/metrics`) gated to admin allow-list.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/middleware/rate_limit.py` | create | Token-bucket per user |
| `backend/app/services/cost_guard.py` | modify | Monthly ceiling + projection |
| `backend/app/api/admin_metrics.py` | create | Aggregate metrics |
| `backend/app/core/logging.py` | create | Structured JSON logger |
| `backend/tests/test_rate_limit.py` | create | 429 after N |
| `backend/tests/test_cost_guard_monthly_ceiling.py` | create | Aborts past projection |

#### Tasks (checkboxes)

- [x] **13.0** Rate-limit guard + LLM cost ceiling + observability
  - [x] **13.1** `rate_limit` middleware — per-user token bucket; 10 Lens queries/day.
  - [x] **13.2** Extend `cost_guard` with monthly projection from rolling token spend.
  - [x] **13.3** Structured JSON logger on every pipeline run.
  - [x] **13.4** `/api/admin/metrics` — daily card count, p95 generation time, override rate, signal false-positive rate (PRD §13 metrics).
  - [x] **13.5** Test: 429 path; monthly ceiling abort; metrics shape.

---

### Story P2-S14 — Signal monitor: richer market + macro fact sources

- **Assigned:** Jordan
- **Points:** 4
- **Layers:** Services, jobs (consumer)
- **Depends on:** Phase 1 (P1-S11 signal monitor, P1-S6 event ingest); optional alignment with existing **NSE announcements** / NewsAPI adapters
- **Parallel with:** P2-S10 (email), P2-S11 (Factor DB / Map)

**User story**

> As the platform, I want the scheduled signal monitor to corroborate card signals against **actionable market and macro lines** — not only generic `events` table titles — so High/Medium/Low confidence routing better reflects listing, index, and announcement reality where data is available.

**Acceptance criteria**

- [x] **Unified fact feed:** `run_signal_monitor`’s default path (production) builds the `MarketFact` list by **merging** at least two streams: (a) existing recent **`events`** rows (macro/ingest proxy), and (b) at least one **market-leaning** stream with stable `source_id`, text line, and `observed_at`.
- [x] **Market stream (minimum bar):** e.g. **NSE corporate announcements** and/or **benchmark index level / move** lines (Nifty/Sensex or agreed substitute), sourced via an adapter that reuses or extends Phase 1 source patterns (`app/sources/*`), with timeouts and parse fallbacks documented.
- [x] **No silent empty prod:** if a stream fails, log and continue; document which streams are optional vs required per env.
- [x] **Configuration:** feature flags or env toggles to disable brittle sources without code deploy where practical.
- [x] **Tests:** unit tests for merge + dedup-by-`source_id`; at least one fixture-based test proving `evaluate()` sees facts from both streams; contract test or recorded-response test for the market adapter if live calls are flaky in CI.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/market_facts.py` | modify | Orchestrate `build_market_facts(reference_time)` |
| `backend/app/services/market_facts_adapters.py` | create | NSE/index + events merge, normalization |
| `backend/app/sources/nse_announcements.py` | modify | Harden / narrow window for monitor use (if needed) |
| `backend/app/services/signal_monitor_runner.py` | modify | Default `facts_provider` uses merged builder |
| `backend/tests/test_market_facts_merge.py` | create | Merge + evaluate integration |
| `backend/tests/test_nse_facts_adapter_contract.py` | create | Optional recorded-response / schema test |

#### Tasks (checkboxes)

- [x] **14.0** Signal monitor: richer market + macro fact sources
  - [x] **14.1** Design fact-merge contract (`MarketFact`, ordering, cap on list size, dedup rules).
  - [x] **14.2** Implement market adapter(s): NSE announcements and/or index snapshot lines with `observed_at` in IST/UTC consistently.
  - [x] **14.3** Merge with `fetch_recent_event_facts`; wire as default in `run_signal_monitor` (keep `facts_provider` override for tests).
  - [x] **14.4** Env toggles + structured logging when a stream is empty or errors.
  - [x] **14.5** Tests: merge unit tests + dual-stream `evaluate` fixture test.
  - [x] **14.6** Document operational playbook (rate limits, market holidays vs cron) in PR comment or short `docs/` note if needed.

---

### Story P2-S15 — Phase 1.5 performance debt closure + cross-phase standards (ad-hoc, end of Phase 2)

- **Status:** **Partially closed** (harness + standards + CI extension shipped). **Remediation** → **`docs/plans/finnwise-phase2.5-implementation-tasks.md`** (Phase 2.5, pre–Phase 3).
- **Assigned:** Riley
- **Points:** 3
- **Layers:** Ops, Docs, CI, API (validation)
- **Depends on:** P2-S1 (Mirror), P2-S6/S8 (Lens), P2-S11 (Map), P1.5-S9/S9b (harness), P1.5-S10 (sign-off evidence)
- **Parallel with:** _None — run last in Phase 2 (Months 8–9)_

**User story**

> As the Product Owner, I want the Phase 1.5 performance benchmarks that were accepted as deferrals at phase close to be met on production, and a written standard so every Phase 2 (and later Phase 3) page inherits SSR, bundle, Lighthouse, and API bench practices — so we do not regress as surface area grows.

**Context (from P1.5-S10 PO sign-off, 23-05-2026)**

- Proxy warm API p95 was ~**1.75 s** vs target **&lt;800 ms** (improved from ~8 s baseline).
- Mobile LCP ~**2.6 s** vs **2.5 s** “meaningful content” target — optional polish if cheap.

**Acceptance criteria**

- [x] `docs/plans/cross-phase-performance-standards.md` checked in — checklist derived from Phase 1.5 (SSR, caching, pool, fonts, measurement, CI budgets); **required reading** for Phase 3 stories that add routes.
- [ ] `scripts/bench_api_latency.mjs` post-deploy: **feed + card detail warm p95 &lt;800 ms** — **moved to Phase 2.5** (P2.5-S2); baseline recorded 24 May 2026 (see Phase 2.5 plan).
- [x] `scripts/lighthouse.mjs` extended to audit **Mirror, Lens, Map** (in addition to Pulse + Thread); mobile + desktop profiles; CI job fails on budget miss (same thresholds as P1.5-S9/S9b). `map-sector` pending Map deploy → P2.5-S1.
- [ ] Each new Phase 2 route audited: RSC initial load, dynamic imports for heavy panels, no full-app font pull on light pages — **moved to Phase 2.5** (P2.5-S5).
- [ ] Post-remediation JSON saved under `Page Load Performance/` for all six surfaces — **partial** (5/6 mobile, May 2026); **moved to Phase 2.5** (P2.5-S6).
- [ ] Phase 2 close note in `docs/Post Implementation documentation/` — **moved to Phase 2.5** (P2.5-S6).

**Tech notes**

- Reuse existing harness — do not fork Lighthouse logic. Add URL list / env vars e.g. `LIGHTHOUSE_MIRROR=1`, `LIGHTHOUSE_MAP_SLUG=...`.
- Bench requires `BENCH_API_DIRECT_URL` set to Render production origin (not loopback `.env.local`).
- If p95 cannot reach 800 ms after one focused tuning pass, document root cause (query ms vs proxy) and PO re-acceptance — do not silently waive.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `docs/plans/cross-phase-performance-standards.md` | create | Cross-phase perf checklist (Phase 2 + 3) |
| `scripts/lighthouse.mjs` | modify | Add Mirror, Lens, Map URLs |
| `scripts/lighthouse-budget.mjs` | modify | Surface list / helpers if needed |
| `scripts/bench_api_latency.mjs` | reference | Post-deploy p50/p95 evidence |
| `.github/workflows/ci.yml` | modify | Lighthouse job includes new surfaces |
| `scripts/README.md` | modify | Document new URLs + Phase 2 close bench |
| `frontend/app/(app)/mirror/page.tsx` | review | SSR / initialData pattern |
| `frontend/app/(app)/lens/**` | review | Stream + result; avoid dev-only perf assumptions |
| `frontend/app/(app)/map/**` | review | RSC + matrix lazy load |
| `Page Load Performance/*.json` | reference | Archive |

#### Tasks (checkboxes)

- [x] **15.0** Phase 1.5 performance debt closure + cross-phase standards _(harness complete; remediation in **Phase 2.5**)_
  - [x] **15.1** Author `docs/plans/cross-phase-performance-standards.md` (Phase 1.5 learnings → mandatory PR checklist).
  - [ ] **15.2** Run `bench_api_latency.mjs` on production; tune until **p95 &lt;800 ms** OR PO waiver — → **P2.5-S2** ([x] baseline bench run 24 May 2026).
  - [x] **15.3** Extend `lighthouse.mjs` + CI for Mirror, Lens, Map (mobile + desktop).
  - [ ] **15.4** Perf audit each Phase 2 route — → **P2.5-S5**.
  - [ ] **15.5** Capture and archive Lighthouse JSON for six surfaces — → **P2.5-S6** ([x] partial mobile archive May 2026).
  - [ ] **15.6** Performance close-out note — → **P2.5-S6** (`finnwise-phase2.5-implementation-tasks.md`).

---

## Risks

- **Mirror grading mis-reads cards** — Mitigated by P2-S2 grading using Original View only + per-level rubric in `grading.v1.md` + explicit forbid-generic-gaps. Add a spot-check ritual to `docs/plans/phase2-go-no-go.md`.
- **Personalisation drift into stored financial data** (PRD §11.1) — P2-S9 enforces session-only storage with a unit test asserting the backend never sees per-stock holdings. Re-review in legal pass (Phase 3).
- **Email channel becomes a recommendation channel** — P2-S10 template lint asserts no buy/sell/hold copy; PR review checklist for any future email work.
- **LLM cost from Lens spikes** (PRD §12 risk 7) — P2-S13 enforces per-user rate limit + monthly ceiling.
- **Factor DB expansion quality** — P2-S11 keeps MMJ + source invariant from Phase 1; coverage test prevents partial seeds shipping.
- **Signal gate over-fit to headlines** — P2-S14 adds market-leaning fact streams so P1-S11 gates are not driven only by `events` titles; monitor failures fall back to partial coverage with logged skips.
- **Reasoning-gap heuristics produce trivial gaps** — P2-S4 tests must include negative fixtures (insufficient history → suppress panel).
- **Performance regression on new surfaces** — Mitigated by § Performance standards + **P2-S15** (extend Lighthouse CI, close API p95 debt, cross-phase checklist for Phase 3).

## Recommendations

- Run P2-S11 (Factor DB expansion) on the critical path from Week 1 — Riley owns it solo and it gates P2-S4 (gaps link to Map modules).
- Land Mirror stack (S1 + S2 + S3 + S4 + S5) by end of Month 5; gives 4 weeks of self-grading before Lens lands.
- The Lens stack (S6 + S7 + S8) is one developer pair-week per story; tackle in sequence to keep stream contract clean.
- P2-S12 (polish) is a continuous trickle — schedule one half-day per week, not a single sprint.
- **P2-S14** (signal fact pipeline) should land before you rely on auto-gated signal actions at scale; keep event-only corroboration in Phase 1 until then.
- **P2-S15** delivered harness + standards; **Phase 2.5** (`finnwise-phase2.5-implementation-tasks.md`) is the **mandatory pre–Phase 3 gate** for green Lighthouse CI, API p95, and Map production deploy.

---

## How to execute Phase 2

Suggested order (Months 4–9, 24 weeks):

1. **Month 4:** Sam P2-S1 + P2-S5 (Mirror UI). Jordan P2-S2 (grading service). Riley P2-S11 starts (Factor DB sectors 1–3) + P2-S3 (notifications).
2. **Month 5:** Sam P2-S6 + P2-S8 (Lens UI). Jordan P2-S7 (Lens stream). Riley P2-S4 (gaps) + continues P2-S11 (sectors 4–6).
3. **Month 6:** Jordan P2-S9 (personalisation) + **starts P2-S14** (signal fact pipeline). Riley P2-S10 (email) + P2-S11 (sectors 7–8). Sam P2-S12 (polish trickle).
4. **Month 7:** Jordan P2-S13 (rate-limit + observability); **finish P2-S14** if not done. Riley finishes P2-S11 + Map modules linked to gaps. Sam polish + Phase 2 tester onboarding.
5. **Month 8–9:** Soak test, Phase 2 tester cohort, feedback iteration; **Riley P2-S15** (harness + CI — done); **Phase 2.5** (API p95, Lighthouse green, Map deploy); then prepare Phase 3 go/no-go.

Parallel-safe pairs: `{S1, S2, S6, S11}` in Month 4; `{S3, S4, S5, S7, S8}` in Month 5; `{S9, S10, S13, S14}` in Month 6–7. **P2-S15 is sequential last** (depends on S1, S6, S11).

---

## Appendix — Taskmaster-style export (per developer)

### Notes

- Same test placement and commands as Phase 1.
- Reuse `.env.local`; add only new keys (`EMAIL_API_KEY`, `EMAIL_FROM`, `EMAIL_PROVIDER`).
- All Phase 1 invariants (SEBI footer, MMJ tags, append-only `track_record`, no buy/sell/hold) continue to apply.
- **Phase 1.5 performance:** follow § Performance standards on every story; harness in **P2-S15**; close deferred benchmarks in **Phase 2.5** (`finnwise-phase2.5-implementation-tasks.md`, `scripts/README.md`).

### Relevant Files (rollup)

- `frontend/app/(app)/mirror/**` — Mirror surface (S1, S3, S4, S5)
- `frontend/app/(app)/lens/**` — Lens surface (S6, S7, S8)
- `frontend/app/(app)/map/**` — Map content (S11)
- `frontend/app/(app)/settings/email/**` — Email prefs (S10)
- `frontend/components/Holdings/**` — Holdings modal (S9)
- `frontend/lib/lens/**` — Lens state + stream hooks
- `frontend/lib/personalisation/**` — Session-only holdings store
- `backend/app/api/**` — mirror, mirror_notifications, mirror_gaps, mirror_streak, lens, lens_stream, saved_threads, map, unsubscribe, admin_metrics
- `backend/app/services/**` — mirror_stats, prediction_grader, reasoning_gap_detector, notify_on_grade, lens_pipeline, feed_ranker, email_client, **market_facts / market_facts_adapters (P2-S14)**, cost_guard (modified)
- `backend/app/jobs/**` — grade_on_resolve, email_on_signal, **signal_monitor (consumer of merged facts, P2-S14)**
- `backend/app/middleware/rate_limit.py`
- `backend/prompts/grading.v1.md`
- `backend/email-templates/signal_fired.html`
- `backend/db/migrations/**` — 0010 through 0015
- `backend/db/seeds/sectors/*.sql`
- `notes/phase1-feedback-backlog.md`

### Tasks by developer — Jordan

- [x] **2.0** Mirror — three-level accuracy grading service
  - [x] **2.1** Accuracy column migration
  - [x] **2.2** `grading.v1.md`
  - [x] **2.3** `prediction_grader.grade()`
  - [x] **2.4** `grade_on_resolve` job
  - [x] **2.5** Persist + append `track_record`
  - [x] **2.6** Idempotency
  - [x] **2.7** Grader + Original-View tests
- [x] **7.0** Lens — live six-step pipeline stream
  - [x] **7.1** `lens_pipeline.run()` milestones
  - [x] **7.2** SSE endpoint
  - [x] **7.3** `LoadingCard`
  - [x] **7.4** `PipelineStep` states
  - [x] **7.5** `useLensStream` hook
  - [x] **7.6** Progress bar
  - [x] **7.7** Mandatory disclaimer
  - [x] **7.8** Six-event ordering test
- [x] **9.0** Portfolio Protector personalisation (session-only)
  - [x] **9.1** `HoldingsModal`
  - [x] **9.2** `sessionHoldings` store
  - [x] **9.3** `personalisation_token` derivation
  - [x] **9.4** Feed re-rank
  - [x] **9.5** `HoldingCallout` in Thread
  - [x] **9.6** "Not stored on our servers" copy
  - [x] **9.7** Session-only + re-rank tests
- [x] **13.0** Rate-limit guard + LLM cost ceiling + observability
  - [x] **13.1** Per-user rate-limit middleware
  - [x] **13.2** Monthly cost projection
  - [x] **13.3** Structured JSON logging
  - [x] **13.4** `/api/admin/metrics`
  - [x] **13.5** 429 + ceiling tests
- [ ] **14.0** Signal monitor: richer market + macro fact sources
  - [ ] **14.1** Fact-merge contract + caps
  - [ ] **14.2** NSE/index (or agreed) adapter
  - [ ] **14.3** Merge with `events`; default in `run_signal_monitor`
  - [ ] **14.4** Env toggles + logging on stream failure
  - [ ] **14.5** Merge + dual-stream evaluate tests
  - [ ] **14.6** Ops notes (holidays, rate limits)

### Tasks by developer — Sam

- [x] **1.0** Mirror — prediction history list + stats strip
  - [x] **1.1** `/api/mirror/predictions`
  - [x] **1.2** `/api/mirror/stats`
  - [x] **1.3** `mirror_stats.compute()`
  - [x] **1.4** `StatsStrip`
  - [x] **1.5** `FilterPills` URL sync
  - [x] **1.6** `PredictionCard`
  - [x] **1.7** `AccuracyMeter`
  - [x] **1.8** `GapInsightExpanded` slot
  - [x] **1.9** Empty / loading / error
  - [x] **1.10** No-`₹` + bars + filter-sync tests
- [x] **5.0** Mirror — streak tracker grid + summary
  - [x] **5.1** `/api/mirror/streak`
  - [x] **5.2** `StreakTracker` grid
  - [x] **5.3** `StreakSummary` paragraph
  - [x] **5.4** Legend row
  - [x] **5.5** Ordering + transparent + summary tests
- [ ] **6.0** Lens — query input + history + examples
  - [ ] **6.1** `lens_queries` migration
  - [ ] **6.2** `POST /api/lens/queries`
  - [ ] **6.3** `GET /api/lens/queries/me`
  - [ ] **6.4** `useLensState` reducer
  - [ ] **6.5** `QueryInput`
  - [ ] **6.6** Time-estimate note
  - [ ] **6.7** `ExampleGrid`
  - [ ] **6.8** `QueryHistory`
  - [ ] **6.9** `PhaseBadge`
  - [ ] **6.10** State + gating + tap-fill tests
- [x] **8.0** Lens — result rendering + Save to Thread
  - [x] **8.1** `ResultCard` reuses Phase 1 ICE components
  - [x] **8.2** `LensLimitations` mandatory aside
  - [x] **8.3** Lens-specific Confidence Composition note
  - [x] **8.4** Bias Flags aside
  - [x] **8.5** Meta row
  - [x] **8.6** `saved_threads` migration + API
  - [x] **8.7** `SaveToThreadButton`
  - [x] **8.8** Saved sub-nav in sidebar
  - [x] **8.9** "← New query" preserves text
  - [x] **8.10** Limitations + save + preserve tests
- [x] **12.0** Phase 1 UI polish + tester-feedback iteration
  - [x] **12.1** Triage `notes/phase1-feedback-backlog.md`
  - [x] **12.2** Close all P0
  - [x] **12.3** `axe` a11y tests
  - [x] **12.4** Lighthouse CI ≥90
  - [x] **12.5** Copy clarity pass
  - [x] **12.6** A11y + Lighthouse green in CI

### Tasks by developer — Riley

- [x] **3.0** Resolved-card notification system + topbar badge
  - [x] **3.1** `card_graded` enum value
  - [x] **3.2** `notify_on_grade` fan-out
  - [x] **3.3** `/api/mirror/notifications/unread`
  - [x] **3.4** `ResolvedBadge` pulsing
  - [x] **3.5** `ReadyToGradePanel`
  - [x] **3.6** Read-on-viewport-intersect
  - [x] **3.7** Scope + visibility + pulse tests
- [x] **4.0** Reasoning-gap analysis + Map module linking
  - [x] **4.1** Gap taxonomy
  - [x] **4.2** `reasoning_gap_detector.analyse()`
  - [x] **4.3** `/api/mirror/gaps`
  - [x] **4.4** `ReasoningGapPanel`
  - [x] **4.5** Wire `gap_insight` into expanded PredictionCard
  - [x] **4.6** Recompute on resolve
  - [x] **4.7** Fixture-history + UI tests
- [ ] **10.0** Email notifications for fired signals
  - [ ] **10.1** Provider creds in `.env.local`
  - [ ] **10.2** `user_email_preferences` + tokens
  - [ ] **10.3** `email_client.send()` abstraction
  - [ ] **10.4** Signal-fired template
  - [ ] **10.5** `email_on_signal.fan_out()`
  - [ ] **10.6** `/unsubscribe` endpoint
  - [ ] **10.7** Email settings page
  - [ ] **10.8** Scope + single-shot + language-lint tests
- [x] **11.0** Factor DB expansion to all 8 sectors + The Map content
  - [x] **11.1** Seeds: IT / Energy / Consumer / Auto / Pharma / Metals / Telecom / Infra
  - [x] **11.2** `map_modules` migration + content
  - [x] **11.3** Map API endpoints
  - [x] **11.4** Map index page
  - [x] **11.5** Map sector-detail page
  - [x] **11.6** Cross-link gaps → modules
  - [x] **11.7** Coverage + linked-modules tests
- [ ] **15.0** Phase 1.5 performance debt closure + cross-phase standards
  - [ ] **15.1** `cross-phase-performance-standards.md`
  - [ ] **15.2** Production bench p95 &lt;800 ms
  - [ ] **15.3** Lighthouse CI — Mirror, Lens, Map
  - [ ] **15.4** Route perf audit (SSR, splits, fonts)
  - [ ] **15.5** Archive Lighthouse JSON (6 surfaces)
  - [ ] **15.6** Phase 2 performance close-out note

---

## Optional user stories (backlog — not in core Phase 2 scope)

_These are explicitly deferred from Phase 1 or deprioritised; pick up when roadmap allows._

### Optional — In-app alerts: read/unread, dismissal, recency window (Phase 1 surfaces)

- **Context:** Phase 1 (P1-S11) writes `signal_fired` (and other kinds) into `in_app_notifications` and shows a pulsing topbar badge when any matching row exists in the fetched list. There is **no** read state, user dismissal, or “only show if newer than X days” rule.
- **Rough scope when prioritised:**
  - Add `read_at` / `dismissed_at` (or equivalent) on notification rows.
  - `PATCH /api/notifications/:id/read` (or batch read).
  - Badge reflects **unread** `signal_fired` only; optional TTL (e.g. hide pulse for alerts older than 7 days).
  - Optional: notification panel / dropdown in the shell (not only deep link from badge).
- **Depends on:** Phase 1 auth + existing `GET /api/notifications`.
