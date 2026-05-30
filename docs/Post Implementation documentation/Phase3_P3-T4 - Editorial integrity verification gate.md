# Post Implementation Detailed Document — P3-T4

**Version:** v1.0 | **Date:** 31-05-2026  
**Story ID:** P3-T4 (Phase 3, Test gate 4)  
**PRD2 gaps:** G-07 (number validator), G-09 (section regen), G-15 (editorial checklist)  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **14.0**–**14.5**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §8 (editorial integrity)  
**Upstream handover:**  
- `docs/Post Implementation documentation/Phase3_P3-S1i - Number validator hard publish gate.md`  
- `docs/Post Implementation documentation/Phase3_P3-S1j - Editorial checklist 4 automated plus 1 manual.md`  
- P3-S1k section regen (`card_regen.py`, `RegenSection.tsx` — plan task **13.0**)

---

## Narrative style (read this first)

Phase 3 shipped three editorial hard gates in sequence: **P3-S1i** (number validator blocks publish on ungrounded numerics), **P3-S1j** (four automated checklist items + one manual plain-English tick), and **P3-S1k** (targeted section regen with post-regen validator re-run). Each story had unit and integration tests, but nothing proved they **work together end-to-end** before the next milestone — **P3-S1l** (Fog of War `is_major` + banner) — starts changing confidence routing.

**P3-T4** closes that gap. It adds:

1. **Backend E2E integration** — `test_editorial_integrity_e2e.py` seeds draft cards, exercises `GET /api/admin/cards/{id}` and `POST /api/admin/cards/{id}/publish`, and proves publish is blocked until Evidence grounds numbers and all four automated checklist items pass.
2. **Happy-path publish proof** — fix Evidence in DB → validator PASS → auto checklist PASS → reject without `plain_english_confirmed` → confirm → HTTP 200 + `lifecycle_state: published`.
3. **Regen bypass regression** — section regen that introduces ungrounded content cannot reach publish; the publish hard gate still returns 422 with `number_validator_failed`.
4. **Go/no-go evidence** — `docs/plans/phase3-go-no-go.md` links T4 test commands for P3-S8 launch-readiness.

This story adds **no new migrations, API routes, or production services** — only tests and documentation. The publish-button disable UX was already delivered in P3-S1j and is referenced via existing RTL tests.

**Tests executed and passed (P3-T4–specific):**

| Suite | Command | Result |
|-------|---------|--------|
| Editorial integrity E2E | `python -m pytest -q backend/tests/test_editorial_integrity_e2e.py` | **3 passed** (integration; requires `SUPABASE_DB_URL`) |
| ChecklistPanel RTL | `pnpm test ChecklistPanel.test.tsx` (from `frontend/`) | **3 passed** |
| PublishGate RTL | `pnpm test PublishGate.test.tsx` (from `frontend/`) | **4 passed** |
| **P3-T4 combined (recommended)** | pytest command above + both RTL suites | **10 passed** |
| Full backend regression (post-T4) | `python -m ruff check backend` + `python -m pytest -q backend/tests` | **323 passed**, ruff clean |
| Frontend RTL (related) | `pnpm test ChecklistPanel.test.tsx PublishGate.test.tsx` | **7 passed** |

**Three anchors for handover:** (1) **Do not start P3-S1l while P3-T4 is red** — FoW changes confidence routing; editorial integrity must stay proven. (2) **Publish route is `/api/admin/cards/{id}/publish`**, not `/api/cards/{id}/publish` — live editorial UI is `/admin/review`, not `(app)/editor/cards`. (3) **Do not add a publish override endpoint** — P3-T4 assumes no escape hatch around validator + checklist; regen test patches synthesis guard only to prove publish hard gate, not to weaken production regen.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-T4 |
| **Title** | Editorial integrity verification gate |
| **Category** | **Full Stack** (backend E2E integration tests + existing frontend RTL; no new production code) |
| **Points / owner (plan)** | 2 · Jordan |
| **Depends on** | P3-S1i (number validator), P3-S1j (editorial checklist), P3-S1k (section regen) |
| **Parallel with** | _None_ |
| **Blocks** | **P3-S1l** (FoW `is_major` + banner) |

