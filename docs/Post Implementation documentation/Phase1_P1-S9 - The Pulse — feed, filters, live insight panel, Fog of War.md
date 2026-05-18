# Post Implementation Detailed Document — P1-S9

**Version:** v1.0 | **Date:** 18-05-2026  
**Story ID:** P1-S9 (Phase 1, Story 9)  
**Reference plan:** `docs/plans/finnwise-phase1-implementation-tasks.md`

---

## Narrative style

**The Pulse** is FinnWise’s “shallow reading” home: a continuous stream of **Event Intelligence Cards** where the **financial consequence is the headline** and the **raw news headline is secondary context**. Architecturally, it is the first place where three separate concerns meet in one screen: **editorially published analytical objects** (cards in Postgres), **who is viewing** (onboarding session profile—not full auth personalisation yet), and **truthfulness UX** (confidence and “Fog of War” when the world is too chaotic to compress into tidy certainty).

From a **data-flow** perspective, the browser does not talk to Supabase for the feed. The Next.js app calls the **Python FastAPI** service at **`GET /api/feed`**, which uses **`SUPABASE_DB_URL`** and **psycopg** (the same pattern as the factor DB and card repository) to **join** `cards` → `events`, pull **instrument assessments**, derive presentation fields (confidence tiers, excerpts), and compute a **boolean `fog_of_war`** flag from a **global** view of “major” active events—not just from whatever filters the user clicked. That split is intentional: filters narrow what you *see*; Fog of War answers whether the **market regime** is noisy enough that the product should **front-load uncertainty** before analysis.

From a **UI architecture** perspective, the Pulse is a **client island** inside the App Router: **`pulse/page.tsx`** is a thin server wrapper with **`Suspense`** around **`PulseClient`**, because **`useSearchParams`** must be inside a suspense boundary. Inside the client, **`usePulseFeed`** owns **fetch state**, **selected card id**, and **refetch**; **URL search params** own the **category filter canonical state** (`?category=macro,rbi_policy`), so a refresh or shared link reproduces the same filter. The **insight panel** is not a separate route—it is **sibling UI** driven by the same selection state—so “browsing” stays on one URL (`/pulse`) until the user explicitly opts into **The Thread** (`/thread/[cardId]`). On **viewports under 860px**, the right column is **not mounted** for width; instead, tapping a card **navigates** to the thread placeholder, matching the PRD’s mobile trade-off (space over parallel panels).

**Session linkage** matters for the “personalised feed” story without building full JWT-backed profile APIs in this slice: when onboarding finishes, **`session_id`** is stored in **`localStorage`** (`finnwise_session_id`). The feed API accepts **`session_id`** as a query parameter, looks up **`session_profiles`** (horizon, mode), and applies a **time window** on **`cards.created_at`** from that horizon. Category pills still **override** the visible slice of cards; horizon **does not** add new columns to cards—it is a **viewer lens** on recency until richer tagging exists.

**Fog of War** is worth understanding as **product logic**, not just a banner: we treat “major” as **`events.confidence_score >= 70`** and “compounding” as **at least three** cards in **`active`** or **`signal_triggered`** lifecycle **and** **category overlap** (some category appears at least twice). That is stricter than “three bad headlines”—it encodes *overlapping thematic risk* so the banner does not fire on three unrelated one-off spikes.

If you only remember **three architectural anchors**: (1) **Feed reads go through FastAPI + psycopg**, not the browser-to-Supabase path used for auth/onboarding visuals; (2) **filter state is URL-first** so Pulse remains shareable and refresh-safe; (3) **Fog of War is globally computed**, decoupled from the user’s category filter, so the honesty signal tracks **market state**, not **UI narrowing**.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1-S9 |
| **Title** | The Pulse — feed, filters, live insight panel, Fog of War |
| **Category** | **Full Stack** (FastAPI feed + Postgres queries, Next.js App Router UI + client hooks, RTL tests, onboarding touchpoint for session id) |

**What this story aimed to achieve (plain language)**

Deliver the **Phase 1 Pulse surface**: a **220px** sidebar consistent with the PRD navigation spec (including **Phase 2** badges on Mirror and Lens); a **two-column** desktop layout (~**60%** feed / ~**40%** sticky **insight panel**); **category pills** in a **sticky topbar** (navy active treatment); **event cards** with **Playfair** consequence headline, italic **event context**, **two separate confidence indicators** (direction vs magnitude—never merged), and **instrument chips**; **selection** that updates the panel **without routing**; **Fog of War** banner when overlapping major active events cross a threshold; **resolved** cards **remaining visible** with a green pill; **mobile** behaviour that **hides** the panel and **deep-links** to **`/thread/[cardId]`**; plus **loading / empty / error-retry** UX and **automated tests** on backend rules and key RTL assertions.

**How it fits into the overall application**

