# Post Implementation Detailed Document — P1-S7

**Version:** v1.1 | **Date:** 18-05-2026  
**Story ID:** P1-S7 (Phase 1, Story 7)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`

---

Narrative style:

Phase 1 needed to turn a **queued editorial event** into a **draft Event Intelligence Card** without letting the model invent facts. This story implements a **three-call Gemini pipeline** — **synthesis**, then **dissent**, then **framework** — with **hard validators** that reject drafts whose numbers are not grounded in a deterministic **Evidence bundle** built from the Factor DB plus event metadata, and that reject prose that omits **MMJ tags** on quantitative sentences. A **UTC daily generation budget** (50 slots) is enforced in Postgres so runaway spend cannot silently burn the account.

**What actually runs**

`draft_card_from_event(event_id, …)` loads the `events` row over Postgres, builds Evidence by materialising the **banking** sector sensitivity matrix (`fetch_matrix_rows`), reserves one **atomic** LLM slot via `try_consume_llm_card_slot`, runs three Gemini **`generate_content`** calls (`google-genai` SDK) expecting **JSON-only** replies, validates numbers and MMJ on Insight, Context, instrument assessment text, dissent, and framework copy, then **inserts** one `cards` row and any nested `signals` and `instrument_assessments` in a single transaction.

**API surface**

`POST /api/cards/draft-from-event` accepts JSON `{"event_id": "<uuid>", "editor_notes": null }` and returns `{"card_id": "<uuid>"}` or structured HTTP errors (`404` missing event, `429` daily cap, `422` validation or pipeline failure).

**Before you call it “done” in an environment**

Apply migration **0008**, ensure **`SUPABASE_DB_URL`** is set for the API (validators and Factor DB already depended on it; the cap RPC must be executable for the DB role you use), set **`GEMINI_API_KEY`** (or **`GOOGLE_API_KEY`** — same value), and optionally **`GEMINI_MODEL`**.

**If you remember one thing**

⚠️ **Numeric grounding is substring-based against a normalised Evidence corpus** — it stops obvious hallucinations but is not a formal proof system; editorial review (P1-S8) and prompt discipline remain mandatory.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S7 |
| **Title** | LLM 3-call card-synthesis pipeline (Gemini) |
| **Category** | **Backend** (PostgreSQL migration + RPC, FastAPI route, Python services, Gemini / `google-genai` integration, automated tests) |

**What this story aimed to achieve (plain language)**

1. Turn a **draft `event`** into a **draft `cards` row** with ICE-shaped fields: Insight, Context, structured Evidence snapshot, dissenting view, and Framework Behind This.  
2. Use **three separate, versioned prompts** so prompt lineage is auditable (`prompt_version` on the card combines the three template ids).  
3. **Block** synthesis (and downstream steps) if any number in validated prose cannot be found in the Evidence text, or if any sentence containing a digit lacks `[MEASURED]`, `[MODELLED]`, or `[JUDGED]`.  
4. Run **dissent** as its own model call and **fail** if the payload is empty or structurally generic.  
5. Run **framework last**, persist it on the card, and record **token counts + estimated USD cost** while enforcing a **50 drafts/day UTC** ceiling via the database.

**How it fits into the overall application**

P1-S7 is the **editorial “draft card” factory** between **P1-S6** (events queue) and **P1-S8** (review/publish). It depends on **P1-S4** (core tables incl. `signals`, `instrument_assessments`), **P1-S5** (Factor DB for real banking sensitivities in Evidence), and **P1-S6** (`events` rows). Downstream: Pulse/Thread/feed stories consume **published** cards; S8 regenerate will reuse this pipeline with `editor_notes`.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items (plan 7.1–7.10) and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **7.1** | `backend/prompts/synthesis.v1.md` — JSON-only ICE synthesis; numeric + MMJ rules; Factor Evidence + event vars. |
| **7.2** | `backend/prompts/dissent.v1.md` — mechanistic dissent only; JSON `dissenting_view`. |
| **7.3** | `backend/prompts/framework.v1.md` — transferable pattern; JSON with `pattern_name` + `framework_behind_this`. |
| **7.4** | `app/services/llm_client.py` — `LlmClient.complete_json()`, retries on rate/5xx, YAML front matter stripped before send, structured log line per success. |
| **7.5** | `app/services/card_pipeline.py` — `draft_card_from_event()` orchestration, Evidence build, three calls, validators, persist bundle. |
| **7.6** | `app/services/number_validator.py` — extract numeric tokens from prose; require each appears in normalised Evidence corpus. |
| **7.7** | `app/services/mmj_validator.py` — any sentence containing a digit must include an MMJ tag in that sentence. |
| **7.8** | `app/services/cost_guard.py` + SQL `try_consume_llm_card_slot` — atomic daily cap before LLM calls. |
| **7.9** | `app/api/cards.py` — `POST /api/cards/draft-from-event`. |
| **7.10** | `tests/test_card_pipeline.py`, `test_number_validator.py`, `test_mmj_validator.py`. |

**Functional breakdown**

- **Evidence layer:** Markdown listing each banking ticker × factor sensitivity, MMJ, and source URL; plus a **macro stub** stating Phase 1 has no live macro feed; plus full matrix JSON and event snapshot inside `evidence_layer` JSON for audit/replay.  
- **Synthesis:** Model returns title, insight, context, optional assessments and signals; assessments/signals coerced and capped.  
- **Dissent:** Second call; specificity heuristics (minimum length; multiple generic phrase hits fail).  
- **Framework:** Third call; requires non-trivial `pattern_name` and body; stored as Markdown prefix `**pattern**` + body.  
- **Persistence:** `insert_draft_card_bundle` inserts `cards` then child rows; card defaults `lifecycle_state = draft`.

**Edge cases, validations, and error handling**

- **Event missing:** `LookupError` → API `404`.  
- **Daily cap:** `DailyLLMCardCapError` → API `429` with `llm_daily_cap`.  
- **Validation failures:** dissent/framework/number/MMJ → `422` with `draft_pipeline_failed`.  
- **Missing `GEMINI_API_KEY` / `GOOGLE_API_KEY`:** `RuntimeError` when constructing default client → `422` in current API mapping.  
- **Slot consumed before LLM:** cap increments atomically **before** the first Gemini call (after Evidence build and client construction); if the model fails mid-way, the slot is still consumed (cost-control posture).

**Business rules enforced**

- PRD-aligned **no fabricated numerics** relative to Evidence corpus (validator enforcement on validated fields).  
- **MMJ tags** required on quantitative sentences in the same sentence.  
- **Separate dissent call**; empty or generic dissent fails the draft.  
- **Framework is last call** and persisted on the card.  
- **50 card generations per UTC day** max via RPC.  
- ⚠️ **Phase 1 API is not authenticated** (aligned with `GET /admin/events` posture); production should treat this as an internal-only route until RBAC is added.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Parent `cards` table + migration 0008** | `signals` / `instrument_assessments` already referenced `card_id` in P1-S4 without a parent; this story adds the missing entity. | JSON-only card blob in `events`: breaks normalised feeds and child tables. |
| **Postgres RPC for daily cap** | Same atomic pattern as NewsAPI budget in 0006; safe under concurrent API workers. | In-memory or Redis counter: extra infra; app-level read-modify-write races. |
| **`GRANT EXECUTE … TO service_role` only** | Prevents unauthorised budget draining via PostgREST exposure. | Public execute: security risk. |
| **Evidence = banking matrix in Phase 1** | PRD Phase 1 starts with Banking slice; keeps implementation deterministic. | Dynamic sector from event category: more logic; can be Phase 2. |
| **JSON extraction via brace slicing** | Robust to occasional preamble text from the model. | Strict `response_format` tool use: SDK/version coupling. |
| **Rough USD cost from token counts** | Satisfies “per-card cost recorded” without billing integration. | Omit cost: fails acceptance; live billing API: out of scope. |
| **`draft_card_from_event` name** | Clear entrypoint; plan text said `draft_card`. | Rename to match plan only: cosmetic. |

**Assumptions**

- DB connection role used by the API can execute `try_consume_llm_card_slot` (typically Supabase `postgres` superuser or a role granted execute).  
- Model id in `GEMINI_MODEL` must support `response_mime_type=application/json` (e.g. `gemini-2.0-flash`).

**⚠️ Critical — do not reverse lightly**

- Do not **disable numeric or MMJ validators** without Product/Compliance sign-off — they implement PRD §6.3 constraints.  
- Do not **merge dissent into synthesis** — acceptance criteria requires a **separate** dissent call.  
- Do not **grant `try_consume_llm_card_slot` to `anon`**.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Dependency |
|-----------|------------|
| **Upstream** | P1-S4 (`events`, `signals`, `instrument_assessments`, enums), P1-S5 (Factor DB + `fetch_matrix_rows`), P1-S6 (draft events to consume). |
| **Downstream** | P1-S8 (review, publish, regenerate with `editor_notes`), P1-S9/P1-S10 (UI against card JSON), P1-S11+ (signals lifecycle expects `cards` parent). |
| **Shared modules** | `app/db/connection.py`, `app/services/factor_db.py`, `app/models/enums.py` (`LifecycleState`, `SignalState`). |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Pattern** | Service layer pipeline + thin API + repository-style SQL for card bundle insert. |
| **Schema** | `cards` 1→N `signals`, 1→N `instrument_assessments`; FKs added in 0008; `ON DELETE CASCADE` from card. |
| **API** | `POST /api/cards/draft-from-event`; no auth in Phase 1. |
| **Third-party** | `google-genai` Python SDK (Gemini API). |
| **Prompts** | Repo-checked markdown under `backend/prompts/` with semantic version in filename; front matter stripped at load. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0008_cards_llm_budget.sql` | `backend/db/migrations/0008_cards_llm_budget.sql` | `cards`, `llm_card_daily_usage`, RPC cap, FKs. |
| `synthesis.v1.md` | `backend/prompts/synthesis.v1.md` | Synthesis prompt (Role 1). |
| `dissent.v1.md` | `backend/prompts/dissent.v1.md` | Dissent prompt (Role 2). |
| `framework.v1.md` | `backend/prompts/framework.v1.md` | Framework prompt (Role 3). |
| `llm_client.py` | `backend/app/services/llm_client.py` | Gemini client + prompt load/render + JSON parse. |
| `card_pipeline.py` | `backend/app/services/card_pipeline.py` | Three-call orchestration + validation. |
| `card_repository.py` | `backend/app/services/card_repository.py` | Fetch event + insert card bundle. |
| `number_validator.py` | `backend/app/services/number_validator.py` | Numeric grounding checks. |
| `mmj_validator.py` | `backend/app/services/mmj_validator.py` | MMJ tag checks. |
| `cost_guard.py` | `backend/app/services/cost_guard.py` | Cap + token cost estimate helper. |
| `cards.py` | `backend/app/api/cards.py` | FastAPI draft route. |
| `test_card_pipeline.py` | `backend/tests/test_card_pipeline.py` | Mocked pipeline + migration smoke asserts. |
| `test_number_validator.py` | `backend/tests/test_number_validator.py` | Hallucination + grounded number cases. |
| `test_mmj_validator.py` | `backend/tests/test_mmj_validator.py` | Missing/present MMJ cases. |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `migrate.py` | `backend/app/db/migrate.py` | Registered migration `0008_cards_llm_budget.sql`. |
| `main.py` | `backend/app/main.py` | Mounted `cards` router at `/api/cards`. |
| `settings.py` | `backend/app/core/settings.py` | `gemini_api_key` (env `GEMINI_API_KEY` or `GOOGLE_API_KEY`), `gemini_model`. |
| `pyproject.toml` | `backend/pyproject.toml` | `google-genai` dependency (replaces legacy Anthropic SDK). |
| `finnwise-phase1-implementation-tasks.md` | `docs/plans/finnwise-phase1-implementation-tasks.md` | P1-S7 tasks marked complete (plan hygiene). |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**`public.cards`**

