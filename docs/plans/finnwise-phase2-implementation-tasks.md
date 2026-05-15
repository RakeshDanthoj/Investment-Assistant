# FinnWise — Phase 2 Implementation Tasks (Engagement Layer, Months 4–9)

_Source PRD_: `FinnWise_PRD_v3_Final.md` — Section 10 / Phase 2, with binding decisions in §5 (Screens 4 & 5), §6, §7, §11, §12.
_generated for independent execution without prd-planner_

## Overview

- **Summary**: Phase 2 introduces the engagement layer on top of the Phase 1 foundation: **The Mirror** (prediction history, three-level accuracy, reasoning-gap analysis, streak tracker), **The Lens** (on-demand ICE card generation with visible six-step pipeline), Portfolio Protector personalisation against session-only holdings, email notifications when signals fire, expansion of the Factor Exposure DB to all eight sectors plus The Map content, and a UI polish pass driven by Phase 1 tester feedback.
- **Tech stack**: same as Phase 1 (Next.js + Tailwind, FastAPI, Supabase, Anthropic Sonnet, Vercel, Render). New additions: a lightweight email provider (Resend or Postmark free tier) and Server-Sent Events for the Lens pipeline progress stream. Tests: Jest + RTL (frontend), Pytest (backend). Single `.env.local`.
- **Slicing approach**: every story is an end-to-end vertical slice (UI + API + DB minimum) with explicit test step(s). Parent task IDs are **per-phase** — this file uses `1.0`–`13.0`. All PRD §6 / §8.6 / §11 constraints from Phase 1 continue to apply unchanged.
- **Prerequisite**: Phase 1 is fully shipped and stable (Onboarding, Pulse, Thread, LLM pipeline, signal monitor, track record, bias audit) and at least one tester cohort has completed three sessions.

## Team plan

| Developer | Focus | Total points |
|-----------|-------|---------------|
| Jordan | Mirror grading service, Lens loading stream, Portfolio Protector backend, cost & rate-limit hardening | 20 |
| Sam | Mirror UI (prediction list, streak), Lens UI (query / loading / result states), Phase 1 polish iteration | 24 |
| Riley | Reasoning-gap analysis, resolved-card notification system, email channel, Factor DB expansion to 8 sectors + Map content | 20 |

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

- [ ] Route `/(app)/mirror` reachable from sidebar; protected behind auth.
- [ ] Topbar: "The Mirror" + subtitle + notification badge slot (filled by P2-S3).
- [ ] Stats strip: four cells per PRD §5 Screen 4 — Playfair 28px number + DM Mono 10px label + Inter 11px subtext. Accuracy numbers coloured green (≥70%) or amber (<70%).
- [ ] Filter pills above list: All / Resolved / Active / Pending.
- [ ] Prediction Card per PRD §5: event tag + headline + "Your call: ..." + status badge + three-level accuracy meter; expandable inline (no navigation) to reveal Gap Insight + Map module link.
- [ ] **Zero rupee figures anywhere on this surface** (PRD §5 Screen 4 design decision) — lint test asserts no `₹` substrings in the page subtree.

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

- [ ] **1.0** The Mirror — prediction history list + stats strip
  - [ ] **1.1** `GET /api/mirror/predictions` — filter by status, paginated, includes joined card metadata.
  - [ ] **1.2** `GET /api/mirror/stats` — total / mechanism % / market % / gaps count.
  - [ ] **1.3** `mirror_stats.compute(user_id)` pure function with tested thresholds.
  - [ ] **1.4** Page shell + `StatsStrip` reading the stats endpoint.
  - [ ] **1.5** `FilterPills` syncing to URL params.
  - [ ] **1.6** `PredictionCard` with status badge + three accuracy meter slots.
  - [ ] **1.7** `AccuracyMeter` — three labelled bars (Mechanism / Business Impact / Market Reaction) with correct / partial / incorrect / monitoring states.
  - [ ] **1.8** `GapInsightExpanded` slot — populated by P2-S4.
  - [ ] **1.9** Empty state + loading skeleton + error retry.
  - [ ] **1.10** Test: stats threshold colouring; no-rupee assertion; three independent bars; filter URL sync.

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

- [ ] Job runs on every card transition to `resolved`; idempotent per (user, card).
- [ ] Three accuracy fields per `user_predictions` row populated: `mechanism_accuracy`, `business_accuracy`, `market_accuracy` each in `{correct, partial, incorrect, monitoring}`.
- [ ] Grading inputs are exclusively the immutable Original View (`track_record` Day 1 row) and the final card state — never an interim revision.
- [ ] Gap Insight text written to `user_predictions.gap_insight` (consumed by P2-S4).
- [ ] Reasoning encoded — never a generic "markets are unpredictable" (PRD §5 Screen 4 design decision).

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