**What this story aimed to achieve (plain language)**

The platform needs automated proof that a draft card **cannot be published** until every quantitative claim is grounded in Evidence, all four automated editorial checks pass, and the editor confirms plain English. Section regen must not create a loophole: if regen leaves the card in a failing validator state, publish must still return 422. P3-T4 makes those failures **CI-visible** before FoW work changes how confidence is routed on the feed.

**How it fits into the overall application**

- **Upstream:** P3-S1i (`number_validator.py`, publish hard stop); P3-S1j (`editorial_checklist.py`, `ChecklistPanel.tsx`, `PublishGate.tsx`); P3-S1k (`card_regen.py`, post-regen `_run_post_checks`).
- **This story:** Executable acceptance gate for G-07/G-09/G-15 working together across admin review API and publish flow.
- **Downstream:** P3-S1l (FoW banner + `confidence_effective` dampening); P3-T5 (FoW + signal test gate after S1l/S1m); P3-S8 go/no-go checklist cites T4 evidence.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **14.1** | E2E fixture: ungrounded `99.9%` in Insight → GET shows validator/checklist FAIL → publish 422. |
| **14.2** | E2E happy path: update Evidence → auto PASS → reject without plain English → confirm → publish 200. |
| **14.3** | Regen insight with ungrounded number → post-check FAIL → publish still 422. |
| **14.4** | Tests run in CI via full `pytest backend/tests` (no workflow change required). |
| **14.5** | T4 evidence linked in `docs/plans/phase3-go-no-go.md` and `phase3-calibration.md`. |

**Functional breakdown**

1. **Ungrounded number blocked (14.1)**  
   Inserts draft `events` + `cards` row. Insight cites `99.9% certainty [JUDGED]`; Evidence markdown omits `99.9%`. Calls `GET /api/admin/cards/{card_id}`. Asserts `number_validation.status == "FAIL"`, checklist item `numbers` is FAIL, `all_automated_pass == false`. Posts publish with `plain_english_confirmed: true` anyway — still **422** with `code: number_validator_failed` (validator runs before checklist at publish time).

2. **Evidence fix → publish (14.2)**  
   Same failing fixture. Confirms publish 422. Updates `cards.evidence_layer` via SQL to include `analyst consensus at 99.9% certainty` in markdown and sources. Re-GET: validator PASS, four automated checklist items PASS. Posts publish with `plain_english_confirmed: false` → **422** `publish_rejected`. Posts with `plain_english_confirmed: true` → **200**, `lifecycle_state: published`. Verifies card row is published on subsequent GET.

3. **Regen cannot bypass publish gate (14.3)**  
   Starts from grounded card (`-4` sensitivity in Insight + matrix Evidence). Patches `validate_numbers_in_evidence` to no-op (simulates bad content persisting past synthesis guard). Calls `regenerate_section(..., llm=_BadInsightLlm())` which writes Insight with ungrounded `99.9%`. Asserts `post_check.number_validation.status == "FAIL"`. GET admin card confirms FAIL. Publish with plain English confirmed → **422** `number_validator_failed`.

4. **UI publish button (referenced, not new in T4)**  
   `ChecklistPanel.test.tsx` proves Publish stays disabled until automated checks pass and plain-English checkbox is ticked; disabled when validator or checklist FAIL even if checkbox ticked.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| No `SUPABASE_DB_URL` | E2E tests **skip** (`conftest.py`); unit tests in `test_editorial_checklist.py`, `test_publish_gate.py` still run in CI. |
| Publish with plain English but failing validator | 422 `number_validator_failed` — plain English does not override. |
| Publish with passing validator/checklist but no plain English | 422 `publish_rejected` — server-side `PublishCardError`. |
| Successful publish creates `track_record` | Append-only — test cleanup **does not** DELETE from `track_record`; deletes card/event only (matches `test_publish_writes_track_record.py` pattern). |
| Regen synthesis guard | Production `validate_numbers_in_evidence` normally blocks ungrounded LLM output during regen; T4 patches it to test publish hard gate in isolation. |
| Context step numbers (`1.`, `2.`) | Excluded from numeric extraction per S1i — not exercised in T4 fixtures. |

