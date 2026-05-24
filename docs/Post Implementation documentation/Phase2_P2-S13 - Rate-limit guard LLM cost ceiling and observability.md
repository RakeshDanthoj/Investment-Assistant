# Post Implementation Detailed Document — P2-S13

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S13 (Phase 2, Story 13)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`  
**Assigned (plan):** Jordan | **Points:** 4 | **Layers:** Services, Ops

---

## Narrative style

**P2-S13** is a **Backend / Ops** hardening story: it protects the research budget as Phase 2 usage grows (especially **The Lens** on-demand ICE generation). Four capabilities shipped together: **(1)** a per-user **10 Lens queries/day** cap with HTTP **429** and `Retry-After`; **(2)** a configurable **monthly LLM spend ceiling** in INR that aborts pipelines before they run when projected month cost would exceed budget; **(3)** **structured JSON logs** on every card-draft pipeline run (prompt version, tokens, duration); **(4)** an admin-only **`GET /api/admin/metrics`** endpoint exposing PRD §13 ops metrics (daily card count, p95 generation time, high-confidence override / false-positive rates).

No frontend UI was added. Lens and editorial regenerate paths surface new error codes to clients (`lens_daily_rate_limit`, `llm_monthly_budget`). Operators must apply migration **`0020_rate_limit_observability.sql`** and set admin email env vars before production use.

**Tests executed and passed (P2-S13 scope):**

| Area | Command / suite | Result |
|------|-----------------|--------|
| Rate limit | `tests/test_rate_limit.py` | **3 passed** — 429 + `Retry-After`, enforce raises, happy path under cap |
| Monthly ceiling | `tests/test_cost_guard_monthly_ceiling.py` | **3 passed** — abort over projection, zero budget skip, Lens 402 |
| Admin metrics | `tests/test_admin_metrics.py` | **2 passed** — 403 non-admin, 200 shape for admin |
| Regression | `tests/test_card_pipeline.py`, `tests/test_lens_routes.py` | **6 passed** — pipeline + Lens routes still green with new guards mocked |
| **Combined** | `python -m pytest tests/test_rate_limit.py tests/test_cost_guard_monthly_ceiling.py tests/test_admin_metrics.py tests/test_card_pipeline.py tests/test_lens_routes.py -q` | **14 passed** |

**Operator follow-up (required):** run migration `0020` on Supabase; redeploy backend; set `ADMIN_EMAILS` (or `FACTOR_DB_ADMIN_EMAILS`). See B6 and B7.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S13 |
| **Title** | Rate-limit guard + LLM cost ceiling + observability |
| **Category** | **Backend** (services, middleware, migration, ops API; no frontend) |

**What this story aimed to achieve**

Phase 2 adds Lens on-demand card generation on top of Phase 1’s editorial pipeline. Without guardrails, a small tester cohort could spike Gemini usage and blow the ₹20K research budget (PRD §12 risk 7). This story caps each user to **10 Lens queries per UTC day**, enforces a **configurable monthly INR budget** across all LLM card drafts, emits **machine-readable pipeline logs** for every run, and exposes a **single admin metrics read API** aligned to PRD §13 success metrics.

**How it fits into the overall application**

**P1-S7** introduced the 50 cards/day UTC slot and per-card token accounting on `cards`. **P2-S7** streams Lens pipeline progress over SSE but reuses `draft_card_from_event`. P2-S13 layers **user-level** Lens throttling and **platform-level** monthly projection on top of the existing daily cap, and gives the product owner observability before **P3-S5** (hosted log/SLO hardening). **Phase 3** metrics work can build on `pipeline_runs` and JSON stdout logs introduced here.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | Delivered |
|----------|-----------|
| **13.1** | `app/middleware/rate_limit.py` + `try_consume_lens_query_slot` — 10 Lens queries/user/UTC day; 429 + `Retry-After` |
| **13.2** | Extended `cost_guard.py` — month-to-date `cards.llm_cost_usd` × `USD_INR_RATE` vs `LLM_MONTHLY_BUDGET_INR`; abort before pipeline |
| **13.3** | `app/core/logging.py` + `pipeline_telemetry.py` — JSON log line + `pipeline_runs` row per card draft |
| **13.4** | `GET /api/admin/metrics` — daily card count, p95 generation ms, override / false-positive rates |
| **13.5** | Pytest suites for 429, monthly ceiling, metrics access + shape |

**Functional breakdown — Lens rate limit (13.1)**

- On `POST /api/lens/queries`, before `create_query`, `enforce_lens_daily_limit(user_id)` calls DB RPC `try_consume_lens_query_slot`.
- First query of the UTC day inserts `lens_user_daily_usage` with `query_count = 1`.
- At cap (`query_count >= 10`), returns **429** with body `code: lens_daily_rate_limit` and header `Retry-After: <seconds until UTC midnight>`.
- Atomic `FOR UPDATE` row lock prevents race under concurrent requests (same pattern as P1-S7 `try_consume_llm_card_slot`).

**Functional breakdown — monthly cost ceiling (13.2)**

- `check_monthly_budget_or_raise()` runs:
  - On `POST /api/lens/queries` (before query row is created).
  - At start of `draft_card_from_event()` (before daily slot consume and LLM calls).
- Projection = `SUM(cards.llm_cost_usd)` for current UTC month + estimated cost of pending 3-call draft (~12k in / 4k out tokens at Flash-tier rates).
- If `projected_inr > LLM_MONTHLY_BUDGET_INR` → `MonthlyLLMBudgetError`.
- Setting `LLM_MONTHLY_BUDGET_INR=0` disables the check (escape hatch for local dev).
- Lens API returns **402** with `llm_monthly_budget`; SSE stream yields `event: error` with same code when pipeline fails mid-stream.

**Functional breakdown — structured logging (13.3)**

- App startup calls `configure_structured_logging()` — root logger emits one JSON object per line to stdout.
- Each `draft_card_from_event` completion (success or failure) calls `record_pipeline_run()`:
  - Logs `pipeline.run` with `prompt_version`, `input_tokens`, `output_tokens`, `duration_ms`, `status`, `event_id`, optional `card_id`.
  - Inserts into `public.pipeline_runs` when DB is available.
- DB insert failures are **swallowed** (warning log only) so telemetry never breaks card generation — important before migration 0020 is applied.

**Functional breakdown — admin metrics (13.4)**

| Metric | Source | Notes |
|--------|--------|-------|
| `daily_card_count` | `COUNT(cards)` where `created_at >= today UTC` | Editorial + Lens drafts |
| `p95_generation_time_ms` | `percentile_cont` proxy on `pipeline_runs.duration_ms` last N days | `null` if no runs |
| `high_confidence_override_rate` | High `confidence_gate_log` rows where `cards.updated_at > gate.created_at + 5 min` | Proxy for editorial reversal |
| `signal_false_positive_rate` | Same computation as override rate in V1 | PRD §13 uses override log for high-confidence auto-updates |

**Validations and error handling**

| Case | HTTP / behaviour |
|------|------------------|
| Lens query over daily cap | **429**, `Retry-After`, `lens_daily_rate_limit` |
| Monthly budget exceeded (Lens POST) | **402**, `llm_monthly_budget` |
| Monthly budget exceeded (pipeline) | Exception → Lens SSE error event; cards/admin regenerate **402** |
| Daily 50-card cap (unchanged P1-S7) | **429**, `llm_daily_cap` |
| Admin metrics, no Bearer token | **401** |
| Admin metrics, email not on allow-list | **403** |
| Admin metrics, DB down | **503**, `db_unavailable` |
| `pipeline_runs` table missing | Pipeline still succeeds; persist warning only |

**Business rules**

- Lens cap: **10 queries per user per UTC calendar day** (not rolling 24h).
- Platform daily cap: **50 LLM card generations per UTC day** (unchanged from P1-S7).
- Monthly ceiling: default **₹20,000**; USD spend from stored `cards.llm_cost_usd`, converted at `USD_INR_RATE` (default 85).
- Rate limit consumes a slot on **query creation**, not on stream completion (prevents queue flooding).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **DB-backed Lens rate limit (not in-memory token bucket)** | Matches P1-S7 `try_consume_llm_card_slot`; survives multi-worker Render deploys |
| **Rate check in route handler, not Starlette middleware** | Middleware cannot access `get_current_user` without duplicating Supabase auth |
| **Monthly check uses persisted `llm_cost_usd` on cards** | Ground truth already written by P1-S7 pipeline; no separate billing table |
| **402 for monthly budget** | Distinguishes “platform budget exhausted” from 429 daily caps; clients can show distinct copy |
| **Telemetry DB insert is best-effort** | Avoids hard dependency on migration 0020 during deploy ordering |
| **Admin allow-list reuses `FACTOR_DB_ADMIN_EMAILS` fallback** | One env var for operators who already have Factor DB admin access |
| **Override / false-positive rate proxy** | No dedicated “override” event table yet; `cards.updated_at` vs `confidence_gate_log.created_at` is V1 approximation |

⚠️ **Do not move Lens rate limit to client-only checks** — trivial to bypass; must stay server-side with atomic RPC.

⚠️ **Do not fail pipelines if `pipeline_runs` insert fails** — telemetry is supplementary; card generation is primary.

⚠️ **Do not grant `try_consume_lens_query_slot` to `anon`** — same security model as `try_consume_llm_card_slot` (service_role / API connection only).

⚠️ **Lens slot is consumed on POST, not on stream start** — changing this would allow 10 queued streams + unlimited POST spam; document if product wants “charge on completion” instead.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / modules |
|-----------|-------------------|
| **Upstream** | **P1-S7** `cost_guard` daily cap + `cards.llm_*` token fields; **P2-S6** Lens query API; **P2-S7** Lens SSE stream calling `draft_card_from_event`; **P1-S11** `confidence_gate_log` for metrics |
| **Downstream** | **P3-S5** scalability/observability — can ship JSON logs to hosted provider; **P2-S15** perf CI (orthogonal); all Lens usage stories inherit caps |
| **Parallel** | Every other P2 story — no blocking dependency |
| **Shared** | `draft_card_from_event`, `cost_guard`, Supabase auth (`get_current_user`), admin email pattern from Factor DB |

---

### A5. DESIGN CHOICES

**Architecture**

- Thin modules: `rate_limit.py` (Lens), `cost_guard.py` (budget), `pipeline_telemetry.py` (observability), `admin_metrics.py` (aggregation).
- JSON logging via custom `JsonLogFormatter` on root logger — no new third-party observability SDK (Phase 3).

**Database**

- `lens_user_daily_usage` — composite PK `(user_id, usage_date)`.
- `pipeline_runs` — append-only telemetry; indexed on `created_at DESC`.
- Security-definer RPCs with `REVOKE ALL FROM PUBLIC`.

**API contracts**

| Method | Route | Auth | Purpose |
|--------|-------|------|---------|
| POST | `/api/lens/queries` | Bearer (user) | **Modified** — rate + budget checks before create |
| GET | `/api/admin/metrics` | Bearer (admin email) | **New** — ops metrics JSON |
| POST | `/api/cards/draft-from-event` | (existing) | **Modified** — monthly budget error **402** |
| POST | `/api/admin/cards/{id}/regenerate` | (existing) | **Modified** — monthly budget error **402** |

**UI/UX**

- None in this story. Frontend may later map `lens_daily_rate_limit` / `llm_monthly_budget` to user-facing messages.

**Libraries**

- No new Python dependencies. Uses existing `psycopg`, FastAPI, Pydantic settings.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| 0020_rate_limit_observability.sql | `backend/db/migrations/0020_rate_limit_observability.sql` | Lens daily usage table + RPC; `pipeline_runs` table |
| __init__.py | `backend/app/middleware/__init__.py` | Middleware package marker |
| rate_limit.py | `backend/app/middleware/rate_limit.py` | Lens daily limit enforce + 429 helper |
| logging.py | `backend/app/core/logging.py` | JSON log formatter + `log_event()` |
| pipeline_telemetry.py | `backend/app/services/pipeline_telemetry.py` | Log + persist pipeline runs |
| admin_metrics.py | `backend/app/services/admin_metrics.py` | SQL aggregation for PRD §13 metrics |
| admin_metrics.py | `backend/app/api/admin_metrics.py` | `GET /api/admin/metrics` router |
| test_rate_limit.py | `backend/tests/test_rate_limit.py` | 429 + Retry-After tests |
| test_cost_guard_monthly_ceiling.py | `backend/tests/test_cost_guard_monthly_ceiling.py` | Monthly budget abort tests |
| test_admin_metrics.py | `backend/tests/test_admin_metrics.py` | Admin gate + response shape |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| cost_guard.py | `backend/app/services/cost_guard.py` | Monthly projection, `MonthlyLLMBudgetError`, `check_monthly_budget_or_raise` |
| card_pipeline.py | `backend/app/services/card_pipeline.py` | Monthly check, timing, `record_pipeline_run` on success/error |
| lens.py | `backend/app/api/lens.py` | Rate limit + monthly budget before `create_query` |
| lens_stream.py | `backend/app/api/lens_stream.py` | SSE error payload for `MonthlyLLMBudgetError` |
| cards.py | `backend/app/api/cards.py` | Handle `MonthlyLLMBudgetError` → 402 |
| admin_review.py | `backend/app/api/admin_review.py` | Handle `MonthlyLLMBudgetError` on regenerate → 402 |
| settings.py | `backend/app/core/settings.py` | `ADMIN_EMAILS`, `LLM_MONTHLY_BUDGET_INR`, `USD_INR_RATE` |
| migrate.py | `backend/app/db/migrate.py` | Register `0020_rate_limit_observability.sql` |
| main.py | `backend/app/main.py` | Structured logging startup; include admin metrics router |
| test_lens_routes.py | `backend/tests/test_lens_routes.py` | Mock new guards in happy-path test |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S13 acceptance + tasks marked complete |

---

### A8. TESTS EXECUTED

**Backend — automated (P2-S13 + regression)**

| Test file | Status | What it covers |
|-----------|--------|----------------|
| `test_rate_limit.py` | **Passed (3)** | `LensDailyRateLimitError` retry seconds; POST Lens 429 + `Retry-After` header; 201 when under cap |
| `test_cost_guard_monthly_ceiling.py` | **Passed (3)** | `check_monthly_budget_or_raise` raises over ₹100 cap; skipped when budget=0; Lens POST 402 |
| `test_admin_metrics.py` | **Passed (2)** | Non-admin 403; admin 200 with expected JSON keys |
| `test_card_pipeline.py` | **Passed (2)** | Mocked LLM pipeline still completes; migration file asserts RPC names |
| `test_lens_routes.py` | **Passed (4)** | Auth required; create/list shapes with guards mocked |

**Command used**

```bash
cd backend
python -m pytest tests/test_rate_limit.py tests/test_cost_guard_monthly_ceiling.py tests/test_admin_metrics.py tests/test_card_pipeline.py tests/test_lens_routes.py -q
```

**Result:** **14 passed** (executed 24-05-2026).

**Frontend:** None (no frontend changes in P2-S13).

**Manual testing recommended**

| Check | Expected |
|-------|----------|
| Apply migration 0020 on Supabase | Tables + RPCs exist; Lens POST no longer 503 on rate limit |
| `GET /api/admin/metrics` with admin Bearer token | 200 JSON metrics payload |
| Same request with non-admin token | 403 |
| 11th Lens query same user same UTC day | 429 + `Retry-After` |
| Render logs | JSON lines with `"event":"pipeline.run"` after card draft |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**`public.lens_user_daily_usage`**

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | uuid PK (part 1) | FK → `auth.users` |
| `usage_date` | date PK (part 2) | UTC calendar date |
| `query_count` | integer | Incremented atomically |

**`public.try_consume_lens_query_slot(p_user_id uuid, p_max int default 10)`**

- Returns `true` if slot consumed, `false` if at cap.
- `SECURITY DEFINER`, granted to `service_role` only.

**`public.pipeline_runs`**

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `pipeline` | text | e.g. `card_draft` |
| `prompt_version` | text | e.g. `synthesis.v1\|dissent.v1\|framework.v1` |
| `input_tokens`, `output_tokens` | integer | Summed usage for run |
| `duration_ms` | integer | Wall time for full pipeline |
| `status` | text | `ok` \| `error` |
| `error_message` | text nullable | Set on failure |
| `context` | jsonb | e.g. `event_id`, `card_id` |
| `created_at` | timestamptz | Default `now()` |

**Migration sequencing:** `0020_rate_limit_observability.sql` after `0019_saved_threads.sql` (registered in `migrate.py`).

**Seed data:** None.

---

### B2. API / INTEGRATION CONTRACTS

#### `POST /api/lens/queries` (modified)

**Auth:** Bearer (Supabase JWT) — unchanged.

**New pre-checks (before 201):**

1. Lens daily rate limit → **429**
2. Monthly budget → **402**

**429 example**

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 43200
Content-Type: application/json

{
  "detail": {
    "code": "lens_daily_rate_limit",
    "message": "Lens daily query limit reached (10/day)"
  }
}
```