- [ ] **2.0** The Mirror — three-level accuracy grading service
  - [ ] **2.1** Migration: add `mechanism_accuracy`, `business_accuracy`, `market_accuracy`, `gap_insight` to `user_predictions`.
  - [ ] **2.2** Author `grading.v1.md` with explicit rubric per level + forbid generic gap explanations.
  - [ ] **2.3** `prediction_grader.grade(prediction, original_card, final_card)` — three-level output + gap insight.
  - [ ] **2.4** `grade_on_resolve` job hooks card state transition to `resolved`.
  - [ ] **2.5** Persist three accuracy columns + gap insight + append a row to `track_record` summarising the grade.
  - [ ] **2.6** Idempotency: re-running job on already-graded predictions is a no-op.
  - [ ] **2.7** Test: fixture-card grading; assert Original View is the source; idempotency test.

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

- [ ] Badge visible only when ≥1 of the user's predictions has just transitioned to a graded state and the user has not yet viewed it.
- [ ] Tapping the badge scrolls/expands the relevant card in the prediction history (P2-S1 list).
- [ ] Dismissal happens only on view, not on tap-away.
- [ ] Notifications table reused from Phase 1 (P1-S11) with a new `kind='card_graded'` value.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/0011_notifications_kind_enum.sql` | create | Add `card_graded` enum value |
| `backend/app/services/notify_on_grade.py` | create | Fan-out on resolve |
| `backend/app/api/mirror_notifications.py` | create | `GET /api/mirror/notifications/unread` |
| `frontend/app/(app)/mirror/_components/ResolvedBadge.tsx` | create | Pulsing badge |
| `frontend/app/(app)/mirror/_components/ReadyToGradePanel.tsx` | create | Right-panel item list |
| `frontend/app/(app)/mirror/_components/ResolvedBadge.test.tsx` | create | RTL test |
| `backend/tests/test_notify_on_grade.py` | create | Fan-out only to users with logged predictions |

#### Tasks (checkboxes)

- [ ] **3.0** Resolved-card notification system + topbar badge
  - [ ] **3.1** Add `card_graded` to notification kind enum.
  - [ ] **3.2** `notify_on_grade.fan_out(card_id)` — one notification per user with a graded prediction.
  - [ ] **3.3** `GET /api/mirror/notifications/unread` returns count + list.
  - [ ] **3.4** `ResolvedBadge` with pulsing dot animation (reuses §8.6 keyframe).
  - [ ] **3.5** `ReadyToGradePanel` right-panel — green-tinted items, each clickable to scroll/expand the card.
  - [ ] **3.6** Mark notification read on viewport-intersection with the corresponding card (not on tap-elsewhere).
  - [ ] **3.7** Test: fan-out scope; badge hidden when zero unread; RTL pulsing-class assertion.

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

- [ ] `reasoning_gap_detector.analyse(user_id)` returns top-3 gaps with `gap_name`, `pattern_explanation`, `linked_map_module_id`.
- [ ] Gaps derived from actual patterns (e.g. consistently correct on mechanism but wrong on market reaction) — not manually assigned.
- [ ] Gap items rendered in the right-panel "Reasoning Gap Analysis" with icon + name (Inter 13px bold) + explanation + `🗺 The Map: [module name] →`.
- [ ] Map links resolve to real modules created in P2-S11.
- [ ] Recomputes on every new resolved prediction (or on demand via "Refresh analysis").

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/services/reasoning_gap_detector.py` | create | Pattern-mining over user_predictions |
| `backend/app/api/mirror_gaps.py` | create | `GET /api/mirror/gaps` |
| `frontend/app/(app)/mirror/_components/ReasoningGapPanel.tsx` | create | Right-panel block |
| `backend/tests/test_reasoning_gap_detector.py` | create | Fixture histories → expected gaps |
| `frontend/app/(app)/mirror/_components/ReasoningGapPanel.test.tsx` | create | RTL render + link |

#### Tasks (checkboxes)

