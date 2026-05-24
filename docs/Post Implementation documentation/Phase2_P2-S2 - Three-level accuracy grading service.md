# Post Implementation Detailed Document — P2-S2

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P2-S2 (Phase 2, Story 2)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P2-S1** delivered The Mirror surface: prediction history, stats strip, three-level accuracy meters, and expandable gap-insight slots. Those meters stayed empty until a backend grader populated `user_predictions` accuracy columns and `gap_insight`.

**P2-S2** closes that loop on the server. When an ICE card’s lifecycle moves to `resolved`, the platform grades every **ungraded** prediction for that card at three independent levels — **Mechanism**, **Business Impact**, and **Market Reaction** — using only:

1. The user’s logged prediction text  
2. The immutable **Original View** (Day-1 `track_record` row with `kind = initial_publish`)  
3. The **final** card state at resolution (live `cards` row joined with event metadata)

Interim card revisions are never used as the baseline. Grading runs through the existing **Gemini** JSON client (`LlmClient.complete_json`) and a new prompt (`grading.v1.md`). Each result is validated (enum values + rejection of generic “markets are unpredictable” gap copy), written to `user_predictions`, and summarized in an append-only `track_record` row (`kind = prediction_grade`). Re-running the job on already-graded rows is a **no-op** (`mechanism_accuracy IS NULL` guard).

The editorial entry point is **`transition_card_to_resolved(card_id)`** in `backend/app/jobs/grade_on_resolve.py`. There is still **no** public HTTP “resolve card” admin route in this story; editors must call the Python hook (script/shell) until a future admin API is wired.

**Tests executed and passed (automated):**

| # | Test module | Result |
|---|-------------|--------|
| 1 | `test_prediction_grader.py` (4 cases) | Passed |
| 2 | `test_grader_uses_original_view.py` (1 integration case) | Passed |
| 3 | `test_user_predictions_gap_insight_migration.py` (1 case) | Passed |

**Command:** `cd backend && python -m pytest tests/test_prediction_grader.py tests/test_grader_uses_original_view.py tests/test_user_predictions_gap_insight_migration.py -q` → **6 passed**

**Three anchors for handover:** (1) **`fetch_track_record_initial_publish`** is the only Original View source — never grade from live card alone; (2) **`transition_card_to_resolved`** is how cards enter the graded path today; (3) **idempotency** — rows with `mechanism_accuracy` set are skipped on re-run.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S2 |
| **Title** | The Mirror — three-level accuracy grading service |
| **Category** | **Backend** (services, DB migration, background job hook; no new public Mirror HTTP routes) |

**What this story aimed to achieve (plain language)**

When a published ICE card is marked resolved, FinnWise should automatically score each user’s logged prediction on three separate learning dimensions and write a specific “reasoning gap” paragraph. Users see an honest split rating in The Mirror (mechanism vs business vs market) instead of one misleading overall score or vague disclaimers.

**How it fits into the overall application**

- **Phase 1** created `user_predictions`, append-only `track_record`, and the `initial_publish` snapshot at card publish.  
- **P2-S1** built The Mirror UI and read APIs that *display* grades when present.  
- **P2-S2** *produces* those grades.  
- **P2-S3** (notifications) and **P2-S4** (reasoning-gap analysis / Map links) consume graded data and `gap_insight` downstream.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

#### Sub-stories covered

| Sub-task | What it does |
|----------|----------------|
| **2.1** | DB: add `gap_insight` column (`0014` migration; accuracy columns already in `0004`) |
| **2.2** | Author `grading.v1.md` — per-level rubric + forbidden generic gap phrases |
| **2.3** | `prediction_grader.grade()` — LLM call + JSON validation |
| **2.4** | `grade_on_resolve` — hook on transition to `resolved` |
| **2.5** | Persist three accuracy fields + `gap_insight` + append `track_record` grade row |
| **2.6** | Idempotency — skip predictions already graded |
| **2.7** | Pytest: unit grader, Original View source, integration idempotency |

