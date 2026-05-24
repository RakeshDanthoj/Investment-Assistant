# Post Implementation Detailed Document — P2-S7

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S7 (Phase 2, Story 7)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P2-S7** turns The Lens **loading state** from a static placeholder into a live, transparent pipeline view. After a user submits a query (P2-S6), the client opens a **Server-Sent Events** stream at `GET /api/lens/queries/{id}/stream`. The backend runs the same **three-call ICE card pipeline** as Phase 1 (`card_pipeline.draft_card_from_event`), but instruments it with **six real milestones** that match PRD §5 Screen 5 exactly: Factor DB queried → Macro signals retrieved → Synthesising ICE layers → Generating dissenting view → Articulating framework → Validating numbers against Evidence. Each milestone fires when that phase of work actually completes — not on a timer.

The UI shows a centred **LoadingCard** (max 560px): the user’s question in Playfair italic with a blue left border, an animated progress bar, six step rows (pending → active/pulsing → done with green check), and the mandatory disclaimer verbatim. When generation finishes, the stream emits `complete` with `card_id`; the Lens state machine moves to **result** (still a placeholder ICE layout until **P2-S8**, but `card_id` is now populated on the query row).

**Tests executed and passed:** 9 pytest (`test_lens_stream_six_steps.py`, `test_card_pipeline.py`, `test_lens_routes.py`); 14 Jest (`streamTypes.test.ts`, `useLensState.test.ts`, `LoadingCard.test.tsx`, `QueryInput.test.tsx`); frontend `tsc --noEmit` passed.

**Three anchors:** (1) **Step labels are a shared contract** — `lens_pipeline_steps.py` and `pipelineSteps.ts` must stay in sync; (2) **Generation is stream-driven** — `enqueue_generation()` remains a no-op; the worker runs when the client connects to SSE; (3) **Do not break P2-S6 hash deep links** — `#loading/{id}` must still open the loading view and start the stream.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S7 |
| **Title** | The Lens — loading state with live six-step pipeline |
| **Category** | **Full Stack** (API SSE, services, UI) |

**What this story aimed to achieve**

While users wait 30–90 seconds for an on-demand ICE card, show **exactly what the system is doing** through six named pipeline steps that animate in sequence. The wait should feel like rigour and transparency, not an anonymous spinner.

**How it fits into the overall application**

The Lens (PRD Screen 5) has three UI states on one route: query → **loading** → result. P2-S6 built query input, history, and the state machine. P2-S7 wires **real generation progress** into loading and persists `card_id` when done. **P2-S8** renders the full ICE result and “Save to Thread” using that `card_id`. The pipeline reuses **P1-S7** `card_pipeline` (Gemini three-call synthesis) with Lens-specific synthetic `events` rows.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | Delivered |
|----------|-----------|
| **7.1** | `lens_pipeline.run(query_id)` — runs ICE pipeline, yields SSE payloads at six `on_milestone` callbacks from `card_pipeline` |
| **7.2** | `GET /api/lens/queries/{id}/stream` — `text/event-stream`, auth + ownership check |
| **7.3** | `LoadingCard` — centred max 560px, Playfair italic query echo, blue left border |
| **7.4** | `PipelineStep` — pending (grey number) / active (blue, `animate-pulse`) / done (green ✓) |
| **7.5** | `useLensStream` — authenticated fetch-based SSE reader; updates step state; `STREAM_COMPLETE` / `STREAM_ERROR` reducer actions |
| **7.6** | Progress bar — width from `progressPercentFromSteps()` (interpolates across six steps) |
| **7.7** | Disclaimer — `LENS_DISCLAIMER` constant, DM Mono 10px slate-500, verbatim PRD copy |
| **7.8** | Tests — six `done` step events in order (backend); pending→active→done (frontend `PipelineStep` + `applyStreamStep`) |

**Functional breakdown**

