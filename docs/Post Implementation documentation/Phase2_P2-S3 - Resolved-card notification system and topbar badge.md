# Post Implementation Detailed Document — P2-S3

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S3 (Phase 2, Story 3)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P2-S2** grades user predictions when an ICE card enters `resolved`. **P2-S3** closes the feedback loop: after grading, the platform inserts an in-app notification (`kind = card_graded`) for each affected user, and The Mirror surfaces a pulsing topbar badge plus a green **Ready to grade** panel. Unread state is `read_at IS NULL` on `in_app_notifications`. Dismissal happens only when the user actually views the graded prediction card (50% viewport intersection via `IntersectionObserver`) — not when they tap elsewhere or only open the badge.

Fan-out runs in the **same database transaction** as `grade_on_resolve` (after new grades are persisted). The Mirror client calls `GET /api/mirror/notifications/unread` with a Supabase Bearer token; badge and panel items scroll to and expand the matching `PredictionCard` by `prediction_id`.

**Tests executed and passed:** 7 pytest (`test_notify_on_grade.py`, `test_mirror_notifications.py`, `test_grade_on_resolve_notifies.py`); 4 Jest (`ResolvedBadge.test.tsx`, `mirror/page.test.tsx`).

**Three anchors:** (1) **`read_at IS NULL`** = unread; (2) **fan-out only for users graded in the current run** (idempotent with P2-S2); (3) **badge/panel navigate; viewport marks read**.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S3 |
| **Title** | Resolved-card notification system + topbar badge |
| **Category** | **Full Stack** |

**What this story aimed to achieve**

When a card the user predicted on is resolved and graded, they should see a clear reason to return to The Mirror: a pulsing “N cards resolved — ready to grade” badge and a right-panel list that jumps straight to the graded prediction. Notifications clear only after they have actually seen the card, not on accidental taps.

**How it fits into the overall application**

This story sits between **P2-S2** (which writes grades) and **P2-S4** (reasoning-gap analysis). It reuses the Phase 1 **`in_app_notifications`** table (P1-S8 publish, P1-S11 `signal_fired`) and the **P2-S1** Mirror shell (topbar slot, prediction list). It does not send email; that is a later story.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **3.1** | Migration `0015`: `read_at` on `in_app_notifications`; partial index for unread `card_graded`. |
| **3.2** | `notify_on_grade.fan_out_on_grade(cur, card_id, user_ids)` — one row per newly graded user; skips duplicate unread for same `(user, card)`. |
| **3.3** | `GET /api/mirror/notifications/unread` (count + list); `POST /api/mirror/notifications/{id}/read`. |
| **3.4** | `ResolvedBadge` — blue pill, `thread-signal-pulse` dot, hidden when count = 0. |
| **3.5** | `ReadyToGradePanel` — PRD green tint; click scrolls/expands target card. |
| **3.6** | `IntersectionObserver` threshold 0.5 on prediction card → POST mark-read. |
| **3.7** | Automated tests for fan-out scope, API shapes, badge visibility, pulse class. |

**Functional breakdown**

1. Card resolves → P2-S2 grades → `fan_out_on_grade` inserts `card_graded` with payload `{ card_title, event_title, resolved_at }`.
2. User opens `/mirror` while signed in → client fetches unread list → badge + panel render.
3. User clicks badge or panel row → `prediction_id` used to `scrollIntoView` + set `expanded` on `PredictionCard`.
4. Card ≥50% visible → `POST .../read` → badge count decreases.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| No session / missing Bearer | Mirror shows “Sign in to view…” (same as P2-S1); unread API returns 401. |
| Zero unread | `ResolvedBadge` returns `null` (not rendered). |
| Duplicate fan-out | `NOT EXISTS` guard: no second unread `card_graded` for same user+card. |
| Re-run grading (P2-S2 idempotent) | No new grades → no new notifications. |
| Mark-read for wrong user / already read | API returns 404. |
| DB unavailable | 503 with `db_unavailable` (consistent with other Mirror routes). |

**Business rules**