- [ ] **4.0** Reasoning-gap analysis + Map module linking
  - [ ] **4.1** Define gap taxonomy (e.g. "Direction-correct, magnitude-wrong", "Anchored on narrative", "Sector concentration in your predictions") with linked Map module IDs.
  - [ ] **4.2** `reasoning_gap_detector.analyse(user_id)` — heuristic + LLM-light pattern detection.
  - [ ] **4.3** `GET /api/mirror/gaps` returns top-3.
  - [ ] **4.4** `ReasoningGapPanel` UI — three items, each linking to `/map/[moduleId]`.
  - [ ] **4.5** Gap insight inside the expanded PredictionCard (P2-S1 slot) reads `user_predictions.gap_insight` directly.
  - [ ] **4.6** Recompute trigger on grade-on-resolve job tail.
  - [ ] **4.7** Test: fixture histories yield expected gap names; UI renders the three items.

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

- [ ] Grid renders 14 cells, each colour-coded green / amber / red / grey / transparent per PRD §5 Screen 4 spec.
- [ ] DM Mono letters inside cells: `M / P / ✗ / · / –`.
- [ ] Summary paragraph below grid compares mechanism % to market % and explains why a gap is normal.
- [ ] Sorted most recent first; missing slots render transparent.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/mirror/_components/StreakTracker.tsx` | create | 14-cell grid |
| `frontend/app/(app)/mirror/_components/StreakSummary.tsx` | create | Plain-English block |
| `backend/app/api/mirror_streak.py` | create | `GET /api/mirror/streak` |
| `backend/tests/test_mirror_streak.py` | create | Cell ordering + transparent slots |
| `frontend/app/(app)/mirror/_components/StreakTracker.test.tsx` | create | RTL test |

#### Tasks (checkboxes)

- [ ] **5.0** Streak tracker grid + summary
  - [ ] **5.1** `GET /api/mirror/streak` returns last 14 grading events (some may be `monitoring` / transparent).
  - [ ] **5.2** `StreakTracker` renders 14 cells, exact colour map from PRD §8.3.
  - [ ] **5.3** `StreakSummary` compares mechanism % vs market % and templates the explanation paragraph.
  - [ ] **5.4** Legend row below the grid.
  - [ ] **5.5** Test: ordering most-recent first; transparent rendering for missing slots; summary numerics.

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

- [ ] Route `/(app)/lens` reachable from sidebar; sidebar shows the Phase 2 purple badge in topbar.
- [ ] Query text area min 80px, placeholder exactly as PRD §5 Screen 5.
- [ ] Sector + Horizon optional dropdowns in the query-box footer.
- [ ] "Generate card →" disabled until input >10 chars.
- [ ] DM Mono time-estimate note: "Cards take 30–90 seconds to generate."
- [ ] 2×3 example query grid with coloured category tags; clicking fills the textarea.
- [ ] Recent query history list with relative dates; clicking navigates to result state for that query.
- [ ] No page navigation between input / loading / result states.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/lens/page.tsx` | create | Lens shell w/ state machine |
| `frontend/app/(app)/lens/_components/QueryInput.tsx` | create | Textarea + dropdowns + CTA |
| `frontend/app/(app)/lens/_components/ExampleGrid.tsx` | create | 2×3 examples |
| `frontend/app/(app)/lens/_components/QueryHistory.tsx` | create | Recent queries |
| `frontend/app/(app)/lens/_components/PhaseBadge.tsx` | create | Purple Phase 2 pill |
| `frontend/lib/lens/useLensState.ts` | create | Query/Loading/Result state machine |
| `backend/db/migrations/0012_lens_queries.sql` | create | `lens_queries(id, user_id, query, sector, horizon, status, created_at)` |
| `backend/app/api/lens.py` | create | `POST /api/lens/queries` + `GET /api/lens/queries/me` |
| `frontend/lib/lens/useLensState.test.ts` | create | State-machine tests |
| `frontend/app/(app)/lens/_components/QueryInput.test.tsx` | create | CTA disabled <10 chars |

#### Tasks (checkboxes)

- [ ] **6.0** The Lens — query input + history + examples
  - [ ] **6.1** Migration: `lens_queries` table with `status` enum (`queued`, `running`, `done`, `failed`).
  - [ ] **6.2** `POST /api/lens/queries` creates a row, returns id, enqueues for generation.
  - [ ] **6.3** `GET /api/lens/queries/me` returns user's recent 20.
  - [ ] **6.4** `useLensState` reducer: `idle → submitting → loading → result | error`. URL hash for shareability.
  - [ ] **6.5** `QueryInput` with sector + horizon dropdowns; CTA disabled <10 chars.
  - [ ] **6.6** Time-estimate note below box (DM Mono 10px slate-400).
  - [ ] **6.7** `ExampleGrid` with six static examples covering Macro / RBI / Regulatory / India-specific / Geopolitical / Budget.
  - [ ] **6.8** `QueryHistory` list with relative dates.
  - [ ] **6.9** `PhaseBadge` purple pill in topbar.
  - [ ] **6.10** Test: state-machine transitions; CTA gating; example-tap fills textarea.

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