| Column | Type | Notes |
|--------|------|--------|
| `id` | uuid | PK |
| `event_id` | uuid | FK → `events.id`, `ON DELETE CASCADE` |
| `title`, `insight_layer`, `context_layer` | text | ICE narrative layers |
| `evidence_layer` | jsonb | Structured Evidence + matrix snapshot |
| `dissenting_view`, `framework_behind_this` | text | Post-validation prose |
| `prompt_version` | text | e.g. `synthesis.v1\|dissent.v1\|framework.v1` |
| `lifecycle_state` | `lifecycle_state` | Default `draft` |
| `llm_input_tokens`, `llm_output_tokens` | int | Summed across three calls |
| `llm_cost_usd` | numeric(14,6) | Estimated from tokens |
| `created_at`, `updated_at` | timestamptz | Defaults `now()` |

**`public.llm_card_daily_usage`**

- `usage_date` date PK (UTC), `generations_count` int ≥ 0.

**`try_consume_llm_card_slot(p_max default 50)`**

- `SECURITY DEFINER`, `REVOKE ALL FROM PUBLIC`, `GRANT EXECUTE TO service_role`.

**Foreign keys**

- `signals.card_id` → `cards.id`  
- `instrument_assessments.card_id` → `cards.id`  

**Sequencing:** apply after `0007_factor_db.sql` (Factor DB must exist for Evidence build).