- Badge copy: singular vs plural from unread count.
- Only `kind = 'card_graded'` with `read_at IS NULL` counts as unread for Mirror.
- Dismissal is **view-based**, not tap-away (PRD §5 Screen 4).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Migration `0015` not `0011`** | `0011_card_bias_flags.sql` already applied in sequence. |
| **`kind` stays `text`** | Matches Phase 1 schema; `card_graded` documented in migration comment, not a new PG enum. |
| **Unread = `read_at IS NULL`** | Minimal change; optional Phase 2 backlog can extend to `signal_fired`. |
| **Fan-out in grade transaction** | Notifications never exist without persisted grades. |
| **Dismiss on viewport, not badge click** | Matches acceptance criteria; badge/panel only navigate. |
| **Sub-router on `/api/mirror`** | Keeps Mirror API cohesive vs global `/api/notifications` (Pulse signal badge). |

⚠️ **Do not mark notifications read on badge click alone** — that would violate story acceptance and PRD intent.

⚠️ **Do not fan-out to all users** — only `user_predictions` rows graded in the current run (users with a logged prediction on that card).

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / artifacts |
|-----------|---------------------|
| **Upstream** | P1-S8/P1-S11 `in_app_notifications`; P1-S12 `user_predictions`; P2-S1 Mirror UI; P2-S2 `grade_on_resolve`. |
| **Downstream** | P2-S4 reasoning-gap panel; P2-S5 streak (same Mirror layout). |
| **Shared** | `in_app_notifications`, `user_predictions`, Mirror `PredictionCard`, Supabase JWT auth (`CurrentUser`). |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Service (`notify_on_grade`) + thin API (`mirror_notifications`) + client observer pattern. |
| **Schema** | Add `read_at timestamptz`; partial index `WHERE kind = 'card_graded' AND read_at IS NULL`. |
| **API auth** | Bearer JWT on both unread and mark-read (same as `/api/mirror/predictions`). |
| **UI** | Two-column Mirror at `min-[960px]`; `thread-signal-pulse` from `globals.css` (§8.6). |
| **Libraries** | `lucide-react` ChevronRight in panel; native `IntersectionObserver` (no extra dep). |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| 0015 migration | `backend/db/migrations/0015_notifications_card_graded_read_at.sql` | `read_at` + unread index |
| notify_on_grade.py | `backend/app/services/notify_on_grade.py` | Fan-out, list unread, mark read |
| mirror_notifications.py | `backend/app/api/mirror_notifications.py` | HTTP routes |
| ResolvedBadge.tsx | `frontend/app/(app)/mirror/_components/ResolvedBadge.tsx` | Topbar pulsing badge |
| ReadyToGradePanel.tsx | `frontend/app/(app)/mirror/_components/ReadyToGradePanel.tsx` | Right-panel list |
| ResolvedBadge.test.tsx | `frontend/app/(app)/mirror/_components/ResolvedBadge.test.tsx` | RTL: pulse, zero hidden |
| test_notify_on_grade.py | `backend/tests/test_notify_on_grade.py` | Fan-out SQL scope |
| test_mirror_notifications.py | `backend/tests/test_mirror_notifications.py` | API contract |
| test_grade_on_resolve_notifies.py | `backend/tests/test_grade_on_resolve_notifies.py` | Job wiring |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| grade_on_resolve.py | `backend/app/jobs/grade_on_resolve.py` | Collect `graded_user_ids`; call `fan_out_on_grade` before commit |
| mirror.py | `backend/app/api/mirror.py` | `include_router(mirror_notifications_router)` |
| migrate.py | `backend/app/db/migrate.py` | Register `0015_notifications_card_graded_read_at.sql` |
| MirrorClient.tsx | `frontend/app/(app)/mirror/_components/MirrorClient.tsx` | Unread fetch, badge, panel, observer, two-column layout |
| PredictionCard.tsx | `frontend/app/(app)/mirror/_components/PredictionCard.tsx` | `forwardRef`, controlled `expanded`, `id` / `data-prediction-id` |
| types.ts | `frontend/lib/mirror/types.ts` | `MirrorUnreadNotification`, response types |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S3 checkboxes marked complete |

---

### A8. TESTS EXECUTED

| Test file | Status | What it covers |
|-----------|--------|----------------|
| `test_notify_on_grade.py` | **Passed (2)** | Fan-out SQL targets graded `user_predictions` only; empty `user_ids` early return |
| `test_mirror_notifications.py` | **Passed (4)** | Unread list shape; empty list; mark-read 200/404 |
| `test_grade_on_resolve_notifies.py` | **Passed (1)** | `grade_predictions_for_card` invokes `fan_out_on_grade` |
| `ResolvedBadge.test.tsx` | **Passed (3)** | Hidden at 0; pulse class; singular/plural copy; click handler |
| `mirror/page.test.tsx` | **Passed (1)** | No `₹` on Mirror page (P2-S1 regression) |

