# Post Implementation Detailed Document — P3-T1

**Version:** v1.0 | **Date:** 30-05-2026  
**Story ID:** P3-T1 (Phase 3, Test gate 1)  
**PRD2 gap:** G-13 (verification layer for synthetic seed isolation)  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **2.0**–**2.5**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §7.2 — *Synthetic isolation verification (P3-T1)*  
**Upstream handover:** `docs/Post Implementation documentation/Phase3_P3-S0 - Synthetic historical seed and triple-layer isolation.md`

---

## Narrative style (read this first)

**P3-S0** seeded 20 synthetic events and wired **Layer 1 (RLS)** and **Layer 2 (`SyntheticFilterMixin`)** so calibration data never pollutes Pulse, Thread, or Mirror. **P3-T1** completes **Layer 3**: automated proof that isolation holds and stays enforced in CI.

This story adds **no new API routes, migrations, or UI**. It adds two pytest modules: a **static guard** that fails the build if a known user-facing read module drops the synthetic filter, and **integration tests** that seed synthetic data, deliberately create probe rows (published card on synthetic event, synthetic `user_predictions`), and assert Pulse feed, Thread detail, and Mirror list exclude them. A **negative smoke** confirms the `postgres` / service-role connection can still `SELECT` synthetic rows for admin and calibration jobs.

**Tests executed and passed (P3-T1–specific):**

| Suite | Command | Result |
|-------|---------|--------|
| Static query-path guard | `python -m pytest backend/tests/test_query_synthetic_filter.py -q` | **5 passed** |
| Integration isolation gate | `python -m pytest backend/tests/test_synthetic_isolation.py -q` | **4 passed** (requires `SUPABASE_DB_URL`; see B5) |
| **P3-T1 combined** | `python -m pytest backend/tests/test_query_synthetic_filter.py backend/tests/test_synthetic_isolation.py -q` | **9 passed** |
| Full backend regression (post-T1) | `python -m pytest -q backend/tests` | **265 passed** |
| Lint | `python -m ruff check backend` | **All checks passed** |

**Three anchors for handover:** (1) **Update `USER_FACING_READ_MODULES`** in `test_query_synthetic_filter.py` whenever a new user-facing read path joins `events` / `user_predictions` / `track_record`; (2) **Static tests always run in CI** — no DB secret required; (3) **Integration tests skip in CI** unless `SUPABASE_DB_URL` is added to the backend job — merge protection for isolation is primarily the static guard today.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-T1 |
| **Title** | Synthetic isolation verification gate |
| **Category** | **Backend** (tests + documentation; no runtime feature code) |
| **Points / owner (plan)** | 2 · Riley |
| **Depends on** | P3-S0 (migration `0021`, seed, `SyntheticFilterMixin`) |
| **Parallel with** | P3-S1c (after P3-S0 migration lands) |
| **Blocks** | Confidence in Week 1 foundation; plan risk register cites T1 tests must stay green |

**What this story aimed to achieve (plain language)**

Week 1 synthetic seed data lives in the same database as real events. This story adds **automated proof** that synthetic rows never appear in Pulse (feed), Thread (card detail), or Mirror (prediction list). If a developer removes the service-layer filter or adds a new read path without it, **CI should fail** before merge.

**How it fits into the overall application**

- **Upstream:** P3-S0 triple-layer isolation (RLS + `SyntheticFilterMixin` + seed).
- **This story:** Layer 3 — CI/static + integration verification.
- **Downstream:** P3-S1c, S1d, S1e, and all later Phase 3 work assume synthetic data cannot leak into user trust metrics; plan explicitly lists **synthetic data leak** as a risk if T1 tests go red.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **2.1** | `test_synthetic_isolation.py` — integration tests for Pulse (`build_feed_response`), Thread (`build_card_detail`), Mirror (`list_predictions`). |
| **2.2** | `test_query_synthetic_filter.py` — parametrized static guard on four service modules. |
| **2.3** | Tests run via existing `.github/workflows/ci.yml` backend job (`python -m pytest -q backend/tests`); no workflow file change required. |
| **2.4** | `test_service_role_direct_query_can_read_synthetic_events` — direct SQL counts 20 synthetic / 7 major. |
| **2.5** | One paragraph added to PRD2 §7.2 documenting the triple-layer contract and test file names. |

**Functional breakdown**

1. **Static guard (`test_query_synthetic_filter.py`)**  
   For each module in `USER_FACING_READ_MODULES`, read source from disk and assert:
   - File exists.
   - `SyntheticFilterMixin` is referenced.
   - Required fragment names appear (`events_not_synthetic`, and for Mirror also `predictions_not_synthetic`).

