# Post Implementation Detailed Document — P2-S1

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P2-S1 (Phase 2, Story 1)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style (read this first)

**Phase 1 (P1-S12)** gave readers a way to log one honest prediction per card on The Thread, tied to Supabase identity and the append-only `track_record`. **P2-S1** turns that data into the first real **Mirror** experience: a signed-in user opens `/(app)/mirror`, sees a four-stat accountability strip, filters their history (All / Resolved / Active / Pending), and expands any prediction card inline to inspect three-level accuracy meters and a gap-insight slot — with **no rupee figures anywhere** on the surface.

The backend adds two authenticated read APIs: **`GET /api/mirror/predictions`** (joined with `cards` and `events`) and **`GET /api/mirror/stats`** (aggregates computed by a pure **`mirror_stats.compute()`** function with PRD threshold colouring: green at ≥70%, amber below). Grading itself is **not** part of this story; until **P2-S2** runs, accuracy columns are usually null and meters show **Monitoring**.

**Tests executed and passed (at story close-out):**

| Suite | Command | Result |
|-------|---------|--------|
| Backend | `python -m pytest tests/test_mirror_stats.py tests/test_mirror_routes.py -q` | **8 passed** |
| Frontend | `npm test -- --testPathPattern="mirror/(page\|AccuracyMeter\|FilterPills\|StatsStrip)"` | **4 passed** |

**Three anchors:** (1) **read-only Mirror APIs** over existing `user_predictions` + card/event joins; (2) **`mirror_stats.compute()`** owns strip maths and tone; (3) **expand-in-place cards** — no navigation away from the history list.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S1 |
| **Title** | The Mirror — prediction history list + stats strip |
| **Category** | **Full Stack** (read APIs + stats service + Mirror UI + tests) |

**What this story aimed to achieve (plain language)**

Returning users need a personal accountability surface that answers: *“Am I getting better at reasoning?”* — not *“How much money did I make?”* P2-S1 delivers the **prediction history list**, a **four-stat strip** (total predictions, mechanism accuracy %, market reaction match %, reasoning gaps found), **status filters**, and **expandable prediction cards** with three independent accuracy meters. The topbar reserves a **notification badge slot** for P2-S3; the expanded card reserves **gap insight + Map link** for P2-S4 once P2-S2 writes grades.

**How it fits into the overall application**

- **Upstream:** **P1-S12** (`user_predictions` + auth), **P1-S4** schema (`user_predictions` accuracy columns exist but are populated by **P2-S2**), **P1-S3** (JWT on API).
- **Parallel:** **P2-S2** (grading), **P2-S6** (Lens).
- **Downstream:** **P2-S3** (resolved-card badge in topbar slot), **P2-S4** (gap insight content + Map links), **P2-S5** (streak panel — separate route/UI).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items (plan mapping)**

| Sub-task | Delivered |
|----------|-----------|
| **1.1** | `GET /api/mirror/predictions?status=&limit=&offset=` — joins `user_predictions` → `cards` → `events`; returns card title, event metadata, lifecycle, mirror status, accuracy fields (when set). |
| **1.2** | `GET /api/mirror/stats` — total, mechanism %, market %, reasoning gaps count, `mechanism_tone` / `market_tone`. |
| **1.3** | `mirror_stats.compute(rows)` — pure function; `accuracy_tone()` at 70% threshold; tested in `test_mirror_stats.py`. |
| **1.4** | `mirror/page.tsx` + `MirrorClient` + `StatsStrip` fetching stats endpoint. |
| **1.5** | `FilterPills` + `?status=` URL sync via `router.replace`. |
| **1.6** | `PredictionCard` — category tag, event name, date, headline, “Your call”, status badge, `AccuracyMeterGroup`. |
| **1.7** | `AccuracyMeter` — Mechanism / Business impact / Market reaction bars; correct / partial / incorrect / monitoring states. |
| **1.8** | `GapInsightExpanded` — placeholder copy when `gap_insight` null; Map link when module id/name present (filled by P2-S4). |
| **1.9** | Loading skeletons, empty state (“log on Thread”), error + retry. |
| **1.10** | Automated tests: stats tone, no `₹`, three bars, filter callback. |

**Edge cases, validations, and error handling**

