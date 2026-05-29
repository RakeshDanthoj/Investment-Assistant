# Post Implementation Detailed Document — P2.5-S1

**Version:** v1.0 | **Date:** 29-05-2026  
**Story ID:** P2.5-S1 (Phase 2.5, Story 1)  
**Reference plan:** `docs/plans/finnwise-phase2.5-implementation-tasks.md`

---

## Narrative style (read this first)

**P2-S11** built The Map in the repository: eight sector tiles, `/map/{slug}` detail pages, `map_modules` in Postgres, and authenticated `/api/map/*` routes. By May 2026, production still failed the Phase 2.5 bar: Vercel sometimes served `/map` but not `/map/it`, and Render returned **404** on `/api/map/sectors` because the Map router was not on the deployed API image. Seeds and migration `0018` were also not guaranteed on the production database.

**P2.5-S1** closes that gap. It is a **Full Stack deploy and verification** story: ship the existing Map frontend and backend to Vercel and Render, apply `0018_map_modules.sql` plus Factor DB and `map_modules` seeds on production Supabase, prove auth behaviour (**401** without Bearer, **200** when signed in), and add **`map-sector`** to Lighthouse CI so `/map/it` is audited with the other Phase 2 routes. No new Map product logic was invented here — the work is release engineering, database ops, smoke tooling, and CI wiring.

**Tests executed and passed:**

| Suite / check | Command or method | Result |
|---------------|-------------------|--------|
| Backend Map API | `python -m pytest tests/test_map_api.py -q` | **3 passed** |
| Production smoke (unauth + frontend) | `node scripts/map_production_smoke.mjs` | **Pass** (operator) |
| Production smoke (authenticated API) | `MAP_SMOKE_BEARER_TOKEN=… node scripts/map_production_smoke.mjs` | **Pass** (operator) |
| Browser E2E | Signed-in `/map` → sector tile → `/map/{slug}` | **Pass** (operator) |

**Three anchors:** (1) **404 on `/api/map/sectors` means missing Render deploy**, not bad credentials — expect **401** when the route exists; (2) **migration + seeds are one-time per DB** — deploy without them yields empty or 503 Map; (3) **`map-sector` in CI** depends on production `/map/{slug}` returning **200** (Lighthouse preflight fails on 404).

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2.5-S1 |
| **Title** | Map production deploy (`/map/{slug}` + API) |
| **Category** | **Full Stack** (deploy, DB ops, CI, smoke scripts; feature code from P2-S11) |

**What this story aimed to achieve (plain language)**

Users opening a sector from The Map index on production should see factor sensitivities and learning modules loaded from the live API — not a Next.js or API **404**. Operators needed Vercel and Render on builds that include the dynamic Map routes and `map.py` router, production Postgres on migration `0018` with all sector and module seeds, and CI Lighthouse coverage for a representative sector slug (default `it`).

**How it fits into the overall application**

- **Upstream:** **P2-S11** (Map UI, APIs, migration, seeds in repo).
- **Blocks:** **P2.5-S6** evidence archive (`map-sector` JSON); **P2.5-S3/S4** Lighthouse on full Phase 2 surface set.
- **Phase 3 gate:** Phase 2.5 exit criteria require Map slug **200** and API **401** unauthenticated — satisfied when this story is green.

**Production URLs (baseline)**

| Layer | URL |
|-------|-----|
| Frontend | `https://investment-assistant-frontend.vercel.app` |
| API | `https://investment-assistant-3eqc.onrender.com` |

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **1.1** | Merge Map work to `main`; trigger Vercel + Render deploys so `map/[slug]/page.tsx` and `app.include_router(map_router)` are live. |
| **1.2** | Run `python scripts/apply_migrations.py` on production `SUPABASE_DB_URL`; run `apply_all_factor_db_seeds()` for eight sectors + `map_modules`. |
| **1.3** | Browser smoke: signed-in user navigates `/map` → sector tile → `/map/{slug}` with modules and matrix visible. |
| **1.4** | API smoke: unauthenticated `GET /api/map/sectors` → **401**; with Supabase access token → **200** on list and sector detail. |
| **1.5** | Add `map-sector` to `LIGHTHOUSE_PAGES` in `.github/workflows/ci.yml` (mobile + desktop jobs). |