#### Functional breakdown — grading pipeline

```
Editorial / future admin: transition_card_to_resolved(card_id)
│
├─ UPDATE cards.lifecycle_state → 'resolved'
│     (from: published | active | signal_triggered | thesis_confirmed | thesis_weakened)
│
└─ grade_predictions_for_card(card_id)
      │
      ├─ Require card.lifecycle_state == 'resolved'
      ├─ Load original_publish = fetch_track_record_initial_publish(card_id)
      │     └── FAIL if missing (card never published with snapshot)
      ├─ Load final_card = fetch_card_detail_for_review(card_id)
      │
      └─ FOR EACH user_predictions WHERE mechanism_accuracy IS NULL:
            ├─ grade(prediction_text, original_publish, final_card)  [Gemini JSON]
            ├─ parse_grade_payload() — enums + gap_insight quality
            ├─ UPDATE user_predictions (3 accuracy cols + gap_insight)
            └─ INSERT track_record { kind: prediction_grade, ... }
```

#### Functional breakdown — single prediction grade (LLM)

```
build_grading_user_payload()
  → JSON: { user_prediction, original_view (ice_snapshot), final_card_state }

render_prompt(grading.v1.md, { grading_payload })
  → system + user sent to LlmClient.complete_json(prompt_version=grading.v1)

parse_grade_payload()
  → GradeResult(mechanism_accuracy, business_accuracy, market_accuracy, gap_insight)
```

#### Edge cases, validations, and error handling

| Scenario | Behaviour |
|----------|-----------|
| Card not found | `LookupError` from `grade_predictions_for_card` / `transition_card_to_resolved` |
| Card not `resolved` | `ValueError("card_must_be_resolved")` |
| No `initial_publish` snapshot | `ValueError("original_publish_snapshot_missing")` |
| LLM returns invalid enum | `GradingQualityError` from `parse_grade_payload` |
| Generic gap insight (“markets are unpredictable”, etc.) | `GradingQualityError` — rejected before persist |
| `gap_insight` &lt; 24 chars | `GradingQualityError` |
| Re-run on graded row | SELECT filters `mechanism_accuracy IS NULL`; UPDATE rowcount 0 → skip |
| Card already `resolved`, call `transition_card_to_resolved` again | Lifecycle update no-op; grading still runs but grades 0 if all done |
| Resolve from `draft` / `archived` | `ValueError("card_not_resolvable_from_{state}")` |

#### Business rules enforced

| Rule | Implementation |
|------|----------------|
| Three independent levels | Separate fields + rubric sections in `grading.v1.md` |
| Allowed grades | `correct`, `partial`, `incorrect`, `monitoring` |
| Original View only for baseline | `original_view` = `initial_publish.ice_snapshot` in payload |
| No generic gap explanations | `_GENERIC_GAP_MARKERS` blocklist in `prediction_grader.py` |
| Append-only audit | `track_record` INSERT per grade; table remains non-deletable |
| PRD §5 Screen 4 | Split ratings + specific gap text (not single score) |

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Why | Alternatives considered |
|----------|-----|-------------------------|
| **Gemini via `LlmClient`** | Same stack as P1-S7 card pipeline; one API key, retries, JSON mode | Task note mentioned Sonnet; not in current codebase |
| **Migration `0014` for `gap_insight` only** | `mechanism_accuracy` / `business_accuracy` / `market_accuracy` already in `0004_core_tables.sql`; `0010` filename taken by signal monitoring | New `0010_user_predictions_accuracy_cols.sql` per plan table |
| **`transition_card_to_resolved` as public hook** | No editorial resolve HTTP API in scope | DB trigger on lifecycle (harder to test); cron batch |
| **Idempotency via `mechanism_accuracy IS NULL`** | All three levels written atomically in one UPDATE | Separate `graded_at` column (deferred) |
| **Post-LLM validation** | Enforce PRD anti-generic-gap rule even if model drifts | Trust model output only |

