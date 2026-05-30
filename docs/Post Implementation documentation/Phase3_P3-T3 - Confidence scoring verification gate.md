# Post Implementation Detailed Document — P3-T3

**Version:** v1.0 | **Date:** 31-05-2026  
**Story ID:** P3-T3 (Phase 3, Test gate 3)  
**PRD2 gaps:** G-01, G-02 (verification before editorial hard gates)  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **10.0**–**10.5**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §3.1 (confidence scorer), §3.2 (gate thresholds)  
**Upstream handover:**  
- `docs/Post Implementation documentation/Phase3_P3-S1g - Rule-based confidence scorer and gate swap.md`  
- P3-S1h explainability UI (`ConfidenceComposition.tsx`, `frontend/lib/api/confidenceBreakdown.ts` — plan task **9.0**)

---

## Narrative style (read this first)

Phase 3 replaced the Phase 1 **source-count heuristic** with a rule-based confidence scorer (P3-S1g), narrow gate thresholds (G-02), and a Thread **“Why this confidence tier?”** panel (P3-S1h). Each piece had unit tests, but nothing proved they **agree** before the next story — **P3-S1i** (number validator hard publish gate) — starts depending on scores in production.

**P3-T3** closes that gap. It adds:

1. **API verification** — `GET /api/events/{id}/confidence-breakdown` returns input bars whose weighted sum matches `confidence_raw`, and FoW dampening sets `confidence_effective = raw × 0.6` with tier derived from effective score.
2. **Signal monitor regression** — three matching market facts with `confidence_effective = 0.40` routes to **low** (digest), not high — proving routing uses stored effective score, not fact count.
3. **Frontend RTL** — expanded `ConfidenceComposition` shows all five scorer inputs from a fixture.
4. **Calibration ritual** — `docs/plans/phase3-calibration.md` documents Day 30/60 recalibration (no code auto-tuning).

This story adds **no new migrations, API routes, or production services** — only tests and documentation.

**Tests executed and passed (P3-T3–specific):**

| Suite | Command | Result |
|-------|---------|--------|
| Confidence scoring gate | `python -m pytest -q backend/tests/test_confidence_scoring_gate.py` | **3 passed** (integration; requires `SUPABASE_DB_URL`) |
| Breakdown API contract | `python -m pytest -q backend/tests/test_confidence_breakdown_api.py` | **2 passed** (integration + 404) |
| ConfidenceComposition RTL | `pnpm test ConfidenceComposition.test.tsx` (from `frontend/`) | **2 passed** |
| **P3-T3 combined (recommended)** | `python -m pytest -q backend/tests/test_confidence_scoring_gate.py backend/tests/test_confidence_breakdown_api.py` + frontend test above | **7 passed** |
| Full backend regression (post-T3) | `python -m ruff check backend` + `python -m pytest -q backend/tests` | **295 passed**, ruff clean |
| Frontend lint/typecheck | `pnpm lint` + `pnpm typecheck` | Pass |

**Three anchors for handover:** (1) **Do not start P3-S1i while P3-T3 is red** — publish gate depends on trustworthy scores; (2) **Any change to `confidence_config.py` must re-run** `test_confidence_scorer.py` and `test_confidence_scoring_gate.py`; (3) **FoW API test uses `monkeypatch` on `fetch_fog_active`** — unit FoW math is still proven in `test_confidence_scorer.py`; optional follow-up is a DB-only test seeding three `is_major` active events.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-T3 |
| **Title** | Confidence scoring verification gate |
| **Category** | **Full Stack** (backend integration tests + frontend RTL; no new production code) |
| **Points / owner (plan)** | 2 · Riley |
| **Depends on** | P3-S1g (scorer + gate), P3-S1h (explainability UI) |
| **Parallel with** | _None_ |
| **Blocks** | **P3-S1i** (number validator hard publish gate) |

**What this story aimed to achieve (plain language)**

The platform needs automated proof that the new confidence scorer, narrow HIGH/MEDIUM/LOW thresholds, breakdown API, Thread explainability panel, and signal monitor routing all tell the same story. If breakdown bars do not sum to the displayed raw score, or the signal monitor still routes on “how many facts matched” instead of `confidence_effective`, editors could see trustworthy-looking UI with wrong backend behaviour. P3-T3 makes those failures **CI-visible** before hard publish gates trust the scores.

