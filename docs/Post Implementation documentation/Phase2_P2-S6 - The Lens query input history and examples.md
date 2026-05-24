# Post Implementation Detailed Document — P2-S6

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S6 (Phase 2, Story 6)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P2-S6** replaces The Lens placeholder with the full **query input** experience: a centred page (max 680px) where signed-in users type a free-text question, optionally filter by sector and horizon, and submit to create a persisted `lens_queries` row. The UI teaches capability through a **2×3 example grid** (Macro / RBI Policy / Regulatory / India-specific / Geopolitical / Budget) and surfaces **recent query history** with relative dates. All three PRD states — query, loading, result — live on one route (`/lens`) via a client-side state machine and URL hash (`#loading/{id}`, `#result/{id}`); there is no Next.js navigation between states.

The backend exposes `POST /api/lens/queries` (create + enqueue hook) and `GET /api/lens/queries/me` (last 20). Generation itself is **not** implemented here: `enqueue_generation()` is a no-op placeholder for **P2-S7**; loading and result panels are minimal shells until P2-S7 (six-step SSE pipeline) and P2-S8 (ICE result + Save to Thread).

**Tests executed and passed:** 5 pytest (`test_lens_routes.py`, `test_lens_queries_migration.py`); 8 Jest (`useLensState.test.ts`, `QueryInput.test.tsx`).

**Three anchors:** (1) **Query must exceed 10 characters** (11+ chars enforced in API and UI); (2) **hash sync** preserves shareable loading/result deep links; (3) **history `done` → result**, **`queued`/`running` → loading** without leaving `/lens`.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S6 |
| **Title** | The Lens — query input + history + examples |
| **Category** | **Full Stack** (UI, API, DB) |

**What this story aimed to achieve**

Give curious users a deliberate research entry point: type any event question, see what The Lens can answer via examples, revisit past queries, and move through query → loading → result on a single page without losing context.

**How it fits into the overall application**

The Lens is Phase 2’s on-demand ICE generator (PRD Screen 5). P2-S6 establishes the data model and input surface; **P2-S7** streams real pipeline progress into the loading state; **P2-S8** renders the generated card and “Save to Thread”. Sidebar already links to `/lens` with a Phase 2 nav badge; this story adds the purple **Phase 2** pill in the Lens page topbar per PRD.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | Delivered |
|----------|-----------|
| **6.1** | Migration `0016_lens_queries.sql` — table + `lens_query_status` enum |
| **6.2** | `POST /api/lens/queries` — insert row (`status=queued`), return `id`, call `enqueue_generation()` |
| **6.3** | `GET /api/lens/queries/me` — recent 20, newest first |
| **6.4** | `useLensState` reducer + URL hash hydration |
| **6.5** | `QueryInput` — textarea, sector/horizon selects, gated CTA |
| **6.6** | DM Mono time-estimate note below query box |
| **6.7** | `ExampleGrid` — six static examples with category pills |
| **6.8** | `QueryHistory` — relative dates via `Intl.RelativeTimeFormat` |
| **6.9** | `PhaseBadge` — purple pill in Lens topbar |
| **6.10** | Unit tests for reducer, CTA gating, hash helpers |

**Functional breakdown**

- **Query state:** `QueryInput` + `ExampleGrid` + `QueryHistory`; submit POSTs to API and transitions to loading.
- **Loading state:** `LoadingPlaceholder` shows user query in Playfair italic with blue left border and bottom disclaimer (verbatim PRD line); no live pipeline steps yet.
- **Result state:** `ResultPlaceholder` with “← New query” and DM Mono label; full ICE layout deferred to P2-S8.
- **History click:** Rehydrates textarea fields and switches view by `status` (`done` → result, `queued`/`running` → loading, `failed` → error on input view).

**Validations and error handling**

| Rule | Where |
|------|--------|
| Query length > 10 chars | `canSubmitLensQuery` / `LENS_QUERY_MIN_CHARS = 11`; Pydantic `min_length=11` on API |
| Auth required | `CurrentUser` dependency; 401 without Bearer token |
| DB unavailable | 503 with `db_unavailable` when `SUPABASE_DB_URL` missing or connection fails |
| History / submit fetch errors | `describeFetchFailure` + retry on history load |