**402 example (monthly budget)**

```json
{
  "detail": {
    "code": "llm_monthly_budget",
    "message": "monthly LLM budget exceeded: projected ₹21000.00 > ceiling ₹20000"
  }
}
```

#### `GET /api/admin/metrics` (new)

**Auth:** Bearer + email on `ADMIN_EMAILS` or `FACTOR_DB_ADMIN_EMAILS`.

**Query params:** `window_days` (default 30, 1–365).

**200 example**

```json
{
  "as_of": "2026-05-24T12:00:00+00:00",
  "window_days": 30,
  "daily_card_count": 3,
  "p95_generation_time_ms": 45230.0,
  "high_confidence_override_rate": 0.1,
  "signal_false_positive_rate": 0.1,
  "high_confidence_gate_total": 10,
  "high_confidence_gate_overridden": 1
}
```

**curl (smoke test)**

```bash
curl -H "Authorization: Bearer <supabase-access-token>" \
  https://<render-api-host>/api/admin/metrics
```

Obtain `<supabase-access-token>` from browser DevTools → Network → any authenticated API request → copy `Authorization` header value after `Bearer `.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Lens rate limit flow**

```
POST /api/lens/queries
  → enforce_lens_daily_limit(user_id)
       → try_consume_lens_query_slot (DB RPC)
            → false → 429 + Retry-After
  → check_monthly_budget_or_raise()
       → projected_inr > budget → 402
  → create_query() → 201
```

