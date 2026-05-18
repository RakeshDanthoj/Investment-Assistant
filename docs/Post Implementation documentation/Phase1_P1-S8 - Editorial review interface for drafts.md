# Post Implementation Detailed Document — P1-S8

**Version:** v1.0 | **Date:** 18-05-2026  
**Story ID:** P1-S8 (Phase 1, Story 8)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`

---

## Narrative style

FinnWise treats an **Event Intelligence Card (ICE)** as a living artifact: machines can **draft**, but humans must **gate** what becomes part of the customer-facing narrative. This story is that gate. Architecturally, it sits **between the LLM factory (P1-S7)** and **every consumer surface that only ever sees `published` cards** (Pulse, Thread, feeds, notifications). The editorial experience is deliberately **two-lane**: on the left, the editor sees the card in a **Thread-shaped, read-only shell**—the same intellectual shape the product promised for “deep read” later—so checklist items are judged against real copy, not a JSON tree. On the right, a **sidecar** forces a **five-point non-expert checklist** derived from PRD §6.1 before **Publish** unlocks; that design encodes compliance and tone rules into UI friction rather than hoping reviewers memorise policy.

When the editor publishes, the backend performs a **single database transaction** that (1) promotes the **`cards`** row and its parent **`events`** row to **`published`**, (2) writes an **append-only `track_record`** snapshot capturing title, category, optional **anonymous review duration**, and a signals snapshot—establishing an immutable audit anchor for “what went live”—and (3) fans out **in-app notification rows** for onboarded users whose **optional category subscription** matches the event category (or who have not narrowed categories yet). Regeneration is intentionally **outside** that transaction: it reuses **`draft_card_from_event`** from P1-S7 with **`editor_notes`** injected into synthesis, consumes another LLM slot, produces a **new** draft **`cards`** row, then **archives** the superseded draft so the queue does not accumulate ambiguous siblings.

If you anchor one mental model for later debugging: **review is state transition + audit + fan-out**, not “edit JSON.” Edits that require model rework flow through **regenerate**, not silent PATCH endpoints—preserving lineage and prompt accountability.

---

## Audit style — PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S8 |
| **Title** | Editorial review interface for drafts |
| **Category** | **Full stack** — Next.js admin route + checklist UX; FastAPI admin-card routes; Postgres migration (`notify_categories`, `in_app_notifications`); Python services (`publish_card`, `regenerate_card`, repository reads); automated backend + frontend tests |

**What this story aimed to achieve (plain language)**

1. Give the Product Owner an **internal screen** (`/admin/review/[draftId]`) to read a **full draft ICE** beside an **editorial checklist**, targeting the PRD “~45 minutes per card” editorial rhythm with **anonymous time-on-page** captured at publish.  
2. **Gate publishing**: all five checklist confirmations must be ticked before the UI enables **Publish**—mirroring PRD §6.1 editorial discipline.  
3. **Publish** promotes lifecycle to **`published`**, writes the **first immutable `track_record`** row for that card, and creates **in-app notification** rows for users whose profile subscription semantics match the card’s event category.  
4. **Send-back**: optional editor notes trigger **regeneration** via the existing three-call pipeline (P1-S7), then **archive** the old draft card.  

**How it fits into the overall application**

P1-S8 closes the loop opened by **P1-S6** (events enter as drafts) and **P1-S7** (draft `cards` + child rows). Upstream it **depends on** normalized `cards` / `events` / `signals` / `instrument_assessments` and the **`draft_card_from_event`** contract. Downstream, **Pulse / Thread / feed** work (P1-S9+, P1-S10) should query **`lifecycle_state = published`** (and later resolved/active semantics)—this story is where that invariant becomes true. It also establishes **`in_app_notifications`** as the Phase 1 hook for “something happened” without building push/email yet.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items (plan 8.1–8.6) and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **8.1** | **`ThreadReviewShell`** + **`IceCardReader`** — Thread-like chrome (sticky header, main + ~340px aside grid); ICE tabs (Insight / Context / Evidence), confidence strip from **event** score, dissent + framework blocks, instrument assessment tiles. Read-only by design. |
| **8.2** | **`ChecklistPanel`** — five items aligned to PRD §6.1 narrative (MMJ/numbers, dissent specificity, confidence vs freshness, non-expert language, no recommendation language); **Publish** disabled until all checked. |
| **8.3** | **`publish_draft_card`** — transactional publish + **`track_record`** insert + **`in_app_notifications`** bulk insert keyed off **`session_profiles`** + **`notify_categories`**. |
| **8.4** | **`regenerate_draft_with_notes`** — **`draft_card_from_event(event_id, editor_notes=…)`** then **`archive_card`** on the prior draft UUID. |
| **8.5** | **`ReviewWorkspace`** records **`openedAtMs`** on mount; POST **`editor_review_seconds`** with publish payload (integer seconds, no PII). |
| **8.6** | **`test_publish_writes_track_record`** (integration-style against real DB when configured); **`ChecklistPanel.test.tsx`** (RTL + `fireEvent`). |

**Functional breakdown**

- **GET `/api/admin/cards/{card_id}`** loads joined **`cards` + `events`** fields needed for rendering plus **`instrument_assessments`** list.  
- **POST `/api/admin/cards/{card_id}/publish`** validates draft-only, applies lifecycle updates, immutable audit row, notifications.  
- **POST `/api/admin/cards/{card_id}/regenerate`** validates draft-only, invokes LLM pipeline (inherits **`DailyLLMCardCapError`** / validator failures), returns **`new card_id`**, replacing URL client-side.  
- **Published revisit**: UI detects **`lifecycle_state !== draft`** and replaces checklist with explanatory copy—publish/regenerate are idempotently unavailable server-side too (`PublishCardError` / `RegenerateCardError`).  

**Edge cases, validations, and error handling**

| Scenario | Behaviour |
|----------|-----------|
| Unknown `card_id` | `LookupError` → HTTP **404** (`card_not_found`). |
| Publish non-draft | `PublishCardError` → HTTP **422** (`publish_rejected`). |
| Double publish | Second call fails draft-only guard → **422**. |
| Regenerate non-draft | `RegenerateCardError` → **422**. |
| LLM cap / pipeline failure on regenerate | **429** (`llm_daily_cap`) or **422** (`draft_pipeline_failed`) mirroring **`cards`** router semantics. |
| Negative `editor_review_seconds` (server) | Normalised to omit / treat as absent in payload assembly (defensive). |
| No matching subscribers | Notification insert inserts **zero rows**—still a successful publish. |

**Business rules enforced**

- Only **`draft`** cards publish or regenerate.  
- **`track_record`** carries **`kind: initial_publish`** plus **`editor_review_seconds`**, title, category, **`signals_snapshot`**.  
- **`events.lifecycle_state`** co-promoted to **`published`** with the card—keeps editorial queue semantics aligned (draft events should drop off filtered queues).  
- Category targeting: **`notify_categories` NULL or empty array ⇒ match all categories**; otherwise Postgres **`ANY`** against event category slug text.  

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Thread-shaped reader lives under `components/thread/`** | Positions **`IceCardReader`** as the canonical “deep card” presentation for reuse by **The Thread (S10)**; admin only adds chrome + sidecar. | Duplicated markdown in admin-only components: diverges from product vision. |
| **Publish = one SQL transaction** | Atomicity: no “published card without audit” or “audit without notifications” intermediate states observable to other readers. | Separate micro-calls: race windows + partial failures. |
| **`in_app_notifications` without FK to `auth.users`** | Supabase often blocks direct inserts into **`auth.users`** from app SQL; **`user_id`** is still the same UUID space as profiles. | Strict FK: might fail CI inserts without seeded auth rows. |
| **`notify_categories text[]` on `session_profiles`** | Minimal Phase 1 expression of “profile matches category” without redesigning onboarding flows. | Full preference centre UI: later story. |
| **Regenerate = new card + archive old** | Avoids destructive edits to immutable-ish draft lineage; aligns with prompt versioning & audit story later. | In-place overwrite of `cards` JSON: loses history and child-row semantics. |
| **Archive after successful pipeline** | If Gemini fails, editor retains working draft. | Archive-first: leaves user with no draft on failure. |

**Assumptions**

- Editors navigate with **`cards.id`** UUID from **`draft-from-event`** responses or tooling—not inferred from events alone when multiple drafts could theoretically exist across retries (archive path reduces ambiguity).  
- Phase 1 admin APIs remain **unauthenticated** like **`GET /admin/events`**—network perimeter / future RBAC required before production exposure.  

**⚠️ Critical — do not reverse lightly**

- Do **not** delete or **`UPDATE`** **`track_record`** rows to “fix” publish bugs—schema triggers/policies intentionally forbid mutation (**append-only**). Fix forward with compensating **`track_record`** kinds in a future story if needed.  
- Do **not** bypass the **draft-only** guards without revisiting downstream feeds that assume **`published`** invariant.  

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Links |
|-----------|--------|
| **Upstream dependencies** | **P1-S4** (`cards`, `events`, `signals`, `instrument_assessments`, `track_record`), **P1-S7** (`draft_card_from_event`, validators, prompts), **P1-S2/S3** (`session_profiles.user_id` population for notifications to matter). |
| **Downstream consumers** | **P1-S9** Pulse feed should filter **`published`** (+ resolved semantics later); **P1-S10** Thread should reuse **`IceCardReader`**; future **notification drawer / badge UI** reads **`in_app_notifications`**. |
| **Shared artifacts touched** | **`LifecycleState`** enum values; **`cards`**, **`events`**, **`session_profiles`** columns; **`track_record`** payload JSON shape for publish snapshots. |

---

### A5. DESIGN CHOICES

| Layer | Choice |
|-------|--------|
| **Architecture** | Thin FastAPI router (**`admin_review.py`**) delegating to **`publish_card`** / **`regenerate_card`** services; repository SQL isolated in **`card_repository.py`**. |
| **Database** | Migration **`0009_editorial_publish_notifications.sql`** — additive column + new notifications table + indexes. |
| **API** | Routes mounted under **`/api/admin`** (distinct from **`/admin`** queue router). |
| **UI/UX** | Checklist + disabled Publish communicates policy without modal spam; regenerate isolated with textarea—orthogonal checklist path. |
| **Libraries** | Existing stack only (**FastAPI**, **psycopg**, **Next.js**, **RTL/Jest**). |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0009_editorial_publish_notifications.sql` | `backend/db/migrations/` | `notify_categories` + `in_app_notifications`. |
| `publish_card.py` | `backend/app/services/` | Transactional publish + audit + notifications. |
| `regenerate_card.py` | `backend/app/services/` | Regenerate orchestration + `RegenerateCardError`. |
| `admin_review.py` | `backend/app/api/` | GET card, POST publish, POST regenerate. |
| `test_publish_writes_track_record.py` | `backend/tests/` | Publish lifecycle + single `track_record` + reject double publish. |
| `ThreadReviewShell.tsx` | `frontend/components/thread/` | Thread-like layout chrome for admin review. |
| `IceCardReader.tsx` | `frontend/components/thread/` | Read-only ICE presentation (tabs, sections). |
| `page.tsx` | `frontend/app/admin/review/[draftId]/` | Route entry → workspace. |
| `ReviewWorkspace.tsx` | `frontend/app/admin/review/[draftId]/` | Data fetch, timers, publish/regenerate orchestration. |
| `ChecklistPanel.tsx` | `frontend/app/admin/review/_components/` | Five-item gate + regenerate notes. |
| `ChecklistPanel.test.tsx` | `frontend/app/admin/review/_components/` | RTL gate behaviour. |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `migrate.py` | `backend/app/db/` | Registered migration **`0009_…`**. |
| `card_repository.py` | `backend/app/services/` | Card fetch for review join; archive draft; signals + assessments reads for API/payload. |
| `main.py` | `backend/app/` | **`include_router(admin_review_router, prefix="/api/admin")`**. |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**`session_profiles.notify_categories`** (`text[]`, nullable)