2. **Integration — Pulse**  
   After `seed_events()` (20 synthetic rows), call `build_feed_response()`. Every feed item’s `event_id` must not be in the set of synthetic event IDs.

3. **Integration — Thread**  
   Insert a **published** probe `cards` row linked to a seeded synthetic `events` row. `build_card_detail(card_id, view="current")` must return `None`. Probe card deleted in `finally`.

4. **Integration — Mirror**  
   Insert probe card + `user_predictions` row with `is_synthetic = TRUE` for a test `auth.users` row. `list_predictions(user_id)` must not return the probe `card_id`. Cleanup in `finally`.

5. **Integration — service-role smoke**  
   Raw `SELECT count(*)` on `events WHERE is_synthetic = TRUE` (and major subset) — expects 20 and 7. Confirms calibration/admin SQL path can see seed data (RLS bypass via postgres role in tests).

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| No `SUPABASE_DB_URL` | Integration tests **skip** (`conftest.py` `database_url` fixture). |
| Static guard | **Never skips** — runs in CI without secrets. |
| Feed with no cards on synthetic events | Pulse test still valid: asserts no `event_id` in synthetic set (probe card would fail if filter broken). |
| Thread probe | Uses minimal ICE columns + `published` lifecycle to exercise real detail query path. |
| Test DB connection sharing | `_use_db_connection` patches `connection()` on seed, feed, card_repository, mirror_predictions so all use the pytest fixture connection. |
| New read module added | ⚠️ Must add path to `USER_FACING_READ_MODULES` or static guard will not protect it. |

**Business rules enforced (via tests, not new runtime code)**

- User-facing Pulse, Thread, Mirror paths must not surface `is_synthetic = TRUE` events or predictions.
- Synthetic seed remains visible to service-role SQL (calibration / ops).
- Documented contract aligns with PRD2 G-13 triple-layer model.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Service-layer tests, not HTTP `TestClient`** | Matches `test_query_consolidation.py`; exercises real SQL in `feed.py`, `card_repository.py`, `mirror_predictions.py`. | Full API e2e: heavier setup, duplicates S0 filter logic. |
| **Explicit module allowlist for static guard** | Fails fast on omission; clear handover list for new paths. | Repo-wide AST/grep for all `FROM public.events`: noisy false positives. |
| **Probe rows in integration tests** | Proves exclusion even when synthetic events have no production cards. | Seed-only assertion: weak if no cards exist on synthetic events. |
| **No `ci.yml` change** | Existing backend pytest job already runs all `backend/tests`. | Separate job step: redundant. |
| **PRD2 paragraph only (no new ops doc)** | Task 2.5 AC; S0 handover remains source for seed/migration ops. | Duplicate runbook in `backend/scripts/README.md`. |
| **`is_synthetic IS NOT TRUE` in mixin** | Matches partial indexes from P3-S0 / `0022` (NULL-safe). | `= FALSE` only: diverges from production SQL. |

⚠️ **Do not remove modules from `USER_FACING_READ_MODULES` without replacing coverage** — that weakens the only CI-enforced isolation check when integration tests skip.

⚠️ **Do not add user-facing `events` reads without `SyntheticFilterMixin`** — static test will fail only if the file is in the allowlist; new files are invisible until added.

⚠️ **Do not assume integration tests run in GitHub Actions today** — unless `SUPABASE_DB_URL` is added to the backend job secrets.

**Assumptions**

- P3-S0 seed has been run on the DB used for local integration runs (or `synthetic_seed` fixture runs `seed_events()`).
- Mirror probe uses same `auth.users` insert pattern as `test_predictions_write_to_track_record.py`.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S0** — `0021_synthetic_isolation.sql`, `SyntheticFilterMixin`, `seed_synthetic_events.py`, 20-event fixture. |
| **Downstream** | All Phase 3 stories that rely on synthetic calibration data (P3-S1g scorer, P3-S1l FoW, P3-S2 after 30-day soak). Plan risk: *Synthetic data leak — P3-T1 triple-layer tests must stay green in CI.* |
| **Parallel** | P3-S1c (dedup), P3-S1d (NewsAPI), P3-S1e (watchlist) per milestone map. |

**Shared components touched (read-only verification)**

- `app/services/feed.py` (Pulse)
- `app/services/card_repository.py` + `app/services/card_detail.py` (Thread)
- `app/services/mirror_predictions.py` (Mirror)
- `app/services/market_facts.py` (static guard only; no dedicated integration test yet)

**No runtime code paths modified** — only tests and PRD2/plan documentation.

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Test gate / contract test** — encodes PRD2 isolation as executable specification.
- **Two-speed testing:** fast static (CI always) + slow integration (local / optional CI DB).

**Database schema**

- None in P3-T1 (uses P3-S0 schema).