**Monthly projection**

```
mtd_usd = SUM(cards.llm_cost_usd) WHERE created_at >= month_start_utc
estimate_usd = estimate_cost_usd(12000 in, 4000 out)  # if not provided
projected_inr = (mtd_usd + estimate_usd) * USD_INR_RATE
abort if projected_inr > LLM_MONTHLY_BUDGET_INR
```

**Pipeline telemetry flow**

```
draft_card_from_event()
  → started = perf_counter()
  → try:
       check_monthly_budget_or_raise()
       consume_slot_or_raise()  # daily 50 cap
       ... 3 LLM calls ...
       insert_draft_card_bundle()
    except:
       record_pipeline_run(status=error)
       raise
  → record_pipeline_run(status=ok)
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Notes |
|------------|-------|
| Override / false-positive metrics are **proxies** | Uses `cards.updated_at` vs gate log timestamp; no explicit “editor reversed auto-update” event |
| Lens cap is **UTC midnight reset**, not user timezone | Document for Indian testers if UX copy added later |
| Monthly budget uses **estimated** next-draft cost | Actual token usage may differ; conservative estimate may block early |
| `pipeline_runs` only tracks **`card_draft`** pipeline | Prediction grader / other LLM calls not logged yet |
| No frontend handling for 429/402 on Lens | Users may see generic errors until P2 polish |
| Rate limit + budget checks require **live DB** | Local tests mock guards; integration tests need migration 0020 |

---

### B5. TESTING NOTES

**Automated:** All P2-S13 tests mock DB guards or admin fetch; no live Supabase required for CI unit tests.

**Not automated in this story:**

- End-to-end: 11 Lens POSTs same user → 429 on prod after migration
- Render log drain / JSON parsing in hosted log tool
- Admin metrics with real `confidence_gate_log` data

**Gaps:** No integration test against real `try_consume_lens_query_slot` RPC (would need `db_connection` fixture + migration).

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_MONTHLY_BUDGET_INR` | `20000` | Monthly INR ceiling; `0` disables check |
| `USD_INR_RATE` | `85` | Converts stored USD costs to INR for projection |
| `ADMIN_EMAILS` | `""` | Comma-separated emails allowed on `/api/admin/metrics` |
| `FACTOR_DB_ADMIN_EMAILS` | `""` | Fallback allow-list if `ADMIN_EMAILS` empty |

