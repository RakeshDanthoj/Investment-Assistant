# Post Implementation Detailed Document — P1-S6

**Version:** v1.0 | **Date:** 17-05-2026  
**Story ID:** P1-S6 (Phase 1, Story 6)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`

---
Narrative style:

FinnWise Phase 1 needed a way to **pull candidate market events from the outside world** and park them as **draft rows** before anyone turns them into cards. We shipped exactly that: a Python job that runs on a schedule (and can be run by hand), three **feed-specific adapters** (NewsAPI, RBI RSS, NSE corporate announcements), and a **small editorial surface** so someone can see what was ingested and in what order of trust.

**What actually runs**

A single entrypoint, `python -m app.jobs.event_detection`, walks the adapters, turns each raw headline into a **category** and a **0–100 confidence score**, then **inserts** into Supabase’s `events` table with `lifecycle_state = draft`. If the same story shows up again (same adapter id + same canonical URL), Postgres rejects the duplicate and we count it as a **duplicate**, not a second row—that’s the idempotency story.

**NewsAPI** is special: we must not blow the **free-tier daily call limit**, so the database tracks usage per UTC day and a small RPC (`try_newsapi_call_budget`) decides whether we’re allowed one more call before we hit the HTTP client. The other two sources don’t use that budget.

**RBI** is a straight RSS parse with `feedparser`. **NSE** is best-effort: exchanges change shapes and sometimes block scrapers, so failures become an empty result for that run and a log line, not a crashed job.

**What people see**

There’s an API, `GET /admin/events`, and a Next.js page at **`/admin/queue`** with filter pills (category + source) and a table sorted by confidence. Phase 1 deliberately didn’t add auth to that path—same “internal tool, open in dev” posture as other foundation stories—so anyone wiring production should treat that as a **known gap** until you add an allow-list or proper RBAC.

**What changed in the repo**

You’ll find new pieces under `backend/app/sources/`, `backend/app/services/` (classification, scoring, Supabase REST helpers), `backend/app/jobs/`, migration `0006` for dedupe columns plus the NewsAPI quota table and RPC, tests for idempotency and mocked adapters, and the admin page under `frontend/app/admin/queue/`. We also added tiny **placeholder** cron modules for other Render jobs so deploys don’t import missing modules.

**Before you call it “done” in an environment**

Apply migration **0006**, set Supabase URL + **service role** key (server-only), optional `NEWSAPI_KEY`, and point the browser at the API with **`NEXT_PUBLIC_API_BASE_URL`**.

**If you remember one thing**

The editorial queue is only as good as **canonical URLs** and **adapter behaviour**: fiddle with normalisation or drop the unique index without a replacement plan, and you’ll either duplicate noise or block real inserts—so treat dedupe and quota as **first-class**, not polish.

--------------------------------------------


## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S6 |
| **Title** | Event-detection scheduled job + editorial queue |
| **Category** | **Full Stack** (PostgreSQL migration + RPC, FastAPI job + admin API, Next.js editorial UI, automated tests) |

**What this story aimed to achieve (plain language)**

The editorial pipeline needs a steady stream of candidate market events before they become Event Intelligence Cards. This story delivers: (1) a **scheduled Python job** (every four hours on Render, plus a **manual entrypoint**) that polls **NewsAPI**, an **RBI RSS** feed, and a **best-effort NSE** corporate-announcements source; (2) **typed source adapters** behind a common interface so new feeds add one class; (3) **persistence** into the existing `events` table as **draft** rows with a **0–100 confidence** score and **idempotent dedupe** on `(event_source, canonical_url)`; (4) a **daily NewsAPI call budget** so free-tier usage stays under the 100-calls/day guard (PRD §7.3); and (5) an internal **`/admin/queue`** page plus **`GET /admin/events`** API to triage drafts with **filters by category and source**, sorted **confidence descending**.

**How it fits into the overall application**

This story is the **ingestion edge** of the Phase 1 editorial loop: raw world signals enter as `events` in `lifecycle_state = draft`. Downstream, **P1-S7** (LLM card synthesis) and later editorial/signal stories consume this queue. It depends on **P1-S1** (deploy/runtime, secrets) and **P1-S4** (core `events` table and enums). It runs in parallel with factor/onboarding workstreams in the plan.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items (from the implementation plan) and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **6.1** | `SourceAdapter` abstract base in `app/sources/base.py`: `fetch(window: timedelta) -> list[RawEvent]`, `normalize_canonical_url()` (strips `utm_*` query params), `AdapterSource` enum (`newsapi`, `rbi_rss`, `nse_bse`), `SourceFailure` for non-fatal source outages. |
| **6.2** | `NewsAPISourceAdapter`: `GET https://newsapi.org/v2/everything` with India-oriented `q`; **before** each HTTP call, `reserve_news_api_call()` invokes Postgres RPC `try_newsapi_call_budget(p_max)` (default ceiling **95**) via PostgREST; if budget exhausted, adapter returns **no articles** (zero extra API calls). |
| **6.3** | `RBIRSSSourceAdapter`: downloads RBI press feed URL, parses with **feedparser**, maps entries to `RawEvent` with title, link-based canonical URL, optional excerpt. |
| **6.4** | `NSEAnnouncementsSourceAdapter`: warms NSE origin session, calls corporate-announcements JSON; on HTTP/JSON failure raises **`SourceFailure`** — job **logs and continues** (empty snapshot for that run; “last good” = no crash, other sources still run). |
| **6.5** | `event_confidence.score(source, raw)` combines **source tier prior** (RBI highest, NSE middle, NewsAPI lowest) plus **keyword bump** (capped) and tiny hash jitter; result clamped **0–100**. |
| **6.6** | `event_classification.infer_event_category` maps text + adapter to `event_category` enum. `event_persistence.persist_draft_event` **POST**s to Supabase PostgREST; unique index on `(event_source, canonical_url)` → duplicate insert treated as **`duplicate`** (no duplicate row). |
| **6.7** | `python -m app.jobs.event_detection` is the cron command; structured logging on completion (`inserted`, `duplicates`, `errors`, `skipped_config`, `source_failures`). Render `render.yaml` already defines **`0 */4 * * *`** for this module. |
| **6.8** | FastAPI **`GET /admin/events`** (`admin_queue` router); Next.js **`/admin/queue`** client page: table, filter pills for **category** and **event_source**, default **draft**, server-sorted confidence via API query params. |
| **6.9** | Pytest: **idempotency** (custom `FrozenAdapter` + in-memory persist mock — second run yields only duplicates); **per-source** tests with mocked `httpx` / client for RBI, NewsAPI, NSE shapes. |

