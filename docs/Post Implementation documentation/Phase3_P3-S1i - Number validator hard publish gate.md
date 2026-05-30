# Post Implementation Detailed Document — P3-S1i

**Version:** v1.0 | **Date:** 31-05-2026  
**Story ID:** P3-S1i (Phase 3, Story 1i)  
**PRD2 gaps:** G-07 (number validator hard publish gate — Option B: structured diff + comparative soft flags)  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **11.0**–**11.6**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §5.1 · `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` WS-3 / G-07  
**Upstream handover:**  
- `docs/Post Implementation documentation/Phase3_P3-T3 - Confidence scoring verification gate.md` (P3-T3 green before S1i)  
- Phase 1 `number_validator.py` (draft-time `validate_numbers_in_evidence` in `card_pipeline.py`)

---

## Narrative style (read this first)

Phase 1 already rejected **hallucinated numbers at draft generation** — the LLM pipeline called `validate_numbers_in_evidence()` and raised if Insight/Context contained a numeric token absent from the Evidence corpus. That protected synthesis quality but **did not block publish**: an editor could still tick a manual checklist and publish a card whose narrative numbers were not grounded in Evidence.

**P3-S1i** closes that gap. It is the product’s most important integrity mechanism (PRD2 G-07): **Publish is impossible until `number_validator.check()` returns PASS**. There is no override endpoint and no per-card exception.

The implementation adds:

1. **Structured validator** — `check()` / `check_card()` return `PASS` or `FAIL` with `ungrounded[]` (sentence, number, index), `missing_provenance[]` (evidence rows lacking `source_url`, `retrieved_at`, or `mmj_tag`), and `comparative_flags[]` (soft warnings only).
2. **Backend hard gate** — `publish_draft_card()` runs the validator before any lifecycle transition; `POST /api/admin/cards/{id}/publish` returns **422** with the full diff payload on FAIL.
3. **Card load validation** — `GET /api/admin/cards/{id}` includes `number_validation` so the UI can disable Publish on load.
4. **Editor UI** — `PublishGate.tsx` renders PASS/FAIL with sentence-level diff; `ChecklistPanel` requires validator PASS **and** all five manual checklist ticks before enabling Publish.

Comparative quantifiers (`doubled`, `record high`, etc.) are **logged at INFO** and shown in the UI as non-blocking soft flags — they do not fail the gate (PO Option B).

