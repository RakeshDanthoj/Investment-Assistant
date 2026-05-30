# Post Implementation Detailed Document — P3-T2

**Version:** v1.0 | **Date:** 31-05-2026  
**Story ID:** P3-T2 (Phase 3, Test gate 2)  
**PRD2 gaps:** G-03, G-04, G-05, G-06 (verification layer for data pipeline stories)  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **7.0**–**7.5**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §4.1–§4.4 (dedup, NewsAPI, watchlist, market facts)  
**Upstream handover:**  
- `docs/Post Implementation documentation/Phase3_P3-S1c - Event de-duplication pipeline.md`  
- `docs/Post Implementation documentation/Phase3_P3-S1d - NewsAPI factor keyword scheduler.md`  
- `docs/Post Implementation documentation/Phase3_P3-S1e - Slow-burn watchlist.md`  
- `docs/Post Implementation documentation/Phase3_P3-S1f - Market facts freshness and fallback chain.md`

---

## Narrative style (read this first)

Phase 3 Week 1–2 delivered four independent pipeline capabilities: **dedup merge** (P3-S1c), **NewsAPI factor rotation** (P3-S1d), **watchlist escalation** (P3-S1e), and **critical-facts hold** (P3-S1f). Each had its own unit/integration tests, but nothing proved they work **together** as a coherent ingest → queue → draft gate. **P3-T2** closes that gap.

This story adds one cross-service pytest module (`test_data_pipeline_integration.py`) that exercises all four behaviours in a single test gate:

1. Three duplicate ingests of the same story merge to **one** event row with `source_count = 3`.
2. An eight-factor NewsAPI scheduler simulation completes **nine ticks** (sum of per-factor budgets) without exceeding any daily cap.
3. A watchlist manual escalate creates a **draft** event visible in the editorial queue filter.
4. An unavailable critical fact **holds** the card draft pipeline — no card row, `pipeline_runs.status = 'held'`.

Implementing test **7.4** exposed a production bug: `card_pipeline.py` already recorded `status="held"`, but migration `0020` only allowed `'ok'` and `'error'` on `pipeline_runs`. T2 therefore ships migration **`0026_pipeline_runs_held_status.sql`**, registers it in `migrate.py`, and adds `conn.commit()` in `pipeline_telemetry.py` so held runs persist.

**Tests executed and passed (P3-T2–specific):**

| Suite | Command | Result |
|-------|---------|--------|
| Data pipeline integration gate | `python -m pytest backend/tests/test_data_pipeline_integration.py -q` | **4 passed** (3 integration + 1 unit; integration requires `SUPABASE_DB_URL`) |
| Migration SQL contract | `python -m pytest backend/tests/test_pipeline_runs_migration_sql.py -q` | **1 passed** |
| **P3-T2 combined** | `python -m pytest backend/tests/test_data_pipeline_integration.py backend/tests/test_pipeline_runs_migration_sql.py -q` | **5 passed** |
| Full backend regression (post-T2) | `python -m pytest -q backend/tests` | **292 passed** |
| Lint | `python -m ruff check backend` | **All checks passed** |

**Three anchors for handover:** (1) **Apply migration `0026` on every environment** before relying on `held` rows in `pipeline_runs` or the 7.4 integration test; (2) **Integration tests use a session-scoped `db_connection`** — always `rollback()` in `finally` blocks so one failure does not poison later DB tests; (3) **P3-S1g must not merge until P3-T2 stays green** — confidence scoring depends on clean post-dedup `source_count` and stable pipeline gates.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-T2 |
| **Title** | Data pipeline integration test gate |
| **Category** | **Backend** (tests + small migration/fix; no UI) |
| **Points / owner (plan)** | 2 · Jordan |
| **Depends on** | P3-S1c, P3-S1d, P3-S1e, P3-S1f |
| **Parallel with** | _None_ |
| **Blocks** | **P3-S1g** (confidence scorer), **P3-S1a** (NLP filings — after T2 stable), **P3-T5** (FoW + signal gate — plan lists T2 as foundation) |

**What this story aimed to achieve (plain language)**

Before the platform replaces the Phase 1 source-count gate with a rule-based confidence scorer, it needs **automated proof** that the Week 1–2 data pipeline stories behave correctly end-to-end: duplicates merge, NewsAPI rotation respects caps, watchlist escalations land in the editorial queue, and missing critical market facts block card drafting without silently failing. If any of these regress, **CI should fail** before P3-S1g merges.

**How it fits into the overall application**

