# FinnWise — Phase 1 Implementation Tasks (Foundation, Months 1–3)

_Source PRD_: `FinnWise_PRD_v3_Final.md` — Section 10 / Phase 1 plus all binding decisions in §5, §6, §7, §8, §11.
_generated for independent execution without prd-planner_

## Overview

- **Summary**: Phase 1 ships the V1 foundation. Three surfaces go live — Onboarding, The Pulse, The Thread — backed by the three-call LLM card-synthesis pipeline, the event-detection scheduled job, the Banking-sector slice of the Factor Exposure Database, signal monitoring with confidence-gated triggering, append-only track-record logging, and the bias audit log. **Route and API auth gating are intentionally omitted for Phase 1** (open access to app surfaces); magic-link / invite-only access is a post–Phase 1 hardening item before wider external testing.
- **Tech stack** (PRD §9): Next.js + React + Tailwind (frontend on Vercel), Python + FastAPI (backend on Render), PostgreSQL via Supabase, Supabase Auth (magic link), Anthropic Claude Sonnet (LLM). Tests: Jest + React Testing Library (frontend), Pytest + httpx (backend). Single `.env.local` for all secrets — never duplicated across `.env` / `.env.example` files (per workspace rules).

- **Slicing approach**: every story is an end-to-end vertical slice — UI + API + DB minimum, with explicit test step(s) in the checklist. Parent task IDs are **per-phase** (this file uses `1.0`–`14.0`). All MMJ, SEBI, bias-flag, and track-record constraints from PRD §6, §8.6, §11 are treated as non-negotiable acceptance criteria, not nice-to-haves.

## Team plan

| Developer | Focus | Total points |
|-----------|-------|---------------|
| Jordan | Backend pipeline, LLM orchestration, scheduled jobs, signal monitoring, event detection | 22 |
| Sam | Frontend surfaces (Onboarding, Pulse, Thread, ICE components, design system, prediction logger) | 25 |
| Riley | DB schema/RLS, editorial tooling, compliance (SEBI, MMJ, bias log, track record), Factor DB Banking seed, CI/infra, tester launch kit | 26 |

---

## Phase 1: Foundation

_Stand up the foundation surfaces (Pulse + Thread + Onboarding), the LLM card pipeline, event detection, Banking sector Factor DB, and track-record logging from Day 1._ · **Duration estimate:** 12 weeks (3 months).

### Story P1-S1 — Project bootstrap, Supabase, deploys, CI

- **Assigned:** Riley
- **Points:** 4
- **Layers:** Infra, DB, CI
- **Depends on:** _None_
- **Parallel with:** _None_

**User story**

> As the team, I want a working monorepo wired to Supabase, Vercel, Render, and GitHub Actions with a single `.env.local`, so that every later story can ship behind a green build.

**Acceptance criteria**

- [x] Repo contains `frontend/` (Next.js + Tailwind) and `backend/` (FastAPI), with shared `docs/` and `scripts/`.
- [x] Supabase project provisioned (dev) — URL + anon key stored only in `.env.local`.
- [x] Vercel auto-deploys `frontend/` from `main`; Render auto-deploys `backend/` from `main`.
- [x] GitHub Actions runs lint + type-check + unit tests for both apps on every PR.
- [x] `GET /health` on the backend returns `200 {"status":"ok"}` from both local dev and Render.
- [x] One `.env.local` at repo root only — no `.env`, no `.env.example` duplicates.

**Tech notes**

- Use `pnpm` workspaces or simple folder split. Tailwind config seeded with PRD §8 colour tokens.
- Python 3.11+, FastAPI, `uvicorn`, `httpx`, `pydantic v2`, `python-dotenv` pointing at `../.env.local`.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `package.json` (workspace root) | create | Workspace + script aliases |
| `frontend/package.json` | create | Next.js app |
| `frontend/tailwind.config.ts` | create | Seed PRD colour + font tokens |
| `frontend/app/page.tsx` | create | Landing redirect to onboarding |
| `backend/pyproject.toml` | create | FastAPI deps + pytest |
| `backend/app/main.py` | create | FastAPI entrypoint + `/health` |
| `backend/app/core/settings.py` | create | Load secrets from `../.env.local` |
| `backend/tests/test_health.py` | create | Pytest for `/health` |
| `.env.local` | create | Single source of secrets (gitignored) |
| `.github/workflows/ci.yml` | create | Lint + test + type-check matrix |
| `vercel.json` / `render.yaml` | create | Deploy targets |

#### Tasks (checkboxes)

- [x] **1.0** Project bootstrap, Supabase, deploys, CI
  - [x] **1.1** Init monorepo with `frontend/` (Next.js 14 + TS + Tailwind) and `backend/` (FastAPI).
  - [x] **1.2** Create single `.env.local` with placeholders: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `CLAUDE_API_KEY`, `NEWSAPI_KEY`. Add to `.gitignore` (already present).
  - [x] **1.3** Provision Supabase project (dev). Capture URL + keys into `.env.local` only.
  - [x] **1.4** Add `backend/app/main.py` with `GET /health` and CORS for the Vercel preview domain pattern.
  - [x] **1.5** Wire Tailwind config to PRD §8.3 colour palette (slate, blue, green, amber, red, surface).
  - [x] **1.6** Set up Vercel project → deploy `frontend/`. Set up Render service → deploy `backend/`.
  - [x] **1.7** GitHub Actions workflow: `frontend` job (`pnpm lint && pnpm typecheck && pnpm test && pnpm build`) and `backend` job (`ruff check . && pytest -q`).
  - [x] **1.8** Test: `pytest backend/tests/test_health.py` passes locally and in CI; `pnpm test` in frontend runs a smoke Jest test for `app/page.tsx`.

---

### Story P1-S2 — Onboarding three-question flow + mode detection

- **Assigned:** Sam
- **Points:** 5
- **Layers:** DB, API, UI
- **Depends on:** P1-S1 — UI can be built against mocked API (no auth gate required for Phase 1)
- **Parallel with:** P1-S3, P1-S5

**User story**

> As a first-time visitor, I want to answer three plain-English questions about my investment status, amount, and horizon, so that FinnWise routes me to the right starting surface (The Pulse or The Map) with my mode visibly explained. 

**Acceptance criteria**