**Business rules**

- Sector values align with `public.event_category` enum (optional).
- Horizon values match onboarding: `under_1y`, `1_3y`, `3_7y`, `7_plus` (optional).
- New queries always start as `queued`; no card is generated in this story.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Migration `0016` not `0012`** | `0012`–`0015` already used (`user_predictions_unique`, `tester_acceptances`, `gap_insight`, `notifications_card_graded`). |
| **Separate `PhaseBadge` under `lens/_components`** | Avoids collision with global sidebar `PhaseBadge` (Phase 1 tester blue pill). |
| **URL hash over query params** | Plan specified hash for shareability; avoids polluting server RSC searchParams. |
| **`enqueue_generation` no-op** | P2-S7 owns pipeline worker + SSE; POST still calls hook for stable integration point. |
| **Loading/result placeholders** | Keeps P2-S6 scope bounded; state machine and API contract ready for P2-S7/S8. |
| **No `date-fns`** | `Intl.RelativeTimeFormat` covers history labels with zero new dependencies. |

⚠️ **Do not remove hash sync** when adding P2-S7 stream — deep links to `#loading/{id}` must keep working.

⚠️ **Do not shorten query validation below 11 characters** without updating PRD and both API + `canSubmitLensQuery`.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / modules |
|-----------|-----------------|
| **Upstream** | P1-S3 auth (Bearer JWT), P1-S4 `event_category` enum, Phase 1 cards schema (`card_id` FK for future results) |
| **Downstream** | **P2-S7** — SSE `GET /api/lens/queries/{id}/stream`, `lens_pipeline`, replace `LoadingPlaceholder` |
| | **P2-S8** — ICE result UI, Save to Thread, replace `ResultPlaceholder` |
| | **P2-S15** — add `/lens` to Lighthouse CI when touching perf close-out |
| **Shared** | `PULSE_CATEGORY_OPTIONS` / `categoryPillClass`, onboarding `Horizon` type, `getApiBaseUrl`, Supabase client session |

---

### A5. DESIGN CHOICES

**Architecture**

- Client-heavy page: `LensClient` owns reducer, history fetch, submit, and hash `replaceState`.
- Backend thin API layer over `lens_queries` service (mirrors Mirror list pattern).

**Database**

- `lens_queries`: `id`, `user_id`, `query`, `sector`, `horizon`, `status`, `card_id` (nullable, for P2-S8), `created_at`.
- Index on `(user_id, created_at DESC)` for history list.

**API contracts**

| Method | Route | Auth | Body / response |
|--------|-------|------|-----------------|
| POST | `/api/lens/queries` | Bearer | `{ query, sector?, horizon? }` → `{ id, status }` (201) |
| GET | `/api/lens/queries/me` | Bearer | → `{ items: LensQueryItem[] }` (max 20) |

**UI/UX**

- Centred column `max-w-[680px]`; query box focus ring `#1A4FCC` + 3px shadow.
- Placeholder text exactly per PRD §5 Screen 5.
- Example grid `sm:grid-cols-2` (2×3).
- Purple Phase 2 badge: `Badge variant="phase2"` (`#F3E8FF` / `#6B21A8`).

**Libraries**