**API contracts**

- None created or modified.

**UI/UX**

- None.

**Libraries / tools**

- `pytest` + `unittest.mock.patch` (existing dev deps).
- No new pip dependencies.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `test_synthetic_isolation.py` | `backend/tests/test_synthetic_isolation.py` | Integration: Pulse, Thread, Mirror exclusion + service-role smoke |
| `test_query_synthetic_filter.py` | `backend/tests/test_query_synthetic_filter.py` | Static guard on user-facing read modules |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `FinnWise_PRD2_Intelligence_Architecture.md` | `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` | Added §7.2 subsection *Synthetic isolation verification (P3-T1)* |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-T1 acceptance criteria and tasks **2.0**–**2.5** marked complete |

**Not modified (plan listed, not required)**

| File | Note |
|------|------|
| `.github/workflows/ci.yml` | Backend job already runs full `backend/tests`; static guard included |

---

### A8. TESTS EXECUTED

#### P3-T1–specific tests

| Test | File | Status | What it verifies |
|------|------|--------|------------------|
| `test_user_facing_module_imports_and_applies_synthetic_filter[app/services/feed.py]` | `test_query_synthetic_filter.py` | **Pass** | Pulse feed module uses `SyntheticFilterMixin` + `events_not_synthetic` |
| `test_user_facing_module_imports_and_applies_synthetic_filter[app/services/card_repository.py]` | `test_query_synthetic_filter.py` | **Pass** | Thread/detail repository uses event filter |
| `test_user_facing_module_imports_and_applies_synthetic_filter[app/services/mirror_predictions.py]` | `test_query_synthetic_filter.py` | **Pass** | Mirror uses prediction + event filters |
| `test_user_facing_module_imports_and_applies_synthetic_filter[app/services/market_facts.py]` | `test_query_synthetic_filter.py` | **Pass** | Market facts event reads filtered |
| `test_synthetic_filter_mixin_documents_pulse_thread_mirror_scope` | `test_query_synthetic_filter.py` | **Pass** | Mixin docstring scope + SQL fragment shape |
| `test_pulse_feed_excludes_synthetic_events` | `test_synthetic_isolation.py` | **Pass** (integration) | No synthetic `event_id` in feed items |
| `test_thread_detail_excludes_synthetic_event_cards` | `test_synthetic_isolation.py` | **Pass** (integration) | Card on synthetic event → `build_card_detail` is `None` |
| `test_mirror_predictions_exclude_synthetic_rows` | `test_synthetic_isolation.py` | **Pass** (integration) | Synthetic prediction not in `list_predictions` |
| `test_service_role_direct_query_can_read_synthetic_events` | `test_synthetic_isolation.py` | **Pass** (integration) | Direct SQL: 20 synthetic, 7 major |

#### Commands

```bash
# P3-T1 only (from repo root)
python -m pytest -q backend/tests/test_query_synthetic_filter.py backend/tests/test_synthetic_isolation.py

# CI-equivalent backend suite
python -m ruff check backend
python -m pytest -q backend/tests
```

#### Related regression (recommended after touching isolation)

| Test file | Relevance |
|-----------|-----------|
| `test_synthetic_isolation_migration_sql.py` | P3-S0 migration contract |
| `test_synthetic_seed_idempotent.py` | P3-S0 seed idempotency |
| `test_feed_filtering.py`, `test_query_consolidation.py` | Pulse/Thread paths unchanged |
| `test_mirror_routes.py` | Mirror API shapes |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**None in P3-T1.**

Integration tests **read and write probe data** only:

- Reuse seeded `events` (`is_synthetic = TRUE`).
- Temporary `cards` and `user_predictions` rows (deleted in test `finally`).
- Optional `auth.users` row for Mirror probe (same pattern as P1-S12 tests).

---

### B2. API / INTEGRATION CONTRACTS

**No HTTP endpoints added or changed.**

Tests call service functions directly:

| Surface | Function under test | Expected when synthetic |
|---------|---------------------|-------------------------|
| Pulse | `build_feed_response(session_id=None, horizon=None, category=None)` | No items with synthetic `event_id` |
| Thread | `build_card_detail(card_id, view="current")` | `None` for card on synthetic event |
| Mirror | `list_predictions(user_id)` | No rows for synthetic probe card |

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Isolation contract (enforced by P3-S0 implementation, verified by P3-T1)**

```
User request → FastAPI (postgres role, bypasses RLS)
  → Service SQL includes: alias.is_synthetic IS NOT TRUE
  → Synthetic events/predictions never joined/returned

Authenticated PostgREST/JWT → RLS policy: NOT is_synthetic
  → Synthetic rows hidden at DB layer

Ops / seed / calibration → postgres or service role
  → May SELECT synthetic rows (smoke test asserts counts)
```

