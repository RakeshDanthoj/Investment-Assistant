# Post Implementation Detailed Document — P2-S8

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S8 (Phase 2, Story 8)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P2-S8** completes The Lens **result state**: after P2-S7’s six-step SSE pipeline finishes, the generated card renders in the **same ICE structure as The Thread** — Insight / Context / Evidence tabs, instrument assessments, dissenting view, and framework — without duplicating layer components. A dedicated **280px aside** shows Confidence Composition (with a Lens-specific footnote about higher Judged proportion), Bias Flags from the existing `card_bias_flags` path, and a **mandatory Lens Limitations** block with exact PRD §5 Screen 5 copy.

Users can **Save to Thread**, which persists `(user_id, card_id)` in `saved_threads` (idempotent) and surfaces saved cards under a **Saved** sub-nav in the desktop sidebar. **← New query** returns to the input state while **preserving the textarea** via `RESET_TO_IDLE`. The meta row shows category + horizon tags and **Generated in Xs · Date** (seconds measured client-side during the loading stream).

**Tests executed and passed:** 4 pytest (`test_saved_threads.py`); 18 Jest across lens-related suites (`LensLimitations`, `formatGeneratedMeta`, `useLensState`, `LoadingCard`, `QueryInput`, `streamTypes`, a11y).

**Three anchors:** (1) **Reuse Phase 1 ICE components** — do not fork Insight/Context/Evidence layers; (2) **Lens Limitations cannot be removed** — trust mechanism per PRD; (3) **Save is idempotent** — repeat POST returns 200 with `created: false`.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S8 |
| **Title** | The Lens — result rendering + Save to Thread |
| **Category** | **Full Stack** (UI, API, DB) |

**What this story aimed to achieve**

Lens users who wait through generation should see a full, honest ICE card — clearly labelled as non-editorial — and optionally promote a useful card into their personal Thread collection. The result layout matches Thread rigour while making editorial vs on-demand distinction visible.

**How it fits into the overall application**

P2-S6 built query input and state machine; P2-S7 streamed real pipeline milestones. P2-S8 is the payoff: ICE rendering, Save to Thread, and sidebar discovery. Downstream **P2-S5** (email notifications) can key off `saved_threads` rows when signals fire.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | Delivered |
|----------|-----------|
| **8.1** | `ResultCard` composes Phase 1 `InsightLayer`, `ContextLayer`, `EvidenceLayer`, `IceTabs`, `DissentingView` / `InstrumentCard` / `FrameworkBehindThis` (via InsightLayer) |
| **8.2** | `LensLimitations` — mandatory aside, exact PRD title + body |
| **8.3** | `ConfidenceComposition` extended with optional `footnote`; Lens uses `LENS_CONFIDENCE_NOTE` |
| **8.4** | `BiasFlags` aside — same `bias_audit` payload as Thread |
| **8.5** | Meta row — `categoryLabel` + `horizonLabel` + `formatGeneratedMeta(seconds, date)` |
| **8.6** | Migration `0019_saved_threads.sql` + `POST/GET /api/saved-threads` |
| **8.7** | `SaveToThreadButton` — auth’d POST, status toast, `saved-threads-changed` event |
| **8.8** | `SavedThreadsNav` under **Saved** in desktop sidebar |
| **8.9** | `RESET_TO_IDLE` keeps `queryText` / sector / horizon |
| **8.10** | Tests: limitations copy, idempotent save API, preserve text on reset |

**Functional breakdown**

- **Result topbar:** ← New query, DM Mono “The Lens — Generated card”, Save to Thread, Read full ICE card → (`/thread/{cardId}`).
- **Main column:** Card title, event deck, user query echo (Playfair italic), direction/magnitude confidence strip, ICE tabs with progressive unlock (no prediction logger on Lens).
- **Aside:** Confidence + bias + Lens Limitations (sticky on large screens).
- **Save flow:** POST with Bearer token → 201 first save, 200 on repeat → toast → sidebar list refresh via `window` event.
- **Generation time:** `LoadingCard` records `startedAt` per `queryId`; passes seconds into `STREAM_COMPLETE` reducer action.

**Validations and error handling**

| Rule | Where |
|------|--------|
| Save requires auth | `CurrentUser` on saved-threads routes; button shows toast if no session |
| Card must exist | POST returns 404 `card_not_found` if `cards.id` missing |
| Idempotent save | `ON CONFLICT (user_id, card_id) DO NOTHING` + return existing `saved_at` |
| Card detail load failure | `ResultCard` shows retry + ← New query |
| Result without `card_id` | Fallback message when hash/history points to incomplete query |