**Functional breakdown**

- **Job orchestration:** `run_event_detection` iterates default adapters (RBI → NewsAPI → NSE order in `default_adapters`), scores each `RawEvent`, infers category, persists via REST.
- **Dedupe:** Application relies on **database uniqueness**, not client-side sets; re-run with same canonical URLs yields PostgREST **409** / duplicate detection path → counted as **`duplicate`**.
- **NewsAPI quota:** Table `news_api_daily_usage` plus **`try_newsapi_call_budget`** implements **atomic** check-and-increment per **UTC calendar day** inside the RPC (row-level logic in migration).

**Edge cases, validations, and error handling**

- **Missing Supabase URL / service role key:** persist returns `skipped_no_config`; job tallies `skipped_config`.
- **NewsAPI key absent:** `NewsAPISourceAdapter` returns empty list (no external call).
- **RBI / NSE total failure:** `SourceFailure` or empty parse → logged `event_detection.adapter_failed`, other adapters unaffected.
- **PostgREST insert conflict:** treated as **`duplicate`**, not error.
- **Generic HTTP errors on insert:** logged and counted as **`errors`**.

**Business rules enforced**

- Every stored event has **`lifecycle_state = draft`** on insert from the job.
- **Confidence** is heuristic only (pre-LLM triage), not an investment recommendation.
- **Phase 1:** Editorial queue API and page are **not authenticated** (open access aligns with plan’s Phase 1 posture for internal tools unless Product Owner adds allow-list later).
- ⚠️ **Amounts and PII** are not part of this story; events are **headline / URL / taxonomy** only.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **PostgREST for writes** (not raw `psycopg` in the job) | Matches existing pattern (`session_profile_store`); cron env on Render already has **service role**; avoids shipping `SUPABASE_DB_URL` on cron if only REST keys are available. | Direct SQL from job: requires DB URL on every worker. |
| **`canonical_url` column + unique `(event_source, canonical_url)`** | Stable dedupe key distinct from optional display `source_url`; supports synthetic NSE keys. | Hash-only column: harder to debug in admin UI. |
| **RPC `try_newsapi_call_budget` with `SECURITY DEFINER`** | Atomic daily counter; avoids race on parallel crons. | App-only read-modify-write: race risk under concurrent crons. |
| **`GRANT EXECUTE … TO service_role` only** | Prevents anonymous clients from burning NewsAPI budget via public PostgREST. | Grant to `anon`: **security risk**. |
| **`app/sources/__init__.py` exports only base types** | Avoids import side-effects loading all adapters when importing `base`. | Eager re-exports: slower tests / circular import risk. |
| **Placeholder jobs** `signal_monitor`, `weekly_bias_report` | `render.yaml` referenced them pre-story; stubs prevent cron boot failures until P1-S11 / future slices. | Removing cron entries: would diverge from infra-as-code expectations. |
| **NSE adapter raises `SourceFailure` on hard errors** | PRD §7.3 “fallback” interpreted as **degrade gracefully** (skip bad source) rather than crash entire run. | Retry storm against NSE: could trigger blocking. |