**How it fits into the overall application**

- **Upstream:** P3-S1g (`confidence_scorer.py`, `confidence_gate.py`, `confidence_config.py`, audit table); P3-S1h (`ConfidenceComposition`, `confidenceBreakdown` client); P3-T2 (clean post-dedup `source_count` for scorer inputs).
- **This story:** Executable acceptance gate for G-01/G-02 agreement across API, UI, and signal monitor.
- **Downstream:** P3-S1i (publish blocked on ungrounded numbers); P3-S1m (override log feeds Day 30/60 calibration in `phase3-calibration.md`).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **10.1** | API tests: weighted sum vs `confidence_raw`; FoW dampener on effective score and tier. |
| **10.2** | Signal monitor integration: high fact count + low `confidence_effective` → low gate + `digest_log`. |
| **10.3** | RTL: expand panel → five inputs + FoW callout + escalation badge; lazy fetch; 404 error. |
| **10.4** | `docs/plans/phase3-calibration.md` — Week 2, Day 30, Day 60, monthly ritual. |
| **10.5** | Full CI green before P3-S1i. |

**Functional breakdown**

1. **Breakdown sum (10.1)**  
   Inserts draft `events` row with three RBI/ET/Mint sources and `factor_db_match_count = 2`. Calls `GET /api/events/{id}/confidence-breakdown`. Recomputes weighted sum from `inputs.*.value × WEIGHTS` and asserts `confidence_raw ≈ sum` (ε = 0.002).

2. **FoW dampener via API (10.1)**  
   `monkeypatch.setattr(..., fetch_fog_active, lambda **_: True)` so breakdown payload has `fog_active: true`. Asserts `confidence_effective ≈ round(confidence_raw × 0.6, 3)`, `tier == tier_from_score(effective)`, and `route(effective).tier` matches API tier.

3. **Signal monitor regression (10.2)**  
   Seeds published card + pending signal. Event has `confidence_raw = 0.80` but `confidence_effective = 0.40`. Supplies **three** `MarketFact` rows (Phase 1 would have suggested “high”). Runs `run_signal_monitor(...)`. Asserts `confidence_gate_log.gate = 'low'` and row in `digest_log`.

4. **RTL explainability (10.3)**  
   Mocks `fetch` for breakdown JSON fixture. Clicks “Why this confidence tier?” — fetch runs once on expand. Asserts labels for all five inputs, fixture detail strings, `confidence-fow-callout`, `confidence-escalation-badge`. Separate test: 404 → `confidence-breakdown-error`.

5. **Calibration doc (10.4)**  
   Operational ritual only — no scheduler or auto-tuning.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| No `SUPABASE_DB_URL` | DB integration tests **skip** (`conftest.py`); unit tests in `test_confidence_scorer.py` still run in CI. |
| Event missing | `test_confidence_breakdown_not_found` → HTTP 404. |
| FoW detection in API test | Patched `fetch_fog_active` — avoids flaky cross-pool DB visibility when seeding three `is_major` rows (see B4). |
| `sources` JSONB insert | Must use `json.dumps(sources)` — raw Python list fails psycopg adapt. |
| Collapsed panel | `global.fetch` not called until expand (P3-S1h lazy-load preserved). |

**Business rules enforced (via tests)**

