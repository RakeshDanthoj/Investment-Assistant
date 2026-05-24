# Post Implementation Detailed Document — P2-S11

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S11 (Phase 2, Story 11)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style (read this first)

**Phase 1 (P1-S5)** seeded the Factor Exposure DB for **Banking** only: eight macro factors (PRD §7.1), NSE instruments, and sensitivity cells that always carry an **MMJ tag** and **source URL**. **P2-S11** expands that data layer to **seven additional sectors** (120 NSE instruments total across all eight sectors) and ships **The Map** — a Portfolio Builder learning surface at `/(app)/map` with sector cover tiles, per-sector “How this sector reacts to events” modules, and a preview of the factor sensitivity matrix.

The backend adds **`map_modules`** (migration `0018`), authenticated Map APIs under `/api/map`, and **`reasoning_gap_map`** — a gap-type → module resolver that **P2-S4** will consume when Reasoning Gap Analysis links Mirror predictions to targeted reading. The frontend replaces the Map placeholder with an SSR index page and a sector detail route that highlights modules when deep-linked via `?module=`.

**Tests executed and passed:**

| Suite | Command | Result |
|-------|---------|--------|
| Backend | `python -m pytest tests/test_factor_db_coverage.py tests/test_map_api.py tests/test_factor_db_seed.py -q` | **7 passed** |

**Three anchors:** (1) **≥120 instruments × 8 factors**, every cell MMJ + source URL; (2) **`map_modules`** + sector seeds are **manual one-time** DB steps (not on app startup); (3) **gap-type cross-links** are seeded and exposed via API — Mirror UI wiring is **P2-S4**, not this story.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S11 |
| **Title** | Factor DB expansion to all 8 sectors + The Map content |
| **Category** | **Full Stack** (DB seeds, migration, APIs, Map UI, coverage tests) |

**What this story aimed to achieve (plain language)**

Portfolio Builders need to understand how Indian equity sectors respond to macro and policy events **before** they trade the live Pulse feed. This story fills the Factor DB for IT, Energy, FMCG, Auto, Pharma, Metals, Telecom, and Infra (banking was already done), and builds The Map so users can browse sectors, read reaction guides, and inspect factor sensitivities. It also prepares **reasoning-gap → Map module** links so P2-S4 can route learners to the right content.

**How it fits into the overall application**

- **Upstream:** **P1-S5** (Factor DB schema, banking seed, `factor_db` service, MMJ invariant).
- **Parallel:** **P2-S2** (grading), **P2-S4** (gap analysis — consumes Map modules), **P2-S9** (holdings).
- **Downstream:** **P2-S4** (Reasoning Gap panel + Map links in Mirror), **P2-S15** (Lighthouse budgets for Map), Lens/card pipeline (already reads Factor DB for banking context).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **11.1** | Seven sector SQL seeds under `backend/db/seeds/sectors/` (15 NSE tickers each); banking remains `banking_sector.sql`. |
| **11.2** | Migration `0018_map_modules.sql` + `map_modules.sql` seed — per-sector reaction bodies + three global gap modules with `linked_gap_types`. |
| **11.3** | `GET /api/map/sectors`, `GET /api/map/sectors/{slug}`, `GET /api/map/modules/by-gap-type`, `GET /api/map/modules/{id}`. |
| **11.4** | `/(app)/map` — `SectorTile` grid; highlights cross-sector gap module when `?module=` is set. |
| **11.5** | `/(app)/map/[slug]` — `MapModule` list + `SensitivityMatrix` preview (12 tickers). |
| **11.6** | `reasoning_gap_map.py` + gap modules seeded with slugs `direction_magnitude_mismatch`, `narrative_anchoring`, `sector_concentration`. |
| **11.7** | `test_factor_db_coverage.py`, `test_map_api.py`; existing `test_factor_db_seed.py` still passes. |

**Functional breakdown**