- **Submit (P2-S6):** `POST /api/lens/queries` → `status=queued`, view → loading, hash `#loading/{id}`.
- **Stream connect:** `LoadingCard` loads Supabase session token, `useLensStream` opens `GET .../stream` with `Authorization: Bearer`.
- **Server worker:** Background thread sets `status=running`, inserts synthetic `events` row (`event_source=lens`), runs `draft_card_from_event` with `editor_notes` = user query text, updates `lens_queries` to `done` + `card_id` (or `failed` on error).
- **SSE events:** `step` (index, name, status `active`|`done`), then `complete` (`card_id`) or `error` (`message`, optional `code` for monthly LLM budget).
- **Client completion:** All steps marked done; reducer `STREAM_COMPLETE` → view `result`; hash becomes `#result/{id}` via existing `lensHashForState`.

**Validations and error handling**

| Rule | Where |
|------|--------|
| Query must belong to current user | `get_query_for_user` before stream; 404 if missing |
| Already `done` with `card_id` | Stream short-circuits to single `complete` event (no re-generation) |
| `failed` status | Stream emits `error` without re-running pipeline |
| Pipeline / DB / LLM budget failure | `status=failed` on row; SSE `error` payload |
| Unauthenticated stream | 401 via `CurrentUser` dependency |
| Malformed SSE chunks | Client parser skips invalid JSON lines |

**Business rules**

- Six step **names** must match PRD §5 Screen 5 exactly (enforced by shared constants).
- Milestones reflect **real** pipeline work (Factor DB fetch, macro stub in evidence layer, synthesis LLM, dissent LLM, framework LLM, final Evidence/MMJ validation before persist).
- Generation consumes one **daily LLM slot** (`consume_slot_or_raise`) as in editorial draft flow.
- Lens cards are **draft** lifecycle; not published to Pulse/Thread feed by this story.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Reuse `card_pipeline` with `on_milestone` callback** | Avoid duplicating three-call orchestration; P1-S7 remains single source of truth for ICE generation. |
| **Synthetic `events` row per Lens query** | `draft_card_from_event` requires `event_id`; `canonical_url=lens:{query_id}@finnwise.internal` dedupes per query. |
| **Stream triggers generation (not `enqueue_generation`)** | Client opens SSE when loading view mounts; no separate worker queue in Phase 2. |
| **Background thread + `queue.Queue` for milestones** | `draft_card_from_event` is synchronous; thread allows interleaving SSE yields without rewriting pipeline as async generator. |
| **Fetch-based SSE instead of native `EventSource`** | Browser `EventSource` cannot set `Authorization: Bearer`; fetch + manual SSE parse matches rest of app auth. |
| **Validation milestone last (`STEP_VALIDATE`)** | PRD lists validation after framework; synthesis layers still validated immediately after synthesis call (unchanged P1-S7 safety), final milestone gates persist. |
| **Removed `LoadingPlaceholder`** | Replaced entirely by `LoadingCard`; no dual loading UIs. |

⚠️ **Do not rename pipeline steps** in only one of Python/TypeScript — UI labels and SSE `name` fields will drift from PRD.

⚠️ **Do not move generation back into `enqueue_generation` without a job runner** — today, no stream connection means no generation for `queued` rows.

⚠️ **Do not remove `on_milestone` hooks from `card_pipeline`** when editing P1-S7 — Mirror/regenerate paths pass `on_milestone=None` (no-op); Lens depends on them.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / modules |
|-----------|-----------------|
| **Upstream** | **P2-S6** — `lens_queries` table, POST/GET routes, `useLensState`, `#loading/{id}` hash |
| | **P1-S7** — `card_pipeline`, `cost_guard`, validators, Gemini prompts |
| | **P1-S3** — Bearer JWT on stream route |
| | **P1-S5** — Factor DB rows in evidence layer (banking sector in Phase 1) |
| **Downstream** | **P2-S8** — `ResultCard`, ICE layers, Save to Thread, meta row “Generated in Xs” (uses `card_id` from stream) |
| | **P2-S13** — per-user rate limits on Lens generation |
| | **P2-S15** — Lighthouse CI for `/lens` loading path |
| **Shared** | `events`, `cards`, `lens_queries.card_id`, `getApiBaseUrl`, Supabase session |

---

### A5. DESIGN CHOICES

**Architecture**

