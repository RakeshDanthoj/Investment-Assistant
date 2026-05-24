# Post Implementation Detailed Document — P2-S10

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S10 (Phase 2, Story 10)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P1-S11** already fires in-app notifications when the signal monitor routes a hit through the confidence gate. **P2-S10** adds an **email channel** for the same moment of interest — but only when a signal’s `state` transitions to **`triggered`** on the **high-confidence path** (not medium editorial queue or low digest-only paths). Users who have **logged a prediction** on that card (and, when P2-S8 ships, users who **saved the thread**) receive a plain informational email: *a signal you were watching has fired*, with a deep link to the Thread card and a one-click unsubscribe link.

The implementation is deliberately **provider-agnostic** (Resend or Postmark), **opt-in by default** for Phase 2 testers (`signal_fired_enabled = true` until they unsubscribe), and **safe when unconfigured** — if `EMAIL_API_KEY` is missing, the signal monitor still runs; sends are skipped and logged. Copy is lint-tested to exclude buy/sell/hold recommendation language. Preferences can be managed at **`/settings/email`** or via the unsubscribe link in every message.

**Tests executed and passed:** 10 pytest (`test_email_on_signal.py`, `test_unsubscribe.py`, `test_email_template_lint.py`). No new Jest tests were added for the settings page in this story.

**Three anchors:** (1) **Email only on `triggered`** (high path), not every gate tier; (2) **stake + opt-in + dedupe** before send; (3) **no recommendation copy** in templates (automated lint).

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S10 |
| **Title** | Email notifications for fired signals |
| **Category** | **Full Stack** |

**What this story aimed to achieve**

Users who care enough to log a prediction (or save a thread) should get an email when a watched signal actually fires, so they can return to FinnWise at the right time. Emails must be informational only — never buy/sell/hold advice — and must include a compliant one-click unsubscribe. Users can also toggle signal emails in Settings.

**How it fits into the overall application**

This story extends **P1-S11** (signal monitor + in-app `signal_fired` notifications) with an outbound email channel. It depends on **P1-S12** (`user_predictions`) for stakeholder detection and will also include **`saved_threads`** when **P2-S8** lands. It is parallel to **P2-S9** (Portfolio Protector) and **P2-S11** (Map). In-app Mirror graded notifications (**P2-S3**) remain separate; this story does not send email on card resolve.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **10.1** | Env vars: `EMAIL_PROVIDER`, `EMAIL_API_KEY`, `EMAIL_FROM`, `APP_PUBLIC_URL` (documented in `scripts/README.md`). |
| **10.2** | Migration `0017`: `user_email_preferences`, `unsubscribe_tokens`, `signal_email_log`. |
| **10.3** | `email_client.send()` — Resend or Postmark; template render with `{{var}}` placeholders. |
| **10.4** | `signal_fired.html` — informational copy, Thread deep link, unsubscribe link; forbidden-word lint. |
| **10.5** | `email_on_signal.fan_out()` — stakeholders with prediction/saved thread; opted-in; not already sent. |
| **10.6** | `GET /unsubscribe?token=` — single-shot token; sets `signal_fired_enabled = false`. |
| **10.7** | `/settings/email` — GET/PUT `/api/email/preferences` with Supabase Bearer token. |
| **10.8** | Pytest: fan-out scope, opt-in, high-path hook, unsubscribe, template lint. |

**Functional breakdown**