**Assumptions**

- Cards that reach `resolved` were previously published and have an `initial_publish` `track_record` row (P1-S8 publish path).
- Editorial resolve is infrequent enough that synchronous LLM grading per prediction is acceptable for now.

⚠️ **Critical — do not reverse without review**

- **Never grade using only the live card** as the “original” baseline. Always use `fetch_track_record_initial_publish`.
- **Do not DELETE `track_record` rows** in tests or ops — append-only triggers deny DELETE (see `0005_track_record_append_only.sql`).

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / components |
|-----------|----------------------|
| **Upstream** | P1-S4 schema, P1-S8 `publish_card` → `initial_publish`, P1-S10 Original View read path, P1-S12 `predictions.log`, P2-S1 Mirror list/stats APIs |
| **Downstream** | P2-S3 `card_graded` notifications, P2-S4 reasoning-gap detector + Map links, Mirror `AccuracyMeter` / `GapInsightExpanded` / `StatsStrip` |
| **Shared touchpoints** | `user_predictions`, `track_record`, `cards.lifecycle_state`, `card_repository.fetch_track_record_initial_publish`, `mirror_predictions` / `mirror_stats` |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Service (`prediction_grader`) + job module (`grade_on_resolve`); injectable LLM protocol for tests |
| **Database** | One new nullable `text` column: `user_predictions.gap_insight` |
| **API contracts** | No new public routes in P2-S2; Mirror continues `GET /api/mirror/predictions` and `/stats` (P2-S1) |
| **UI/UX** | None in this story; P2-S1 UI already renders grades when populated |
| **Third-party** | Google Gemini (`GEMINI_API_KEY` / `GEMINI_MODEL` via `app.core.settings`) |

**`track_record` grade payload shape**

```json
{
  "kind": "prediction_grade",
  "user_id": "<uuid>",
  "prediction_id": "<uuid>",
  "mechanism_accuracy": "correct|partial|incorrect|monitoring",
  "business_accuracy": "...",
  "market_accuracy": "...",
  "gap_insight": "<plain English>",
  "prompt_version": "grading.v1",
  "source": "grade_on_resolve"
}
```

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| grading.v1.md | `backend/prompts/grading.v1.md` | Three-level rubric + output schema + forbidden gap phrases |
| prediction_grader.py | `backend/app/services/prediction_grader.py` | `grade()`, `parse_grade_payload()`, payload builder |
| grade_on_resolve.py | `backend/app/jobs/grade_on_resolve.py` | Resolve lifecycle + grade + persist + track_record append |
| 0014_user_predictions_gap_insight.sql | `backend/db/migrations/0014_user_predictions_gap_insight.sql` | Adds `gap_insight` column |
| test_prediction_grader.py | `backend/tests/test_prediction_grader.py` | Unit tests for parser + LLM wiring |
| test_grader_uses_original_view.py | `backend/tests/test_grader_uses_original_view.py` | DB integration: Original View vs final, idempotency |
| test_user_predictions_gap_insight_migration.py | `backend/tests/test_user_predictions_gap_insight_migration.py` | Migration SQL smoke test |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| migrate.py | `backend/app/db/migrate.py` | Registered `0014_user_predictions_gap_insight.sql` in `MIGRATION_FILES` |
| mirror_predictions.py | `backend/app/services/mirror_predictions.py` | `SELECT up.gap_insight` in list + stats queries (was hardcoded `None`) |

---

### A8. TESTS EXECUTED