**Functional breakdown**

1. Operator confirms `main` contains P2-S11 Map code (`backend/app/api/map.py`, `frontend/app/(app)/map/[slug]/page.tsx`, `main.py` router registration).
2. Vercel deploy picks up App Router dynamic segment `[slug]`.
3. Render deploy registers `/api/map/*` under existing `/api` prefix.
4. `apply_migrations.py` ensures `0018_map_modules.sql` is recorded in `schema_migrations`.
5. `apply_all_factor_db_seeds()` idempotently loads sector instruments/sensitivities and `map_modules` rows.
6. Smoke script and manual browser verify end-to-end behaviour.
7. CI audits `/map/{LIGHTHOUSE_MAP_SLUG}` (default `it`) alongside pulse, thread, mirror, lens, map index.

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| Not signed in (browser) | `/map` and `/map/{slug}` render “Sign in to explore The Map.” — page may still return **200** without sector API data. |
| Not signed in (API) | `GET /api/map/sectors` → **401** `Missing bearer token` or invalid token detail. |
| Map router missing on Render | **404** on `/api/map/sectors` — smoke script documents this as deploy gap, not auth failure. |
| Unknown sector slug | **404** from API; Next.js `notFound()` on sector page after failed fetch. |
| DB not configured / unavailable | API **503** `Database is not configured`. |
| Lighthouse preflight | `scripts/lighthouse.mjs` fails CI if `/map/{slug}` returns ≥400 before audit runs. |
| Re-run seeds | Safe — idempotent SQL with `ON CONFLICT` and fixed module UUIDs (P2-S11). |

**Business rules enforced**

- Map remains an **authenticated** Portfolio Builder surface (Bearer JWT on all `/api/map/*` routes — unchanged from P2-S11).
- Production must expose the **same** eight sectors and module inventory as seeded in dev (operator verifies tile count and sector detail content).
- Unauthenticated API must **not** return **404** for `/api/map/sectors` once deploy is correct — **401** proves the route is registered.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Deploy story separate from P2-S11** | Feature merged in Phase 2; production lag tracked as Phase 2.5 close-out before Phase 3 load. | Folding deploy into P2-S11: blurred “done in repo” vs “done in prod”. |
| **Dedicated `map_production_smoke.mjs`** | Repeatable operator check for frontend + API status codes without curl/PowerShell quirks on Windows. | Manual curl only: fragile across shells; easy to misread 404 vs 401. |
| **Enable `map-sector` only after slug route live** | Lighthouse preflight fails on 404 and blocks entire CI job. | Enable early: red CI until Vercel deploy caught up. |
| **Default smoke slug `it`** | Matches `LIGHTHOUSE_MAP_SLUG` default in CI and plan. | `banking` only: less representative of Phase 2 sector expansion narrative. |
| **Re-run full `apply_all_factor_db_seeds()`** | Ensures seven Phase 2 sectors + `map_modules` exist even if migration was applied earlier without seeds. | Map-only seed script: extra tooling; full bundle already in `seeds.py`. |

⚠️ **Do not treat API 404 as “fix auth”** — redeploy Render or verify `map_router` is included in `main.py` on the deployed branch.

⚠️ **Do not skip seeds after migration** — `0018` creates an empty `map_modules` table; sector pages load but modules/matrix may be empty or API may error depending on data.

⚠️ **Do not remove `map-sector` from CI** without PO waiver — Phase 2.5 exit and P2.5-S6 evidence require six surfaces including one Map slug.

**Assumptions**