| Semantics | Effect on publish fan-out |
|-----------|---------------------------|
| **`NULL`** | Treat as **subscribe-all** (matches every event category). |
| **`{}` / zero-length** | Same **subscribe-all** interpretation via `COALESCE(array_length(...), 0) = 0`. |
| Non-empty array | Notify only if **`events.category::text`** equals **any** array element (slug strings such as **`macro`**, **`rbi_policy`**, …). |

**`public.in_app_notifications`**

| Column | Notes |
|--------|--------|
| `user_id` | UUID aligned with **`session_profiles.user_id`** (no FK enforced). |
| `card_id` | FK → **`cards.id`** **`ON DELETE CASCADE`**. |
| `kind` | Default **`card_published`**. |
| `payload` | JSON with **`card_title`**, **`event_category`** at minimum—expand later for deep links. |

**Sequencing:** Apply **`0009`** **after** **`0008`** (cards parent exists). **`migrate.py`** ordering encodes this.

---

### B2. API / INTEGRATION CONTRACTS

**Base path:** `/api/admin` | **Auth (Phase 1):** none — internal/trusted network assumption.

#### `GET /api/admin/cards/{card_id}`

Returns JSON combining card + event columns plus **`instrument_assessments`** array. Key fields consumed by UI include **`lifecycle_state`**, **`title`**, ICE layers, **`event_title`**, **`event_category`**, **`event_confidence_score`**, **`evidence_layer`**.

