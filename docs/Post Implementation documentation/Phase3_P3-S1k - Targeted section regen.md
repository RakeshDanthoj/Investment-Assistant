# Post Implementation Detailed Document — P3-S1k

**Version:** v1.0 | **Date:** 31-05-2026  
**Story ID:** P3-S1k (Phase 3, Story 1k)  
**PRD2 gap:** G-09 (editorial rejection loop — targeted section regen, Option B)  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **13.0**–**13.6**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §5.3 · `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` WS-3 / G-09  
**Upstream handover:**  
- `docs/Post Implementation documentation/Phase3_P3-S1i - Number validator hard publish gate.md` (post-regen `check_card()` hook)  
- Phase 1 `card_pipeline.py` (3-call synthesis) · Phase 1 `regenerate_card.py` (legacy full draft replace)

---

## Narrative style (read this first)

Before P3-S1k, editorial “send back” always meant **regenerating the entire card**: a new draft row, three LLM calls, and approved sections discarded. That was expensive and ignored which ICE section actually failed review.

**P3-S1k** implements PRD2 **G-09 Option B**: the editor picks one failing section (Insight, Context, Evidence, Dissent, or Framework), adds a short annotation (max 500 chars), and the platform runs **one targeted regen** while treating all other sections as read-only context. Evidence regen rebuilds from the Factor DB (no LLM). After every section or full regen, the platform re-runs **`number_validator.check_card()`** and a new **`consistency_check`** (ticker/entity references in the regen output must not introduce symbols absent from approved sections or evidence).

Full regen remains available for fundamentally wrong cards, but it now updates the **same card row** (preserving audit history) with tiered guards: first full regen is silent; second requires confirmation; third and beyond block until **`po_regen_flag_cleared`** is set on the row. Each regen appends to **`regen_history`** JSONB on the card.

The live UI is **`RegenSection.tsx`** in the admin review aside (`/admin/review/[draftId]`), alongside the legacy **“Regenerate draft (new card)”** button from Phase 1.

