# Post Implementation Detailed Document — P1-S11

**Version:** v1.0 | **Date:** 18-05-2026  
**Story ID:** P1-S11 (Phase 1, Story 11)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`

---

## Narrative — how this fits in the architecture

Imagine FinnWise as a loop: **events** enter the world, become **cards**, readers **log predictions**, and the product promises that **signals** written on those cards (conditions to watch) stay honest relative to what is happening in markets and macro news. P1-S11 is the **automated referee** for that last part. It does not replace editors; it **triages** “did something in the real world corroborate this signal?” into three buckets—**high**, **medium**, and **low** confidence—and then **acts differently** in each case so the platform neither over-reacts to noise nor ignores structured evidence.

At a **high level**, the architecture is a **scheduled worker** (the signal monitor job) that wakes up on a cron rhythm, checks **whether Indian cash-market hours apply**, loads **recent “facts”** (today: mostly **recent `events` rows**—headlines and timestamps from your ingestion pipeline), loads every **pending signal** on **published / active / signal-triggered** cards, and for each pairing runs a **two-stage pipeline**: (1) **signal_check.evaluate** decides how strongly those facts align with the signal text (direct hits in a four-hour window vs weaker or older overlap), then (2) **confidence_gate.route** turns that shape into **high / medium / low** with a short **reason code**. The runner then **persists** the outcome: audit row always (**confidence_gate_log**), branch-specific side effects (auto-update + **track_record** + two-hour editor deadline on **high**, **editorial_signal_queue** on **medium**, **digest_log** only on **low**), and **fan-out** to **in_app_notifications** for users who **logged a prediction** on that card. The **web app** exposes **GET /api/notifications** and a small **NotificationBadge** that deep-links into the Thread.

Why this matters architecturally: you now have a **single orchestration module** (`signal_monitor_runner`) that is the **only** place where “signal fired → business consequence” is decided for automated paths. Downstream stories (admin UX for the queue—**P1-S15** in the plan, Phase 2 richer **market_facts**) should extend **inputs** or **surfaces**, not duplicate gate logic. The **append-only** nature of **track_record** is preserved: high-confidence auto-updates add a **new** row explaining what happened; we never rewrite history silently without going through defined flows.

**If you remember one thing:** the confidence gate is only as honest as the **fact stream**. Today that stream is deliberately **lightweight** (ingested **events** as a macro proxy). Treat **P2-S14** (richer market/index/NSE facts) as the upgrade path, not a reason to fork the gate.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S11 |
| **Title** | Signal monitoring + confidence-gated detection + in-app notifications |
| **Category** | **Full Stack** (Postgres migration + services + cron job + FastAPI + Next.js badge + tests) |

**What this story aimed to achieve (plain language)**

1. **Watch** pending signals on live-ish cards during **Indian equity cash session** (Mon–Fri, **09:15–15:30 IST** in code; Render cron still fires every 30 minutes UTC but the job **exits early** outside that window).  
2. **Compare** each signal’s text to a list of **market/macro “facts”** (implemented today primarily from **recent `events`** titles and timestamps—see narrative above).  
3. **Classify** corroboration into **high / medium / low** routes per PRD-style rules (≥3 strong recent sources → high; 1–2 → medium; weak/diffuse → low).  
4. **Persist** outcomes: **always** log to **confidence_gate_log**; **high** mutates card + signal + **track_record** + **editor_override_deadline**; **medium** queues **editorial_signal_queue**; **low** writes **digest_log** only.  
5. **Notify** users who **predicted on that card** via **in_app_notifications** (`kind = signal_fired`) and show a **pulsing badge** in the shell that links to the Thread.

**How it fits into the overall application**

- **Upstream:** **P1-S6** (`events`), **P1-S7**/`P1-S8` (cards with **signals** child rows, publish flow). **P1-S12** (**user_predictions**) defines who gets notifications.  
- **This story:** closes the loop from “card in the wild” to “signal corroboration → editorial / digest / auto-update → user ping.”  
- **Downstream:** **P1-S15** (admin UI for **editorial_signal_queue**), **P2-S14** (richer fact adapter merge), optional Phase 2 **read/unread** for notifications (backlog in Phase 2 plan).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories (plan checklist) mapped to behaviour**

| Sub-task | What it does in the codebase |
|----------|-------------------------------|
| **11.1** `signal_check.evaluate` | Tokenises signal + fact summaries, Jaccard overlap; **direct** = strong overlap **and** fact `observed_at` within **4h** of reference time; else **partial** if weaker overlap; **status** derived: `triggered` / `partial` / `none`. Returns **source_id** buckets for gate. |
| **11.2** `confidence_gate.route` | Maps direct/partial counts → **`high` / `medium` / `low`** + reason string. **Raises** if called with empty evaluation (caller must skip when status is `none`). |
| **11.3** High path | Updates **card**: `lifecycle_state → signal_triggered`, sets **editor_override_deadline** = now+**2h**, appends short note to **insight_layer**; marks **signal** `triggered` + **triggered_at**; inserts **track_record** payload `kind: signal_auto_update` with sources + deadline. |
| **11.4** Medium path | **Upsert** **editorial_signal_queue** (`ON CONFLICT` refresh pending payload); signal stays **pending** for automation until editorial resolves elsewhere. |
| **11.5** Low path | Insert **digest_log** once per signal (dedupe: skip if digest row already exists for that **signal_id**—prevents 30-min spam). Card/signal unchanged for low. |
| **11.6** Notifications | **INSERT…SELECT** into **in_app_notifications** from **user_predictions** for that **card_id**, `kind = signal_fired`. Medium path **suppresses repeat** fan-out if queue row already existed (first medium only notifies). |
| **11.7** NotificationBadge | Client fetches **GET /api/notifications** with Supabase **Bearer**; if any `signal_fired`, show pulsing dot; click → **`/thread/{cardId}`**. |
| **11.8** Cron | **Render** `*/30 * * * *`; **IST gate inside Python** (NSE cash window). |
| **11.9** Tests | Gate branches, monitor DB integration (with **`only_card_id`** isolation), fan-out SQL sanity, IST window tests. |

**Edge cases, validations, error handling**

- **Outside market hours:** `MonitorSummary.skipped_market_hours = True`; no DB reads for signals.  
- **Missing `SUPABASE_DB_URL`:** Summary `skipped_no_db`; job logs warning (cron must have **direct Postgres URL**—same as other `psycopg` paths).  
- **Evaluate `none`:** No gate log, no branch, no notification—signal stays pending.  
- **Low digest dedupe:** Second run skips processing for that signal (no duplicate digest/gate spam from repeated low classification).  
- **Transaction safety:** Single **`conn.transaction()`** per signal after fixing an earlier bug where a pre-probe cursor left an open transaction and **rolled back** writes silently.  
- **Shared dev DB pollution:** `only_card_id` optional filter on the monitor query for **tests** so stray pending signals don’t affect assertions.

**Business rules enforced**

- Only cards in **`published` / `active` / `signal_triggered`** lifecycle with **`signals.state = pending`** are scanned.  
- **High** confidence implies **auto surface change** (lifecycle + insight note) and **editor override window** timestamp on the card.  
- **Low** never mutates card content or signal state (only digest + audit + optional notify on first hit).  
- ⚠️ **Notifications** are meant for users who **engaged with predictions**—not all subscribers.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Facts from `events` table first** | Reuses **P1-S6** output; no new vendor for v1; same DB connection pattern. | Immediate NSE price API: more scope + reliability work (deferred **P2-S14**). |
| **`psycopg` in runner** | Matches **publish_card** / **card_repository** for transactional updates + JSONB. | PostgREST only: awkward for multi-statement atomic branch. |
| **`confidence_gate_log` + branch tables** | Supports PRD §13-style **override / gate analysis** later. | Logging only to application logs: lost for SQL analytics. |
| **`editorial_signal_queue` unique (card_id, signal_id)** | Idempotent medium path; safe reruns. | Duplicate queue rows per rerun: noisy ops. |
| **`only_card_id` test hook** | Integration tests on real Supabase dev DB without deleting global pending signals. | Truncate all signals: destructive. |
| **NSE session window 09:15–15:30 IST** | Aligns with **cash session** end; pre-open not included. | 09:00–16:00: broader than exchange continuous session. |

**⚠️ Critical — do not reverse without replacing behaviour**

- **Do not** split gate persistence across **multiple connections** without a single transaction for one signal’s outcome—risk of **silent rollback** (debugged during implementation).  
- **Do not** delete **`track_record`** rows in tests: **append-only triggers** forbid DELETE.  
- **Do not** remove **`SUPABASE_DB_URL`** from Render cron for this job: REST keys alone are insufficient for the runner’s SQL path.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1-S4/6:** `events`; **P1-S7/8:** `cards`, `signals`, publish; **P1-S9?** N/A; **P1-S12:** `user_predictions` for fan-out. |
| **Enables** | **P1-S15:** admin list UI for **editorial_signal_queue**; **P2-S14:** swap/merge fact providers in **market_facts** + runner default `facts_provider`. |
| **Shared models** | `MarketFact` / `SignalEvalResult` / `GateDecision`; enums **LifecycleState**, **SignalState**. |
| **Touches** | `in_app_notifications` (shared with **P1-S8** publish alerts); **track_record** (shared append-only audit). |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Pattern** | Pipeline: **fetch candidates → evaluate → route → transactional side effects**; injectable **`facts_provider`** for tests. |
| **Schema** | New: **confidence_gate_log**, **digest_log**, **editorial_signal_queue**; **cards.editor_override_deadline**. |
| **API** | **`GET /api/notifications`** — **Bearer** required; **`GET /api/admin/signal-queue`** — Phase 1 open admin (same posture as other admin routes). |
| **UI** | **NotificationBadge** in **AppShell** (mobile) + **Sidebar** (desktop); minimal surface—no notification centre yet. |
| **Tooling** | **httpx** not required in S11 core path; **zoneinfo** for IST. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0010_signal_monitoring.sql` | `backend/db/migrations/` | Gate log, digest, editorial queue, `editor_override_deadline`. |
| `signal_check.py` | `backend/app/services/` | Fact vs signal evaluation. |
| `confidence_gate.py` | `backend/app/services/` | High/medium/low routing. |
| `market_facts.py` | `backend/app/services/` | Load recent `events` as `MarketFact` list. |
| `signal_monitor_runner.py` | `backend/app/services/` | Orchestration, IST window, DB branches, fan-out. |
| `notifications.py` | `backend/app/api/` | `GET /api/notifications`. |
| `admin_signal_queue.py` | `backend/app/api/` | `GET /api/admin/signal-queue`. |
| `test_confidence_gate.py` | `backend/tests/` | Gate branches + empty guard. |
| `test_signal_check.py` | `backend/tests/` | Evaluate scenarios. |
| `test_signal_monitor_logs_override_decisions.py` | `backend/tests/` | High/medium/low DB integration. |
| `test_signal_notifications_fanout.py` | `backend/tests/` | Fan-out targets `user_predictions`. |
| `test_ist_market_session.py` | `backend/tests/` | NSE cash window boundaries. |
| `NotificationBadge.tsx` | `frontend/components/Topbar/` | Badge + navigation. |
| `NotificationBadge.test.tsx` | `frontend/components/Topbar/` | RTL + mocks. |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `signal_monitor.py` | `backend/app/jobs/` | Real implementation calling `run_signal_monitor`; log IST message. |
| `migrate.py` | `backend/app/db/` | Register **`0010_signal_monitoring.sql`**. |
| `main.py` | `backend/app/` | Routers: **notifications**, **admin_signal_queue** (and pre-existing admin review wiring as in repo). |
| `render.yaml` | repo root | Cron schedule + comment on IST gate. |
| `AppShell.tsx` | `frontend/components/Sidebar/` | Embeds **NotificationBadge**. |
| `Sidebar.tsx` | `frontend/components/Sidebar/` | Badge in desktop header row. |
| `finnwise-phase1-implementation-tasks.md` | `docs/plans/` | P1-S11 tasks/AC marked done; **11.8** text aligned to NSE hours. |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

