# Post Implementation Detailed Document — P3-S1d

**Version:** v1.0 | **Date:** 30-05-2026  
**Story ID:** P3-S1d (Phase 3, Story 1d)  
**PRD2 gap:** G-04  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **4.0**–**4.6**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §4.2, `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` G-04 / WS-1

---

## Narrative style (read this first)

Phase 1’s NewsAPI adapter used one broad India-market query and a **global** daily cap (`try_newsapi_call_budget` via PostgREST), but PRD2 never mapped calls to the **eight Factor DB macro factors** — so ingest was either noisy or missed factor-specific signal. **P3-S1d** fixes that: keyword sets and per-factor daily budgets live in `newsapi_keywords.yaml` (editable without deploy), and each **4-hour event-detection cron tick** polls **exactly one factor** in round-robin order, respecting both the **100 calls/day global cap** and each factor’s allocated budget (15+15+20+10×5 = 100).

Every completed poll writes a row to `factor_poll_log` (`status`: `ok` | `empty` | `error`, plus `article_count`). Structured logs emit `newsapi.poll_status` with factor slug and RSS-fallback flag. On **HTTP 429**, the adapter does **not** burn another NewsAPI call; it falls back to **ET Markets** and **Mint** RSS feeds (PRD2 §4.4). Poll outcomes are surfaced in the **Sunday editorial digest** HTML template as an operational table (log-only, not user-facing product copy).

During handover smoke-testing, a **budget RPC response-parsing bug** was found: Supabase PostgREST returns a bare JSON boolean (`true`/`false`), but the legacy client only accepted a wrapped object — successful reservations were misread as “exhausted,” so no NewsAPI GET and no `factor_poll_log` rows. That is fixed in `parse_newsapi_budget_rpc_response()` in `news_api_budget.py`.