1. Operator applies migration `0018` and runs `apply_all_factor_db_seeds()` once per database.
2. Signed-in user opens `/map` → server fetches sector list → tiles link to `/map/{slug}`.
3. User opens a sector → sees “How {sector} reacts to events” module(s) + sensitivity table (subset of instruments).
4. Deep link `/map?module={uuid}` loads gap module on index, or redirects to `/map/{sector}?module={uuid}` when module is sector-scoped.
5. P2-S4 (future) calls `/api/map/modules/by-gap-type` or `resolve_module_for_gap_type()` to attach `linked_map_module_id` on Mirror predictions.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Not signed in | Map pages show “Sign in to explore The Map.” (no API call). |
| Unknown sector slug | `GET /api/map/sectors/{slug}` → **404**; Next.js `notFound()`. |
| Unknown module id | `GET /api/map/modules/{id}` → **404**. |
| `by-gap-type` with no query params | Returns modules for **all three** gap types in taxonomy. |
| Route order for `by-gap-type` vs `{id}` | `by-gap-type` registered **before** `{module_id}` to avoid UUID parse errors. |
| DB unavailable | **503** `Database is not configured` (same pattern as Mirror/Factor DB). |
| Re-run seeds | Idempotent `ON CONFLICT` on instruments and sensitivities; map modules use fixed UUIDs. |
| TestClient vs fixture connection | Integration tests **`commit()`** after seeds so API pool sees data. |

**Business rules enforced**

- **Eight macro factors** per PRD §7.1 — shared `factors` table; not duplicated per sector.
- **Sensitivity range** −5…+5; **MMJ tag** and **non-empty source_url** on every cell (Phase 1 invariant).
- **≥120 NSE instruments** with full 8-factor grid across all sectors (15 banking + 7×15 others).
- **Evidence freshness** on matrix preview uses same `freshness_for_retrieved_at()` as P1-S5 (green ≤6mo, amber 6–18mo, red >18mo).
- **Matrix preview cap** — sector detail API returns at most **12** instruments in the table (full count in `instrument_count`).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Migration `0018` not `0015`** | `0015`–`0017` already used (`notifications`, `lens_queries`, `user_email_preferences`, etc.). | Renumbering applied migrations: unsafe on shared DBs. |
| **Sector seeds as SQL files** | Matches P1-S5 `banking_sector.sql` pattern; easy diff/review. | Python-only seeding at runtime: harder to audit in PR. |
| **`generate_sector_seeds.py`** | Deterministic sensitivities from ticker×factor hash; keeps 7 files maintainable. | Hand-authored 2k+ lines per sector: error-prone. |
| **Fixed UUIDs for `map_modules`** | Idempotent upsert on re-seed; stable links for P2-S4/tests. | Random UUIDs each seed run: breaks deep links. |
| **Reuse `factor_db.fetch_matrix_rows()`** | Single matrix builder; Map detail is a thin wrapper + preview limit. | Duplicate SQL in `map_content`: DRY violation. |
| **Map APIs require JWT** | Consistent with Factor DB sensitivity lookup and Mirror. | Public Map: product wanted authenticated Portfolio Builder surface. |
| **Gap modules `sector_slug = null`** | Cross-cutting learning content; sector modules stay per-slug. | One module per sector per gap type: 24 rows, harder to maintain. |
| **Deep link `/map?module=`** | Matches existing `GapInsightExpanded` href pattern from P2-S1 slot. | Only slug routes: breaks Mirror placeholder links until P2-S4. |

⚠️ **Do not run seeds without committing** when testing via HTTP — TestClient uses a separate connection pool; uncommitted fixture data causes “only banking” or 503 symptoms.

⚠️ **Do not register `/modules/{id}` before `/modules/by-gap-type`** — FastAPI will treat `by-gap-type` as a UUID path param.

⚠️ **Do not skip `apply_all_factor_db_seeds()` in production** — Map UI and coverage tests expect all eight sectors; banking alone shows one tile.

**Assumptions**