**Business rules**

- Lens cards use `showPredictionLogger={false}` — predictions are a Thread/editorial behaviour.
- Lens Limitations block is mandatory on every result (test asserts exact copy).
- Saved list joins `cards` + `events` for title and category in sidebar.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Migration `0019` not `0013`/`0017`** | `0013` tester acceptances, `0017` already `user_email_preferences`; `0019` registered after `0018_map_modules`. |
| **Reuse Thread components via imports** | PRD requires identical ICE structure; avoids drift between Thread and Lens. |
| **`footnote` on shared `ConfidenceComposition`** | Single progress bar implementation; Lens-only note without a duplicate component. |
| **Client-side generation seconds** | No DB column added; measured from stream start to `complete` event (good enough for transparency meta row). |
| **`saved-threads-changed` custom event** | Sidebar is outside `LensClient`; event avoids prop-drilling through layout. |
| **Desktop-only Saved sub-nav** | Mobile uses compact top nav; saved cards still reachable via `/thread/{id}` after save. |
| **Removed `ResultPlaceholder`** | Replaced entirely by `ResultCard`; no dead shell. |

⚠️ **Do not remove `LensLimitations` from `ResultCard`** — PRD mandates non-editorial labelling on every Lens result.

⚠️ **Do not break idempotent save** — P2-S5 notification triggers may rely on stable `(user_id, card_id)` rows.

⚠️ **Register `0019_saved_threads.sql` in `migrate.py`** — filename alone does not apply; must be in `MIGRATION_FILES` tuple.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / modules |
|-----------|-----------------|
| **Upstream** | P1-S10 Thread ICE components, P1-S7 `card_pipeline` / `GET /api/cards/{id}`, P1-S13 bias flags, P2-S6 `lens_queries` + state machine, P2-S7 SSE stream + `card_id` on complete |
| **Downstream** | **P2-S5** — email when signal fires on card with prediction or **saved_threads** row |
| | **P2-S15** — Lighthouse CI for `/lens` result layout (wider grid) |
| **Shared** | `useCard`, `CardDetailResponse`, `categoryPillClass`, `horizonLabel`, Supabase session + `getApiBaseUrl` |

---

### A5. DESIGN CHOICES

**Architecture**

- `ResultCard` is a client component: fetches card via `useCard(cardId, "current")`, mirrors Thread layout without lifecycle tracker / signals / current-original toggle.
- Saved threads: thin service + FastAPI router pattern (same as Mirror / Lens list APIs).

**Database**

```sql
CREATE TABLE public.saved_threads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  card_id uuid NOT NULL REFERENCES public.cards (id) ON DELETE CASCADE,
  saved_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, card_id)
);
```

**API contracts**

| Method | Route | Auth | Notes |
|--------|-------|------|-------|
| POST | `/api/saved-threads` | Bearer | Body `{ card_id }` → `{ card_id, created, saved_at }` — **201** if new, **200** if exists |
| GET | `/api/saved-threads` | Bearer | `{ items: [{ card_id, card_title, event_category, saved_at }] }` |

**UI/UX**

- Result layout: `max-w-6xl` full width (query state stays `max-w-[680px]`).
- Aside width: `280px` column per PRD Screen 5.
- Primary CTA “Read full ICE card →” — navy `#0F172A`.
- Lens Limitations: `#F8FAFC` surface, `slate-200` border.

**Libraries**