- [ ] Six steps named exactly per PRD §5 Screen 5: Factor DB queried / Macro signals retrieved / Synthesising ICE layers / Generating dissenting view / Articulating framework / Validating numbers against Evidence.
- [ ] Stream is Server-Sent Events at `GET /api/lens/queries/{id}/stream`.
- [ ] Each step transitions on real backend milestones — not faked time slices.
- [ ] Loading card centred, max 560px, with user query displayed in Playfair italic.
- [ ] Bottom disclaimer present verbatim: "Every number is validated against the Evidence layer before display."

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

- [ ] **7.0** The Lens — loading state with live six-step pipeline
  - [ ] **7.1** `lens_pipeline.run(query_id)` instruments `card_pipeline` with six `yield`ed milestones.
  - [ ] **7.2** `GET /api/lens/queries/{id}/stream` SSE endpoint that consumes the pipeline iterator.
  - [ ] **7.3** `LoadingCard` centred component with query echo in Playfair italic.
  - [ ] **7.4** `PipelineStep` with state classes: pending (grey) / active (blue pulsing) / done (green ✓).
  - [ ] **7.5** `useLensStream` hook connects EventSource, updates step state in reducer.
  - [ ] **7.6** Progress bar component (0→100%) interpolating between milestones.
  - [ ] **7.7** Disclaimer text rendered verbatim.
  - [ ] **7.8** Test: six events emitted in order; UI transitions pending→active→done correctly.

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

- [ ] Result reuses InsightLayer / ContextLayer / EvidenceLayer / DissentingView / InstrumentCard / FrameworkBehindThis from Phase 1 — no duplication.
- [ ] Aside includes Confidence Composition with Lens-specific note (higher Judged proportion) + applicable bias flags + **mandatory** Lens Limitations block with the exact PRD copy.
- [ ] "Save to Thread" copies the card to the user's personal Thread collection (a `saved_threads` join table) and surfaces it in sidebar.
- [ ] "← New query" returns to query state, preserving textarea content.
- [ ] Meta row shows generation time and date.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/lens/_components/ResultCard.tsx` | create | Wraps Phase 1 ICE components |
| `frontend/app/(app)/lens/_components/LensLimitations.tsx` | create | Mandatory aside block |
| `frontend/app/(app)/lens/_components/SaveToThreadButton.tsx` | create | Save action |
| `backend/db/migrations/0013_saved_threads.sql` | create | `saved_threads(user_id, card_id, saved_at)` |
| `backend/app/api/saved_threads.py` | create | `POST /api/saved-threads` + list |
| `frontend/app/(app)/lens/_components/LensLimitations.test.tsx` | create | Asserts block present + exact copy |
| `backend/tests/test_saved_threads.py` | create | Idempotent save per (user, card) |

#### Tasks (checkboxes)

- [ ] **8.0** The Lens — result rendering + Save to Thread
  - [ ] **8.1** `ResultCard` composes the existing Phase 1 ICE components against the new card payload.
  - [ ] **8.2** `LensLimitations` aside block — mandatory, exact PRD §5 Screen 5 copy.
  - [ ] **8.3** Confidence Composition aside with the Lens-specific explanatory note.
  - [ ] **8.4** Bias Flags aside reading the same `card_bias_flags` mechanism from Phase 1.
  - [ ] **8.5** Meta row: event type tag + horizon tag + "Generated in Xs · Date".
  - [ ] **8.6** Migration + API: `saved_threads` with unique `(user_id, card_id)`.
  - [ ] **8.7** `SaveToThreadButton` with toast confirmation.
  - [ ] **8.8** Sidebar surface for saved threads under a "Saved" sub-nav.
  - [ ] **8.9** "← New query" — restores textarea content from `useLensState`.
  - [ ] **8.10** Test: `LensLimitations` always rendered; save idempotent; "← New query" preserves text.

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

- [ ] Holdings collected via a lightweight modal launched from the user chip; persisted **only** in encrypted browser session storage (PRD §11.1 — no user financial data stored beyond session).
- [ ] Backend never sees the per-stock list — instead the client sends an opaque `personalisation_token` (hashed list of instrument IDs) per request.
- [ ] Pulse feed re-ranks based on the token; top of feed = cards whose instrument assessments intersect the user's holdings.
- [ ] Thread shows a per-holding "what this means for your XYZ" callout when intersection is non-empty.
- [ ] Modal includes a clear "this data is not stored on our servers" line.

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

- [ ] **9.0** Portfolio Protector personalisation (session-only holdings)
  - [ ] **9.1** `HoldingsModal` triggered from user chip; typeahead from instruments table.
  - [ ] **9.2** `sessionHoldings.save/get/clear` — backed by `sessionStorage`, cleared on tab close.
  - [ ] **9.3** Derive `personalisation_token` (hashed, salted instrument-id set) on client.
  - [ ] **9.4** `GET /api/feed` accepts optional token; `feed_ranker.rerank(cards, token)` reorders.
  - [ ] **9.5** `HoldingCallout` rendered on Thread when intersection non-empty.
  - [ ] **9.6** Explicit "not stored on our servers" copy in the modal.
  - [ ] **9.7** Test: token-based re-rank; session-only persistence; intersection callout visibility.

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

- [ ] Email provider integration (Resend or Postmark) with templates in `backend/email-templates/`.
- [ ] Trigger: `signal_state` transitions to `triggered` on a card with a logged prediction or saved-thread row for the user.
- [ ] One-click unsubscribe link present in every email (anti-spam compliance).
- [ ] `user_email_preferences` table; default opt-in for Phase 2 testers; opt-out preserved.
- [ ] Email never contains a recommendation — only "a signal you were watching has fired, view it in FinnWise".

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/0014_user_email_preferences.sql` | create | Prefs + unsubscribe tokens |
| `backend/app/services/email_client.py` | create | Provider abstraction |
| `backend/email-templates/signal_fired.html` | create | Plain HTML template |
| `backend/app/jobs/email_on_signal.py` | create | Trigger on signal transitions |
| `backend/app/api/unsubscribe.py` | create | `GET /unsubscribe?token=` |
| `frontend/app/(app)/settings/email/page.tsx` | create | Manage preferences |
| `backend/tests/test_email_on_signal.py` | create | Fan-out only to opted-in predicting users |
| `backend/tests/test_unsubscribe.py` | create | Token use is single-shot |