| Rule | Where proven |
|------|----------------|
| `confidence_raw` = weighted sum of five inputs (G-01) | `test_confidence_breakdown_weighted_sum_matches_raw` |
| FoW: dampener on **effective** only; tier from effective (PRD2) | `test_confidence_breakdown_fow_dampens_effective_and_tier` + `test_fog_dampener_applies_to_effective_only` (scorer unit) |
| Gate tiers: HIGH ≥ 0.75, MEDIUM 0.55–0.74, LOW &lt; 0.55 (G-02) | Implicit via `route()` / `tier_from_score` in gate tests |
| Signal monitor uses `confidence_effective`, not fact count (G-02 swap) | `test_signal_monitor_routes_by_effective_score_not_fact_count` |
| Explainability shows five inputs (G-01 UI) | `ConfidenceComposition.test.tsx` |

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **New module `test_confidence_scoring_gate.py`** | Keeps P3-T3 gate in one file (mirrors P3-T2 pattern); leaves `test_confidence_breakdown_api.py` for HTTP shape/404 from S1g. | Fold all tests into breakdown API file — mixes story ownership. |
| **`monkeypatch` for FoW API test** | Seeding 3 `is_major` active events did not reliably set `fog_active` true across session `db_connection` vs app connection pool in one environment. | Only DB seed — flaky; skip FoW API test entirely — loses HTTP contract proof. |
| **Regression test uses contradicting fact count vs effective** | Clear proof Phase 1 heuristic is gone: 3 facts + effective 0.40 → low, not high. | Extend parametrized `test_signal_monitor_logs_override_decisions` only — existing cases align fact count with tier via DB scores. |
| **RTL asserts labels + detail strings** | Plan requires “all five inputs from fixture”; labels catch missing bars, details catch wrong data. | Snapshot test — heavier maintenance. |
| **`phase3-calibration.md` separate from post-impl doc** | Plan path is `docs/plans/` for operator ritual; this doc is developer handover. | Embed ritual only here — harder for PO to find. |

⚠️ **Do not change `confidence_gate.route()` tier boundaries without updating** `test_confidence_gate.py`, `test_confidence_scoring_gate.py`, and `test_signal_monitor_logs_override_decisions.py`.

⚠️ **Do not reintroduce fact-count-based gate routing in `signal_monitor_runner.py`** — P3-T3 regression test exists specifically to prevent Phase 1 behaviour.

⚠️ **Do not start P3-S1i while P3-T3 tests fail** — plan hard-dependency.

**Assumptions**

- P3-S1g breakdown endpoint and scorer are deployed in the branch under test.
- Migrations through `0027_confidence_audit.sql` (and prior) applied when integration tests run.
- `ConfidenceComposition` and `confidenceBreakdown.ts` from P3-S1h are present (T3 only extends RTL assertions).

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S1g** — scorer, gate, breakdown API, audit; **P3-S1h** — Thread panel + client; **P3-T2** — trustworthy `source_count` after dedup |
| **Downstream** | **P3-S1i** — number validator publish gate (blocked until T3 green); **P3-S1m** — override log feeds calibration doc; **P3-S2** — interaction model (Day 30+ soak per plan) |
| **Parallel** | None per plan |

**Shared components touched (tests only — no production edits)**

| Component | Role in T3 |
|-----------|------------|
| `app/services/confidence_scorer.py` | `build_confidence_breakdown_payload`, `fetch_fog_active`, `tier_from_score` |
| `app/services/confidence_gate.py` | `route(confidence_effective)` |
| `app/services/signal_monitor_runner.py` | `run_signal_monitor` gate routing |
| `app/api/events.py` | `GET .../confidence-breakdown` |
| `ConfidenceComposition.tsx` | Lazy expand + breakdown panel |
| `confidence_config.py` | `WEIGHTS`, `FOG_DAMPENER`, `THRESHOLDS` (read by tests) |

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Verification gate** — tests as executable spec (same pattern as P3-T1, P3-T2).
- **Layered proof:** unit (scorer) + HTTP (breakdown) + service integration (signal monitor) + RTL (UI).
- **TestClient + session `db_connection`** for API tests; direct `run_signal_monitor` for monitor test.

**Database schema**

- No changes in P3-T3. Tests insert/delete probe rows on `events`, `cards`, `signals`, `confidence_gate_log`, `digest_log`.

**API contracts (under test, not modified)**

| Method | Route | Auth | Cache |
|--------|-------|------|-------|
| GET | `/api/events/{event_id}/confidence-breakdown` | Same as other event reads | `Cache-Control: max-age=60` |

**UI/UX (under test)**

- Collapsible “Why this confidence tier?” — fetch on expand only.
- Five progress bars (source count, quality, factor match, recency, unique publishers).
- FoW callout when `fog_active` and effective &lt; raw.
- Editorial escalation badge when `force_editorial_review`.

**Libraries / tools**

