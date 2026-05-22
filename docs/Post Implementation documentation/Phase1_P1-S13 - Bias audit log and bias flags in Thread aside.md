# Post Implementation Detailed Document — P1-S13

**Version:** v1.0 | **Date:** 21-05-2026  
**Story ID:** P1-S13 (Phase 1, Story 13)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`  
**PRD anchor:** §6.5 Bias Audit Log, §5 Screen 3 aside — Bias Flags

---

## Narrative style (read this first)

FinnWise’s product promise includes **bias honesty**: readers should see uncertainty **before** they absorb a conclusion, not buried in footnotes. **P1-S10** shipped the Thread aside slot **`BiasFlags`** but fed it a **placeholder** `bias_audit` object from the server. **P1-S13** replaces that placeholder with a real audit pipeline: six bias types from the PRD are **detected**, **persisted**, and **surfaced** on every published card.

Architecturally, bias detection is a **post-publish side effect**, not part of the LLM draft loop. When an editor publishes a draft (**`publish_draft_card`**), the card and event transition to **`published`**, then **`bias_detector.detect_all(card_id)`** runs against live card + event data, writes rows to **`card_bias_flags`**, and embeds a frozen **`bias_audit`** JSON snapshot into the **append-only** **`track_record`** payload (alongside **`ice_snapshot`**). The Thread does not call a separate bias API: **`GET /api/cards/{id}`** already returns **`bias_audit`** inside the assembled card detail—**current** view reads live flags from the table; **original** view prefers the snapshot stored at publish time.

A second track handles **editorial coverage bias**, which the PRD treats as a **weekly** disclosure (“which event categories we covered vs omitted”). That is **not** stored per card; the **`weekly_bias_report`** cron writes **`notes/bias-report-YYYY-WW.md`** (gitignored) for editorial review.

**Three anchors for handover:** (1) **detect at publish**, not at draft generation; (2) **`track_record` carries `bias_audit` for Original view**—never UPDATE that table; (3) **sector concentration in V1 uses `event_category`**, not Factor DB sector slug, until a richer sector dimension exists on cards.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S13 |
| **Title** | Bias audit log + bias flags rendered in Thread aside |
| **Category** | **Full Stack** (Postgres migration + detector services + publish hook + weekly cron job + Thread UI/tests; no new public HTTP routes) |

**What this story aimed to achieve (plain language)**

1. Track **six bias types** from PRD §6.5: recency, sector concentration, narrative, editorial coverage (weekly), survivorship, and anchoring.  
2. **Flag** cards when rules fire (e.g. >60% of Evidence sources from the last 30 days; three consecutive published cards in the same category; high direction confidence with fewer than three Evidence sources).  
3. **Persist** per-card results in **`card_bias_flags`** and expose them through the existing **`bias_audit`** field on **`GET /api/cards/{id}`**.  
4. Keep **anchoring** and non-triggered checks in a **monitored** (grey) state; render **flagged** checks in **amber** in the Thread aside.  
5. Emit a **weekly markdown report** of editorial category coverage under **`notes/`**.

**How it fits into the overall application**

- **Upstream:** **P1-S7** (ICE + evidence JSON on cards), **P1-S8** (publish + `track_record`), **P1-S10** (`BiasFlags` aside + `bias_audit` contract on card detail).  
- **This story:** Makes the aside **trustworthy** and auditable; satisfies PRD “confidence before conclusion.”  
- **Downstream:** **P1-S14** (tester launch / go-no-go), **Phase 2** Lens and transparency pages may reuse **`card_bias_flags`** aggregates; **P1-S10** doc references to “placeholder bias” are now superseded for published cards.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items (plan mapping)**

| Sub-task | Scope |
|----------|--------|
| **13.1** | Migration **`0011_card_bias_flags.sql`**: table with **`card_id`**, **`bias_type`**, **`severity`** (`flagged` \| `monitored`), **`description`**, **`detected_at`**; unique **(card_id, bias_type)**. |
| **13.2** | **`detect_all(card_id)`** invoked from **`publish_draft_card`** after lifecycle transition to **`published`**; findings persisted; **`bias_audit`** included in **`track_record`** INSERT (not UPDATE). |
| **13.3** | **Recency**, **sector concentration**, **narrative** detectors implemented with PRD thresholds. |
| **13.4** | **Survivorship** (regex on ICE text for historical/backtest framing) and **anchoring** (always monitored; cites separate dissent LLM call). |
| **13.5** | **`weekly_bias_report`** job: counts cards per **`event_category`** over trailing 7 days; writes **`notes/bias-report-{ISO-week}.md`**. |
| **13.6** | **`build_card_detail`** serves real **`bias_audit`** (replaces **`bias_audit_placeholder()`** for current view); **`BiasFlags.tsx`** unchanged in contract—amber/grey blocks + optional note. |
| **13.7** | **`test_bias_detector.py`** (per detector + persist), **`test_weekly_bias_report.py`**, **`test_publish_writes_track_record.py`** (`bias_audit` in payload), **`BiasFlags.test.tsx`**. |

**Per-detector behaviour (code-level)**

| Bias type | Severity when triggered | Rule |
|-----------|-------------------------|------|
| **recency** | `flagged` | More than **60%** of Evidence rows with **`retrieved_at`** fall within the last **30 days** (uses **`build_evidence_rows`** from **`card_detail`**). |
| **sector_concentration** | `flagged` | The **3** most recently **`created_at`** cards in published lifecycles share the **same** **`events.category`** as the current card. |
| **narrative** | `flagged` | **`confidence_tier(event_confidence_score) == 'high'`** (score ≥ 70) **and** fewer than **3** Evidence sources after LLM-name filter. |
| **survivorship** | `flagged` | Insight/context/evidence markdown matches historical framing regex (`historical`, `backtest`, `since 20xx`, `over the past N years`). |
| **anchoring** | always `monitored` | V1 does not auto-flag; description explains separate dissent prompt (PRD §6.4). |
| **editorial_coverage** | N/A per card | Weekly **`notes/`** markdown only; lists covered vs uncovered **`event_category`** values. |

**Edge cases, validations, and error handling**

- **No dated Evidence sources:** Recency returns **monitored** with a generic “watching” message (cannot compute share).  
- **Fewer than 3 published cards in DB:** Sector concentration returns **monitored**.  
- **Publish without evidence sources:** Narrative may flag if event confidence is high and source count is 0.  
- **`detect_all` after publish:** Card must already be **`published`** so sector query includes the new card.  
- **⚠️ `track_record` append-only:** **`bias_audit`** is set in the **initial INSERT** payload; an UPDATE was attempted early in development and correctly rejected by **`deny_track_record_mutation()`**.  
- **Original view for cards published before P1-S13:** If **`track_record.payload`** lacks **`bias_audit`**, **`build_card_detail`** falls back to **live** **`card_bias_flags`** (may differ from Day-1; re-publish or backfill if strict immutability is required).

**Business rules enforced (PRD-aligned)**

- Bias flags appear in the **aside**, not footnotes (**P1-S10** layout).  
- Plain-English **`description`** strings per finding (no internal codes shown to users).  
- Evidence source counting **excludes** source names containing **`llm`**, **`gemini`**, or **`gpt`** (aligned with Thread Evidence hygiene).  
- Recency threshold is **strictly greater than** 60% (`share > 0.6`), not ≥ 60%.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Run detectors on publish only** | Flags matter for readers of **published** cards; draft review does not need full audit noise. | Run on every LLM draft: extra DB churn, misleading flags on unpublished text. |
| **`bias_audit` inside `track_record` INSERT** | Respects append-only triggers; Original view gets Day-1 bias state. | UPDATE payload after insert: **blocked** by DB policy. |
| **`event_category` as sector proxy** | Phase 1 events only have **`event_category`** enum, not Factor DB **`sectors.slug`**. | Join instruments → sectors: incomplete for macro-only cards. |
| **Lazy import of `build_evidence_rows`** | Avoids circular import **`bias_detector` ↔ `card_detail`**. | Extract shared **`evidence_rows` module**: cleaner long-term, deferred to limit scope. |
| **Anchoring always monitored in V1** | PRD mitigates via separate dissent call; no reliable automated anchoring score yet. | Flag when dissent is empty: too many false positives on pipeline failures. |
| **Survivorship via text regex** | Lightweight V1 signal for historical framing without a delisted-company database. | Full survivorship model: Phase 2+ scope. |
| **Weekly report to `notes/`** | Gitignored operational artifact for editors; not user-facing API. | Admin UI for coverage: **P1-S14** / later slices. |

**⚠️ Critical — do not reverse without replanning**

- **Do not** UPDATE **`track_record`** to patch **`bias_audit`** after publish.  
- **Do not** remove **`detect_all`** from the publish path without providing another persistence trigger, or Thread will show stale/empty flags.  
- **Do not** change recency to `>= 0.6` without PRD/product sign-off (wording is “more than 60%”).

**Assumptions**

- “Sector concentration” in Phase 1 is approximated by **repeated `event_category`** on consecutive published cards.  
- Cards published before migration **0011** have no **`card_bias_flags`** until re-published or manually backfilled.  
- **`notes/`** directory is writable on the host running the weekly cron (Render worker filesystem).

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1-S7** (evidence JSON / sources), **P1-S8** (`publish_draft_card`, `track_record`), **P1-S10** (`BiasFlags`, `GET /api/cards/{id}`, `bias_audit` shape in **`threadTypes.ts`**). |
| **Enables** | **P1-S14** (go/no-go can cite real bias surfacing); Phase 2/3 transparency pages reading **`card_bias_flags`** summaries. |
| **Parallel (same phase)** | **P1-S11** (signals), **P1-S12** (predictions)—no direct code coupling. |
| **Touches shared modules** | **`publish_card`**, **`card_detail.build_card_detail`**, **`feed.confidence_tier`**, **`card_repository.fetch_card_detail_for_review`**, Render cron **`finnwise-bias-report`**. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Pattern** | **Rules engine** + **persist + project**: detectors return **`BiasFinding`** dataclass; **`build_bias_audit`** maps to UI **`flags`** / **`monitored`** arrays. |
| **Database** | New table **`card_bias_flags`**; no change to **`cards`** columns. |
| **API** | **No new routes**; extended **`GET /api/cards/{id}`** response field **`bias_audit`**. |
| **Auth** | Unchanged Phase 1 posture (card detail read open). |
| **UI** | Existing **`BiasFlags`** component; amber inner cards for **`flags`**, slate for **`monitored`**; **`data-testid`** hooks added for tests. |
| **Jobs** | **`python -m app.jobs.weekly_bias_report`** — schedule **`0 9 * * 1`** (Mondays 09:00) in **`render.yaml`**. |
| **Libraries** | No new runtime dependencies. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0011_card_bias_flags.sql` | `backend/db/migrations/` | Schema for per-card bias findings |
| `bias_detector.py` | `backend/app/services/` | All per-card detectors, persist, `build_bias_audit`, `detect_all` |
| `weekly_bias_report.py` | `backend/app/jobs/` | Editorial coverage rollup → `notes/bias-report-*.md` |
| `test_bias_detector.py` | `backend/tests/` | Unit + DB integration tests per detector |
| `test_weekly_bias_report.py` | `backend/tests/` | Markdown render smoke test |
| `BiasFlags.test.tsx` | `frontend/app/(app)/thread/_components/aside/` | Amber vs grey DOM class assertions |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `migrate.py` | `backend/app/db/` | Registers **`0011_card_bias_flags.sql`** |
| `publish_card.py` | `backend/app/services/` | Calls **`detect_all`** after publish; embeds **`bias_audit`** in **`track_record`** payload |
| `card_detail.py` | `backend/app/services/` | **`build_card_detail`** uses **`build_bias_audit(card_id=…)`** or snapshot; **`bias_audit_placeholder`** retained for exports/tests |
| `BiasFlags.tsx` | `frontend/app/(app)/thread/_components/aside/` | Added **`data-testid`** on flagged/monitored blocks (shadcn Card wrapper unchanged) |
| `test_publish_writes_track_record.py` | `backend/tests/` | Asserts **`bias_audit`** in publish payload; cleans **`card_bias_flags`** in teardown |
| `.gitignore` | repo root | Added **`notes/`** |
| `finnwise-phase1-implementation-tasks.md` | `docs/plans/` | P1-S13 acceptance criteria and tasks marked complete |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Table: `public.card_bias_flags`**

