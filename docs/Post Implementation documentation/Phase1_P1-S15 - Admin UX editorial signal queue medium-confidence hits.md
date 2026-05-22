# Post Implementation Detailed Document — P1-S15

**Version:** v1.0 | **Date:** 22-05-2026  
**Story ID:** P1-S15 (Phase 1, Story 15)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`

---

## Narrative — how this fits in the architecture

P1-S11 introduced the **confidence gate** and, for **medium** hits, a durable **`editorial_signal_queue`** table plus a read-only **`GET /api/admin/signal-queue`** endpoint. That backend path answers “what needs human eyes?” but left editors with only **curl**, **SQL**, or raw JSON to discover work. P1-S15 closes that operational gap with a **first-class admin screen** at **`/admin/signal-queue`**.

Architecturally, this story is a **thin consumer surface**: no new gate logic, no schema, no mutations. The page loads **pending** queue rows from the existing API, renders them in an editorial table consistent with **`/admin/queue`** (draft events), and deep-links each row into the **existing review workspace** (`/admin/review/[cardId]` from **P1-S8**). The editor’s workflow becomes: **signal monitor queues hit → open signal queue → open review → decide publish/regenerate or future resolve flows**.

**If you remember one thing:** this UI is the **operational front door** for medium-confidence automation output. Do not re-implement queue filtering or gate routing here—extend **`admin_signal_queue.py`** or **`signal_monitor_runner.py`** instead, and keep this page as a **read-only triage list**.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S15 |
| **Title** | Admin UX: editorial signal queue (medium-confidence hits) |
| **Category** | **Frontend** (Next.js admin route + RTL tests; consumes existing FastAPI endpoint from P1-S11) |

**What this story aimed to achieve (plain language)**

1. Give editors a **dedicated admin screen** listing **pending** medium-confidence signal hits from **`editorial_signal_queue`**.  
2. Show enough context per row—**card identifier**, **gate reason**, **gate tier**, **queued timestamp**—to prioritise review without opening the database.  
3. Provide a **one-click path** into the existing **`/admin/review/[cardId]`** workspace for each queued card.  
4. Handle **empty**, **loading**, and **error** states with a **retry** action, matching other Phase 1 admin pages.  

**How it fits into the overall application**

- **Upstream:** **P1-S11** writes medium-path rows and exposes **`GET /api/admin/signal-queue`**. **P1-S8** provides the review workspace the queue links into.  
- **This story:** makes the medium-confidence editorial loop **operable by non-engineers**.  
- **Downstream:** Future work may add **dismiss/resolve** actions, richer card titles, or nav links from **`ThreadReviewShell`**—those belong in later stories, not duplicated gate logic.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories (plan checklist 15.1–15.4) mapped to behaviour**

| Sub-task | What it does in the codebase |
|----------|-------------------------------|
| **15.1** | **`SignalQueueClient`** fetches **`GET {API}/api/admin/signal-queue?status=pending`** on mount via **`buildSignalQueueUrl()`**; uses **`cache: "no-store"`**. |
| **15.2** | **`SignalQueueTable`** renders a shadcn **Table** with Card / Signal reason / Gate / Queued / Review columns; **empty state** copy when `rows.length === 0`; **loading** text while fetch in flight; **error Alert** with CORS/API hint + **Try again** button. |
| **15.3** | Each row’s **Open review** link uses **`href={`/admin/review/${row.card_id}`}`** (Next.js **`Link`**). |
| **15.4** | **`page.test.tsx`** — RTL asserts formatted reason text, gate badge, review **`href`**, empty state, and fetch URL contract. |

**Functional breakdown**

- **`page.tsx`** — thin route shell wrapping **`SignalQueueClient`** in **`Suspense`** with a loading fallback (matches **`/admin/queue`** pattern).  
- **`SignalQueueClient.tsx`** — client component owning fetch state (`rows`, `loading`, `error`) and page chrome (header, SEBI editorial footer).  
- **`SignalQueueTable`** — exported presentational sub-component (table + empty/loading) to keep tests focused without full page mount where unnecessary.  
- **`formatReason()`** — humanises gate reason codes (`one_to_two_direct_sources:2` → `one to two direct sources · 2`).  
- **`formatQueuedAt()`** — locale **`dateStyle: medium`**, **`timeStyle: short`** from ISO **`created_at`**.  
- **`cardLabel()`** — displays **`payload.card_title`** when present; otherwise **`card_id`** (full UUID in **`title`** tooltip).  

**Edge cases, validations, and error handling**

| Scenario | Behaviour |
|----------|-----------|
| API non-2xx | Surfaces response body or status text in error Alert; clears rows. |
| Network / parse failure | Generic **“Failed to fetch signal queue.”** message. |
| Empty pending queue | Dashed-border empty state explaining monitor + editorial path. |
| Invalid **`created_at`** | Falls back to raw ISO string. |
| Missing **`NEXT_PUBLIC_API_BASE_URL`** | Defaults to **`http://127.0.0.1:8000`** via **`getApiBaseUrl()`** (local dev). |