**Tests executed and passed (P3-S1d–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Scheduler + adapter behaviour | `python -m pytest backend/tests/test_newsapi_scheduler.py -q` | **12 passed** |
| Budget RPC parsing | `python -m pytest backend/tests/test_news_api_budget.py -q` | **4 passed** |
| Poll digest template | `python -m pytest backend/tests/test_newsapi_poll_digest.py -q` | **2 passed** |
| Migration SQL contract | `python -m pytest backend/tests/test_factor_poll_log_migration_sql.py -q` | **1 passed** |
| Adapter URL normalisation (updated mocks) | `python -m pytest backend/tests/test_source_adapters.py::test_newsapi_adapter_normalizes_tracking_params -q` | **1 passed** |
| Editorial digest (unit; S1e sections mocked) | `python -m pytest backend/tests/test_editorial_digest.py -m "not integration" -q` | **1 passed** |
| **Combined P3-S1d slice (unit)** | `python -m pytest backend/tests/test_newsapi_scheduler.py backend/tests/test_news_api_budget.py backend/tests/test_newsapi_poll_digest.py backend/tests/test_factor_poll_log_migration_sql.py backend/tests/test_source_adapters.py backend/tests/test_editorial_digest.py -m "not integration" -q` | **19 passed**, 1 deselected (integration) |
| Lint (touched modules) | `python -m ruff check backend` | **All checks passed** (full backend) |

**Three anchors for handover:** (1) **Apply migration `0024` once per environment** before expecting `factor_poll_log` rows; (2) **Ensure `public.factors` has 8 seed rows** (banking sector seed) or poll writes log `factor_poll_log.unknown_factor` and skip insert; (3) **Successful budget reservation must show `GET newsapi.org` in cron logs** — if you only see `global_budget_exhausted` with no GET, check RPC parsing and today’s `news_api_daily_usage` count (see B7).

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S1d |
| **Title** | NewsAPI factor keyword scheduler |
| **Category** | **Backend** (config YAML, services, source adapter, DB migration, email template fragment; no new REST routes) |
| **Points / owner (plan)** | 3 · Sam |
| **Depends on** | P3-S0 (Phase 3 baseline); Factor DB `public.factors` from P1-S5 / `0007` + seeds |
| **Parallel with** | P3-S1c (dedup), P3-S1e (watchlist) |
| **Blocks** | P3-T2 (data pipeline test gate), P3-S1f (market facts freshness — pipeline ordering) |

**What this story aimed to achieve (plain language)**

NewsAPI’s free tier allows **100 HTTP calls per UTC day**. This story splits those calls across the **eight macro factors** (crude oil, dollar–rupee, domestic rates, global risk, monsoon, government capex, GST, regulatory environment) using PRD2 keyword sets, rotates **one factor per cron run**, records every poll for Sunday editorial review, and falls back to Indian market RSS when NewsAPI rate-limits.

**How it fits into the overall application**

- **Upstream:** P1-S6 event-detection cron and `0006` global quota RPC; P1-S5 eight `factors` rows; P3-S0 schema baseline.
- **This story:** Targeted ingest signal aligned with Factor DB; audit trail for ops; digest visibility.
- **Downstream:** P3-T2 integration gate (rotation + cap); P3-S1g confidence scorer benefits from cleaner, factor-oriented headlines; editorial Sunday digest (with P3-S1e watchlist/dedup sections).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **4.1** | `backend/app/config/newsapi_keywords.yaml` — 8 factors, keywords, `daily_calls` summing to 100. |
| **4.2** | `newsapi_scheduler.py` + adapter: round-robin next factor with remaining per-factor budget. |
| **4.3** | Migration `0024_factor_poll_log.sql` + `factor_poll_log.py` insert on each poll. |
| **4.4** | Classify `ok` / `empty` / `error`; 429 → `news_rss_fallback.py` (ET Markets, Mint). |
| **4.5** | `format_newsapi_poll_summary_html()` + `editorial_digest.html` section. |
| **4.6** | Unit tests: cap, rotation, status classification, RPC parse, template render. |

**Functional breakdown**

1. `python -m app.jobs.event_detection` runs adapters in order: RBI RSS → **NewsAPI** → NSE (unchanged order).
2. `NewsAPISourceAdapter.fetch()`:
   - No-op if `NEWSAPI_KEY` empty.
   - Load YAML config; resolve next factor slug from last `factor_poll_log` row + today’s per-factor counts.
   - If no factor has budget left → return `[]` (log `newsapi.scheduler.all_budgets_exhausted`).
   - Call `reserve_news_api_call(ceiling=100)` (PostgREST RPC) → if false, return `[]` (log `global_budget_exhausted`).
   - Build `q` from factor keywords (`OR`-joined; phrases quoted).
   - `GET https://newsapi.org/v2/everything` with `from=<window start date>`, `pageSize=45`, `language=en`.
   - Map HTTP outcome to `poll_status`; on **429**, RSS fallback with keyword filter on title/summary.
   - `record_factor_poll(factor_slug, status, article_count)` via **direct Postgres** (`SUPABASE_DB_URL`).
   - Return `list[RawEvent]` for existing dedup persist path (P3-S1c).
3. Global quota increments **only** when RPC returns true (same as P1-S6).

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| `NEWSAPI_KEY` missing | Adapter returns `[]`; no budget RPC; no poll log. |
| Global budget exhausted (`api_call_count >= p_max`) | RPC returns `false`; no HTTP call; **no** poll log row. |
| All per-factor budgets exhausted for UTC day | `resolve_next_factor` → `None`; no RPC; no poll log. |
| NewsAPI **200**, zero articles | `status = empty`, `article_count = 0`, row logged. |
| NewsAPI **401/4xx** (except 429) | `status = error`, logged, no RSS. |
| NewsAPI **429** | RSS fallback; `ok` if articles found else `empty`; `used_rss_fallback` in logs. |
| NewsAPI **5xx** / network error | `status = error`. |
| Unknown factor slug (no DB row) | `record_factor_poll` warns `unknown_factor`; no insert. |
| `SUPABASE_DB_URL` missing / DB error | `factor_poll_log.write_failed` logged; ingest may still return articles. |
| RPC body bare `true`/`false` | Parsed correctly after P3-S1d handover fix (see A3). |

**Business rules enforced**

- **PRD2 §4.2:** Per-factor `daily_calls` total **exactly 100**; validated at YAML load time.
- **One factor per cron tick** (round-robin), not all eight per run.
- **Poll audit:** `factor_poll_log.status` ∈ `ok`, `empty`, `error`.
- **Fallback chain (market news):** NewsAPI → RSS (ET Markets, Mint) on 429 only in Phase 3 scope.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Keep `backend/app/sources/newsapi.py`** (not separate `newsapi_adapter.py`) | Matches existing P1 layout; plan filename was illustrative. | New adapter module: duplicate `SourceAdapter` wiring. |
| **Round-robin pointer from `factor_poll_log`** | No new state table; survives restarts. | In-memory index: lost on restart. |
| **Per-factor budget = count of poll rows today** | Simple; aligns “one call = one log row”. | Separate counter table per factor: more schema. |
| **Global cap still via `0006` RPC** | Atomic increment; proven in P1-S6. | App-only counter: race under parallel crons. |
| **RSS only on 429** | PRD2 fallback for rate limit, not “zero results”. | RSS on empty NewsAPI: conflates “no news” with outage. |
| **Poll log via `SUPABASE_DB_URL`** | Same pattern as P3-S1c dedup; transactional insert. | PostgREST insert: no factor FK convenience. |
| **Digest: HTML table in template** | Task 4.5 “log-only fields”; reuses P2-S10 `render_template`. | New admin page for polls: out of scope. |
| **`DEFAULT_NEWSAPI_DAILY_MAX = 100`** | Aligns with PRD2 factor budget sum (was 95). | Keep 95: drift from PRD2. |
| **`parse_newsapi_budget_rpc_response`** | Supabase returns bare boolean; legacy parser always false. | Require wrapped JSON only: breaks production RPC. |

⚠️ **Do not remove per-factor budgets from YAML without rebalancing to 100** — `load_newsapi_config()` raises if sum ≠ `max_daily_calls`.

⚠️ **Do not log a poll row when `reserve_news_api_call` fails** — no NewsAPI attempt occurred; empty `factor_poll_log` with `global_budget_exhausted` in logs means budget/RPC issue, not “no news”.

⚠️ **Do not assume `factor_poll_log` is protected by the same code path as budget** — budget uses **PostgREST** (`SUPABASE_URL` + service role); poll log uses **`SUPABASE_DB_URL`**.

**Assumptions**

- Event-detection cron remains **4-hourly** (~6 ticks/day → ~16 calls/factor/day average over 8 factors).
- Factor slugs in YAML match `public.factors.slug` from banking seed (`crude_oil`, `dollar_rupee`, …).
- Editorial digest **send** job is optional; template/variables exist for future Sunday cron.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / artefacts |
|-----------|---------------------|
| **Upstream** | P3-S0 migrations; P1-S5 `factors` table; P1-S6 `0006` quota + `event_detection` job; P3-S1c dedup persist on ingest |
| **This story** | Factor-targeted NewsAPI + `factor_poll_log` + digest poll table |
| **Downstream** | **P3-T2** — mock rotation + cap tests; **P3-S1f** — freshness gates on facts; **P3-S1g** — confidence inputs; **P3-S1e** — shared `editorial_digest.html` |
| **Shared touchpoints** | `NewsAPISourceAdapter`, `news_api_daily_usage`, `try_newsapi_call_budget`, `run_event_detection`, `editorial_digest.py` |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Config** | YAML in `app/config/`; `@lru_cache` load with validation (8 factors, budget sum). |
| **Scheduler** | Pure functions `pick_next_factor_slug` / `resolve_next_factor` (testable without DB). |
| **Adapter** | `NewsApiPollResult` dataclass on adapter instance (`last_poll`) for tests/digest. |
| **Database** | `factor_poll_log` FK → `factors(id)`; RLS enabled, no policies (service role / postgres only). |
| **API** | No new HTTP routes. |
| **UI** | None. |
| **Email** | `editorial_digest.html` — `{{ newsapi_poll_summary }}` plus S1e watchlist/dedup placeholders. |
| **Libraries** | Existing `httpx`, `feedparser`, `pyyaml`. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `newsapi_keywords.yaml` | `backend/app/config/newsapi_keywords.yaml` | Factor keyword sets + daily call budgets |
| `newsapi_config.py` | `backend/app/services/newsapi_config.py` | Load/validate YAML; build NewsAPI `q` string |
| `newsapi_scheduler.py` | `backend/app/services/newsapi_scheduler.py` | Round-robin factor selection |
| `factor_poll_log.py` | `backend/app/services/factor_poll_log.py` | Insert/query poll audit rows |
| `news_rss_fallback.py` | `backend/app/sources/news_rss_fallback.py` | ET Markets + Mint RSS on 429 |
| `0024_factor_poll_log.sql` | `backend/db/migrations/0024_factor_poll_log.sql` | Poll audit table + indexes |
| `editorial_digest.html` | `backend/email-templates/editorial_digest.html` | Sunday digest (watchlist, dedup, NewsAPI polls) |
| `test_newsapi_scheduler.py` | `backend/tests/test_newsapi_scheduler.py` | Rotation, cap, status classification |
| `test_news_api_budget.py` | `backend/tests/test_news_api_budget.py` | RPC body parsing + reserve |
| `test_newsapi_poll_digest.py` | `backend/tests/test_newsapi_poll_digest.py` | Digest HTML includes poll rows |
| `test_factor_poll_log_migration_sql.py` | `backend/tests/test_factor_poll_log_migration_sql.py` | Static migration contract |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `newsapi.py` | `backend/app/sources/newsapi.py` | Full rewrite: scheduler, poll log, 429 RSS, status logging |
| `news_api_budget.py` | `backend/app/services/news_api_budget.py` | `parse_newsapi_budget_rpc_response`; ceiling 100 |
| `editorial_digest.py` | `backend/app/services/editorial_digest.py` | `format_newsapi_poll_summary_html` (integrated with S1e digest builder) |
| `migrate.py` | `backend/app/db/migrate.py` | Register `0024_factor_poll_log.sql` |
| `test_source_adapters.py` | `backend/tests/test_source_adapters.py` | Mock scheduler/budget for NewsAPI unit test |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S1d AC and tasks marked complete |

---

### A8. TESTS EXECUTED

| Test module | What it verifies | Status |
|-------------|------------------|--------|
| `test_newsapi_scheduler.py` | YAML sums to 100; rotation order; skip exhausted factor; full 9-tick rotation obeys budgets; `ok`/`empty`/`error`/429+RSS; adapter logs poll; global budget skip | **12 passed** |
| `test_news_api_budget.py` | Parse bare `true`, `false`, wrapped object; `reserve_news_api_call` with mocked HTTP | **4 passed** |
| `test_newsapi_poll_digest.py` | Empty poll HTML; full digest render with mocked poll row | **2 passed** |
| `test_factor_poll_log_migration_sql.py` | Table, FK, status check, `article_count` | **1 passed** |
| `test_source_adapters.py` | NewsAPI UTM stripping still works with scheduler mocks | **1 passed** (NewsAPI test) |
| `test_editorial_digest.py` | Digest sections cap (integration, DB); unit render with mocked sections | **1 passed** unit; integration deselected without DB in slice |

**Not automated in CI for S1d alone:** Live NewsAPI HTTP, live RSS fetch, live Supabase RPC against production project (manual smoke).

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Table: `public.factor_poll_log`**

| Column | Type | Notes |
|--------|------|--------|
| `id` | `uuid` PK | `gen_random_uuid()` |
| `factor_id` | `uuid` FK → `factors(id)` | RESTRICT on delete |
| `polled_at` | `timestamptz` | Default `now()` |
| `status` | `text` | CHECK: `ok`, `empty`, `error` |
| `article_count` | `smallint` | ≥ 0 |

**Indexes:** `polled_at DESC`; `(factor_id, polled_at DESC)`.

**Migration sequencing:** Apply **`0024`** after `0023` (dedup). Registered in `app/db/migrate.py` / `scripts/apply_migrations.py`.

**Existing table used:** `news_api_daily_usage` (`0006`) — global daily counter unchanged.

**Seed data:** None in `0024`; requires existing eight `factors` rows from banking seed.

---

### B2. API / INTEGRATION CONTRACTS

**No new REST endpoints.**

**External integrations**

| Integration | Method | Purpose |
|-------------|--------|---------|
| NewsAPI | `GET /v2/everything` | Headlines per factor query |
| Supabase PostgREST | `POST /rest/v1/rpc/try_newsapi_call_budget` | Global daily budget |
| ET Markets RSS | `GET` feed URL in `news_rss_fallback.py` | 429 fallback |
| Mint markets RSS | `GET` feed URL in `news_rss_fallback.py` | 429 fallback |

**PostgREST RPC payload**

```json
{ "p_max": 100 }
```

**Response (Supabase):** bare JSON boolean `true` or `false` (must use `parse_newsapi_budget_rpc_response`).

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Round-robin selection (per tick)**

```
last_slug ← latest factor_poll_log.slug (or null)
for each factor in order starting after last_slug:
  if count_today[factor] < daily_budget[factor]:
    return factor
return null  // all per-factor budgets exhausted
```

**Poll status decision tree**

```
reserve_news_api_call() == false → stop (no log)
HTTP 429 → RSS fallback → articles? ok : empty
HTTP >= 500 or network → error
HTTP >= 400 (not 429) → error
HTTP 200, articles > 0 → ok
HTTP 200, zero articles → empty
```

**Keyword query example (`crude_oil`):**

`"crude oil" OR brent OR WTI OR OPEC OR "oil price India" OR petroleum OR "ATF price" OR ONGC OR "oil ministry"`

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Detail |
|------|--------|
| **One HTTP call per cron tick** | Even if a factor’s budget is 15/day, only one call is made per 4h run; full budget unused if cron stops. |
| **RSS fallback scope** | Only on **429**, not on 401/403 or empty results. |
| **NSE / RBI failures** | Unchanged from P1; unrelated to S1d. |
| **Pool shutdown warnings** | `event_detection` exits without closing psycopg pool — noisy on CLI, harmless on Render. |
| **No GNews fallback** | PRD2 lists GNews as tier-2; not implemented in Phase 3. |
| **Digest send not scheduled** | Template + `send_editorial_digest()` exist with S1e; no new Render cron in S1d. |
| **Per-factor budget vs global** | Theoretically global cap could block before per-factor budgets spent — by design (shared 100). |

---

### B5. TESTING NOTES

| Type | Coverage |
|------|----------|
| **Unit** | Scheduler math, config validation, RPC parse, adapter mocks, digest HTML |
| **Integration** | `test_editorial_digest.py` (DB + migrations) when `SUPABASE_DB_URL` set |
| **Manual smoke** | `python -m app.jobs.event_detection` → expect `GET newsapi.org` + `newsapi.poll_status`; SQL on `factor_poll_log` |

**Manual verification SQL**

```sql
SELECT usage_date, api_call_count FROM public.news_api_daily_usage
ORDER BY usage_date DESC LIMIT 2;

SELECT f.slug, p.status, p.article_count, p.polled_at
FROM public.factor_poll_log p
JOIN public.factors f ON f.id = p.factor_id
ORDER BY p.polled_at DESC LIMIT 8;
```

**Known gap:** No CI test hits live NewsAPI or live RSS (would need secrets + flaky network).

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required for | Notes |
|----------|----------------|-------|
| `NEWSAPI_KEY` | NewsAPI HTTP | Empty → adapter no-op |
| `SUPABASE_URL` | Budget RPC | Full URL, normalized |
| `SUPABASE_SERVICE_ROLE_KEY` | Budget RPC | Not granted to `anon` |
| `SUPABASE_DB_URL` | `factor_poll_log` writes | Session pooler URI on Render |

**Deploy sequencing**

1. Apply migration **`0024`**.
2. Confirm **`public.factors`** count = 8.
3. Deploy backend + event-detection cron with same env as API.
4. Optional: run one manual `event_detection` and verify `factor_poll_log`.

**Config file:** Edit `newsapi_keywords.yaml` and redeploy backend image (no migration).

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing this code**

1. Read PRD2 §4.2 factor table — budgets must sum to **100**.
2. Trace `NewsAPISourceAdapter.fetch()` end-to-end: scheduler → budget RPC → HTTP → `record_factor_poll`.
3. Distinguish **`global_budget_exhausted`** (RPC false / parse failure) from **`all_budgets_exhausted`** (per-factor caps).

**Common mistakes**

| Mistake | Symptom |
|---------|---------|
| Expecting poll rows when budget RPC fails | Empty `factor_poll_log`; log shows `global_budget_exhausted` |
| Missing `SUPABASE_DB_URL` | `factor_poll_log.write_failed` in logs; articles may still ingest |
| Missing factor seeds | `factor_poll_log.unknown_factor` |
| Invalid `NEWSAPI_KEY` | `status = error`, `article_count = 0`, but row **is** logged |
| Querying poll log without join | Use `factor_id` FK, not slug column on log table |

**Where to look**

| Concern | Path |
|---------|------|
| Keywords / budgets | `backend/app/config/newsapi_keywords.yaml` |
| Round-robin | `backend/app/services/newsapi_scheduler.py` |
| Adapter + HTTP | `backend/app/sources/newsapi.py` |
| RSS fallback | `backend/app/sources/news_rss_fallback.py` |
| Poll persistence | `backend/app/services/factor_poll_log.py` |
| Budget RPC | `backend/app/services/news_api_budget.py` |
| Cron entry | `backend/app/jobs/event_detection.py` |
| Digest HTML | `backend/email-templates/editorial_digest.html` |

**Contact by role:** Product Owner for keyword/budget allocation changes; backend owner for ingest/dedup pipeline (Jordan/Sam per phase plan).

---

## Related documentation

- `docs/Post Implementation documentation/Phase1_P1-S6 - Event-detection scheduled job and editorial queue.md`
- `docs/Post Implementation documentation/Phase3_P3-S1c - Event de-duplication pipeline.md`
- `docs/Post Implementation documentation/Phase3_P3-S0 - Synthetic historical seed and triple-layer isolation.md`