| Scenario | Behaviour |
|----------|-----------|
| **Not signed in** | Mirror APIs return **401**; client shows *“Sign in to view your prediction history.”* |
| **No predictions** | Empty state with link to Pulse; stats show zeros / dashes. |
| **Ungraded predictions** | Accuracy fields null → meters show **Monitoring**; stats % is **—** (`neutral` tone). |
| **Invalid `status` query** | FastAPI validates enum; unknown values → **422**. |
| **DB unavailable** | **503** `db_unavailable` when `SUPABASE_DB_URL` missing. |
| **Fetch failure** | Client `describeFetchFailure` message + **Try again** button. |
| **Filter: Resolved** | `cards.lifecycle_state = 'resolved'`. |
| **Filter: Active** | `active`, `signal_triggered`, `thesis_confirmed`, `thesis_weakened`. |
| **Filter: Pending** | All other lifecycle states (e.g. `published`, `draft`). |

**Business rules enforced (PRD-aligned)**

- **Zero rupee figures** on Mirror — enforced by product copy + `page.test.tsx` asserts no `₹` in subtree.
- **Three-level accuracy displayed separately** — never a single blended score on the card.
- **Expand inline** — click toggles `GapInsightExpanded`; no route change.
- **Stats strip colouring** — mechanism/market % use `strong` (green) ≥70%, `developing` (amber) &lt;70%, `neutral` when ungraded.
- **Reasoning gaps count** — rows with non-empty `gap_insight`, else proxy: any level `incorrect` or `partial` (until P2-S2 writes insights).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Pure `mirror_stats.compute()`** | Plan task 1.3; easy unit tests without DB. | SQL aggregates only: harder to test threshold logic. |
| **`mirror_filter_status()` from card lifecycle** | Single source for badge + API filter consistency. | Derive only on frontend: drift risk. |
| **Client-side data fetch in `MirrorClient`** | Matches Thread prediction logger auth pattern (`Bearer` from Supabase session). | RSC + server fetch: would need cookie-forwarding pattern not used elsewhere yet. |
| **No list virtualisation** | Plan: only if &gt;100 items; default limit 50. | react-window upfront: premature. |
| **`GapInsightExpanded` placeholder** | P2-S4 owns copy; slot must exist for expand UX now. | Hide expand until graded: breaks empty-state learning. |
| **`mirror/layout.tsx` editorial fonts** | PRD Playfair + DM Mono on Mirror; matches Thread layout pattern. | Root layout only: Pulse/Mirror typography inconsistent. |
| **No new migration** | `user_predictions` + `cards` + `events` already sufficient for reads. | New `mirror_predictions` view table: unnecessary denormalisation. |

**⚠️ Critical — do not reverse without replanning**

- **Do not** show portfolio P&amp;L or rupee returns on Mirror — PRD §5 Screen 4 design decision; test guards `₹`.
- **Do not** collapse three accuracy levels into one score on the card UI.
- **Do not** navigate away from the list when expanding a card — comparative learning depends on context.

**Assumptions**

- Users reach Mirror only after Phase 1 auth + tester gate (`/mirror` in `middleware.ts` and `tester-gate.ts`).
- Pagination default 50 is enough for early cohorts; `limit` max 100.
- `gap_insight` column may be added in **P2-S2** migration; P2-S1 reads it when present (list query omits until column exists in some DBs — service returns `null`).

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1-S12** predictions + auth; **P1-S4** `user_predictions`, `cards`, `events`; **P1-S3** JWT; sidebar route already registered. |
| **Enables** | **P2-S2** — populates accuracy columns consumed here; **P2-S3** — topbar badge slot (`data-testid="mirror-notification-slot"`); **P2-S4** — `gap_insight` + Map links in expand panel. |
| **Touches** | `backend/app/main.py` (router mount); `frontend/middleware.ts` (protected path); `frontend/components/Sidebar/Sidebar.tsx` (nav item). |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Pattern** | Thin API router + `mirror_predictions` query service + pure `mirror_stats` |
| **Database** | Read-only joins; no new tables |
| **API** | `GET /api/mirror/predictions`, `GET /api/mirror/stats`; **Bearer** required |
| **UI** | Sticky topbar → stats strip → scrollable list; shadcn `ToggleGroup` for filters |
| **Typography** | Playfair 28px stats, DM Mono 10px labels, Inter 11px subtext (via Tailwind utilities) |
| **Auth** | Same as `PredictionLogger`: `createClient().auth.getSession()` → `Authorization` header |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `mirror.py` | `backend/app/api/` | `GET /mirror/predictions`, `GET /mirror/stats` |
| `mirror_stats.py` | `backend/app/services/` | Pure stats + `mirror_filter_status()` |
| `mirror_predictions.py` | `backend/app/services/` | Joined list query + `stats_for_user()` |
| `test_mirror_stats.py` | `backend/tests/` | Threshold tone + filter status + compute maths |
| `test_mirror_routes.py` | `backend/tests/` | Auth, predictions shape, stats shape |
| `types.ts` | `frontend/lib/mirror/` | Shared TS types + filter options |
| `layout.tsx` | `frontend/app/(app)/mirror/` | Editorial font CSS variables |
| `page.tsx` | `frontend/app/(app)/mirror/` | Suspense shell → `MirrorClient` |
| `MirrorClient.tsx` | `frontend/app/(app)/mirror/_components/` | Fetch orchestration, list, states |
| `MirrorTopbar.tsx` | `frontend/app/(app)/mirror/_components/` | Title, subtitle, notification slot, filters |
| `StatsStrip.tsx` | `frontend/app/(app)/mirror/_components/` | Four-stat grid |
| `FilterPills.tsx` | `frontend/app/(app)/mirror/_components/` | All / Resolved / Active / Pending |
| `PredictionCard.tsx` | `frontend/app/(app)/mirror/_components/` | Expandable card |
| `AccuracyMeter.tsx` | `frontend/app/(app)/mirror/_components/` | Three labelled mini-bars |
| `GapInsightExpanded.tsx` | `frontend/app/(app)/mirror/_components/` | Expand panel slot |
| `page.test.tsx` | `frontend/app/(app)/mirror/` | No `₹` assertion |
| `AccuracyMeter.test.tsx` | `frontend/app/(app)/mirror/_components/` | Three independent bars |
| `FilterPills.test.tsx` | `frontend/app/(app)/mirror/_components/` | Filter callback |
| `StatsStrip.test.tsx` | `frontend/app/(app)/mirror/_components/` | Green/amber tone classes |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `main.py` | `backend/app/` | `app.include_router(mirror_router, prefix="/api")` |
| `page.tsx` | `frontend/app/(app)/mirror/` | Replaced Phase 2 placeholder with real page |
| `finnwise-phase2-implementation-tasks.md` | `docs/plans/` | P2-S1 acceptance criteria and tasks **1.0–1.10** marked complete |