- **Upstream:** P3-S1c (dedup), S1d (NewsAPI scheduler), S1e (watchlist), S1f (critical-facts gate).
- **This story:** Cross-service verification gate — executable specification of G-03 through G-06 working together.
- **Downstream:** P3-S1g reads post-dedup `source_count` and assumes editorial queue rows are trustworthy; P3-S1a batch NLP should not add load until this gate is green.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **7.1** | `test_three_duplicate_ingests_merge_to_one_event_with_source_count_three` — three outlets, same headline/window → one row, `source_count = 3`, `sources` length 3. |
| **7.2** | `test_newsapi_eight_factor_rotation_respects_daily_cap` — simulated round-robin over 8 factors; 9 ticks; no factor exceeds budget. |
| **7.3** | `test_watchlist_escalated_event_visible_in_editorial_draft_queue` — escalate seed item → draft event with `event_source = 'watchlist'` in editorial filter. |
| **7.4** | `test_unavailable_critical_fact_records_held_pipeline_run` — gate raises → no card, `pipeline_runs.status = 'held'`. |
| **7.5** | Full backend CI green (ruff + pytest). |

**Functional breakdown**

1. **Dedup integration (7.1)**  
   Calls `persist_deduped_event` three times with distinct `event_source` + `canonical_url` but identical headline and detection window. Asserts outcomes `inserted`, `duplicate`, `duplicate`. Queries DB for single row with `source_count = 3`. Cleans up test events in `finally`.

2. **NewsAPI rotation (7.2)**  
   Uses in-memory `_eight_factor_config()` (mirrors production shape: 8 factors, budgets summing to 9 for fast simulation). Loops `resolve_next_factor` until exhausted. Asserts tick count equals `max_daily_calls` and per-factor counts ≤ budget. **No HTTP** — pure scheduler logic gate.

3. **Watchlist → editorial queue (7.3)**  
   Resets seed watchlist item `a1000001-0001-4001-8001-000000000001` to `watching`, deletes prior escalated event, calls `escalate_watchlist_item`. Asserts returned `event_id` appears in SQL filter matching editorial queue semantics (`lifecycle_state = 'draft'`, `event_source = 'watchlist'`). Restores seed state in `finally`.

4. **Critical-facts hold (7.4)**  
   Inserts minimal draft `events` row. Patches `assert_critical_facts_available` to raise `CriticalFactsHoldError(["inr_usd"])`. Calls `draft_card_from_event`. Asserts: exception raised, zero `cards` for event, latest `pipeline_runs` row has `status = 'held'` and `context.event_id` match. Cleans probe rows in `finally`.

5. **Connection patching (`_use_db_connection`)**  
   Patches `connection()` on dedup, watchlist, card_repository, pipeline_telemetry, and cost_guard so all services share the pytest session `db_connection` fixture.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| No `SUPABASE_DB_URL` | Integration tests **skip** (`conftest.py` `database_url` fixture). Unit test 7.2 **always runs**. |
| Session-scoped DB connection left in error state | ⚠️ Tests use `rollback()` in `finally` after failed `pipeline_runs` insert (pre-0026) poisoned downstream tests. |
| Watchlist seed item already escalated | Test resets item to `watching` and deletes prior event before escalate. |
| Critical facts unavailable vs stale | 7.4 tests **unavailable** path only; stale-allowed path covered in `test_market_facts_freshness.py`. |
| NewsAPI test uses mini budget (9 not 100) | Intentional — proves rotation/cap logic without 100-iteration loop; production budgets validated in `test_newsapi_scheduler.py`. |

**Business rules enforced (via tests)**

- Same real-world story from multiple sources → one queue row with accumulating `source_count` (G-03).
- NewsAPI factor scheduler must not exceed per-factor daily budgets (G-04).
- Watchlist escalation creates a draft event eligible for editorial review (G-05).
- Unavailable critical facts hold card drafting; pipeline telemetry records `held` (G-06).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Single integration module vs four separate files** | Plan specifies one cross-service E2E file; easier handover as one gate. | Extend each story’s test file only — no cross-story proof. |
| **Direct SQL for editorial queue assertion** | `fetch_events_filtered` uses Supabase REST + env keys; DB SQL matches queue semantics without extra secrets. | HTTP `GET /admin/events` — heavier, needs Supabase URL + service key in CI. |
| **Mini NewsAPI config in 7.2 (9 calls)** | Fast unit test; same `resolve_next_factor` code path as production. | Load real YAML (100 calls) — slow, redundant with `test_newsapi_scheduler.py`. |
| **Migration 0026 for `held` status** | 7.4 exposed DB constraint mismatch with `card_pipeline.py` behaviour from P3-S1f. | Test-only mock of `record_pipeline_run` — would not fix production telemetry gap. |
| **`pipeline_telemetry.py` commit** | Without commit, held rows were invisible to subsequent SELECT on same connection in tests and would not persist in production pool usage. | Rely on autocommit — not how `connection()` pool works. |
| **Patch critical-facts gate in 7.4** | Deterministic hold without live Yahoo/RBI/NSE network in test. | Full adapter chain — flaky, covered in `test_market_facts_freshness.py`. |