- Top-150 NSE coverage is approximated by **15 liquid names per sector** (120 total), not a live NSE index API.
- Sensitivity values in new sectors are **seed-quality** (deterministic placeholders with real government/source URLs), not analyst-curated like banking.
- P2-S4 will adopt gap slugs defined in `reasoning_gap_map.ALL_GAP_TYPES` without renaming.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1-S5** — `sectors`, `factors`, `instruments`, `instrument_factor_sensitivity`, `factor_db` service, banking seed. |
| **Enables** | **P2-S4** — reasoning gaps link to `map_modules.id`; **P2-S15** — Lighthouse/perf for `/map`; card/Lens pipeline can reference non-banking sectors once prompts expand. |
| **Parallel** | **P2-S2**, **P2-S9** — no hard dependency; Factor DB used optionally by card pipeline today (banking). |
| **Shared** | `public.sectors`, `public.factors`, `instrument_factor_sensitivity`, Supabase JWT (`get_current_user`), PRD §7.1 factor slugs. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | SQL seeds + thin services (`map_content`, `reasoning_gap_map`) + FastAPI router; SSR pages + small client components for highlight/query params. |
| **Schema** | `map_modules(id, sector_slug → sectors.slug, title, body, linked_gap_types[], sort_order)`; RLS enabled, no anon policies (service role / app connection). |
| **API auth** | Bearer JWT on all `/api/map/*` routes. |
| **UI** | Sector tiles with gradient accents per slug; matrix table with freshness dots; module cards with optional highlight ring. |
| **Libraries** | No new npm/pip dependencies; reuses existing `factor_db`, Supabase server client, shadcn `Skeleton`. |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| 0018_map_modules.sql | `backend/db/migrations/0018_map_modules.sql` | `map_modules` table + indexes |
| it.sql … infra.sql | `backend/db/seeds/sectors/*.sql` (8 files) | Per-sector instruments + sensitivities |
| map_modules.sql | `backend/db/seeds/map_modules.sql` | Sector reaction + gap modules |
| generate_sector_seeds.py | `backend/scripts/generate_sector_seeds.py` | Regenerate sector SQL from ticker lists |
| map_content.py | `backend/app/services/map_content.py` | Sector list, detail, module-by-id |
| reasoning_gap_map.py | `backend/app/services/reasoning_gap_map.py` | Gap taxonomy + resolver for P2-S4 |
| map.py | `backend/app/api/map.py` | HTTP routes |
| test_factor_db_coverage.py | `backend/tests/test_factor_db_coverage.py` | ≥120 instruments × 8 factors |
| test_map_api.py | `backend/tests/test_map_api.py` | Map API + gap-type links |
| types.ts | `frontend/lib/map/types.ts` | Map TypeScript contracts |
| mapServer.ts | `frontend/lib/api/mapServer.ts` | Server-side fetch helpers |
| page.tsx | `frontend/app/(app)/map/page.tsx` | Map index (replaces placeholder) |
| [slug]/page.tsx | `frontend/app/(app)/map/[slug]/page.tsx` | Sector detail |
| MapIndexClient.tsx | `frontend/app/(app)/map/_components/MapIndexClient.tsx` | Tile grid + highlighted module |
| MapSectorClient.tsx | `frontend/app/(app)/map/_components/MapSectorClient.tsx` | Modules + matrix on detail |
| SectorTile.tsx | `frontend/app/(app)/map/_components/SectorTile.tsx` | Cover tile |
| MapModule.tsx | `frontend/app/(app)/map/_components/MapModule.tsx` | Module renderer |
| SensitivityMatrix.tsx | `frontend/app/(app)/map/_components/SensitivityMatrix.tsx` | Factor grid preview |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| seeds.py | `backend/app/db/seeds.py` | `apply_phase2_sector_seeds`, `apply_map_modules_seed`, `apply_all_factor_db_seeds` |
| migrate.py | `backend/app/db/migrate.py` | Register `0018_map_modules.sql` |
| main.py | `backend/app/main.py` | `include_router(map_router)` |
| page.tsx (placeholder) | `frontend/app/(app)/map/page.tsx` | Replaced “Phase 2 surface” stub with full index |
| finnwise-phase2-implementation-tasks.md | `docs/plans/finnwise-phase2-implementation-tasks.md` | P2-S11 acceptance + tasks marked complete |

---

### A8. TESTS EXECUTED

| Test file | Status | What it covers |
|-----------|--------|----------------|
| `test_factor_db_coverage.py` | **Passed (2)** | ≥8 sectors; ≥120 NSE instruments each with 8 factors; no null MMJ/empty source URL |
| `test_map_api.py` | **Passed (3)** | Sector list includes banking + IT; banking detail has modules + matrix; each gap type resolves to one module |
| `test_factor_db_seed.py` | **Passed (2)** | Banking-only regression: 15 banks, 8 factors per instrument, MMJ invariant |

**Backend command**

```text
cd backend
python -m pytest tests/test_factor_db_coverage.py tests/test_map_api.py tests/test_factor_db_seed.py -q
```

→ **7 passed** (executed 24-05-2026)

**Frontend automated tests**

None added in P2-S11 (Map UI not in Jest scope for this story). Manual verification of `/map` and `/map/banking` recommended before tester handoff.

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**Existing tables used (P1-S5):** `sectors`, `factors`, `instruments`, `instrument_factor_sensitivity`

