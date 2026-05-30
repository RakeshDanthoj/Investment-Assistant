# Post Implementation Detailed Document — P3-S1j

**Version:** v1.0 | **Date:** 31-05-2026  
**Story ID:** P3-S1j (Phase 3, Story 1j)  
**PRD2 gaps:** G-15 (editorial checklist hard gate — 4 automated + 1 manual)  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **12.0**–**12.6**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §8.2 · `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` G-15 · `docs/PRD/FinnWise_PRD2_Gap_Brainstorm_Workshop.md` (Matt workshop decision)  
**Upstream handover:**  
- `docs/Post Implementation documentation/Phase3_P3-S1i - Number validator hard publish gate.md` (P3-S1i — number validator hard gate)  
- Phase 1 `ChecklistPanel.tsx` (five manual ticks — superseded for four items)

---

## Narrative style (read this first)

Phase 1 gave editors a **five-item manual checklist** on `/admin/review/[draftId]`. Every item was a checkbox the editor had to tick before Publish — including checks that could be computed automatically (number grounding, dissent length, evidence age, SEBI language). Solo-builder fatigue made it too easy to tick everything without reading.

**P3-S1j** upgrades the checklist to a **hard gate with four automated PASS/FAIL checks and one intentional manual confirmation**. On card load, the backend runs all four automated checks and returns structured results. The UI shows PASS/FAIL badges for automated items; only **plain English** remains a manual checkbox. Publish stays disabled until all four automated items pass, the number validator passes (enforced twice — once inside checklist item 1 and again at publish), plain English is confirmed, and the backend receives `plain_english_confirmed: true`.

The four automated checks are:

1. **Number validator PASS** — reuses P3-S1i `check_card()` (no override).
2. **Dissent length > 100 chars** — `dissenting_view` must be substantive, not a generic disclaimer.
3. **Evidence freshness ≤ 18 months** — max `retrieved_at` age across dated Evidence rows; uses existing `freshness_for_retrieved_at()` (`red` = block).
4. **SEBI language scan PASS** — YAML-driven regex for buy/sell/hold, rupee price targets, return expectations; macro allowlist for phrases like `repo rate hold` and `hold rates steady`.

The fifth item — **plain English** — cannot be automated reliably (workshop decision). The editor must tick it; the backend rejects publish without `plain_english_confirmed: true`.