```
LensClient (loading view)
  → LoadingCard
       → useLensStream (fetch SSE)
            → GET /api/lens/queries/{id}/stream
                 → lens_pipeline.run() [generator]
                      → thread: create_lens_event → draft_card_from_event(on_milestone)
```

**Database**

- No new migration in P2-S7.
- Writes: `lens_queries.status` (`running` → `done`|`failed`), `lens_queries.card_id`; inserts `events` (`event_source='lens'`).

**API contracts**

| Method | Route | Auth | Response |
|--------|-------|------|----------|
| GET | `/api/lens/queries/{query_id}/stream` | Bearer | `text/event-stream` — see B2 |

**UI/UX**

- Loading card: `max-w-[560px]`, centred in P2-S6 column.
- Query echo: `font-display` (Playfair), italic, `border-l-4 border-[#1A4FCC]`.
- Progress: navy bar `#1A4FCC`, `transition-[width] duration-500`.
- Steps: ordered list, accessible `aria-label` on progress and step list.
- Disclaimer: exact string from PRD.

**Libraries**

- No new npm/pip dependencies.
- FastAPI `StreamingResponse` for SSE.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| lens_pipeline_steps.py | `backend/app/services/lens_pipeline_steps.py` | Six PRD step label constants |
| lens_pipeline.py | `backend/app/services/lens_pipeline.py` | Generator `run()` — pipeline + SSE payloads |
| lens_stream.py | `backend/app/api/lens_stream.py` | SSE HTTP endpoint |
| test_lens_stream_six_steps.py | `backend/tests/test_lens_stream_six_steps.py` | Six-step ordering + complete/error paths |
| pipelineSteps.ts | `frontend/lib/lens/pipelineSteps.ts` | Frontend step labels + disclaimer constant |
| streamTypes.ts | `frontend/lib/lens/streamTypes.ts` | SSE payload types, `applyStreamStep`, progress helper |
| streamTypes.test.ts | `frontend/lib/lens/streamTypes.test.ts` | Step transition + progress unit tests |
| useLensStream.ts | `frontend/lib/lens/useLensStream.ts` | Fetch SSE hook |
| LoadingCard.tsx | `frontend/app/(app)/lens/_components/LoadingCard.tsx` | Full loading UI |
| PipelineStep.tsx | `frontend/app/(app)/lens/_components/PipelineStep.tsx` | Single step row |
| LoadingCard.test.tsx | `frontend/app/(app)/lens/_components/LoadingCard.test.tsx` | PRD copy + `PipelineStep` state tests |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| card_pipeline.py | `backend/app/services/card_pipeline.py` | `on_milestone` callback; six emit points; `MilestoneCallback` type |
| lens_queries.py | `backend/app/services/lens_queries.py` | `update_query_status`, `create_lens_event_for_query`; `enqueue_generation` documented as stream-driven |
| main.py | `backend/app/main.py` | Register `lens_stream_router` at `/api` |
| LensClient.tsx | `frontend/app/(app)/lens/_components/LensClient.tsx` | `LoadingCard` + stream complete/error dispatch |
| useLensState.ts | `frontend/lib/lens/useLensState.ts` | `STREAM_COMPLETE`, `STREAM_ERROR` actions; synthetic `activeQuery` on complete |
| useLensState.test.ts | `frontend/lib/lens/useLensState.test.ts` | Stream complete/error reducer tests |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S7 acceptance + tasks marked complete |

**Removed**

| File Name | File Path | Reason |
|-----------|-----------|--------|
| LoadingPlaceholder.tsx | `frontend/app/(app)/lens/_components/LoadingPlaceholder.tsx` | Superseded by `LoadingCard` |

---

### A8. TESTS EXECUTED