- No new npm/pip dependencies.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| 0019_saved_threads.sql | `backend/db/migrations/0019_saved_threads.sql` | `saved_threads` table + unique constraint |
| saved_threads.py | `backend/app/services/saved_threads.py` | Save (idempotent) + list with card metadata |
| saved_threads.py | `backend/app/api/saved_threads.py` | REST routes |
| test_saved_threads.py | `backend/tests/test_saved_threads.py` | API + idempotency tests |
| ResultCard.tsx | `frontend/app/(app)/lens/_components/ResultCard.tsx` | Full ICE result layout |
| LensLimitations.tsx | `frontend/app/(app)/lens/_components/LensLimitations.tsx` | Mandatory PRD aside + exported copy constants |
| LensLimitations.test.tsx | `frontend/app/(app)/lens/_components/LensLimitations.test.tsx` | Exact copy assertion |
| SaveToThreadButton.tsx | `frontend/app/(app)/lens/_components/SaveToThreadButton.tsx` | Save action + toast |
| SavedThreadsNav.tsx | `frontend/components/Sidebar/SavedThreadsNav.tsx` | Sidebar Saved sub-nav |
| formatGeneratedMeta.ts | `frontend/lib/lens/formatGeneratedMeta.ts` | Meta row formatter |
| formatGeneratedMeta.test.ts | `frontend/lib/lens/formatGeneratedMeta.test.ts` | Meta label tests |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| main.py | `backend/app/main.py` | Register `saved_threads_router` at `/api` |
| migrate.py | `backend/app/db/migrate.py` | Register `0019_saved_threads.sql` |
| ConfidenceComposition.tsx | `frontend/app/(app)/thread/_components/aside/ConfidenceComposition.tsx` | Optional `footnote` prop |
| useLensState.ts | `frontend/lib/lens/useLensState.ts` | `generationSeconds`; `STREAM_COMPLETE` payload |
| useLensState.test.ts | `frontend/lib/lens/useLensState.test.ts` | Generation seconds + preserve text on reset |
| LensClient.tsx | `frontend/app/(app)/lens/_components/LensClient.tsx` | `ResultCard`; wide layout on result; stream seconds |
| LoadingCard.tsx | `frontend/app/(app)/lens/_components/LoadingCard.tsx` | Pass `generationSeconds` to `onComplete` |
| Sidebar.tsx | `frontend/components/Sidebar/Sidebar.tsx` | Embed `SavedThreadsNav` |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S8 marked complete |

**Removed during implementation:** `frontend/app/(app)/lens/_components/ResultPlaceholder.tsx` (replaced by `ResultCard`).

**Renamed during documentation fix:** `0017_saved_threads.sql` → `0019_saved_threads.sql` (avoid clash with `0017_user_email_preferences.sql`).

---

### A8. TESTS EXECUTED

| Test file | Command | Status | What it covers |
|-----------|---------|--------|----------------|
| `test_saved_threads.py` | `pytest tests/test_saved_threads.py -q` | **Passed (4)** | 401 without auth; 201 then 200 idempotent save; 404 missing card; GET list shape |
| `LensLimitations.test.tsx` | `jest --testPathPattern=LensLimitations` | **Passed (1)** | Mandatory block + exact PRD title/body |
| `formatGeneratedMeta.test.ts` | `jest --testPathPattern=formatGeneratedMeta` | **Passed (2)** | “Generated in Xs · date” vs date-only |
| `useLensState.test.ts` | `jest --testPathPattern=useLensState` | **Passed (7)** | Stream complete + seconds; reset preserves query text |
| `LoadingCard.test.tsx` | `jest --testPathPattern=LoadingCard` | **Passed (2)** | Six steps + disclaimer (P2-S7, regression) |
| `QueryInput.test.tsx` | `jest --testPathPattern=QueryInput` | **Passed (2)** | CTA gating (P2-S6, regression) |
| `streamTypes.test.ts` | `jest --testPathPattern=streamTypes` | **Passed (2)** | SSE step reducer (P2-S7, regression) |
| `tests/a11y/lens.test.tsx` | `jest --testPathPattern=a11y/lens` | **Passed (1)** | Lens a11y smoke |

**Combined backend:** `python -m pytest tests/test_saved_threads.py -q` → **4 passed**

**Combined frontend:** `npm test -- --testPathPattern="lens|formatGeneratedMeta|LensLimitations"` → **18 passed**

---

### A9. MANUAL VERIFICATION (operator checklist)

1. **Apply migration `0019`** (required once per environment) — see B6.
2. **Restart backend** if not running with `--reload` (new `/api/saved-threads` routes).
3. Sign in; open **`/lens`**; submit a query (requires P2-S7 pipeline + `GEMINI_API_KEY` / DB for real card).
4. Wait for loading stream to complete → **full ICE result** with aside (Confidence, Bias, Lens Limitations).
5. Confirm meta row shows **Generated in Ns · date** and category/horizon tags when set.
6. Click **Save to Thread** → toast; button shows **Saved to Thread**; **Saved** section appears in desktop sidebar with card title.
7. Click **← New query** → input view returns with **same textarea text**.
8. Open **Read full ICE card →** → `/thread/{cardId}` loads Thread experience for same card.

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- New table `saved_threads` with FK to `auth.users` and `cards`.
- Unique `(user_id, card_id)` enforces one save row per user per card.
- Index `(user_id, saved_at DESC)` for sidebar list ordering.
- **No change** to `lens_queries` schema in this story (generation seconds are client-only).