⚠️ **Do not remove migration `0026` or revert `held` from the check constraint** — P3-S1f hold telemetry and T2 test 7.4 depend on it.

⚠️ **Do not merge P3-S1g while P3-T2 integration tests are red locally** — plan hard-dependency on clean post-dedup event rows.

⚠️ **Register any new migration in `MIGRATION_FILES` in `migrate.py`** — 0026 was initially missing from the tuple and did not apply until fixed.

**Assumptions**

- Migration `0025` watchlist seed exists (five items including `WATCHLIST_SEED_ID`).
- Migrations through `0026` applied on DB used for integration runs (`apply_migrations` in each integration test).
- P3-S1c dedup columns (`source_count`, `sources`) present from migration `0023`.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S1c** — `persist_deduped_event`, merge columns; **P3-S1d** — `resolve_next_factor`, YAML config; **P3-S1e** — `escalate_watchlist_item`, migration `0025`; **P3-S1f** — `CriticalFactsHoldError`, `draft_card_from_event` hold path |
| **Downstream** | **P3-S1g** — confidence scorer (hard depends on T2); **P3-S1a** — NLP batch (plan: after T2 stable); **P3-T5** — FoW + signal gate |
| **Parallel** | None per plan |

**Shared components touched**

| Component | Role in T2 |
|-----------|------------|
| `app/services/event_dedup.py` | Dedup merge under test |
| `app/services/newsapi_scheduler.py` | Rotation cap under test |
| `app/services/watchlist.py` | Escalate → draft event |
| `app/services/card_pipeline.py` | Hold on critical facts |
| `app/services/pipeline_telemetry.py` | Persist `held` status (**fixed**) |
| `app/db/migrate.py` | Register `0026` |

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Integration test gate** — executable acceptance criteria spanning multiple services.
- **Connection override helper** — same pattern as `test_synthetic_isolation.py` for session fixture sharing.
- **Two-speed testing:** one fast unit test (7.2) + three DB integration tests (7.1, 7.3, 7.4).

**Database schema**

- Migration **`0026_pipeline_runs_held_status.sql`**: extends `pipeline_runs.status` check to `('ok', 'error', 'held')`.

**API contracts**

- None created or modified. Editorial queue asserted via SQL equivalent to `GET /admin/events?lifecycle_state=draft`.

**UI/UX**

- None.

**Libraries / tools**

- `pytest`, `unittest.mock.patch` (existing dev deps).
- No new pip dependencies.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `test_data_pipeline_integration.py` | `backend/tests/test_data_pipeline_integration.py` | Cross-service integration gate (tasks 7.1–7.4) |
| `0026_pipeline_runs_held_status.sql` | `backend/db/migrations/0026_pipeline_runs_held_status.sql` | Allow `held` status on `pipeline_runs` |
| `test_pipeline_runs_migration_sql.py` | `backend/tests/test_pipeline_runs_migration_sql.py` | Static SQL contract for migration 0026 |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `migrate.py` | `backend/app/db/migrate.py` | Added `0026_pipeline_runs_held_status.sql` to `MIGRATION_FILES` |
| `pipeline_telemetry.py` | `backend/app/services/pipeline_telemetry.py` | `conn.commit()` after successful `pipeline_runs` insert |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-T2 acceptance criteria and tasks **7.0**–**7.5** marked complete |

**Not modified (plan listed, not required)**

| File | Note |
|------|------|
| `.github/workflows/ci.yml` | Backend job already runs full `backend/tests` |

---

### A8. TESTS EXECUTED

#### P3-T2–specific tests

