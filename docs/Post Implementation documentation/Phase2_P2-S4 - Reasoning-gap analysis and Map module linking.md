# Post Implementation Detailed Document — P2-S4

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S4 (Phase 2, Story 4)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style

**P2-S2** grades each resolved prediction and writes per-card `gap_insight` text. **P2-S11** seeded The Map with three cross-sector learning modules linked to a reasoning-gap taxonomy (`direction_magnitude_mismatch`, `narrative_anchoring`, `sector_concentration`). **P2-S4** connects those pieces: it mines patterns across a user’s **graded, resolved** prediction history, surfaces up to **three** aggregate reasoning gaps in The Mirror right panel, and links each gap to a real Map module so the next reading is targeted.

The detector is **heuristic, not LLM-based** — pattern rates are computed from `mechanism_accuracy`, `business_accuracy`, and `market_accuracy` (and sector slug via instrument join). Explanations are templated plain-English sentences with counts and percentages. Users with fewer than **three** graded resolved predictions see an “insufficient history” message instead of fabricated gaps. A **Refresh** control re-runs analysis on demand; `grade_on_resolve` also calls `recompute_for_user()` after each grading batch (compute-only — no cache table).

Per-card expanded views still read **`user_predictions.gap_insight`** from P2-S2; P2-S4 additionally fills **`linked_map_module_id`** / **`linked_map_module_name`** on the predictions list when a single card’s grades match a per-prediction gap type (direction or narrative — not sector concentration).

**Tests executed and passed:** 8 pytest cases in `test_reasoning_gap_detector.py`; 3 Jest cases in `ReasoningGapPanel.test.tsx`.

**Three anchors for handover:** (1) **Minimum history gate** — fewer than 3 graded resolved rows → empty gaps + `insufficient_history: true`; (2) **Map modules must be seeded** — `resolve_module_for_gap_type()` reads `map_modules.linked_gap_types`; (3) **No persistence of aggregate gaps** — every GET/refresh recomputes from live DB state.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S4 |
| **Title** | Reasoning-gap analysis + Map module linking |
| **Category** | **Full Stack** (pattern service + Mirror API + right-panel UI + per-card Map links) |

**What this story aimed to achieve (plain language)**

Help self-aware learners see **recurring mistakes** in their prediction history — not just one-off gap text on a single card — and send them to the right **Map** module to study the fix. Gaps must come from real grade patterns (e.g. mechanism often correct while market reaction is wrong), not from a fixed list assigned to everyone.

**How it fits into the overall application**

The Mirror is designed as accountability without rupee figures. P2-S1 shows history and stats; P2-S2 produces grades and per-card gap insight; P2-S5 shows streak patterns. **P2-S4** is the bridge to **The Map** learning surface (P2-S11): aggregate “Reasoning Gap Analysis” in the right panel plus Map links on expanded cards reinforce the PRD loop *accountability → targeted learning*.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **4.1** | Gap taxonomy + labels in `reasoning_gap_map.py` (from P2-S11); three slugs with human-readable names |
| **4.2** | `reasoning_gap_detector.analyse(user_id)` — heuristic scorers + top-3 selection + Map module resolution |
| **4.3** | `GET /api/mirror/gaps` and `POST /api/mirror/gaps/refresh` |
| **4.4** | `ReasoningGapPanel` — icon, bold name (13px), explanation, `🗺 The Map: [module] →` |
| **4.5** | `GapInsightExpanded` reads `gap_insight`; list API now supplies per-card Map link when grades match |
| **4.6** | `grade_on_resolve` tail calls `recompute_for_user()` per graded user |
| **4.7** | Pytest fixture histories + API smoke; RTL panel render + refresh |

**Functional breakdown — aggregate panel**

```
User opens /mirror
│
├─ MirrorClient GET /api/mirror/gaps (parallel with stats, predictions, streak)
│
└─ reasoning_gap_detector.analyse_with_meta(user_id)
      ├─ fetch_graded_resolved_predictions (≤50 rows, resolved cards, mechanism_accuracy NOT NULL)
      ├─ if count < 3 → items=[], insufficient_history=true
      ├─ score_gap_types() → ranked GapTypeScore list
      ├─ take top 3
      └─ resolve_module_for_gap_type() per gap → ReasoningGap with module id + title
```

**Functional breakdown — per-card Map link**