| Object | Detail |
|--------|--------|
| **cards.editor_override_deadline** | `timestamptz` NULL; set on **high** path to now+2h. |
| **confidence_gate_log** | `card_id`, `signal_id`, `gate` (`high`/`medium`/`low`), `reason`, `sources` jsonb, `created_at`; FKs to card/signal with CASCADE. |
| **digest_log** | Low-path internal digest; `signal_id` / `card_id` nullable per migration; `summary` + `payload`. |
| **editorial_signal_queue** | Medium path; **UNIQUE** `(card_id, signal_id)`; `status` pending/dismissed/resolved; `payload` jsonb. |

**Sequencing:** Apply **`0010_signal_monitoring.sql`** after **0009** (or as listed in `migrate.py`).  
**⚠️** **`track_record`** remains append-only; do not add migrations that require DELETE for normal operation.

---

### B2. API / INTEGRATION CONTRACTS

| Method | Route | Auth | Response sketch |
|--------|-------|------|------------------|
| GET | `/api/notifications?limit=` | **Bearer** (Supabase JWT via `Authorization`) | `{ items: [{ id, card_id, kind, payload, created_at }], count }` |
| GET | `/api/admin/signal-queue?status=pending&limit=` | **None** (Phase 1 admin posture) | Array of queue rows (id, card_id, signal_id, status, gate, reason, payload, created_at) |