**Business rules enforced (UI level)**

- Only **`status=pending`** rows are requested (hard-coded query param—no status toggle in v1).  
- Review deep link always targets **`card_id`**, not **`signal_id`** or queue row **`id`**.  
- Page is **read-only**—no dismiss/resolve mutations (queue status changes remain backend/editorial flows for later).  
- SEBI editorial disclaimer footer present (consistent with **`/admin/queue`**).  

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Client-side fetch (not RSC server fetch)** | Matches **`/admin/queue`** and **`ReviewWorkspace`** patterns; simple error/retry in one component. | Server Component + streaming: more complexity for Phase 1 optional screen. |
| **Separate `SignalQueueClient` + exported `SignalQueueTable`** | Enables focused RTL tests on table rendering without mocking full page lifecycle twice. | Monolithic page component: harder to test row/link contract. |
| **Show `card_id` when title absent** | API from P1-S11 does not join **`cards.title`**; acceptance allows **title or id**. | Backend join in S15: out of scope (consumer-only story). |
| **`payload.card_title` optional display** | Forward-compatible if runner later enriches payload without API shape change. | N/A |
| **No admin nav link added yet** | Plan did not require cross-linking; **`ThreadReviewShell`** still points to **`/admin/queue`**. | Global admin index: not in S15 AC. |
| **Relative mock path in Jest** | **`jest.mock("../../../lib/api")`** — Jest resolves **`@/lib/api`** inconsistently in this repo’s test setup. | **`@/lib/api` mock**: failed module resolution in CI/local Jest. |

**Assumptions**

- Editors can review **published / active / signal_triggered** cards in **`ReviewWorkspace`** (read-only when not **`draft`**). Medium-path hits target **live** cards, not pre-publish drafts.  
- Phase 1 admin routes remain **unauthenticated** (same posture as **`GET /api/admin/signal-queue`**).  

**⚠️ Critical — do not reverse without understanding**

- **Do not** add gate or queue-write logic to this page—keep it a **consumer** of P1-S11.  
- **Do not** change review URL pattern to **`signal_id`**—editors expect **card-centric** workspace from P1-S8.  

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1-S11:** `editorial_signal_queue` table + **`GET /api/admin/signal-queue`**. **P1-S8:** **`/admin/review/[draftId]`** review workspace + **`GET /api/admin/cards/{id}`**. |
| **Enables** | Operational editorial triage for medium-confidence automation; reduces reliance on SQL/curl during tester launch. |
| **Shared components** | shadcn **`Table`**, **`Alert`**, **`Badge`**, **`Button`**; **`getApiBaseUrl()`** from **`frontend/lib/api.ts`**. |
| **Touches** | No backend files; plan checklist updated in **`finnwise-phase1-implementation-tasks.md`**. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Pattern** | Client fetch → local state → presentational table; retry via same **`reload`** callback. |
| **Database** | **None** (reads via existing API only). |
| **API consumed** | **`GET /api/admin/signal-queue?status=pending`** — no auth in Phase 1. |
| **UI/UX** | Editorial header hierarchy mirrors **`/admin/queue`**; table layout over cards for scanability; gate as monospace **Badge**; **Open review** as dotted underline link in **`finnwise-blue`**. |
| **Libraries** | Next.js **`Link`**, React hooks, existing shadcn UI primitives—no new npm dependencies. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `page.tsx` | `frontend/app/admin/signal-queue/` | Route entry; Suspense wrapper + loading fallback. |
| `SignalQueueClient.tsx` | `frontend/app/admin/signal-queue/` | Fetch pending queue, page layout, error/retry, composes table. |
| `page.test.tsx` | `frontend/app/admin/signal-queue/` | RTL: row + href, empty state, API fetch contract. |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `finnwise-phase1-implementation-tasks.md` | `docs/plans/` | P1-S15 acceptance criteria and tasks **15.0–15.4** marked complete. |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**None in this story.** Queue schema and migrations live in **P1-S11** (`0010_signal_monitoring.sql`, table **`editorial_signal_queue`**).

| Field (via API) | UI usage |
|-----------------|----------|
| `card_id` | Review link target + primary row label (with tooltip). |
| `signal_id` | Not displayed in v1 (available in API for future columns). |
| `gate` | Badge column (expected **`medium`** for this queue). |
| `reason` | Signal reason column after **`formatReason()`**. |
| `payload` | Optional **`card_title`** for display label. |
| `created_at` | Queued timestamp column. |
| `status` | Filtered to **`pending`** at fetch time only. |

---

### B2. API / INTEGRATION CONTRACTS

**Endpoint consumed (created in P1-S11, not modified here)**

| Method | Route | Auth | Query params | Response |
|--------|-------|------|--------------|----------|
| GET | `/api/admin/signal-queue` | **None** (Phase 1 admin posture) | `status=pending` (required by UI), optional `limit` (default 100, max 200 server-side) | JSON array of **`EditorialSignalRow`** |

