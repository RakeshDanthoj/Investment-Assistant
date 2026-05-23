# Post Implementation Detailed Document — P2-S3

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S3 (Phase 2, Story 3)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P2-S2** grades predictions when a card resolves; **P2-S3** closes the feedback loop by notifying users and surfacing a pulsing Mirror topbar badge plus a **Ready to grade** right panel. When `grade_on_resolve` persists new grades, `notify_on_grade.fan_out_on_grade` inserts one unread `card_graded` row per graded user into the existing Phase 1 `in_app_notifications` table. The Mirror client loads `GET /api/mirror/notifications/unread`, shows `ResolvedBadge` only when count ≥ 1, and dismisses alerts via **viewport intersection** (50% visible) — not on tap-away.

**Tests executed and passed:** 7 pytest (`test_notify_on_grade`, `test_mirror_notifications`, `test_grade_on_resolve_notifies`); 4 Jest (`ResolvedBadge.test.tsx`, `mirror/page.test.tsx`).

**Three anchors:** (1) **`read_at IS NULL`** defines unread; (2) **fan-out runs in the same transaction as grading**; (3) **badge click / panel item scrolls and expands** the matching prediction card.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S3 |
| **Title** | Resolved-card notification system + topbar badge |
| **Category** | **Full Stack** |

**What this story aimed to achieve**

Pull users back to The Mirror when their predictions have been graded on a resolved card, with a clear unread badge and a green-tinted ready-to-grade list that jumps to the relevant history card.

**How it fits into the overall application**

Depends on P2-S2 grading; feeds P2-S4 reasoning-gap analysis (users discover grades). Reuses P1-S11 notification storage.

---

### A2. LOWER LEVEL DETAILS

| Sub-task | Delivered |
|----------|-----------|
| **3.1** | Migration `0015_notifications_card_graded_read_at.sql` — `read_at` column + partial index for unread `card_graded` |
| **3.2** | `notify_on_grade.fan_out_on_grade` — one row per newly graded user; skips duplicate unread for same card |
| **3.3** | `GET /api/mirror/notifications/unread`, `POST /api/mirror/notifications/{id}/read` |
| **3.4** | `ResolvedBadge` — `thread-signal-pulse` keyframe, copy with count |
| **3.5** | `ReadyToGradePanel` — green-tinted list, click scrolls/expands card |
| **3.6** | `IntersectionObserver` at 50% visibility marks read |
| **3.7** | Backend + RTL tests |

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Migration `0015` not `0011`** | `0011` already used for bias flags. |
| **`kind` remains `text`** | Matches Phase 1 table; `card_graded` documented in migration comment. |
| **Dismiss on viewport, not badge tap** | Matches acceptance criteria; badge/panel clicks only navigate. |
| **Fan-out after each grade batch** | Same DB transaction as `grade_on_resolve` commit. |

---

### A4. APPLICATION LINKAGE SUMMARY

- **Upstream:** P1-S11 `in_app_notifications`, P2-S2 `grade_on_resolve`.
- **Downstream:** P2-S4 gap analysis; optional Phase 2 backlog for global `signal_fired` read/unread.

---

### A5. DESIGN CHOICES

- PRD two-column Mirror layout introduced for right panel (`min-[960px]`).
- `PredictionCard` supports controlled `expanded` + `forwardRef` for scroll and observer targets.

---

### A6. FILES CREATED

| File | Purpose |
|------|---------|
| `backend/db/migrations/0015_notifications_card_graded_read_at.sql` | `read_at` + index |
| `backend/app/services/notify_on_grade.py` | Fan-out + unread helpers |
| `backend/app/api/mirror_notifications.py` | Unread + mark-read routes |
| `frontend/.../ResolvedBadge.tsx` | Topbar badge |
| `frontend/.../ReadyToGradePanel.tsx` | Right panel list |
| `backend/tests/test_notify_on_grade.py` | Fan-out scope |
| `backend/tests/test_mirror_notifications.py` | API shapes |
| `backend/tests/test_grade_on_resolve_notifies.py` | Hook wiring |
| `frontend/.../ResolvedBadge.test.tsx` | RTL pulse + hidden when zero |

---

### A7. FILES MODIFIED

| File | Change |
|------|--------|
| `backend/app/jobs/grade_on_resolve.py` | Calls `fan_out_on_grade` after grading |
| `backend/app/api/mirror.py` | Includes notifications sub-router |
| `backend/app/db/migrate.py` | Registers `0015` |
| `frontend/.../MirrorClient.tsx` | Badge, panel, observer, two-column layout |
| `frontend/.../PredictionCard.tsx` | Controlled expand + ref/id |
| `frontend/lib/mirror/types.ts` | Unread notification types |

---

### A8. TESTS EXECUTED (ALL PASSED)

**Backend:** `pytest tests/test_notify_on_grade.py tests/test_mirror_notifications.py tests/test_grade_on_resolve_notifies.py` — 7 passed.

**Frontend:** `jest ResolvedBadge|mirror/page` — 4 passed.

---

### A9. MANUAL VERIFICATION

1. Apply migration `0015` on Supabase (`apply_migrations` or SQL runner).
2. Resolve a card with a logged prediction (grading job runs).
3. Open `/mirror` — badge + Ready to grade panel appear.
4. Click panel item — card scrolls into view and expands.
5. Scroll graded card into view — badge count drops after ~50% visible (read).
