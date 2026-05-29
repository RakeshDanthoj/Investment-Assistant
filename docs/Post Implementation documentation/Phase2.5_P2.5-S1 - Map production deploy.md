# Post Implementation — P2.5-S1 Map production deploy

**Story:** P2.5-S1 — `/map/{slug}` + `/api/map/*` on production  
**Date:** 29 May 2026  
**Owners:** Riley (deploy/migrations) + Jordan (API verify)

---

## Summary

Map **frontend** sector routes are live on Vercel (`/map` and `/map/it` return **200**). Production **Postgres** has migration `0018_map_modules.sql` applied and Factor DB + `map_modules` seeds re-run. The **Render** API still returns **404** on `/api/map/sectors` because the deployed backend build predates `backend/app/api/map.py` registration — **redeploy Render** after merging current `main` to satisfy API acceptance criteria.

---

## Acceptance criteria status

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Latest frontend on Vercel (`map/[slug]/page.tsx`) | **Pass** | `curl` → `/map/it` **200** (29 May 2026) |
| Latest backend on Render (`map.py` registered) | **Pending** | `curl` → `/api/map/sectors` **404** (route missing on deployed image) |
| Migrations `0018` + sector/map seeds | **Pass** | `python scripts/apply_migrations.py`; `apply_all_factor_db_seeds()` |
| Unauthenticated API **401** | **Pending** | Blocked on Render redeploy (currently **404**) |
| Authenticated sector list + slug **200** | **Pending** | Run smoke with Bearer token after Render deploy |
| CI `map-sector` in `LIGHTHOUSE_PAGES` | **Pass** | `.github/workflows/ci.yml` mobile + desktop jobs |

---

## Tasks completed in repo / ops

| Task | Status | Notes |
|------|--------|-------|
| **1.1** Merge + Vercel/Render deploy | **Partial** | Vercel has sector route; Render API redeploy still required |
| **1.2** `apply_migrations.py` + seeds | **Done** | One-time against production `SUPABASE_DB_URL` |
| **1.3** Browser smoke `/map` → tile → slug | **Manual** | Frontend URL reachable; full signed-in flow after API deploy |
| **1.4** `curl` map API auth vs no auth | **Scripted** | `node scripts/map_production_smoke.mjs` |
| **1.5** Lighthouse `map-sector` in CI | **Done** | `LIGHTHOUSE_PAGES=…,map-sector` |

---

## Operator commands

### Database (one-time per environment)

```text
python scripts/apply_migrations.py
cd backend
python -c "import psycopg; from app.core.settings import get_settings; from app.db.seeds import apply_all_factor_db_seeds; s=get_settings();
with psycopg.connect(s.supabase_db_url) as c: apply_all_factor_db_seeds(c); c.commit(); print('Seeds applied.')"
```

### Production smoke (after Render redeploy)

```text
node scripts/map_production_smoke.mjs
MAP_SMOKE_BEARER_TOKEN=<supabase_access_token> node scripts/map_production_smoke.mjs
```

Expected when green:

- No auth → `/api/map/sectors` → **401**
- With Bearer → `/api/map/sectors` and `/api/map/sectors/it` → **200**
- Frontend `/map/it` → **200**

### Render redeploy

1. Ensure `main` includes `backend/app/api/map.py` and `app.include_router(map_router, prefix="/api")` in `main.py`.
2. Trigger Render deploy (manual or push to tracked branch).
3. Re-run `node scripts/map_production_smoke.mjs` with optional Bearer token.

---

## Smoke results (29 May 2026, pre–Render redeploy)

| Check | Result |
|-------|--------|
| `GET /map` | **200** |
| `GET /map/it` | **200** |
| `GET /api/map/sectors` (no auth) | **404** (deploy gap) |

---

## References

- Plan: `docs/plans/finnwise-phase2.5-implementation-tasks.md` § P2.5-S1
- P2-S11 implementation: `docs/Post Implementation documentation/Phase2_P2-S11 - Factor DB expansion and The Map content.md`
- CI: `.github/workflows/ci.yml` — `LIGHTHOUSE_MAP_SLUG` default `it`
