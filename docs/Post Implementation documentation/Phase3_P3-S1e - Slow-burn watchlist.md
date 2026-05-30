# Post Implementation Detailed Document — P3-S1e

**Version:** v1.0 | **Date:** 30-05-2026  
**Story ID:** P3-S1e (Phase 3, Story 1e)  
**PRD2 gap:** G-05  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **5.0**–**5.6**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §4.3, `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` G-05

---

## Narrative style (read this first)

Long-lead risks (monsoon, budget cycle, pending SEBI consultations) do not fit the 4-hour NewsAPI/RBI ingest cadence. Without a durable list, a solo builder loses track of them between editorial sprints. **P3-S1e** adds a **database-backed slow-burn watchlist**, a minimal **editor review UI** at `/editor/watchlist`, and **Sunday digest email sections** that surface up to 10 watching items and 10 pending `dedup_review_queue` rows (from **P3-S1c**).

Escalation is **manual only** in Phase 3: the editor clicks **Escalate**, which inserts a **draft** `events` row with `event_source = 'watchlist'` and marks the watchlist item `escalated`. There is no IMD/SEBI scraper or regex auto-escalation (deferred to Phase 4 per PRD2 workshop). Access is restricted to Product Owner emails on **`ADMIN_EMAILS`** (same allow-list pattern as P2-S13 admin metrics), on both the Next.js page and FastAPI routes under `/api/editor/watchlist`.

The Sunday **editorial digest** template (`editorial_digest.html`) was extended in this story: it now includes watchlist and dedup sections alongside the **NewsAPI factor poll summary** introduced in **P3-S1d**. Sending the digest is implemented (`send_editorial_digest`) but **not scheduled** — operators must trigger it manually or add a cron later.