```
list_predictions() for each row:
  infer_gap_type_for_prediction(mech, biz, market)
    → direction_magnitude_mismatch | narrative_anchoring | None
  resolve_module_for_gap_type(slug) → linked_map_module_id, linked_map_module_name
```

**Gap taxonomy and detection rules**

| Gap slug | Display name | Pattern rule | Min rate |
|----------|--------------|--------------|----------|
| `direction_magnitude_mismatch` | Direction-correct, magnitude-wrong | mechanism `correct` AND market `partial`/`incorrect` | ≥ 25% of eligible rows (both levels graded) |
| `narrative_anchoring` | Anchored on narrative | business `correct` AND mechanism `partial`/`incorrect` | ≥ 25% of eligible rows |
| `sector_concentration` | Sector concentration in your predictions | One sector ≥ 60% of rows with known `sector_slug` | ≥ 3 rows with sector |

Sector slug comes from the first `instrument_assessments` row on the card (ticker → NSE `instruments` → `sectors.slug`).

**Edge cases and error handling**

| Case | Behaviour |
|------|-----------|
| &lt; 3 graded resolved predictions | `items: []`, `insufficient_history: true`, panel copy explains threshold |
| ≥ 3 predictions but no pattern ≥ threshold | `insufficient_history: false`, `items: []`, “no strong patterns yet” copy |
| Map module missing for gap type | Gap omitted from response (scorer ran but link failed) |
| `SUPABASE_DB_URL` missing | HTTP 503 `db_unavailable` |
| Unauthenticated request | 401 via `CurrentUser` |
| Card has no instrument assessment | `sector_slug` null; row excluded from sector concentration numerator |
| `monitoring` grades | Excluded from pattern rate denominators (only `correct`/`partial`/`incorrect`) |

**Business rules enforced**

- PRD §5 Screen 4: three gap items max; icon + Inter 13px bold name + explanation + Map link.
- Gaps derived from history, not manually assigned per user.
- Per-card `gap_insight` remains LLM-authored (P2-S2); aggregate explanations are template-based.
- Map links use `/map?module={uuid}` (index page redirects to sector URL when `sector_slug` is set on module).
- No rupee figures on Mirror (unchanged).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Heuristics over LLM for aggregate gaps** | Predictable, testable, no extra API cost; per-card gap insight already uses LLM (P2-S2) |
| **No `user_reasoning_gaps` cache table** | Simpler ops; recompute on read/refresh/grade is fast at ≤50 rows |
| **MIN_GRADED_RESOLVED = 3** | Plan risk note: suppress trivial gaps when history is thin |
| **MIN_PATTERN_RATE = 0.25** | Avoid surfacing noise from one-off mismatches |
| **Sector via first instrument on card** | Reuses existing card→instrument graph; no new schema |
| **Per-card link excludes sector_concentration** | Concentration is a portfolio-level pattern, not a single-prediction grade signature |
| **Separate `mirror_gaps` router** | Matches plan file layout; mounted at `/api` like `mirror_streak` |
| **POST `/gaps/refresh` same body as GET** | Explicit “Refresh analysis” affordance; both recompute (no stale cache) |

⚠️ **Do not lower `MIN_GRADED_RESOLVED` without PO sign-off** — the panel is intentionally hidden for thin histories to avoid trivial or misleading gaps.

⚠️ **Do not assign gap types manually in API responses** — all items must flow through `score_gap_types()` + module resolution.

⚠️ **Map module seeds are required** — without `apply_all_factor_db_seeds()` / `map_modules.sql`, gaps may compute but return fewer items when `resolve_module_for_gap_type` returns `None`.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories / artifacts |
|-----------|---------------------|
| **Upstream** | **P2-S2** (`mechanism_accuracy`, `business_accuracy`, `market_accuracy`, `gap_insight`); **P2-S11** (`map_modules`, `reasoning_gap_map.py`, seeds); **P2-S1** (Mirror layout, `GapInsightExpanded` slot, predictions API) |
| **Downstream** | None hard-dependent; learners use Map modules for study; stats strip `reasoning_gaps_found` remains P2-S1 proxy logic (not replaced) |
| **Parallel** | P2-S5 (Streak Tracker panel below Reasoning Gap Analysis in aside) |
| **Shared** | `user_predictions`, `map_modules`, `instrument_assessments`, `MirrorClient`, `frontend/lib/mirror/types.ts` |