**Backend command**

```text
cd backend
python -m pytest tests/test_notify_on_grade.py tests/test_mirror_notifications.py tests/test_grade_on_resolve_notifies.py -q
```

→ **7 passed**

**Frontend command**

```text
cd frontend
npm test -- --testPathPattern="ResolvedBadge|mirror/page"
```

→ **4 passed**

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Table:** `public.in_app_notifications` (existing, P1-S8)

| Column | Change |
|--------|--------|
| `read_at` | `timestamptz NULL` — set when user views graded card |
| `kind` | New value: `'card_graded'` (text, not enum) |

**Index:** `idx_in_app_notifications_card_graded_unread` on `(user_id, created_at DESC)` WHERE `kind = 'card_graded' AND read_at IS NULL`.

**Payload example (`card_graded`):**

```json
{
  "card_title": "Aviation faces margin pressure",
  "event_title": "Brent supply shock",
  "resolved_at": "2026-05-20T12:00:00+00:00"
}
```

**Join for unread list:** `in_app_notifications` ⋈ `user_predictions` on `(card_id, user_id)` to return `prediction_id` for UI scroll targeting.

**Migration sequence:** Apply after `0014_user_predictions_gap_insight.sql`.

---

### B2. API / INTEGRATION CONTRACTS

| Method | Route | Auth | Response |
|--------|-------|------|----------|
| GET | `/api/mirror/notifications/unread` | Bearer (Supabase JWT) | `{ count, items[] }` |
| POST | `/api/mirror/notifications/{notification_id}/read` | Bearer | `{ ok: true }` or 404 |

**Unread item shape**

```json
{
  "id": "uuid",
  "card_id": "uuid",
  "prediction_id": "uuid",
  "event_title": "string",
  "card_title": "string",
  "resolved_at": "datetime | null",
  "created_at": "datetime"
}
```

**Example unread response**

```json
{
  "count": 1,
  "items": [
    {
      "id": "a1b2c3d4-...",
      "card_id": "card-uuid",
      "prediction_id": "pred-uuid",
      "event_title": "Brent supply shock",
      "card_title": "Aviation margin pressure",
      "resolved_at": "2026-05-20T12:00:00Z",
      "created_at": "2026-05-21T10:00:00Z"
    }
  ]
}
```

Phase 1 **`GET /api/notifications`** is unchanged (Pulse `signal_fired` badge).

---

### B3. BUSINESS LOGIC & RULES (Detailed)

```
Card → resolved (P2-S2 hook)
  → For each user_prediction with mechanism_accuracy IS NULL:
       grade → persist
       → collect user_id
  → fan_out_on_grade(card_id, user_ids)
       → INSERT card_graded WHERE NOT EXISTS unread row for (user, card)
  → commit

User opens Mirror (authenticated)
  → GET unread
  → if count ≥ 1: show ResolvedBadge + ReadyToGradePanel

User clicks panel row / badge
  → expand prediction card + scrollIntoView
  → (notification still unread)

Card ≥50% in viewport
  → POST mark-read
  → read_at = now()
  → badge count decreases
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Notes |
|------------|--------|
| **No admin “Resolve card” UI** | Grading + notify require calling `transition_card_to_resolved` manually (Python) until editorial resolve API exists. |
| **Auth required for Mirror data** | Phase 1 routes are not gated, but Mirror/notifications APIs need a real Supabase session (see B6). |
| **`signal_fired` still has no read state** | Backlog in Phase 2 plan — only `card_graded` uses `read_at` today. |
| **Filtered prediction list** | If status filter hides the graded card, panel click scrolls to an off-list element only if that card is in the current fetch; user may need **All** or **Resolved** filter. |
| **No E2E Playwright** | Unit/API tests only; full magic-link → grade → badge flow is manual. |

---

### B5. TESTING NOTES

| Type | Covered |
|------|---------|
| **Automated** | Fan-out SQL guards; API JSON shapes; badge DOM; grade job imports fan-out |
| **Manual (required)** | Migration applied; sign-in; log prediction; resolve+grade; badge; scroll dismiss |

See **Manual verification checklist** below.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required for P2-S3 testing |
|----------|----------------------------|
| `SUPABASE_DB_URL` | Yes — migrations + notifications |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` | Yes — JWT verification on API |
| `GEMINI_API_KEY` | Yes — if running live P2-S2 grading (tests can use fake LLM) |
| `NEXT_PUBLIC_API_BASE_URL` | Yes — frontend → backend (e.g. `http://127.0.0.1:8000`) |