| Test file | Test name / scope | Status | What was verified |
|-----------|-------------------|--------|-------------------|
| `test_prediction_grader.py` | `test_parse_grade_payload_accepts_valid` | **Passed** | Valid enums + gap insight accepted |
| `test_prediction_grader.py` | `test_parse_grade_payload_rejects_generic_gap` | **Passed** | “Markets are unpredictable” rejected |
| `test_prediction_grader.py` | `test_grade_uses_llm_and_validates_output` | **Passed** | Fake LLM; Original marker in user prompt |
| `test_prediction_grader.py` | `test_build_grading_payload_includes_original_ice_not_only_final_title` | **Passed** | Payload separates `original_view` vs `final_card_state` |
| `test_grader_uses_original_view.py` | `test_grade_on_resolve_idempotent_and_uses_original_view` | **Passed** | DB: resolve → grade → Original vs LIVE insight; second run grades 0; `track_record` grade row count |
| `test_user_predictions_gap_insight_migration.py` | `test_migration_adds_gap_insight_column` | **Passed** | Migration file contains `gap_insight` + `user_predictions` |

**Not run in CI by this story:** live Gemini end-to-end against production API (tests use injectable fake LLM).

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Table:** `public.user_predictions`

| Column | Type | Notes |
|--------|------|--------|
| `mechanism_accuracy` | `text` | Already in `0004`; values: correct / partial / incorrect / monitoring |
| `business_accuracy` | `text` | Same |
| `market_accuracy` | `text` | Same |
| `gap_insight` | `text` | **Added in `0014`** — plain-English reasoning gap |

**Migration sequencing:** Run after `0013_tester_acceptances.sql`. Registered in `backend/app/db/migrate.py` as `0014_user_predictions_gap_insight.sql`.

```sql
ALTER TABLE public.user_predictions
  ADD COLUMN IF NOT EXISTS gap_insight text;
```

**No seed data** introduced.

---

### B2. API / INTEGRATION CONTRACTS

**No new HTTP endpoints** in P2-S2.

Existing Mirror consumers (P2-S1) already expose graded fields when populated:

| Method | Route | Graded fields in response |
|--------|-------|---------------------------|
| GET | `/api/mirror/predictions` | `mechanism_accuracy`, `business_accuracy`, `market_accuracy`, `gap_insight` |
| GET | `/api/mirror/stats` | Aggregates from graded rows (`mirror_stats.compute`) |

**Programmatic integration (editorial / ops)**

```python
from uuid import UUID
from app.jobs.grade_on_resolve import transition_card_to_resolved

# Resolves lifecycle + grades all ungraded predictions for the card
result = transition_card_to_resolved(UUID("<card-id>"))
# → {"card_id": "...", "graded": <int>}
```

Auth: not applicable to Python hook; future admin route should use existing admin patterns (`/api/admin/...`).

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Resolvable lifecycle states** (can transition to `resolved`):

- `published`, `active`, `signal_triggered`, `thesis_confirmed`, `thesis_weakened`

**Grading eligibility**

- Card `lifecycle_state == resolved`
- `track_record` has `initial_publish` for `card_id`
- `user_predictions.mechanism_accuracy IS NULL`

**Accuracy semantics (per level)**

| Value | Meaning |
|-------|---------|
| `correct` | Aligned with outcome vs Original View + final state |
| `partial` | Right direction, wrong emphasis/timing/magnitude |
| `incorrect` | Wrong read at that level |
| `monitoring` | Outcome not yet fairly judgeable (use sparingly) |

**Stats strip (P2-S1)** treats only `correct` / `partial` / `incorrect` as “graded” for percentage; `monitoring` excluded from pct denominator (`mirror_stats._graded_values`).

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Impact |
|------------|--------|
| **No admin HTTP “resolve card” endpoint** | Editors cannot resolve from UI yet; must use Python hook or SQL + manual grade call |
| **Synchronous LLM per prediction** | Many users × one card = multiple Gemini calls on resolve; may need queue/batch later |
| **No CHECK constraint on accuracy enums** | Invalid values prevented in app layer only |
| **Plan referenced Sonnet** | Implemented with Gemini to match Phase 1 |