**Tests executed and passed (P3-S1j–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Editorial checklist unit | `python -m pytest -q backend/tests/test_editorial_checklist.py` | **9 passed** |
| Publish gate integration | `python -m pytest -q backend/tests/test_publish_gate.py` | **3 passed** (requires `SUPABASE_DB_URL`) |
| Publish regression | `python -m pytest -q backend/tests/test_publish_writes_track_record.py` | **1 passed** |
| Original view regression | `python -m pytest -q backend/tests/test_card_detail_original_immutable.py` | **1 passed** |
| PublishGate RTL | `pnpm test PublishGate.test.tsx` (from `frontend/`) | **4 passed** |
| ChecklistPanel RTL | `pnpm test ChecklistPanel.test.tsx` (from `frontend/`) | **3 passed** |
| **Full backend CI** | `python -m ruff check backend` + `python -m pytest -q backend/tests` | **313 passed**, ruff clean |
| **Full frontend CI** | `pnpm lint` + `pnpm typecheck` + `pnpm test` + `pnpm build` | **Pass** |

**Three anchors for handover:** (1) **Plain English is the only manual checklist item** — do not re-add manual checkboxes for numbers, dissent, freshness, or SEBI without reversing G-15. (2) **Publish requires `plain_english_confirmed: true`** in POST body — scripts and API clients must send it; UI already does. (3) **SEBI allowlist lives in YAML** — tune false positives in `sebi_compliance_patterns.yaml`, not by weakening the publish gate in code.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S1j |
| **Title** | Editorial checklist — 4 automated + 1 manual |
| **Category** | **Full Stack** (backend services + admin API + editorial UI) |
| **Points / owner (plan)** | 3 · Riley |
| **Depends on** | P3-S1i (number validator hard publish gate) |
| **Parallel with** | P3-S1k (targeted section regen) |
| **Blocks** | **P3-T4** (editorial integrity verification gate) |

**What this story aimed to achieve (plain language)**

Editors need guardrails so fatigue cannot skip SEBI-critical steps before Publish. Four checklist items now run automatically when a draft loads: numbers grounded, dissent present, evidence not stale, and no buy/sell/hold language. One item — plain English readability — stays manual because it requires human judgment. Publish only activates when all five are satisfied.

**How it fits into the overall application**

- **Upstream:** P3-S1i made number validation a hard publish gate; Phase 1 provided the manual checklist UI shell.
- **This story:** Automates four of five checklist items, wires results into card load and publish, and enforces plain-English confirmation server-side.
- **Downstream:** P3-T4 will prove end-to-end that publish is impossible until validator + checklist pass; P3-S1k must re-run validator/checklist after section regen.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **12.1** | `editorial_checklist.py` orchestrates four automated checks on card load via `check_card()`. |
| **12.2** | `sebi_compliance_scan.py` + `sebi_compliance_patterns.yaml` — blocked terms with context allowlist. |
| **12.3** | Evidence freshness auto-check — max Evidence `retrieved_at` age ≤ 18 months (`freshness == red` → FAIL). |
| **12.4** | `ChecklistPanel.tsx` — PASS/FAIL badges for auto items; manual checkbox for plain English only. |
| **12.5** | `PublishGate.tsx` integrates checklist — unified PASS/FAIL panel; Publish blocked until all automated items pass. |
| **12.6** | `test_editorial_checklist.py` — SEBI allowlist on hold-rate phrasing; block on buy; dissent length. |

**Functional breakdown**

1. **Card load (`GET /api/admin/cards/{id}`)** — After fetching card detail, API attaches `editorial_checklist` alongside existing `number_validation`.
2. **Checklist orchestration** — `editorial_checklist.check_card()` runs number validator, dissent length, evidence freshness, SEBI scan; appends manual `plain_english` item with status `PENDING`.
3. **SEBI scan** — Collects text from title, ICE layers, framework, and instrument assessment fields; matches blocked regexes; suppresses matches inside allowlisted macro phrases (±40 char context window).
4. **Evidence freshness** — Collects `retrieved_at` from `evidence_layer.sources[]` and `matrix_snapshot.sensitivities` cells; fails if any dated row is `red` (>18 months). No dated rows → PASS (nothing stale to evaluate).
5. **Publish (`POST /api/admin/cards/{id}/publish`)** — After P3-S1i number validator: runs `assert_automated_pass()`; requires `plain_english_confirmed === true`; else 422.
6. **UI** — Auto items render PASS/FAIL badges; plain English checkbox toggles local state; Publish disabled until `all_automated_pass && plainEnglishConfirmed && number_validation PASS`.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Dissent ≤ 100 chars | Checklist item `dissent` → FAIL; publish blocked |
| Evidence row > 18 months old | `evidence_freshness` → FAIL with `stale_rows` in details |
| No dated Evidence rows | `evidence_freshness` → PASS (“No dated Evidence rows to evaluate”) |
| `repo rate hold` in macro copy | SEBI scan → PASS (allowlisted) |
| `hold rates steady` / MPC phrasing | SEBI scan → PASS (allowlisted) |
| `buy` / `sell` / `hold` in recommendation context | SEBI scan → FAIL with violation list |
| `₹230` price target pattern | SEBI scan → FAIL |
| Plain English not ticked | UI disables Publish; API returns 422 `publish_rejected` if `plain_english_confirmed` false |
| Automated checklist FAIL | API 422 `editorial_checklist_failed` with full items payload |
| Number validator FAIL | Still 422 `number_validator_failed` (checked before checklist assert) |

**Business rules enforced**

- **G-15:** Five checklist items; four automated, one manual; all must pass before Publish.
- **PRD2 §8.2 / workshop:** Freshness and SEBI moved from manual to automated; plain English stays manual.
- **SEBI posture:** No buy/sell/hold; no rupee price targets; no explicit return expectations on cards.
- **Dissent quality:** Minimum 100 characters on `dissenting_view` (aligns with pipeline quality expectations).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Reuse `freshness_for_retrieved_at()` from `factor_db.py`** | Same 18-month threshold as Thread Evidence dots; single source of truth | Duplicate day-count logic in checklist module |
| **SEBI patterns in YAML, not hardcoded** | PO can tune allowlist without code deploy for macro phrasing | Inline regex list in Python |
| **Allowlist uses ±40 char context window** | Suppresses `hold` inside `repo rate hold` without blocking all `hold` tokens globally | Block all `hold` — breaks macro cards |
| **`plain_english_confirmed` on publish body** | Server-side enforcement; UI cannot be sole gate | Trust frontend checkbox only |
| **Keep number validator as separate API field + checklist item 1** | P3-S1i consumers still read `number_validation`; checklist item mirrors it for UI badges | Merge into checklist only — breaks S1i contract |
| **Implement under `admin/review/` not `(app)/editor/cards/`** | Live editorial route is `/admin/review/[draftId]` (same as P3-S1i) | Create parallel editor route tree |
| **No dated Evidence → freshness PASS** | Cannot prove staleness without dates; number validator may already FAIL on missing provenance | FAIL when no dates — would block valid macro stub cards |

⚠️ **Do not re-manualise automated checklist items** — G-15 and P3-T4 assume four auto + one manual.

⚠️ **Do not add SEBI publish override** — tune `sebi_compliance_patterns.yaml` instead.

⚠️ **Do not remove `plain_english_confirmed` requirement** without explicit PO sign-off — it is the only human-readability gate.

**Assumptions**

- Instrument assessment text is included in SEBI scan corpus (reasoning, entry/exit conditions, signal label).
- Editors accept ticking plain English after reading Insight layer (unchanged from Phase 1 intent).
- P3-S1k will hook post-regen validation without bypassing this checklist.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S1i** — `number_validator.check_card()` for item 1; **P1-S8** — admin review workspace + publish flow; **P1-S10** — `freshness_for_retrieved_at()` |
| **Parallel** | **P3-S1k** — section regen (must re-run checklist after regen) |
| **Downstream** | **P3-T4** — editorial integrity E2E gate; **P3-S1l** — FoW (after T4 green) |

**Shared components touched**

| Component | Role |
|-----------|------|
| `editorial_checklist.py` | Orchestrator; publish `assert_automated_pass()` |
| `sebi_compliance_scan.py` | SEBI regex + allowlist |
| `number_validator.py` | Unchanged API; called from checklist |
| `factor_db.py` | Freshness tier helper reused |
| `admin_review.py` | GET adds `editorial_checklist`; POST enforces confirmation |
| `publish_card.py` | Checklist + plain English before lifecycle transition |
| `ChecklistPanel.tsx` | Auto badges + manual plain English |
| `PublishGate.tsx` | Unified editorial gate UI |
| `ReviewWorkspace.tsx` | Loads checklist; sends `plain_english_confirmed` |

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Pure validation services** — checklist and SEBI scan have no DB I/O; computed from card dict.
- **YAML-driven policy** — SEBI blocked/allowlist patterns externalised for tuning.
- **Dual enforcement** — UI disables Publish; backend re-validates on POST.
- **Exception carriers** — `EditorialChecklistFailedError` holds full result for HTTP 422.

**Database schema**

- **No migration** — checklist computed from existing `cards` ICE columns and `evidence_layer` JSONB.

**API contracts**

| Method | Route | Change |
|--------|-------|--------|
| GET | `/api/admin/cards/{card_id}` | Response adds `editorial_checklist` object |
| POST | `/api/admin/cards/{card_id}/publish` | Body adds `plain_english_confirmed`; 422 on checklist FAIL |

**`editorial_checklist` response shape**

```json
{
  "items": [
    {
      "key": "numbers",
      "label": "Every quantitative claim carries [MEASURED]...",
      "automated": true,
      "status": "PASS",
      "message": "Number validator PASS.",
      "details": { "status": "PASS", "ungrounded": [], "missing_provenance": [], "comparative_flags": [] }
    },
    {
      "key": "dissent",
      "label": "A specific dissenting mechanism is present...",
      "automated": true,
      "status": "PASS",
      "message": "Dissent length 101 chars (> 100)."
    },
    {
      "key": "evidence_freshness",
      "label": "Every Evidence source is no older than 18 months...",
      "automated": true,
      "status": "PASS",
      "message": "All dated Evidence rows are within 18 months."
    },
    {
      "key": "sebi_compliance",
      "label": "No buy / sell / hold or personalised recommendation language...",
      "automated": true,
      "status": "PASS",
      "message": "SEBI language scan PASS."
    },
    {
      "key": "plain_english",
      "label": "Language is accessible to a non-expert reader...",
      "automated": false,
      "status": "PENDING",
      "message": "Editor must confirm plain English before publishing."
    }
  ],
  "all_automated_pass": true
}
```

**POST publish body (updated)**

```json
{
  "editor_review_seconds": 45,
  "plain_english_confirmed": true
}
```

**422 envelopes**

| Code | When |
|------|------|
| `number_validator_failed` | Ungrounded numbers or missing provenance (P3-S1i) |
| `editorial_checklist_failed` | Any automated checklist item FAIL |
| `publish_rejected` | e.g. not draft, or `plain_english_confirmed` false |

**UI/UX**

- Four automated items show **PASS** / **FAIL** badges (not checkboxes).
- Plain English uses a **checkbox**; status badge shows PENDING → PASS when ticked.
- `PublishGate` shows unified green “Editorial gate — PASS” or red panel with checklist failures + number diff.
- Publish helper text: requires four auto checks + plain English confirmation.

**Libraries / tools**

| Library | Purpose |
|---------|---------|
| `PyYAML` | Load SEBI pattern config |
| stdlib `re`, `dataclasses`, `json` | SEBI scan, result types, evidence parsing |
| Existing FastAPI / TestClient | API integration tests |
| RTL + Jest | ChecklistPanel / PublishGate component tests |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `editorial_checklist.py` | `backend/app/services/editorial_checklist.py` | Four automated checks + manual plain English item; publish assert |
| `sebi_compliance_scan.py` | `backend/app/services/sebi_compliance_scan.py` | YAML-driven SEBI regex scan with allowlist |
| `sebi_compliance_patterns.yaml` | `backend/app/config/sebi_compliance_patterns.yaml` | Blocked terms + macro allowlist patterns |
| `test_editorial_checklist.py` | `backend/tests/test_editorial_checklist.py` | Unit tests for all checklist gates + SEBI scan |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `admin_review.py` | `backend/app/api/admin_review.py` | GET adds `editorial_checklist`; POST body `plain_english_confirmed`; 422 on checklist FAIL |
| `publish_card.py` | `backend/app/services/publish_card.py` | `assert_automated_pass()` + plain English confirmation before publish |
| `ChecklistPanel.tsx` | `frontend/app/admin/review/_components/ChecklistPanel.tsx` | Auto PASS/FAIL badges; single manual checkbox; dual gate logic |
| `PublishGate.tsx` | `frontend/app/admin/review/_components/PublishGate.tsx` | Accepts `checklist` prop; unified editorial gate UI |
| `ReviewWorkspace.tsx` | `frontend/app/admin/review/[draftId]/ReviewWorkspace.tsx` | Loads `editorial_checklist`; sends `plain_english_confirmed: true` on publish |
| `ChecklistPanel.test.tsx` | `frontend/app/admin/review/_components/ChecklistPanel.test.tsx` | Tests auto + manual gate interaction |
| `PublishGate.test.tsx` | `frontend/app/admin/review/_components/PublishGate.test.tsx` | Tests checklist-integrated gate states |
| `test_publish_gate.py` | `backend/tests/test_publish_gate.py` | Long dissent fixture; `plain_english_confirmed`; asserts `editorial_checklist` on GET |
| `test_publish_writes_track_record.py` | `backend/tests/test_publish_writes_track_record.py` | Long dissent + `plain_english_confirmed` for publish regression |
| `test_card_detail_original_immutable.py` | `backend/tests/test_card_detail_original_immutable.py` | Long dissent + `plain_english_confirmed` for original-view regression |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S1j AC + tasks **12.0**–**12.6** marked complete |

**Not modified (intentionally)**

| File | Note |
|------|------|
| `number_validator.py` | Consumed by checklist; P3-S1i logic unchanged |
| `card_pipeline.py` | Draft synthesis unchanged; checklist is publish/review-time only |
| `(app)/editor/cards/` route tree | Does not exist; admin review is canonical editorial surface |

---

### A8. TESTS EXECUTED

| Test file | Test function / group | Status | What it verifies |
|-----------|----------------------|--------|------------------|
| `test_editorial_checklist.py` | `test_checklist_all_automated_pass_on_happy_path` | **Pass** | Four auto PASS + plain English manual item |
| `test_editorial_checklist.py` | `test_dissent_length_gate_fails_when_too_short` | **Pass** | Dissent ≤ 100 → FAIL |
| `test_editorial_checklist.py` | `test_evidence_freshness_blocks_rows_older_than_eighteen_months` | **Pass** | Stale `retrieved_at` → FAIL |
| `test_editorial_checklist.py` | `test_sebi_scan_blocks_buy_language` | **Pass** | `buy` → FAIL |
| `test_editorial_checklist.py` | `test_sebi_scan_allows_repo_rate_hold_phrase` | **Pass** | Macro allowlist |
| `test_editorial_checklist.py` | `test_sebi_scan_allows_hold_rate_phrase` | **Pass** | `hold rates steady` allowlist |
| `test_editorial_checklist.py` | `test_checklist_sebi_item_fails_when_buy_present` | **Pass** | End-to-end card → SEBI FAIL |
| `test_editorial_checklist.py` | `test_assert_automated_pass_raises_on_failure` | **Pass** | Publish helper raises |
| `test_editorial_checklist.py` | `test_assert_automated_pass_succeeds_on_happy_path` | **Pass** | Publish helper passes |
| `test_publish_gate.py` | `test_publish_blocked_with_ungrounded_number` | **Pass** | Number validator still blocks first |
| `test_publish_gate.py` | `test_publish_passes_when_evidence_grounds_numbers` | **Pass** | Full publish + GET checklist |
| `test_publish_gate.py` | `test_get_card_includes_number_validation` | **Pass** | GET includes validation + checklist |
| `test_publish_writes_track_record.py` | `test_publish_writes_track_record_and_sets_lifecycle` | **Pass** | Publish regression with new gates |
| `test_card_detail_original_immutable.py` | `test_original_view_keeps_day_one_copy_while_current_mutates` | **Pass** | Publish still works with checklist |
| `PublishGate.test.tsx` | loading / error / PASS / FAIL with checklist | **Pass** (×4) | Unified gate UI |
| `ChecklistPanel.test.tsx` | auto + manual / SEBI FAIL / validator FAIL | **Pass** (×3) | Publish gating |

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

**Result:** **313** backend tests passed, ruff clean; frontend CI green (31-05-2026 implementation run).

**Manual testing:** Recommended smoke test — open `/admin/review/{draftId}`, confirm four auto badges, tick plain English, publish succeeds; card with `buy` in Insight shows SEBI FAIL.

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**None.** Checklist reads existing columns:

| Column | Table | Usage |
|--------|-------|-------|
| `insight_layer`, `context_layer`, `dissenting_view`, `framework_behind_this`, `title` | `cards` | SEBI scan + dissent length |
| `evidence_layer` | `cards` | Freshness dates + number validator (via item 1) |
| Instrument assessments | joined at API layer | SEBI scan on reasoning/conditions |

No migration to apply for this story.

---

### B2. API / INTEGRATION CONTRACTS

**GET `/api/admin/cards/{card_id}`**

- **Auth:** None today (Phase 1 admin pattern).
- **Cache:** `Cache-Control: no-store`.
- **New field:** `editorial_checklist` (see A5).
- **Existing field:** `number_validation` (P3-S1i — unchanged).

**POST `/api/admin/cards/{card_id}/publish`**

- **Body:** `{ "editor_review_seconds": number | null, "plain_english_confirmed": boolean }`
- **Success:** 200 — `{ "card_id", "lifecycle_state", "bias_audit" }`.
- **FAIL checklist:** 422 — `detail.code === "editorial_checklist_failed"` + items payload.
- **FAIL plain English:** 422 — `detail.code === "publish_rejected"`, message `plain English checklist confirmation required`.
- **FAIL validator:** 422 — `number_validator_failed` (P3-S1i).

**Example checklist FAIL response (truncated)**

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": {
    "code": "editorial_checklist_failed",
    "message": "editorial checklist failed",
    "items": [ ... ],
    "all_automated_pass": false
  }
}
```

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Checklist decision tree (`check_card()`)**

```
check_card(card)
├── numbers     ← check_numbers(card) → PASS | FAIL
├── dissent     ← len(dissenting_view.strip()) > 100
├── freshness   ← max retrieved_at age; red tier → FAIL
├── sebi        ← scan_card(card) with YAML patterns + allowlist
└── plain_english ← always PENDING (manual); not evaluated server-side on load
```

**Publish decision tree**

```
POST /api/admin/cards/{id}/publish
└── publish_draft_card()
    ├── fetch_card_detail_for_review
    ├── lifecycle == draft?
    ├── check_card(detail) == PASS?          ← P3-S1i number validator
    │   └── NO → NumberValidationFailedError
    ├── assert_automated_pass(detail)?       ← P3-S1j four auto items
    │   └── NO → EditorialChecklistFailedError
    ├── plain_english_confirmed == true?
    │   └── NO → PublishCardError
    └── UPDATE cards/events, INSERT track_record, notifications
