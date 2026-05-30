# Post Implementation Detailed Document — P3-S1h

**Version:** v1.0 | **Date:** 31-05-2026  
**Story ID:** P3-S1h (Phase 3, Story 1h)  
**PRD2 gap:** G-01 (explainability UI — Phase 3 must-have)  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **9.0**–**9.6**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` WS-2 · Explainability API §  
**Upstream doc:** `docs/Post Implementation documentation/Phase3_P3-S1g - Rule-based confidence scorer and gate swap.md`

---

## Narrative style (read this first)

P3-S1g shipped the **rule-based confidence scorer** and a read-only breakdown API (`GET /api/events/{id}/confidence-breakdown`), but users still saw only the legacy **ICE confidence composition** bar (Measured / Modelled / Judged) in the Thread and Lens asides — with no explanation of *why* the platform assigned a HIGH / MEDIUM / LOW routing tier. P3-S1h closes that trust gap by wiring the aside **`ConfidenceComposition`** component to the breakdown API behind an expandable **“Why this confidence tier?”** panel.

The panel is **lazy-loaded**: no network call until the user expands it, so Thread and Pulse pages avoid layout shift and unnecessary API load. When opened, it shows the five weighted scorer inputs as progress bars, raw vs effective scores, tier label and copy, a **Fog of War dampener callout** when effective &lt; raw, an **Editorial review** badge when `force_editorial_review` is true (backend sets this when post-dedup `source_count > 5`), and a source list with `retrieved_at` timestamps. The existing ICE composition bar is **unchanged** — it answers “how was this card written?” while the new panel answers “why was this event routed at this confidence tier?”

**Tests executed and passed (P3-S1h–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Breakdown API client | `pnpm exec jest confidenceBreakdown.test --no-coverage` (from `frontend/`) | **4 passed** |
| ConfidenceComposition UI | `pnpm exec jest ConfidenceComposition.test --no-coverage` (from `frontend/`) | **2 passed** |
| **Full frontend CI** | `pnpm lint` · `pnpm typecheck` · `pnpm test` · `pnpm build` | **130 passed**, lint/typecheck/build clean |

**Backend:** No backend changes in P3-S1h — breakdown API contract validated in **P3-S1g** (`test_confidence_breakdown_api.py`).

**Three anchors for handover:** (1) **Do not fetch breakdown on mount** — expand-only lazy load is a perf requirement from the plan (p95 budget for Pulse/Thread). (2) **ICE composition ≠ event tier** — keep both surfaces; do not replace Measured/Modelled/Judged with scorer inputs without PO sign-off. (3) **P3-S1g must be deployed** before this UI works in production — the frontend calls `/api/events/{event_id}/confidence-breakdown` with no fallback scorer logic in the browser.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S1h |
| **Title** | Confidence explainability UI |
| **Category** | **Frontend** (consumes P3-S1g backend API) |
| **Points / owner (plan)** | 3 · Sam |
| **Depends on** | P3-S1g (rule-based confidence scorer + breakdown API) |
| **Parallel with** | _None_ |
| **Blocks** | P3-T3 (confidence scoring verification gate) |

**What this story aimed to achieve (plain language)**

When a user reviews a card and the routing tier looks surprising, they can expand a panel in the Thread (or Lens) aside and see **exactly why** the system assigned HIGH, MEDIUM, or LOW confidence: the five weighted inputs, raw and effective scores, contributing sources with retrieval times, FoW dampening when active, and an editorial escalation badge when source count triggers forced review.

**How it fits into the overall application**

- **Upstream:** **P3-S1g** exposes `GET /api/events/{id}/confidence-breakdown` with inputs, sources, tier, FoW flags, and `force_editorial_review`. Card detail responses already include `event_id` via `GET /api/cards/{id}`.
- **This story:** Adds typed frontend client + expandable UI in `ConfidenceComposition`; passes `eventId` from Thread and Lens card surfaces.
- **Downstream:** **P3-T3** verifies scorer, API, and UI agree; **P3-S1l** may extend FoW messaging in feed banner (aside callout is a first surface); **P3-S5** SEBI audit scope includes PRD2 intelligence UI surfaces.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **9.1** | `frontend/lib/api/confidenceBreakdown.ts` — typed client, URL builder, `ConfidenceBreakdownFetchError`. |
| **9.2** | Expandable panel with five weighted input bars + tier explanation copy (HIGH / MEDIUM / LOW thresholds). |
| **9.3** | Source list with formatted `retrieved_at`; FoW callout when `fog_active` and `confidence_effective < confidence_raw`. |
| **9.4** | Fetch only on collapsible expand; skeleton (`confidence-breakdown-skeleton`) while loading. |
| **9.5** | Amber **Editorial review** badge when `force_editorial_review === true`. |
| **9.6** | Component test: happy path renders fixture; 404 shows error alert; API client unit tests. |

**Functional breakdown**

1. **Collapsed default:** Aside shows existing ICE bar (Measured / Modelled / Judged %) and optional Lens footnote. If `eventId` prop is set, a **“Why this confidence tier?”** collapsible trigger appears below a divider — **no fetch yet**.
2. **On expand:** `fetchConfidenceBreakdown(eventId)` calls `{apiBase}/api/events/{eventId}/confidence-breakdown` with `cache: "no-store"`. Loading skeleton displays until response arrives.
3. **Success:** Renders tier dot + label, raw/effective percentages, five input rows (label, value bar, weight %, detail string from API), tier explanation sentence, optional FoW callout, optional escalation badge, source cards with name / retrieved time / link.
4. **Failure:** Red alert (`confidence-breakdown-error`) with message from `describeHttpFailure` (404, proxy misconfig, network).
5. **Re-expand:** Cached in component state — same session does not refetch unless page remounts.

**Two confidence concepts (do not conflate)**

| Surface | Data source | User question answered |
|---------|-------------|------------------------|
| ICE bar (top of card) | `CardDetailResponse.confidence_composition` | How much of this card is measured vs modelled vs judged evidence? |
| Expandable panel (new) | Breakdown API for parent `event_id` | Why did routing assign this HIGH/MEDIUM/LOW tier? |

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| No `eventId` prop | Expandable section hidden (backward compatible) |
| User expands before fetch completes | Skeleton shown; panel content hidden until loaded |
| API 404 (event missing) | Error alert; ICE bar still visible |
| `retrieved_at` null or invalid | Displays “Time unknown” or raw string |
| `sources[]` empty | Input bars still render; source section omitted |
| FoW inactive or effective ≈ raw | FoW callout hidden |
| `force_editorial_review` false | No escalation badge |
| Production browser | Uses same-origin `/backend/...` proxy via `getApiBaseUrl()` |

**Business rules enforced (display-only — scoring logic remains in P3-S1g)**

- Tier copy reflects PO thresholds: HIGH ≥ 0.75, MEDIUM 0.55–0.74, LOW &lt; 0.55 (`calibration_status: provisional` noted in medium copy).
- Escalation badge reflects backend `force_editorial_review` (set when `source_count > 5` on event upsert).
- FoW callout shows dampener multiplier from API (`fog_dampener`, typically `0.6`).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Lazy fetch on expand only** | Plan perf AC: no layout shift on Pulse/Thread; breakdown not needed for every page view | Fetch on mount: extra API load on every Thread open |
| **Extend `ConfidenceComposition` in place** | Plan specified this file; already in Thread/Lens aside stack with dynamic import + skeleton | New sibling component: duplicate card chrome |
| **Keep ICE bar unchanged** | Different domain (card evidence mix vs event routing score); Lens footnote still applies | Replace ICE bar with scorer inputs: breaks Lens PRD §5 copy |
| **`eventId` optional prop** | Component usable without breakdown when id absent | Require eventId: breaks any caller without event context |
| **Client-side cache per mount** | Avoid duplicate fetch on collapse/re-expand in same session | Refetch every expand: wasteful |
| **No React Query / SWR** | Single lazy panel; matches existing fetch patterns in repo | Global cache layer: over-engineering for one panel |
| **FoW callout when effective &lt; raw** | Matches user-visible dampening; avoids banner when scores equal despite `fog_active` | Show whenever `fog_active`: could confuse when dampener had no effect |

⚠️ **Do not fetch breakdown on component mount** — violates plan perf AC and P3-S5 latency budget work.

⚠️ **Do not duplicate scorer weights/thresholds in the frontend for routing decisions** — display copy only; source of truth is `confidence_config.py` + API payload.

⚠️ **Pass `data.event_id` from card detail, not `card_id`** — breakdown API keys on `events.id`.

**Assumptions**

- Breakdown API remains unauthenticated read (same as P3-S1g); no auth header added in client.
- Thread and Lens always have `event_id` on successful card load when card is tied to an event.
- Pulse feed does not embed `ConfidenceComposition` today — “no layout shift on Pulse” is satisfied by not adding breakdown fetch to Pulse components.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S1g** breakdown API + scorer; **P1-S10** card detail includes `event_id` and `confidence_composition` |
| **Parallel** | None |
| **Downstream** | **P3-T3** confidence verification gate; **P3-S5** SEBI audit (PRD2 UI in scope); **P3-S1l** feed FoW banner (complementary, not replaced) |

**Shared components touched**

| Component | Role |
|-----------|------|
| `ConfidenceComposition.tsx` | ICE bar + expandable breakdown panel |
| `ThreadExperience.tsx` | Passes `eventId={data.event_id}` to aside |
| `ResultCard.tsx` (Lens) | Same `eventId` wiring + existing footnote |
| `getApiBaseUrl()` (`lib/api.ts`) | Resolves `/backend` proxy vs local API origin |
| `describeHttpFailure()` | User-facing error strings for failed breakdown fetch |

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Thin API module** (`confidenceBreakdown.ts`) — types, URL builder, fetch + error class; injectable `fetchImpl` for tests.
- **Presentational subcomponents** inside `ConfidenceComposition.tsx` — `BreakdownPanel`, `BreakdownSkeleton` (no separate files; panel is story-specific).
- **Collapsible (Radix)** — same pattern as `SignalsToWatch.tsx` in Thread aside.
- **Dynamic import** unchanged in parents — `ConfidenceComposition` still loaded with `AsideBlockSkeleton` fallback.

**Database schema**

- **None** — frontend-only story.

**API contracts consumed**

| Method | Route | Auth | Client cache |
|--------|-------|------|--------------|
| GET | `/api/events/{event_id}/confidence-breakdown` | None (today) | Browser: `cache: "no-store"`; server response may include `max-age=60` |

**UI/UX decisions**

| Element | Choice |
|---------|--------|
| Trigger label | “Why this confidence tier?” with Show/Hide hint |
| Tier colours | `finnwise-blue` (high), `finnwise-amber` (medium), slate (low) — aligned with Thread dot classes |
| Input bars | Single blue fill width = normalised input `value` (0–1) |
| FoW callout | Violet bordered box — distinct from amber escalation badge |
| Escalation badge | Amber outline badge, `data-testid="confidence-escalation-badge"` |
| Source links | External `target="_blank"` + `rel="noopener noreferrer"` |

**Libraries / tools**

| Library | Purpose |
|---------|---------|
| `@/components/ui/collapsible` | Expand/collapse without layout jump in collapsed state |
| `@/components/ui/skeleton` | Loading placeholder |
| `@testing-library/react` + `userEvent` | Expand interaction tests |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `confidenceBreakdown.ts` | `frontend/lib/api/confidenceBreakdown.ts` | Typed API client + `ConfidenceBreakdownFetchError` |
| `confidenceBreakdown.test.ts` | `frontend/lib/api/confidenceBreakdown.test.ts` | URL builder, fetch happy path, 404, error class |
| `ConfidenceComposition.test.tsx` | `frontend/app/(app)/thread/_components/aside/ConfidenceComposition.test.tsx` | Expand → render fixture; 404 error state |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `ConfidenceComposition.tsx` | `frontend/app/(app)/thread/_components/aside/ConfidenceComposition.tsx` | Added optional `eventId`, collapsible breakdown panel, lazy fetch, FoW/escalation UI |
| `ThreadExperience.tsx` | `frontend/app/(app)/thread/_components/ThreadExperience.tsx` | Passes `eventId={data.event_id}` to `ConfidenceComposition` |
| `ResultCard.tsx` | `frontend/app/(app)/lens/_components/ResultCard.tsx` | Passes `eventId={data.event_id}` alongside Lens footnote |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S1h AC + tasks **9.0**–**9.6** marked complete |

**Not modified (intentionally)**

| File | Note |
|------|------|
| `backend/**` | API shipped in P3-S1g |
| Pulse components | No `ConfidenceComposition` on feed cards |
| `FogOfWarBanner.tsx` | Feed-level FoW remains **P3-S1l** |

---

### A8. TESTS EXECUTED

| Test file | Test function / group | Status | What it verifies |
|-----------|----------------------|--------|------------------|
| `confidenceBreakdown.test.ts` | `confidenceBreakdownUrl` | **Pass** | Correct `/api/events/{id}/confidence-breakdown` path |
| `confidenceBreakdown.test.ts` | `fetchConfidenceBreakdown` happy path | **Pass** | Parses payload; `cache: "no-store"` |
| `confidenceBreakdown.test.ts` | `fetchConfidenceBreakdown` 404 | **Pass** | Throws `ConfidenceBreakdownFetchError` with status 404 |
| `confidenceBreakdown.test.ts` | `ConfidenceBreakdownFetchError` | **Pass** | Error preserves HTTP status |
| `ConfidenceComposition.test.tsx` | `renders breakdown fixture after expand` | **Pass** | No fetch until click; tier, inputs, FoW, escalation badge |
| `ConfidenceComposition.test.tsx` | `shows error state on 404` | **Pass** | Error alert on failed expand fetch |

**Commands used (full frontend CI)**

```powershell
cd c:\Projects\InvestmentAssistant\frontend
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

**Result:** **130 tests passed** (52 suites), ESLint clean, `tsc --noEmit` clean, Next.js production build succeeded (31-05-2026 implementation run).

**P3-S1h–targeted commands**

```powershell
cd c:\Projects\InvestmentAssistant\frontend
pnpm exec jest confidenceBreakdown.test --no-coverage    # 4 passed
pnpm exec jest ConfidenceComposition.test --no-coverage   # 2 passed
```

**Backend:** Not run for this story (no backend diff). Regression coverage for breakdown API remains in **P3-S1g** (`test_confidence_breakdown_api.py`).

**Manual testing:** Recommended smoke test — open Thread card → expand “Why this confidence tier?” → confirm tier, scores, and sources load against live backend.

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**None.** This story is frontend-only. All persisted scores and audit rows are owned by **P3-S1g** (`events.confidence_raw`, `confidence_effective`, `confidence_score_audit`).

---

### B2. API / INTEGRATION CONTRACTS

**Consumed endpoint (implemented in P3-S1g)**

```http
GET /api/events/{event_id}/confidence-breakdown
```

**Success (200)** — fields used by UI:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "confidence_raw": 0.82,
  "confidence_effective": 0.492,
  "tier": "medium",
  "fog_active": true,
  "fog_dampener": 0.6,
  "force_editorial_review": true,
  "inputs": {
    "source_count": { "value": 0.67, "weight": 0.30, "detail": "2 sources post-dedup" },
    "source_quality": { "value": 0.80, "weight": 0.30, "detail": "primary_source=rbi_rss" },
    "factor_db_match": { "value": 1.0, "weight": 0.25, "detail": "2 factors (slug-a, slug-b)" },
    "recency": { "value": 1.0, "weight": 0.05, "detail": "first_seen=2025-06-01T10:00:00+00:00" },
    "unique_publisher": { "value": 0.67, "weight": 0.10, "detail": "2 publishers (domain-level)" }
  },
  "sources": [
    { "name": "rbi_rss", "url": "https://...", "retrieved_at": "2025-06-01T10:00:00+00:00" }
  ]
}
```

**Error (404)** — event not found; UI shows alert with parsed `detail` when JSON.

**Client URL resolution**

| Environment | Base URL used by `fetchConfidenceBreakdown` |
|-------------|---------------------------------------------|
| Local dev | `NEXT_PUBLIC_API_BASE_URL` or `http://127.0.0.1:8000` |
| Production browser | Same-origin `/backend` (proxied to Render via `app/backend/[...path]/route.ts`) |

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**UI display rules (no scoring in frontend)**

```
User opens Thread/Lens aside
├── ICE bar always visible (measured / modelled / judged from card API)
└── If eventId prop present
    └── Collapsible closed → no network
    └── User expands
        ├── loading → skeleton
        ├── GET breakdown
        │   ├── 200 → BreakdownPanel
        │   │   ├── Show tier + raw + effective
        │   │   ├── If force_editorial_review → Editorial review badge
        │   │   ├── If fog_active AND effective < raw → FoW callout
        │   │   ├── Five input bars (fixed order)
        │   │   └── sources[] with retrieved_at
        │   └── 4xx/5xx → error alert
        └── User collapses → state retained (no refetch)
```

**Input display order (fixed in UI)**

1. `source_count` (30%)  
2. `source_quality` (30%)  
3. `factor_db_match` (25%)  
4. `recency` (5%)  
5. `unique_publisher` (10%)  

Weights displayed from API payload — if P3-S1g config changes, UI stays in sync without code change.

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Impact | Future work |
|------------|--------|-------------|
| No refetch on config change mid-session | Stale breakdown until page reload | Acceptable with 60s server cache; optional manual refresh button |
| No retry button on error | User must collapse/re-expand (refetch blocked if error left breakdown null — **expand again retries** because `breakdown` still null) | Add explicit retry if UX feedback warrants |
| Tier explanation copy hardcoded in TS | Must update if PO changes thresholds in `confidence_config.py` | Consider driving copy from API `calibration_status` + threshold fields |
| Pulse feed has no breakdown UI | Users on Pulse only see direction/magnitude dots | Out of scope; may link to Thread for full explainability |
| Component test mocks `fetch` globally | Does not hit real `/backend` proxy | P3-T3 may add E2E or integration coverage |

⚠️ **Tech debt:** Threshold explanation strings in `tierExplanation()` are not generated from backend config — keep in sync manually until P3-T3 or calibration hardening.

---

### B5. TESTING NOTES

| Area | Automated | Manual |
|------|-----------|--------|
| API client URL + errors | Yes (`confidenceBreakdown.test.ts`) | — |
| Lazy fetch (no call before expand) | Yes (component test asserts `fetch` not called pre-click) | — |
| Full breakdown render | Yes (fixture assertion) | Visual check on real card |
| Production `/backend` proxy | No | Verify on Vercel preview with live API |
| Accessibility of collapsible | Partial (role=button on trigger) | Screen reader pass optional |

**Known gaps**

- No Playwright/a11y test for Thread aside expand flow yet (`tests/a11y/thread.test.tsx` does not cover breakdown panel).
- No test for empty `sources[]` or FoW inactive edge cases in component tests.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

**Environment variables**

| Variable | Required for | Notes |
|----------|--------------|-------|
| `NEXT_PUBLIC_API_BASE_URL` | Production browser | Must point to API origin; browser uses `/backend` proxy when non-loopback |
| _(none new)_ | — | No feature flags introduced |

**Deployment sequencing**

1. Deploy **backend with P3-S1g** (including migration `0027` if not already applied).
2. Deploy **frontend with P3-S1h**.
3. Verify `GET /backend/api/events/{uuid}/confidence-breakdown` returns 200 for a known event from production browser.

**No migrations, seeds, or cron jobs** for this story.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read **P3-S1g** handover doc for scorer semantics — this UI is a thin layer over that API.
2. Distinguish **ICE composition** (card) from **event tier breakdown** (routing).
3. Any change to breakdown JSON shape requires updating `ConfidenceBreakdownResponse` in `confidenceBreakdown.ts` and both test fixtures.

**Common mistakes to avoid**

- Fetching breakdown in `useEffect` on mount — breaks perf AC.
- Using `card_id` in the breakdown URL — endpoint expects `event_id`.
- Removing the ICE bar when adding scorer visuals — Lens footnote depends on current layout.
- Hardcoding weights in the UI instead of reading `input.weight` from API.

**Where to find related code**

| Concern | Path |
|---------|------|
| Breakdown API client | `frontend/lib/api/confidenceBreakdown.ts` |
| Aside UI | `frontend/app/(app)/thread/_components/aside/ConfidenceComposition.tsx` |
| Thread wiring | `frontend/app/(app)/thread/_components/ThreadExperience.tsx` |
| Lens wiring | `frontend/app/(app)/lens/_components/ResultCard.tsx` |
| Backend payload builder | `backend/app/services/confidence_scorer.py` → `build_confidence_breakdown_payload` |
| HTTP route | `backend/app/api/events.py` |

**Who to contact for context (by role)**

| Role | Context |
|------|---------|
| Backend / intelligence pipeline | Scorer weights, API shape, `force_editorial_review` rules |
| Frontend / Thread–Lens surfaces | Aside layout, dynamic imports, proxy behaviour |
| PO / calibration | Tier copy, threshold changes, explainability acceptance for P3-T3 |

---

## Quick reference — acceptance criteria mapping

| Plan AC | Implementation |
|---------|----------------|
| Thread aside loads breakdown API; 5 input bars + sources with `retrieved_at` | `BreakdownPanel` + `fetchConfidenceBreakdown` on expand |
| Shows raw, effective, tier, FoW dampener when active | Tier header + FoW callout when effective &lt; raw |
| Loading/error states; fetch on expand only | Skeleton + error alert; no fetch until collapsible open |
| `source_count > 5` → editorial escalation badge | Displays when API `force_editorial_review` is true |

---

_End of document — P3-S1h v1.0_