*(Later stories may extend `MirrorClient.tsx`, `mirror.py`, and `types.ts` for P2-S3 notifications, P2-S5 streak, etc. — those are out of P2-S1 scope.)*

---

### A8. TESTS EXECUTED

| Test file | What it verifies | Status |
|-----------|------------------|--------|
| `test_mirror_stats.py::test_accuracy_tone_strong_at_threshold` | Green tone at ≥70% | **Pass** |
| `test_mirror_stats.py::test_accuracy_tone_developing_below_threshold` | Amber tone below 70% | **Pass** |
| `test_mirror_stats.py::test_accuracy_tone_neutral_when_ungraded` | Neutral when null % | **Pass** |
| `test_mirror_stats.py::test_compute_mechanism_and_market_percentages` | % maths + gaps count | **Pass** |
| `test_mirror_stats.py::test_mirror_filter_status_mapping` | resolved/active/pending mapping | **Pass** |
| `test_mirror_routes.py::test_mirror_predictions_requires_auth` | 401 without JWT | **Pass** |
| `test_mirror_routes.py::test_mirror_predictions_returns_items` | Predictions JSON shape + status filter | **Pass** |
| `test_mirror_routes.py::test_mirror_stats_returns_strip` | Stats JSON + tone fields | **Pass** |
| `page.test.tsx` | No `₹` in Mirror page subtree | **Pass** |
| `AccuracyMeter.test.tsx` | Three meters + correct/partial/incorrect labels | **Pass** |
| `FilterPills.test.tsx` | `onStatusChange` for Resolved / All | **Pass** |
| `StatsStrip.test.tsx` | Strong → green class, developing → amber | **Pass** |

**Not automated in P2-S1:** full sign-in → Thread log → Mirror list E2E; production Lighthouse on `/mirror` (deferred to **P2-S15** / Phase 1.5 perf standards).

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**No migration in P2-S1.** Reads existing tables:

| Table | Use |
|-------|-----|
| `user_predictions` | User’s logged text, accuracy columns (when graded), `logged_at` |
| `cards` | `title` (headline), `lifecycle_state` |
| `events` | `title`, `category` |

**Filter mapping (`mirror_filter_status`)**

```
lifecycle_state == 'resolved'           → mirror_status 'resolved'
in (active, signal_triggered,          → mirror_status 'active'
    thesis_confirmed, thesis_weakened)
else                                    → mirror_status 'pending'
```

---

### B2. API / INTEGRATION CONTRACTS

**`GET /api/mirror/predictions`**