- `pytest`, `fastapi.testclient.TestClient`, `unittest.mock` / `monkeypatch`.
- `@testing-library/react`, `user-event` (frontend).
- No new pip/npm dependencies.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `test_confidence_scoring_gate.py` | `backend/tests/test_confidence_scoring_gate.py` | P3-T3 gate: sum, FoW API, signal monitor regression |
| `phase3-calibration.md` | `docs/plans/phase3-calibration.md` | Day 30/60/monthly recalibration ritual |
| `Phase3_P3-T3 - Confidence scoring verification gate.md` | `docs/Post Implementation documentation/...` | This handover document |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `ConfidenceComposition.test.tsx` | `frontend/app/(app)/thread/_components/aside/ConfidenceComposition.test.tsx` | P3-T3: assert all five input labels + fixture detail strings |
| `test_confidence_breakdown_api.py` | `backend/tests/test_confidence_breakdown_api.py` | Docstring: notes S1g shape tests; T3 sum/FoW in scoring gate file |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-T3 acceptance criteria and tasks **10.0**–**10.5** marked complete; Riley task **10.0** checked |

**Not modified (reused from upstream stories)**

| File | Owner story |
|------|-------------|
| `confidence_scorer.py`, `confidence_gate.py`, `confidence_config.py` | P3-S1g |
| `events.py` (breakdown route) | P3-S1g |
| `ConfidenceComposition.tsx`, `confidenceBreakdown.ts` | P3-S1h |
| `.github/workflows/ci.yml` | Already runs full `backend/tests` and frontend `pnpm test` |

---

### A8. TESTS EXECUTED

#### P3-T3–primary tests

| Test | File | Status | What it verifies |
|------|------|--------|------------------|
| `test_confidence_breakdown_weighted_sum_matches_raw` | `test_confidence_scoring_gate.py` | **Pass** (integration) | Σ(value×weight) ≈ `confidence_raw` |
| `test_confidence_breakdown_fow_dampens_effective_and_tier` | `test_confidence_scoring_gate.py` | **Pass** (integration + patch) | FoW: effective = raw×0.6; tier from effective |
| `test_signal_monitor_routes_by_effective_score_not_fact_count` | `test_confidence_scoring_gate.py` | **Pass** (integration) | 3 facts + effective 0.40 → low + digest |
| `test_confidence_breakdown_shape` | `test_confidence_breakdown_api.py` | **Pass** (integration) | 200 payload shape, cache header |
| `test_confidence_breakdown_not_found` | `test_confidence_breakdown_api.py` | **Pass** | Missing event → 404 |
| `renders breakdown fixture after expand` | `ConfidenceComposition.test.tsx` | **Pass** | Five inputs, FoW, escalation, lazy fetch |
| `shows error state on 404` | `ConfidenceComposition.test.tsx` | **Pass** | Error panel on failed fetch |

#### Commands

```bash
# P3-T3 only (from repo root)
python -m pytest -q backend/tests/test_confidence_scoring_gate.py backend/tests/test_confidence_breakdown_api.py

# Frontend RTL
cd frontend && pnpm test ConfidenceComposition.test.tsx

# CI-equivalent
python -m ruff check backend
python -m pytest -q backend/tests
cd frontend && pnpm lint && pnpm typecheck
```

#### Related regression (run after touching scorer, gate, or signal monitor)

| Test file | Relevance |
|-----------|-----------|
| `test_confidence_scorer.py` | Weights, FoW unit math, synthetic ≥80% calibration |
| `test_confidence_gate.py` | Tier boundaries 0.75 / 0.55 |
| `test_signal_monitor_logs_override_decisions.py` | High/medium/low paths with tier-aligned DB scores |
| `confidenceBreakdown.test.ts` | API client parse + 404 error type |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**None in P3-T3.**

Tests use existing columns on `public.events`:

| Column | Used in |
|--------|---------|
| `confidence_raw`, `confidence_effective` | Breakdown API + signal monitor routing |
| `source_count`, `sources`, `factor_db_match_count` | Scorer input reconstruction |
| `is_major`, `lifecycle_state` | FoW detection (production; patched in one test) |

Probe rows deleted in `finally` blocks — no permanent seed data.

---

### B2. API / INTEGRATION CONTRACTS

**Endpoint under test:** `GET /api/events/{event_id}/confidence-breakdown`

**Success response (shape asserted in tests):**