#### `POST /api/admin/cards/{card_id}/publish`

**Request**

```json
{
  "editor_review_seconds": 1842
}
```

(`null` omits metric in audit payload semantics—server still publishes.)

**Response (success)**

```json
{
  "card_id": "uuid-string",
  "lifecycle_state": "published"
}
```

#### `POST /api/admin/cards/{card_id}/regenerate`

**Request**

```json
{
  "editor_notes": "Tighten dissent mechanism around INR liquidity…"
}
```

**Response**

```json
{
  "card_id": "new-uuid-string"
}
```

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Publish decision tree**

1. Resolve card + event → missing ⇒ **404**.  
2. If **`lifecycle_state != draft`** ⇒ **`PublishCardError`**.  
3. Snapshot **`signals`** into **`track_record.payload.signals_snapshot`**.  
4. In transaction: **`cards` → published**, **`events` → published**, **`track_record` INSERT**, **`in_app_notifications` INSERT … SELECT`** filtered profiles.  

**Regenerate decision tree**

1. Resolve card → missing ⇒ **404**.  
2. If not draft ⇒ **`RegenerateCardError`**.  
3. Call **`draft_card_from_event`** (consumes LLM slot per P1-S7).  
4. On success **`archive_card`** prior UUID (**`lifecycle_state → archived`** guarded so only drafts archive).  

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Detail |
|------|--------|
| **Append-only `track_record`** | Integration cleanup cannot **`DELETE`** audit rows—tests leave harmless orphans unless DB torn down. ⚠️ |
| **Notification UX absent** | Rows land in Postgres; **no in-app bell UI** in this story—delivery is “data ready”. |
| **`IceCardReader` vs full Thread** | `(app)/thread/page.tsx` remains placeholder until **P1-S10** imports reader + interactive Thread behaviours. |
| **Jest + Next lockfile noise** | Running **`CI=true`** when executing Jest reduces Next lockfile patch friction on some Windows setups. |
| **Single-sector Evidence unchanged** | Regenerate still inherits P1-S7 Evidence construction (banking matrix)—not expanded here. |

---

### B5. TESTING NOTES

| Layer | Coverage |
|-------|----------|
| **Backend** | `test_publish_writes_track_record.py` — requires **`SUPABASE_DB_URL`** (skips otherwise): asserts **`published`**, count **`track_record = 1`**, payload keys, rejects second publish. |
| **Frontend** | `ChecklistPanel.test.tsx` — Publish disabled until 5/5 checks; **`fireEvent`** clicks. |
| **Manual gaps** | Full regenerate E2E against live Gemini not automated here (cost + flake); notification fan-out with real **`session_profiles`** rows not fixture-tested. |

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable / artefact | Role |
|---------------------|------|
| **`SUPABASE_DB_URL`** | Required for publish/regenerate persistence paths (existing backend dependency). |
| **`GEMINI_*` / cost guard** | Regenerate inherits P1-S7 LLM env requirements. |
| **Migration `0009`** | Must be applied in target Supabase / Postgres before notifications column/table exist—publish transaction will fail if migration pending. |

---

### B7. HANDOVER NOTES FOR DEVELOPERS

| Topic | Guidance |
|-------|----------|
| **Where publish logic lives** | `backend/app/services/publish_card.py` — **single source of truth** for lifecycle + audit + fan-out. |
| **Where UI lifecycle branching lives** | `frontend/app/admin/review/[draftId]/ReviewWorkspace.tsx` — controls checklist vs read-only notice after publish. |
| **Extending notifications** | Join **`in_app_notifications`** to **`cards`** / **`events`** in a future API; consider dedupe keys if regenerate spam becomes an issue. |
| **Adding RBAC** | Gate **`/api/admin/**`** first—higher blast radius than page hiding behind Next middleware alone. |
| **Canonical Thread parity** | When implementing **P1-S10**, prefer importing **`IceCardReader`** rather than forking markup—colour drift becomes impossible to reconcile otherwise. |

---

*Document generated per `.cursor/rules/Post Implementation detailed document.md`.*