---

### A5. DESIGN CHOICES

**Architecture**

- Pure scoring in `reasoning_gap_detector.py`; thin HTTP in `mirror_gaps.py`.
- Taxonomy and DB module lookup in `reasoning_gap_map.py` (P2-S11).
- UI: `ReasoningGapPanel` between `ReadyToGradePanel` and `StreakTrackerPanel`.

**Database**

- **No new migration for P2-S4.** Reads existing columns and `map_modules` (migration `0018`).

**API**

| Method | Route | Auth | Purpose |
|--------|-------|------|---------|
| GET | `/api/mirror/gaps` | Bearer JWT | Top-3 gaps + `insufficient_history` |
| POST | `/api/mirror/gaps/refresh` | Bearer JWT | Same as GET (on-demand recompute) |

**UI/UX**

- Panel title: DM Mono 10px uppercase “Reasoning gap analysis”.
- Gap name: Inter 13px **bold**; explanation 12px slate-600.
- Icons: coloured 36×36 box (sky / amber / violet) with Lucide `Compass` / `Layers`.
- Refresh: ghost button with spinning `RefreshCw` while POST in flight.
- Map link: `🗺 The Map: {module title} →` → `/map?module={id}`.

**Libraries**

- No new npm or pip dependencies.

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| reasoning_gap_detector.py | `backend/app/services/reasoning_gap_detector.py` | Pattern scoring, history fetch, `analyse()` / `analyse_with_meta()` |
| mirror_gaps.py | `backend/app/api/mirror_gaps.py` | `GET`/`POST` Mirror gaps routes |
| test_reasoning_gap_detector.py | `backend/tests/test_reasoning_gap_detector.py` | Pytest for scorers, API, module linking |
| ReasoningGapPanel.tsx | `frontend/app/(app)/mirror/_components/ReasoningGapPanel.tsx` | Right-panel aggregate gap UI |
| ReasoningGapPanel.test.tsx | `frontend/app/(app)/mirror/_components/ReasoningGapPanel.test.tsx` | RTL tests for render, empty state, refresh |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| main.py | `backend/app/main.py` | Register `mirror_gaps_router` |
| mirror_predictions.py | `backend/app/services/mirror_predictions.py` | `_linked_map_fields()`; populate `linked_map_module_*` on list rows |
| grade_on_resolve.py | `backend/app/jobs/grade_on_resolve.py` | Call `recompute_for_user()` after commit for each graded user |
| MirrorClient.tsx | `frontend/app/(app)/mirror/_components/MirrorClient.tsx` | Fetch gaps; render `ReasoningGapPanel`; refresh handler |
| mirrorServer.ts | `frontend/lib/api/mirrorServer.ts` | Include `/api/mirror/gaps` in SSR initial payload |
| types.ts | `frontend/lib/mirror/types.ts` | `MirrorReasoningGap`, `MirrorReasoningGapsResponse` |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S4 acceptance + tasks marked complete |

**Not modified (pre-existing, consumed by P2-S4)**

| File | Role |
|------|------|
| `backend/app/services/reasoning_gap_map.py` | Taxonomy labels + `resolve_module_for_gap_type()` (P2-S11) |
| `frontend/app/(app)/mirror/_components/GapInsightExpanded.tsx` | Per-card `gap_insight` + Map link (P2-S1 slot) |
| `backend/db/seeds/map_modules.sql` | Three reasoning-gap modules with fixed UUIDs |

---

### A8. TESTS EXECUTED

| Test file | Status | What it covers |
|-----------|--------|----------------|
| `test_reasoning_gap_detector.py` | **Passed (8)** | Insufficient history; three pattern scorers; per-prediction infer; API GET/POST; module name linkage with seeds |
| `ReasoningGapPanel.test.tsx` | **Passed (3)** | Three items + Map hrefs; insufficient empty state; refresh callback |

**Backend command**

```bash
cd backend
python -m pytest tests/test_reasoning_gap_detector.py -q
```

**Result:** 8 passed

**Frontend command**

```bash
cd frontend
pnpm exec jest ReasoningGapPanel.test
```

**Result:** 3 passed