| Test file | Command | Status | What it covers |
|-----------|---------|--------|----------------|
| `test_lens_stream_six_steps.py` | `pytest tests/test_lens_stream_six_steps.py -q` | **Passed (3)** | Six `done` steps in PRD order; `complete` payload; short-circuit when already `done`; `LookupError` when query missing |
| `test_card_pipeline.py` | `pytest tests/test_card_pipeline.py -q` | **Passed (2)** | Regression: mocked LLM pipeline still persists bundle after milestone refactor |
| `test_lens_routes.py` | `pytest tests/test_lens_routes.py -q` | **Passed (4)** | P2-S6 routes unchanged; no regression from lens router additions |
| `streamTypes.test.ts` | `jest --testPathPattern=streamTypes` | **Passed (2)** | `applyStreamStep` pending→active→done; progress percent increases |
| `useLensState.test.ts` | `jest --testPathPattern=useLensState` | **Passed (8)** | Includes `STREAM_COMPLETE` / `STREAM_ERROR` cases |
| `LoadingCard.test.tsx` | `jest --testPathPattern=LoadingCard` | **Passed (2)** | Six PRD step strings + disclaimer; `PipelineStep` visual states |
| `QueryInput.test.tsx` | `jest --testPathPattern=QueryInput` | **Passed (2)** | P2-S6 regression (unchanged) |

**Combined backend**

```bash
cd backend
python -m pytest tests/test_lens_stream_six_steps.py tests/test_card_pipeline.py tests/test_lens_routes.py -q
```

→ **9 passed**

**Combined frontend**

```bash
cd frontend
npm test -- --testPathPattern="lens|streamTypes"
```

→ **14 passed** (4 suites)

**Typecheck**

```bash
cd frontend
npm run typecheck
```

→ **passed**

---

### A9. MANUAL VERIFICATION (operator checklist)

1. Migration **0016** applied (from P2-S6); backend running with `SUPABASE_DB_URL` and Gemini/cost-guard env from Phase 1.
2. Sign in → `/lens` → submit a query (≥11 characters).
3. Confirm **loading card** appears with query in Playfair italic and six step labels.
4. Watch steps advance (30–90s) — not instant unless LLM mocked locally.
5. DevTools → Network: `GET /api/lens/queries/{id}/stream` stays open; EventStream or fetch shows `data: {"event":"step",...}` lines.
6. On success → UI transitions to **result** placeholder; `lens_queries.card_id` populated in DB.
7. Refresh `#loading/{id}` for a **done** query → stream should emit only `complete` (no second generation).
8. Verify disclaimer at bottom: *"Every number is validated against the Evidence layer before display."*

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**No new tables or migrations in P2-S7.**

| Table | P2-S7 usage |
|-------|-------------|
| `lens_queries` | `status`: `queued` → `running` → `done` \| `failed`; `card_id` set on success |
| `events` | One synthetic draft row per generation (`event_source = 'lens'`, dedupe via `canonical_url`) |
| `cards` | Draft ICE bundle inserted by `insert_draft_card_bundle` (P1-S7) |

---

### B2. API / INTEGRATION CONTRACTS

**GET `/api/lens/queries/{query_id}/stream`**

- **Auth:** `Authorization: Bearer <supabase_access_token>`
- **Ownership:** Query must belong to authenticated `user_id`
- **404:** `{ "detail": { "code": "lens_query_not_found", "message": "Query not found" } }`
- **Content-Type:** `text/event-stream`
- **Headers:** `Cache-Control: no-cache`, `X-Accel-Buffering: no` (proxy buffering off)

**SSE payload shapes**

```json
// Step becomes active (first step emitted at stream start; later steps after previous done)
{"event":"step","index":0,"name":"Factor DB queried","status":"active"}

// Step completed (real milestone from card_pipeline)
{"event":"step","index":0,"name":"Factor DB queried","status":"done"}

// Success terminus
{"event":"complete","card_id":"uuid"}

// Failure terminus
{"event":"error","message":"..."}

// Optional when monthly LLM budget exceeded (cost_guard)
{"event":"error","code":"llm_monthly_budget","message":"..."}
```

**Typical sequence (happy path):**  
`active(0)` → `done(0)` → `active(1)` → `done(1)` → … → `done(5)` → `complete`.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Milestone → pipeline mapping**