---

### B2. API / INTEGRATION CONTRACTS

**`POST /api/cards/draft-from-event`**

- **Request body**

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "editor_notes": null
}
```

- **Response 200**

```json
{ "card_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8" }
```

- **Errors**

| Status | `detail.code` (when present) | Meaning |
|--------|------------------------------|---------|
| 404 | `event_not_found` | No `events` row for id |
| 429 | `llm_daily_cap` | Daily slot budget exhausted |
| 422 | `draft_pipeline_failed` | Validation, JSON parse, or runtime configuration |

- **Auth:** none in Phase 1 (⚠️ treat as internal).

**External:** Google Gemini API (`google-genai` SDK), authenticated with `GEMINI_API_KEY` or `GOOGLE_API_KEY`.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

1. **Evidence corpus** = markdown + macro stub + JSON serialisations of matrix + event snapshot; commas stripped and lowercased for **number** checks.  
2. **Number validator** extracts currency/percent/numeric regex tokens; each normalised token must be a substring of the corpus.  
3. **MMJ validator** splits on sentence boundaries; any sentence with `\d` must match `\[(MEASURED|MODELLED|JUDGED)]`.  
4. **Dissent** must exceed length floor; two or more “generic disclaimer” snippets → `DissentQualityError`.  
5. **Framework** must include `pattern_name` length ≥ 6 chars and body length ≥ 120 chars.  
6. **Cost:** `estimate_cost_usd` uses fixed approximate per-million token rates (documented in code) — **not** vendor invoicing.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

- **Substring numeric matching** can theoretically false-negative/positive on pathological phrases; future work could use token-aligned or structured citation spans.  
- **Macro signals** are stubbed; synthesis must not invent macro levels — enforced by prompt + Evidence stub, not a live feed.  
- **Single sector (banking)** Evidence for all events in Phase 1; cross-sector cards need category→sector mapping later.  
- **Daily cap consumes a slot even if LLM fails after reservation** — intentional cost control; may waste slots on outage days.  
- ⚠️ **No API authentication** — must be gated before any public network exposure.

---

### B5. TESTING NOTES

| Automated | Coverage |
|-----------|----------|
| `test_card_pipeline.py` | Mocked LLM sequence, asserts `prompt_version`, token sums, framework prefix; migration file keywords. |
| `test_number_validator.py` | Rejects ungrounded “99.9%”; accepts grounded “-4”. |
| `test_mmj_validator.py` | Fails bare quant sentence; passes tagged; multi-sentence split. |

**Manual:** Run against a real `event_id` with valid DB + key to validate end-to-end latency and model behaviour (not automated in CI here).

**Gaps:** No contract test against live Gemini; no load test on cap RPC under contention.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Gemini API key from AI Studio (server-only; aliases both env names). |
| `GEMINI_MODEL` | Model id (default `gemini-2.0-flash` in settings). |
| `SUPABASE_DB_URL` | Required for Factor DB, event fetch, card insert, cap RPC. |
| `SUPABASE_URL` + service role | Still used by other stories (events REST); card path uses DB URL for this flow. |

**Deploy:** Apply **0008** before enabling the route in production; run from migration runner (`app.db.migrate` or equivalent ops process).

---

### B7. HANDOVER NOTES FOR DEVELOPERS

- **Entrypoint:** `app/services/card_pipeline.py` → `draft_card_from_event`.  
- **Prompt edits:** change only versioned files under `backend/prompts/`; bump filename or front-matter version when behaviour changes and update `PROMPT_*_VERSION` constants if you fork a new generation of templates.  
- **Do not** call `try_consume_llm_card_slot` from client-side code — server only.  
- **Regenerate (S8):** pass `editor_notes` into the pipeline; synthesis template already injects an editor-notes section.  
- **On-call / context:** Product Owner for prompt wording and sector scope; backend owner for DB role grants and cap tuning.