**Business rules enforced (via tests)**

| Rule | Where proven |
|------|----------------|
| Ungrounded numerics block publish (G-07) | `test_ungrounded_number_blocks_publish_with_422` |
| Checklist item 1 mirrors number validator (G-15) | Same test — `numbers` item FAIL when validator FAIL |
| Four automated items must PASS before publish (G-15) | `test_happy_path_evidence_fix_checklist_then_publish_200` |
| Plain English requires explicit server confirmation | Happy path — 422 without `plain_english_confirmed` |
| Section regen post-check runs validator (G-09) | `test_section_regen_cannot_bypass_validator` — `post_check.number_validation` |
| Publish hard gate is final authority after regen | Same test — 422 on publish after bad regen |
| UI Publish button disabled when gates fail | `ChecklistPanel.test.tsx` |

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **New module `test_editorial_integrity_e2e.py`** | Single file for P3-T4 gate (mirrors P3-T2/T3); leaves `test_publish_gate.py` as S1i-focused unit/integration. | Extend `test_publish_gate.py` only — mixes story ownership and misses regen path. |
| **Evidence fix via SQL UPDATE in 14.2** | Plan AC says “fix Evidence”; simulates editor updating Evidence layer without new PATCH endpoint. | New admin PATCH route — out of scope for test gate. |
| **Patch `validate_numbers_in_evidence` in 14.3** | Production regen already blocks ungrounded synthesis; patch proves publish gate even if bad content persisted. | Expect regen to fail with ValueError — would not test publish path. |
| **Reference existing RTL instead of new Playwright** | Plan lists backend E2E file; S1j already has ChecklistPanel/PublishGate RTL. | Playwright `/admin/review` — deferred; noted in B5 gaps. |
| **`phase3-go-no-go.md` draft for 14.5** | P3-S8 will expand; T4 links evidence now per plan task 14.5. | Wait for P3-S8 — would leave T4 without traceability. |

⚠️ **Do not add a publish override or admin bypass endpoint** — P3-T4 and SEBI integrity posture assume no escape hatch.

⚠️ **Do not re-manualise automated checklist items** — G-15 and P3-T4 assume four auto + one manual; weakening checklist breaks T4 happy path.

⚠️ **Do not start P3-S1l while P3-T4 tests fail** — plan hard-dependency.

⚠️ **Do not DELETE from `track_record` in test cleanup** — table is append-only (`deny_track_record_mutation` trigger).

**Assumptions**

- P3-S1i, S1j, S1k production code is deployed on the branch under test.
- Admin review routes mounted at `/api/admin` (`admin_review.py`).
- Migrations through card regen history (e.g. `0028_card_regen_history.sql`) applied when integration tests run.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S1i** — `number_validator.py`, `publish_card.py` hard stop; **P3-S1j** — `editorial_checklist.py`, checklist UI; **P3-S1k** — `card_regen.py`, post-regen checks; **P3-T3** — confidence gate green before S1i |
| **Downstream** | **P3-S1l** — FoW `is_major` (blocked until T4 green); **P3-T5** — FoW + signal gate; **P3-S8** — go/no-go cites T1–T5 evidence |
| **Parallel** | None per plan |

**Shared components touched (tests only — no production edits in T4)**

| Component | Role in T4 |
|-----------|------------|
| `app/services/publish_card.py` | `publish_draft_card` — validator → checklist → plain English |
| `app/services/number_validator.py` | `check_card`, grounding rules |
| `app/services/editorial_checklist.py` | `check_card`, `assert_automated_pass` |
| `app/services/card_regen.py` | `regenerate_section`, `_run_post_checks` |
| `app/api/admin_review.py` | `GET/POST .../cards/{id}`, publish body |
| `ChecklistPanel.tsx` / `PublishGate.tsx` | Publish button disable logic (RTL) |

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Verification gate** — tests as executable spec (same pattern as P3-T1, T2, T3).
- **Layered proof:** unit (S1i/S1j) + publish integration (`test_publish_gate.py`) + **full editorial E2E** (T4) + RTL (UI disable).
- **TestClient + session `db_connection`** for HTTP tests; direct `regenerate_section` for regen test with injected LLM mock.