| Test | File | Status | What it verifies |
|------|------|--------|------------------|
| `test_three_duplicate_ingests_merge_to_one_event_with_source_count_three` | `test_data_pipeline_integration.py` | **Pass** (integration) | 3 ingests → 1 row, `source_count = 3` |
| `test_newsapi_eight_factor_rotation_respects_daily_cap` | `test_data_pipeline_integration.py` | **Pass** (unit) | 8-factor rotation respects per-factor caps |
| `test_watchlist_escalated_event_visible_in_editorial_draft_queue` | `test_data_pipeline_integration.py` | **Pass** (integration) | Escalate → draft event in editorial filter |
| `test_unavailable_critical_fact_records_held_pipeline_run` | `test_data_pipeline_integration.py` | **Pass** (integration) | Hold → no card, `pipeline_runs.status = held` |
| `test_pipeline_runs_migration_allows_held_status` | `test_pipeline_runs_migration_sql.py` | **Pass** | Migration 0026 SQL contains `held` constraint |

#### Commands

```bash
# P3-T2 only (from repo root)
python -m pytest -q backend/tests/test_data_pipeline_integration.py backend/tests/test_pipeline_runs_migration_sql.py

# CI-equivalent backend suite
python -m ruff check backend
python -m pytest -q backend/tests
```

#### Related regression (recommended after touching pipeline stories)

| Test file | Relevance |
|-----------|-----------|
| `test_event_dedup.py` | P3-S1c dedup unit/integration |
| `test_newsapi_scheduler.py` | P3-S1d rotation + adapter |
| `test_watchlist_escalate.py` | P3-S1e escalate paths |
| `test_market_facts_freshness.py` | P3-S1f gate + hold (mocked pipeline) |
| `test_card_pipeline.py` | ICE draft pipeline regression |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Migration `0026_pipeline_runs_held_status.sql`**

| Change | Detail |
|--------|--------|
| Table | `public.pipeline_runs` |
| Constraint | `pipeline_runs_status_check` — `status IN ('ok', 'error', 'held')` |
| Comment | Column documents `held` = blocked by critical-facts gate |

**Sequencing:** Apply after `0020_rate_limit_observability.sql` (creates `pipeline_runs`). Registered in `MIGRATION_FILES` after `0025_watchlist_items.sql`.

**Probe data in tests (not seed):**

- Temporary `events` rows (dedup + hold tests) — deleted in `finally`.
- Temporary `pipeline_runs` rows (hold test) — deleted in `finally`.
- Watchlist seed item reset after escalate test.

---

### B2. API / INTEGRATION CONTRACTS

**No HTTP endpoints added or changed.**

Tests call services directly:

| Surface | Function under test | Expected behaviour |
|---------|----------------------|-------------------|
| Dedup | `persist_deduped_event(...)` | 3rd ingest returns `duplicate`; `source_count = 3` |
| NewsAPI scheduler | `resolve_next_factor(...)` | Returns `None` when all budgets exhausted |
| Watchlist | `escalate_watchlist_item(item_id)` | Creates draft event; item `status = escalated` |
| Card pipeline | `draft_card_from_event(event_id)` | Raises `CriticalFactsHoldError`; telemetry `held` |

**Editorial queue equivalence**

```sql
SELECT id FROM public.events
WHERE lifecycle_state = 'draft'
  AND event_source = 'watchlist';
```

Matches admin queue filter used by `GET /admin/events?lifecycle_state=draft&event_source=watchlist`.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Data pipeline gate flow (verified by T2)**