- Existing shadcn `Textarea`, `Select`, `Button`; Lucide icons in history list.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| 0016_lens_queries.sql | `backend/db/migrations/0016_lens_queries.sql` | `lens_queries` table + status enum |
| lens_queries.py | `backend/app/services/lens_queries.py` | Create + list + enqueue hook |
| lens.py | `backend/app/api/lens.py` | REST routes |
| test_lens_routes.py | `backend/tests/test_lens_routes.py` | API contract tests |
| test_lens_queries_migration.py | `backend/tests/test_lens_queries_migration.py` | Migration smoke |
| page.tsx | `frontend/app/(app)/lens/page.tsx` | Suspense shell |
| layout.tsx | `frontend/app/(app)/lens/layout.tsx` | Editorial font scope |
| LensClient.tsx | `frontend/app/(app)/lens/_components/LensClient.tsx` | State machine + data loading |
| LensTopbar.tsx | `frontend/app/(app)/lens/_components/LensTopbar.tsx` | Title + Phase 2 badge |
| QueryInput.tsx | `frontend/app/(app)/lens/_components/QueryInput.tsx` | Textarea, dropdowns, CTA |
| ExampleGrid.tsx | `frontend/app/(app)/lens/_components/ExampleGrid.tsx` | 2×3 examples |
| QueryHistory.tsx | `frontend/app/(app)/lens/_components/QueryHistory.tsx` | Recent queries list |
| PhaseBadge.tsx | `frontend/app/(app)/lens/_components/PhaseBadge.tsx` | Purple Phase 2 pill |
| LoadingPlaceholder.tsx | `frontend/app/(app)/lens/_components/LoadingPlaceholder.tsx` | Pre-P2-S7 loading shell |
| ResultPlaceholder.tsx | `frontend/app/(app)/lens/_components/ResultPlaceholder.tsx` | Pre-P2-S8 result shell |
| useLensState.ts | `frontend/lib/lens/useLensState.ts` | Reducer + hash helpers |
| types.ts | `frontend/lib/lens/types.ts` | Shared TS types |
| examples.ts | `frontend/lib/lens/examples.ts` | Static example copy |
| horizons.ts | `frontend/lib/lens/horizons.ts` | Horizon dropdown labels |
| relativeDate.ts | `frontend/lib/lens/relativeDate.ts` | Relative date formatter |
| useLensState.test.ts | `frontend/lib/lens/useLensState.test.ts` | Reducer + hash tests |
| QueryInput.test.tsx | `frontend/app/(app)/lens/_components/QueryInput.test.tsx` | CTA + time note tests |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| main.py | `backend/app/main.py` | Register `lens_router` at `/api` |
| migrate.py | `backend/app/db/migrate.py` | Register `0016_lens_queries.sql` |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S6 acceptance + tasks marked complete |

**Removed during implementation:** `backend/db/migrations/0015_lens_queries.sql` (renamed to `0016` to avoid clash with P2-S3 `0015_notifications_card_graded_read_at.sql`).

---

### A8. TESTS EXECUTED

| Test file | Command | Status | What it covers |
|-----------|---------|--------|----------------|
| `test_lens_routes.py` | `pytest tests/test_lens_routes.py -q` | **Passed (4)** | 401 without auth; POST returns id; POST rejects short query; GET `/me` shape |
| `test_lens_queries_migration.py` | `pytest tests/test_lens_queries_migration.py -q` | **Passed (1)** | Migration defines table + enum values |
| `useLensState.test.ts` | `jest --testPathPattern=useLensState` | **Passed (6)** | Example fill, submit→loading, history→result/loading, reset, hash round-trip, CTA length |
| `QueryInput.test.tsx` | `jest --testPathPattern=QueryInput` | **Passed (2)** | Generate disabled until 11 chars; time-estimate copy |

**Combined backend:** `python -m pytest tests/test_lens_routes.py tests/test_lens_queries_migration.py -q` → **5 passed**

**Combined frontend:** `npm test -- --testPathPattern="lens|useLensState"` → **8 passed**

**Typecheck:** `npm run typecheck` in `frontend/` → **passed**

---

### A9. MANUAL VERIFICATION (operator checklist)

1. **Apply migration `0016`** (required once per environment) — see B6.
2. **Restart or reload backend** if not using `--reload` (new routes are in `app.main`).
3. Sign in, open **`/lens`** from sidebar.
4. Confirm purple **Phase 2** badge in Lens topbar (not the blue Phase 1 tester pill in sidebar header).
5. Type ≤10 characters — **Generate card →** stays disabled; at 11+ chars it enables.
6. Click an example — textarea fills; submit creates a row (check Network: `POST /api/lens/queries` 201).
7. After submit, page shows **loading** shell (no animated steps yet — expected until P2-S7).
8. Refresh with `#result/{id}` for a `done` row in DB — result shell appears (requires seeded or manually updated `status` until pipeline exists).

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