1. Signal monitor evaluates pending signals during NSE cash hours.
2. **High** gate tier → `_high_path` sets `signals.state = triggered`, updates card lifecycle, appends `track_record`, fans out in-app notifications (P1-S11), then calls **`email_on_signal.fan_out`** in the same transaction.
3. Fan-out collects stakeholder `user_id`s from `user_predictions` (and `saved_threads` if table exists).
4. For each user: ensure prefs row (default opt-in), skip if opted out or already in `signal_email_log`, resolve email from `auth.users`, create unsubscribe token, send via provider (or skip if unconfigured), insert send log.
5. User clicks unsubscribe → HTML confirmation; or opens Settings → toggles checkbox → `PUT /api/email/preferences`.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Email not configured | `email_client.send` returns `False`; monitor continues; no exception. |
| User has no email in `auth.users` | Skip with warning log; no send log row. |
| User opted out | `_is_opted_in` returns false; skip. |
| Duplicate monitor run | `signal_email_log` PK `(user_id, signal_id)` prevents second email. |
| Invalid unsubscribe token | 404 HTML “link expired” page. |
| Token already used | `used_at IS NOT NULL` → 404. |
| Medium/low gate only | No email (signal state stays `pending`). |
| `saved_threads` missing (pre P2-S8) | Predictions-only fan-out; code probes `information_schema` before querying saved threads. |
| DB unavailable | Unsubscribe/prefs APIs return 503. |

**Business rules**

- Email subject: *“A signal you were watching has fired — FinnWise”*.
- Body must not contain buy/sell/hold or rupee allocation advice (lint enforced).
- Default **opt-in** for signal-fired emails (`signal_fired_enabled` default `true`).
- Unsubscribe is **single-shot** per token; re-clicking same link fails.
- Email sends only when user has **stake** on the card (prediction or saved thread).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Migration `0017` not `0014`** | `0014_user_predictions_gap_insight.sql` already applied in sequence. |
| **Email only on high path (`triggered`)** | Acceptance criteria tie email to `signal_state` transition; medium/low paths do not set `triggered`. |
| **Separate from in-app fan-out** | P1-S11 notifies on medium/high/low with different rules; email scope is stricter. |
| **`signal_email_log` table** | Idempotent sends without relying on provider idempotency keys. |
| **Unsubscribe via `/backend/unsubscribe` on frontend origin** | Uses existing Vercel `/backend` proxy; `APP_PUBLIC_URL` must be frontend host. |
| **No-op when credentials missing** | Local/dev and CI should not require a live email provider. |
| **Resend + Postmark in one client** | Plan allowed either; env `EMAIL_PROVIDER` selects implementation. |
| **Prefs row created lazily** | First read or fan-out inserts default opt-in row (`ON CONFLICT DO NOTHING`). |

⚠️ **Do not send email on medium or low gate paths** without explicit product change — acceptance criteria and SEBI posture assume informational alerts only when the signal is actually **triggered**.

⚠️ **Do not add buy/sell/hold language to templates** — `test_email_template_lint.py` will fail; legal/compliance requirement from Phase 2 plan.