**Tests executed and passed (P3-S1k–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Section regen + full regen guards | `python -m pytest -q backend/tests/test_card_regen.py` | **4 passed** (requires `SUPABASE_DB_URL`) |
| Consistency check unit | `python -m pytest -q backend/tests/test_consistency_check.py` | **2 passed** |
| Migration static SQL | `python -m pytest -q backend/tests/test_card_regen_migration_sql.py` | **1 passed** |
| ChecklistPanel RTL (updated props) | `pnpm test ChecklistPanel.test.tsx` (from `frontend/`) | **3 passed** |
| **Full backend CI** | `python -m ruff check backend` + `python -m pytest -q backend/tests` | **320 passed**, ruff clean |
| **Full frontend CI** | `pnpm lint` + `pnpm typecheck` + `pnpm test` + `pnpm build` | **Pass** |

**Three anchors for handover:** (1) **Apply migration `0028` before use** — `regen_history`, `full_regen_count`, and `po_regen_flag_cleared` columns must exist. (2) **Section/full regen updates the same card** — do not conflate with legacy `POST /api/admin/cards/{id}/regenerate` which archives the draft and creates a **new** card. (3) **Post-regen validator is mandatory** — P3-T4 editorial integrity gate assumes section regen cannot bypass `number_validator`; do not skip `_run_post_checks()` after regen.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S1k |
| **Title** | Targeted section regen |
| **Category** | **Full Stack** (backend services + admin API + editorial UI) |
| **Points / owner (plan)** | 3 · Sam |
| **Depends on** | P3-S1i (number validator hard publish gate) |
| **Parallel with** | P3-S1j (editorial checklist) |
| **Blocks** | **P3-T4** (editorial integrity test gate) |

**What this story aimed to achieve (plain language)**

When an editor rejects one ICE section, they should regenerate **only that section** with a short note explaining what to fix — without re-running the full 3-call pipeline or losing approved prose. Full regen should still exist for broken cards, but be logged, confirmation-gated after the first use, and blocked after two unless the Product Owner clears a flag. Every regen must be auditable and followed by automatic number and consistency checks.

**How it fits into the overall application**

- **Upstream:** P3-S1i ensures publish cannot proceed with ungrounded numbers; section regen must re-validate after partial edits. Phase 1 card pipeline provides synthesis/dissent/framework prompts and evidence building.
- **This story:** Adds in-place section regen, tiered full regen, `regen_history` audit trail, consistency check, and admin UI.
- **Downstream:** **P3-T4** proves editorial integrity across S1i + S1j + S1k; intelligence pipeline docs reference `regen_history` for decision logging.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **13.1** | `card_regen.py` — single-section LLM call via `regen_section.v1.md` with approved sections as read-only context; evidence section rebuilds Factor DB layer without LLM. |
| **13.2** | Migration `0028_card_regen_history.sql` — `regen_history` JSONB append-only audit; write on each regen. |
| **13.3** | Full regen in-place (3 LLM calls) + `full_regen_count` increment; confirm at ≥1; block at ≥2 without `po_regen_flag_cleared`. |
| **13.4** | `RegenSection.tsx` — section select, 500-char note, submit, loading/error, post-regen PASS/FAIL badges, full regen with confirm dialog. |
| **13.5** | Post-regen `_run_post_checks()` — `check_card()` + `check_after_regen()`; returned in API response. |
| **13.6** | Tests — only target section hash changes; full regen count guards; API shape; migration SQL. |

**Functional breakdown**

1. **Section regen request** — `POST …/regenerate-section` with `{ section, editor_note }`; `editor_note` required, max 500 chars; card must be `lifecycle_state = draft`.
2. **Approved context** — non-target ICE sections injected into regen prompt as read-only blocks; LLM instructed not to contradict them.
3. **Section-specific behaviour** — Insight/Context/Dissent/Framework: one LLM call + MMJ/number grounding validators (same rules as draft pipeline). Evidence: `_build_evidence_layer()` from event + critical facts gate (no slot consumed).
4. **Persist in place** — `update_card_after_section_regen()` updates one column + appends `regen_history` + accumulates token/cost counters on the same `cards.id`.
5. **Post-regen checks** — number validator on full card; consistency check flags new tickers in regen text not present in approved sections or evidence corpus.
6. **Full regen** — re-runs synthesis → dissent → framework on same row; replaces signals and instrument assessments; increments `full_regen_count`; tiered confirm/block rules.
7. **UI reload** — after regen, `ReviewWorkspace` calls `load()` so checklist and number validation refresh from GET card.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Empty `editor_note` | 422 `regen_rejected` — note required |
| `editor_note` > 500 chars | 422 `regen_rejected` |
| Card not draft | 422 `regen_rejected` |
| `full_regen_count >= 1` and `confirmed: false` | 409 `full_regen_confirm_required` |
| `full_regen_count >= 2` and `po_regen_flag_cleared = false` | 423 `full_regen_blocked` |
| Regen introduces ticker (e.g. ICICIBANK) not in approved/evidence | Consistency **FAIL** (non-blocking for save — editor sees badge) |
| Ungrounded number after section regen | Number validator **FAIL** in response (publish still blocked via S1i) |
| Daily/monthly LLM cap | 429 / 402 same as draft pipeline |
| Legacy `POST …/regenerate` | Unchanged — creates **new** draft, archives old (Phase 1 send-back) |

**Business rules enforced**

- **G-09 Option B:** Targeted regen default; consistency check; tiered full regen confirm; `regen_history` audit.
- **Numeric integrity:** Regen prose validated with `validate_numbers_in_evidence` before persist; publish gate re-run via `check_card()` after regen.
- **Cost control:** Section regen consumes one daily LLM slot (except evidence rebuild); full regen consumes three slots (one per pipeline call).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **In-place regen on same `cards.id`** | Preserves `full_regen_count`, `regen_history`, and editor session URL | Always create new card like P1 — loses audit counters on one row |
| **Admin + `/api/cards` alias routes** | Plan specifies `/api/cards/{id}/regenerate-section`; live UI uses `/api/admin/cards/…` like publish | Admin-only route — would miss plan API contract |
| **`RegenSection.tsx` under `admin/review/_components/`** | Plan referenced `(app)/editor/cards/[id]/` which does not exist; editorial workspace is `admin/review` | New editor route tree — duplicate surface |
| **Evidence regen = Factor DB rebuild, no LLM** | Evidence is structured data in this codebase, not LLM-generated in P1 pipeline | LLM regen of evidence markdown — risk of fabricated numerics |
| **Consistency = new-ticker detection** | Workshop “simple: extract entity names, verify no conflicts” — implementable without NLP | Full semantic contradiction detection — deferred |
| **PO clear via DB column only** | PRD2 says PO review flag; no admin UI in scope for S1k | Build PO clear API — out of story points |
| **Keep legacy full regenerate endpoint** | P1 send-back flow may still be in use; labelled “new card” in UI | Remove legacy endpoint — breaking change |

⚠️ **Do not skip post-regen `check_card()`** — P3-T4 editorial integrity gate depends on section regen not bypassing the S1i hard gate.

⚠️ **Do not merge section regen with legacy `/regenerate`** — different semantics (same row vs new card).

⚠️ **Migration `0028` is mandatory** — regen endpoints will fail against DBs without new columns.

**Assumptions**

- Editors use `/admin/review/[draftId]` for draft review (not a separate `(app)/editor` tree).
- PO clears blocked full regen via direct SQL `UPDATE cards SET po_regen_flag_cleared = true` until a future admin tool exists.
- P3-S1j editorial checklist may be complete in parallel; regen UI does not depend on checklist PASS to run.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S1i** — `check_card()` post-regen; **P1-S7** — prompts, evidence layer, validators; **P1-S8** — legacy regenerate + admin review shell |
| **Parallel** | **P3-S1j** — checklist + publish gate (regen does not require checklist PASS first) |
| **Downstream** | **P3-T4** — editorial integrity test gate across S1i + S1j + S1k |

**Shared components touched**

| Component | Role |
|-----------|------|
| `card_regen.py` | Section + full regen orchestration |
| `consistency_check.py` | Post-regen ticker conflict detection |
| `card_repository.py` | Fetch regen fields; in-place UPDATE helpers |
| `number_validator.py` | Post-regen hard validation (read-only call) |
| `card_pipeline.py` | Reused private helpers (`_build_evidence_layer`, validators, full regen 3-call flow) |
| `admin_review.py` | Primary editorial API routes |
| `cards.py` | Public alias routes for plan contract |
| `RegenSection.tsx` | Targeted regen UI |
| `ChecklistPanel.tsx` | Embeds `RegenSection`; legacy send-back retained |

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Service orchestration** — `card_regen.py` coordinates LLM, DB update, and post-checks; no regen logic in route handlers.
- **Append-only audit** — `regen_history = COALESCE(regen_history, '[]') \|\| new_entry::jsonb` per regen.
- **Dual route registration** — `admin_review` implements handlers; `cards.py` delegates for `/api/cards/{id}/…` paths.

**Database schema**

| Column | Table | Type | Purpose |
|--------|-------|------|---------|
| `regen_history` | `cards` | `jsonb NOT NULL DEFAULT '[]'` | Audit entries: section, note, timestamp, model, tokens |
| `full_regen_count` | `cards` | `integer NOT NULL DEFAULT 0` | Tiered full regen guard counter |
| `po_regen_flag_cleared` | `cards` | `boolean NOT NULL DEFAULT false` | PO override after count ≥ 2 |

**`regen_history` entry shape**

```json
{
  "regen_type": "section",
  "section": "insight",
  "editor_note": "Lead with transmission lag, not headline.",
  "timestamp": "2026-05-31T12:00:00+00:00",
  "model": "gemini-pro",
  "tokens_used": 100,
  "input_tokens": 40,
  "output_tokens": 60
}
```

**API contracts**

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/admin/cards/{id}/regenerate-section` | Primary editorial path |
| POST | `/api/cards/{id}/regenerate-section` | Plan contract alias |
| POST | `/api/admin/cards/{id}/regenerate-full` | In-place full 3-call regen |
| POST | `/api/cards/{id}/regenerate-full` | Plan contract alias |
| GET | `/api/admin/cards/{id}` | Now includes `regen_history`, `full_regen_count`, `po_regen_flag_cleared` |

**Section regen request**

```json
{
  "section": "insight",
  "editor_note": "Too generic — name the crude pass-through channel."
}
```

**Section regen success response (200)**

```json
{
  "card_id": "uuid",
  "section": "insight",
  "previous_hash": "sha256…",
  "new_hash": "sha256…",
  "number_validation": { "status": "PASS", "ungrounded": [], "missing_provenance": [], "comparative_flags": [] },
  "consistency_check": { "status": "PASS", "conflicts": [] }
}
```

**Full regen request**

```json
{
  "editor_notes": "Card thesis is wrong — rebuild from event.",
  "confirmed": true
}
```

**Error codes**

| HTTP | `detail.code` | When |
|------|---------------|------|
| 409 | `full_regen_confirm_required` | Second full regen without `confirmed: true` |
| 423 | `full_regen_blocked` | Third+ full regen without PO flag |
| 422 | `regen_rejected` | Business rule (bad note, not draft, etc.) |
| 422 | `regen_pipeline_failed` | LLM/validation failure |

**UI/UX**

- Section dropdown (Insight / Context / Evidence / Dissent / Framework).
- 500-char counter enforcement client-side; server validates max length.
- Post-regen panel shows Number validator + Consistency badges.
- Full regen button label changes when `full_regen_count >= 1`; browser `confirm()` on 409 retry.
- Blocked state message when `full_regen_count >= 2` and PO flag not cleared.

**Libraries / tools**

| Library | Purpose |
|---------|---------|
| Existing Gemini client (`LlmClient`) | Section + full regen LLM calls |
| `regen_section.v1.md` prompt | Single-section revision template |
| shadcn `Select`, `Textarea`, `Button` | RegenSection form |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0028_card_regen_history.sql` | `backend/db/migrations/0028_card_regen_history.sql` | Adds `regen_history`, `full_regen_count`, `po_regen_flag_cleared` |
| `card_regen.py` | `backend/app/services/card_regen.py` | Section + full regen orchestration |
| `consistency_check.py` | `backend/app/services/consistency_check.py` | Post-regen ticker consistency |
| `regen_section.v1.md` | `backend/prompts/regen_section.v1.md` | Targeted section LLM prompt |
| `RegenSection.tsx` | `frontend/app/admin/review/_components/RegenSection.tsx` | Section picker, note, regen actions, post-check display |
| `test_card_regen.py` | `backend/tests/test_card_regen.py` | Section hash isolation, full regen guards, API shape |
| `test_consistency_check.py` | `backend/tests/test_consistency_check.py` | Consistency PASS/FAIL unit tests |
| `test_card_regen_migration_sql.py` | `backend/tests/test_card_regen_migration_sql.py` | Static SQL assertions for migration 0028 |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `migrate.py` | `backend/app/db/migrate.py` | Registered `0028_card_regen_history.sql` |
| `card_repository.py` | `backend/app/services/card_repository.py` | SELECT regen columns; `update_card_after_section_regen`, `update_card_after_full_regen` |
| `admin_review.py` | `backend/app/api/admin_review.py` | Regen section/full endpoints; serialize regen fields on GET |
| `cards.py` | `backend/app/api/cards.py` | Alias routes delegating to admin handlers |
| `ChecklistPanel.tsx` | `frontend/app/admin/review/_components/ChecklistPanel.tsx` | Embeds `RegenSection`; new props `draftId`, `onReload`, regen counts |
| `ChecklistPanel.test.tsx` | `frontend/app/admin/review/_components/ChecklistPanel.test.tsx` | Updated for new required props |
| `ReviewWorkspace.tsx` | `frontend/app/admin/review/[draftId]/ReviewWorkspace.tsx` | Passes regen props; reload after regen |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S1k AC + tasks **13.0**–**13.6** marked complete |

**Not modified (intentionally)**

| File | Note |
|------|------|
| `regenerate_card.py` | Legacy send-back (new card) unchanged |
| `publish_card.py` | Publish gate unchanged — regen does not auto-publish |
| `number_validator.py` | Consumed via `check_card()` only — no schema change |

---

### A8. TESTS EXECUTED

| Test file | Test function | Status | What it verifies |
|-----------|---------------|--------|------------------|
| `test_card_regen.py` | `test_section_regen_only_target_hash_changes` | **Pass** | Only `insight_layer` changes; context/dissent/framework unchanged; `regen_history` appended; post-checks PASS |
| `test_card_regen.py` | `test_full_regen_count_requires_confirm` | **Pass** | `full_regen_count=1` raises `FullRegenConfirmRequiredError` without confirm |
| `test_card_regen.py` | `test_full_regen_blocked_at_two_without_po_flag` | **Pass** | `full_regen_count=2` raises `FullRegenBlockedError` |
| `test_card_regen.py` | `test_regenerate_section_api_returns_post_checks` | **Pass** | `POST /api/cards/{id}/regenerate-section` returns validation + consistency payload |
| `test_consistency_check.py` | `test_consistency_pass_when_regen_reuses_approved_ticker` | **Pass** | HDFCBANK in regen when already in approved sections → PASS |
| `test_consistency_check.py` | `test_consistency_fail_on_new_ticker` | **Pass** | ICICIBANK introduced → FAIL with conflict |
| `test_card_regen_migration_sql.py` | `test_card_regen_migration_adds_audit_columns` | **Pass** | Migration SQL contains all three new columns |

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

**Result:** **320** backend tests passed, ruff clean; frontend CI green (31-05-2026 implementation run).

**Manual testing (recommended after deploy):** See B6 — migration apply + smoke test on draft review page.

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Migration:** `backend/db/migrations/0028_card_regen_history.sql`  
**Sequence:** After `0027_confidence_audit.sql` — registered in `backend/app/db/migrate.py`.

```sql
ALTER TABLE public.cards
  ADD COLUMN IF NOT EXISTS regen_history jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS full_regen_count integer NOT NULL DEFAULT 0
    CHECK (full_regen_count >= 0),
  ADD COLUMN IF NOT EXISTS po_regen_flag_cleared boolean NOT NULL DEFAULT false;
```

**Apply (once per environment):**

```powershell
python scripts/apply_migrations.py
```

Requires `SUPABASE_DB_URL` in `.env.local` (or equivalent).

**No seed data** — existing cards get defaults (`regen_history = []`, `full_regen_count = 0`).

---

### B2. API / INTEGRATION CONTRACTS

**POST `/api/admin/cards/{card_id}/regenerate-section`**

- **Auth:** None today (Phase 1 admin pattern).
- **Cache:** `Cache-Control: no-store`.
- **Body:** `{ "section": "insight"|"context"|"evidence"|"dissent"|"framework", "editor_note": string (1–500) }`
- **Success 200:** See A5 response shape.
- **Errors:** 404 card not found; 422 regen rejected / pipeline failed; 429 daily cap; 402 monthly budget.

**POST `/api/admin/cards/{card_id}/regenerate-full`**

- **Body:** `{ "editor_notes": string (optional), "confirmed": boolean }`
- **Success 200:** `{ card_id, full_regen_count, number_validation, consistency_check }` (consistency always PASS for full regen — section-level check skipped).
- **409:** `full_regen_confirm_required` — UI should retry with `confirmed: true`.
- **423:** `full_regen_blocked` — PO must clear flag in DB.

**GET `/api/admin/cards/{card_id}` — new fields**

```json
{
  "regen_history": [ /* array of audit entries */ ],
  "full_regen_count": 0,
  "po_regen_flag_cleared": false
}
```

**Legacy (unchanged)**

| Method | Route | Behaviour |
|--------|-------|-----------|
| POST | `/api/admin/cards/{id}/regenerate` | New draft card + archive old (P1) |

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Section regen flow**

```
POST regenerate-section
├── fetch_card_detail_for_review
├── validate draft + editor_note (1–500 chars)
├── if section == evidence
│   └── rebuild evidence_layer (no LLM slot)
└── else
    ├── consume_slot_or_raise()
    ├── LLM regen_section.v1 with approved sections block
    ├── validate_mmj_tags + validate_numbers_in_evidence
    └── section-specific quality (_validate_dissent / _validate_framework)
├── update_card_after_section_regen + append regen_history
├── refresh card detail
└── _run_post_checks → number_validation + consistency_check
```

**Full regen tier decision tree**

```
full_regen_count >= 2 AND NOT po_regen_flag_cleared → BLOCK (423)
full_regen_count >= 1 AND NOT confirmed → CONFIRM REQUIRED (409)
else → run 3-call pipeline in place, increment full_regen_count
```

**Consistency check logic**

```
approved_tickers = tickers from all sections EXCEPT regen target
allowed = approved_tickers ∪ evidence_tickers
regen_tickers = tickers in new regen text
conflicts = regen_tickers - allowed (minus blocklist: ICE, RBI, NIM, …)
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Severity | Notes |
|------|----------|-------|
| **No PO clear API/UI** | Medium | Operator runs SQL to set `po_regen_flag_cleared = true` |
| **Consistency is ticker-only** | Low | Does not detect semantic contradictions between sections |
| **No dedicated RegenSection RTL tests** | Low | ChecklistPanel tests cover mount with new props only |
| **Two full regen paths in UI** | Low | “Regenerate draft (new card)” vs “Full regen all sections” — document for editors |
| **Plan path vs repo path** | Doc only | Plan listed `(app)/editor/cards/[id]/RegenSection.tsx`; live path is `admin/review/_components/` |
| **`regen_history` not exposed in Thread** | By design | Audit for editorial/ops; user-facing card detail unchanged |

---

### B5. TESTING NOTES

**Automated**

- DB integration: section hash isolation, regen history write, full regen guards (needs `SUPABASE_DB_URL`).
- Unit: consistency PASS/FAIL without DB.
- Static: migration SQL column names.
- API: mocked regen response shape via `/api/cards/…` alias.

**Manual (recommended after deploy)**

1. Apply migration `0028`.
2. Open draft at `/admin/review/{uuid}`.
3. Regenerate **Context** only with a note — confirm Insight unchanged on card reader.
4. Run full regen twice — confirm dialog on second attempt.
5. Set `full_regen_count = 2` in SQL — confirm UI blocks third full regen until PO flag cleared.

**Known gaps**

- No E2E Playwright for regen flow.
- No test for evidence-only regen path with live Factor DB (mocked in section LLM tests only).
- Full regen 3-call success path not integration-tested with mocked LLM (guard tests only).

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Item | Required? |
|------|-----------|
| New env vars | **No** |
| Migration `0028` | **Yes — once per DB env** |
| Feature flags | **No** |
| Gemini API key | **Yes** (existing — for LLM section/full regen) |

**Deployment sequencing**

1. Deploy **backend** with migration applied first.
2. Deploy **frontend** with `RegenSection` UI.
3. Backend without migration → SQL errors on regen endpoints.

**PO unblock SQL (when needed)**

```sql
UPDATE public.cards
SET po_regen_flag_cleared = true
WHERE id = '<card-uuid>';
```

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read PRD2 §5.3 and G-09 workshop Option B decisions.
2. Ensure migration `0028` applied in target environment.
3. After changing regen prompts or validators, run `test_card_regen.py` and `test_consistency_check.py`.
4. Do not remove `_run_post_checks()` — P3-T4 depends on it.

**Common mistakes**

- Conflating **section regen** (same card) with **legacy regenerate** (new card).
- Skipping migration — `regen_history` column missing causes 500 on regen.
- Treating consistency FAIL as HTTP error — it is returned in 200 response for editor review; publish still blocked separately via number validator / checklist.
- Patching `app.services.card_regen.regenerate_section` in API tests without patching `app.api.admin_review.regenerate_section` — import binding issue.

**Where to find related code**

| Concern | Path |
|---------|------|
| Section/full regen core | `backend/app/services/card_regen.py` |
| Consistency check | `backend/app/services/consistency_check.py` |
| DB updates | `backend/app/services/card_repository.py` |
| Admin API | `backend/app/api/admin_review.py` |
| Public API alias | `backend/app/api/cards.py` |
| Regen prompt | `backend/prompts/regen_section.v1.md` |
| Editorial UI | `frontend/app/admin/review/_components/RegenSection.tsx` |
| Number validator (post-regen) | `backend/app/services/number_validator.py` → `check_card()` |
| Legacy send-back | `backend/app/services/regenerate_card.py` |

**Next story (same stream)**

- **P3-T4** — Editorial integrity test gate: prove S1i publish block + S1j checklist + S1k post-regen validator cannot be bypassed end-to-end.

---

## Handover to P3-T4

P3-S1k delivers:

1. **`POST …/regenerate-section`** and **`POST …/regenerate-full`** with post-regen **`number_validation`** and **`consistency_check`** in the response.
2. **`regen_history`** audit trail on the card row.
3. **Tiered full regen guards** (`full_regen_count`, `po_regen_flag_cleared`).

P3-T4 should verify:

- Section regen cannot leave card in a publishable state when number validator FAILs.
- Full regen count enforcement (confirm + block) via API tests.
- Optional: consistency FAIL surfaced to editor without silent discard.

Do not start P3-T4 by weakening post-regen validation or adding publish shortcuts after regen.