**Frontend:** `NotificationBadge` uses browser Supabase session + `getApiBaseUrl()`.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Evaluation (simplified)**

- Tokenise with regex `[a-z0-9]{3,}` on lowercased text.  
- **Jaccard** intersection/union of token sets.  
- **Direct:** `jaccard >= direct_min` (default ~0.28) **and** fact age ≤ **4h** vs reference.  
- **Partial:** `jaccard >= partial_min` (default ~0.12) but not classified as direct, or strong overlap outside window.

**Gate**

- **High:** `len(direct) ≥ 3`  
- **Medium:** `1 ≤ len(direct) ≤ 2` OR `(len(direct)==0 and 1 ≤ len(partial) ≤ 2)`  
- **Low:** any other non-empty evaluation  
- **`route()`** not called when evaluation status is **`none`**.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **Fact source** | Primarily **`events`** titles—**not** live prices; **P2-S14** planned. |
| **Admin queue UI** | API only in S11; **P1-S15** adds screen. |
| **Notification UX** | No read/dismiss/TTL; **Phase 2 optional** backlog. |
| **Cron vs IST** | Render runs **UTC** schedule; job **self-gates**—wasted invocations outside session are cheap no-ops. |
| **Medium repeated gate logs** | Each run may insert another **confidence_gate_log** for same pending signal until editorial resolves—acceptable for analytics; revisit if noisy. |