No new env vars were introduced by P2-S3.

⚠️ **`NEXT_PUBLIC_FINNWISE_USER_ID`** is not used by this story — Mirror uses `supabase.auth.getSession()` like P2-S1.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing this code**

1. Read P2-S2 `grade_on_resolve.py` — notifications are downstream of grading.
2. Do not conflate with `GET /api/notifications` (Thread signal badge).
3. Preserve viewport-dismiss behaviour — product requirement.

**Key paths**

| Concern | Path |
|---------|------|
| Fan-out SQL | `backend/app/services/notify_on_grade.py` |
| Routes | `backend/app/api/mirror_notifications.py` |
| Mirror UX | `frontend/app/(app)/mirror/_components/MirrorClient.tsx` |
| Pulse animation | `frontend/app/globals.css` → `.thread-signal-pulse` |

**Common mistakes**

- Marking read on badge click only.
- Fan-out to all `session_profiles` instead of predictors only.
- Forgetting migration `0015` (`read_at` column missing → SQL errors on unread query).

---

## Manual verification checklist (operator)

You must do these steps locally; they are **not** automated in CI.

### 1. Apply database migration (one-time per environment)

From repo root (see `docs/PRD/Learnings.md`):

```text
pip install -e "./backend[dev]"
python scripts/apply_migrations.py
```

Confirm in Supabase SQL editor:

```sql
SELECT filename, applied_at
FROM public.schema_migrations
WHERE filename = '0015_notifications_card_graded_read_at.sql';
```

Also confirm column exists:

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'in_app_notifications' AND column_name = 'read_at';
```

### 2. Sign in once (required for Mirror + predictions)

P2-S3 APIs require a **Supabase Bearer token**. Phase 1 does not redirect anonymous users, but Mirror will show “Sign in to view your prediction history” without a session.

1. Open `http://localhost:3000/sign-in`
2. Complete magic link (same browser you use for dev)
3. Complete `/tester-briefing` if middleware redirects you (first time per user)

Session cookies persist across `pnpm dev` restarts — you do **not** need to sign in after every code change.

### 3. Log a prediction (prerequisite)

1. Open a **published/active** Thread card
2. Use **Prediction Logger** to log one of the four fixed strings
3. Requires signed-in session (P1-S12)

### 4. Resolve and grade the card (no admin UI yet)

From `backend/` with venv active and `.env.local` loaded:

```python
from uuid import UUID
from app.jobs.grade_on_resolve import transition_card_to_resolved

card_id = UUID("your-card-uuid-here")
result = transition_card_to_resolved(card_id)
print(result)  # {"card_id": "...", "graded": N}
```

Requires: card in a resolvable lifecycle state, `track_record` initial_publish row, `GEMINI_API_KEY` for live LLM grading.

This run grades predictions **and** inserts `card_graded` notifications.

### 5. Verify Mirror UI

1. Backend: `uvicorn app.main:app --reload --port 8000`
2. Frontend: `npm run dev` in `frontend/`
3. Open `http://localhost:3000/mirror` (signed in)
4. Expect: pulsing badge + **Ready to grade** panel with at least one item
5. Click panel row → card scrolls into view and expands
6. Scroll graded card until mostly visible → badge count drops (read)

### 6. Optional API smoke (curl)

Replace `TOKEN` and `NOTIFICATION_ID`:

```text
curl -s -H "Authorization: Bearer TOKEN" http://127.0.0.1:8000/api/mirror/notifications/unread
curl -s -X POST -H "Authorization: Bearer TOKEN" http://127.0.0.1:8000/api/mirror/notifications/NOTIFICATION_ID/read
```

---

## Summary: what you need to do manually

| Step | Required? | Frequency |
|------|-----------|-----------|
| Run migration `0015` | **Yes** | Once per DB environment |
| Sign in via magic link | **Yes** (for real UI test) | Once per browser until cookies cleared |
| Log prediction on a card | **Yes** | Per test scenario |
| Call `transition_card_to_resolved` | **Yes** (until resolve API exists) | Per card you want to test |
| Start backend + frontend | **Yes** | Each dev session |
| Re-run automated tests | Optional | Before merge |

Nothing else is required in Vercel/Render config for this story beyond existing Supabase and API env vars.