- P2-S11 code on `main` is correct; this story does not change Map business logic.
- Operator has `SUPABASE_DB_URL` in `.env.local` for migration/seed scripts.
- Vercel and Render auto-deploy from `main` (or equivalent production branch) after merge.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P2-S11** — Map routes, `map_content` service, `0018` migration, sector seeds, `map_modules.sql`. |
| **Moved from** | **P2-S15** (implicit) — `/map/{slug}` production 404 and Map API 404 listed in Phase 2 perf close-out. |
| **Enables** | **P2.5-S6** — Lighthouse JSON archive including Map sector; **P2.5-S3/S4** — full mobile perf gate on Phase 2 routes. |
| **Phase 3** | Exit criterion “Map slug 200 + API 401 unauthenticated” — prerequisite satisfied when P2.5-S1 is green. |
| **Shared** | `public.map_modules`, `public.sectors`, Supabase JWT (`get_current_user`), Vercel `NEXT_PUBLIC_API_BASE_URL` → Render API. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | No new services; operational verification of existing P2-S11 stack. |
| **Schema** | Uses existing `0018_map_modules.sql` + P2-S11 seeds (no new migration in P2.5-S1). |
| **API auth** | Unchanged Bearer JWT on `/api/map/*`; **401** is the production proof of route registration. |
| **UI** | Unchanged SSR from `map/page.tsx` and `map/[slug]/page.tsx` + `mapServer.ts` fetch helpers. |
| **CI** | `LIGHTHOUSE_PAGES` extended with `map-sector`; `LIGHTHOUSE_MAP_SLUG` default `it`. |
| **Tooling** | Node smoke script at repo root `scripts/` (same pattern as `bench_api_latency.mjs`, `lighthouse.mjs`). |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| map_production_smoke.mjs | `scripts/map_production_smoke.mjs` | Production smoke: frontend `/map`, `/map/{slug}`, API 401/200 |
| Phase2.5_P2.5-S1 - Map production deploy.md | `docs/Post Implementation documentation/Phase2.5_P2.5-S1 - Map production deploy.md` | This handover document |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| ci.yml | `.github/workflows/ci.yml` | `LIGHTHOUSE_PAGES` includes `map-sector` (mobile + desktop Lighthouse steps) |
| README.md | `scripts/README.md` | Documented Map production smoke commands and 401 vs 404 interpretation |
| finnwise-phase2.5-implementation-tasks.md | `docs/plans/finnwise-phase2.5-implementation-tasks.md` | P2.5-S1 acceptance criteria and tasks marked complete; Phase 2.5 Map exit criterion checked |

**Not modified (relied upon from P2-S11)**

| File Path | Role in production |
|-----------|-------------------|
| `backend/app/api/map.py` | Map HTTP routes |
| `backend/app/main.py` | `include_router(map_router, prefix="/api")` |
| `frontend/app/(app)/map/[slug]/page.tsx` | Sector detail SSR page |
| `frontend/app/(app)/map/page.tsx` | Map index |
| `backend/db/migrations/0018_map_modules.sql` | `map_modules` table |
| `backend/app/db/seeds.py` | `apply_all_factor_db_seeds()` |

---

### A8. TESTS EXECUTED

| Test / check | Status | What it covers |
|--------------|--------|----------------|
| `test_list_sectors_returns_eight` | **Passed** | `GET /api/map/sectors` returns ≥8 sectors including `banking`, `it` |
| `test_sector_detail_has_modules_and_matrix` | **Passed** | Banking detail has factors, instruments, modules, sensitivity payload |
| `test_gap_type_modules_resolve` | **Passed** | Each reasoning-gap slug resolves via `by-gap-type` |
| `map_production_smoke.mjs` (no token) | **Passed** (operator) | `/map` **200**, `/map/it` **200**, `/api/map/sectors` **401** |
| `map_production_smoke.mjs` (with Bearer) | **Passed** (operator) | Authenticated sector list + `/api/map/sectors/it` **200** |
| Browser smoke **1.3** | **Passed** (operator) | Signed-in navigation index → tile → sector detail |

**Backend command (regression for Map API logic)**

```text
cd backend
python -m pytest tests/test_map_api.py -q
```

→ **3 passed**

**Production smoke command**

```text
node scripts/map_production_smoke.mjs
MAP_SMOKE_BEARER_TOKEN=<supabase_access_token> node scripts/map_production_smoke.mjs
```

**CI**

- Lighthouse jobs on `main` use `LIGHTHOUSE_PAGES=pulse,thread,mirror,lens,map,map-sector`.
- Full budget green on `map-sector` is tracked under **P2.5-S6**, not P2.5-S1.

**Frontend automated tests**

None added in P2.5-S1 (deploy story). Map UI coverage remains manual + Lighthouse CI.

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**No new migration in P2.5-S1.** Production must have P2-S11 objects applied:

| Artifact | Purpose |
|----------|---------|
| `0018_map_modules.sql` | Creates `public.map_modules` + indexes + RLS |
| `backend/db/seeds/sectors/*.sql` | Seven Phase 2 sectors (IT, Energy, …) |
| `backend/db/seeds/banking_sector.sql` | Banking sector (P1-S5) |
| `backend/db/seeds/map_modules.sql` | Sector reaction modules + three gap modules |

**Operator sequence (one-time per environment, safe to re-run seeds)**

```text
python scripts/apply_migrations.py
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

**Confirm migration applied**

```sql
SELECT filename FROM public.schema_migrations
WHERE filename = '0018_map_modules.sql';
```

---

### B2. API / INTEGRATION CONTRACTS

Unchanged from P2-S11 — P2.5-S1 verifies they are reachable on Render.

| Method | Route | Auth | Expected (production) |
|--------|-------|------|------------------------|
| GET | `/api/map/sectors` | None | **401** |
| GET | `/api/map/sectors` | Bearer | **200** + sector list |
| GET | `/api/map/sectors/{slug}` | Bearer | **200** + detail (e.g. `it`, `energy`) |
| GET | `/api/map/modules/by-gap-type` | Bearer | **200** |
| GET | `/api/map/modules/{module_id}` | Bearer | **200** or **404** |

**Smoke: unauthenticated sector list**

```text
curl -s -o /dev/null -w "%{http_code}" https://investment-assistant-3eqc.onrender.com/api/map/sectors
```

Expected: `401`

**Smoke: authenticated sector list**

```text
curl -s -H "Authorization: Bearer <token>" \
  https://investment-assistant-3eqc.onrender.com/api/map/sectors
```

Expected: JSON with `sectors` array (≥8 entries).

---

### B3. BUSINESS LOGIC & RULES (Detailed)

```
Deploy verification (P2.5-S1)
  → Vercel build includes app/(app)/map/[slug]/page.tsx
  → Render build includes map_router on /api
  → apply_migrations (0018 present)
  → apply_all_factor_db_seeds (sectors + map_modules)

Operator smoke
  → GET /map, /map/{slug} → 200
  → GET /api/map/sectors (no auth) → 401
  → GET /api/map/sectors (+ Bearer) → 200
  → GET /api/map/sectors/{slug} (+ Bearer) → 200

End user (signed in) — same as P2-S11
  → /map → fetchMapSectorList → tiles
  → /map/{slug} → fetchMapSectorDetail → MapSectorClient
  → optional ?module= deep link on index (redirect to sector when scoped)
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Limitation | Notes |
|------------|--------|
| **Lighthouse `map-sector` budget** | Enabling the URL in CI does not guarantee perf ≥90 — tracked in P2.5-S3/S6. |
| **Signed-out sector pages** | May return **200** with sign-in message; Lighthouse audits unauthenticated HTML shell. |
| **Cold Render start** | First API request after idle can be slow; smoke script uses 30s-friendly fetch (operator may retry). |
| **No automated E2E in CI** | Browser flow **1.3** remains manual or future Playwright. |

---

### B5. TESTING NOTES

| Area | Automated | Manual / operator |
|------|-----------|-------------------|
| Map API contracts | `test_map_api.py` | — |
| Production deploy | `map_production_smoke.mjs` | Browser **1.3** |
| Lighthouse `/map/it` | CI on push to `main` | Local `pnpm perf:lighthouse -- --map-only` |
| Factor DB coverage | `test_factor_db_coverage.py` (P2-S11) | Re-run if seed issues suspected |

**Happy path:** Sign in → `/map` shows 8 tiles → `/map/it` shows modules + sensitivity matrix → Network tab shows **200** on `/api/map/sectors/it` via server or client fetch.

**Failure triage**