**Sequencing:** Run after `0018_map_modules.sql` (registered as `0019` in `migrate.py`).

---

### B2. API / INTEGRATION CONTRACTS

**POST `/api/saved-threads`**

```json
// Request
{ "card_id": "00000000-0000-4000-8000-000000000001" }

// Response 201 (first save)
{
  "card_id": "00000000-0000-4000-8000-000000000001",
  "created": true,
  "saved_at": "2026-05-24T12:00:00Z"
}

// Response 200 (repeat save)
{ "card_id": "...", "created": false, "saved_at": "2026-05-24T12:00:00Z" }
```

**GET `/api/saved-threads`**

```json
{
  "items": [
    {
      "card_id": "uuid",
      "card_title": "US recession impact on IT exporters",
      "event_category": "macro",
      "saved_at": "2026-05-24T12:00:00Z"
    }
  ]
}
```

**Card detail (unchanged, used by ResultCard):** `GET /api/cards/{id}?view=current` — no auth header in current `useCard` implementation (same as Thread).

---

### B3. BUSINESS LOGIC & RULES (Detailed)

```
Save to Thread
├── Authenticated user
├── card_id exists in cards
├── INSERT saved_threads
│   ├── success → created=true, HTTP 201
│   └── conflict → created=false, HTTP 200, existing saved_at
└── Dispatch saved-threads-changed → Sidebar refetch

Lens result render
├── card_id from lens_queries (stream complete or history)
├── useCard loads ICE payload
├── Aside always includes LensLimitations (non-removable)
└── RESET_TO_IDLE clears activeQueryId but keeps queryText
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **Generation seconds are client-only** | Refreshing `#result/{id}` from history without re-streaming shows date without seconds unless we add `completed_at` to `lens_queries` later. |
| **Saved sub-nav desktop only** | Mobile top nav does not list saved cards; users use Thread route or save again from Lens. |
| **No “unsave” API** | Out of scope; only save + list. |
| **Card fetch is public** | Same as Thread; RLS/network policy assumed at infra layer. |
| **E2E generation still heavy** | Full manual test needs Gemini + DB + migration 0016 + 0019. |

---

### B5. TESTING NOTES

- **Automated:** saved-threads idempotency, Lens limitations copy, meta formatter, reducer preserve-text / generation seconds.
- **Manual:** full query → stream → result → save → sidebar link → Thread deep link.
- **Gaps:** No RTL test for full `ResultCard` (would require heavy `useCard` mock); no integration test against real DB for save (unit tests monkeypatch service).

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable / step | Required for P2-S8 |
|-----------------|-------------------|
| `SUPABASE_DB_URL` | Yes — migration + save/list persistence |
| `GEMINI_API_KEY` | Only for **end-to-end** card generation (P2-S7 pipeline), not for save API alone |
| Auth session (Supabase) | Yes — save and saved list |
| **Migration apply** | **Yes — manual once per env** |

From repo root (with `.env.local` containing `SUPABASE_DB_URL`):

```bash
python scripts/apply_migrations.py
```

Or paste `backend/db/migrations/0019_saved_threads.sql` into Supabase SQL Editor.

⚠️ If `0019` was previously applied manually as `0017_saved_threads.sql`, either record `0019_saved_threads.sql` in `schema_migrations` or skip re-run if table already exists.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

| Topic | Location |
|-------|----------|
| Result layout | `frontend/app/(app)/lens/_components/ResultCard.tsx` |
| PRD copy constants | `LensLimitations.tsx` (`LENS_LIMITATIONS_*`, `LENS_CONFIDENCE_NOTE`) |
| Save API | `backend/app/api/saved_threads.py` |
| Sidebar list | `frontend/components/Sidebar/SavedThreadsNav.tsx` |
| State / hash | `frontend/lib/lens/useLensState.ts` |

**Common mistakes**

- Adding a second `0017_*.sql` migration file — check `migrate.py` sequence first.
- Forking ICE layers under `lens/` instead of importing from `thread/_components`.
- Removing `LensLimitations` when tweaking aside layout.

**Related documentation:** PRD §5 Screen 5; P2-S6/S7 post-implementation docs; `docs/plans/cross-phase-performance-standards.md` for `/lens` Lighthouse in P2-S15.