The Pulse is the **default mental home** for **Portfolio Protectors** and a primary entry for **Curious** users (see PRD routing). It sits **downstream** of **P1-S4** (card/event schema), **P1-S7** (cards exist with ICE fields and assessments), and **P1-S3** (app shell + session). It is **upstream** of **P1-S10** (full Thread experience)—the Pulse deliberately stops at a **preview panel** and a **placeholder thread route** until the ICE tabs and aside ship. **P2-S9** (holdings personalisation) will eventually tighten relevance; today, personalisation is **horizon-window + category filters**, not tickers sent to the backend.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items (from the implementation plan) and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **9.1** | **`Sidebar.tsx`**: extracted from the shell; **220px**, logo block padding per §8.4, **Surfaces** group label, nav spacing, **Phase 2** pill on Mirror/Lens, active **blue tint** treatment. |
| **9.2** | **`AppShell`**: wraps **desktop sidebar** + **main column**; adds **mobile top strip** navigation for <860px; **SEBI footer** below `children` for every in-app route using the shell. *Note:* `(app)/layout.tsx` still composes `AppShell`; topbar for Pulse remains **page-owned** (not global) so other routes are not forced into Pulse chrome. |
| **9.3** | **`GET /api/feed`**: query params **`category`** (CSV), **`horizon`** (optional override), **`session_id`** (optional → `session_profiles`); returns **`cards[]`**, **`fog_of_war`**, **`profile`**, **`last_updated`**, **`counts`**; card lifecycle filter includes **published through resolved** (excludes **draft** / **archived** for the public-style feed). |
| **9.4** | **`detect_fog_of_war` + SQL-backed `fetch_fog_of_war_flag`**: threshold on **≥3** relevant cards, **active/signal_triggered**, **major** confidence, **category overlap** (duplicate category). |
| **9.5** | **`EventCard`**: Playfair **15px** headline, italic context, category chip, **two** labelled confidence rows, up to **four** instrument chips, **3px** blue **left** border when selected, **Resolved** pill when `lifecycle_state === resolved`. |
| **9.6** | **`InsightPanel`**: sticky right column; **direction / magnitude / last reviewed** trio; up to **four** mini instrument rows; CTA link to **`/thread/[id]`**; mirrors excerpt + headline. |
| **9.7** | **`FilterPills` + URL**: multi-select; **All** clears selection; **`router.replace`** updates `?category=` sorted list. |
| **9.8** | **`FogOfWarBanner`**: amber treatment; renders when API **`fog_of_war`** true. |
| **9.9** | Backend **does not** exclude `resolved`; green pill on card. |
| **9.10** | **`matchMedia` (max-width 859px)** routes card tap to **`/thread/[cardId]`**; panel hidden with `min-[860px]:` breakpoints. |
| **9.11** | Skeletons while loading; empty copy; error panel with **Retry** → `refetch`. |
| **9.12** | **`test_feed_filtering`**, **`test_fog_of_war_detector`**, **`EventCard.test.tsx`**. |

**Functional breakdown**

- **Feed assembly:** SQL selects visible cards joined to events, optional **horizon cutoff** on `cards.created_at`, optional **`e.category = ANY(...)`**; second query batches **instrument_assessments** (version **1**).
- **Confidence presentation:** direction/magnitude are **derived tiers** from `events.confidence_score` (not separate DB columns)—magnitude uses a **deterministic offset** from the same score so the UI legitimately shows **two different labels**.
- **Selection model:** desktop sets **`selectedId`** in **`usePulseFeed`**; first load auto-selects first card; refetch preserves selection when still present in results.

**Edge cases, validations, and error handling**

- **Invalid `horizon` query:** API returns **422** with a structured detail code.
- **No `SUPABASE_DB_URL`:** `connection()` raises; API maps to **503** with `db_unavailable` for feed route handler.
- **Empty feed:** UI shows **empty state**; counts show **0**.
- **No `session_id`:** profile meta is null; horizon filter is omitted unless **`horizon`** query passed.

**Business rules enforced**

- **No buy/sell/hold** language is a PRD rule enforced more heavily in **P1-S10** copy; Pulse chips only expose **`signal_type`** strings from assessments (expected to stay within opportunity/headwind/watch vocabulary from the pipeline).
- **Fog of War** surfaces **uncertainty first** when compounding majors overlap.
- **Resolved cards stay visible** to avoid survivorship bias in the feed narrative.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Feed via FastAPI + psycopg** | Reuses backend DB access, keeps **service role / DB URL** off the browser; single place to evolve joins and Fog logic. | **Supabase PostgREST from browser**: would expose schema & RLS complexity for a joined card feed; harder to centralise rules. |
| **URL as source of truth for category filters** | Supports refresh + shareable filtered views; avoids desync between pills and fetch. | **React state only**: loses deep-linking. |
| **`session_id` in query string + localStorage** | Matches existing onboarding persistence model (no magic JWT merge story in this slice). | **Cookie session**: would need server middleware changes; larger scope. |
| **Fog computed globally (not per-filter)** | Aligns with “regime honesty”: hiding overlapping major events when user filters one category would be misleading. | **Fog from filtered subset**: simpler but wrong product semantics. |
| **Placeholder Thread route** | **P1-S10** owns ICE; Pulse must still satisfy mobile deep-link acceptance. | Blocking mobile until S10: would violate **9.10**. |
| **860px breakpoint** | Chosen to align with PRD desktop/tablet split language (“>860px” full shell). | Tailwind `lg` (1024px) only: would diverge from PRD spec. |