```
Ingest (multiple sources)
  → persist_deduped_event (P3-S1c)
  → single event row, source_count accumulates

NewsAPI cron tick
  → resolve_next_factor (P3-S1d)
  → per-factor budget not exceeded

Editorial watchlist
  → escalate_watchlist_item (P3-S1e)
  → draft event in queue

Card draft request
  → assert_critical_facts_available (P3-S1f)
  → if unavailable: CriticalFactsHoldError
  → record_pipeline_run(status='held')
  → no card row, no LLM slot consumed
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Integration tests skip in CI without `SUPABASE_DB_URL` | 7.1, 7.3, 7.4 not run on every PR in GitHub | Unit test 7.2 always runs; add DB secret to backend job for full gate |
| NewsAPI test uses 9-call mini config | Does not re-validate production 100-call YAML split | `test_newsapi_scheduler.py` + `test_config_yaml_budgets_sum_to_100` |
| 7.4 mocks critical-facts gate | Does not exercise live adapter chain in integration | `test_market_facts_freshness.py` covers real gate logic |
| Session-scoped `db_connection` | One poisoned transaction breaks later integration tests | Always `rollback()` in `finally`; fixed after pre-0026 failure mode |

**Tech debt (optional improvements)**

- Add `@pytest.mark.integration` module doc noting dependency order (run T2 after S1c–S1f migrations).
- Extend T2 with HTTP-level admin queue assertion when CI has Supabase REST credentials.
- Consider parametrizing factor count in 7.2 if macro factor model expands beyond 8.

---

### B5. TESTING NOTES

**Automated**

| Layer | Coverage |
|-------|----------|
| Unit | NewsAPI rotation cap (7.2) |
| Integration | Dedup merge, watchlist escalate, critical-facts hold (7.1, 7.3, 7.4) |
| Static SQL | Migration 0026 contract |

**Manual (operator)**

| Step | When |
|------|------|
| Run P3-T2 pytest with `.env.local` `SUPABASE_DB_URL` | Before merge if pipeline behaviour changed |
| Confirm migrations through `0026` applied | Required for 7.4 and production `held` telemetry |

**Known gaps**

- No full HTTP e2e from ingest cron → admin UI queue.
- No test combining dedup merge **and** card draft on same event in one scenario (separate tests suffice for gate purpose).
- Cross-category dedup review queue not in T2 scope (covered in `test_dedup_review_queue.py`).

**Bug found during implementation**

- `pipeline_runs.status = 'held'` violated check constraint until migration 0026.
- `0026` not in `MIGRATION_FILES` initially — migration did not auto-apply in tests.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required for | Notes |
|----------|--------------|-------|
| `SUPABASE_DB_URL` | Integration tests 7.1, 7.3, 7.4 | Repo-root `.env.local`; Session pooler URI per `scripts/README.md` |
| _(none new)_ | Unit test 7.2 | Runs without DB |

**Deployment sequencing**

1. Deploy backend with migration **0026** (or run `apply_migrations` on target DB).
2. Merge test files — no frontend deploy required.

**Migration apply (ops)**

```bash
# Via app migrate helper (uses SUPABASE_DB_URL)
python -c "from app.core.settings import get_settings; from app.db.migrate import apply_migrations; import psycopg; c=psycopg.connect(get_settings().supabase_db_url); apply_migrations(c); c.close()"
```

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing pipeline stories S1c–S1f**

1. Run P3-T2 gate after your change:
   ```bash
   python -m pytest -q backend/tests/test_data_pipeline_integration.py backend/tests/test_pipeline_runs_migration_sql.py
   ```
2. If you add a new `pipeline_runs.status` value, extend migration 0026 pattern and update 7.4 assertion.
3. If you add a fifth cross-pipeline invariant, add a test to `test_data_pipeline_integration.py` — keep one module as the Week 2 gate.

**Common mistakes**

- Forgetting to add new migration files to `MIGRATION_FILES` in `migrate.py` — silent skip.
- Integration test without `finally` rollback on session-scoped connection — poisons full suite.
- Adding NewsAPI YAML factors without matching `public.factors` slug — poll log silently drops rows (see P3-S1d handover).

**Where to look**

| Concern | Path |
|---------|------|
| T2 integration tests | `backend/tests/test_data_pipeline_integration.py` |
| Dedup merge | `backend/app/services/event_dedup.py` |
| NewsAPI rotation | `backend/app/services/newsapi_scheduler.py`, `app/config/newsapi_keywords.yaml` |
| Watchlist escalate | `backend/app/services/watchlist.py` |
| Critical-facts hold | `backend/app/services/card_pipeline.py`, `market_facts_adapters.py` |
| Pipeline telemetry | `backend/app/services/pipeline_telemetry.py` |
| Migration 0026 | `backend/db/migrations/0026_pipeline_runs_held_status.sql` |

**Contact for context**

- **Backend / Phase 3 intelligence pipeline** — Jordan per plan (P3-T2, P3-S1g owner).
- **NewsAPI scheduler** — Sam per plan (P3-S1d).
- **Watchlist / editorial** — Riley per plan (P3-S1e).

---

## Audit checklist (story acceptance)

| Acceptance criterion | Met |
|----------------------|-----|
| 3 duplicate ingests → 1 event row, `source_count = 3` | Yes (7.1) |
| NewsAPI 8-factor rotation without exceeding daily cap | Yes (7.2) |
| Watchlist escalate → event visible in editorial queue | Yes (7.3) |
| Critical fact unavailable → card held in pipeline | Yes (7.4) |
| CI green before P3-S1g | Yes (292 passed, ruff clean) |
| Plan tasks 7.0–7.5 complete | Yes |

---

_Document version: v1.0 · Phase 3 · P3-T2 · G-03/G-04/G-05/G-06 verification gate_