---

### B5. TESTING NOTES

| Suite | Coverage |
|-------|----------|
| **Unit** | `test_confidence_gate`, `test_signal_check`, `test_ist_market_session`, `test_signal_notifications_fanout` (SQL string contract). |
| **Integration** | `test_signal_monitor_logs_override_decisions` — requires **`SUPABASE_DB_URL`**; uses **`only_card_id`**; cleanup avoids **`track_record` DELETE**. |

**Gaps:** No E2E with real **auth.users** + predictions fan-out count; optional future test with service-role seed.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable / setting | Where | Purpose |
|--------------------|-------|---------|
| **`SUPABASE_DB_URL`** | Backend + **Render cron `finnwise-signal-monitor`** | `psycopg` for monitor + migrations locally. |
| **`SUPABASE_URL` / keys** | Notifications API | Auth verify + (elsewhere) REST. |
| **Cron** | **`render.yaml`** `*/30 * * * *` | Job decides IST session. |

---

### B7. HANDOVER NOTES FOR DEVELOPERS

1. **Start here:** `backend/app/services/signal_monitor_runner.py` — single orchestration.  
2. **Tune matching:** `backend/app/services/signal_check.py` (thresholds/windows)—changes affect gate distribution.  
3. **Add facts:** extend `market_facts.py` or introduce **`market_facts_adapters.py`** (**P2-S14**); wire merged list into **default** `facts_provider` in runner.  
4. **Never** delete **`track_record`** in fixtures—use orphan rows or test DB scrub policies.  
5. **Product / compliance:** Coordinate changes to **auto-update copy** in insight layer with editorial policy.  
6. **Contact:** **Backend owner** for gate semantics; **frontend owner** for notification UX; **Product** for session hours if pre-open/MTF scope expands.