- **Auth:** `Authorization: Bearer <supabase_access_token>` (required)
- **Query:** `status` optional (`resolved` \| `active` \| `pending`); `limit` (1–100, default 50); `offset` (default 0)
- **200 example (truncated):**
  ```json
  {
    "items": [
      {
        "id": "…",
        "card_id": "…",
        "prediction_text": "Mixed — competing mechanisms cancel…",
        "logged_at": "2026-05-21T12:00:00Z",
        "mechanism_accuracy": null,
        "business_accuracy": null,
        "market_accuracy": null,
        "gap_insight": null,
        "card_title": "Aviation faces margin pressure",
        "event_title": "Brent supply shock",
        "event_category": "macro",
        "lifecycle_state": "active",
        "mirror_status": "active",
        "linked_map_module_id": null,
        "linked_map_module_name": null
      }
    ],
    "limit": 50,
    "offset": 0
  }
  ```

**`GET /api/mirror/stats`**

- **Auth:** Bearer required
- **200 example:**
  ```json
  {
    "total_predictions": 3,
    "mechanism_accuracy_pct": null,
    "market_accuracy_pct": null,
    "reasoning_gaps_found": 0,
    "mechanism_tone": "neutral",
    "market_tone": "neutral"
  }
  ```

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Stats percentage (`_accuracy_pct`)**

- Only grades in `{correct, partial, incorrect}` count toward denominator.
- Numerator = count of `correct`.
- `monitoring` and `null` excluded from %.

**Reasoning gaps count**

1. If `gap_insight` non-empty → count 1 for that prediction.
2. Else if any of mechanism / business / market is `incorrect` or `partial` → count 1.

**Frontend load flow**

```
MirrorClient mount
  → getSession()
  → parallel GET /api/mirror/stats + GET /api/mirror/predictions?status=<url>
  → render StatsStrip + list | empty | error
Filter pill change
  → router.replace(?status=…)
  → effect re-fetch predictions only
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **Ungraded UX** | Until **P2-S2**, meters show Monitoring; stats show — |
| **Gap insight placeholder** | Generic copy until **P2-S4** links real Map modules |
| **Notification slot empty in P2-S1** | **P2-S3** wires `ResolvedBadge` |
| **No server-side list cache** | Every visit refetches; acceptable for v1 |
| **`linked_map_module_*` always null** | Populated when gap analysis story lands |
| **List query omits `gap_insight` column** | Safe on DBs before P2-S2 migration; field returns null |

---

### B5. TESTING NOTES

| Layer | Coverage |
|-------|----------|
| **Backend unit** | Pure stats + lifecycle filter mapping |
| **Backend route** | Auth + mocked list/stats responses |
| **Frontend unit** | No rupee, meters, filters, strip colours |
| **Manual (recommended)** | Sign in → log prediction on Thread → open Mirror → see card → expand → change filters |

**Manual checklist**

1. Signed-in user with ≥1 prediction sees stats strip and list.
2. User with zero predictions sees empty state (not error).
3. Filter pills update URL and list.
4. Expanded card shows gap placeholder (no crash).
5. Confirm no `₹` anywhere on page (visual + test).

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| **`SUPABASE_DB_URL`** | Backend mirror queries (required) |
| **`SUPABASE_URL`** + **`SUPABASE_ANON_KEY`** | JWT verification |
| **`NEXT_PUBLIC_API_BASE_URL`** | Browser fetch to API |

**No new environment variables for P2-S1.**

**Deployment sequencing**

1. Deploy backend (includes `/api/mirror/*` routes).
2. Deploy frontend (`/mirror` page).
3. **No new SQL migration** required for P2-S1 alone.
4. Restart local `uvicorn` / `npm run dev` after pulling if servers were already running.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

1. **All Mirror reads go through `mirror_predictions` + `mirror_stats`** — do not duplicate join SQL in routers.
2. **Grading writes belong in P2-S2** (`prediction_grader`) — P2-S1 only displays columns.
3. **Topbar notification slot** — extend `MirrorTopbar` `notificationSlot` prop; do not fork a second topbar.
4. **Filter URL param** is `status`, not `filter` — keep Pulse category params separate.
5. **Testing:** run mirror pytest + Jest paths above before merge.

**Related code paths**

| Concern | Location |
|---------|----------|
| Stats pure logic | `backend/app/services/mirror_stats.py` |
| List SQL | `backend/app/services/mirror_predictions.py` |
| HTTP routes | `backend/app/api/mirror.py` |
| Mirror UI shell | `frontend/app/(app)/mirror/_components/MirrorClient.tsx` |
| Prediction logging (upstream) | `frontend/.../PredictionLogger.tsx`, `backend/.../predictions.py` |

**Contact by role:** Sam — Mirror UI; Jordan — grading (P2-S2); Riley — notifications/gaps (P2-S3, P2-S4).

---

**End of document**