#### Tasks (checkboxes)

- [ ] **10.0** Email notifications for fired signals
  - [ ] **10.1** Provider credentials in `.env.local` (`EMAIL_PROVIDER`, `EMAIL_API_KEY`, `EMAIL_FROM`).
  - [ ] **10.2** Migration: `user_email_preferences` + `unsubscribe_tokens`.
  - [ ] **10.3** `email_client.send(template, vars, to)` provider-agnostic.
  - [ ] **10.4** Template: signal-fired (no buy/sell/hold copy; deep link to Thread).
  - [ ] **10.5** `email_on_signal.fan_out(card_id, signal_id)` — only opted-in users with stake (prediction or saved).
  - [ ] **10.6** `GET /unsubscribe?token=` flips prefs.
  - [ ] **10.7** Settings page to view/change prefs.
  - [ ] **10.8** Test: fan-out scope; unsubscribe single-shot; template lints clean of forbidden language.

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

- [ ] All 8 PRD §7.1 factors fully seeded across the 8 target sectors covering ≥120 of the top 150 NSE stocks.
- [ ] `/(app)/map` lists sectors with cover tiles; each sector page documents the sector's factor sensitivities + a "How this sector reacts to events" module.
- [ ] At least 1 Reasoning Gap → Map module link exists per gap type defined in P2-S4.
- [ ] Every sensitivity row keeps the MMJ + source-URL invariant from Phase 1.
- [ ] Sector pages render the Map module content that P2-S4 links to.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/seeds/sectors/*.sql` | create | One seed file per sector (8 files) |
| `backend/db/migrations/0015_map_modules.sql` | create | `map_modules(id, sector, title, body, linked_gap_types[])` |
| `backend/app/api/map.py` | create | `GET /api/map/sectors` + `GET /api/map/sectors/{slug}` |
| `frontend/app/(app)/map/page.tsx` | create | Sector index |
| `frontend/app/(app)/map/[slug]/page.tsx` | create | Sector detail + module list |
| `frontend/app/(app)/map/_components/SectorTile.tsx` | create | Cover tile |
| `frontend/app/(app)/map/_components/MapModule.tsx` | create | Module renderer |
| `backend/tests/test_factor_db_coverage.py` | create | ≥120 instruments × 8 factors, all MMJ-tagged |

#### Tasks (checkboxes)

- [ ] **11.0** Factor DB expansion to all 8 sectors + The Map content
  - [ ] **11.1** Author seed files: IT / Energy & Oil / Consumer (FMCG) / Auto / Pharma / Metals & Materials / Telecom / Infra & Capital Goods (banking already done in P1-S5).
  - [ ] **11.2** Migration + seed: `map_modules` for each sector with the "How this sector reacts" body.
  - [ ] **11.3** `GET /api/map/sectors` index + `GET /api/map/sectors/{slug}` detail.
  - [ ] **11.4** `/(app)/map` index page rendering `SectorTile`s.
  - [ ] **11.5** `/(app)/map/[slug]` rendering the sensitivity matrix subset + modules.
  - [ ] **11.6** Cross-link from P2-S4 reasoning gaps to the matching module IDs.
  - [ ] **11.7** Test: factor-DB coverage (≥120 instruments × 8 factors, all MMJ-tagged); Map module endpoint returns linked modules for known gap types.

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

- [ ] Backlog of tester findings captured in `notes/phase1-feedback-backlog.md` (gitignored), each item triaged P0/P1/P2.
- [ ] All P0 findings closed before any P2 story ships to testers.
- [ ] WCAG AA contrast verified on PRD §8.3 palette; automated check via `axe` in tests.
- [ ] Lighthouse score ≥90 on Pulse, Thread, Mirror, Lens.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `notes/phase1-feedback-backlog.md` | create | Triaged backlog (gitignored) |
| `frontend/tests/a11y/*.test.tsx` | create | `axe` automated checks per surface |
| `scripts/lighthouse.mjs` | create | Lighthouse CI harness |

#### Tasks (checkboxes)

- [ ] **12.0** Phase 1 UI polish + tester-feedback iteration
  - [ ] **12.1** Collect + triage Phase 1 tester feedback into `notes/phase1-feedback-backlog.md`.
  - [ ] **12.2** Close every P0 item.
  - [ ] **12.3** Add `axe` automated a11y check across Pulse, Thread, Mirror, Lens.
  - [ ] **12.4** Lighthouse CI configured for the four surfaces; budget ≥90.
  - [ ] **12.5** Copy clarity pass on Insight Panel + Instrument Card reasoning blocks.
  - [ ] **12.6** Test: a11y suite green; Lighthouse budget enforced in CI.

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

- [ ] Per-user rate limit: 10 Lens queries/day; 429 with `retry-after` past the limit.
- [ ] Monthly cost ceiling: pipeline aborts and surfaces a clear error when projected month cost > ₹X budget threshold (configurable).
- [ ] Structured logs (JSON) on every pipeline run with prompt_version + token counts + duration.
- [ ] Basic metrics endpoint (`/api/admin/metrics`) gated to admin allow-list.

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

- [ ] **13.0** Rate-limit guard + LLM cost ceiling + observability
  - [ ] **13.1** `rate_limit` middleware — per-user token bucket; 10 Lens queries/day.
  - [ ] **13.2** Extend `cost_guard` with monthly projection from rolling token spend.
  - [ ] **13.3** Structured JSON logger on every pipeline run.
  - [ ] **13.4** `/api/admin/metrics` — daily card count, p95 generation time, override rate, signal false-positive rate (PRD §13 metrics).
  - [ ] **13.5** Test: 429 path; monthly ceiling abort; metrics shape.

---

## Risks

- **Mirror grading mis-reads cards** — Mitigated by P2-S2 grading using Original View only + per-level rubric in `grading.v1.md` + explicit forbid-generic-gaps. Add a spot-check ritual to `docs/plans/phase2-go-no-go.md`.
- **Personalisation drift into stored financial data** (PRD §11.1) — P2-S9 enforces session-only storage with a unit test asserting the backend never sees per-stock holdings. Re-review in legal pass (Phase 3).
- **Email channel becomes a recommendation channel** — P2-S10 template lint asserts no buy/sell/hold copy; PR review checklist for any future email work.
- **LLM cost from Lens spikes** (PRD §12 risk 7) — P2-S13 enforces per-user rate limit + monthly ceiling.
- **Factor DB expansion quality** — P2-S11 keeps MMJ + source invariant from Phase 1; coverage test prevents partial seeds shipping.
- **Reasoning-gap heuristics produce trivial gaps** — P2-S4 tests must include negative fixtures (insufficient history → suppress panel).

## Recommendations

- Run P2-S11 (Factor DB expansion) on the critical path from Week 1 — Riley owns it solo and it gates P2-S4 (gaps link to Map modules).
- Land Mirror stack (S1 + S2 + S3 + S4 + S5) by end of Month 5; gives 4 weeks of self-grading before Lens lands.
- The Lens stack (S6 + S7 + S8) is one developer pair-week per story; tackle in sequence to keep stream contract clean.
- P2-S12 (polish) is a continuous trickle — schedule one half-day per week, not a single sprint.

---

## How to execute Phase 2

Suggested order (Months 4–9, 24 weeks):

1. **Month 4:** Sam P2-S1 + P2-S5 (Mirror UI). Jordan P2-S2 (grading service). Riley P2-S11 starts (Factor DB sectors 1–3) + P2-S3 (notifications).
2. **Month 5:** Sam P2-S6 + P2-S8 (Lens UI). Jordan P2-S7 (Lens stream). Riley P2-S4 (gaps) + continues P2-S11 (sectors 4–6).
3. **Month 6:** Jordan P2-S9 (personalisation). Riley P2-S10 (email) + P2-S11 (sectors 7–8). Sam P2-S12 (polish trickle).
4. **Month 7:** Jordan P2-S13 (rate-limit + observability). Riley finishes P2-S11 + Map modules linked to gaps. Sam polish + Phase 2 tester onboarding.
5. **Month 8–9:** Soak test, Phase 2 tester cohort, feedback iteration, prepare Phase 3 go/no-go.

Parallel-safe pairs: `{S1, S2, S6, S11}` in Month 4; `{S3, S4, S5, S7, S8}` in Month 5; `{S9, S10, S13}` in Month 6.

---

## Appendix — Taskmaster-style export (per developer)

### Notes

- Same test placement and commands as Phase 1.
- Reuse `.env.local`; add only new keys (`EMAIL_API_KEY`, `EMAIL_FROM`, `EMAIL_PROVIDER`).
- All Phase 1 invariants (SEBI footer, MMJ tags, append-only `track_record`, no buy/sell/hold) continue to apply.

### Relevant Files (rollup)

- `frontend/app/(app)/mirror/**` — Mirror surface (S1, S3, S4, S5)
- `frontend/app/(app)/lens/**` — Lens surface (S6, S7, S8)
- `frontend/app/(app)/map/**` — Map content (S11)
- `frontend/app/(app)/settings/email/**` — Email prefs (S10)
- `frontend/components/Holdings/**` — Holdings modal (S9)
- `frontend/lib/lens/**` — Lens state + stream hooks
- `frontend/lib/personalisation/**` — Session-only holdings store
- `backend/app/api/**` — mirror, mirror_notifications, mirror_gaps, mirror_streak, lens, lens_stream, saved_threads, map, unsubscribe, admin_metrics
- `backend/app/services/**` — mirror_stats, prediction_grader, reasoning_gap_detector, notify_on_grade, lens_pipeline, feed_ranker, email_client, cost_guard (modified)
- `backend/app/jobs/**` — grade_on_resolve, email_on_signal
- `backend/app/middleware/rate_limit.py`
- `backend/prompts/grading.v1.md`
- `backend/email-templates/signal_fired.html`
- `backend/db/migrations/**` — 0010 through 0015
- `backend/db/seeds/sectors/*.sql`
- `notes/phase1-feedback-backlog.md`

### Tasks by developer — Jordan

- [ ] **2.0** Mirror — three-level accuracy grading service
  - [ ] **2.1** Accuracy column migration
  - [ ] **2.2** `grading.v1.md`
  - [ ] **2.3** `prediction_grader.grade()`
  - [ ] **2.4** `grade_on_resolve` job
  - [ ] **2.5** Persist + append `track_record`
  - [ ] **2.6** Idempotency
  - [ ] **2.7** Grader + Original-View tests
- [ ] **7.0** Lens — live six-step pipeline stream
  - [ ] **7.1** `lens_pipeline.run()` milestones
  - [ ] **7.2** SSE endpoint
  - [ ] **7.3** `LoadingCard`
  - [ ] **7.4** `PipelineStep` states
  - [ ] **7.5** `useLensStream` hook
  - [ ] **7.6** Progress bar
  - [ ] **7.7** Mandatory disclaimer
  - [ ] **7.8** Six-event ordering test
- [ ] **9.0** Portfolio Protector personalisation (session-only)
  - [ ] **9.1** `HoldingsModal`
  - [ ] **9.2** `sessionHoldings` store
  - [ ] **9.3** `personalisation_token` derivation
  - [ ] **9.4** Feed re-rank
  - [ ] **9.5** `HoldingCallout` in Thread
  - [ ] **9.6** "Not stored on our servers" copy
  - [ ] **9.7** Session-only + re-rank tests
- [ ] **13.0** Rate-limit guard + LLM cost ceiling + observability
  - [ ] **13.1** Per-user rate-limit middleware
  - [ ] **13.2** Monthly cost projection
  - [ ] **13.3** Structured JSON logging
  - [ ] **13.4** `/api/admin/metrics`
  - [ ] **13.5** 429 + ceiling tests

### Tasks by developer — Sam

- [ ] **1.0** Mirror — prediction history list + stats strip
  - [ ] **1.1** `/api/mirror/predictions`
  - [ ] **1.2** `/api/mirror/stats`
  - [ ] **1.3** `mirror_stats.compute()`
  - [ ] **1.4** `StatsStrip`
  - [ ] **1.5** `FilterPills` URL sync
  - [ ] **1.6** `PredictionCard`
  - [ ] **1.7** `AccuracyMeter`
  - [ ] **1.8** `GapInsightExpanded` slot
  - [ ] **1.9** Empty / loading / error
  - [ ] **1.10** No-`₹` + bars + filter-sync tests
- [ ] **5.0** Mirror — streak tracker grid + summary
  - [ ] **5.1** `/api/mirror/streak`
  - [ ] **5.2** `StreakTracker` grid
  - [ ] **5.3** `StreakSummary` paragraph
  - [ ] **5.4** Legend row
  - [ ] **5.5** Ordering + transparent + summary tests
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
- [ ] **8.0** Lens — result rendering + Save to Thread
  - [ ] **8.1** `ResultCard` reuses Phase 1 ICE components
  - [ ] **8.2** `LensLimitations` mandatory aside
  - [ ] **8.3** Lens-specific Confidence Composition note
  - [ ] **8.4** Bias Flags aside
  - [ ] **8.5** Meta row
  - [ ] **8.6** `saved_threads` migration + API
  - [ ] **8.7** `SaveToThreadButton`
  - [ ] **8.8** Saved sub-nav in sidebar
  - [ ] **8.9** "← New query" preserves text
  - [ ] **8.10** Limitations + save + preserve tests
- [ ] **12.0** Phase 1 UI polish + tester-feedback iteration
  - [ ] **12.1** Triage `notes/phase1-feedback-backlog.md`
  - [ ] **12.2** Close all P0
  - [ ] **12.3** `axe` a11y tests
  - [ ] **12.4** Lighthouse CI ≥90
  - [ ] **12.5** Copy clarity pass
  - [ ] **12.6** A11y + Lighthouse green in CI

### Tasks by developer — Riley

- [ ] **3.0** Resolved-card notification system + topbar badge
  - [ ] **3.1** `card_graded` enum value
  - [ ] **3.2** `notify_on_grade` fan-out
  - [ ] **3.3** `/api/mirror/notifications/unread`
  - [ ] **3.4** `ResolvedBadge` pulsing
  - [ ] **3.5** `ReadyToGradePanel`
  - [ ] **3.6** Read-on-viewport-intersect
  - [ ] **3.7** Scope + visibility + pulse tests
- [ ] **4.0** Reasoning-gap analysis + Map module linking
  - [ ] **4.1** Gap taxonomy
  - [ ] **4.2** `reasoning_gap_detector.analyse()`
  - [ ] **4.3** `/api/mirror/gaps`
  - [ ] **4.4** `ReasoningGapPanel`
  - [ ] **4.5** Wire `gap_insight` into expanded PredictionCard
  - [ ] **4.6** Recompute on resolve
  - [ ] **4.7** Fixture-history + UI tests
- [ ] **10.0** Email notifications for fired signals
  - [ ] **10.1** Provider creds in `.env.local`
  - [ ] **10.2** `user_email_preferences` + tokens
  - [ ] **10.3** `email_client.send()` abstraction
  - [ ] **10.4** Signal-fired template
  - [ ] **10.5** `email_on_signal.fan_out()`
  - [ ] **10.6** `/unsubscribe` endpoint
  - [ ] **10.7** Email settings page
  - [ ] **10.8** Scope + single-shot + language-lint tests
- [ ] **11.0** Factor DB expansion to all 8 sectors + The Map content
  - [ ] **11.1** Seeds: IT / Energy / Consumer / Auto / Pharma / Metals / Telecom / Infra
  - [ ] **11.2** `map_modules` migration + content
  - [ ] **11.3** Map API endpoints
  - [ ] **11.4** Map index page
  - [ ] **11.5** Map sector-detail page
  - [ ] **11.6** Cross-link gaps → modules
  - [ ] **11.7** Coverage + linked-modules tests