```sql
-- Enum
CREATE TYPE public.lens_query_status AS ENUM ('queued', 'running', 'done', 'failed');

-- Table (simplified)
CREATE TABLE public.lens_queries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  query text NOT NULL,
  sector public.event_category,
  horizon text CHECK (horizon IS NULL OR horizon IN ('under_1y','1_3y','3_7y','7_plus')),
  status public.lens_query_status NOT NULL DEFAULT 'queued',
  card_id uuid REFERENCES public.cards (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
```

**Sequencing:** Run after `0015_notifications_card_graded_read_at.sql` (registered in `migrate.py` before `0016`).

---

### B2. API / INTEGRATION CONTRACTS

**POST `/api/lens/queries`**

```json
// Request
{
  "query": "What would a US recession mean for Indian IT exporters?",
  "sector": "macro",
  "horizon": "3_7y"
}

// Response 201
{ "id": "uuid", "status": "queued" }
```

**GET `/api/lens/queries/me`**

```json
{
  "items": [
    {
      "id": "uuid",
      "query": "...",
      "sector": "macro",
      "horizon": "3_7y",
      "status": "queued",
      "card_id": null,
      "created_at": "2026-05-24T12:00:00Z"
    }
  ]
}
```

**Auth:** `Authorization: Bearer <supabase_access_token>` on both routes.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

```
User opens /lens
  → load GET /api/lens/queries/me
  → optional HYDRATE_FROM_HASH from location.hash

User submits (≥11 chars)
  → POST /api/lens/queries
  → view = loading, hash = #loading/{id}

User clicks history item
  → status done     → view = result,  hash = #result/{id}
  → status queued|running → view = loading
  → status failed   → view = error (input visible)

User clicks "← New query"
  → view = idle, hash cleared
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Follow-up |
|------------|-----------|
| No real card generation | **P2-S7** pipeline + worker consuming `enqueue_generation` |
| Loading UI has no six SSE steps | **P2-S7** `LoadingCard` + `useLensStream` |
| Result is placeholder only | **P2-S8** Thread-compatible ICE layout |
| `/lens` not in Lighthouse CI yet | **P2-S15** when extending perf harness |
| `card_id` always null after submit | Populated when generation completes (P2-S7/8) |

---

### B5. TESTING NOTES

- **Automated:** reducer transitions, API mocks, migration SQL smoke, QueryInput CTA.
- **Manual:** end-to-end submit against real Supabase after migration; verify row in `lens_queries`.
- **Gap:** no integration test against live DB for insert/list; no E2E Playwright for `/lens` yet.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

**No new environment variables.**

| Requirement | Notes |
|-------------|--------|
| `SUPABASE_DB_URL` | Required for migration script and API persistence |
| Existing auth | Same Bearer flow as Mirror / Thread |
| Migration apply | From repo root (loads `.env.local` via backend settings): |

```bash
python scripts/apply_migrations.py
```

Or paste `backend/db/migrations/0016_lens_queries.sql` into Supabase SQL Editor if you prefer manual SQL.

**Deploy sequencing:** Apply `0016` before deploying backend that registers lens routes; frontend can deploy with backend (graceful empty history if API 503).

---

### B7. HANDOVER NOTES FOR DEVELOPERS

| Topic | Location |
|-------|----------|
| State machine | `frontend/lib/lens/useLensState.ts` |
| Page orchestration | `frontend/app/(app)/lens/_components/LensClient.tsx` |
| API routes | `backend/app/api/lens.py` |
| DB access | `backend/app/services/lens_queries.py` |
| P2-S7 hook | Extend `enqueue_generation()` + add `lens_stream.py` |

**Common mistakes**

- Renaming lens `PhaseBadge` and breaking import from `LensTopbar`.
- Using `0012` filename for lens migration (conflicts with existing files).
- Expecting animated pipeline or ICE card on submit in P2-S6 — only placeholders exist.

**Related documentation:** PRD §5 Screen 5; `docs/plans/cross-phase-performance-standards.md` for future `/lens` perf work.