```

**SEBI scan corpus fields**

- `title`, `insight_layer`, `context_layer`, `dissenting_view`, `framework_behind_this`
- Per instrument: `reasoning`, `entry_conditions`, `exit_conditions`, `signal_label`

**Freshness rule**

- Uses `freshness_for_retrieved_at()` — green ≤ ~6 months, amber ≤ ~18 months, **red > ~18 months**.
- Checklist fails on **red** only (18-month max per G-15).

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Severity | Notes |
|------|----------|-------|
| **Plain English not machine-verified** | By design | Only manual tick + `plain_english_confirmed` flag |
| **SEBI regex false positives/negatives** | Medium | Tune YAML; no ML readability check |
| **`hold` allowlist is context-window based** | Low | Edge cases may need new allowlist entries |
| **Freshness PASS when no dated rows** | Low | Relies on number validator for provenance completeness |
| **Duplicate number check** | Low | Validator runs at publish (S1i) and inside checklist item 1 — intentional clarity for UI |
| **Plan path vs repo path** | Doc only | Plan listed `(app)/editor/cards/[id]/ChecklistPanel.tsx`; implemented under `admin/review` |
| **No E2E Playwright test yet** | Medium | Covered by P3-T4 editorial integrity gate |

---

### B5. TESTING NOTES

**Automated**

- Unit: dissent length, freshness stale rows, SEBI buy block, hold-rate allowlist, checklist orchestration.
- Integration: publish gate with long dissent + plain English confirmation; GET shape.
- RTL: ChecklistPanel auto/manual interaction; PublishGate with checklist failures.

**Manual (recommended after deploy)**

1. Open draft at `/admin/review/{uuid}` — confirm four PASS/FAIL badges on load.
2. Card with short dissent — dissent item FAIL; Publish disabled.
3. Card with macro “repo rate hold” copy — SEBI PASS.
4. Card with “buy this name” — SEBI FAIL.
5. Tick plain English only after auto items PASS — Publish enables.

**Known gaps**

- P3-T4 E2E (`test_editorial_integrity_e2e.py`) not yet implemented.
- SEBI scan does not cover every PRD forbidden phrase variant (sample regex coverage).
- Integration tests require live `SUPABASE_DB_URL` (skip in CI without DB).

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Item | Required? |
|------|-----------|
| New env vars | **No** |
| New migrations | **No** |
| Feature flags | **No** |
| YAML config | **`backend/app/config/sebi_compliance_patterns.yaml`** — tune blocked/allowlist patterns |

**Deployment**

- Deploy **backend and frontend together** — UI depends on GET `editorial_checklist`; POST requires `plain_english_confirmed`.
- No manual migration or env setup.

**Operational impact**

- Drafts with short dissent, stale Evidence, or SEBI violations will **fail publish** until fixed.
- Editors must **tick plain English** on every publish — one intentional manual step per card.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read PRD2 G-15 and workshop decision (4 auto + 1 manual) — do not revert to five manual checkboxes.
2. Run `test_editorial_checklist.py` after any checklist rule change.
3. Run `test_publish_gate.py` after publish flow changes.
4. After SEBI pattern edits, add/adjust unit tests for new allowlist cases.

**Common mistakes**

- Re-adding manual checkboxes for automated items — breaks G-15 fatigue-reduction goal.
- Weakening SEBI gate in Python instead of editing YAML allowlist.
- Forgetting `plain_english_confirmed: true` in scripts calling publish API.
- Using short dissent text in test fixtures — publish will fail after P3-S1j (`DISSENT_MIN_CHARS = 100`).

**Where to find related code**

| Concern | Path |
|---------|------|
| Checklist orchestrator | `backend/app/services/editorial_checklist.py` |
| SEBI scan | `backend/app/services/sebi_compliance_scan.py` |
| SEBI patterns | `backend/app/config/sebi_compliance_patterns.yaml` |
| Number validator (item 1) | `backend/app/services/number_validator.py` |
| Evidence freshness tiers | `backend/app/services/factor_db.py` |
| Publish enforcement | `backend/app/services/publish_card.py` |
| Admin API | `backend/app/api/admin_review.py` |
| Editorial UI | `frontend/app/admin/review/[draftId]/ReviewWorkspace.tsx` |
| Checklist UI | `frontend/app/admin/review/_components/ChecklistPanel.tsx` |
| Gate UI | `frontend/app/admin/review/_components/PublishGate.tsx` |

**Next stories (same stream)**

- **P3-S1k** — Section regen; must re-run number validator + checklist after regen (parallel-safe with S1j).
- **P3-T4** — Editorial integrity E2E gate across S1i + S1j + S1k.
- **P3-S1l** — FoW `is_major` (after T4 green).

**Contact for context (by role)**

- **Product / integrity rules** — PO (G-15 checklist composition, SEBI allowlist tuning).
- **Editorial UX** — Frontend owner for `/admin/review` checklist panel.
- **Pipeline / publish** — Backend owner for `publish_card.py` and admin API.

---

## Handover to P3-T4 / P3-S1k

P3-S1j delivers **`editorial_checklist` on card load** and **server-side enforcement** of four automated checks plus plain-English confirmation. Downstream work should:

1. **P3-T4** — Prove E2E: ungrounded number → Publish 422 + button disabled; fix Evidence → auto items PASS → manual tick → publish 200; section regen cannot bypass validator/checklist.
2. **P3-S1k** — After `POST /regenerate-section`, re-run `check_card()` and `assert_automated_pass()` before allowing publish; do not weaken S1j gates.

Do not start downstream stories by adding publish overrides or re-manualising automated checklist items.