⚠️ **`APP_PUBLIC_URL` must be the frontend origin**, not the Render API URL — unsubscribe and Thread links depend on `/backend` proxy or same host routing.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / artifacts |
|-----------|---------------------|
| **Upstream** | P1-S11 `signal_monitor_runner` (high path, `signals.state`); P1-S12 `user_predictions`; Supabase `auth.users.email`. |
| **Parallel** | P2-S8 `saved_threads` (fan-out ready when table exists); P2-S9 personalisation; P2-S11 Map. |
| **Downstream** | None blocking; future email types would extend `user_email_preferences` and templates. |
| **Related but separate** | P2-S3 `card_graded` in-app notifications (no email); P1-S11 in-app `signal_fired` rows (still inserted on broader gate rules). |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | `email_client` (transport) + `email_on_signal` (fan-out rules) + thin API routes + settings UI. |
| **Schema** | Three new tables: prefs, tokens, send log; no changes to `signals` or `user_predictions`. |
| **API auth** | Preferences: Bearer JWT (`CurrentUser`). Unsubscribe: public token (no auth). |
| **UI** | `/settings/email` card with checkbox; link from sidebar user menu. |
| **Third-party** | Resend REST or Postmark REST via `httpx`; no SDK dependency. |
| **Templates** | Static HTML in `backend/email-templates/` with `{{card_title}}`, `{{thread_url}}`, `{{unsubscribe_url}}`. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| 0017 migration | `backend/db/migrations/0017_user_email_preferences.sql` | Prefs, unsubscribe tokens, send log |
| email_client.py | `backend/app/services/email_client.py` | Provider abstraction + template render |
| signal_fired.html | `backend/email-templates/signal_fired.html` | Signal-fired HTML template |
| email_on_signal.py (service) | `backend/app/services/email_on_signal.py` | Stakeholder fan-out, opt-in, dedupe |
| email_on_signal.py (job) | `backend/app/jobs/email_on_signal.py` | CLI manual fan-out for operators |
| unsubscribe.py | `backend/app/api/unsubscribe.py` | `GET /unsubscribe?token=` HTML flow |
| email_preferences.py | `backend/app/api/email_preferences.py` | `GET/PUT /api/email/preferences` |
| page.tsx | `frontend/app/(app)/settings/email/page.tsx` | Settings page shell (auth gate) |
| EmailPrefsForm.tsx | `frontend/app/(app)/settings/email/_components/EmailPrefsForm.tsx` | Load/save prefs via API |
| test_email_on_signal.py | `backend/tests/test_email_on_signal.py` | Fan-out scope, opt-in, high-path hook |
| test_unsubscribe.py | `backend/tests/test_unsubscribe.py` | Token validation + HTTP responses |
| test_email_template_lint.py | `backend/tests/test_email_template_lint.py` | Forbidden wording in templates |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| settings.py | `backend/app/core/settings.py` | `EMAIL_PROVIDER`, `EMAIL_API_KEY`, `EMAIL_FROM`, `APP_PUBLIC_URL` |
| migrate.py | `backend/app/db/migrate.py` | Register `0017_user_email_preferences.sql` |
| signal_monitor_runner.py | `backend/app/services/signal_monitor_runner.py` | Call `fan_out_signal_emails` from `_high_path` after `triggered` |
| main.py | `backend/app/main.py` | Mount `email_preferences` and `unsubscribe` routers |
| UserChip.tsx | `frontend/components/Sidebar/UserChip.tsx` | Menu link to `/settings/email` |
| README.md | `scripts/README.md` | P2-S10 env var table and behaviour notes |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S10 acceptance criteria and tasks marked complete |

---

### A8. TESTS EXECUTED

| Test file | Status | What it covers |
|-----------|--------|----------------|
| `test_email_on_signal.py` | **Passed (5)** | SQL includes `user_predictions` + `saved_threads`; opt-in + dedupe in fan-out; high path calls email fan-out; mocked skip when opted out; mocked send when opted in |
| `test_unsubscribe.py` | **Passed (3)** | Invalid UUID token rejected; success HTML 200; invalid/used token 404 |
| `test_email_template_lint.py` | **Passed (2)** | Source template has no buy/sell/hold; rendered HTML has no forbidden words + unsubscribe present |

**Backend command**

```text
cd backend
python -m pytest tests/test_email_on_signal.py tests/test_unsubscribe.py tests/test_email_template_lint.py -q
```

→ **10 passed** (executed 24-05-2026)

**Frontend**

No new Jest/RTL tests in this story. Settings UI should be manually verified (see checklist below).

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Table:** `public.user_email_preferences`

| Column | Type | Notes |
|--------|------|--------|
| `user_id` | `uuid` PK → `auth.users` | One row per user |
| `signal_fired_enabled` | `boolean NOT NULL DEFAULT true` | Opt-in default for Phase 2 |
| `updated_at` | `timestamptz` | Set on preference change |

**Table:** `public.unsubscribe_tokens`

| Column | Type | Notes |
|--------|------|--------|
| `token` | `uuid` PK | Embedded in email link |
| `user_id` | `uuid` → `auth.users` | Owner |
| `created_at` | `timestamptz` | Issued at send time |
| `used_at` | `timestamptz NULL` | Set on successful unsubscribe |

