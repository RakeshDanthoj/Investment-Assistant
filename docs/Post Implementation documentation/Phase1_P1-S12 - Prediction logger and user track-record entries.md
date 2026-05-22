# Post Implementation Detailed Document — P1-S12

**Version:** v1.0 | **Date:** 21-05-2026  
**Story ID:** P1-S12 (Phase 1, Story 12)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`

---

## Narrative style (read this first)

**P1-S10** put a **Prediction Logger** on The Thread’s Insight tab: four discrete choices, PRD copy, and a minimal **`POST /api/predictions`** that wrote only to **`user_predictions`** using a dev **`user_id` bridge**. That was enough to prove the UX slot and wire the ICE reading flow, but it was not yet the **honest learner record** the PRD promises for **The Mirror** (Phase 2).

**P1-S12** closes that gap. A signed-in reader must **form a view before the Context tab is revealed**; once they submit, the logger **collapses to a confirmation** and disappears if they unlock Context in the same session. On the server, **`predictions.log()`** is now the single write path: it inserts into **`user_predictions`** and, in the **same transaction**, appends a tagged row to **`track_record`** (`kind: user_prediction`). Auth is enforced via **Supabase JWT** (`CurrentUser`); duplicates return **409** with the **previously logged text**. **`GET /api/predictions/me`** lists the caller’s predictions for future Mirror and notification flows.

Architecturally, this story is a **small but critical integrity bridge**: it connects **reader identity** (auth), **per-card learner state** (`user_predictions`), and **append-only audit history** (`track_record`) without mutating ICE content. **P1-S11** already fans out **`signal_fired`** notifications to users who predicted; **P1-S12** ensures those rows exist with real auth and a durable audit trail.

If you remember **three** anchors: **auth-backed one prediction per user+card**, **dual-write to append-only `track_record`**, and **Context-tab gating in `useCard` session state**.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S12 |
| **Title** | Prediction logger + user track-record entries |
| **Category** | **Full Stack** (Postgres migration + service + authenticated API + Thread UI gating + tests) |

**What this story aimed to achieve (plain language)**

Before a reader opens the **Context (causal chain)** tab on a card, they should log one of four **non-advisory** prediction options. That choice is stored **once per user per card**, tied to their **Supabase identity**, and copied into the **append-only track record** for later grading in **The Mirror**. The UI must show the **exact PRD disclaimer**, collapse to a **confirmation block** after submit, and **hide the logger** once Context has been revealed in the current card-view session.

**How it fits into the overall application**

- **Upstream:** **P1-S4** (`user_predictions`, `track_record` schema + append-only RLS), **P1-S3** (Supabase session / JWT verification), **P1-S10** (Prediction Logger UI shell + Thread ICE flow).
- **Parallel:** **P1-S11** (signal notifications query `user_predictions`), **P1-S13** (bias audit — unrelated to predictions).
- **Downstream:** **Phase 2 / The Mirror** (grade user vs event using logged predictions + `track_record`); notification and analytics features that need **`GET /api/predictions/me`**.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items (plan mapping) and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **12.1** | Migration **`0012_user_predictions_unique.sql`**: idempotent **`UNIQUE (user_id, card_id)`** on **`user_predictions`** (constraint may already exist from **`0004_core_tables.sql`**). |
| **12.2** | Service **`predictions.log()`**: validates text length, asserts card exists, **dual INSERT** into **`user_predictions`** + **`track_record`**, **`conn.commit()`**; **`DuplicatePredictionError`** carries prior **`prediction_text`**. |
| **12.3** | API **`POST /api/predictions`** (auth, no body `user_id`); **`GET /api/predictions/me`** returns `{ items: [{ card_id, prediction_text, logged_at }] }`. |
| **12.4** | **`PredictionLogger.tsx`**: Supabase **`Bearer`** token; on success or **409**, replace UI with **`PREDICTION_CONFIRMATION`**; on mount, **`GET /me`** shows confirmation if prediction already exists for card. |
| **12.5** | **`useCard`**: **`contextRevealed`** + **`revealContext()`**; reset on **`cardId`** / **`view`** change; **`ThreadExperience`** calls **`revealContext()`** when ICE tier ≥ 1; **`InsightLayer`** receives **`showPredictionLogger={!contextRevealed}`**. |
| **12.6** | Exported **`PREDICTION_DISCLAIMER`** constant matches PRD §5 Screen 3; tested in **`PredictionLogger.test.tsx`**. |
| **12.7** | Backend integration tests (dual-write, 409 with prior text); route tests (auth, 409 payload); frontend tests (disclaimer, confirmation, gating). |

**Edge cases, validations, and error handling**

| Scenario | Behaviour |
|----------|-----------|
| **Not signed in** | POST returns **401**; UI shows *"Sign in to log your prediction."* |
| **Unknown card** | **`PredictionError("card_not_found")`** → **404** |
| **Invalid user FK** | **`ForeignKeyViolation`** → **404** (`user_or_card_invalid`) |
| **Duplicate submit** | **`UniqueViolation`** → fetch existing text → **409** with **`prediction_text`** in detail; UI treats **409** as logged (confirmation) |
| **Text too short/long** | Service + Pydantic: **8–2000** characters after strip |
| **DB unavailable** | **503** (`db_unavailable`) when **`SUPABASE_DB_URL`** missing |
| **Context already revealed** | Logger not rendered (`showPredictionLogger={false}`) |
| **Current / Original toggle** | **`contextRevealed`** resets — logger can appear again on fresh view (by design for session gating) |

**Business rules enforced (PRD-aligned)**

- **One prediction per (user, card)** — enforced by DB unique constraint + API **409**.
- **Four fixed prediction strings** — no buy/sell/hold or allocation advice (inherited from P1-S10; **`screen3CopyLint.test.ts`** still applies).
- **Disclaimer copy** — exact PRD string via **`PREDICTION_DISCLAIMER`**.
- **Append-only audit** — user predictions write **`track_record`** with **`kind: user_prediction`**, **`user_id`**, **`prediction_text`**, **`source: prediction_logger`**; no UPDATE/DELETE on **`track_record`**.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **`predictions.py` service (not extend `prediction_log.py` in place)** | Plan names **`predictions.log()`**; clear home for dual-write, list, and duplicate handling. | Inline SQL in router: harder to test and reuse. |
| **`prediction_log.py` as thin re-export shim** | Avoid breaking any stale imports; forwards to **`predictions.log`**. | Delete shim immediately: risk if external docs reference old module. |
| **Auth via `CurrentUser` / Supabase JWT** | Matches **`notifications`** route pattern; removes spoofable **`user_id`** in body. | Keep **`NEXT_PUBLIC_FINNWISE_USER_ID`**: insecure for production. |
| **`contextRevealed` in `useCard` hook** | Plan explicitly places gating state there; co-located with card fetch lifecycle. | Prop-drill only from **`ThreadExperience`**: plan deviation. |
| **Idempotent migration `0012`** instead of renumbering plan’s `0007` | **`0007_factor_db.sql`** already exists; safe add for DBs missing constraint. | New duplicate migration number: would conflict. |
| **Explicit `conn.commit()` in `log()`** | **`connection()`** context manager does not auto-commit; without it, writes rolled back on close. | Rely on implicit commit: silent data loss in production. |
| **409 → confirmation in UI** | User already has a logged view; better UX than error toast. | Show error on duplicate: contradicts “one honest record” UX. |
| **Integration tests skip `track_record` DELETE** | Append-only triggers deny DELETE; tests clean **`user_predictions`**, **`cards`**, **`events`**, **`auth.users`** only. | Disable triggers in tests: would invalidate append-only guarantees. |

**⚠️ Critical — do not reverse without replanning**

- **Do not** accept **`user_id` in POST body** again — enables impersonation and breaks audit integrity.
- **Do not** write **`user_predictions` without `track_record`** for logger submissions — Mirror and compliance expect append-only user-level entries.
- **Do not** **`DELETE` from `track_record`** in tests or app code — use orphan rows or separate test DB strategies.

**Assumptions**

- Readers who need to log predictions have completed Supabase magic-link sign-in (**P1-S3**).
- Phase 1 does not require prediction logging for anonymous users (UI prompts sign-in).
- **`GET /api/predictions/me`** is sufficient for Mirror v1; no pagination beyond **`limit`** (default 100, max 200 in service) needed yet.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1-S4** (`user_predictions`, `track_record`, append-only **0005**); **P1-S3** (`get_current_user`, Supabase JWT); **P1-S10** (Prediction Logger UI, ICE unlock, Thread route). |
| **Enables** | **The Mirror (Phase 2)** — grade **`user_predictions`** vs resolved card outcomes; richer “my predictions” surfaces using **`GET /me`**. |
| **Already consumes this** | **P1-S11** **`signal_monitor_runner._fan_out_signal_notifications`** — selects **`user_predictions`** for **`signal_fired`** notifications (now populated via authenticated path). |
| **Touches shared modules** | **`card_repository.fetch_card_detail_for_review`** (card existence check); **`app/db/migrate.py`** (migration list); **`InsightLayer`**, **`ThreadExperience`**, **`useCard`**. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Pattern** | **Domain service + thin API router**; HTTP mapping in **`_raise_prediction_error`**. |
| **Database** | No new tables; **`track_record.payload`** JSON for user entries; unique index on **`user_predictions(user_id, card_id)`**. |
| **API** | **`POST /api/predictions`** `{ card_id, prediction_text }` + **`Authorization: Bearer`**; **`GET /api/predictions/me?limit=100`**. |
| **Auth** | **`CurrentUser`** required on both endpoints; **401** if missing/invalid token. |
| **UI** | shadcn **`Card`**, **`Button`**, **`Alert`** on logger; PRD colours **`#F0F4FF` / `#BFDBFE`** preserved. |
| **Session gating** | Client-only **`contextRevealed`** — not persisted server-side (session = current Thread view). |
| **Libraries** | No new runtime deps; **`@supabase/ssr` client** for session token (same as **`NotificationBadge`**). |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `predictions.py` | `backend/app/services/` | **`log()`**, **`list_for_user()`**, dual-write, duplicate handling |
| `0012_user_predictions_unique.sql` | `backend/db/migrations/` | Idempotent unique constraint on **`user_predictions`** |
| `test_predictions_one_per_user_per_card.py` | `backend/tests/` | DB integration: duplicate raises **`DuplicatePredictionError`** with prior text |
| `test_predictions_write_to_track_record.py` | `backend/tests/` | DB integration: both tables receive rows with expected payload |
| `PredictionLogger.test.tsx` | `frontend/app/(app)/thread/_components/` | Disclaimer copy, submit confirmation, existing prediction state |
| `InsightLayer.test.tsx` | `frontend/app/(app)/thread/_components/` | Logger visible/hidden based on **`showPredictionLogger`** |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `predictions.py` | `backend/app/api/` | Auth via **`CurrentUser`**; removed body **`user_id`**; added **`GET /predictions/me`**; **409** includes **`prediction_text`** |
| `prediction_log.py` | `backend/app/services/` | Re-export shim → **`predictions.log`** |
| `migrate.py` | `backend/app/db/` | Registers **`0012_user_predictions_unique.sql`** |
| `PredictionLogger.tsx` | `frontend/app/(app)/thread/_components/` | Supabase auth, confirmation collapse, **`GET /me`** hydration, exported disclaimer constants |
| `useCard.ts` | `frontend/lib/cards/` | **`contextRevealed`**, **`revealContext()`**, reset on card/view change |
| `ThreadExperience.tsx` | `frontend/app/(app)/thread/_components/` | Wires gating: **`revealContext`** on ICE unlock; passes **`showPredictionLogger`** |
| `InsightLayer.tsx` | `frontend/app/(app)/thread/_components/` | Optional **`showPredictionLogger`** prop; conditional render |
| `test_predictions_route_shapes.py` | `backend/tests/` | Isolated FastAPI app for router tests; auth override; **409** + **`GET /me`** cases |
| `finnwise-phase1-implementation-tasks.md` | `docs/plans/` | P1-S12 acceptance criteria and subtasks marked complete |