| Test name | Layer | Assertion |
|-----------|-------|-----------|
| `test_insufficient_history_returns_empty` | Backend | &lt; 3 rows → `analyse_from_history` returns `[]` |
| `test_direction_magnitude_pattern_surfaces` | Backend | Top scorer is `direction_magnitude_mismatch` with explanation text |
| `test_narrative_anchoring_pattern_surfaces` | Backend | Narrative gap appears in scored types |
| `test_sector_concentration_pattern_surfaces` | Backend | Sector gap when 75% banking |
| `test_infer_per_prediction_gap_type` | Backend | Grade tuple → slug mapping |
| `test_mirror_gaps_api_insufficient_history` | Backend | HTTP 200, empty items, `insufficient_history: true` |
| `test_mirror_gaps_refresh_endpoint` | Backend | POST refresh returns 200 + `items` key |
| `test_analyse_from_history_links_map_module_names` | Backend | Seeded DB → gap has module id + title |
| `renders three gap items with Map links` | Frontend | Three links; correct `/map?module=…` href |
| `suppresses items when history is insufficient` | Frontend | `reasoning-gap-empty` testid |
| `calls onRefresh when Refresh is clicked` | Frontend | `onRefresh` invoked once |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**No schema changes in P2-S4.**

**Tables read**

| Table | Usage |
|-------|--------|
| `user_predictions` | `mechanism_accuracy`, `business_accuracy`, `market_accuracy` |
| `cards` | Filter `lifecycle_state = 'resolved'` |
| `instrument_assessments` | First instrument per card for sector |
| `instruments` | Ticker join (`exchange = 'NSE'`) |
| `sectors` | `slug` for concentration |
| `map_modules` | `linked_gap_types` GIN lookup for module id/title |

**Seeds required (P2-S11, not auto-run with migrate)**

`backend/db/seeds/map_modules.sql` inserts three modules:

| UUID (prefix) | Title | `linked_gap_types` |
|---------------|-------|-------------------|
| `a1000001-…-000001` | Direction vs magnitude | `direction_magnitude_mismatch` |
| `a1000001-…-000002` | Narrative vs mechanism | `narrative_anchoring` |
| `a1000001-…-000003` | Sector concentration | `sector_concentration` |

---

### B2. API / INTEGRATION CONTRACTS

**Endpoint:** `GET /api/mirror/gaps`  
**Endpoint:** `POST /api/mirror/gaps/refresh`

**Auth:** `Authorization: Bearer <supabase_access_token>`

**Response 200 (example — patterns found)**

```json
{
  "items": [
    {
      "gap_type": "direction_magnitude_mismatch",
      "gap_name": "Direction-correct, magnitude-wrong",
      "pattern_explanation": "In 4 of your last 6 resolved predictions (67%), mechanism was correct but market reaction was partial or incorrect — you are reading the transmission chain but mis-sizing how prices react.",
      "linked_map_module_id": "a1000001-0001-4000-8000-000000000001",
      "linked_map_module_name": "Direction vs magnitude"
    }
  ],
  "insufficient_history": false
}
```

**Response 200 (insufficient history)**

```json
{
  "items": [],
  "insufficient_history": true
}
```

`items` length is **0–3**.

**Errors**

| Status | When |
|--------|------|
| 401 | Missing/invalid JWT |
| 503 | `SUPABASE_DB_URL` not configured or DB unreachable |

**Predictions list (P2-S1, extended by P2-S4)**

`GET /api/mirror/predictions` items may include:

```json
{
  "gap_insight": "You underweighted the duration channel…",
  "linked_map_module_id": "a1000001-0001-4000-8000-000000000001",
  "linked_map_module_name": "Direction vs magnitude"
}
```

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Scoring pipeline**

```
fetch_graded_resolved_predictions(user_id)  [max 50, resolved, graded]
        │
        ▼
count < 3? ──yes──► return [], insufficient_history=true
        │
        no
        ▼
score_gap_types(rows)
  ├─ direction_magnitude (rate ≥ 0.25)
  ├─ narrative_anchoring (rate ≥ 0.25)
  └─ sector_concentration (share ≥ 0.60, ≥3 sector rows)
        │
        ▼
sort by (-score, gap_type) → [:3]
        │
        ▼
for each: resolve_module_for_gap_type → ReasoningGap
```

**Per-prediction infer (expanded card only)**