**Table:** `public.signal_email_log`

| Column | Type | Notes |
|--------|------|--------|
| `user_id`, `signal_id` | composite PK | Idempotent send guard |
| `sent_at` | `timestamptz` | Audit timestamp |

**Migration sequence:** Apply after `0016_lens_queries.sql`.

---

### B2. API / INTEGRATION CONTRACTS

| Method | Route | Auth | Response |
|--------|-------|------|----------|
| GET | `/api/email/preferences` | Bearer (Supabase JWT) | `{ "signal_fired_enabled": true }` |
| PUT | `/api/email/preferences` | Bearer | Body: `{ "signal_fired_enabled": false }` → same shape |
| GET | `/unsubscribe?token={uuid}` | None (public) | HTML 200 success or HTML 404 invalid |

**Proxied unsubscribe (production browser)**

```text
GET {APP_PUBLIC_URL}/backend/unsubscribe?token={uuid}
```

→ Next.js `app/backend/[...path]/route.ts` → Render `{API}/unsubscribe?token=...`

**Preferences example**

```json
{ "signal_fired_enabled": true }
```

---

### B3. BUSINESS LOGIC & RULES (Detailed)

```
Signal monitor (P1-S11)
  → evaluate pending signal
  → route gate decision
  → if tier == "high":
       UPDATE signals SET state = 'triggered'
       UPDATE card lifecycle → signal_triggered
       INSERT track_record
       fan_out in-app notifications (existing)
       email_on_signal.fan_out(card_id, signal_id, card_title)
         → stakeholders = predictions ∪ saved_threads (if table exists)
         → for each user_id:
              skip if not opted in
              skip if signal_email_log exists
              skip if no auth.users.email
              create unsubscribe token
              email_client.send(signal_fired.html)
              INSERT signal_email_log
  → if tier == "medium" | "low":
       no email (state may remain pending)
```

**Template variables**

| Variable | Source |
|----------|--------|
| `card_title` | Card title from monitor row |
| `thread_url` | `{APP_PUBLIC_URL}/thread/{card_id}` |
| `unsubscribe_url` | `{APP_PUBLIC_URL}/backend/unsubscribe?token={token}` |

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Notes |
|------------|--------|
| **`saved_threads` not in Phase 2 yet** | Fan-out code probes for table; only predictions count until P2-S8 migration. |
| **No Jest test for settings page** | Manual toggle verification required. |
| **No E2E with live provider** | Unit tests mock `email_client.send`; Resend/Postmark not hit in CI. |
| **Email only on automated high path** | Manual signal state edits do not trigger fan-out unless `_high_path` runs. |
| **Single email type** | Only `signal_fired`; future channels need new preference columns + templates. |
| **Unsubscribe needs frontend proxy in prod** | Direct `http://127.0.0.1:8000/unsubscribe` works locally; production emails should use `APP_PUBLIC_URL` + `/backend`. |

---

### B5. TESTING NOTES

| Type | Covered |
|------|---------|
| **Automated** | Fan-out SQL scope; opt-in/dedupe logic; high-path wiring; unsubscribe token rules; template forbidden words |
| **Manual (required)** | Migration applied; provider domain verified; env on Render; send test email; unsubscribe link; settings toggle |