**Database schema**

- No changes in P3-T4. Tests insert/delete probe rows on `events`, `cards`. Published happy path leaves orphan `track_record` row (append-only — acceptable for pytest fixtures).

**API contracts (under test, not modified)**

| Method | Route | Purpose in T4 |
|--------|-------|----------------|
| GET | `/api/admin/cards/{card_id}` | Returns `number_validation` + `editorial_checklist` on load |
| POST | `/api/admin/cards/{card_id}/publish` | Body: `{ editor_review_seconds?, plain_english_confirmed }` |

**Publish error codes (asserted)**

| HTTP | `detail.code` | When |
|------|---------------|------|
| 422 | `number_validator_failed` | Ungrounded numerics |
| 422 | `editorial_checklist_failed` | Automated checklist fail (not primary T4 path) |
| 422 | `publish_rejected` | Missing `plain_english_confirmed` |

**UI/UX (under test via existing RTL)**

- Four automated PASS/FAIL badges on checklist load.
- Manual plain-English checkbox — only way to enable Publish when auto checks pass.
- `PublishGate` panel shows validator FAIL details (ungrounded diff).
- Publish button `data-testid="publish-draft-btn"` disabled when `canPublish` is false.

**Libraries / tools**

- `pytest`, `fastapi.testclient.TestClient`, `unittest.mock.patch`.
- `@testing-library/react` (ChecklistPanel, PublishGate — upstream S1j).
- No new pip/npm dependencies.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `test_editorial_integrity_e2e.py` | `backend/tests/test_editorial_integrity_e2e.py` | P3-T4 gate: ungrounded block, happy path, regen bypass |
| `phase3-go-no-go.md` | `docs/plans/phase3-go-no-go.md` | Draft P3-S8 checklist with T1–T5 CI evidence (T4 linked) |
| `Phase3_P3-T4 - Editorial integrity verification gate.md` | `docs/Post Implementation documentation/...` | This handover document |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `phase3-calibration.md` | `docs/plans/phase3-calibration.md` | Added T4 rows to Related CI tests table |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-T4 acceptance criteria and tasks **14.0**–**14.5** marked complete |

**Not modified (reused from upstream stories)**

| File | Owner story |
|------|-------------|
| `publish_card.py`, `number_validator.py` | P3-S1i |
| `editorial_checklist.py`, `sebi_compliance_scan.py` | P3-S1j |
| `card_regen.py`, `consistency_check.py` | P3-S1k |
| `admin_review.py` | P1-S8 / S1j / S1k |
| `ChecklistPanel.tsx`, `PublishGate.tsx` | P3-S1j |
| `.github/workflows/ci.yml` | Already runs full `backend/tests` and frontend `pnpm test` |

---

### A8. TESTS EXECUTED

#### P3-T4–primary tests

| Test | File | Status | What it verifies |
|------|------|--------|------------------|
| `test_ungrounded_number_blocks_publish_with_422` | `test_editorial_integrity_e2e.py` | **Pass** (integration) | GET FAIL + publish 422 `number_validator_failed` |
| `test_happy_path_evidence_fix_checklist_then_publish_200` | `test_editorial_integrity_e2e.py` | **Pass** (integration) | Evidence fix → 4 auto PASS → plain English → 200 |
| `test_section_regen_cannot_bypass_validator` | `test_editorial_integrity_e2e.py` | **Pass** (integration + patch) | Bad regen → post-check FAIL → publish 422 |
| `disables Publish until automated checks pass and plain English is confirmed` | `ChecklistPanel.test.tsx` | **Pass** | Button disabled until checkbox + auto PASS |
| `keeps Publish disabled when automated checklist fails` | `ChecklistPanel.test.tsx` | **Pass** | Button disabled on SEBI FAIL |
| `keeps Publish disabled when number validator fails` | `ChecklistPanel.test.tsx` | **Pass** | Button disabled on validator FAIL |
| `PublishGate` suite (4 cases) | `PublishGate.test.tsx` | **Pass** | Loading, error, PASS, FAIL panel rendering |