| Column | Type | Notes |
|--------|------|--------|
| `id` | `uuid` PK | Default `gen_random_uuid()` |
| `card_id` | `uuid` FK → `cards(id)` ON DELETE CASCADE | |
| `bias_type` | `text` | e.g. `recency`, `sector_concentration`, `narrative`, `survivorship`, `anchoring` |
| `severity` | `text` | CHECK: `flagged` or `monitored` |
| `description` | `text` | Plain-English copy for UI |
| `detected_at` | `timestamptz` | Default `now()` |
| **Unique** | `(card_id, bias_type)` | Re-detect replaces via DELETE + INSERT in **`persist_bias_flags`** |

**Migration sequencing:** **`0011_card_bias_flags.sql`** after **`0010_signal_monitoring.sql`** (see **`backend/app/db/migrate.py`**).

**`track_record.payload` extension**

```json
{
  "kind": "initial_publish",
  "ice_snapshot": { ... },
  "signals_snapshot": [ ... ],
  "bias_audit": {
    "flags": [
      { "id": "recency", "label": "Recency bias", "status": "flagged", "detail": "..." }
    ],
    "monitored": [
      { "id": "anchoring", "label": "Anchoring bias", "status": "monitored", "detail": "..." }
    ]
  }
}
```

**Seed data:** None. Flags appear when **`detect_all`** runs at publish.