**Example response row (illustrative)**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "card_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "signal_id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
  "status": "pending",
  "gate": "medium",
  "reason": "one_to_two_direct_sources:2",
  "payload": {
    "gate": "medium",
    "reason": "one_to_two_direct_sources:2",
    "sources": []
  },
  "created_at": "2026-05-22T10:30:00+00:00"
}
```

**Frontend fetch call**

```http
GET {NEXT_PUBLIC_API_BASE_URL}/api/admin/signal-queue?status=pending
Cache-Control: no-store (via fetch option)
```

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**UI data flow**

```
Mount SignalQueueClient
  → buildSignalQueueUrl()
  → fetch pending rows
  → on success: setRows(data)
  → on failure: setError + clear rows
  → SignalQueueTable renders loading | empty | table
  → Review link: /admin/review/{card_id}
```

**Reason code display mapping**

- Underscores → spaces.  
- Colons → ` · ` separator (e.g. **`partial_match_only_sources:1`** → **`partial match only sources · 1`**).  

**Queue population (backend, for context — not implemented in S15)**

Medium-path hits are upserted by **`signal_monitor_runner._medium_path`** when **`confidence_gate.route`** returns **`medium`**. This page only **lists** those rows.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **No card title in API** | Rows show **UUID** unless **`payload.card_title`** is added server-side later. |
| **No dismiss/resolve UI** | Queue **`status`** transitions (`dismissed` / `resolved`) not exposed—editors must use future tooling or SQL. |
| **No cross-admin navigation** | **`ThreadReviewShell`** still links to **`/admin/queue`**, not signal queue—consider a small nav enhancement later. |
| **Published card review UX** | Link opens **`ReviewWorkspace`**; non-draft cards show read-only copy (no checklist)—expected for live-card signal hits. |
| **Phase 1 open admin** | Route and API unauthenticated—network perimeter / RBAC required before production. |

---

### B5. TESTING NOTES

| Suite | Coverage |
|-------|----------|
| **`page.test.tsx`** | **`SignalQueueTable`**: reason formatting, gate badge, review **`href`**, empty state. **`SignalQueueClient`**: fetch URL + link after async load. |

**Commands**

```bash
cd frontend
npm test -- app/admin/signal-queue/page.test.tsx
npm run typecheck
```

**Manual smoke (recommended)**

1. Ensure backend running with **`SUPABASE_DB_URL`** and migration **0010** applied.  
2. Seed or run signal monitor to create a **pending** **`editorial_signal_queue`** row.  
3. Open **`http://localhost:3000/admin/signal-queue`** with **`NEXT_PUBLIC_API_BASE_URL`** pointing at backend.  
4. Click **Open review** → confirm **`/admin/review/{card_id}`** loads.  

**Gaps**

- No Playwright E2E against live API.  
- No test for error Alert + **Try again** button interaction.  
- No backend test changes (API unchanged).  

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Where | Purpose |
|----------|-------|---------|
| **`NEXT_PUBLIC_API_BASE_URL`** | Root **`.env.local`** (read by Next.js) | Backend origin for browser **`fetch`**; defaults to **`http://127.0.0.1:8000`**. |
| **`SUPABASE_DB_URL`** | Backend only | Required for API to return rows (not a new S15 variable). |

**Deployment**

- Frontend: Vercel auto-deploy includes new route under **`frontend/app/admin/signal-queue/`**.  
- No backend redeploy required for S15 UI alone (API already shipped in P1-S11).  
- Ensure Render backend CORS allows Vercel preview/production origins (same as other admin fetches).  

---

### B7. HANDOVER NOTES FOR DEVELOPERS

1. **Start here:** `frontend/app/admin/signal-queue/SignalQueueClient.tsx` — all UI + fetch logic.  
2. **API contract:** `backend/app/api/admin_signal_queue.py` — extend response shape there if adding **card title** or **signal excerpt** joins.  
3. **Review target:** `frontend/app/admin/review/[draftId]/ReviewWorkspace.tsx` — linked by **`card_id`**.  
4. **Do not** duplicate **`confidence_gate`** or queue upsert logic in the frontend.  
5. **Adding dismiss/resolve:** implement backend mutations first, then add row actions to **`SignalQueueTable`** with optimistic or reload-on-success patterns.  
6. **Common mistake:** mocking **`@/lib/api`** in Jest without verifying resolution—follow relative path pattern used in **`page.test.tsx`**.  
7. **Contact:** **Frontend owner** for admin UX; **backend owner** for queue API / monitor runner; **Product** for editorial workflow after medium hits.  

---

## Quick reference — routes & files

| Route | Component |
|-------|-----------|
| `/admin/signal-queue` | `frontend/app/admin/signal-queue/page.tsx` → `SignalQueueClient` |

| Related backend | `backend/app/api/admin_signal_queue.py` |
| Related migration | `backend/db/migrations/0010_signal_monitoring.sql` |
| Parent story doc | `docs/Post Implementation documentation/Phase1_P1-S11 - Signal monitoring confidence gate and in-app notifications.md` |