```
mechanism correct + market partial|incorrect → direction_magnitude_mismatch
business correct + mechanism partial|incorrect → narrative_anchoring
else → no module link
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **Template explanations only (aggregate)** | Not personalised LLM copy; may feel repetitive vs per-card `gap_insight` |
| **Sector slug coverage** | Cards without `instrument_assessments` weaken sector concentration detection |
| **No persisted gap snapshot** | Historical “what we told you last week” not stored; refresh always reflects current DB |
| **`reasoning_gaps_found` stat unchanged** | Stats strip still uses P2-S1 proxy (gap_insight or partial/incorrect levels), not aggregate panel count |
| **GET and POST refresh identical** | No cache invalidation semantics differ between them |
| **Client fetch for gaps** | Included in SSR initial payload via `mirrorServer.ts`; client refresh uses POST |

---

### B5. TESTING NOTES

| Area | Automated | Manual (recommended) |
|------|-----------|----------------------|
| Pattern thresholds | Yes (pytest fixtures) | — |
| Insufficient history UI | Yes (RTL) | Sign in with &lt; 3 graded resolves |
| Map link navigation | Partial (href assert) | Click link → Map module highlight / redirect |
| Post-grade recompute | No integration test | Resolve card with predictions → reopen Mirror |
| Module seed missing | Partial (integration uses seeds) | Staging DB without seeds → empty module links |

**Manual smoke**

1. Ensure `apply_all_factor_db_seeds()` has run on the DB.
2. Sign in with a user who has ≥ 3 resolved, graded predictions.
3. Open `/mirror` → confirm **Reasoning gap analysis** panel between Ready to Grade and Streak tracker.
4. Click **Refresh** → network shows `POST /api/mirror/gaps/refresh`.
5. Expand a card with mechanism correct + market wrong → Map link under gap insight.
6. Click `🗺 The Map: …` → lands on Map with module context.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Item | Required for P2-S4? |
|------|---------------------|
| New env vars | **No** |
| New DB migration | **No** |
| `SUPABASE_DB_URL` | **Yes** (backend) |
| `GEMINI_API_KEY` | **No** (aggregate gaps do not call LLM) |
| Map module seeds | **Yes** (once per environment) |

**Deployment sequencing**

1. Migrations `0014` + `0018` applied (if not already from P2-S2 / P2-S11).
2. Run `apply_all_factor_db_seeds()` so `map_modules` reasoning-gap rows exist.
3. Deploy backend (new `/api/mirror/gaps` routes).
4. Deploy frontend (`ReasoningGapPanel` + initial gaps fetch).
5. Restart local API if it was running before router registration.

**Operator one-liner (seeds)**

```python
from app.db.connection import connection
from app.db.seeds import apply_all_factor_db_seeds
with connection() as conn:
    apply_all_factor_db_seeds(conn)
    conn.commit()
```

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing gap detection**

1. Read PRD §5 Screen 4 — Reasoning Gap Analysis Panel row.
2. Read `backend/app/services/reasoning_gap_detector.py` — all thresholds live as module constants.
3. Read `backend/app/services/reasoning_gap_map.py` — taxonomy slugs must match `map_modules.linked_gap_types`.

**Common mistakes**

- Adding LLM calls to aggregate gaps without PO approval (cost + testability).
- Using `event_category` instead of instrument sector for concentration (wrong signal).
- Linking sector concentration on single-card expand (not supported by `infer_gap_type_for_prediction`).
- Expecting gaps before P2-S2 grades exist (`mechanism_accuracy IS NULL` rows excluded).

**Related code paths**

| Concern | Path |
|---------|------|
| Scoring logic | `backend/app/services/reasoning_gap_detector.py` |
| Taxonomy + module lookup | `backend/app/services/reasoning_gap_map.py` |
| Gaps API | `backend/app/api/mirror_gaps.py` |
| Post-grade hook | `backend/app/jobs/grade_on_resolve.py` |
| Per-card Map fields | `backend/app/services/mirror_predictions.py` |
| Panel UI | `frontend/app/(app)/mirror/_components/ReasoningGapPanel.tsx` |
| Per-card insight UI | `frontend/app/(app)/mirror/_components/GapInsightExpanded.tsx` |
| Data load | `frontend/app/(app)/mirror/_components/MirrorClient.tsx` |
| Map seeds | `backend/db/seeds/map_modules.sql` |

**Contact (by role):** Riley (gaps + Map linkage) / Jordan (grading data) / Sam (Mirror UI) per phase-2 team plan.