*(P1-S10 created **`predictions.py` API** and **`PredictionLogger.tsx`**; P1-S12 hardened and extended them rather than replacing the Thread shell.)*

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**`user_predictions`** (from **P1-S4**, unchanged columns)

| Column | Notes |
|--------|--------|
| `user_id` | FK → **`auth.users`** |
| `card_id` | UUID (no FK to **`cards`** in schema) |
| `prediction_text` | Logged choice text |
| `logged_at` | Default **`now()`** |
| **Constraint** | **`user_predictions_user_card_key UNIQUE (user_id, card_id)`** — in **0004**; **0012** ensures presence idempotently |

**`track_record`** append-only row for each log

```json
{
  "kind": "user_prediction",
  "user_id": "<uuid>",
  "prediction_text": "<string>",
  "source": "prediction_logger"
}
```

- Multiple **`user_prediction`** rows per **`card_id`** are allowed (different users); same user cannot create two via **`user_predictions`** constraint.
- ⚠️ Test cleanup **must not** **`DELETE FROM track_record`** — triggers raise **`InsufficientPrivilege`**.

**Migration sequencing:** **`0012_user_predictions_unique.sql`** after **`0011_card_bias_flags.sql`** in **`MIGRATION_FILES`**.

---

### B2. API / INTEGRATION CONTRACTS