```json
{
  "event_id": "uuid",
  "confidence_raw": 0.82,
  "confidence_effective": 0.492,
  "tier": "low",
  "fog_active": true,
  "fog_dampener": 0.6,
  "calibration_status": "provisional",
  "scorer_version": "confidence_scorer.v1",
  "is_major": false,
  "force_editorial_review": false,
  "inputs": {
    "source_count": { "value": 1.0, "weight": 0.3, "detail": "3 sources post-dedup" },
    "source_quality": { "value": 1.0, "weight": 0.3, "detail": "primary_source=rbi_rss" },
    "factor_db_match": { "value": 1.0, "weight": 0.25, "detail": "2 factors (...)" },
    "recency": { "value": 1.0, "weight": 0.05, "detail": "first_seen=..." },
    "unique_publisher": { "value": 1.0, "weight": 0.1, "detail": "3 publishers (domain-level)" }
  },
  "sources": [{ "name": "rbi_rss", "url": "...", "retrieved_at": "..." }]
}
```

**Weighted sum rule (verified in 10.1):**

```
confidence_raw ≈ round(clamp(Σ inputs[k].value × WEIGHTS[k], 0, 1), 3)
```

**404:** `{ "detail": { "code": "event_not_found", "message": "Event not found" } }` (client normalizes to `ConfidenceBreakdownFetchError`).

**Auth:** Same as other `/api/events/*` routes (no new permission model).

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Confidence agreement flow (what T3 proves)**

```
Event row (sources, counts, category)
  → build_scorer_input + compute_confidence (P3-S1g)
  → confidence_raw, confidence_effective, tier
  → GET /confidence-breakdown (recompute + JSON inputs)
  → ConfidenceComposition expand (fetch + render bars)

Signal fires (market facts match text)
  → evaluate(signal_text, facts)  [match quality only]
  → route(COALESCE(confidence_effective, confidence_raw))  [tier decision]
  → high / medium / low path + confidence_gate_log
```

**FoW dampening (G-01 / PRD2)**

```
if fetch_fog_active():
    effective = round(raw × 0.6, 3)
else:
    effective = raw
tier = tier_from_score(effective)   # NOT from raw
```

**Phase 1 vs Phase 3 signal routing**

| Phase | Gate input |
|-------|------------|
| Phase 1 (removed) | Implicitly fact count / match strength |
| Phase 3 (current) | `events.confidence_effective` via `route()` |

T3 regression: `fact_count=3` cannot override `effective=0.40`.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| FoW API test uses `monkeypatch` on `fetch_fog_active` | Does not integration-test DB count of `is_major` events | `test_fog_dampener_applies_to_effective_only` in `test_confidence_scorer.py`; optional future DB seed test |
| Integration tests skip in CI without `SUPABASE_DB_URL` | T3 HTTP/monitor tests may not run on every PR | Run locally before merge; add DB secret to CI for full gate |
| Session-scoped `db_connection` vs app pool | Rare visibility quirks (motivated FoW patch) | Always `commit()` before TestClient calls; `DELETE` in `finally` |
| RTL uses mocked `fetch` | Does not hit real backend | `confidenceBreakdown.test.ts` + breakdown API integration tests |

**Tech debt (optional improvements)**

- Add `test_fetch_fog_active_true_when_three_major_active_events` seeding DB without patch.
- Add `@pytest.mark.integration` to `test_confidence_scoring_gate.py` module doc.
- Parametrize epsilon / threshold edge cases (0.749 vs 0.750) in dedicated gate test module.

---

### B5. TESTING NOTES

**Automated**

| Layer | Coverage |
|-------|----------|
| Integration | Breakdown sum, FoW API (patched), signal monitor regression |
| HTTP contract | Shape + 404 (`test_confidence_breakdown_api.py`) |
| RTL | Expand/collapse, five inputs, error state |
| Unit (upstream) | Scorer weights, calibration ≥80%, gate boundaries |

**Manual (operator)**

| Step | When |
|------|------|
| Run P3-T3 pytest with `.env.local` `SUPABASE_DB_URL` | Before merge if scorer/gate/monitor changed |
| Spot-check Thread panel against live breakdown API | After S1h UI changes |
| Day 30/60 calibration per `phase3-calibration.md` | Calendar — not part of T3 delivery |

**Known gaps**

