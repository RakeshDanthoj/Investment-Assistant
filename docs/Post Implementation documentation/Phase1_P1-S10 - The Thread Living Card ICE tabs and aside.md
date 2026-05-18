# Post Implementation Detailed Document — P1-S10

**Version:** v1.0 | **Date:** 18-05-2026  
**Story ID:** P1-S10 (Phase 1, Story 10)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`

---

## Narrative style (read this first)

FinnWise’s core reading experience is **The Thread**: a single Event Intelligence Card shown at full depth, using the **ICE** mental model (**Insight → Context → Evidence**). Before this story, users could see cards on **The Pulse** as a feed and land on a placeholder thread route. This story turns **`/thread/[cardId]`** into the real product surface: headline, confidence, **progressive ICE tabs** (Insight always available; Context and Evidence unlocked by deliberate taps), instrument assessments with **world-fact entry/exit conditions** (no advisory language), **dissent**, **prediction logger**, **framework** block, and a **sticky aside** with lifecycle, signals, confidence composition, and bias placeholders.

Architecturally, the Thread is a **read-heavy composition layer**. It does not own card authoring; it **projects** whatever the backend considers “current truth” for a card, and optionally a frozen **Original** view taken from the **append-only `track_record`** row written at **first publish**. That split is the accountability backbone of the PRD: users can compare “what we say now” with “what we said on Day 1” without mutating history.

The backend therefore gained two responsibilities: (1) **`GET /api/cards/{id}`** assembles a **denormalised JSON document**—ICE text, parsed context steps, evidence rows with **freshness tiers**, signals, instruments, lifecycle tracker positions, and placeholder bias metadata—so the frontend stays thin; (2) **`POST /api/predictions`** records the learner’s discrete choice into **`user_predictions`**, bridging toward **P1-S12**’s fuller predictions story (dual-write to `track_record`, auth, Mirror). Publish was extended so **`track_record.payload`** carries an **`ice_snapshot`**: the immutable bundle needed for Original view.

If you remember **three** architectural anchors later: **ICE progressive disclosure** (UX trust ladder), **`track_record` as the Original source of truth** (not the live `cards` row), and **card detail as an assembled API contract** (one GET drives the whole page).

--------------------------------------------

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S10 |
| **Title** | The Thread — Living Card with ICE tabs + aside |
| **Category** | **Full Stack** (FastAPI read/write endpoints + assembly service + publish payload extension; Next.js App Router page + client composition + tests) |

**What this story aimed to achieve (plain language)**

Deliver the **full-thread reading experience** for a published (or otherwise visible) card: breadcrumb and lifecycle affordances, **Current / Original** toggle, **ICE** layers with PRD-aligned gating, instrument cards and dissent, **four-option prediction logger** calling the API, framework block, and an **aside** with lifecycle tracker (seven visible stages), signals-to-watch with expandable consequence map, MMJ-style confidence composition bar, and bias flags (placeholder until editorial audit lands). Enforce **Screen 3 language constraints** in automated frontend tests where practical.

**How it fits into the overall application**

- **Upstream:** **P1-S4** (schema: `cards`, `signals`, `instrument_assessments`, `user_predictions`, `track_record`), **P1-S7** (draft ICE content), **P1-S8** (publish writes **initial** `track_record` and transitions lifecycle). **P1-S9** links users from Pulse into `/thread/[id]`.
- **Same phase / parallel:** **P1-S8** (review/publish), **P1-S9** (Pulse UI).
- **Downstream:** **P1-S11** (signal monitoring, notifications tied to predictions), **P1-S12** (full predictions service + auth + optional dual-write), **P1-S13** (real **bias_audit** payload instead of placeholder).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items (plan mapping) and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **10.1** | **`ThreadExperience`** top chrome: link back to Pulse, category pill, lifecycle badge with **pulsing dot** when `lifecycle_state` is `active` or `signal_triggered`, **CurrentOriginalToggle**. |
| **10.2** | **`IceTabs`**: default **Insight**; **Context** requires first unlock tap; **Evidence** requires second tap after Context is unlocked; hint if Evidence clicked too early. |
| **10.3** | **`InsightLayer`**: prose from `insight_layer`, **`InstrumentCard`** grid, **`DissentingView`**, **`PredictionLogger`**, **`FrameworkBehindThis`**. |
| **10.4** | **`InstrumentCard`**: normalised pills (`opportunity signal` / `headwind signal` / `watch`), entry (green) / exit (amber) columns; backend **`normalize_signal_label`** maps legacy DB values (e.g. positive/negative). |
| **10.5** | **`ContextLayer`**: numbered navy circles; **`parse_context_steps`** (backend) splits context prose; MMJ badge per step from `[MEASURED|MODELLED|JUDGED]` when present; fallback single block if parsing yields nothing useful. |
| **10.6** | **`EvidenceLayer`**: table from **`evidence_rows`**; freshness via **`freshness_for_retrieved_at`** (month-scale bands aligned with PRD §5 Evidence and Factor DB helper); explicit note that LLM must not appear as a source row (filter + product copy); matrix fallback when no `sources` array. |
| **10.7** | **`LifecycleTracker`**: seven steps (`published` → `archived`); **CSS** `thread-lifecycle-pulse` (1.5s ease-in-out) on **current** stage when lifecycle is interactive. |
| **10.8** | **`SignalsToWatch`**: dot styles pending/triggered/resolved; triggered uses **`thread-signal-pulse`**; expand/collapse **consequence map** referencing instruments. |
| **10.9** | **`ConfidenceComposition`**: segmented bar from **`confidence_composition`** ratios (derived from MMJ bracket counts across layers). |
| **10.10** | **`BiasFlags`**: renders **`bias_audit_placeholder`** from API until **P1-S13** supplies real flags. |
| **10.11** | **`PredictionLogger`**: four fixed strings; **`POST /api/predictions`**; disabled until **`NEXT_PUBLIC_FINNWISE_USER_ID`** set (dev bridge). |
| **10.12** | **`useCard(cardId, view)`** → **`GET /api/cards/{id}?view=current|original`**; Original merges **`ice_snapshot`** + **`signals_snapshot`** from **`track_record`** where `kind = initial_publish`. Toggle resets ICE unlock tier to avoid accidental mixing of modes. |
| **10.13** | Tests: **`InstrumentCard`** / **`DissentingView`** / **`screen3CopyLint`**; backend **`test_card_detail_original_immutable`**; route-shape tests for predictions; publish test asserts **`ice_snapshot`** presence. |

**Edge cases, validations, and error handling**

- **Original view without publish snapshot:** API returns **404** (`original_view_unavailable`); UI shows error + retry + link to Pulse.
- **Unknown card:** **404** for current view if card row missing.
- **Prediction POST:** **404** if card missing or FK violation on user; **409** on duplicate **(user_id, card_id)**; validation on prediction text length (service + Pydantic).
- **DB unavailable:** FastAPI **503** path consistent with other routes when connection fails.

**Business rules enforced (PRD-aligned)**

- No **buy / sell / hold** or **₹ + digits** patterns in tested instrument/prediction copy paths.
- Instrument conditions framed as **observable world facts**, not price targets (content discipline + tests on sample props).
- Evidence freshness communicated via **green / amber / red** from **`retrieved_at`** using shared **`freshness_for_retrieved_at`** semantics.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Denormalised `GET /api/cards/{id}`** | Single round-trip drives entire Thread; keeps React components presentational. | Many micro-endpoints: more waterfall, harder consistency. |
| **`ice_snapshot` inside publish `track_record` payload** | Original view must survive later edits to `cards`; append-only row is the PRD anchor. | Read-only “copy tables”: duplicates schema drift risk. |
| **Progressive ICE unlock in client state** | Matches PRD “one tap / second tap” without requiring URL routing complexity in v1. | Hash-based routing only: deferred (plan optional). |
| **`NEXT_PUBLIC_FINNWISE_USER_ID` bridge** | Backend expects real **`auth.users`** FK; full JWT/session wiring belongs to **P1-S12**. | Fake user_id without FK: breaks DB integrity. |
| **Evidence rows from `sources` JSON or matrix flattening** | Pipeline may not yet emit structured citations everywhere; matrix gives sensible fallback. | Empty Evidence tab until pipeline perfect: worse UX. |
| **Bias panel placeholder JSON from server** | No `bias_audit` column on `cards`; **P1-S13** owns richer audit. | Hard-coded only in UI: harder to swap to API-driven later. |
| **Aside hidden below `lg`** | Desktop-first layout parity with mock; mobile aside stack not in minimal slice. | Always show aside: cramped on small phones without design pass. |

**⚠️ Critical — do not reverse without replanning**

- **Do not** serve **Original** view from mutable **`cards`** columns alone; **`track_record`** + **`ice_snapshot`** is the integrity boundary.
- **Do not** loosen **`track_record`** append-only guarantees to “fix” test cleanup—orphan rows or transactional test strategies are preferable.

**Assumptions**

- Context layer text remains parseable enough for step splitting; deeply unstructured prose falls back to one step.
- Authenticated prediction logging will replace the public env UUID approach in **P1-S12**.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1-S4** tables/enums; **P1-S7** card JSON shapes; **P1-S8** publish + first `track_record` row; **P1-S9** navigation to thread. |
| **Enables** | **P1-S11** (notifications for users who predicted); **P1-S12** (predictions API hardening, Mirror); **P1-S13** (bias payload feeding **`BiasFlags`**). |
| **Touches shared modules** | **`publish_card`** (payload shape), **`card_repository`** (`fetch_track_record_initial_publish`), **`feed`**-adjacent tier helpers reused via **`confidence_tier`** / **`tier_label`**, **`factor_db.freshness_for_retrieved_at`**, **`AppShell`** / **`SebiFooter`** (global regulatory footer—not duplicated on Thread). |
| **Legacy / adjacent UI** | Older **`frontend/components/thread/IceCardReader.tsx`** remains for read-only/admin-style surfaces; Thread route uses **`app/(app)/thread/_components/**`** as the product implementation. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Pattern** | **BFF-style aggregate**: one GET returns a ready-to-render **CardDetailResponse** shape typed in **`threadTypes.ts`**. |
| **Database** | No new tables; extended **`track_record.payload`** JSON (`ice_snapshot`, existing `signals_snapshot`). |
| **API** | **`GET /api/cards/{uuid}?view=current\|original`**; **`POST /api/predictions`** body `{ card_id, prediction_text, user_id }`. |
| **Auth** | Predictions: **explicit `user_id`** (until **P1-S12**); card detail: **unauthenticated read** (Phase 1 posture—lock down for production if needed). |
| **UI** | Tailwind + existing FinnWise tokens; custom keyframes in **`globals.css`** for lifecycle/signal pulse. |
| **Libraries** | No new runtime deps; React client hooks + `fetch`. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `ThreadExperience.tsx` | `frontend/app/(app)/thread/_components/` | Client page shell: chrome, layout, data hook, ICE + aside composition |
| `CurrentOriginalToggle.tsx` | `frontend/app/(app)/thread/_components/` | Two-segment Current / Original control |
| `IceTabs.tsx` | `frontend/app/(app)/thread/_components/` | ICE tab bar + progressive unlock |
| `InsightLayer.tsx` | `frontend/app/(app)/thread/_components/` | I-layer assembly |
| `ContextLayer.tsx` | `frontend/app/(app)/thread/_components/` | C-layer numbered chain + MMJ chips |
| `EvidenceLayer.tsx` | `frontend/app/(app)/thread/_components/` | E-layer table + stubs |
| `InstrumentCard.tsx` | `frontend/app/(app)/thread/_components/` | Instrument assessment tile |
| `DissentingView.tsx` | `frontend/app/(app)/thread/_components/` | Amber dissent block |
| `PredictionLogger.tsx` | `frontend/app/(app)/thread/_components/` | Four options + POST predictions |
| `FrameworkBehindThis.tsx` | `frontend/app/(app)/thread/_components/` | Dark gradient framework block |
| `LifecycleTracker.tsx` | `frontend/app/(app)/thread/_components/aside/` | Seven-step lifecycle column |
| `SignalsToWatch.tsx` | `frontend/app/(app)/thread/_components/aside/` | Signals list + consequence map |
| `ConfidenceComposition.tsx` | `frontend/app/(app)/thread/_components/aside/` | MMJ proportion bar |
| `BiasFlags.tsx` | `frontend/app/(app)/thread/_components/aside/` | Bias placeholder UI |
| `threadTypes.ts` | `frontend/lib/cards/` | TypeScript types mirroring API |
| `useCard.ts` | `frontend/lib/cards/` | Fetch hook for card detail |
| `InstrumentCard.test.tsx` | `frontend/app/(app)/thread/_components/` | Language guard on instrument copy |
| `DissentingView.test.tsx` | `frontend/app/(app)/thread/_components/` | Dissent always rendered when text provided |
| `screen3CopyLint.test.ts` | `frontend/app/(app)/thread/_components/` | Static lint on prediction option strings |
| `card_detail.py` | `backend/app/services/` | Assemble card JSON, evidence rows, lifecycle tracker, MMJ composition |
| `cards_detail.py` | `backend/app/api/` | FastAPI route for GET card detail |
| `prediction_log.py` | `backend/app/services/` | Insert into `user_predictions` with validation |
| `predictions.py` | `backend/app/api/` | POST `/api/predictions` |
| `test_card_detail_original_immutable.py` | `backend/tests/` | Original snapshot immutability vs live card edits |
| `test_predictions_route_shapes.py` | `backend/tests/` | HTTP mapping / mocked success path |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `page.tsx` | `frontend/app/(app)/thread/[cardId]/` | Replaced placeholder with `ThreadExperience` |
| `globals.css` | `frontend/app/` | Added `thread-lifecycle-pulse` and `thread-signal-pulse` keyframes |
| `publish_card.py` | `backend/app/services/` | Adds `ice_snapshot` + instrument snapshot into `track_record` payload |
| `card_repository.py` | `backend/app/services/` | `fetch_track_record_initial_publish` for Original view |
| `main.py` | `backend/app/` | Registers `cards_detail_router`, `predictions_router` |
| `test_publish_writes_track_record.py` | `backend/tests/` | Asserts `ice_snapshot.title` on publish payload |

*(If your branch also shows unrelated edits to `main.py` from other stories—e.g. notifications—treat those as concurrent integration; the Thread-specific registrations are **`cards_detail`** and **`predictions`**.)*

--------------------------------------------

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- **No new migrations** for P1-S10.
- **`track_record.payload`** JSON gains **`ice_snapshot`** (title, ICE layers, evidence JSON, dissent, framework, instruments, event fields, lifecycle at publish) alongside existing **`kind`**, **`signals_snapshot`**, metadata.
- **`user_predictions`** used by **`prediction_log`** (existing unique **(user_id, card_id)**).
- ⚠️ **`track_record`** remains **append-only** (triggers/RLS): integration tests must not **`DELETE`** rows; cleanup deletes **`cards`** / **`events`** where FK allows and may leave orphan `track_record` in dev DBs.

---

### B2. API / INTEGRATION CONTRACTS

**`GET /api/cards/{card_id}?view=current|original`**

- **200:** Full card detail object (see **`threadTypes.ts`** / `build_card_detail` return shape).
- **404:** Unknown card (current) or no `initial_publish` snapshot (original).
- **503:** DB unavailable (same pattern as other routes).

**`POST /api/predictions`**

- **Body:** `{ "card_id": "<uuid>", "user_id": "<uuid>", "prediction_text": "<8..2000 chars>" }`
- **200:** `{ "ok": true }`
- **404:** Unknown card or invalid user FK
- **409:** Duplicate prediction for user+card
- **422:** Validation / business errors from service

---

### B3. BUSINESS LOGIC & RULES (Detailed)

- **`build_card_detail`:** Chooses live **`cards` + `events` join** vs **`track_record`** snapshot for Original; builds **`evidence_rows`** from `sources[]` or **`matrix_snapshot.sensitivities`**; filters source names containing **`llm` / `gemini` / `gpt`**; computes **`lifecycle_tracker`** positions from current slug order; **`mmj_composition_from_text`** counts bracket tags across layers.
- **`publish_draft_card`:** Serialises **`evidence_layer`** to a dict before embedding in JSON payload (handles string/dict edge cases from drivers).

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **Prediction auth** | **`user_id` in body** + env UUID is a **dev bridge**; replace with session/JWT in **P1-S12**. |
| **Bias data** | Placeholder **`bias_audit_placeholder`** until **P1-S13**. |
| **Mobile aside** | Hidden below **`lg`**; no stacked aside column on phones in this slice. |
| **ICE hash routing** | Optional shareable deeplinks not implemented. |
| **Orphan `track_record`** | Possible in dev when deleting cards; acceptable or handle with service-role maintenance. |

---

### B5. TESTING NOTES

| Layer | Coverage |
|-------|------------|
| **Backend** | Immutability of Original vs mutated current card; publish payload contains **`ice_snapshot`**; predictions route error mapping + mocked success |
| **Frontend** | RTL on **`InstrumentCard`** / **`DissentingView`**; static copy lint on prediction strings |
| **Manual** | Recommended: Pulse → Thread → toggle Original on a **published** card; attempt prediction with valid Supabase user UUID in env |

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| **`NEXT_PUBLIC_API_BASE_URL`** | Backend origin for **`useCard`** and **`PredictionLogger`** |
| **`NEXT_PUBLIC_FINNWISE_USER_ID`** | Dev-only UUID matching **`auth.users.id`** to enable prediction POST from browser |

Restart **`next dev`** after env changes.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

1. **Original view** will **404** until **`publish_draft_card`** has created **`track_record`** with **`kind = initial_publish`**—do not confuse with draft-only cards.
2. When extending **`track_record` payload**, preserve **`ice_snapshot`** as the contract for Original; version or migrate carefully.
3. **`card_detail.build_card_detail`** is the single place to adjust assembly logic—avoid duplicating field mapping in the router.
4. For **production**, plan **auth** on **`POST /api/predictions`** and likely **`GET /api/cards/{id}`** if cards must not be public.
5. **Product / Compliance:** pairing this story with formal **tester acceptance** and legal review is outside this implementation doc but required before broader rollout (see PRD risk notes).

---

**End of document**