**Assumptions**

- **Horizon → recency window** mapping (`under_1y`, `1_3y`, etc. to day counts) is an MVP stand-in until event/card objects carry explicit investment-horizon tags.

**⚠️ Critical — do not reverse lightly**

- **Do not fold Fog of War into client-only logic** without a server source of truth—mobile and future clients must see the same honesty flag.
- **Do not merge direction and magnitude** into a single score in the Pulse card UI—PRD §8.6 is explicit; regression tests guard this.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Dependency |
|-----------|------------|
| **Upstream** | **P1-S3** (`AppShell`, auth display), **P1-S4** (`cards`, `events`, `instrument_assessments`, enums), **P1-S7** (card rows exist), **onboarding** (`session_profiles`, `session_id` persistence). |
| **Downstream** | **P1-S10** replaces thread placeholder with full ICE UI; **P2-S9** may add holdings-aware ranking (must stay session-safe per Phase 2 plan). |
| **Shared** | **`getApiBaseUrl` / `NEXT_PUBLIC_API_BASE_URL`**, **Tailwind FinnWise tokens**, **SEBI footer component**, **Supabase auth user chip** (unchanged contract). |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | Next.js **RSC shell** + **client island** for Pulse; FastAPI **read API** with explicit DTO shaping for UI. |
| **Database** | **No new migrations** in this story—uses existing **`cards`**, **`events`**, **`instrument_assessments`**, **`session_profiles`**. |
| **API** | **`GET /api/feed`** — optional **`session_id`**, **`category`**, **`horizon`**; JSON payload with **`cards`**, **`fog_of_war`**, **`profile`**, timestamps. |
| **Auth** | **None on feed** in Phase 1 posture (consistent with other read paths); session profile is **opt-in** via id. |
| **UI/UX** | Playfair + DM Mono metadata; **navy** (`#1A4FCC`) active pills; **amber** Fog banner; **two-column** only on desktop. |
| **Libraries** | Existing stack only (React 18, Next 14, Tailwind). |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `Sidebar.tsx` | `frontend/components/Sidebar/Sidebar.tsx` | PRD sidebar nav + Phase 2 badges + user chip area |
| `sessionProfile.ts` | `frontend/lib/sessionProfile.ts` | `localStorage` helpers for `finnwise_session_id` |
| `pulseTypes.ts` | `frontend/lib/cards/pulseTypes.ts` | Feed response TypeScript types |
| `categories.ts` | `frontend/lib/cards/categories.ts` | Category labels + pill colour maps |
| `usePulseFeed.ts` | `frontend/lib/cards/usePulseFeed.ts` | Fetch + selection + refetch hook |
| `FilterPills.tsx` | `frontend/app/(app)/pulse/_components/FilterPills.tsx` | Multi-select pills + All |
| `FogOfWarBanner.tsx` | `frontend/app/(app)/pulse/_components/FogOfWarBanner.tsx` | Amber warning banner |
| `EventCard.tsx` | `frontend/app/(app)/pulse/_components/EventCard.tsx` | Feed card presentation |
| `InsightPanel.tsx` | `frontend/app/(app)/pulse/_components/InsightPanel.tsx` | Sticky preview column |
| `Topbar.tsx` | `frontend/app/(app)/pulse/_components/Topbar.tsx` | Pulse chrome + pills row |
| `PulseClient.tsx` | `frontend/app/(app)/pulse/_components/PulseClient.tsx` | Orchestrates layout, breakpoints, data bind |
| `EventCard.test.tsx` | `frontend/app/(app)/pulse/_components/EventCard.test.tsx` | RTL tests (two dots, resolved) |
| `page.tsx` | `frontend/app/(app)/thread/[cardId]/page.tsx` | Mobile thread **placeholder** until P1-S10 |
| `feed.py` | `backend/app/services/feed.py` | SQL + fog detection + DTO shaping |
| `feed.py` | `backend/app/api/feed.py` | FastAPI router for `/api/feed` |
| `test_feed_filtering.py` | `backend/tests/test_feed_filtering.py` | Mocked feed response + tier tests |
| `test_fog_of_war_detector.py` | `backend/tests/test_fog_of_war_detector.py` | Fog + horizon unit tests |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `AppShell.tsx` | `frontend/components/Sidebar/AppShell.tsx` | Uses `Sidebar`; mobile nav strip; `SebiFooter` in main column |
| `page.tsx` | `frontend/app/(app)/pulse/page.tsx` | `Suspense` + `PulseClient` entry |
| `Step4ModeResult.tsx` | `frontend/app/onboarding/_components/Step4ModeResult.tsx` | Persists `session_id` to `localStorage` on completion |
| `main.py` | `backend/app/main.py` | Registers **`/api/feed`** router |
| `finnwise-phase1-implementation-tasks.md` | `docs/plans/finnwise-phase1-implementation-tasks.md` | P1-S9 checkboxes marked done |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- **None introduced in P1-S9.** The feed **reads** `cards`, `events`, `instrument_assessments`, and `session_profiles` as created in earlier migrations (**0002**, **0004**, **0008**, etc.).