**`POST /api/predictions`**

- **Auth:** **`Authorization: Bearer <supabase_access_token>`** (required)
- **Body:**
  ```json
  {
    "card_id": "550e8400-e29b-41d4-a716-446655440000",
    "prediction_text": "Primary thesis unfolds — mechanisms align with the stated horizon."
  }
  ```
- **200:** `{ "ok": true }`
- **401:** Missing or invalid token
- **404:** Unknown card or invalid user/card FK
- **409:**
  ```json
  {
    "detail": {
      "code": "duplicate_prediction",
      "message": "Prediction already logged for this card",
      "prediction_text": "<previously logged text>"
    }
  }
  ```
- **422:** Validation / business errors
- **503:** DB unavailable

**`GET /api/predictions/me?limit=100`**

- **Auth:** Bearer required
- **200:**
  ```json
  {
    "items": [
      {
        "card_id": "550e8400-e29b-41d4-a716-446655440000",
        "prediction_text": "Mixed — competing mechanisms cancel; outcome stays ambiguous.",
        "logged_at": "2026-05-21T12:00:00Z"
      }
    ]
  }
  ```

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**`predictions.log()` flow**

```
POST body validated (Pydantic 8..2000 chars)
  → strip prediction_text
  → assert_card_exists(card_id)  [fetch_card_detail_for_review]
  → BEGIN (implicit transaction)
       INSERT user_predictions
       INSERT track_record (kind=user_prediction)
  → COMMIT
  → on UniqueViolation: fetch existing prediction_text → DuplicatePredictionError
  → on ForeignKeyViolation: PredictionError(user_or_card_invalid)
```