- No Playwright e2e from Thread page to real API.
- No test that stored DB `confidence_raw` on row equals API (API recomputes); test validates internal consistency of API payload.
- FoW banner on Pulse (`P3-S1l`) out of T3 scope.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required for | Notes |
|----------|--------------|-------|
| `SUPABASE_DB_URL` | `test_confidence_scoring_gate.py`, `test_confidence_breakdown_api.py` | Repo-root `.env.local` |
| _(none new)_ | Frontend RTL | Mocks `fetch`; no API URL needed |

**Deployment sequencing**

1. No migration or env changes for P3-T3 alone.
2. Merge test + doc files — deploy only if rest of branch includes S1g/S1h production code.

**Manual ops**

- None required for T3 delivery.
- Future: follow `docs/plans/phase3-calibration.md` at Day 30/60 (export logs, optional threshold PR).

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing scorer, gate, breakdown API, or signal monitor**

1. Run P3-T3 gate:
   ```bash
   python -m pytest -q backend/tests/test_confidence_scoring_gate.py backend/tests/test_confidence_breakdown_api.py
   cd frontend && pnpm test ConfidenceComposition.test.tsx
   ```
2. If you change `WEIGHTS` or `THRESHOLDS`, also run:
   ```bash
   python -m pytest -q backend/tests/test_confidence_scorer.py backend/tests/test_confidence_gate.py
   ```
3. Update `docs/plans/phase3-calibration.md` if recalibration ritual changes.

**Common mistakes**

- Inserting `sources` as Python list into psycopg — use `json.dumps(sources)`.
- Changing breakdown `inputs` keys without updating `INPUT_ORDER` in `ConfidenceComposition.tsx` and RTL fixture.
- Tuning signal paths on fact count instead of `route(confidence_effective)` — breaks T3 regression.
- Removing `monkeypatch` FoW test without replacing DB seed strategy — may cause flaky CI.

**Where to look**

| Concern | Path |
|---------|------|
| P3-T3 gate tests | `backend/tests/test_confidence_scoring_gate.py` |
| Breakdown HTTP shape | `backend/tests/test_confidence_breakdown_api.py` |
| Scorer + breakdown builder | `backend/app/services/confidence_scorer.py` |
| Gate routing | `backend/app/services/confidence_gate.py`, `signal_monitor_runner.py` |
| Config (single source of truth) | `backend/app/core/confidence_config.py` |
| Thread UI | `frontend/app/(app)/thread/_components/aside/ConfidenceComposition.tsx` |
| API client | `frontend/lib/api/confidenceBreakdown.ts` |
| Calibration ritual | `docs/plans/phase3-calibration.md` |

**Contact for context (by role)**

- **Backend confidence / gate** — Jordan per plan (P3-S1g).
- **Thread explainability UI** — Sam per plan (P3-S1h).
- **Verification gates / publish gate** — Riley per plan (P3-T3, P3-S1i).

---

## Audit checklist (story acceptance)

| Acceptance criterion | Met |
|----------------------|-----|
| API: breakdown sums match `confidence_raw` within epsilon | Yes (`test_confidence_breakdown_weighted_sum_matches_raw`) |
| FoW active: effective = raw × 0.6; tier from effective | Yes (`test_confidence_breakdown_fow_dampens_effective_and_tier` + scorer unit) |
| RTL: expanded panel shows all five inputs | Yes (`ConfidenceComposition.test.tsx`) |
| Regression: signal monitor uses new gate tiers | Yes (`test_signal_monitor_routes_by_effective_score_not_fact_count`) |
| Day 30/60 ritual documented | Yes (`docs/plans/phase3-calibration.md`) |
| CI green before P3-S1i | Yes (295 backend tests, ruff clean, frontend lint/typecheck/RTL) |
| Plan tasks 10.0–10.5 complete | Yes |

---

## Audit style — production code inventory

P3-T3 did **not** ship new production modules. Production behaviour under test was delivered in:

| Story | Production deliverables |
|-------|-------------------------|
| P3-S1g | `confidence_scorer.py`, `confidence_gate.py`, `confidence_config.py`, breakdown route, `confidence_score_audit` |
| P3-S1h | `ConfidenceComposition.tsx`, `confidenceBreakdown.ts` |
| P1-S11 | `signal_monitor_runner.py` (updated in S1g to use `route(confidence_effective)`) |

---

_Document version: v1.0 · Phase 3 · P3-T3 · G-01/G-02 verification gate · Blocks P3-S1i_
