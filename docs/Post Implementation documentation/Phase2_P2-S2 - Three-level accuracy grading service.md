# Post Implementation Detailed Document — P2-S2

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P2-S2 (Phase 2, Story 2)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P2-S1** shipped The Mirror UI and read APIs, but accuracy meters stayed empty until a grader ran. **P2-S2** adds the backend grading pipeline: when a card moves to `resolved`, every ungraded `user_predictions` row for that card is scored at three independent levels (Mechanism / Business Impact / Market Reaction) using the immutable Day-1 **Original View** (`track_record` `initial_publish`) plus the live card at resolution — never interim revisions.

Grading uses the existing **Gemini** JSON client (`LlmClient.complete_json`) with a new `grading.v1.md` rubric. Outputs are validated (enum sets + anti-generic gap phrases), persisted on `user_predictions`, and summarized in append-only `track_record` rows (`kind=prediction_grade`). The job is idempotent: rows with `mechanism_accuracy` already set are skipped.

**Tests executed and passed:** 6 pytest cases across `test_prediction_grader.py`, `test_grader_uses_original_view.py`, and `test_user_predictions_gap_insight_migration.py`.

**Three anchors:** (1) **`fetch_track_record_initial_publish`** is the only Original View source; (2) **`transition_card_to_resolved`** is the editorial hook (future admin API can call it); (3) **re-run grading is a no-op** when accuracy columns are populated.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S2 |
| **Title** | The Mirror — three-level accuracy grading service |
| **Category** | **Backend** (services, migration, job; no new public HTTP routes) |

**What this story aimed to achieve**

Automatically score each logged user prediction on three learning dimensions when an ICE card resolves, and write a specific reasoning-gap paragraph — not a single blended score and not generic market disclaimers.

**How it fits into the overall application**

P2-S1 displays grades in Mirror UI; P2-S2 produces them. P2-S3 (notifications) and P2-S4 (reasoning-gap analysis) depend on graded rows and `gap_insight`.

---

### A2. LOWER LEVEL DETAILS

| Sub-task | Delivered |
|----------|-----------|
| **2.1** | Migration `0014_user_predictions_gap_insight.sql` (accuracy cols already in `0004`) |
| **2.2** | `backend/prompts/grading.v1.md` |
| **2.3** | `prediction_grader.grade()` + `parse_grade_payload()` validation |
| **2.4** | `grade_on_resolve.transition_card_to_resolved()` + `grade_predictions_for_card()` |
| **2.5** | UPDATE `user_predictions` + INSERT `track_record` grade summary |
| **2.6** | Skip rows where `mechanism_accuracy IS NOT NULL` |
| **2.7** | Unit + integration pytest coverage |

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Gemini, not Sonnet** | Matches Phase 1 `LlmClient`; task tech note mentioned Sonnet but stack is Gemini. |
| **Migration `0014` not `0010`** | `0010` already used for signal monitoring; only `gap_insight` was missing. |
| **`transition_card_to_resolved` export** | No admin resolve API yet; hook is callable from future editorial endpoint. |
| **Idempotency via `mechanism_accuracy IS NULL`** | Simple, index-friendly; all three levels set atomically. |

⚠️ Do not grade from live card alone — always pass `initial_publish` ice_snapshot as Original View.

---

### A4. APPLICATION LINKAGE SUMMARY

- **Upstream:** P1-S4 schema, P1-S8 publish snapshot, P1-S12 predictions, P2-S1 mirror read APIs.
- **Downstream:** P2-S3 notifications on grade, P2-S4 gap analysis, Mirror `GapInsightExpanded` (already reads `gap_insight`).

---

### A5. DESIGN CHOICES

- **Prompt:** Markdown with `{{grading_payload}}` JSON blob (user prediction + original_view + final_card_state).
- **Validation:** Post-LLM `parse_grade_payload` enforces enums and rejects generic gap phrases.
- **Track record:** Append-only `prediction_grade` payload per graded prediction.

---

### A6. FILES CREATED

| File | Path | Purpose |
|------|------|---------|
| grading.v1.md | `backend/prompts/grading.v1.md` | Rubric |
| prediction_grader.py | `backend/app/services/prediction_grader.py` | Grader service |
| grade_on_resolve.py | `backend/app/jobs/grade_on_resolve.py` | Resolve hook + persistence |
| 0014 migration | `backend/db/migrations/0014_user_predictions_gap_insight.sql` | `gap_insight` column |
| test_prediction_grader.py | `backend/tests/test_prediction_grader.py` | Unit tests |
| test_grader_uses_original_view.py | `backend/tests/test_grader_uses_original_view.py` | Integration + idempotency |
| test_user_predictions_gap_insight_migration.py | `backend/tests/test_user_predictions_gap_insight_migration.py` | Migration smoke |

---

### A7. FILES MODIFIED

| File | Path | What changed |
|------|------|--------------|
| migrate.py | `backend/app/db/migrate.py` | Register `0014` |
| mirror_predictions.py | `backend/app/services/mirror_predictions.py` | SELECT `gap_insight` for list + stats |

---

### A8. TESTS EXECUTED

| Test file | Status | What it covers |
|-----------|--------|----------------|
| `test_prediction_grader.py` | **Passed** | Payload parsing, generic gap rejection, LLM wiring |
| `test_grader_uses_original_view.py` | **Passed** | Original vs final insight in grader input; DB idempotency |
| `test_user_predictions_gap_insight_migration.py` | **Passed** | Migration SQL contains `gap_insight` |

**Command:** `python -m pytest tests/test_prediction_grader.py tests/test_grader_uses_original_view.py tests/test_user_predictions_gap_insight_migration.py -q` → **6 passed**

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE CHANGES

```sql
ALTER TABLE public.user_predictions ADD COLUMN IF NOT EXISTS gap_insight text;
```

`mechanism_accuracy`, `business_accuracy`, `market_accuracy` already exist on `user_predictions` from `0004_core_tables.sql`.

### B2. OPERATIONAL NOTES

- Call `transition_card_to_resolved(card_id)` from editorial tooling when an event concludes.
- Requires `GEMINI_API_KEY` for live grading; tests use injectable fake LLM.
- Apply migration via `apply_migrations()` before deploy.