---

### B2. API / INTEGRATION CONTRACTS

**No new HTTP endpoints.**

**Modified response shape: `GET /api/cards/{card_id}?view=current|original`**

Field **`bias_audit`** (unchanged TypeScript contract in **`threadTypes.ts`**):

| Sub-field | Type | Meaning |
|-----------|------|---------|
| `flags` | `BiasEntry[]` | `severity === 'flagged'` → amber aside blocks |
| `monitored` | `BiasEntry[]` | `severity === 'monitored'` → grey aside blocks |
| `note` | `string?` | Optional footer (omitted when using live data; placeholder had a note) |

**`BiasEntry`:** `{ id, label, status, detail }` where **`id`** matches **`bias_type`**.

**Auth:** Same as P1-S10 — unauthenticated read in Phase 1.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Publish sequence (`publish_draft_card`)**

1. Transaction A: UPDATE **`cards`** → `published`, UPDATE **`events`** → `published`.  
2. **`detect_all(card_id)`** → **`run_detectors_for_card`** → **`persist_bias_flags`**.  
3. **`build_bias_audit(findings)`** → JSON for UI.  
4. Transaction B: INSERT **`track_record`** with full payload including **`bias_audit`**; INSERT **`in_app_notifications`** (unchanged P1-S8 behaviour).