#### Commands

```powershell
# P3-T4 only (from repo root)
python -m pytest -q backend/tests/test_editorial_integrity_e2e.py

# Frontend RTL (editorial publish gate)
cd frontend
pnpm test ChecklistPanel.test.tsx PublishGate.test.tsx

# CI-equivalent
python -m ruff check backend
python -m pytest -q backend/tests
cd frontend
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

#### Related regression (run after touching publish, validator, checklist, or regen)

| Test file | Relevance |
|-----------|-----------|
| `test_publish_gate.py` | S1i publish 422/200 paths |
| `test_editorial_checklist.py` | Four automated checks unit coverage |
| `test_card_regen.py` | Section regen hash + post-check PASS path |
| `test_publish_writes_track_record.py` | Publish lifecycle + track_record insert |
| `test_card_detail_original_immutable.py` | Context step number skip regression |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**None in P3-T4.**

Tests use existing columns on `public.cards` and `public.events`:

| Column / table | Used in |
|----------------|---------|
| `cards.insight_layer`, `context_layer`, `evidence_layer` | Validator grounding corpus |
| `cards.dissenting_view` | Checklist dissent length (> 100 chars in fixtures) |
| `cards.lifecycle_state` | Draft → published assertion |
| `cards.regen_history` | Written by regen test (not asserted in T4) |
| `track_record` | Created on happy-path publish; not deleted in cleanup |

Probe rows deleted in `finally` — `track_record` rows may remain orphaned for pytest card IDs (append-only policy).

---

### B2. API / INTEGRATION CONTRACTS

**Endpoints under test**

#### `GET /api/admin/cards/{card_id}`

Returns card detail plus computed gates:

```json
{
  "card_id": "uuid",
  "lifecycle_state": "draft",
  "insight_layer": "...",
  "evidence_layer": { "markdown": "...", "sources": [] },
  "number_validation": {
    "status": "FAIL",
    "ungrounded": [{ "number": "99.9%", "sentence": "...", "index": 0 }],
    "missing_provenance": [],
    "comparative_flags": []
  },
  "editorial_checklist": {
    "all_automated_pass": false,
    "items": [
      { "key": "numbers", "automated": true, "status": "FAIL", "label": "..." },
      { "key": "dissent", "automated": true, "status": "PASS", "label": "..." },
      { "key": "evidence_freshness", "automated": true, "status": "PASS", "label": "..." },
      { "key": "sebi_compliance", "automated": true, "status": "PASS", "label": "..." },
      { "key": "plain_english", "automated": false, "status": "PENDING", "label": "..." }
    ]
  }
}
```

#### `POST /api/admin/cards/{card_id}/publish`

**Request:**

```json
{
  "editor_review_seconds": 45,
  "plain_english_confirmed": true
}
```

**Success (200):**

```json
{
  "card_id": "uuid",
  "lifecycle_state": "published",
  "bias_audit": { }
}
```

**Failure (422) — number validator:**

```json
{
  "detail": {
    "code": "number_validator_failed",
    "message": "number validator failed",
    "status": "FAIL",
    "ungrounded": [ { "number": "99.9%", "sentence": "...", "index": 0 } ],
    "missing_provenance": [],
    "comparative_flags": []
  }
}
```

**Failure (422) — plain English not confirmed:**

```json
{
  "detail": {
    "code": "publish_rejected",
    "message": "plain English checklist confirmation required"
  }
}
```

**Auth:** Phase 1 admin review routes — no auth gate on `/api/admin/*` (documented in S1j handover).

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Publish gate sequence (what T4 proves)**

```
GET /api/admin/cards/{id}
  → check_card()           → number_validation payload
  → check_editorial()      → editorial_checklist payload

POST /api/admin/cards/{id}/publish
  → fetch_card_detail_for_review
  → check_card()           → NumberValidationFailedError if FAIL
  → assert_automated_pass() → EditorialChecklistFailedError if any auto item FAIL
  → plain_english_confirmed? → PublishCardError if false
  → UPDATE lifecycle + track_record + notifications
```

**UI gate sequence (ChecklistPanel — RTL)**

```
canPublish =
  numberValidation.status == "PASS"
  AND editorialChecklist.all_automated_pass
  AND plainEnglishConfirmed (local state)
  AND not loading/error
```

Server always re-validates — UI disable is UX only; T4 proves server rejects bypass attempts.

**Regen + publish (G-09)**

```
regenerate_section(...)
  → LLM or evidence rebuild
  → validate_numbers_in_evidence (synthesis guard — patched in T4 test)
  → update card row
  → _run_post_checks → check_card + consistency_check
  → return post_check to caller

publish_draft_card(...)
  → check_card again (hard gate — cannot skip even if post_check was ignored)
```

**Number grounding rule (G-07)**

Every numeric token in Insight/Context must appear (normalized) in Evidence corpus (markdown, sources, matrix JSON). T4 uses `99.9%` in Insight without matching Evidence → FAIL; adding `99.9%` to Evidence markdown → PASS.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Integration tests skip in CI without `SUPABASE_DB_URL` | T4 E2E may not run on every PR | Run locally before merge; add DB secret to CI for full gate |
| Regen test patches synthesis guard | Does not prove production regen writes bad content | `validate_numbers_in_evidence` enforced in `card_regen.py`; `test_card_regen.py` covers happy regen |
| No Playwright E2E on `/admin/review` | Full browser flow not automated | RTL + backend E2E; optional Playwright in future |
| Happy path leaves orphan `track_record` | Test DB accumulates rows | Acceptable; use unique UUIDs; do not DELETE track_record |
| Evidence fix via SQL not admin API | 14.2 simulates editor fix without PATCH endpoint | Real UI edits Evidence through regen or future admin edit |

**Tech debt (optional improvements)**

- Add Playwright test: load draft → see FAIL → fix via UI → publish (P3-T4 follow-up).
- Add API-level regen test without patching synthesis guard (expect 422 from regen pipeline itself).
- Mark module `@pytest.mark.integration` in `test_editorial_integrity_e2e.py`.

---

### B5. TESTING NOTES

**Automated**

| Layer | Coverage |
|-------|----------|
| E2E integration | Ungrounded block, evidence fix publish, regen bypass |
| Unit (upstream) | Checklist items, number validator, publish gate, regen hash |
| RTL | Publish button disable, PublishGate FAIL rendering |

**Manual (operator)**

| Step | When |
|------|------|
| Run T4 pytest with `.env.local` `SUPABASE_DB_URL` | Before merge if publish/validator/checklist/regen changed |
| Spot-check `/admin/review/[draftId]` with failing draft | After S1j UI changes |
| Verify go/no-go T4 row green before P3-S1l kickoff | Milestone review |

**Known gaps**

- No browser E2E from admin review page to real API.
- Regen test uses service call + patch, not `POST /api/admin/cards/{id}/regenerate-section` with live LLM.
- Checklist FAIL paths other than `numbers` (e.g. SEBI, stale evidence) not in T4 E2E — covered in `test_editorial_checklist.py`.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required for | Notes |
|----------|--------------|-------|
| `SUPABASE_DB_URL` | `test_editorial_integrity_e2e.py` | Repo-root `.env.local` |
| _(none new)_ | Frontend RTL | Component props/fixtures only |

**Deployment sequencing**

1. No migration or env changes for P3-T4 alone.
2. Merge test + doc files — deploy only if rest of branch includes S1i/S1j/S1k production code.

**Manual ops**

- None required for T4 delivery.
- P3-S8: complete `docs/plans/phase3-go-no-go.md` when all gates green.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing publish, validator, checklist, or regen**

1. Run P3-T4 gate:
   ```powershell
   python -m pytest -q backend/tests/test_editorial_integrity_e2e.py
   cd frontend
   pnpm test ChecklistPanel.test.tsx PublishGate.test.tsx
   ```
2. If you change publish order or error codes, also run:
   ```powershell
   python -m pytest -q backend/tests/test_publish_gate.py backend/tests/test_editorial_checklist.py backend/tests/test_card_regen.py
   ```
3. Update `docs/plans/phase3-go-no-go.md` T4 row if test file names change.

**Common mistakes**

- Adding publish override “for admins” — breaks SEBI posture and T4 assumptions.
- Re-adding manual checkboxes for automated items — breaks G-15 and T4 happy path.
- Using `/api/cards/{id}/publish` — wrong route; admin publish is under `/api/admin`.
- Deleting `track_record` in test cleanup — trigger `deny_track_record_mutation` raises.
- Removing `validate_numbers_in_evidence` from regen — weakens synthesis guard; publish gate alone is not sufficient UX.

**Where to look**

| Concern | Path |
|---------|------|
| P3-T4 gate tests | `backend/tests/test_editorial_integrity_e2e.py` |
| Publish orchestration | `backend/app/services/publish_card.py` |
| Number validator | `backend/app/services/number_validator.py` |
| Editorial checklist | `backend/app/services/editorial_checklist.py` |
| Section regen + post-check | `backend/app/services/card_regen.py` |
| Admin API | `backend/app/api/admin_review.py` |
| Review UI | `frontend/app/admin/review/[draftId]/ReviewWorkspace.tsx` |
| Checklist + Publish button | `frontend/app/admin/review/_components/ChecklistPanel.tsx` |
| Validator FAIL panel | `frontend/app/admin/review/_components/PublishGate.tsx` |
| Go/no-go evidence | `docs/plans/phase3-go-no-go.md` |

**Contact for context (by role)**

- **Product / integrity rules** — PO (G-15 checklist, no publish override).
- **Editorial UX** — Frontend owner for `/admin/review`.
- **Pipeline / publish** — Backend owner for `publish_card.py` and admin API.
- **Verification gates** — Jordan per plan (P3-T4); Riley per plan (S1i/S1j).

---

## Audit checklist (story acceptance)

| Acceptance criterion | Met |
|----------------------|-----|
| E2E: ungrounded number → Publish 422 | Yes (`test_ungrounded_number_blocks_publish_with_422`) |
| E2E: button disabled (validator/checklist FAIL) | Yes (`ChecklistPanel.test.tsx`) |
| E2E: fix Evidence → auto PASS → manual tick → publish 200 | Yes (`test_happy_path_evidence_fix_checklist_then_publish_200` + RTL checkbox test) |
| Section regen does not bypass validator | Yes (`test_section_regen_cannot_bypass_validator`) |
| CI gate before P3-S1l | Yes (323 backend tests, ruff clean; full suite in CI) |
| Go/no-go evidence linked | Yes (`docs/plans/phase3-go-no-go.md`, `phase3-calibration.md`) |
| Plan tasks 14.0–14.5 complete | Yes |

---

## Audit style — production code inventory

P3-T4 did **not** ship new production modules. Production behaviour under test was delivered in:

| Story | Production deliverables |
|-------|-------------------------|
| P3-S1i | `number_validator.py`, publish hard stop in `publish_card.py` |
| P3-S1j | `editorial_checklist.py`, `sebi_compliance_scan.py`, `ChecklistPanel.tsx`, `PublishGate.tsx` |
| P3-S1k | `card_regen.py`, `consistency_check.py`, regen admin routes |
| P1-S8 | `admin_review.py`, `track_record` append-only publish snapshot |

---

## Handover to P3-S1l / P3-T5

P3-S1l may change feed confidence display (`confidence_effective`, FoW banner). **Editorial integrity gates must remain hard stops** — re-run P3-T4 after any change to:

- `publish_card.py`
- `number_validator.py` / `editorial_checklist.py`
- `admin_review.py` publish or GET handlers
- `ChecklistPanel.tsx` / `PublishGate.tsx` disable logic

P3-T5 will add FoW + signal override verification after S1l and S1m land.

---

_Document version: v1.0 · Phase 3 · P3-T4 · G-07/G-09/G-15 editorial integrity gate · Blocks P3-S1l_