**Tests executed and passed (P3-S1i–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Number validator unit | `python -m pytest -q backend/tests/test_number_validator.py` | **8 passed** |
| Publish gate integration | `python -m pytest -q backend/tests/test_publish_gate.py` | **3 passed** (requires `SUPABASE_DB_URL`) |
| PublishGate RTL | `pnpm test PublishGate.test.tsx` (from `frontend/`) | **4 passed** |
| ChecklistPanel RTL | `pnpm test ChecklistPanel.test.tsx` (from `frontend/`) | **2 passed** |
| Card detail regression | `python -m pytest -q backend/tests/test_card_detail_original_immutable.py` | **Pass** (ordered-list marker fix) |
| **Full backend CI** | `python -m ruff check backend` + `python -m pytest -q backend/tests` | **304 passed**, ruff clean |
| **Full frontend CI** | `pnpm lint` + `pnpm typecheck` + `pnpm test` + `pnpm build` | **Pass** |

**Three anchors for handover:** (1) **Do not add a publish override endpoint** — P3-S1j checklist item 1 and P3-T4 editorial integrity gate depend on this being a hard stop. (2) **Publish route is `/api/admin/cards/{id}/publish`**, not `/api/cards/{id}/publish` — the live editorial UI is `admin/review`, not `(app)/editor/cards`. (3) **Context step numbers (`1.`, `2.`) are intentionally excluded** from numeric extraction so ICE step lists do not false-fail; do not remove `_should_skip_numeric_match` without updating `test_card_detail_original_immutable.py`.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S1i |
| **Title** | Number validator hard publish gate |
| **Category** | **Full Stack** (backend service + admin API + editorial UI) |
| **Points / owner (plan)** | 5 · Riley |
| **Depends on** | P3-T3 (confidence scoring verification gate) |
| **Parallel with** | _None_ |
| **Blocks** | **P3-S1j** (editorial checklist), **P3-S1k** (section regen), **P3-T4** (editorial integrity test gate) |

**What this story aimed to achieve (plain language)**

Editors must not be able to publish a card until every numeric token in the Insight and Context layers appears in the Evidence layer, and every structured Evidence row has complete provenance. When validation fails, the UI shows **which sentence** contains an ungrounded number so the editor can add Evidence or rewrite prose — faster than bypassing, and bypassing is not allowed.

**How it fits into the overall application**

- **Upstream:** Phase 1 draft pipeline numeric grounding; P3-T3 proved confidence scoring trustworthy before editorial hard gates.
- **This story:** Moves number validation from “draft-time warning via exception” to **publish-time hard gate** with structured API/UI feedback.
- **Downstream:** P3-S1j wires checklist item 1 to `number_validation.status === "PASS"`; P3-S1k re-runs validator after section regen; P3-T4 proves editorial integrity end-to-end.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **11.1** | Extend `number_validator.py`: `check()`, `check_card()`, `NumberValidationResult`, `UngroundedNumber`, `MissingProvenance`, `NumberValidationFailedError`. |
| **11.2** | `publish_draft_card()` + `POST /api/admin/cards/{id}/publish` return **422** with diff payload on FAIL. |
| **11.3** | `PublishGate.tsx` — disable Publish; render sentence-level ungrounded list + provenance gaps. |
| **11.4** | Comparative quantifier regex → `comparative_flags[]` + `_LOG.info` (non-blocking). |
| **11.5** | Loading/error states when card load lacks `number_validation` or fetch fails. |
| **11.6** | `test_number_validator.py` extended; `test_publish_gate.py` created (422 + PASS paths). |

**Functional breakdown**

1. **Extract numerics** from combined Insight + Context using conservative regex (currency, `%`, standalone digits). Normalise tokens (strip commas, currency prefix, lower-case) for corpus substring match.
2. **Build evidence corpus** from `markdown`, `macro_stub`, `matrix_snapshot`, `event_snapshot`, and optional `sources[]` claims/excerpts.
3. **Ungrounded check** — for each unique numeric token per sentence, fail if normalised token not found in corpus.
4. **Provenance check** — for each row in `sources[]` and each Factor DB cell in `matrix_snapshot.sensitivities`, require `source_url`, `retrieved_at`, and `mmj_tag`.
5. **Comparative soft flags** — detect phrases like `doubled`, `record high`; append to result and log; **do not** set `status = FAIL`.
6. **Publish** — `check_card(detail)` before lifecycle update; raise `NumberValidationFailedError` → HTTP 422.
7. **Card load** — attach `number_validation` to admin GET response; frontend disables Publish until `status === "PASS"`.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Ordered-list markers (`1. Step one…`) | Skipped via `_should_skip_numeric_match` — not treated as ungrounded numbers |
| Duplicate same number in one sentence | Deduped by `(sentence_index, normalised_token)` |
| Empty `evidence_layer {}` with no numbers in prose | PASS (no ungrounded tokens; no provenance rows to check) |
| Empty evidence but numbers in Insight | FAIL with `ungrounded[]` populated |
| `sources[]` row missing `retrieved_at` | FAIL with `missing_provenance[]` |
| Pipeline card with full `matrix_snapshot` (Factor DB) | Provenance checked per sensitivity cell; pipeline includes `retrieved_at` from DB |
| Comparative phrase in prose | `comparative_flags[]` populated; status remains PASS if numbers grounded |
| Card not draft | `PublishCardError` (422 `publish_rejected`) — validator not reached if already published |
| `track_record` append-only | Integration test cleanup must **not** DELETE from `track_record` — use rollback pattern |

**Business rules enforced**

- **G-07 Option B:** Hard gate, no override, structured diff, comparative quantifiers soft-only.
- **PRD2 §5.1:** Every number in Insight/Context must appear in Evidence; every Evidence row must have provenance fields.
- **LLM-never-invents-numbers invariant** enforced at publish, not only at draft synthesis.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Admin route `/api/admin/cards/...`** not `cards.py` draft router | Live editorial workspace is `admin/review`; publish already lived on `admin_review.py` | New route on `cards.py` — would duplicate or miss existing publish flow |
| **`PublishGate` under `admin/review/_components/`** | Plan referenced `(app)/editor/cards/[id]/` which does not exist in repo | Create parallel editor route tree — unnecessary duplication |
| **Skip Context list markers `1.`–`99.`** | ICE Context uses numbered steps; `1` in `1. Step` false-failed publish on real cards | Require editors to ground step numbers in Evidence — unusable UX |
| **Provenance on matrix cells + sources only** | Matches PRD2 Evidence row model; markdown-only evidence has no structured rows | Fail if markdown lacks URL per line — too strict for Phase 1 macro stub pattern |
| **Keep Phase 1 `validate_numbers_in_evidence()`** | Draft pipeline still raises on first bad token during synthesis | Replace with `check()` everywhere — would change draft error shape mid-phase |
| **422 detail merges `code` + full `to_dict()`** | Frontend can show diff without second fetch | Minimal `{ message }` only — PO chose Option B structured diff |

⚠️ **Do not add a publish override or admin bypass** — SEBI integrity posture; P3-S1j/P3-T4 assume no escape hatch.

⚠️ **Do not remove ordered-list skip logic** without fixing Context step cards and `test_card_detail_original_immutable.py`.

⚠️ **Validator runs on Insight + Context only** — instrument assessment reasoning is still validated at draft time via `_validate_layers`, not re-checked at publish in this story.

**Assumptions**

- Factor DB seed data includes `source_url`, `retrieved_at`, `mmj_tag` on sensitivity rows (pipeline `matrix_snapshot` inherits these).
- Manual `sources[]` entries added by editors in future stories will include the three provenance fields.
- P3-S1j will replace the first manual checklist tick with an automated PASS tied to `number_validation.status`.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P1-S7** draft `validate_numbers_in_evidence`; **P3-T3** confidence gate green; **P1-S8** `publish_draft_card` lifecycle + `track_record` |
| **Parallel** | None |
| **Downstream** | **P3-S1j** — checklist item 1 auto = number validator PASS; **P3-S1k** — post-regen re-run; **P3-T4** — editorial integrity test gate |

**Shared components touched**

| Component | Role |
|-----------|------|
| `number_validator.py` | Core `check()` / structured FAIL |
| `publish_card.py` | Hard gate before DB publish |
| `admin_review.py` | GET includes validation; POST 422 on FAIL |
| `card_pipeline.py` | Unchanged publish path; still uses legacy `validate_numbers_in_evidence` at draft |
| `ReviewWorkspace.tsx` | Loads `number_validation`; passes to checklist |
| `ChecklistPanel.tsx` | Publish disabled until validator + checklist pass |

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Pure validation service** — `check()` has no DB I/O; easy to unit test and call from API + publish service.
- **Exception carrier** — `NumberValidationFailedError` holds full `NumberValidationResult` for HTTP serialisation.
- **Dual enforcement** — UI disables Publish on load; backend re-validates on POST (never trust client).

**Database schema**

- **No migration** — validation is computed from existing `cards.evidence_layer` JSONB and ICE text columns.

**API contracts**

| Method | Route | Change |
|--------|-------|--------|
| GET | `/api/admin/cards/{card_id}` | Response adds `number_validation` object |
| POST | `/api/admin/cards/{card_id}/publish` | **422** `number_validator_failed` with diff payload on FAIL |

**`number_validation` / 422 payload shape**

```json
{
  "status": "FAIL",
  "ungrounded": [
    { "sentence": "Analysts cite 99.9% certainty [JUDGED].", "number": "99.9%", "index": 0 }
  ],
  "missing_provenance": [
    { "evidence_id": "source-0", "missing_fields": ["source_url", "retrieved_at", "mmj_tag"] }
  ],
  "comparative_flags": ["doubled"]
}
```

**422 `detail` envelope on publish FAIL**

```json
{
  "code": "number_validator_failed",
  "message": "number validator failed",
  "status": "FAIL",
  "ungrounded": [ ... ],
  "missing_provenance": [ ... ],
  "comparative_flags": [ ... ]
}
```

**UI/UX**

- Green **Number validator — PASS** banner when grounded.
- Red FAIL panel with per-sentence ungrounded list and provenance gap list.
- Amber soft-flag line for comparative quantifiers (non-blocking).
- Publish button helper text: requires validator PASS **and** five checklist ticks.
- Loading skeleton on card fetch; error alert if validation payload missing.

**Libraries / tools**

| Library | Purpose |
|---------|---------|
| stdlib `re`, `dataclasses`, `json`, `logging` | Token extraction, result types, evidence parsing, soft-flag logs |
| Existing FastAPI / TestClient | API integration tests |
| RTL + Jest | `PublishGate` / `ChecklistPanel` component tests |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `PublishGate.tsx` | `frontend/app/admin/review/_components/PublishGate.tsx` | PASS/FAIL UI, sentence diff, loading/error states |
| `PublishGate.test.tsx` | `frontend/app/admin/review/_components/PublishGate.test.tsx` | RTL tests for gate states |
| `test_publish_gate.py` | `backend/tests/test_publish_gate.py` | Publish 422 + PASS + GET includes validation |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `number_validator.py` | `backend/app/services/number_validator.py` | Added `check()`, `check_card()`, structured result types, comparative flags, list-marker skip, provenance checks |
| `publish_card.py` | `backend/app/services/publish_card.py` | Runs `check_card()` before publish; raises `NumberValidationFailedError` |
| `admin_review.py` | `backend/app/api/admin_review.py` | GET adds `number_validation`; POST catches validator error → 422 with diff |
| `ChecklistPanel.tsx` | `frontend/app/admin/review/_components/ChecklistPanel.tsx` | Integrates `PublishGate`; Publish requires validator PASS |
| `ChecklistPanel.test.tsx` | `frontend/app/admin/review/_components/ChecklistPanel.test.tsx` | Tests validator FAIL keeps Publish disabled |
| `ReviewWorkspace.tsx` | `frontend/app/admin/review/[draftId]/ReviewWorkspace.tsx` | Passes validation props; handles 422 publish message |
| `test_number_validator.py` | `backend/tests/test_number_validator.py` | Extended with structured FAIL, provenance, comparative, list-marker cases |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S1i AC + tasks **11.0**–**11.6** marked complete |

**Not modified (intentionally)**

| File | Note |
|------|------|
| `backend/app/api/cards.py` | Draft-from-event only; publish stays on admin router |
| `card_pipeline.py` | Still uses legacy `validate_numbers_in_evidence` at synthesis — publish gate is separate layer |
| `ChecklistPanel` automated checks | Full 4-auto + 1-manual checklist is **P3-S1j** |

---

### A8. TESTS EXECUTED

| Test file | Test function / group | Status | What it verifies |
|-----------|----------------------|--------|------------------|
| `test_number_validator.py` | `test_rejects_hallucinated_number` | **Pass** | Legacy `validate_numbers_in_evidence` raises on 99.9% |
| `test_number_validator.py` | `test_accepts_grounded_number_with_mmj` | **Pass** | Grounded `-4` accepted |
| `test_number_validator.py` | `test_check_returns_structured_fail_with_sentence` | **Pass** | FAIL includes sentence + number + index |
| `test_number_validator.py` | `test_check_passes_when_numbers_grounded` | **Pass** | PASS when corpus contains tokens |
| `test_number_validator.py` | `test_check_reports_missing_provenance` | **Pass** | FAIL on incomplete `sources[]` row |
| `test_number_validator.py` | `test_comparative_quantifiers_are_soft_warnings_only` | **Pass** | PASS status with non-empty `comparative_flags` |
| `test_number_validator.py` | `test_accepts_ordered_list_markers_without_grounding` | **Pass** | Context `1.` / `2.` steps do not fail |
| `test_number_validator.py` | `test_number_validation_failed_error_carries_result` | **Pass** | Exception holds full result |
| `test_publish_gate.py` | `test_publish_blocked_with_ungrounded_number` | **Pass** | Service + API 422 with `ungrounded` |
| `test_publish_gate.py` | `test_publish_passes_when_evidence_grounds_numbers` | **Pass** | Publish succeeds; GET shows PASS |
| `test_publish_gate.py` | `test_get_card_includes_number_validation` | **Pass** | Admin GET includes validation object |
| `PublishGate.test.tsx` | loading / error / PASS / FAIL diff | **Pass** (×4) | UI states |
| `ChecklistPanel.test.tsx` | checklist + validator interaction | **Pass** (×2) | Publish gated on both |

**Commands used (full CI)**

```powershell
cd c:\Projects\InvestmentAssistant
python -m ruff check backend
python -m pytest -q backend/tests

cd frontend
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

**Result:** **304** backend tests passed, ruff clean; frontend CI green (31-05-2026 implementation run).

**Manual testing:** Not required for story sign-off; recommended smoke test: open `/admin/review/{draftId}` on a draft with known grounded/ungrounded numbers.

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**None.** Validation reads existing columns:

| Column | Table | Usage |
|--------|-------|-------|
| `insight_layer`, `context_layer` | `cards` | Prose scanned for numeric tokens |
| `evidence_layer` | `cards` | JSONB corpus + provenance rows |
| `lifecycle_state` | `cards` | Must be `draft` to publish |

No migration to apply for this story.

---

### B2. API / INTEGRATION CONTRACTS

**GET `/api/admin/cards/{card_id}`**

- **Auth:** None today (Phase 1 admin pattern — same as pre-S1i).
- **Cache:** `Cache-Control: no-store` via admin middleware.
- **New field:** `number_validation` (see A5 payload shape).

**POST `/api/admin/cards/{card_id}/publish`**

- **Body:** `{ "editor_review_seconds": number | null }`
- **Success:** 200 — `{ "card_id", "lifecycle_state", "bias_audit" }` (unchanged).
- **FAIL validator:** 422 — `detail.code === "number_validator_failed"` + diff fields.
- **Other 422:** `publish_rejected` (e.g. not draft).

**Example FAIL response (truncated)**

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": {
    "code": "number_validator_failed",
    "message": "number validator failed",
    "status": "FAIL",
    "ungrounded": [
      {
        "sentence": "Analysts cite 99.9% certainty [JUDGED].",
        "number": "99.9%",
        "index": 0
      }
    ],
    "missing_provenance": [],
    "comparative_flags": []
  }
}
```

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Numeric token regex (conservative)**

```
(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d+)?
| \d[\d,]*(?:\.\d+)?%
| (?<!\w)\d[\d,]*(?:\.\d+)?(?!\w)
```

**Normalisation pipeline**

1. Strip whitespace  
2. Remove commas  
3. Strip currency prefix (`₹`, `Rs`, `INR`)  
4. Lower-case  
5. Substring search in normalised evidence corpus  

**Decision tree (`check()`)**

```
check(insight, context, evidence_layer)
├── Build corpus_norm from evidence JSON
├── comparative_flags = detect comparative phrases → LOG if any
├── ungrounded = tokens in (insight + context) not in corpus_norm
│   └── skip ordered-list markers (1., 2., …)
├── missing_provenance = sources[] + matrix cells missing url/date/mmj
├── if ungrounded OR missing_provenance → FAIL
└── else → PASS (comparative_flags may be non-empty)
```

**Publish flow**

```
POST /api/admin/cards/{id}/publish
└── publish_draft_card()
    ├── fetch_card_detail_for_review
    ├── lifecycle == draft?
    ├── check_card(detail) == PASS?
    │   └── NO → NumberValidationFailedError → HTTP 422
    └── UPDATE cards/events, INSERT track_record, notifications
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Severity | Notes |
|------|----------|-------|
| **No publish override** | By design | PO G-07 — do not add “force publish” |
| **Insight/Context only at publish** | Low | Instrument reasoning validated at draft, not re-checked on publish |
| **`assert_numbers_in_evidence()` unused** | Low | Helper added with wrong kwarg name; dead code — remove or fix if adopted |
| **Comparative log lacks `card_id`** | Low | Log message uses `card_id=unknown`; pass ID from `check_card` in follow-up |
| **One-click “Add Evidence” prefilled** | Deferred | PRD2 workshop: Phase 4 UX; Phase 3 is structured diff list only |
| **Plan path vs repo path** | Doc only | Plan listed `(app)/editor/cards/[id]/PublishGate.tsx`; implemented under `admin/review` |

---

### B5. TESTING NOTES

**Automated**

- Unit: token extraction, PASS/FAIL, provenance, comparative soft flags, list markers.
- Integration: DB seed draft → publish blocked/passed; admin GET shape.
- RTL: PublishGate states; ChecklistPanel dual gate.

**Manual (recommended after deploy)**

1. Open draft at `/admin/review/{uuid}` — confirm green PASS or red FAIL panel.
2. Attempt Publish on FAIL card — button disabled; if forced via API, expect 422.
3. Tick all checklist items on PASS card — Publish enables and succeeds.

**Known gaps**

- No E2E Playwright test for full admin review publish flow.
- No test for every comparative quantifier phrase in regex (sample coverage only).
- Publish integration tests require live `SUPABASE_DB_URL` (skip in CI without DB).

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Item | Required? |
|------|-----------|
| New env vars | **No** |
| New migrations | **No** |
| Feature flags | **No** |

**Deployment**

- Deploy **backend and frontend together** — UI disable logic depends on GET `number_validation`; backend POST enforces gate.
- No manual migration or config steps.

**Operational impact**

- Existing drafts with ungrounded numbers or incomplete provenance will **fail publish** until fixed via Evidence or prose edits.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read PRD2 §5.1 and G-07 workshop decision (Option B) — **no override** is intentional.
2. Run `test_number_validator.py` and `test_publish_gate.py` after any regex or provenance rule change.
3. If changing Context step format, re-run `test_card_detail_original_immutable.py`.

**Common mistakes**

- Adding override endpoint “for emergencies” — breaks P3-S1j/T4 contract.
- Treating comparative flags as hard FAIL — they are log + UI warning only.
- Deleting `track_record` rows in test cleanup — table is append-only (trigger denies DELETE).
- Pointing frontend at wrong API base — publish is under `/api/admin/cards/`, not `/api/cards/`.

**Where to find related code**

| Concern | Path |
|---------|------|
| Validator core | `backend/app/services/number_validator.py` |
| Publish enforcement | `backend/app/services/publish_card.py` |
| Admin API | `backend/app/api/admin_review.py` |
| Draft-time validation (legacy) | `backend/app/services/card_pipeline.py` → `_validate_layers` |
| Editorial UI | `frontend/app/admin/review/[draftId]/ReviewWorkspace.tsx` |
| Gate component | `frontend/app/admin/review/_components/PublishGate.tsx` |

**Next stories (same developer stream — Riley)**

- **P3-S1j** — Replace manual “numbers” checklist tick with auto PASS from `number_validation`; add SEBI scan, dissent length, evidence freshness.
- **P3-S1k** — Call `check_card()` after section regen.
- **P3-T4** — Editorial integrity test gate across S1i + S1j + S1k.

---

## Handover to P3-S1j

P3-S1i delivers **`number_validation` on card load** and **422 on publish FAIL**. P3-S1j should:

1. Wire checklist item 1 (number validator) to **automated** `number_validation.status === "PASS"` instead of a manual checkbox.
2. Keep Publish disabled until **all five** checklist items pass (four auto + one manual plain English).
3. Reuse `PublishGate.tsx` — do not duplicate diff UI in `ChecklistPanel`.

Do not start P3-S1j by weakening or bypassing the hard gate implemented here.