| Symptom | Likely cause |
|---------|----------------|
| `/map/it` **404** | Vercel deploy missing `[slug]` route |
| API **404** | Render deploy missing `map_router` |
| API **503** | `SUPABASE_DB_URL` wrong or DB down |
| API **200** but empty modules | Seeds not applied |
| CI Lighthouse fails Map sector only | Perf budget (P2.5-S3/S6), not deploy |

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Where | Purpose |
|----------|-------|---------|
| `SUPABASE_DB_URL` | `.env.local` / Render | Migrations + seeds (`apply_migrations.py`) |
| `NEXT_PUBLIC_API_BASE_URL` | Vercel | Frontend → Render API |
| `LIGHTHOUSE_PAGES` | CI workflow | Includes `map-sector` after P2.5-S1 |
| `LIGHTHOUSE_MAP_SLUG` | CI secret or default `it` | Sector URL for Lighthouse |
| `MAP_SMOKE_FRONTEND_URL` | Optional smoke override | Default Vercel production URL |
| `MAP_SMOKE_API_URL` | Optional smoke override | Default Render production URL |
| `MAP_SMOKE_BEARER_TOKEN` | Smoke script only | Enables authenticated API checks |
| `MAP_SMOKE_MAP_SLUG` | Smoke script only | Default `it` |

**Deployment sequencing**

1. Merge to `main` (Map code present).
2. Wait for Vercel + Render deploys (or trigger manual).
3. Run migrations + seeds on production DB.
4. Run `node scripts/map_production_smoke.mjs`.
5. Confirm CI Lighthouse includes `map-sector` on next `main` build.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing Map deploy or CI**

1. Read **P2-S11** handover: `docs/Post Implementation documentation/Phase2_P2-S11 - Factor DB expansion and The Map content.md`.
2. Run `node scripts/map_production_smoke.mjs` after any Render/Vercel/DB change.
3. Distinguish **401** (route exists, need token) from **404** (router not deployed).

**Common mistakes**

- Applying only migration `0018` without `apply_all_factor_db_seeds()` → empty Map.
- Removing `map-sector` from CI while Phase 2.5 exit still requires six surfaces.
- Assuming `/map/{slug}` **404** is a Next.js bug when Vercel is on an old build.

**Where to find code**

| Concern | Path |
|---------|------|
| Map API routes | `backend/app/api/map.py` |
| Router registration | `backend/app/main.py` |
| Map data layer | `backend/app/services/map_content.py` |
| Sector page | `frontend/app/(app)/map/[slug]/page.tsx` |
| Map index | `frontend/app/(app)/map/page.tsx` |
| Server fetch | `frontend/lib/api/mapServer.ts` |
| Production smoke | `scripts/map_production_smoke.mjs` |
| Lighthouse pages | `scripts/lighthouse.mjs`, `.github/workflows/ci.yml` |

**Contact by role**

| Role | Responsibility |
|------|----------------|
| Riley | Vercel/Render deploy, migrations, seeds, Lighthouse CI |
| Jordan | Map API behaviour, auth, Render env |
| Sam | Map UI regressions after deploy |

---

## Manual verification checklist (operator)

### 1. Production smoke script

```text
node scripts/map_production_smoke.mjs
MAP_SMOKE_BEARER_TOKEN=<token> node scripts/map_production_smoke.mjs
```

### 2. Browser (signed in)

1. Open `/map` — eight sector tiles.
2. Open `/map/it` (or another slug) — modules + sensitivity matrix.
3. Optional: `/map?module=<uuid>` redirect when module is sector-scoped.

### 3. CI

Confirm `.github/workflows/ci.yml` lists `LIGHTHOUSE_PAGES: pulse,thread,mirror,lens,map,map-sector`.

---

## Summary: what you need to do manually

| Step | Required? | Frequency |
|------|-----------|-----------|
| Deploy `main` to Vercel + Render | **Yes** (if Map 404) | Per release |
| `apply_migrations.py` + seeds | **Yes** | Once per new DB env; seeds safe to re-run |
| `map_production_smoke.mjs` | **Yes** | After deploy or DB change |
| Browser sign-in test | **Yes** | Per major Map release |
| `test_map_api.py` | Recommended | Before merge / after API changes |

---

## References

| Doc / script | Role |
|--------------|------|
| `docs/plans/finnwise-phase2.5-implementation-tasks.md` | P2.5-S1 tasks and exit criteria |
| `docs/Post Implementation documentation/Phase2_P2-S11 - Factor DB expansion and The Map content.md` | Feature implementation handover |
| `scripts/map_production_smoke.mjs` | Production deploy regression |
| `scripts/lighthouse.mjs` | CI audits including `map-sector` |
