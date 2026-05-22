# Post Implementation Detailed Document — P1-S14

**Version:** v1.0 | **Date:** 22-05-2026  
**Story ID:** P1-S14 (Phase 1, Story 14)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`

---

## Narrative — how this fits in the architecture

Phase 1 ships a **research preview** to **10–15 invited testers**, not a public product. By Week 11–12, every user-facing surface (Onboarding, Pulse, Thread, predictions, notifications) is live — but the **compliance posture** still depends on two things the PRD treats as non-negotiable: a **persistent SEBI disclaimer** on every screen (already delivered in earlier stories) and a **mandatory signed tester briefing** before anyone who was invited via magic link can use the app as an identified user.

P1-S14 is the **launch gate** for that second requirement. Architecturally it is a **thin compliance layer** sitting between **Supabase Auth** (P1-S3) and the **app shell** (P1-S9+): when a **signed-in** user hits a gated route (`/pulse`, `/thread`, `/admin`, etc.), **Next.js middleware** checks whether a row exists in **`tester_acceptances`**. If not, the browser is redirected to **`/tester-briefing`**, where the user must **scroll the full briefing**, **check an explicit consent box**, and **Accept**. Acceptance is persisted server-side with **`accepted_at`** and **`ip`** (V1 e-signature surrogate — no PDF workflow yet). Only then does the normal app experience unlock.

Anonymous visitors remain **ungated** — consistent with Phase 1’s deliberate choice (P1-S3) not to block anonymous access to surfaces during internal build. The gate applies to **invited, authenticated testers** only. That split matters: developers can still browse without signing in; testers who accept the magic link cannot bypass the briefing.

A parallel **ops artefact** ships with the code: **`docs/plans/phase1-go-no-go.md`** — a gitignored checklist covering all **PRD §13** quantitative and qualitative success metrics plus compliance smoke items (first published card, track-record row, etc.). S14 is not a one-time sign-off ceremony; the plan treats it as a **Week 11–12 ritual** that will surface gaps.

Visually, every in-app session also carries a non-dismissable **“Phase 1 tester”** pill (`PhaseBadge`) in the mobile topbar and desktop sidebar — a constant reminder that the build is a research preview, not a regulated advice product.

**If you remember one thing:** do not remove the **anonymous-open / signed-in-gated** split without revisiting P1-S3, P3-S3 legal hardening, and PRD risk #5 (testers making real-money decisions). The briefing gate exists to make the compliance story **defensible**, not to replace legal review before any audience beyond the invite list.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S14 |
| **Title** | Tester launch kit + Phase 1 go/no-go checklist |
| **Category** | **Full Stack** (Postgres migration + RLS, FastAPI acceptance API, Next.js briefing page + middleware gate + shell badge, ops checklist, tests) |

**What this story aimed to achieve (plain language)**

1. Provide a **mandatory tester briefing** with scope, SEBI framing, no-real-money-decisions language, and feedback expectations.  
2. Implement an **acceptance flow** (scroll + checkbox + Accept) that records **timestamp + IP** as a V1 e-signature surrogate.  
3. **Redirect signed-in users** who have not accepted away from app routes until they complete the flow.  
4. Show a **persistent “Phase 1 tester” pill** on all in-app surfaces — never dismissable.  
5. Author a **go/no-go checklist** (`phase1-go-no-go.md`) aligned to **PRD §13** for Week 11–12 launch ritual.

**How it fits into the overall application**

- **Upstream:** **P1-S2** (onboarding), **P1-S3** (magic-link auth + session cookies), **P1-S9–S12** (all user-facing surfaces testers will use).  
- **This story:** final **Phase 1 compliance gate** before inviting the 5–10 tester cohort; pairs with persistent **SebiFooter** (P1-S2) and Thread copy lint (P1-S10).  
- **Downstream:** **P1-S15** (optional admin signal queue) can ship in parallel; **P3-S3 / P3-S4** harden briefing (PDF download, formal legal sign-off); **P3-S7** public marketing routes new users through `/tester-briefing` before app access.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories (plan checklist) mapped to behaviour**

| Sub-task | What it does in the codebase |
|----------|-------------------------------|
| **14.1** | **`notes/tester-briefing.md`** (gitignored local draft) + committed mirror **`frontend/lib/tester-briefing/content.ts`**: scope, SEBI framing, no real-money decisions, feedback channel. |
| **14.2** | **`/tester-briefing`** page: scrollable briefing cards, scroll-to-end gate, checkbox consent, **Accept** → `POST /api/tester/accept` → redirect `/pulse`. Requires Supabase session (magic link). |
| **14.3** | Migration **`0013_tester_acceptances.sql`**: table + RLS (select/insert own row); registered in **`migrate.py`**. |
| **14.4** | **`frontend/middleware.ts`**: after session refresh, if user + gated path + no `tester_acceptances` row → redirect **`/tester-briefing`**. Pure path logic in **`frontend/lib/tester-gate.ts`**. |
| **14.5** | **`PhaseBadge`** in **`AppShell`** (mobile header) and **`Sidebar`** (desktop header row) — always rendered, no dismiss state. |
| **14.6** | **`docs/plans/phase1-go-no-go.md`**: PRD §13 metrics table, qualitative criteria, compliance items, infra smoke, sign-off lines — **gitignored** via `.gitignore` entry. |
| **14.7** | **`test_tester_acceptance_required.py`** (API + `require_tester_acceptance` dependency); **`tester-gate.test.ts`**, **`PhaseBadge.test.tsx`**. |

**Functional breakdown**

- **Briefing content:** five sections (scope, SEBI, no real-money, feedback, acceptance) rendered from **`TESTER_BRIEFING_SECTIONS`** constant.  
- **Scroll gate:** client tracks scroll position; checkbox + Accept disabled until user scrolls to bottom (~24px tolerance).  
- **Accept API:** FastAPI verifies Supabase JWT via **`get_current_user`**, captures IP from **`X-Forwarded-For`** (first hop) or **`request.client.host`**, inserts via **service role PostgREST** in **`tester_acceptance.record_acceptance`**.  
- **Middleware gate:** Supabase SSR client queries **`tester_acceptances`** with user JWT (RLS allows read own row). Anonymous users skip query entirely.  
- **Status API:** **`GET /api/tester/status`** returns `{ accepted: bool }` for authenticated clients (optional UX; middleware uses direct Supabase read).

**Edge cases, validations, and error handling**

- **Not signed in on briefing page:** Accept shows inline error — “Sign in with your invite link before accepting.”  
- **Duplicate accept:** API returns **409** `already_accepted` if row exists (pre-check + DB unique PK on `user_id`).  
- **Supabase not configured (local dev):** `has_accepted` returns **false**; `record_acceptance` raises **`supabase_not_configured`** → API **503**. Middleware query may fail silently depending on Supabase client config — devs without DB should sign in only when testing gate.  
- **Already on `/tester-briefing`:** middleware never redirects away (prevents redirect loop).  
- **Onboarding / sign-in / callback:** exempt from gate via **`pathRequiresTesterAcceptance`** — user can complete magic link exchange before briefing.

**Business rules enforced**

- ⚠️ **Signed-in testers must accept** before Pulse, Thread, Map, Mirror, Lens, Admin, or `/api/protected/*`.  
- ⚠️ **Anonymous Phase 1 access remains open** — no redirect to `/sign-in` for visitors without session (P1-S3 posture preserved).  
- Acceptance record is **append-only in V1** (one row per user; no UPDATE/DELETE policies).  
- Briefing explicitly states **educational analysis only** — aligns with PRD §12 risk #3 and #5.  
- **Operational AC still open:** first real published card + first **`track_record`** row — verified manually via go/no-go checklist, not automated in this story.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Migration `0013` not `0009`** | **`0009_editorial_publish_notifications.sql`** already exists in repo sequence. | Renumbering old migrations: risky for applied DBs. |
| **Checkbox + timestamp + IP (no PDF in V1)** | Plan explicitly allows e-signature surrogate; faster to ship for Week 11–12. | PDF generation + download: deferred to **P3-S3/S4**. |
| **Dual briefing sources** | **`notes/tester-briefing.md`** gitignored for PO/legal edits; **`content.ts`** committed so Vercel deploy always has copy. | Single gitignored file only: production deploy would miss briefing text. |
| **Gate in Next middleware (not FastAPI for pages)** | Page access is a frontend routing concern; uses existing Supabase SSR cookie refresh. | Backend-only gate: cannot block RSC page render without frontend hook. |
| **`require_tester_acceptance` FastAPI dependency** | Allows future API routes to enforce same rule without duplicating checks. | Middleware-only: APIs like predictions could be called before accept if not wired. |
| **Service role for accept INSERT** | Matches **`session_profile_store`** pattern; reliable write regardless of RLS edge cases. | User JWT insert via PostgREST: would rely on insert policy only; harder to audit centrally. |
| **Anonymous users ungated** | Preserves P1-S3 “no route blocking for Phase 1” for dev/demo; gate targets **invited signed-in** testers per PRD Week 11–12. | Gate all visitors: would break anonymous onboarding demos and conflict with S3 AC. |

**Assumptions**

- Invited testers **always complete magic link** before using gated features; briefing Accept requires Bearer token.  
- **`phase1-go-no-go.md`** is filled by Product Owner during launch week — template ships empty checkboxes.

**⚠️ Critical — do not reverse without understanding full context**

- **Do not** remove middleware gate for signed-in users while PRD still requires mandatory briefing (risk #5).  
- **Do not** make **`PhaseBadge`** dismissable — story AC requires always-visible research-preview labelling.  
- **Do not** add UPDATE/DELETE on **`tester_acceptances`** without legal/compliance review — V1 treats acceptance as immutable audit evidence.  
- **Do not** conflate this gate with full **route auth** — anonymous access is intentional until public beta hardening.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1-S2:** SebiFooter pattern; **P1-S3:** Supabase session + middleware refresh; **P1-S9–S12:** surfaces testers use after accept. |
| **Enables** | **Week 11–12 tester cohort** launch; **P3-S3** legal audit baseline; **P3-S7** invite funnel through `/tester-briefing`. |
| **Shared components** | **AppShell**, **Sidebar**, **SebiFooter**, Supabase **`updateSession`** middleware helper. |
| **Shared data** | **`auth.users`** FK on **`tester_acceptances.user_id`**. |
| **Plan linkage** | Final Phase 1 story before optional **P1-S15**; Phase 2 starts after Phase 1 complete per plan timeline. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Pattern** | **Defence in depth:** middleware (pages) + optional FastAPI dependency (APIs) + RLS (direct Supabase reads). |
| **Schema** | Single table **`tester_acceptances`**: PK **`user_id`**, **`accepted_at`**, nullable **`ip`**. |
| **API** | **`POST /api/tester/accept`**, **`GET /api/tester/status`** — Bearer JWT required. |
| **UI** | Briefing page inside **`(app)` layout** (shell + SebiFooter); scroll-gated consent; blue **Phase 1 tester** pill (`#EFF6FF` / `#1D4ED8`). |
| **Ops** | Gitignored **`phase1-go-no-go.md`** + gitignored **`notes/tester-briefing.md`**. |
| **Tooling** | **httpx** PostgREST for backend writes; **@supabase/ssr** for middleware reads. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `0013_tester_acceptances.sql` | `backend/db/migrations/` | Acceptance table, index, RLS policies. |
| `tester_acceptance.py` | `backend/app/services/` | `has_accepted`, `record_acceptance` via PostgREST. |
| `tester_acceptance.py` | `backend/app/api/` | Accept/status routes + `require_tester_acceptance` dependency. |
| `test_tester_acceptance_required.py` | `backend/tests/` | Auth, accept, 403 gate, status tests. |
| `content.ts` | `frontend/lib/tester-briefing/` | Committed briefing copy for UI. |
| `tester-gate.ts` | `frontend/lib/` | Pure path/gate helpers for middleware. |
| `tester-gate.test.ts` | `frontend/lib/` | Unit tests for redirect logic. |
| `page.tsx` | `frontend/app/(app)/tester-briefing/` | Briefing + scroll gate + accept flow. |
| `PhaseBadge.tsx` | `frontend/components/Topbar/` | Always-visible Phase 1 pill. |
| `PhaseBadge.test.tsx` | `frontend/components/Topbar/` | RTL smoke test. |
| `tester-briefing.md` | `notes/` | Gitignored PO/legal draft (mirrors content.ts). |
| `phase1-go-no-go.md` | `docs/plans/` | Gitignored launch checklist (PRD §13). |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `main.py` | `backend/app/` | Register **`tester_acceptance_router`** at `/api`. |
| `migrate.py` | `backend/app/db/` | Register **`0013_tester_acceptances.sql`**. |
| `middleware.ts` | `frontend/` | Tester acceptance redirect after session refresh; expanded matcher for `/tester-briefing`. |
| `middleware.ts` | `frontend/lib/supabase/` | Return **`supabase`** client from **`updateSession`** for acceptance query. |
| `AppShell.tsx` | `frontend/components/Sidebar/` | Embed **`PhaseBadge`** in mobile header beside **`NotificationBadge`**. |
| `Sidebar.tsx` | `frontend/components/Sidebar/` | Embed **`PhaseBadge`** in desktop header row. |
| `.gitignore` | repo root | Explicit ignore for **`docs/plans/phase1-go-no-go.md`**. |
| `finnwise-phase1-implementation-tasks.md` | `docs/plans/` | P1-S14 tasks **14.0–14.7** marked complete; migration path corrected to **0013**. |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

| Object | Detail |
|--------|--------|
| **`tester_acceptances`** | **`user_id uuid PK`** → **`auth.users(id) ON DELETE CASCADE`**; **`accepted_at timestamptz NOT NULL DEFAULT now()`**; **`ip text`** nullable. |
| **Index** | **`tester_acceptances_accepted_at_idx`** on **`accepted_at DESC`** for audit queries. |
| **RLS** | **`tester_acceptances_select_own`**: `auth.uid() = user_id`; **`tester_acceptances_insert_own`**: insert only for self. No UPDATE/DELETE policies — V1 append-only semantics. |
| **Backend writes** | **`record_acceptance`** uses **service role key** (bypasses RLS) — same pattern as **`session_profile_store`**. |

**Sequencing:** Apply **`0013_tester_acceptances.sql`** after **`0012_user_predictions_unique.sql`** (per **`migrate.py`**).

**Seed data:** None — rows created only on user Accept.

---

### B2. API / INTEGRATION CONTRACTS

| Method | Route | Auth | Request | Response |
|--------|-------|------|---------|----------|
| POST | `/api/tester/accept` | **Bearer** (Supabase JWT) | Empty body | `{ "ok": true, "accepted_at": "<ISO8601>" }` |
| GET | `/api/tester/status` | **Bearer** | — | `{ "accepted": true \| false, "accepted_at": null }` |

**Error responses**

| Status | Code | When |
|--------|------|------|
| 401 | — | Missing/invalid Bearer token |
| 409 | `already_accepted` | Row already exists for user |
| 403 | `tester_acceptance_required` | **`require_tester_acceptance`** dependency on protected route |
| 503 | `supabase_not_configured` | No Supabase URL/service key in backend env |

**Example — accept (success)**

```http
POST /api/tester/accept HTTP/1.1
Authorization: Bearer <supabase_access_token>
```

```json
{ "ok": true, "accepted_at": "2026-05-22T10:15:00+00:00" }
```

**Frontend integration:** Briefing page uses browser Supabase session + **`getApiBaseUrl()`** — same pattern as **`NotificationBadge`**.

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Middleware decision tree**

```
Request to matched route
├── updateSession (refresh cookies, get user)
├── No user → pass through (anonymous OK)
├── User + path exempt (onboarding, sign-in, callback, /) → pass through
├── User + path gated
│   ├── Query tester_acceptances for user_id
│   ├── Row exists → pass through
│   └── No row + not already on /tester-briefing → redirect /tester-briefing
└── Return supabaseResponse
```

**Gated path prefixes:** `/pulse`, `/thread`, `/mirror`, `/lens`, `/map`, `/admin`, `/api/protected`.

**Briefing page accept flow**

1. User scrolls briefing container to bottom → **`hasScrolledToEnd = true`**.  
2. User checks consent checkbox.  
3. **`POST /api/tester/accept`** with session access token.  
4. On success: **`router.replace("/pulse")`** + **`router.refresh()`**.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **No PDF briefing** | V1 uses in-app text only; **P3-S3/S4** adds PDF download + hardened capture. |
| **`GET /tester/status` omits `accepted_at` when accepted** | Returns `accepted: true` only; timestamp available from DB audit queries — minor API completeness gap. |
| **Predictions API not wired to `require_tester_acceptance`** | Middleware blocks page access; direct API calls with Bearer still possible until dependency added to sensitive routes. |
| **Middleware Supabase query on every gated navigation** | Acceptable for 10–15 testers; consider cookie flag or short TTL cache if latency becomes visible. |
| **Legal review not included** | PRD ⚠️ requires SEBI-specialised lawyer before audience beyond invite list — briefing copy is best-effort, not legal advice. |
| **Operational AC open** | First published card + **`track_record`** row — manual go/no-go items. |
| **Duplicate `PhaseBadge` name in Phase 2** | **P2-S6** plans a purple Lens **`PhaseBadge`** — different component/path; avoid naming collision when Phase 2 lands. |

---

### B5. TESTING NOTES

| Suite | Coverage |
|-------|----------|
| **Backend** | `test_tester_acceptance_required.py` — 401 without auth, accept records user_id, 403 via dependency when not accepted, 200 when accepted, status endpoint true/false. |
| **Frontend unit** | `tester-gate.test.ts` — gated vs exempt paths, redirect predicate. |
| **Frontend RTL** | `PhaseBadge.test.tsx` — pill always renders with accessible label. |

**Gaps**

- No E2E Playwright flow: magic link → redirect → scroll → accept → land on Pulse.  
- No integration test against real Supabase **`tester_acceptances`** table (backend tests mock **`has_accepted`** / **`record_acceptance`**).  
- Middleware itself not executed in Jest (logic covered via **`tester-gate`** pure functions).

**Manual smoke recommended before invite**

1. Apply migration **0013** on dev Supabase.  
2. Magic-link as invited user → navigate to `/pulse` → redirected to `/tester-briefing`.  
3. Complete accept → land on Pulse with **Phase 1 tester** pill visible.  
4. Verify row in **`tester_acceptances`** with timestamp and IP.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable / setting | Where | Purpose |
|--------------------|-------|---------|
| **`SUPABASE_URL`**, **`SUPABASE_ANON_KEY`** | Frontend (middleware, briefing page) | Session refresh + RLS read of acceptances. |
| **`SUPABASE_SERVICE_ROLE_KEY`** | Backend | PostgREST insert in **`record_acceptance`**. |
| **`NEXT_PUBLIC_API_BASE_URL`** | Frontend | Points Accept POST to Render/local FastAPI. |
| **`.gitignore`** | `notes/`, `docs/plans/phase1-go-no-go.md` | Local PO drafts and filled checklist stay out of git. |

**Deployment sequencing**

1. Deploy backend with new router + env keys.  
2. Apply **`0013`** migration on Supabase.  
3. Deploy frontend with middleware + briefing page.  
4. PO fills **`phase1-go-no-go.md`** during launch week.

**Feature toggles:** None — gate is always on for signed-in users on gated paths once deployed.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

1. **Start here:** `frontend/middleware.ts` + `frontend/lib/tester-gate.ts` for page gate; `backend/app/api/tester_acceptance.py` for API.  
2. **Copy changes:** edit **`frontend/lib/tester-briefing/content.ts`** and mirror to **`notes/tester-briefing.md`** for PO; redeploy frontend after copy changes.  
3. **Adding new app routes:** if a route should require briefing acceptance, add its prefix to **`gatedPrefixes`** in **`tester-gate.ts`** and to **`middleware.config.matcher`**.  
4. **Protecting new APIs:** add **`Depends(require_tester_acceptance)`** alongside **`get_current_user`**.  
5. **Common mistake:** gating anonymous users — breaks P1-S3 Phase 1 posture; only gate when **`user`** is non-null.  
6. **Common mistake:** redirect loop — ensure **`/tester-briefing`** is exempt in **`pathRequiresTesterAcceptance`**.  
7. **Audit queries:** `SELECT * FROM tester_acceptances ORDER BY accepted_at DESC` — confirm tester cohort acceptance before expanding access.  
8. **Contact:** **Compliance / Product Owner** for briefing copy and go/no-go sign-off; **Backend owner** for PostgREST/service-role writes; **Frontend owner** for middleware matcher changes.

---

## Related plan items still open (outside this story’s code scope)

| Item | Owner | Notes |
|------|-------|-------|
| First real event card published | Editorial / PO | **P1-S8** publish flow; verify in go/no-go checklist |
| First **`track_record`** row in DB | Editorial / PO | Logged on publish or user prediction per **P1-S12** |
| **P1-S15** admin signal queue UX | Riley/Jordan | Optional polish before tester launch |
| Formal legal review | PO + legal | Required before any non-invite audience (PRD §12) |