**Frontend gating flow**

```
Thread loads → useCard.contextRevealed = false
  → InsightLayer showPredictionLogger = true
User taps Context tab → IceTabs onUnlockTier(1) → revealContext()
  → showPredictionLogger = false (logger unmounts)
User toggles Current/Original → contextRevealed resets → logger may show again until Context tapped
```

**Hydration on reload (signed-in user)**

```
PredictionLogger mount → GET /api/predictions/me
  → if any item.card_id === cardId → phase = "logged" (confirmation only)
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **Anonymous readers** | Cannot log predictions without sign-in; Phase 1 routes remain ungated — product may want optional anonymous mode later (would conflict with FK to **`auth.users`**). |
| **Session gating is client-only** | Refresh after revealing Context but before logging does not server-enforce “must predict first”; ICE unlock state is not persisted. |
| **`GET /me` on every card mount** | Extra round-trip per Thread visit for signed-in users; acceptable for Phase 1; consider card-scoped endpoint later. |
| **Orphan `track_record` rows** | Deleting test **`cards`** leaves user_prediction audit rows — intentional under append-only policy. |
| **Circular import in `main.py`** | Full-app TestClient imports fail due to **`bias_detector` ↔ `card_detail`** cycle; route tests use isolated FastAPI app. Fix separately if whole-app test suite needed. |
| **Removed dev bridge** | **`NEXT_PUBLIC_FINNWISE_USER_ID`** no longer used by **`PredictionLogger`** — use real Supabase session. |

---

### B5. TESTING NOTES

| Layer | Coverage |
|-------|------------|
| **Backend unit/route** | **`test_predictions_route_shapes.py`**: 401 without auth, 409 with **`prediction_text`**, success propagation, **`GET /me`** shape (7 tests total with integration files) |
| **Backend integration** | **`test_predictions_one_per_user_per_card.py`**: duplicate + card_not_found |
| **Backend integration** | **`test_predictions_write_to_track_record.py`**: dual-write payload assertions |
| **Frontend** | **`PredictionLogger.test.tsx`**: disclaimer, submit → confirmation, existing prediction |
| **Frontend** | **`InsightLayer.test.tsx`**: gating prop |
| **Frontend** | **`screen3CopyLint.test.ts`**: forbidden words in **`PREDICTION_OPTIONS`** (from P1-S10) |
| **Manual** | Sign in → Thread → log prediction → confirm collapse → unlock Context → logger hidden; retry POST → 409; check **`track_record`** row in Supabase |

**Known gaps**

- No E2E Playwright covering full sign-in → log → Context gate.
- **`list_for_user`** not integration-tested against real DB (covered via mocked route test).

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| **`SUPABASE_DB_URL`** | Backend dual-write (required for persistence) |
| **`SUPABASE_URL`** + **`SUPABASE_ANON_KEY`** | JWT verification in **`get_current_user`** |
| **`NEXT_PUBLIC_API_BASE_URL`** | Frontend fetch target for predictions API |
| ~~**`NEXT_PUBLIC_FINNWISE_USER_ID`**~~ | **Deprecated for predictions** — replaced by Supabase session |

**Deployment sequencing**

1. Apply migrations through **`0012_user_predictions_unique.sql`** on Supabase.
2. Deploy backend (auth-required predictions API).
3. Deploy frontend (session-based logger).

Restart **`next dev`** / backend after env changes.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

1. **All prediction writes must go through `predictions.log()`** — do not insert into **`user_predictions`** from routers or other jobs without the matching **`track_record`** row (unless a future story explicitly defines a different audit kind).
2. **`track_record.payload.kind`** distinguishes entry types: **`initial_publish`**, **`signal_auto_update`**, **`user_prediction`** — Mirror and reporting should filter by **`kind`**.
3. **Context gating** lives in **`useCard.contextRevealed`** — if you add server-side “must predict before Context” enforcement, align with this client state to avoid double UX.
4. **Testing:** never **`DELETE FROM track_record`**; use unique UUIDs per test run and accept orphan audit rows in dev DBs.
5. **Auth pattern:** copy **`NotificationBadge.tsx`** / **`predictions.py` API** for other user-scoped endpoints.
6. **Product / Compliance:** prediction disclaimer is legally meaningful — keep **`PREDICTION_DISCLAIMER`** in sync with PRD §5; run **`PredictionLogger.test.tsx`** if copy changes.

**Related code paths**

| Concern | Location |
|---------|----------|
| Dual-write service | `backend/app/services/predictions.py` |
| HTTP routes | `backend/app/api/predictions.py` |
| JWT auth | `backend/app/core/auth.py` |
| Logger UI | `frontend/app/(app)/thread/_components/PredictionLogger.tsx` |
| Context gating | `frontend/lib/cards/useCard.ts`, `ThreadExperience.tsx` |
| Signal notification fan-out | `backend/app/services/signal_monitor_runner.py` |

**Contact by role:** Backend owner for service/API changes; Frontend owner for ICE gating UX; Riley/DB owner for migration or append-only policy questions.

---

**End of document**