**Tests executed and passed (P3-S1e–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Watchlist migration SQL contract | `python -m pytest backend/tests/test_watchlist_migration_sql.py -q` | **2 passed** |
| Watchlist escalate + seeds (integration) | `python -m pytest backend/tests/test_watchlist_escalate.py -q` | **3 passed** |
| Editorial digest sections | `python -m pytest backend/tests/test_editorial_digest.py -q` | **2 passed** |
| Editor watchlist API (auth + escalate shape) | `python -m pytest backend/tests/test_editor_watchlist_api.py -q` | **2 passed** |
| NewsAPI poll + digest template (P3-S1d regression) | `python -m pytest backend/tests/test_newsapi_poll_digest.py -q` | **2 passed** |
| **Combined P3-S1e slice** | `python -m pytest backend/tests/test_watchlist_migration_sql.py backend/tests/test_watchlist_escalate.py backend/tests/test_editorial_digest.py backend/tests/test_editor_watchlist_api.py backend/tests/test_newsapi_poll_digest.py -q` | **11 passed** |
| Lint (watchlist modules) | `python -m ruff check backend/app/services/watchlist.py backend/app/api/editor_watchlist.py backend/app/services/editorial_digest.py` | **All checks passed** |
| Frontend build | `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` (from `frontend/`) | **Pass** (route `/editor/watchlist` present) |

Integration tests require `SUPABASE_DB_URL` in `.env.local`; CI skips them when unset.

**Three anchors for handover:** (1) **Apply migration `0025` once per environment** before using the UI or API; (2) **`ADMIN_EMAILS` must match on Vercel and Render** — page gate and API both use it; (3) **Do not add auto-escalation in Phase 3** without PO sign-off — scope was explicitly manual-only.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S1e |
| **Title** | Slow-burn watchlist |
| **Category** | **Full Stack** (DB migration + API + `/editor/watchlist` UI + digest email template) |
| **Points / owner (plan)** | 3 · Riley |
| **Depends on** | P3-S0 (events table baseline); benefits from P3-S1c (`dedup_review_queue` for digest) |
| **Parallel with** | P3-S1c, P3-S1d |
| **Blocks** | P3-T2 (data pipeline test gate lists watchlist + dedup in Sunday review) |

**What this story aimed to achieve (plain language)**

Give the Product Owner a durable place to track slow-moving risks (elections, monsoon, budget, regulatory reviews, geopolitical tensions) that will not appear as breaking NewsAPI headlines. Each item can be reviewed weekly, status-updated, or **escalated** into the normal editorial pipeline as a draft event. The Sunday digest email reminds the editor what is still **watching** and what dedup collisions need human review.

**How it fits into the overall application**

- **Upstream:** P3-S0 synthetic isolation and core `events` schema; P3-S1c populates `dedup_review_queue` for cross-category collisions.
- **This story:** Operational process for long-lead editorial memory — complements high-frequency ingest (P1-S6, P3-S1d).
- **Downstream:** P3-T2 integration gate; future Phase 4 could add RSS monitors matching `escalation_trigger` text.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **5.1** | Migration `0025_watchlist_items.sql`: table + 5 fixed-id seed rows (PRD2 categories). |
| **5.2** | API: `GET` list, `PATCH` status, `POST .../escalate` → `events` insert + item `escalated`. |
| **5.3** | `/editor/watchlist` page: table, status dropdown, Escalate button. |
| **5.4** | `ADMIN_EMAILS` allow-list on API (`require_admin`) and Next.js page (`editor-admin.ts`). |
| **5.5** | `editorial_digest.html` + `editorial_digest.py`: watchlist (≤10) + dedup queue (≤10) sections. |
| **5.6** | Tests: migration contract, escalate → event, API auth, digest render. |

**Functional breakdown**

1. Editor signs in with allow-listed email → opens `/editor/watchlist`.
2. Client fetches `GET /api/editor/watchlist` with Bearer token.
3. **Status change:** `PATCH /api/editor/watchlist/{id}` with `{ "status": "watching" \| "escalated" \| "closed" }` sets `last_reviewed_at`.
4. **Escalate:** `POST /api/editor/watchlist/{id}/escalate` in a transaction:
   - `INSERT` into `events` (`event_source='watchlist'`, `canonical_url=watchlist:{id}`, `confidence_score=55`, `lifecycle_state=draft`).
   - `UPDATE watchlist_items` → `status='escalated'`, `escalated_event_id` set.
5. Draft event appears in existing **`/admin/queue`** (filter by source `watchlist` if needed).
6. Digest builder loads watching items + pending dedup rows (cap 10 each) into HTML for email.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Missing `SUPABASE_DB_URL` | API returns 503 from connection layer on DB routes. |
| Unknown watchlist `id` | `404` `watchlist_not_found`. |
| Escalate when already escalated (with `escalated_event_id`) | `409` `already_escalated`. |
| Escalate when `closed` | `409` `watchlist_closed`. |
| Re-escalate same item after DB cleanup | `ON CONFLICT (event_source, canonical_url)` updates title/category on existing event row. |
| Invalid `category` in DB | `EventCategory` validation on escalate may raise (seeds use valid enum values). |
| Non-admin email | `403` on API; forbidden page on Next.js. |
| Email not configured | `send_editorial_digest` no-ops (`False`); template still renderable for preview. |
| Digest cap | Max 10 watchlist + 10 dedup rows per send (constants in `editorial_digest.py`). |

**Business rules enforced**

- **G-05 / workshop:** Manual escalation only in Phase 3 — no auto-create from triggers.
- **`escalation_trigger`:** Human-readable text only; not evaluated by code.
- **Escalated events:** `event_source = 'watchlist'` (not `newsapi` / `rbi_rss`).
- **Default confidence on escalate:** `55` (editorial queue band; not auto-published).
- **Seeds:** Five PRD2 slow-burn categories pre-loaded; idempotent `ON CONFLICT (id) DO NOTHING`.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **`/editor/watchlist` not `/admin/watchlist`** | Phase 3 plan + PRD2 workshop: editorial surface separate from P1 admin queue. | Reuse `/admin/queue` only: no room for watchlist-specific columns/triggers. |
| **`ADMIN_EMAILS` (not new env var)** | Reuses P2-S13 `require_admin`; one PO list. | `WATCHLIST_ADMIN_EMAILS`: duplicate config risk. |
| **Postgres direct writes for watchlist** | Escalate needs transaction + `FOR UPDATE`; matches S1c dedup style. | Supabase REST `event_persistence`: no row lock / single transaction. |
| **`canonical_url = watchlist:{uuid}`** | Satisfies `0006` unique `(event_source, canonical_url)` per item. | Random URL per escalate: harder to idempotently re-escalate. |
| **Fixed UUID seeds in migration** | Stable IDs for tests/docs; idempotent re-apply. | `gen_random_uuid()` only: harder to reference in handover tests. |
| **Extend `editorial_digest.py` (S1d)** | One Sunday email with polls + watchlist + dedup. | Separate email per concern: operator email fatigue. |
| **`send_html` in `email_client`** | Digest sections are pre-rendered HTML fragments. | Force nested templates: awkward variable injection. |
| **No digest cron in S1e** | Out of acceptance criteria; function ready for manual/cron wiring. | GitHub Action in same story: scope creep. |

⚠️ **Do not implement auto-escalation** (IMD/SEBI RSS matching `escalation_trigger`) in Phase 3 without PO approval — explicit Phase 4 deferral.

⚠️ **Do not remove `ADMIN_EMAILS` gating** on `/api/editor/*` — watchlist data is editorial strategy, not public.

⚠️ **`event_source = 'watchlist'`** must remain distinct from ingest adapters so queue filters and metrics stay honest.

**Assumptions**

- Editors use existing `/admin/queue` to turn escalated drafts into cards (P1-S8 flow unchanged).
- `category` on watchlist rows uses same string values as `event_category` enum.
- Sunday digest recipient list will be wired when a scheduled job is added (not in S1e).

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S0** (`events`, migrations baseline); **P3-S1c** (`dedup_review_queue` for digest section). |
| **Parallel** | **P3-S1d** (NewsAPI polls in same `editorial_digest.html`). |
| **Downstream** | **P3-T2** data pipeline test gate; **P3-S1f** market facts (independent); editorial stories (checklist, regen) reuse `/editor/*` namespace later. |

**Shared components touched**

- `public.watchlist_items` (new)
- `public.events` (insert on escalate)
- `public.dedup_review_queue` (read-only in digest)
- `app/services/editorial_digest.py` (extended)
- `backend/email-templates/editorial_digest.html` (extended)
- `app/main.py` (router + `Cache-Control: no-store` for `/api/editor`)

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Thin API router** (`editor_watchlist.py`) + **service layer** (`watchlist.py`) over `psycopg` `connection()`.
- **Reuse `require_admin`** from `admin_metrics` for consistent PO auth.
- **Server component gate + client table** on frontend (same as `/admin/factor-db`).

**Database schema (summary)**

| Object | Change |
|--------|--------|
| `watchlist_items` | New table: description, category, review metadata, status, optional `escalated_event_id` FK → `events`. |
| `events` | No schema change; rows inserted on escalate. |

**API contracts**

| Method | Route | Auth | Purpose |
|--------|-------|------|---------|
| GET | `/api/editor/watchlist` | Bearer + `ADMIN_EMAILS` | List items (optional `?status=`). |
| PATCH | `/api/editor/watchlist/{id}` | Bearer + admin | Update `status`; sets `last_reviewed_at`. |
| POST | `/api/editor/watchlist/{id}/escalate` | Bearer + admin | Create draft event; mark escalated. |

**UI/UX**

- Single-page table: description, category, review frequency, status badge + dropdown, Escalate (disabled when already escalated).
- Link hint to `/admin/queue` after escalation.
- Footer note: digest includes ≤10 watchlist + ≤10 dedup items.

**Libraries / tools**

| Library | Purpose |
|---------|---------|
| shadcn `Table`, `Select`, `Button`, `Badge` | Watchlist UI |
| Existing `email_client.render_template` | Digest HTML |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0025_watchlist_items.sql` | `backend/db/migrations/0025_watchlist_items.sql` | Table, indexes, 5 seed rows |
| `watchlist.py` | `backend/app/services/watchlist.py` | List, patch, escalate (Postgres) |
| `editor_watchlist.py` | `backend/app/api/editor_watchlist.py` | FastAPI routes under `/api/editor` |
| `editor-admin.ts` | `frontend/lib/editor-admin.ts` | `ADMIN_EMAILS` normalisation for page gate |
| `page.tsx` | `frontend/app/(app)/editor/watchlist/page.tsx` | Server auth + allow-list |
| `WatchlistClient.tsx` | `frontend/app/(app)/editor/watchlist/WatchlistClient.tsx` | Client table + API calls |
| `test_watchlist_migration_sql.py` | `backend/tests/test_watchlist_migration_sql.py` | Static migration contract |
| `test_watchlist_escalate.py` | `backend/tests/test_watchlist_escalate.py` | Integration: escalate + seeds |
| `test_editor_watchlist_api.py` | `backend/tests/test_editor_watchlist_api.py` | API 403 + escalate response shape |
| `test_editorial_digest.py` | `backend/tests/test_editorial_digest.py` | Digest section caps + HTML render |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `migrate.py` | `backend/app/db/migrate.py` | Registered `0025_watchlist_items.sql` |
| `main.py` | `backend/app/main.py` | Included `editor_watchlist_router`; `no-store` for `/api/editor` |
| `editorial_digest.py` | `backend/app/services/editorial_digest.py` | Added watchlist + dedup HTML builders; `send_editorial_digest` |
| `editorial_digest.html` | `backend/email-templates/editorial_digest.html` | Watchlist + dedup sections + digest date |
| `email_client.py` | `backend/app/services/email_client.py` | Added `send_html()` for pre-rendered digest |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S1e AC + tasks **5.0**–**5.6** marked complete |

**Not modified (intentionally)**

| File | Note |
|------|------|
| `event_detection.py` | Watchlist is orthogonal to 4-hour ingest |
| `render.yaml` | No new cron for digest send |

---

### A8. TESTS EXECUTED

| Test file | Test function | Status | What it verifies |
|-----------|---------------|--------|------------------|
| `test_watchlist_migration_sql.py` | `test_watchlist_migration_creates_table` | **Pass** | DDL + status CHECK constraint |
| `test_watchlist_migration_sql.py` | `test_watchlist_migration_seeds_five_rows` | **Pass** | Five fixed seed UUIDs + `ON CONFLICT` |
| `test_watchlist_escalate.py` | `test_escalate_creates_event_with_watchlist_source` | **Pass** (integration) | Draft event `event_source=watchlist`, category preserved |
| `test_watchlist_escalate.py` | `test_migration_seeds_five_items` | **Pass** (integration) | `count(*) >= 5` in table |
| `test_watchlist_escalate.py` | `test_escalate_twice_returns_conflict_path` | **Pass** (integration) | Second escalate → `already_escalated` |
| `test_editorial_digest.py` | `test_digest_sections_include_counts` | **Pass** (integration) | Caps ≤10; watchlist URL present |
| `test_editorial_digest.py` | `test_render_editorial_digest_html_has_sections` | **Pass** | HTML contains watchlist + dedup headings |
| `test_editor_watchlist_api.py` | `test_watchlist_list_requires_admin_email` | **Pass** | Non-admin → 403 |
| `test_editor_watchlist_api.py` | `test_escalate_returns_event_id` | **Pass** | Mocked escalate returns `event_id` + `escalated` status |
| `test_newsapi_poll_digest.py` | `test_format_poll_summary_empty` | **Pass** | S1d regression: empty poll message |
| `test_newsapi_poll_digest.py` | `test_render_editorial_digest_includes_poll_row` | **Pass** | S1d regression: poll row in full template |

**Commands used**

```bash
python -m ruff check backend/app/services/watchlist.py backend/app/api/editor_watchlist.py backend/app/services/editorial_digest.py
python -m pytest backend/tests/test_watchlist_migration_sql.py backend/tests/test_watchlist_escalate.py backend/tests/test_editorial_digest.py backend/tests/test_editor_watchlist_api.py backend/tests/test_newsapi_poll_digest.py -q
cd frontend && pnpm lint && pnpm typecheck && pnpm test && pnpm build
```

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**`watchlist_items` (new in `0025`)**

| Column | Type | Notes |
|--------|------|--------|
| `id` | `uuid PK` | Seeds use fixed UUIDs |
| `event_description` | `text NOT NULL` | Becomes event `title` on escalate |
| `category` | `text NOT NULL` | Must match `event_category` enum values |
| `added_at` | `timestamptz` | Default `now()` |
| `review_frequency` | `text` | `daily` \| `weekly` \| `monthly` |
| `last_reviewed_at` | `timestamptz` | Set on patch / escalate |
| `escalation_trigger` | `text` | Display + digest only in Phase 3 |
| `status` | `text` | `watching` \| `escalated` \| `closed` |
| `escalated_event_id` | `uuid FK → events` | Nullable; `ON DELETE SET NULL` |

**Migration sequencing:** Apply after `0024_factor_poll_log.sql`. Registered in `backend/app/db/migrate.py` → run your project’s migration apply step (e.g. `python scripts/apply_migrations.py` if used locally).

**Seed data (5 rows)**

| ID suffix | Theme | Category |
|-----------|--------|----------|
| `...0001` | Maharashtra state election calendar | `india_specific` |
| `...0002` | SEBI consultation (F&O / algo) | `regulatory` |
| `...0003` | IMD monsoon outlook windows | `macro` |
| `...0004` | Union Budget 2026 cycle | `budget` |
| `...0005` | India–China trade / import restrictions | `geopolitical` |

**Verification SQL**

```sql
SELECT id, category, status, left(event_description, 60) AS desc
FROM public.watchlist_items
ORDER BY added_at;

SELECT id, title, event_source, lifecycle_state, category::text
FROM public.events
WHERE event_source = 'watchlist'
ORDER BY created_at DESC
LIMIT 5;
```

---

### B2. API / INTEGRATION CONTRACTS

**List watchlist**

```http
GET /api/editor/watchlist?status=watching&limit=100
Authorization: Bearer <supabase_jwt>
```

Response: `200` array of `WatchlistItem` objects.

**Patch status**

```http
PATCH /api/editor/watchlist/{item_id}
Content-Type: application/json

{ "status": "closed" }
```

**Escalate**

```http
POST /api/editor/watchlist/{item_id}/escalate
```

Response `200`:

```json
{
  "item": { "id": "...", "status": "escalated", "escalated_event_id": "...", ... },
  "event_id": "uuid-of-new-or-updated-event"
}
```

Errors: `403` (not admin), `404` (not found), `409` (`already_escalated` \| `watchlist_closed`), `503` (DB).

**Auth:** Supabase JWT via `get_current_user`; email must be in `ADMIN_EMAILS` or (fallback) `FACTOR_DB_ADMIN_EMAILS` per `require_admin` in `admin_metrics.py`.

**Cache:** `Cache-Control: no-store` on `/api/editor/*` (middleware in `main.py`).

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Escalate flow**

```text
BEGIN
  SELECT watchlist_items WHERE id = ? FOR UPDATE
  IF missing → watchlist_not_found
  IF status = escalated AND escalated_event_id set → already_escalated
  IF status = closed → watchlist_closed
  INSERT events (
    title = event_description,
    category,
    event_source = 'watchlist',
    canonical_url = source_url = 'watchlist:{id}',
    confidence_score = 55,
    lifecycle_state = 'draft',
    external_id = 'watchlist-{id}'
  )
  ON CONFLICT (event_source, canonical_url) DO UPDATE title, category
  UPDATE watchlist_items SET status='escalated', escalated_event_id, last_reviewed_at=now()
COMMIT
```

**Digest section builder**

```text
watchlist_lines = up to 10 items WHERE status = 'watching'
dedup_lines     = up to 10 rows FROM dedup_review_queue WHERE status = 'pending'
render editorial_digest.html with HTML fragments + newsapi_poll_summary (S1d)
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Detail |
|------|--------|
| **No scheduled digest** | `send_editorial_digest(to=...)` exists; no cron/GitHub Action wired. |
| **No CRUD API for new watchlist rows** | Only migration seeds + DB edits; no “Add item” UI. |
| **Escalate link goes to `/admin/queue`** | Does not deep-link to specific `event_id` yet. |
| **Digest uses `list_watchlist_items(status='watching')`** | Escalated items drop out of Sunday list (intended). |
| **Category as free text in DB** | Must stay aligned with `EventCategory` enum on escalate. |
| **Phase 4 auto-escalation** | `escalation_trigger` is not machine-evaluated. |

---

### B5. TESTING NOTES

| Type | Coverage |
|------|----------|
| **Automated — static** | `test_watchlist_migration_sql.py` (no DB) |
| **Automated — integration** | Escalate, seed count, digest caps (needs `SUPABASE_DB_URL`) |
| **Automated — API unit** | Admin 403, escalate response shape (mocked service) |
| **Automated — regression** | `test_newsapi_poll_digest.py` after digest template merge |
| **Automated — frontend** | `pnpm test` / build includes `/editor/watchlist` route |
| **Manual** | Apply `0025` → set `ADMIN_EMAILS` → sign in → escalate → verify `/admin/queue` |
| **Gap** | No Playwright e2e for watchlist page |
| **Gap** | No test for `send_editorial_digest` against live Resend/Postmark |
| **Gap** | No API test for `PATCH` status without integration DB |

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required | Notes |
|----------|----------|--------|
| `SUPABASE_DB_URL` | **Yes** (API + integration tests) | Postgres pool for watchlist service |
| `ADMIN_EMAILS` | **Yes** (editor UX) | Comma-separated PO emails; **same on Vercel + Render** |
| `FACTOR_DB_ADMIN_EMAILS` | Fallback | Used by `require_admin` only if `ADMIN_EMAILS` empty |
| `EMAIL_PROVIDER`, `EMAIL_API_KEY`, `EMAIL_FROM` | Optional | For sending digest |
| `APP_PUBLIC_URL` | Recommended | Correct `watchlist_url` in digest emails |

**No feature flags.**

**Deployment sequencing (per environment)**

1. Deploy backend with `watchlist.py`, `editor_watchlist.py`, digest changes.  
2. Deploy frontend with `/editor/watchlist`.  
3. Apply migration **`0025_watchlist_items.sql`**.  
4. Set **`ADMIN_EMAILS`** on API and frontend; redeploy both.  
5. Smoke: sign in → `/editor/watchlist` → Escalate one seed → confirm draft in `/admin/queue` with source `watchlist`.

Migrations are **not** run automatically on Render web service startup.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read PRD2 §4.3 (watchlist schema) and G-05 workshop notes (manual escalate only).  
2. Read `escalate_watchlist_item` in `watchlist.py` before changing event insert fields.  
3. If changing digest caps, update both `editorial_digest.py` and acceptance criteria in the plan.

**Common mistakes**

- Applying code without migration **`0025`** → API 503 / missing table.  
- **`ADMIN_EMAILS` only on frontend** → page loads but API returns 403.  
- Expecting **auto-escalation** from `escalation_trigger` text — not implemented.  
- Adding watchlist items only via UI — **no create endpoint**; use SQL or extend story.  
- Breaking **P3-S1d** digest tests when editing `editorial_digest.html` poll section.

**Where to look**

| Concern | Location |
|---------|----------|
| Watchlist DB logic | `backend/app/services/watchlist.py` |
| HTTP routes | `backend/app/api/editor_watchlist.py` |
| Admin auth | `backend/app/api/admin_metrics.py` → `require_admin` |
| Digest | `backend/app/services/editorial_digest.py`, `backend/email-templates/editorial_digest.html` |
| Frontend page | `frontend/app/(app)/editor/watchlist/` |
| Page allow-list | `frontend/lib/editor-admin.ts` |
| Migration | `backend/db/migrations/0025_watchlist_items.sql` |
| Plan / AC | `docs/plans/finnwise-phase3-implementation-tasks.md` § P3-S1e |

**Next stories**

- **P3-T2** — data pipeline test gate (watchlist + dedup in Sunday review).  
- **P3-S1f** — market facts freshness (parallel track).  
- **Phase 4** — optional RSS auto-escalation against `escalation_trigger`.

**Context owner (role):** Editorial platform / Phase 3 data-pipeline owner (Riley per plan); PO for seed content and `ADMIN_EMAILS` membership.

---

_End of document — P3-S1e v1.0_