### B2. API / INTEGRATION CONTRACTS

**`GET /api/feed`**

| Query param | Required | Description |
|-------------|----------|-------------|
| `category` | No | Comma-separated `event_category` values (e.g. `macro,rbi_policy`). |
| `horizon` | No | `under_1y` \| `1_3y` \| `3_7y` \| `7_plus` — overrides profile horizon window. |
| `session_id` | No | UUID → lookup `session_profiles` for default horizon/mode metadata. |

**Response (conceptual)**

```json
{
  "cards": [
    {
      "id": "uuid",
      "headline": "…",
      "event_context": "…",
      "category": "macro",
      "lifecycle_state": "active",
      "direction_confidence": { "tier": "high", "label": "High" },
      "magnitude_confidence": { "tier": "moderate", "label": "Moderate" },
      "instruments": [{ "instrument_id": "HDFCBANK", "signal_type": "watch" }],
      "insight_excerpt": "…",
      "last_reviewed_at": "…",
      "created_at": "…",
      "event_id": "uuid"
    }
  ],
  "fog_of_war": false,
  "profile": {
    "horizon": "1_3y",
    "mode": "portfolio_protector",
    "effective_horizon": "1_3y"
  },
  "last_updated": "2026-05-18T12:00:00+00:00",
  "counts": 1
}
```

**Errors**

- **422** — invalid `horizon`.
- **503** — database URL missing / connection error surfaced as `db_unavailable` in handler.

### B3. BUSINESS LOGIC & RULES (Detailed)

- **Visible card lifecycles:** `published`, `active`, `signal_triggered`, `thesis_confirmed`, `thesis_weakened`, `resolved`.
- **Horizon window:** applied to **`cards.created_at`** (not event ingestion time)—documented assumption.
- **Major event threshold:** `events.confidence_score >= 70`.
- **Fog predicate:** count **≥3** rows where `cards.lifecycle_state ∈ {active, signal_triggered}` and event is major, **and** ∃ category with multiplicity **≥2** among those rows.

### B4. KNOWN CONSTRAINTS & TECH DEBT

- **Confidence tiers** are **heuristic** from a single numeric score—when the LLM pipeline gains explicit direction/magnitude fields, replace derivation instead of tuning offsets.
- **Thread page** is a **placeholder**—do not build product demos that assume ICE content there yet.
- **JWT / user_id profile join** not implemented—`session_profiles.user_id` linking post-magic-link is a future enhancement.
- ⚠️ **Next/Jest** may log lockfile patch noise on some Windows/pnpm setups; tests still run—see local `npm test` output.

### B5. TESTING NOTES

| Area | Coverage |
|------|----------|
| Backend | Fog thresholds, category splitting, profile merge call shape, tier labels |
| Frontend RTL | Separate direction/magnitude labels; resolved pill remains clickable |
| Manual | Run API + UI against a seeded DB with mixed lifecycles & categories to **see** Fog toggle |

**Gaps:** no Playwright/e2e for mobile navigation; no contract snapshot test for `/api/feed` JSON.

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| `SUPABASE_DB_URL` | Required for feed queries (backend). |
| `NEXT_PUBLIC_API_BASE_URL` | Browser feed fetch target (defaults to `http://127.0.0.1:8000`). |

### B7. HANDOVER NOTES FOR DEVELOPERS

- **Start here:** `backend/app/services/feed.py` for truth rules; `PulseClient.tsx` for URL/filter/selection wiring.
- **Common mistake:** computing Fog from **filtered** cards client-side—flag must stay server-authoritative.
- **Thread work:** extend **`/thread/[cardId]`** in **P1-S10**; keep mobile deep link stable.
- **Product / compliance questions:** refer to PRD §5 Screen 2 and §8.x typography/colour tables—this story mirrors those tables literally in several places.