**Unchanged (still required):** `SUPABASE_DB_URL`, `GEMINI_API_KEY`, Supabase auth keys.

**Deployment sequencing**

1. Deploy backend code.
2. Run migration **0020** (or full `apply_migrations`).
3. Set `ADMIN_EMAILS` on Render.
4. Verify `GET /api/admin/metrics` and one Lens query.

⚠️ Deploying code **before** migration 0020: Lens rate limit RPC will fail → likely **503** on Lens POST; pipeline telemetry rows skipped (logged warning only).

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing this code**

- Read **P1-S7** post-implementation doc for daily 50-card cap and `llm_cost_usd` semantics.
- Lens rate limit is **independent** of the 50/day **platform** cap — both apply (user can hit either first).
- To change Lens cap, update `LENS_DAILY_CAP` in `rate_limit.py` **and** RPC default / migration comment; keep in sync.

**Common mistakes**

- Adding rate limit only on SSE stream — users can still spam `POST /api/lens/queries`.
- Making `record_pipeline_run` raise on DB error — breaks card generation in staging without migration.
- Using `FACTOR_DB_ADMIN_EMAILS` alone without setting it on Render — metrics endpoint returns 403 for everyone.

**Where to find related code**

| Concern | Path |
|---------|------|
| Lens rate limit | `backend/app/middleware/rate_limit.py`, `backend/app/api/lens.py` |
| Monthly budget | `backend/app/services/cost_guard.py` |
| Pipeline timing/logs | `backend/app/services/card_pipeline.py`, `pipeline_telemetry.py` |
| Admin metrics SQL | `backend/app/services/admin_metrics.py` |
| JSON logging | `backend/app/core/logging.py` |
| Migration | `backend/db/migrations/0020_rate_limit_observability.sql` |

**Who to contact for context**

- **Product Owner** — budget thresholds (₹20K), whether Lens cap should be 10/day or adjusted for tester cohort size.
- **Backend owner (Jordan per plan)** — cost guard + observability follow-ups for Phase 3.

---

*End of document — P2-S13 v1.0*