⚠️ **Tech debt:** Add `POST /api/admin/cards/{id}/resolve` calling `transition_card_to_resolved` when editorial workflow is ready.

---

### B5. TESTING NOTES

| Coverage | Automated | Manual (recommended) |
|----------|-----------|----------------------|
| Payload parsing / generic gap rejection | Yes | — |
| Original View in LLM input | Yes (fake LLM + integration) | — |
| Idempotency | Yes (integration) | — |
| Live Gemini quality on real card | No | Resolve one test card; inspect Mirror meters + gap copy |
| Migration on staging/prod DB | No | Run `apply_migrations.py` once per environment |
| Mirror UI with real grades | No | Open `/mirror` after resolving a card you predicted on |

**Known gap:** No test for missing `GEMINI_API_KEY` failure path in production deploy checklist.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required for live grading | Notes |
|----------|---------------------------|--------|
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | **Yes** | `LlmClient` raises if unset |
| `GEMINI_MODEL` | No (default `gemini-2.0-flash`) | Optional override |
| `SUPABASE_DB_URL` | **Yes** | For migration + grading persistence |

**Deployment sequencing**

1. Deploy backend code (includes migration file + grader).  
2. Run migrations on target database **before** first resolve in that environment.  
3. Confirm `GEMINI_API_KEY` on Render (or local `.env.local` for dev).  
4. Resolve a card via `transition_card_to_resolved` to validate end-to-end.

**Feature toggles:** None.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing this code**

1. Read PRD §5 Screen 4 (three levels, no rupee figures, specific gap insights).  
2. Read `backend/prompts/grading.v1.md` before editing rubric wording.  
3. Understand append-only `track_record` — never add DELETE cleanup in tests against shared DB.

**Common mistakes**

- Grading from live `cards.insight_layer` as “original” — **wrong**; use `fetch_track_record_initial_publish`.  
- Expecting grades on cards that never went through `publish_draft_card` (no `initial_publish`).  
- Deleting `track_record` rows in integration tests — triggers `InsufficientPrivilege`.

**Where to look**

| Concern | Path |
|---------|------|
| Grader logic | `backend/app/services/prediction_grader.py` |
| Resolve + persist | `backend/app/jobs/grade_on_resolve.py` |
| Original View fetch | `backend/app/services/card_repository.py` → `fetch_track_record_initial_publish` |
| Mirror read API | `backend/app/api/mirror.py`, `backend/app/services/mirror_predictions.py` |
| Prompt | `backend/prompts/grading.v1.md` |

**Context by role:** Jordan (grading service owner); Sam (Mirror UI — displays grades); Riley (P2-S3 notifications, P2-S4 gap analysis).

---

## Manual actions checklist (operator)

Use this after pulling P2-S2 code:

| Step | Action | Required? |
|------|--------|-----------|
| 1 | **Run migration `0014`** on each environment DB: from repo root, `python scripts/apply_migrations.py` (needs `SUPABASE_DB_URL` in `.env.local`) | **Yes — once per env** |
| 2 | **Confirm `GEMINI_API_KEY`** on Render backend (and locally if testing live grading) | **Yes for live LLM grades** |
| 3 | **Deploy backend** with new code before resolving cards in prod | **Yes** |
| 4 | **Resolve a card** to trigger grading — today via Python (`transition_card_to_resolved`) or a script; **no admin UI button yet** | **Yes to see grades in Mirror** |
| 5 | **Verify in Mirror** (`/mirror`): expanded card shows three meters + gap insight for a card you predicted on | Recommended smoke test |
| 6 | Frontend redeploy | **Not required** for P2-S2 (backend-only); P2-S1 UI already reads graded fields |

**You do not need to:** change `.env.local` for new variables (unless `GEMINI_API_KEY` was already missing), run frontend build, or manually ALTER accuracy columns (they exist from Phase 1).