**New table:** `public.map_modules`

| Column | Type | Notes |
|--------|------|--------|
| `id` | `uuid` PK | Fixed UUIDs in seed for idempotency |
| `sector_slug` | `text` FK → `sectors.slug` | `NULL` for cross-sector gap modules |
| `title` | `text` | Display title |
| `body` | `text` | Learning copy (plain text) |
| `linked_gap_types` | `text[]` | GIN index; empty `{}` for sector reaction modules |
| `sort_order` | `smallint` | Display order |
| `created_at` | `timestamptz` | Default `now()` |

**Seed inventory**

| Category | Count | Notes |
|----------|-------|--------|
| Sectors | 8 slugs | `banking` + 7 new |
| Instruments | 120 | 15 per sector, NSE |
| Sensitivity cells | 960 | 120 × 8 |
| Sector reaction modules | 9 | One per sector slug |
| Gap modules | 3 | One per P2-S4 gap type |

**Migration sequence:** Apply after `0017_user_email_preferences.sql` (and any other pending `0017_*` files your environment tracks). Registered name: **`0018_map_modules.sql`**.

---

### B2. API / INTEGRATION CONTRACTS

| Method | Route | Auth | Purpose |
|--------|-------|------|---------|
| GET | `/api/map/sectors` | Bearer | Sector index + instrument counts + `cover_accent` |
| GET | `/api/map/sectors/{slug}` | Bearer | Sector detail: modules, factors, matrix preview |
| GET | `/api/map/modules/by-gap-type?gap_type=` | Bearer | Resolve modules for gap slug(s); omit param = all types |
| GET | `/api/map/modules/{module_id}` | Bearer | Single module (deep links) |

**Sector list response (abbreviated)**

```json
{
  "sectors": [
    {
      "slug": "banking",
      "name": "Banking & Financial Services",
      "instrument_count": 15,
      "cover_accent": "sky"
    }
  ]
}
```

**Gap-type link response (abbreviated)**

```json
{
  "items": [
    {
      "gap_type": "narrative_anchoring",
      "gap_label": "Anchored on narrative",
      "module": {
        "id": "a1000001-0001-4000-8000-000000000002",
        "title": "Narrative vs mechanism",
        "sector_slug": null,
        "href": "/map?module=a1000001-0001-4000-8000-000000000002"
      }
    }
  ]
}
```

**Gap type slugs (P2-S4 contract)**

| Slug | Label |
|------|--------|
| `direction_magnitude_mismatch` | Direction-correct, magnitude-wrong |
| `narrative_anchoring` | Anchored on narrative |
| `sector_concentration` | Sector concentration in your predictions |

---

### B3. BUSINESS LOGIC & RULES (Detailed)

```
Operator
  → apply_migrations (includes 0018)
  → apply_all_factor_db_seeds()
  → commit

User (authenticated)
  → GET /api/map/sectors
  → pick slug
  → GET /api/map/sectors/{slug}
       → factor_db.fetch_matrix_rows(slug)
       → truncate instruments to 12 for UI
       → attach map_modules for sector_slug

Deep link
  → /map?module={id}
       → GET /api/map/modules/{id}
       → if sector_slug set → redirect /map/{sector_slug}?module={id}
       → else show module on index (gap content)

P2-S4 (future)
  → reasoning_gap_detector.analyse(user)
  → resolve_module_for_gap_type(slug)
  → populate linked_map_module_id on Mirror prediction / gap panel
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Notes |
|------------|--------|
| **Seeds not auto-applied** | Unlike migrations, seeds require explicit `apply_all_factor_db_seeds()` — no CLI wrapper in repo yet. |
| **Sensitivity data quality** | New sectors use deterministic placeholder scores; banking seed remains the curated reference. |
| **No frontend unit tests** | Map components untested in Jest; rely on API tests + manual QA. |
| **Matrix preview only** | Detail page shows 12 of N tickers; full matrix still behind admin `/api/factor-db/matrix`. |
| **P2-S4 not implemented** | Gap modules exist; Mirror `ReasoningGapPanel` and `linked_map_module_*` population still pending. |
| **Duplicate `0017_*` migration files in tree** | `0017_saved_threads.sql` exists on disk but is not in `MIGRATION_FILES` until that story lands — do not confuse with `0018`. |

---

### B5. TESTING NOTES

| Type | Covered |
|------|---------|
| **Automated** | Full DB seed coverage count; MMJ/source invariant; Map API shapes; gap-type resolution; banking regression |
| **Manual** | Sign-in → `/map` eight tiles → sector page modules + table; `?module=` highlight; redirect to sector when module is sector-scoped |
| **Gaps** | No Playwright E2E; no Lighthouse run for Map (deferred to **P2-S15**) |

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required for P2-S11 |
|----------|---------------------|
| `SUPABASE_DB_URL` | **Yes** — migrations + seeds + Map APIs |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` | **Yes** — JWT on Map routes |
| `NEXT_PUBLIC_API_BASE_URL` | **Yes** — frontend server fetch to backend |