**Assumptions**

- NSE public JSON shape may change; `_unwrap_announcement_rows` is defensive but not guaranteed forever.
- RBI RSS URL remains discoverable; feed moves would require adapter config update.

**⚠️ Critical — do not reverse lightly**

- **Do not** grant `try_newsapi_call_budget` to **`anon`** or expose budget RPC publicly without rate limits.
- **Do not** drop unique index **`events_source_canonical_uidx`** without replacing dedupe strategy — duplicate events will flood editorial queue and downstream P1-S7.

---

### A4. APPLICATION LINKAGE SUMMARY

| Linkage | Detail |
|---------|--------|
| **Depends on** | **P1-S1** — FastAPI app, `.env.local`, Render cron wiring; **P1-S4** — `events` table, `event_category`, `lifecycle_state` enums. |
| **Enables** | **P1-S7** — LLM card synthesis needs draft `events`; **P1-S11** — signal monitoring references events/cards (job placeholder exists). |
| **Parallel with** | **P1-S5** (Factor DB), **P1-S2** (onboarding) per plan — no runtime coupling. |
| **Shared artefacts** | `EventRecord` schema (`canonical_url`, `event_source`); Supabase service role; `render.yaml` cron services. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Adapter pattern per external source; single orchestrator job; service modules for classification, confidence, persistence. |
| **Database** | Migration `0006_events_dedupe_newsapi_quota.sql`: new columns, unique index, `news_api_daily_usage`, RPC `try_newsapi_call_budget(smallint)`. |
| **API** | `GET /admin/events` — query params: `lifecycle_state` (default `draft`), optional `category`, `event_source`, `limit`; response: list of `EventRecord` JSON. **No auth** in Phase 1. |
| **UI/UX** | `/admin/queue`: pill filters, sort by confidence via API, SEBI-style disclaimer footer (editorial-only, not advice). |
| **Libraries** | **feedparser** — RSS; **httpx** — HTTP (existing). |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0006_events_dedupe_newsapi_quota.sql` | `backend/db/migrations/` | Dedupe columns, quota table, unique index, NewsAPI budget RPC + grants |
| `base.py` | `backend/app/sources/` | `SourceAdapter`, `RawEvent`, `AdapterSource`, URL normalisation, `SourceFailure` |
| `newsapi.py` | `backend/app/sources/` | NewsAPI adapter + quota reservation before HTTP |
| `rbi_rss.py` | `backend/app/sources/` | RBI RSS adapter |
| `nse_announcements.py` | `backend/app/sources/` | NSE corporate announcements adapter |
| `__init__.py` | `backend/app/sources/` | Lightweight package exports (base symbols only) |
| `news_api_budget.py` | `backend/app/services/` | Calls `try_newsapi_call_budget` via PostgREST |
| `event_confidence.py` | `backend/app/services/` | Heuristic `score()` |
| `event_classification.py` | `backend/app/services/` | `infer_event_category()` |
| `event_persistence.py` | `backend/app/services/` | `persist_draft_event`, `fetch_events_filtered` |
| `event_detection.py` | `backend/app/jobs/` | Main job module + `run_event_detection` |
| `__init__.py` | `backend/app/jobs/` | Jobs package marker |
| `signal_monitor.py` | `backend/app/jobs/` | Render cron placeholder (P1-S11) |
| `weekly_bias_report.py` | `backend/app/jobs/` | Render cron placeholder |
| `admin_queue.py` | `backend/app/api/` | `GET /admin/events` |
| `test_event_detection_idempotent.py` | `backend/tests/` | Idempotent persist behaviour |
| `test_source_adapters.py` | `backend/tests/` | Mocked adapter unit tests |
| `page.tsx` | `frontend/app/admin/queue/` | Editorial draft queue UI |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `migrate.py` | `backend/app/db/` | Appended `0006_events_dedupe_newsapi_quota.sql` to `MIGRATION_FILES` |
| `schemas.py` | `backend/app/models/` | `EventRecord` extended with `canonical_url`, `event_source` |
| `main.py` | `backend/app/main.py` | Registered `admin_router` at prefix `/admin` |
| `pyproject.toml` | `backend/` | Added runtime dependency `feedparser>=6.0.11` |
| `finnwise-phase1-implementation-tasks.md` | `docs/plans/` | P1-S6 acceptance criteria and tasks 6.0–6.9 marked complete |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

| Object | Detail |
|--------|--------|
| **`events.event_source`** | `text NOT NULL` — adapter id (`newsapi`, `rbi_rss`, `nse_bse` or legacy backfill). |
| **`events.canonical_url`** | `text NOT NULL` — dedupe key; backfilled from `source_url` where possible, else synthetic `legacy:no-url:<uuid>`. |
| **Unique index** | `events_source_canonical_uidx` on `(event_source, canonical_url)`. |
| **`news_api_daily_usage`** | `(usage_date date PK, api_call_count smallint)` — UTC-day counter. |
| **`try_newsapi_call_budget(p_max smallint)`** | Inserts first row or increments if below `p_max`; returns boolean via PostgREST RPC. |
| **Sequence** | Apply **`0006`** after existing migrations (`0003`–`0005`) via `apply_migrations`. |

---

### B2. API / INTEGRATION CONTRACTS

| Method | Route | Purpose |
|--------|-------|---------|
| `GET` | `/admin/events` | List events with filters; backend sorts by `confidence_score` descending when requested via PostgREST `order`. |

**Query parameters**

| Param | Example | Notes |
|-------|---------|-------|
| `lifecycle_state` | `draft` | Default in client; pass `null`/omit behaviour depends on client — API accepts optional filter. |
| `category` | `rbi_policy` | Must match `event_category` enum value. |
| `event_source` | `rbi_rss` | Exact adapter id string. |
| `limit` | `200` | Capped in route (e.g. 1–500). |

**Response:** JSON array of `EventRecord`-shaped objects (`id`, `title`, `category`, `source_url`, `canonical_url`, `event_source`, `confidence_score`, `lifecycle_state`, `prompt_version`, `created_at`).

**External integrations**

| System | Usage |
|--------|--------|
| **NewsAPI** | `v2/everything`, API key header |
| **RBI** | RSS XML over HTTPS |
| **NSE** | JSON corporate announcements (best-effort) |
| **Supabase PostgREST** | `POST /rest/v1/events`, `GET /rest/v1/events`, `POST /rest/v1/rpc/try_newsapi_call_budget` |

---

### B3. BUSINESS LOGIC & RULES (Detailed)

1. **Window:** Default ingest window **`timedelta(hours=4)`** in `run_event_detection` (cron-aligned).
2. **Confidence:** `score()` = tier prior + capped keyword score + small URL hash jitter → **0–100**.
3. **Category:** RBI RSS → typically `rbi_policy`; NSE → `india_specific`; NewsAPI → keyword routing to macro / RBI / regulatory / budget / geopolitical / india-specific / default macro.
4. **Dedupe:** Uniqueness on `(event_source, canonical_url)`; second insert is **duplicate**, not a new row.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|-------|
| **NSE fragility** | Exchange may require cookies, change JSON shape, or block datacenter IPs — adapter may return **zero rows** after `SourceFailure`. |
| **BSE** | Story title mentions BSE; implementation ships **NSE-shaped** adapter as `nse_bse` source id — true BSE feed can be a **second adapter class** later. |
| **Admin auth** | No RBAC on `/admin/events` or `/admin/queue` — align with Product Owner before external testers. |
| **Service role on cron** | PostgREST writes use **service role** — ⚠️ never expose that key to browsers. |

---

### B5. TESTING NOTES

| Type | Coverage |
|------|----------|
| **Automated** | `test_event_detection_idempotent.py` — duplicate detection via mock persist; `test_source_adapters.py` — RSS/News/NSE parsing with mocks. Full backend suite **37 tests** passing at time of documentation. |
| **Manual** | Run `python -m app.jobs.event_detection` with valid `.env.local` and applied migration; open `/admin/queue` with `NEXT_PUBLIC_API_BASE_URL` pointing at API. |
| **Gaps** | No live integration test against Supabase/NewsAPI in CI (would need secrets); NSE success path is environment-dependent. |

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| `SUPABASE_URL` | PostgREST base (normalised if project ref). |
| `SUPABASE_SERVICE_ROLE_KEY` | Inserts + RPC + admin list (server-side only). |
| `NEWSAPI_KEY` | NewsAPI adapter (optional — adapter no-ops if empty). |
| `NEXT_PUBLIC_API_BASE_URL` | Browser → FastAPI origin for `/admin/queue`. |
| `SUPABASE_DB_URL` | Not required for job persist path; **required** to run `apply_migrations` from repo tooling. |

**Deployment:** Render cron service `finnwise-event-detection` should include same secrets as web service for Supabase + NewsAPI. Apply **`0006`** migration **before** relying on dedupe + quota in production.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

1. **Start here:** `backend/app/jobs/event_detection.py` → `run_event_detection` → `default_adapters` → `persist_draft_event`.
2. **Add a source:** New file under `backend/app/sources/`, subclass `SourceAdapter`, set `adapter_source` (may need new enum value + migration if not reusing existing ids), register in `default_adapters`.
3. **Debugging duplicates:** Check `events.event_source` + `canonical_url` pair; verify URL normalisation in `normalize_canonical_url`.
4. **NewsAPI budget:** Inspect `news_api_daily_usage` and RPC definition in `0006`; tune `p_max` in `news_api_budget.py` (default **95**).
5. **Frontend CORS:** Backend `CORSMiddleware` must allow the Next.js origin (localhost + Vercel regex already in `main.py`).
6. **Product / compliance:** For disclaimer and SEBI copy changes, coordinate with **Product Owner / Compliance** — do not weaken mandatory disclosures on public surfaces.

---

_End of document._