- [x] Split-screen layout on desktop (420px brand panel + right onboarding panel). Mobile hides brand panel (PRD §5 Screen 1).
- [x] Three progress dots, never a percentage bar. Active dot blue (#1A4FCC), 1.2× scale.
- [x] Step 1: three full-width option buttons. Step 2: free-text amount with `₹` prefix + Monthly/One-time segment. Step 3: 2×2 horizon grid.
- [x] Step 4 reveals detected mode (Portfolio Builder / Protector / Curious) with one-sentence rationale + four-surface preview + CTA "Enter FinnWise →".
- [x] Persistent red SEBI footer present on every step (PRD §8.6) — never a popup, never dismissable.
- [x] No financial data persisted beyond session — mode + horizon are server-stored, amount is **session-only** (PRD §11.1).
- [x] Portfolio Builder routes to `/map`; Portfolio Protector and Curious route to `/pulse`.

**Reference screen**

- Filename : C:\Projects\InvestmentAssistant\Page Designs\finnwise_onboarding_screen.html

**Tech notes**

- DB: `session_profiles(session_id PK, user_id FK, mode, status, horizon, cadence, created_at)` — no amount column.
- API: `POST /onboarding/session` → returns `{mode, starting_surface, rationale}`.
- UI: typed state machine; no external form library — keep deps minimal.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/onboarding/page.tsx` | create | Page shell + step orchestrator |
| `frontend/app/onboarding/_components/BrandPanel.tsx` | create | Left brand panel |
| `frontend/app/onboarding/_components/ProgressDots.tsx` | create | Three-dot indicator |
| `frontend/app/onboarding/_components/Step1Status.tsx` | create | Investment status options |
| `frontend/app/onboarding/_components/Step2Amount.tsx` | create | Amount + cadence toggle |
| `frontend/app/onboarding/_components/Step3Horizon.tsx` | create | 2×2 horizon grid |
| `frontend/app/onboarding/_components/Step4ModeResult.tsx` | create | Mode reveal + CTA |
| `frontend/components/SebiFooter.tsx` | create | Reusable persistent disclaimer footer |
| `frontend/lib/onboarding/state.ts` | create | Typed reducer for the 4-step flow |
| `frontend/lib/onboarding/state.test.ts` | create | Reducer unit tests |
| `frontend/app/onboarding/_components/Step1Status.test.tsx` | create | RTL snapshot + interaction tests |
| `backend/app/api/onboarding.py` | create | `POST /onboarding/session` route |
| `backend/app/services/mode_detection.py` | create | Pure function mapping inputs → mode |
| `backend/tests/test_mode_detection.py` | create | Pytest covering all 9 input combos |
| `backend/db/migrations/0002_session_profiles.sql` | create | Supabase migration |

#### Tasks (checkboxes)

- [x] **2.0** Onboarding three-question flow + mode detection
  - [x] **2.1** Migration: `session_profiles` table + RLS (user can only read/write own row).
  - [x] **2.2** Implement `mode_detection.detect_mode(status, horizon)` as a pure function — table of 9 cases.
  - [x] **2.3** `POST /onboarding/session` route, Pydantic request/response, never accepts or stores the amount value (passed back as echo for client only).
  - [x] **2.4** Build `BrandPanel`, `ProgressDots`, persistent `SebiFooter` components from PRD §5 Screen 1 spec.
  - [x] **2.5** Build `Step1Status` with three radio-style option buttons + selected state (blue border 1.5px, `#EEF3FF` bg).
  - [x] **2.6** Build `Step2Amount` — `₹` prefix box, free-text input (numeric mask only), Monthly/One-time two-segment toggle.
  - [x] **2.7** Build `Step3Horizon` 2×2 grid (Under 1y / 1–3y / 3–7y / 7+y).
  - [x] **2.8** Build `Step4ModeResult` — read mode from API response, render Playfair Display 20px headline, four-surface preview, CTA.
  - [x] **2.9** Loading + error states on Step 4 submit (skeleton dots while POST in flight; inline error block on failure).
  - [x] **2.10** Route after CTA: Builder → `/map`, Protector/Curious → `/pulse`.
  - [x] **2.11** Test: Jest reducer test for all transitions; RTL test for Step1 selection; Pytest test covering all 9 mode-detection inputs.

---

### Story P1-S3 — Supabase session + user chip (route gating deferred)

- **Assigned:** Jordan
- **Points:** 4
- **Layers:** DB, API, UI
- **Depends on:** P1-S1
- **Parallel with:** P1-S2, P1-S4, P1-S5

**User story**

> As a developer or early user, I want Supabase session support and a visible identity chip when signed in, without route-level auth blocking Phase 1 surfaces.

**Acceptance criteria**

- [x] Supabase magic-link auth wired end-to-end; callback page exchanges token and creates a session cookie (when email delivery works).
- [ ] **Phase 1:** Routes under `/(app)/*` and onboarding exits are **not** gated — no redirect to `/sign-in` for anonymous visitors. Re-introduce guards before public beta / wider testing.
- [x] User chip (PRD §8.4) appears at bottom of sidebar: 28px blue avatar circle + initials + name + DM Mono sub-label; placeholders when no session.
- [x] Sign-out clears session + redirects to public landing.

**Tech notes**

- Server components use `@supabase/ssr`. Backend `get_current_user` exists for future protected APIs; Phase 1 frontend does not use JWT gates for page access.
- `GET /api/protected/me` returns an anonymous-shaped payload when there is no session (no `401` in Phase 1).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(auth)/sign-in/page.tsx` | create | Email entry for magic link (optional manual flow) |
| `frontend/app/(auth)/callback/route.ts` | create | Token exchange route handler |
| `frontend/middleware.ts` | create | Session refresh only — **no** auth redirect in Phase 1 |
| `frontend/components/Sidebar/UserChip.tsx` | create | Bottom-of-sidebar identity chip |
| `frontend/lib/supabase/client.ts` | create | Singleton browser client |
| `frontend/lib/supabase/server.ts` | create | Server-side client (RSC + route handlers) |
| `backend/app/core/auth.py` | create | `get_current_user` FastAPI dependency |
| `backend/tests/test_auth_dependency.py` | create | Pytest covering valid/invalid JWT |
| `frontend/components/Sidebar/UserChip.test.tsx` | create | RTL test |

#### Tasks (checkboxes)

- [ ] **3.0** Supabase session + user chip (route gating deferred)
  - [x] **3.1** Configure Supabase Auth in dashboard — magic-link only, no password.
  - [x] **3.2** `sign-in/page.tsx` — single email input + "Send link" button, success/error inline states.
  - [x] **3.3** `/callback` route handler exchanges code and writes session cookie.
  - [ ] **3.4** `middleware.ts` — refresh Supabase session cookies on matched routes; **do not** bounce unauthenticated users to `/sign-in` during Phase 1.
  - [x] **3.5** Backend `get_current_user` FastAPI dependency — verifies Supabase JWT, returns `User` model.
  - [x] **3.6** `UserChip` component reading from session; rendered in the sidebar slot.
  - [x] **3.7** Sign-out action + button in user chip menu.
  - [x] **3.8** Test: Pytest for `get_current_user` (valid + invalid JWT); RTL test for `UserChip` rendering name/initials; smoke E2E (Playwright optional, Jest mock acceptable for V1).

---

### Story P1-S4 — Core DB schema + append-only track record + SEBI footer

- **Assigned:** Riley
- **Points:** 5
- **Layers:** DB, API, UI
- **Depends on:** P1-S1
- **Parallel with:** P1-S2, P1-S3, P1-S5

**User story**

> As the platform, I want the core analytical tables (events, signals, instrument_assessments, user_predictions, track_record) created with the append-only track_record enforced at the database level, so that no future story can quietly mutate the record of what was said when.

**Acceptance criteria**

- [x] Tables created per PRD §7.2: `events`, `signals`, `instrument_assessments`, `user_predictions`, `track_record`.
- [x] `track_record` enforces append-only via RLS + revoked UPDATE/DELETE for all roles (incl. service role policy denies UPDATE/DELETE). PRD §6.4 + §11.1.
- [x] Pytest integration test attempts UPDATE and DELETE on `track_record` and both fail.
- [x] `SebiFooter` component reused on Pulse, Thread (later stories) — exported from `components/SebiFooter.tsx` and present on every page that shows instrument-specific analysis.
- [x] All `MEASURED | MODELLED | JUDGED` enums declared at DB level as a Postgres `mmj_type`.
- [x] All `lifecycle_state` declared as Postgres enum matching the 8 PRD states (draft → archived).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/0003_core_tables.sql` | create | events / signals / instrument_assessments / user_predictions / track_record |
| `backend/db/migrations/0004_track_record_append_only.sql` | create | RLS + revokes enforcing append-only |
| `backend/db/migrations/0005_enums.sql` | create | `mmj_type`, `lifecycle_state`, `signal_state` |
| `backend/app/models/*.py` | create | Pydantic + SQLAlchemy models matching schema |
| `backend/tests/test_track_record_append_only.py` | create | Asserts UPDATE/DELETE rejected |
| `backend/tests/test_enums.py` | create | Asserts enum values match PRD |
| `frontend/components/SebiFooter.tsx` | modify | Confirm component meets spec; export from index |

#### Tasks (checkboxes)

- [x] **4.0** Core DB schema + append-only track record + SEBI footer
  - [x] **4.1** Migration: `enums.sql` for `mmj_type`, `lifecycle_state` (8 states), `signal_state` (pending/triggered/resolved), `event_category`.
  - [x] **4.2** Migration: `events` table — id, title, category, source_url, confidence_score, lifecycle_state, prompt_version, created_at.
  - [x] **4.3** Migration: `signals` table — id, card_id, signal_text, state, triggered_at.
  - [x] **4.4** Migration: `instrument_assessments` — id, card_id, version, instrument_id, signal_type, reasoning, entry_conditions[], exit_conditions[].
  - [x] **4.5** Migration: `user_predictions` — id, user_id, card_id, prediction_text, logged_at, mechanism_accuracy, business_accuracy, market_accuracy.
  - [x] **4.6** Migration: `track_record` — id, card_id, payload jsonb, logged_at — **no updated_at**. RLS denies UPDATE+DELETE for all roles.
  - [x] **4.7** Backend Pydantic + SQLAlchemy/asyncpg models matching the schema.
  - [x] **4.8** Confirm `SebiFooter` (from S2) implements PRD §8.6 spec; verify on every protected-app shell page.
  - [x] **4.9** Test: Pytest integration test that attempts UPDATE and DELETE on `track_record` — both must fail with permission error.

---

### Story P1-S5 — Factor Exposure DB — Banking sector slice + admin viewer

- **Assigned:** Riley
- **Points:** 5
- **Layers:** DB, API, UI (internal)
- **Depends on:** P1-S1, P1-S4
- **Parallel with:** P1-S2, P1-S3, P1-S6

**User story**

> As the Product Owner, I want the Banking & Financial Services sector loaded into the Factor Exposure Database with 8-factor sensitivities and an internal viewer, so that the LLM pipeline has a real grounding dataset to query for its first cards.

**Acceptance criteria**

- [ ] Tables: `sectors`, `instruments`, `factors` (the 8 from PRD §7.1), `instrument_factor_sensitivity(instrument_id, factor_id, sensitivity, mmj_tag, source_url, retrieved_at)`.
- [ ] Banking sector seeded with at least 15 NSE-listed banks, each tagged across all 8 factors.
- [ ] Every sensitivity row carries an MMJ tag (PRD §6.2) and source URL — rows without an MMJ tag fail check constraint.
- [ ] Internal `/admin/factor-db` page (gated to Product Owner email allow-list) renders the matrix with filter by sector and factor.
- [ ] `GET /api/factor-db/sensitivity?instrument=...&factor=...` returns the row with freshness metadata.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/0006_factor_db.sql` | create | Schema for sectors/instruments/factors/sensitivities |
| `backend/db/seeds/banking_sector.sql` | create | Banking seed (≥15 NSE banks × 8 factors) |
| `backend/app/api/factor_db.py` | create | Query endpoint |
| `backend/app/services/factor_db.py` | create | Sensitivity lookup service |
| `backend/tests/test_factor_db_seed.py` | create | Asserts seed completeness + MMJ tag on every row |
| `frontend/app/admin/factor-db/page.tsx` | create | Internal matrix viewer |
| `frontend/app/admin/factor-db/_components/FactorMatrix.tsx` | create | Grid component |
| `frontend/app/admin/factor-db/page.test.tsx` | create | RTL render test |

#### Tasks (checkboxes)

- [ ] **5.0** Factor Exposure DB — Banking sector slice + admin viewer
  - [ ] **5.1** Migration: factor-DB tables + check constraint `mmj_tag IN ('MEASURED','MODELLED','JUDGED')` and `NOT NULL` on `source_url`.
  - [ ] **5.2** Seed: 8 factors from PRD §7.1 with descriptions.
  - [ ] **5.3** Seed: Banking sector with ≥15 instruments (top NSE banks) — capture ticker, ISIN, exchange.
  - [ ] **5.4** Manually research and load sensitivities (Product Owner task; engineer scripts the CSV→SQL loader).
  - [ ] **5.5** `factor_db.lookup(instrument, factor)` service function with freshness flag (green / amber / red per PRD §8.6).
  - [ ] **5.6** `GET /api/factor-db/sensitivity` route, requires auth; admin-only `GET /api/factor-db/matrix?sector=`.
  - [ ] **5.7** Internal `FactorMatrix` UI — sticky first column (instruments), 8 factor columns, MMJ-coloured dots per cell.
  - [ ] **5.8** Admin allow-list check on the page (server component returns 403 if email not on list).
  - [ ] **5.9** Test: Pytest seed integrity (every row has MMJ + source + 8/8 factors covered); RTL render test for `FactorMatrix`.

---

### Story P1-S6 — Event-detection scheduled job + editorial queue

- **Assigned:** Jordan
- **Points:** 5
- **Layers:** API, DB, UI (internal), Scheduler
- **Depends on:** P1-S1, P1-S4
- **Parallel with:** P1-S5, P1-S2

**User story**

> As the editorial pipeline, I want a 4-hourly Python job that watches NewsAPI + RBI RSS + an NSE/BSE announcements feed and pushes detected events with a confidence score into an editorial queue, so that the Product Owner can triage what becomes a card.

**Acceptance criteria**

- [ ] Scheduled job runs every 4 hours on Render (cron) and on demand via `python -m app.jobs.event_detection`.
- [ ] Each polled source has a typed adapter behind a `SourceAdapter` interface; adding a new source is one new class.
- [ ] Each detected event lands in `events` table with `lifecycle_state='draft'` and a 0–100 confidence score.
- [ ] Editorial queue UI `/admin/queue` lists draft events sorted by confidence desc with filters by category + source.
- [ ] Daily call quota guard: NewsAPI usage stays under the 100-calls/day free-tier limit (PRD §7.3).
- [ ] Job is idempotent — re-running on the same window does not create duplicate event rows (dedupe by source + canonical URL).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/jobs/event_detection.py` | create | Entrypoint + scheduler hook |
| `backend/app/sources/base.py` | create | `SourceAdapter` ABC |
| `backend/app/sources/newsapi.py` | create | NewsAPI adapter |
| `backend/app/sources/rbi_rss.py` | create | RBI RSS adapter |
| `backend/app/sources/nse_announcements.py` | create | NSE/BSE adapter (with abstraction for fallback) |
| `backend/app/services/event_confidence.py` | create | Heuristic + LLM-light confidence scorer |
| `backend/app/api/admin_queue.py` | create | List + filter draft events |
| `backend/tests/test_event_detection_idempotent.py` | create | Re-run yields zero new rows |
| `backend/tests/test_source_adapters.py` | create | Fixtures per source |
| `frontend/app/admin/queue/page.tsx` | create | Editorial queue UI |
| `render.yaml` | create | Render deployment config with web service and cron jobs |

#### Tasks (checkboxes)

- [ ] **6.0** Event-detection scheduled job + editorial queue
  - [ ] **6.1** `SourceAdapter` ABC: `fetch(window: timedelta) -> list[RawEvent]` + canonical URL helper.
  - [ ] **6.2** NewsAPI adapter — query for India-market keywords; respect daily call ceiling with a Redis-less in-DB call counter.
  - [ ] **6.3** RBI RSS adapter using `feedparser`.
  - [ ] **6.4** NSE announcements adapter — wrap public CSV/HTML scrape with a `SourceFailure` exception path (fallback to last-good-state per PRD §7.3 risk note).
  - [ ] **6.5** `event_confidence.score(raw_event)` — combines keyword heuristics + source priority (RBI > Exchange > News). 0–100.
  - [ ] **6.6** Dedupe + persist: hash on `(source, canonical_url)` unique constraint; upsert path is no-op.
  - [ ] **6.7** Render cron job: every 4 hours; emits structured logs.
  - [ ] **6.8** Admin queue route + Next.js page listing drafts (table view) with filter pills.
  - [ ] **6.9** Test: idempotency test (run twice → zero new rows); per-source unit test with HTTP fixtures.

---

### Story P1-S7 — LLM 3-call card-synthesis pipeline (Claude Sonnet)

- **Assigned:** Jordan
- **Points:** 7
- **Layers:** API, DB, Services
- **Depends on:** P1-S4 (schema), P1-S5 (Factor DB lookup), P1-S6 (events queue)
- **Parallel with:** P1-S9, P1-S10 (UI surfaces can build against mocked card JSON)

**User story**

> As the editorial pipeline, I want to turn a queued event into a structurally complete Event Intelligence Card via three separate, version-controlled Claude Sonnet calls (Synthesis / Dissent / Framework), so that every card carries an Insight, a Context causal chain, a dissenting view, and a Framework Behind This — with every number traceable to the Evidence layer.

**Acceptance criteria**

- [ ] Three prompt templates checked into `prompts/` with semantic versions in their filename or front-matter. Cards persist `prompt_version` per PRD §6.3.
- [ ] LLM never generates or fabricates numbers — synthesis-call output is parsed, and any number not present in the Evidence layer fails validation and rejects the draft (PRD §6.3 constraint).
- [ ] Every quantitative claim carries an MMJ tag, enforced by post-generation validator.
- [ ] Dissenting view is a **separate** call — pipeline fails the draft if dissent payload is empty or generic (PRD §6.3 Role 2).
- [ ] Framework Behind This is generated last and stored with the card.
- [ ] Per-card LLM cost recorded; daily cap of 50 cards enforced (PRD §12 risk 7).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/prompts/synthesis.v1.md` | create | Prompt template — Role 1 |
| `backend/prompts/dissent.v1.md` | create | Prompt template — Role 2 |
| `backend/prompts/framework.v1.md` | create | Prompt template — Role 3 |
| `backend/app/services/llm_client.py` | create | Thin Anthropic Sonnet client w/ retries |
| `backend/app/services/card_pipeline.py` | create | Orchestrates 3 calls + validation |
| `backend/app/services/number_validator.py` | create | Rejects numbers absent from Evidence layer |
| `backend/app/services/mmj_validator.py` | create | Asserts every quantitative claim has an MMJ tag |
| `backend/app/services/cost_guard.py` | create | Daily 50-card cap + cost log |
| `backend/app/api/cards.py` | create | `POST /api/cards/draft-from-event` |
| `backend/tests/test_card_pipeline.py` | create | End-to-end with mocked LLM responses |
| `backend/tests/test_number_validator.py` | create | Asserts hallucinated numbers rejected |
| `backend/tests/test_mmj_validator.py` | create | Asserts missing MMJ tags rejected |

#### Tasks (checkboxes)

- [ ] **7.0** LLM 3-call card-synthesis pipeline (Claude Sonnet)
  - [ ] **7.1** Author `synthesis.v1.md` with explicit instruction: "Use only numbers found in the Evidence inputs; every quantitative claim must end with `[MEASURED]`, `[MODELLED]`, or `[JUDGED]` tags."
  - [ ] **7.2** Author `dissent.v1.md` — must produce a specific mechanism, not a generic disclaimer (cite PRD §5 Screen 3 language rule).
  - [ ] **7.3** Author `framework.v1.md` — must name the transferable pattern.
  - [ ] **7.4** `llm_client.complete(prompt, version, vars)` — wraps Anthropic SDK with retry/backoff, logs prompt version + token counts.
  - [ ] **7.5** `card_pipeline.draft_card(event_id)` — pull event + Factor DB sensitivities + macro signals, call synthesis, validate numbers + MMJ, call dissent, call framework, persist draft card + signals + instrument assessments.
  - [ ] **7.6** `number_validator` parses numbers from Insight/Context layers and asserts each appears in the Evidence layer payload.
  - [ ] **7.7** `mmj_validator` parses every quantitative claim and asserts presence of an MMJ token.
  - [ ] **7.8** `cost_guard.check_and_record()` — abort pipeline if today's count ≥ 50.
  - [ ] **7.9** `POST /api/cards/draft-from-event` accepts `event_id`, runs pipeline, returns draft card id or structured error.
  - [ ] **7.10** Test: pipeline test with mocked Anthropic responses; validator tests covering hallucinated numbers and missing MMJ tags.

---

### Story P1-S8 — Editorial review interface for drafts

- **Assigned:** Riley
- **Points:** 5
- **Layers:** UI (internal), API
- **Depends on:** P1-S7
- **Parallel with:** P1-S9, P1-S10

**User story**

> As the Product Owner, I want an internal screen to review a draft ICE card against the non-expert checklist and either approve-and-publish or send back for regeneration, in under 45 minutes per card (PRD §13 metric).

**Acceptance criteria**

- [ ] `/admin/review/[draft_id]` shows the full draft card in the same shell as The Thread (read-mostly) with an editorial sidecar.
- [ ] Non-expert checklist (5 items per PRD §6.1) — all must be ticked before Publish enables.
- [ ] Publish writes `lifecycle_state='published'`, inserts initial `track_record` row (immutable), and notifies in-app any user whose profile matches the card's category.
- [ ] Send-back path triggers regeneration with optional editor notes injected into the synthesis prompt.
- [ ] Editor time-per-card auto-logged on publish.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/admin/review/[draftId]/page.tsx` | create | Editorial review page |
| `frontend/app/admin/review/_components/ChecklistPanel.tsx` | create | 5-item checklist + publish gate |
| `backend/app/api/admin_review.py` | create | `POST /api/admin/cards/{id}/publish` + `/regenerate` |
| `backend/app/services/publish_card.py` | create | Publish workflow + track-record insert |
| `backend/app/services/regenerate_card.py` | create | Re-run pipeline with editor notes |
| `backend/tests/test_publish_writes_track_record.py` | create | Asserts immutable record |
| `frontend/app/admin/review/_components/ChecklistPanel.test.tsx` | create | Publish disabled until all 5 ticked |

#### Tasks (checkboxes)

- [ ] **8.0** Editorial review interface for drafts
  - [ ] **8.1** Page shell reusing Thread components in read-only mode (lifts S10 components — coordinate import order).
  - [ ] **8.2** `ChecklistPanel` — 5 items from PRD §6.1 ("all numbers source-tagged", "dissenting view present", "confidence consistent with freshness", "language non-expert accessible", "no buy/sell/hold language").
  - [ ] **8.3** `POST /publish` writes `lifecycle_state='published'`, inserts append-only `track_record` row, fires in-app notify.
  - [ ] **8.4** `POST /regenerate` re-invokes `card_pipeline.draft_card` with `editor_notes` field appended to synthesis vars.
  - [ ] **8.5** Editor-time log: capture time-on-page from open to publish (no PII), surface in admin metrics later.
  - [ ] **8.6** Test: Pytest asserting publish creates exactly one `track_record` row and the card transitions to `published`; RTL test asserting Publish button disabled until 5/5 checked.

---

### Story P1-S9 — The Pulse — feed, filters, live insight panel, Fog of War

- **Assigned:** Sam
- **Points:** 7
- **Layers:** UI, API
- **Depends on:** P1-S3 (app shell + session), P1-S4 (schema), P1-S7 (cards exist)
- **Parallel with:** P1-S8, P1-S10 (different surfaces; can develop in parallel with mocked card JSON)

**User story**

> As a Portfolio Protector / Curious user, I want a feed of recent Event Intelligence Cards filtered by my profile with a live insight panel that updates as I scroll, so that I can quickly browse financial implications without page navigation.

**Acceptance criteria**

- [ ] Left sidebar (220px) per PRD §8.4 with 5 nav items; Phase 2 items (Mirror, Lens) show grey badge.
- [ ] Two-column layout: feed (~60%) + sticky insight panel (~40%) per PRD §5 Screen 2.
- [ ] Category filter pills in the topbar (not in the feed column). Active pill = navy bg, white text.
- [ ] Event card: financial-consequence headline in Playfair 15px, event context italic, separate direction + magnitude confidence dots (never combined — PRD §8.6).
- [ ] Selecting a card updates the right insight panel **without** route navigation; selected card shows 3px blue left border.
- [ ] Fog of War banner appears when ≥3 major events are simultaneously active (PRD §5 Screen 2).
- [ ] Resolved cards remain in the feed with green "Resolved" pill (PRD design rule — no survivorship bias).
- [ ] Single-column on mobile; insight panel hidden, tap-through to Thread.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/layout.tsx` | create | App shell with sidebar |
| `frontend/components/Sidebar/Sidebar.tsx` | create | 220px sidebar per §8.4 |
| `frontend/app/(app)/pulse/page.tsx` | create | Pulse page (server component) |
| `frontend/app/(app)/pulse/_components/Topbar.tsx` | create | Topbar with filter pills |
| `frontend/app/(app)/pulse/_components/FilterPills.tsx` | create | Category pills |
| `frontend/app/(app)/pulse/_components/FogOfWarBanner.tsx` | create | Conditional amber banner |
| `frontend/app/(app)/pulse/_components/EventCard.tsx` | create | Feed card |
| `frontend/app/(app)/pulse/_components/InsightPanel.tsx` | create | Sticky right panel |
| `frontend/lib/cards/usePulseFeed.ts` | create | Client hook for feed + selection state |
| `backend/app/api/feed.py` | create | `GET /api/feed?category=&horizon=` |
| `backend/app/services/feed.py` | create | Profile-aware filter + Fog of War detector |
| `backend/tests/test_feed_filtering.py` | create | Asserts profile + category filters |
| `backend/tests/test_fog_of_war_detector.py` | create | Asserts banner triggers at ≥3 active majors |
| `frontend/app/(app)/pulse/_components/EventCard.test.tsx` | create | RTL test |

#### Tasks (checkboxes)

- [ ] **9.0** The Pulse — feed, filters, live insight panel, Fog of War
  - [ ] **9.1** Implement `Sidebar` strictly to PRD §8.4 spec (widths, paddings, active state colours, Phase 2 badge).
  - [ ] **9.2** `(app)/layout.tsx` wraps Sidebar + Topbar slot + main + SEBI footer.
  - [ ] **9.3** `GET /api/feed` accepts category + horizon, joins on user profile, returns published+resolved cards.
  - [ ] **9.4** `services/feed.detect_fog_of_war()` — true when ≥3 cards have `lifecycle_state in (active, signal_triggered)` and category overlap.
  - [ ] **9.5** `EventCard` — Playfair 15px headline, italic context, category tag, two confidence dots, instrument chips.
  - [ ] **9.6** `InsightPanel` — sticky, updates via shared selection state hook; shows confidence trio + 4 instrument mini cards + "Read full analysis in The Thread →".
  - [ ] **9.7** `FilterPills` in Topbar — multi-select pills, "All" reset, persist in URL search params.
  - [ ] **9.8** `FogOfWarBanner` rendered above feed when API flag is true.
  - [ ] **9.9** Resolved badge inline on event card (green pill) — do not filter out resolved cards.
  - [ ] **9.10** Mobile: hide insight panel, tap card → `/thread/[id]`.
  - [ ] **9.11** Loading skeletons + empty state ("No events match your filters") + error retry.
  - [ ] **9.12** Test: API filter tests; Fog of War threshold test; RTL test asserting two separate confidence dots and resolved cards stay in list.

---

### Story P1-S10 — The Thread — Living Card with ICE tabs + aside

- **Assigned:** Sam
- **Points:** 8
- **Layers:** UI, API
- **Depends on:** P1-S7 (card data), P1-S4 (schema)
- **Parallel with:** P1-S8, P1-S9

**User story**

> As any user, I want to open a full Event Intelligence Card with the ICE three-layer architecture, lifecycle tracker, signals to watch, bias flags, confidence composition, dissenting view, and Original/Current toggle, so that I can choose how deep I read and trust the evidence trail.

**Acceptance criteria**

- [ ] Route `/thread/[cardId]` with breadcrumb + lifecycle badge (pulsing for Active) + Current/Original toggle (PRD §5 Screen 3).
- [ ] ICE tabs: I always visible, C requires one tap, E requires second tap.
- [ ] Instrument Assessment Card with signal pill (`opportunity signal` / `headwind signal` / `watch`) + reasoning + Entry/Exit conditions in two-column grid (green / amber backgrounds). **No price targets anywhere.**
- [ ] C tab: numbered causal chain with MMJ badge inline per step.
- [ ] E tab: source table with freshness dot (green ≤6m / amber 6–18m / red >18m).
- [ ] Aside: 7-step Lifecycle tracker, Signals to Watch with consequence map, Confidence Composition segmented bar, Bias Flags.
- [ ] Dissenting View block on every card — amber-tinted, separately styled.
- [ ] Prediction Logger appears **before** the Context tab is revealed, with 4 discrete prediction options.
- [ ] Current/Original toggle — Original View is read from the immutable `track_record` row.
- [ ] All language rules from PRD §5 Screen 3 enforced — automated lint check on copy in test.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `frontend/app/(app)/thread/[cardId]/page.tsx` | create | Thread page |
| `frontend/app/(app)/thread/_components/IceTabs.tsx` | create | I / C / E tab control |
| `frontend/app/(app)/thread/_components/InsightLayer.tsx` | create | I layer |
| `frontend/app/(app)/thread/_components/ContextLayer.tsx` | create | C layer |
| `frontend/app/(app)/thread/_components/EvidenceLayer.tsx` | create | E layer + freshness dots |
| `frontend/app/(app)/thread/_components/InstrumentCard.tsx` | create | Instrument assessment |
| `frontend/app/(app)/thread/_components/DissentingView.tsx` | create | Amber block |
| `frontend/app/(app)/thread/_components/PredictionLogger.tsx` | create | 4-option logger |
| `frontend/app/(app)/thread/_components/FrameworkBehindThis.tsx` | create | Dark gradient framework block |
| `frontend/app/(app)/thread/_components/aside/LifecycleTracker.tsx` | create | 7-step vertical |
| `frontend/app/(app)/thread/_components/aside/SignalsToWatch.tsx` | create | Signals + consequence map |
| `frontend/app/(app)/thread/_components/aside/ConfidenceComposition.tsx` | create | MMJ bar |
| `frontend/app/(app)/thread/_components/aside/BiasFlags.tsx` | create | Bias panel |
| `frontend/app/(app)/thread/_components/CurrentOriginalToggle.tsx` | create | View toggle |
| `frontend/lib/cards/useCard.ts` | create | Fetcher hook (current + original) |
| `backend/app/api/cards_detail.py` | create | `GET /api/cards/{id}?view=current|original` |
| `backend/tests/test_card_detail_original_immutable.py` | create | Original view returns track_record snapshot |
| `frontend/app/(app)/thread/_components/InstrumentCard.test.tsx` | create | Asserts no buy/sell/hold copy + no `₹` price targets |
| `frontend/app/(app)/thread/_components/DissentingView.test.tsx` | create | Required on every card |

#### Tasks (checkboxes)

- [ ] **10.0** The Thread — Living Card with ICE tabs + aside
  - [ ] **10.1** Page shell with breadcrumb + lifecycle badge + Current/Original toggle.
  - [ ] **10.2** `IceTabs` — I active by default; C and E gated behind tap (no URL change required, but URL hash optional for shareability).
  - [ ] **10.3** `InsightLayer` — summary paragraphs + InstrumentCards + DissentingView + PredictionLogger + FrameworkBehindThis.
  - [ ] **10.4** `InstrumentCard` — signal pill (only the three allowed values), Entry/Exit two-column grid, conditions = world facts only.
  - [ ] **10.5** `ContextLayer` — numbered steps with navy circle, MMJ badge inline.
  - [ ] **10.6** `EvidenceLayer` — table with freshness dot computed from `retrieved_at`; LLM never appears in this table.
  - [ ] **10.7** Aside: `LifecycleTracker` with 7 steps + pulsing dot animation (1.5s ease-in-out per §8.6).
  - [ ] **10.8** Aside: `SignalsToWatch` — Pending/Triggered/Resolved dot states; clicking signal expands consequence map.
  - [ ] **10.9** Aside: `ConfidenceComposition` segmented bar (M/M/J proportions).
  - [ ] **10.10** Aside: `BiasFlags` reading from card's `bias_audit` payload (placeholder until P1-S13 fills it).
  - [ ] **10.11** `PredictionLogger` — 4 discrete options, "Log my prediction →" calls `POST /api/predictions`; appears before C tab is revealed.
  - [ ] **10.12** `CurrentOriginalToggle` — Original View hits `?view=original`; backend returns the immutable `track_record` snapshot for Day 1.
  - [ ] **10.13** Test: RTL asserting InstrumentCard has no `buy|sell|hold|₹\d` substrings; DissentingView is required to render; original-view backend test asserting immutability.

---

### Story P1-S11 — Signal monitoring + confidence-gated detection + in-app notifications

- **Assigned:** Jordan
- **Points:** 6
- **Layers:** Services, API, UI
- **Depends on:** P1-S6 (events), P1-S7 (cards have signals)
- **Parallel with:** P1-S8, P1-S10

**User story**

> As the platform, I want a signal-monitoring service that watches for trigger conditions on every active card and routes events through the High/Medium/Low confidence gate (PRD §6.4), so that auto-updates, editorial-review queue, and digest-only entries are handled correctly without manual polling.

**Acceptance criteria**

- [ ] Background job runs every 30 minutes during market hours; signals are checked against latest market + macro data.
- [ ] High confidence (3+ sources, direct match within 4h): auto-update card, 2-hour editor override window; logs to `track_record`.
- [ ] Medium confidence (1–2 sources, partial match): draft update queued for editor; surfaces in admin queue.
- [ ] Low confidence: logged to internal digest only — no card change.
- [ ] In-app notification badge in topbar when a signal fires on a card the user has predicted on.
- [ ] All gate decisions logged with rationale for later override-rate analysis (PRD §13 metric).

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/jobs/signal_monitor.py` | create | 30-min scheduled job |
| `backend/app/services/signal_check.py` | create | Per-signal evaluator |
| `backend/app/services/confidence_gate.py` | create | High/Medium/Low routing |
| `backend/app/api/notifications.py` | create | `GET /api/notifications` |
| `frontend/components/Topbar/NotificationBadge.tsx` | create | Pulsing badge |
| `backend/tests/test_confidence_gate.py` | create | All three branches |
| `backend/tests/test_signal_monitor_logs_override_decisions.py` | create | Asserts override log written |
| `frontend/components/Topbar/NotificationBadge.test.tsx` | create | RTL test |

#### Tasks (checkboxes)

- [ ] **11.0** Signal monitoring + confidence-gated detection + in-app notifications
  - [ ] **11.1** `signal_check.evaluate(signal)` — returns `triggered|partial|none` + sources list.
  - [ ] **11.2** `confidence_gate.route(result)` — High/Medium/Low decision + reason.
  - [ ] **11.3** High path: write card update + new `track_record` row; open 2-hour override window flag.
  - [ ] **11.4** Medium path: enqueue draft update for `/admin/review`.
  - [ ] **11.5** Low path: write to `digest_log` table — no card mutation.
  - [ ] **11.6** Notification: insert row into `notifications` for any user with a logged prediction on the affected card.
  - [ ] **11.7** Frontend `NotificationBadge` — pulsing blue dot; click navigates to the affected Thread.
  - [ ] **11.8** Scheduled cron entry (every 30 minutes during market hours 9:00–16:00 IST).
  - [ ] **11.9** Test: confidence-gate branches; override-log creation; notification fan-out covers only predicting users.

---

### Story P1-S12 — Prediction logger + user track-record entries

- **Assigned:** Sam (UI), with Riley collab on DB constraints
- **Points:** 5
- **Layers:** UI, API, DB
- **Depends on:** P1-S10 (UI in Thread), P1-S4 (schema)
- **Parallel with:** P1-S11, P1-S13

**User story**

> As a reader, I want to log my prediction on a card before the Context tab is revealed, so that The Mirror (Phase 2) has an honest user-vs-event record to grade later.

**Acceptance criteria**

- [ ] `POST /api/predictions` requires auth, records user_id + card_id + prediction_text + logged_at.
- [ ] One prediction per (user, card) — second attempt returns 409 with the previously logged value.
- [ ] Prediction logger UI only appears when the Context tab has not yet been revealed for this session.
- [ ] After submission, logger collapses to a "Your view logged — reviewed in The Mirror when this resolves." confirmation block.
- [ ] Predictions log to the append-only `track_record` table as well (user-level entries clearly tagged).
- [ ] Disclaimer text exactly matches PRD §5 Screen 3 Prediction Logger spec.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/app/api/predictions.py` | create | `POST /api/predictions` + `GET /api/predictions/me` |
| `backend/app/services/predictions.py` | create | Service writes to both `user_predictions` and `track_record` |
| `backend/db/migrations/0007_user_predictions_unique.sql` | create | Unique (user_id, card_id) |
| `frontend/app/(app)/thread/_components/PredictionLogger.tsx` | modify | Wire to API + collapse state |
| `backend/tests/test_predictions_one_per_user_per_card.py` | create | 409 on duplicate |
| `backend/tests/test_predictions_write_to_track_record.py` | create | Asserts both tables receive a row |
| `frontend/app/(app)/thread/_components/PredictionLogger.test.tsx` | modify | Asserts gating before C tab + disclaimer copy |

#### Tasks (checkboxes)

- [ ] **12.0** Prediction logger + user track-record entries
  - [ ] **12.1** Migration: unique constraint on `user_predictions(user_id, card_id)`.
  - [ ] **12.2** `predictions.log(...)` service writes to `user_predictions` and inserts append-only row in `track_record`.
  - [ ] **12.3** `POST /api/predictions` route + Pydantic schemas; `GET /api/predictions/me` returns the current user's predictions (used by Mirror later).
  - [ ] **12.4** Wire `PredictionLogger.tsx` to the API; on success replace component with confirmation block.
  - [ ] **12.5** Gate: hide logger if Context tab has already been revealed in this card-view session (state in `useCard`).
  - [ ] **12.6** Assert exact disclaimer copy (snapshot test).
  - [ ] **12.7** Test: 409 on duplicate; both tables written; UI gating + disclaimer.

---

### Story P1-S13 — Bias audit log + bias flags rendered in Thread aside

- **Assigned:** Riley
- **Points:** 4
- **Layers:** Services, DB, UI
- **Depends on:** P1-S7 (cards), P1-S10 (aside slot)
- **Parallel with:** P1-S11, P1-S12

**User story**

> As the user reading a card, I want bias flags surfaced in the always-visible aside (PRD §6.5) — not hidden in footnotes — so that I see uncertainty before conclusion.

**Acceptance criteria**

- [ ] Six bias types tracked: recency, sector concentration, narrative, editorial coverage (weekly), survivorship, anchoring.
- [ ] Recency bias flagged when >60% of Evidence sources are from the last 30 days.
- [ ] Sector concentration flagged when 3 consecutive published cards cover the same sector.
- [ ] Narrative bias flagged when direction confidence is high but Evidence layer has fewer than 3 sources.
- [ ] Bias detector runs as a post-generation pipeline step; results persist to `card_bias_flags`.
- [ ] `BiasFlags` aside component renders flagged (amber) and monitored (grey) flags with plain-English descriptions.
- [ ] Weekly editorial-coverage report generated as a markdown export under `gitignore`d `notes/` folder.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `backend/db/migrations/0008_card_bias_flags.sql` | create | Schema for flags |
| `backend/app/services/bias_detector.py` | create | All 6 detectors |
| `backend/app/jobs/weekly_bias_report.py` | create | Weekly editorial-coverage rollup |
| `backend/tests/test_bias_detector.py` | create | One test per detector |
| `frontend/app/(app)/thread/_components/aside/BiasFlags.tsx` | modify | Read real data |
| `frontend/app/(app)/thread/_components/aside/BiasFlags.test.tsx` | modify | Asserts amber/grey treatments |

#### Tasks (checkboxes)

- [ ] **13.0** Bias audit log + bias flags rendered in Thread aside
  - [ ] **13.1** Migration: `card_bias_flags(card_id, bias_type, severity, description, detected_at)`.
  - [ ] **13.2** `bias_detector.detect_all(card_id)` runs after pipeline publish/regenerate.
  - [ ] **13.3** Implement recency / sector-concentration / narrative detectors.
  - [ ] **13.4** Implement survivorship + anchoring detectors (lightweight V1 — anchoring monitored via separate-prompt confirmation only).
  - [ ] **13.5** Weekly cron: emit `notes/bias-report-YYYY-WW.md` editorial-coverage rollup (gitignored).
  - [ ] **13.6** Wire `BiasFlags.tsx` to fetch flags via card detail API and render amber (flagged) vs grey (monitored).
  - [ ] **13.7** Test: per-detector unit tests with fixture cards; UI test for amber/grey states.

---

### Story P1-S14 — Tester launch kit + Phase 1 go/no-go checklist

- **Assigned:** Riley
- **Points:** 3
- **Layers:** Compliance, Ops, UI
- **Depends on:** P1-S2, P1-S9, P1-S10, P1-S11, P1-S12 (everything user-facing)
- **Parallel with:** _None — final gate_

**User story**

> As the Product Owner, I want a signed-tester-briefing flow, an in-app "Phase 1 tester" banner, and a documented go/no-go checklist, so that the 10–15 invitees in Week 11–12 have the right expectations and the compliance posture is defensible.

**Acceptance criteria**

- [ ] Tester briefing PDF + acceptance flow (e-signature surrogate is a checkbox + timestamp + IP for V1).
- [ ] In-app "Phase 1 tester" pill in topbar; cannot be hidden.
- [ ] Phase 1 go/no-go checklist exists in `docs/plans/phase1-go-no-go.md` (gitignored) with all PRD §13 success metrics.
- [ ] First real event card published + first `track_record` row visible in DB.

#### Relevant files

| Path | Type | Purpose |
|------|------|---------|
| `docs/plans/phase1-go-no-go.md` | create | Checklist |
| `notes/tester-briefing.md` | create | Briefing source (gitignored) |
| `frontend/app/(app)/tester-briefing/page.tsx` | create | Acceptance flow |
| `backend/db/migrations/0009_tester_acceptance.sql` | create | `tester_acceptances(user_id, accepted_at, ip)` |
| `backend/app/api/tester_acceptance.py` | create | `POST /api/tester/accept` |
| `frontend/components/Topbar/PhaseBadge.tsx` | create | "Phase 1 tester" pill |
| `backend/tests/test_tester_acceptance_required.py` | create | Blocks access if not accepted |

#### Tasks (checkboxes)

- [ ] **14.0** Tester launch kit + Phase 1 go/no-go checklist
  - [ ] **14.1** Draft `notes/tester-briefing.md` (gitignored): scope, SEBI framing, no real-money decisions, feedback channel.
  - [ ] **14.2** `/tester-briefing` page — read briefing, scroll to confirm, checkbox + Accept button.
  - [ ] **14.3** Migration: `tester_acceptances` + RLS.
  - [ ] **14.4** Middleware: invited users who have not accepted are redirected to `/tester-briefing`.
  - [ ] **14.5** `PhaseBadge` "Phase 1 tester" pill always visible in topbar.
  - [ ] **14.6** Author `docs/plans/phase1-go-no-go.md` covering all PRD §13 metrics + sign-off lines.
  - [ ] **14.7** Test: acceptance-required middleware test.

---

## Risks

- **LLM qualitative drift** (PRD §12 risk 1) — Mitigated by S7 number-validator + mmj-validator + S8 editorial review + version-controlled prompts. Add a sample-of-N spot-check ritual in `docs/plans/phase1-go-no-go.md`.
- **Factor DB sensitivities unvalidated** (PRD §12 risk 2) — Banking-only seed limits blast radius; every cell MMJ-tagged.
- **SEBI line-crossing** (PRD §12 risk 3) — Persistent SEBI footer + signed tester acceptance (S14) + lint test for forbidden language in S10. Legal review still required before any non-tester audience.
- **yfinance / NSE pipeline brittleness** (PRD §12 risk 4) — Source-abstraction in S6 + freshness dots in S10 surface staleness immediately.
- **Editorial review > 45 min/card** (PRD §13 target) — S8 captures time-on-page; first 3 cards inform whether prompts need refactor.
- **LLM cost overruns** (PRD §12 risk 7) — S7 `cost_guard` enforces 50-card/day ceiling.

## Recommendations

- Build S1 → S4 → S5 → S7 on the critical path. S2 + S3 + S9 + S10 are UI-heavy and proceed in parallel against mock data.
- Land Banking Factor DB (S5) by end of Week 5 — it gates the first real card test in S7.
- Run S8 (editorial review) against a synthetic card by Week 8 so the Product Owner can practise the 45-minute cycle before live tester cards.
- Treat S14 not as a sign-off ceremony but as a continuous Week-11/12 ritual — accept the checklist will discover gaps.

---

## How to execute Phase 1

Suggested order (12 weeks, solo + AI agents per PRD §9):

1. **Week 1–2:** Riley S1 → Riley S4 → Riley S5 (start). Jordan S3 in parallel. Sam S2 in parallel (against mocked `/onboarding/session`).
2. **Week 3–4:** Riley finishes S5 Banking seed. Jordan S6 (event detection). Sam continues S2 + starts Sidebar/shell pieces ahead of S9/S10.
3. **Week 5–6:** Jordan S7 (LLM pipeline) — gated on S5. Sam starts S9 + S10 against mock card JSON.
4. **Week 7–8:** Riley S8 (editorial review). Sam continues S10. Jordan S11 (signal monitoring) starts.
5. **Week 9–10:** Sam finishes S9 + S10 + S12 (prediction logger). Riley S13 (bias audit). Jordan finishes S11.
6. **Week 11–12:** Riley S14 tester launch kit. First real card published. Track-record timestamp logged. 5–10 testers onboarded.

Parallel-safe pairs at every week boundary: `S2/S3/S5`, `S6/S7`, `S8/S9/S10`, `S11/S12/S13`. Anything past S14 is Phase 2.

---

## Appendix — Taskmaster-style export (per developer)

### Notes

- Unit tests live next to sources (e.g. `Component.tsx` + `Component.test.tsx`; `service.py` + `tests/test_service.py`).
- Run tests: `pnpm test` (frontend), `pytest -q` (backend). CI runs both on every PR.
- Single `.env.local` at repo root — never duplicated.

### Relevant Files (rollup)

- `frontend/app/onboarding/**` — Onboarding wizard (S2)
- `frontend/app/(app)/pulse/**` — Pulse surface (S9)
- `frontend/app/(app)/thread/[cardId]/**` — Thread surface (S10)
- `frontend/app/admin/factor-db/**` — Internal Factor DB viewer (S5)
- `frontend/app/admin/queue/**` — Editorial queue (S6)
- `frontend/app/admin/review/[draftId]/**` — Editorial review (S8)
- `frontend/components/Sidebar/**` — Sidebar + UserChip (S3, S9)
- `frontend/components/SebiFooter.tsx` — Persistent SEBI bar (S2, S4)
- `frontend/components/Topbar/**` — Notification badge + Phase badge (S11, S14)
- `backend/app/api/**` — Onboarding, feed, cards, predictions, admin_queue, admin_review, notifications, tester_acceptance
- `backend/app/services/**` — mode_detection, factor_db, event_confidence, card_pipeline, number_validator, mmj_validator, cost_guard, signal_check, confidence_gate, bias_detector, publish_card
- `backend/app/jobs/**` — event_detection, signal_monitor, weekly_bias_report
- `backend/app/sources/**` — newsapi, rbi_rss, nse_announcements
- `backend/prompts/**` — synthesis.v1.md, dissent.v1.md, framework.v1.md
- `backend/db/migrations/**` — 0002 through 0009
- `backend/db/seeds/banking_sector.sql`
- `.env.local` — single source of secrets
- `.github/workflows/ci.yml`
- `docs/plans/phase1-go-no-go.md`

### Tasks by developer — Jordan

- [ ] **3.0** Supabase session + user chip (route gating deferred)
  - [ ] **3.1** Configure Supabase Auth magic-link only
  - [ ] **3.2** Sign-in page UI
  - [ ] **3.3** Callback route handler
  - [ ] **3.4** Middleware: session refresh only — **no** auth redirect in Phase 1
  - [ ] **3.5** `get_current_user` FastAPI dependency
  - [ ] **3.6** `UserChip` from session
  - [ ] **3.7** Sign-out action
  - [ ] **3.8** Auth tests (Pytest + RTL)
- [ ] **6.0** Event-detection scheduled job + editorial queue
  - [ ] **6.1** `SourceAdapter` ABC
  - [ ] **6.2** NewsAPI adapter w/ daily-cap
  - [ ] **6.3** RBI RSS adapter
  - [ ] **6.4** NSE adapter + fallback path
  - [ ] **6.5** Confidence scorer
  - [ ] **6.6** Dedupe + persist
  - [ ] **6.7** Render 4-hour cron
  - [ ] **6.8** Admin queue API + page
  - [ ] **6.9** Idempotency + adapter tests
- [ ] **7.0** LLM 3-call card-synthesis pipeline (Claude Sonnet)
  - [ ] **7.1** `synthesis.v1.md`
  - [ ] **7.2** `dissent.v1.md`
  - [ ] **7.3** `framework.v1.md`
  - [ ] **7.4** `llm_client.complete()`
  - [ ] **7.5** `card_pipeline.draft_card()`
  - [ ] **7.6** `number_validator`
  - [ ] **7.7** `mmj_validator`
  - [ ] **7.8** `cost_guard` (50/day cap)
  - [ ] **7.9** `POST /api/cards/draft-from-event`
  - [ ] **7.10** Pipeline + validator tests
- [ ] **11.0** Signal monitoring + confidence gating + notifications
  - [ ] **11.1** `signal_check.evaluate()`
  - [ ] **11.2** `confidence_gate.route()`
  - [ ] **11.3** High path: auto-update + override window
  - [ ] **11.4** Medium path: editor queue
  - [ ] **11.5** Low path: digest log only
  - [ ] **11.6** Notification fan-out
  - [ ] **11.7** Frontend `NotificationBadge`
  - [ ] **11.8** 30-min scheduled cron
  - [ ] **11.9** Gate + override + notification tests

### Tasks by developer — Sam

- [x] **2.0** Onboarding three-question flow + mode detection
  - [x] **2.1** `session_profiles` migration + RLS
  - [x] **2.2** `detect_mode()` pure function
  - [x] **2.3** `POST /onboarding/session` route
  - [x] **2.4** `BrandPanel`, `ProgressDots`, `SebiFooter`
  - [x] **2.5** `Step1Status`
  - [x] **2.6** `Step2Amount`
  - [x] **2.7** `Step3Horizon`
  - [x] **2.8** `Step4ModeResult`
  - [x] **2.9** Loading + error states
  - [x] **2.10** Routing logic (Builder/Protector/Curious)
  - [x] **2.11** Reducer + RTL + Pytest tests
- [ ] **9.0** The Pulse — feed, filters, live insight panel, Fog of War
  - [ ] **9.1** Sidebar (PRD §8.4)
  - [ ] **9.2** `(app)/layout.tsx`
  - [ ] **9.3** `GET /api/feed`
  - [ ] **9.4** Fog of War detector
  - [ ] **9.5** `EventCard`
  - [ ] **9.6** `InsightPanel` sticky
  - [ ] **9.7** `FilterPills` w/ URL state
  - [ ] **9.8** `FogOfWarBanner`
  - [ ] **9.9** Resolved badge inline
  - [ ] **9.10** Mobile behaviour
  - [ ] **9.11** Loading/empty/error
  - [ ] **9.12** API + Fog + RTL tests
- [ ] **10.0** The Thread — Living Card with ICE tabs + aside
  - [ ] **10.1** Page shell + lifecycle badge + Current/Original toggle
  - [ ] **10.2** `IceTabs` (I default, C/E gated)
  - [ ] **10.3** `InsightLayer`
  - [ ] **10.4** `InstrumentCard` (no buy/sell/hold, no price targets)
  - [ ] **10.5** `ContextLayer` w/ MMJ badges
  - [ ] **10.6** `EvidenceLayer` w/ freshness dots
  - [ ] **10.7** Aside `LifecycleTracker`
  - [ ] **10.8** Aside `SignalsToWatch` + consequence map
  - [ ] **10.9** Aside `ConfidenceComposition`
  - [ ] **10.10** Aside `BiasFlags` (placeholder)
  - [ ] **10.11** `PredictionLogger` before C tab
  - [ ] **10.12** `CurrentOriginalToggle` reads `track_record`
  - [ ] **10.13** Language-rule + dissent-required + immutable tests
- [ ] **12.0** Prediction logger + user track-record entries
  - [ ] **12.1** Unique constraint migration
  - [ ] **12.2** `predictions.log()` dual-write
  - [ ] **12.3** Prediction API routes
  - [ ] **12.4** Wire `PredictionLogger`
  - [ ] **12.5** Gating before C tab
  - [ ] **12.6** Disclaimer snapshot
  - [ ] **12.7** Dup + dual-write + UI tests

### Tasks by developer — Riley

- [x] **1.0** Project bootstrap, Supabase, deploys, CI
  - [x] **1.1** Monorepo init
  - [x] **1.2** Single `.env.local`
  - [x] **1.3** Supabase project provisioning
  - [x] **1.4** `/health` endpoint
  - [x] **1.5** Tailwind seeded w/ PRD palette
  - [x] **1.6** Vercel + Render deploys
  - [x] **1.7** CI workflow
  - [x] **1.8** Smoke tests
- [x] **4.0** Core DB schema + append-only track record + SEBI footer
  - [x] **4.1** Enums migration
  - [x] **4.2** `events`
  - [x] **4.3** `signals`
  - [x] **4.4** `instrument_assessments`
  - [x] **4.5** `user_predictions`
  - [x] **4.6** `track_record` append-only RLS
  - [x] **4.7** Pydantic/SQLAlchemy models
  - [x] **4.8** Verify `SebiFooter` on every protected page
  - [x] **4.9** Append-only test
- [ ] **5.0** Factor Exposure DB — Banking sector slice + admin viewer
  - [ ] **5.1** Schema + check constraints
  - [ ] **5.2** 8-factor seed
  - [ ] **5.3** 15 NSE banks seed
  - [ ] **5.4** CSV→SQL loader script
  - [ ] **5.5** `factor_db.lookup()`
  - [ ] **5.6** Factor DB API routes
  - [ ] **5.7** `FactorMatrix` UI
  - [ ] **5.8** Admin allow-list gate
  - [ ] **5.9** Seed-integrity + RTL tests
- [ ] **8.0** Editorial review interface for drafts
  - [ ] **8.1** Reuse Thread components in read-only
  - [ ] **8.2** `ChecklistPanel` (5 items)
  - [ ] **8.3** `POST /publish` + track-record insert
  - [ ] **8.4** `POST /regenerate` w/ editor notes
  - [ ] **8.5** Editor time-on-page log
  - [ ] **8.6** Publish + checklist-gate tests
- [ ] **13.0** Bias audit log + bias flags rendered in Thread aside
  - [ ] **13.1** `card_bias_flags` migration
  - [ ] **13.2** Detector wiring post-publish
  - [ ] **13.3** Recency / concentration / narrative detectors
  - [ ] **13.4** Survivorship + anchoring detectors
  - [ ] **13.5** Weekly editorial-coverage report (`notes/`)
  - [ ] **13.6** Wire `BiasFlags.tsx`
  - [ ] **13.7** Per-detector + UI tests
- [ ] **14.0** Tester launch kit + Phase 1 go/no-go checklist
  - [ ] **14.1** Draft briefing in `notes/`
  - [ ] **14.2** `/tester-briefing` acceptance page
  - [ ] **14.3** `tester_acceptances` migration
  - [ ] **14.4** Middleware gate
  - [ ] **14.5** `PhaseBadge` pill
  - [ ] **14.6** `docs/plans/phase1-go-no-go.md`
  - [ ] **14.7** Acceptance middleware test