No new environment variables were introduced.

**Deployment sequencing (per environment)**

1. Deploy backend + frontend code.
2. `python scripts/apply_migrations.py`
3. Run seed script (see manual checklist below).
4. Restart services.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing this code**

1. Read **P1-S5** `factor_db.py` — Map detail delegates matrix building there.
2. Read **`reasoning_gap_map.py`** before implementing **P2-S4** — use the same gap slugs.
3. Regenerating sector SQL: `python backend/scripts/generate_sector_seeds.py` then re-run seeds.

**Key paths**

| Concern | Path |
|---------|------|
| Map business logic | `backend/app/services/map_content.py` |
| Gap resolver | `backend/app/services/reasoning_gap_map.py` |
| Routes | `backend/app/api/map.py` |
| Seeds | `backend/app/db/seeds.py`, `backend/db/seeds/sectors/`, `map_modules.sql` |
| Map UI | `frontend/app/(app)/map/` |
| Types | `frontend/lib/map/types.ts` |

**Common mistakes**

- Forgetting to **commit** after seeds when debugging API tests.
- Adding sector tickers that already exist under another sector — `ON CONFLICT` moves `sector_id`, which can surprise counts.
- Changing gap slugs without updating `map_modules.sql` and P2-S4 detector together.

**Contact by role:** Riley — Factor DB + Map content; Sam — Map UI; Jordan — downstream Lens/card if sector context expands.

---

## Manual verification checklist (operator)

### 1. Apply database migration (one-time per environment)

```text
pip install -e "./backend[dev]"
python scripts/apply_migrations.py
```

Confirm:

```sql
SELECT filename FROM public.schema_migrations
WHERE filename = '0018_map_modules.sql';
```

### 2. Apply Factor DB + Map seeds (one-time per environment)

From repo root:

```text
cd backend
python -c "
import psycopg
from app.core.settings import get_settings
from app.db.seeds import apply_all_factor_db_seeds
with psycopg.connect(get_settings().supabase_db_url) as conn:
    apply_all_factor_db_seeds(conn)
    conn.commit()
print('Seeds applied.')
"
```

Confirm coverage:

```sql
SELECT count(DISTINCT i.id) FROM public.instruments i
JOIN public.instrument_factor_sensitivity s ON s.instrument_id = i.id
WHERE upper(i.exchange) = 'NSE'
GROUP BY i.id HAVING count(DISTINCT s.factor_id) = 8;
-- expect ≥ 120 rows from the outer count
```

### 3. Sign in and open The Map

1. Backend: `uvicorn app.main:app --reload --port 8000`
2. Frontend: `npm run dev` in `frontend/`
3. Sign in via magic link
4. Open `http://localhost:3000/map` — expect **8 sector tiles**
5. Open `http://localhost:3000/map/it` — expect reaction module + sensitivity table

### 4. Optional API smoke (curl)

```text
curl -s -H "Authorization: Bearer TOKEN" http://127.0.0.1:8000/api/map/sectors
curl -s -H "Authorization: Bearer TOKEN" http://127.0.0.1:8000/api/map/sectors/banking
curl -s -H "Authorization: Bearer TOKEN" "http://127.0.0.1:8000/api/map/modules/by-gap-type?gap_type=narrative_anchoring"
```

---

## Summary: what you need to do manually

| Step | Required? | Frequency |
|------|-----------|-----------|
| Run `apply_migrations.py` (includes `0018`) | **Yes** | Once per DB environment |
| Run `apply_all_factor_db_seeds()` | **Yes** | Once per DB environment (safe to re-run) |
| Sign in for UI test | **Yes** | Per browser session |
| Start backend + frontend | **Yes** | Each dev session |
| Re-run pytest suite | Optional | Before merge |

No Vercel/Render config changes beyond existing Supabase and API base URL variables.