**Static guard rule:** each file in `USER_FACING_READ_MODULES` must contain `SyntheticFilterMixin` and the listed method name strings in source (proxy for SQL usage).

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Integration tests skip in CI without `SUPABASE_DB_URL` | Pulse/Thread/Mirror leakage not caught on every PR in GitHub | Static guard still runs; consider adding DB secret to backend job |
| `market_facts.py` in static list only | No integration test for Lens/market-facts reads | Add test if market-facts becomes user-trust critical |
| Allowlist maintenance | New read modules can ship without guard until listed | Code review + update `USER_FACING_READ_MODULES` |
| Probe cards use manual SQL in tests | Not testing full editorial publish pipeline | Sufficient for filter verification |

**Tech debt (optional improvements)**

- Add `test_synthetic_isolation` marker to CI with ephemeral test DB or Supabase branch.
- Extend integration coverage to HTTP layer (`TestClient` on `/api/feed`, `/api/cards/{id}`, `/api/mirror/predictions`).

---

### B5. TESTING NOTES

**Automated**

| Layer | Coverage |
|-------|----------|
| Static | 4 modules × parametrized + 1 mixin contract test |
| Integration | 4 tests with DB (seed fixture module-scoped) |

**Manual (operator)**

| Step | When |
|------|------|
| Run P3-T1 pytest with `.env.local` `SUPABASE_DB_URL` | Before merge if integration behaviour changed |
| Confirm `seed_synthetic_events.py` already run on target DB | Integration fixture expects 20 synthetic rows |

**Known gaps**

- No frontend/E2E test for synthetic leakage (backend-only story).
- No test for `signals` or `track_record` user-facing reads in isolation file (filtered in `card_repository` / future stories).

**Flaky-run note:** During initial T1 implementation, an unrelated full-suite run reported 2 NewsAPI test failures; a later full run reported **265 passed**. Failures were not caused by P3-T1 files. Re-run `pytest backend/tests` if diagnosing CI redness.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required for | Notes |
|----------|--------------|-------|
| `SUPABASE_DB_URL` | Integration tests only | Repo-root `.env.local`; Session pooler URI per `scripts/README.md` |
| _(none new)_ | Static tests | Run without DB |

**Deployment:** No deploy steps. Merge test files + PRD2 paragraph; ensure backend CI green.

**Seed (P3-S0 dependency):**

```bash
python backend/scripts/seed_synthetic_events.py
```

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing user-facing reads**

1. Open `backend/tests/test_query_synthetic_filter.py` — add any new module that `SELECT`s from `events`, `user_predictions`, or `track_record` for users.
2. Apply `SyntheticFilterMixin` in SQL (see `backend/app/db/queries/base.py`).
3. Run:
   ```bash
   python -m pytest -q backend/tests/test_query_synthetic_filter.py backend/tests/test_synthetic_isolation.py
   ```

**Common mistakes**

- Relying on RLS alone for FastAPI — **API uses postgres role; RLS does not apply.**
- Adding `FROM public.events` in a new service without mixin — static guard only catches listed files.
- Removing `events_not_synthetic` from JOIN clause “for performance” without partial index review — breaks T1 and corrupts trust metrics.

**Where to look**

| Concern | Path |
|---------|------|
| SQL filter helpers | `backend/app/db/queries/base.py` |
| Pulse | `backend/app/services/feed.py` |
| Thread | `backend/app/services/card_repository.py`, `card_detail.py` |
| Mirror | `backend/app/services/mirror_predictions.py` |
| Static guard list | `backend/tests/test_query_synthetic_filter.py` → `USER_FACING_READ_MODULES` |
| Integration probes | `backend/tests/test_synthetic_isolation.py` |
| Seed / migration | P3-S0 handover doc, `0021_synthetic_isolation.sql` |

**Contact for context**

- **Backend / Phase 3 intelligence pipeline** — owner of P3-S0 seed and downstream scorer (Jordan per plan).
- **Test gates / editorial integrity** — Riley per plan assignment for P3-T1.

---

## Audit checklist (story acceptance)

| Acceptance criterion | Met |
|----------------------|-----|
| `test_synthetic_isolation.py`: Pulse, Thread, Mirror zero synthetic when seed exists | Yes |
| `test_query_synthetic_filter.py`: static guard on user-facing modules | Yes |
| Failing test blocks merge via existing CI pytest job | Yes (static tests) |
| Service-role can read synthetic (smoke) | Yes |
| PRD2 isolation paragraph | Yes |
| Plan tasks 2.0–2.5 complete | Yes |

---

_Document version: v1.0 · Phase 3 · P3-T1 · G-13 verification gate_