| Step name | Emitted after |
|-----------|----------------|
| Factor DB queried | `fetch_matrix_rows` returns (banking sector) |
| Macro signals retrieved | Macro stub appended to evidence layer |
| Synthesising ICE layers | Synthesis LLM returns; synthesis layer validators run |
| Generating dissenting view | Dissent LLM returns; dissent quality checks pass |
| Articulating framework | Framework LLM returns; framework quality checks pass |
| Validating numbers against Evidence | Final MMJ/number validation on dissent + framework before persist |

```
Client: view = loading, queryId set
  → LoadingCard mounts
  → GET /stream (Bearer)
       → lens_pipeline.run
            → if status=done + card_id → yield complete only
            → if status=failed → yield error
            → else start thread:
                 update status running
                 INSERT events (lens)
                 draft_card_from_event(on_milestone)
                 update status done + card_id
            → yield step events from milestone queue
            → yield complete | error
  → STREAM_COMPLETE → view = result, hash #result/{id}
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Follow-up |
|------------|-----------|
| **Result UI still placeholder** | **P2-S8** — full ICE layout, Lens Limitations aside, Save to Thread |
| **Sector in Factor DB hardcoded to banking** | Phase 1 `card_pipeline`; Lens sector selector not yet passed into matrix fetch |
| **Macro signals stub** | Phase 1 evidence `macro_stub`; step still fires when stub is built |
| **Re-open stream on `queued` re-runs generation** | No distributed lock; refresh during loading could start duplicate thread |
| **Thread-per-request worker** | Acceptable for Phase 2 volume; consider job queue if concurrent Lens usage grows |
| **No E2E Playwright for SSE** | Unit/integration mocks only |
| **30–90s wait still real** | Progress bar reflects steps, not wall-clock estimate |

---

### B5. TESTING NOTES

- **Automated:** Milestone order with mocked `draft_card_from_event`; reducer stream actions; `applyStreamStep` / `PipelineStep` states; `card_pipeline` regression.
- **Manual:** Full path needs live DB + Gemini + cost guard slot; verify `events.event_source='lens'` and `lens_queries.card_id`.
- **Gaps:** No HTTP-level test of `StreamingResponse`; no test with real LLM; no duplicate-stream concurrency test.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

**No new environment variables in P2-S7.**

| Requirement | Notes |
|-------------|--------|
| `SUPABASE_DB_URL` | Status updates + event/card inserts |
| Phase 1 LLM env | Same as P1-S7 (`GEMINI_*`, etc.) |
| `consume_slot_or_raise` | Daily slot consumed on each Lens generation |
| CORS | Existing FastAPI CORS allows frontend origin for long-lived GET |

**Deploy sequencing:** Deploy backend with `lens_stream` router before or with frontend that uses `LoadingCard`; P2-S6 migration must already be applied.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

| Topic | Location |
|-------|----------|
| Step label constants (backend) | `backend/app/services/lens_pipeline_steps.py` |
| Pipeline + SSE generator | `backend/app/services/lens_pipeline.py` |
| HTTP SSE route | `backend/app/api/lens_stream.py` |
| Milestone instrumentation | `backend/app/services/card_pipeline.py` (`on_milestone`) |
| Synthetic event insert | `backend/app/services/lens_queries.py` → `create_lens_event_for_query` |
| Stream hook (UI) | `frontend/lib/lens/useLensStream.ts` |
| Loading UI | `frontend/app/(app)/lens/_components/LoadingCard.tsx` |
| State transitions | `frontend/lib/lens/useLensState.ts` (`STREAM_COMPLETE`, `STREAM_ERROR`) |
| Page wiring | `frontend/app/(app)/lens/_components/LensClient.tsx` |

**Common mistakes**

- Changing step strings in only frontend or only backend.
- Expecting `POST /api/lens/queries` alone to generate a card — generation starts on **stream connect**.
- Using `EventSource` without Bearer token — use `useLensStream` fetch pattern.
- Removing hash sync when editing loading/result transitions.

**Related documentation**

- PRD §5 Screen 5 (Loading Card spec)
- `docs/Post Implementation documentation/Phase2_P2-S6 - The Lens query input history and examples.md`
- `docs/Post Implementation documentation/Phase1_P1-S7 - LLM 3-call card-synthesis pipeline (Gemini).md`
- Next: **P2-S8** — result rendering + Save to Thread