**`build_card_detail` bias resolution**

- **`view=current`:** **`build_bias_audit(card_id=card_id)`** reads **`card_bias_flags`**.  
- **`view=original`:** Prefer **`track_record.payload.bias_audit`**; else fall back to live table (pre-P1-S13 publishes).

**Detector dependency graph**

```
fetch_card_detail_for_review
        │
        ├─► detect_recency(evidence_layer)     ──► build_evidence_rows (lazy)
        ├─► detect_sector_concentration(card_id, event_category)
        ├─► detect_narrative(score, evidence_layer)
        ├─► detect_survivorship(insight, context, evidence)
        └─► detect_anchoring()  [always monitored]
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **Sector = `event_category`** | Not banking-sector slug from Factor DB; rename or extend when cards carry explicit sector FK. |
| **Pre-P1-S13 publishes** | No **`bias_audit`** in **`track_record`**; Original view may show **current** flags from DB. |
| **`bias_audit_placeholder` still in codebase** | Dead path for **`build_card_detail`**; safe to remove in cleanup if no tests import it. |
| **Circular import workaround** | Lazy import of **`build_evidence_rows`** inside detectors; extract **`evidence_rows.py`** when touching evidence logic again. |
| **Regenerate flow** | **`regenerate_draft_with_notes`** creates a **new draft**; bias runs only when **that** draft is **published**, not on regenerate itself. |
| **Weekly report filesystem** | Cron must run where repo **`notes/`** is writable; production may need object storage if Render ephemeral disk is insufficient. |
| **Re-detect on republish** | Not implemented; second publish path blocked for same card id in normal flow. |

---

### B5. TESTING NOTES

| Layer | Coverage |
|-------|----------|
| **Backend unit** | Recency (>60%), narrative (high + <3 sources), survivorship regex, anchoring monitored, evidence LLM filter |
| **Backend DB** | Sector concentration with 3 macro cards; **`detect_all`** persist + **`build_bias_audit`** split |
| **Backend integration** | Publish writes **`bias_audit`** in **`track_record`** |
| **Backend job** | **`render_report_markdown`** content structure |
| **Frontend** | **`BiasFlags.test.tsx`** — `bias-flag-*` / `bias-monitored-*` testids and Tailwind classes |
| **Manual** | Publish a card via admin review → open Thread → verify amber/grey blocks; run **`python -m app.jobs.weekly_bias_report`** locally and inspect **`notes/bias-report-*.md`** |

**Gaps:** No E2E browser test from publish → Thread; no test for Original view **`bias_audit`** immutability when live flags change later.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Item | Role |
|------|------|
| **`SUPABASE_DB_URL`** / **`SUPABASE_URL`** + service role | Required for detectors and weekly job (same as rest of backend) |
| **Migration `0011`** | Must be applied before publish path can persist flags (`python -m app.db.migrate` or pytest **`apply_migrations`**) |
| **`notes/`** | Gitignored; weekly cron output directory |
| **Render cron `finnwise-bias-report`** | Already defined in **`render.yaml`** — replaces placeholder log-only job |

No new feature flags or frontend env vars.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

1. **To add a seventh bias type:** extend **`CARD_TRACKED_TYPES`**, implement **`detect_*`**, add label in **`_BIAS_LABELS`**, include in **`run_detectors_for_card`**, and document PRD alignment.  
2. **To change thresholds:** edit **`bias_detector.py`** only; add/adjust tests in **`test_bias_detector.py`**.  
3. **Thread UI** only reads **`data.bias_audit`** — do not hard-code bias copy in **`BiasFlags.tsx`** unless the API contract changes.  
4. **⚠️ Never UPDATE `track_record`** for bias fixes; add a new append-only row type in a future story if “bias correction” history is needed.  
5. **Weekly editorial report** is for **internal** review (`notes/`), not exposed in the app in Phase 1.  
6. **Compliance / Product:** bias surfacing supports PRD credibility metrics (e.g. bias flag trigger rate); legal copy in aside remains plain English, not disclaimers replacing SEBI footer.

**Related code paths**

- Detectors: `backend/app/services/bias_detector.py`  
- Publish hook: `backend/app/services/publish_card.py`  
- API assembly: `backend/app/services/card_detail.py`  
- UI: `frontend/app/(app)/thread/_components/aside/BiasFlags.tsx`  
- Weekly job: `backend/app/jobs/weekly_bias_report.py`

---

**End of document**