See **Manual verification checklist** below.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required for email send | Purpose |
|----------|-------------------------|---------|
| `EMAIL_PROVIDER` | Yes (to send) | `resend` or `postmark` |
| `EMAIL_API_KEY` | Yes (to send) | Provider API key |
| `EMAIL_FROM` | Yes (to send) | Verified sender address |
| `APP_PUBLIC_URL` | Yes (correct links) | Frontend origin for Thread + unsubscribe |
| `SUPABASE_DB_URL` | Yes | Migrations + fan-out + prefs |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` | Yes (prefs API) | JWT verification |
| `NEXT_PUBLIC_API_BASE_URL` | Yes (settings UI) | Browser → backend for `/api/email/preferences` |

When `EMAIL_API_KEY` is unset, signal monitoring and in-app notifications are unaffected.

**Deploy sequencing:** apply migration → set email env on Render → redeploy backend → set `APP_PUBLIC_URL` to production frontend → verify sender domain in Resend/Postmark.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing this code**

1. Read `signal_monitor_runner._high_path` — email is downstream of `triggered` transition only.
2. Do not conflate with P2-S3 `card_graded` emails (there are none) or P1-S11 in-app insert logic.
3. Any new email template must pass `test_email_template_lint.py`.

**Key paths**

| Concern | Path |
|---------|------|
| Send transport | `backend/app/services/email_client.py` |
| Fan-out rules | `backend/app/services/email_on_signal.py` |
| Trigger hook | `backend/app/services/signal_monitor_runner.py` → `_high_path` |
| Unsubscribe | `backend/app/api/unsubscribe.py` |
| Prefs API | `backend/app/api/email_preferences.py` |
| Settings UI | `frontend/app/(app)/settings/email/` |
| Template | `backend/email-templates/signal_fired.html` |

**Common mistakes**

- Sending email on medium/low gate tiers.
- Setting `APP_PUBLIC_URL` to the Render API host (breaks unsubscribe proxy).
- Forgetting migration `0017` (prefs/tokens/log tables missing).
- Adding marketing or recommendation copy to templates.

**Contact by role:** Riley — email channel; Jordan — signal monitor; Sam — frontend settings surfaces.

---

## Manual verification checklist (operator)

These steps are **not** automated in CI.

### 1. Apply database migration (one-time per environment)

From repo root:

```text
pip install -e "./backend[dev]"
python scripts/apply_migrations.py
```

Confirm `0017_user_email_preferences.sql` appears in `public.schema_migrations`.

### 2. Configure email provider

1. Create Resend or Postmark account; verify sending domain.
2. Add to repo-root `.env.local` and Render:

```text
EMAIL_PROVIDER=resend
EMAIL_API_KEY=re_...
EMAIL_FROM=FinnWise <alerts@yourdomain.com>
APP_PUBLIC_URL=https://investment-assistant-frontend.vercel.app
```

3. Redeploy backend after env changes.

### 3. Settings UI

1. Sign in → user menu → **Email notifications** (or `/settings/email`).
2. Confirm toggle loads; turn off → refresh → still off.
3. Turn on again.

### 4. End-to-end email (staging)

1. Log a prediction on a card with a pending signal.
2. Run signal monitor in conditions that produce a **high** gate hit (or use job CLI with test data).
3. Confirm email received; copy has no buy/sell/hold; **View in FinnWise** opens Thread.
4. Click **Unsubscribe** → confirmation page.
5. Confirm `/settings/email` shows alerts disabled.

### 5. CLI manual fan-out (optional)

```text
cd backend
python -m app.jobs.email_on_signal --card-id <uuid> --signal-id <uuid> --card-title "Test card"
```

---

## Audit style summary

| Acceptance criterion | Status | Evidence |
|---------------------|--------|----------|
| Resend/Postmark + templates in `backend/email-templates/` | Done | `email_client.py`, `signal_fired.html` |
| Trigger on `signal_state` → `triggered` with stake | Done | `_high_path` → `fan_out`; predictions + saved_threads probe |
| One-click unsubscribe in every email | Done | Template link; `GET /unsubscribe` |
| `user_email_preferences`; default opt-in | Done | Migration default `true`; lazy insert |
| No recommendation copy | Done | `test_email_template_lint.py` |
| Settings page | Done | `/settings/email` |
| Automated tests | Done | 10 pytest passed |

---

*End of document — P2-S10 v1.0*
