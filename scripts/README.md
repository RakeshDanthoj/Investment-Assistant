# Scripts

Shared automation for the FinnWise monorepo.

## Database migrations (P1-S4)

1. In Supabase → **Project Settings → Database**, copy the **Connection string** (URI).
2. Add to repo-root `.env.local` as `SUPABASE_DB_URL=postgresql://...` (do not commit).
   - **Local / migrations:** use the **Direct connection** URI (`db.<ref>.supabase.co:5432`).
   - **Render / other IPv4 hosts:** use the **Session pooler** URI (`…pooler.supabase.com:5432`) from Supabase → Database → Connect. Direct `:5432` often fails from Render while REST API still works.
3. From repo root:

```bash
pip install -e "./backend[dev]"
python scripts/apply_migrations.py
```

Migrations live in `backend/db/migrations/` (`0003` enums → `0004` core tables → `0005` track_record append-only).

## Supabase Auth (P1-S3)

Configure the Supabase project dashboard once per environment:

1. **Authentication → Providers → Email**: enable Email; disable password sign-in (magic link only).
2. **Authentication → URL configuration**: add redirect URLs:
   - `http://localhost:3000/callback`
   - `https://<your-vercel-preview>.vercel.app/callback`
   - `https://<your-production-domain>/callback`
3. **Authentication → Email templates**: optional — customise the magic-link email for invited testers.

## API latency bench (P1.5-S1)

Measure warm-request latency for Pulse feed and Thread card detail. The bench compares **Render direct** vs **Vercel `/backend/...` proxy** and reads `X-FinnWise-Timing` headers (`db_connect_ms`, `db_query_ms`, `total_ms`).

### Prerequisites

- Backend deployed with P1.5-S1 timing headers (or run locally — see below).
- Render `SUPABASE_DB_URL` uses the **Session pooler** URI (`…pooler.supabase.com:5432`), not the direct `:5432` host.
- Production card id for Thread bench (default from Lighthouse trace): `e708b82c-f7c7-45e7-a59b-6b66dac8927a`.

### Environment variables

| Variable | Purpose |
|----------|---------|
| `BENCH_API_DIRECT_URL` | Render backend origin (e.g. `https://your-service.onrender.com`) |
| `BENCH_VERCEL_URL` | Vercel frontend for proxy path (default: production Vercel URL) |
| `BENCH_CARD_ID` | Published card UUID for `/api/cards/{id}` |
| `NEXT_PUBLIC_API_BASE_URL` | Fallback for direct URL when `BENCH_API_DIRECT_URL` unset |

### Run (production)

From repo root:

```bash
node scripts/bench_api_latency.mjs
```

Example with explicit URLs:

```bash
BENCH_API_DIRECT_URL=https://your-service.onrender.com \
BENCH_VERCEL_URL=https://investment-assistant-frontend.vercel.app \
BENCH_CARD_ID=e708b82c-f7c7-45e7-a59b-6b66dac8927a \
node scripts/bench_api_latency.mjs
```

The script discards one warmup request, then runs **5 warm iterations** per endpoint and prints wall-clock p50/p95 plus server timing p50/p95 when headers are present.

### Run (local backend)

1. Start API: `pnpm dev:backend` (port 8000).
2. Point direct URL at loopback for feed/card direct paths only — proxy still needs Vercel:

```bash
BENCH_API_DIRECT_URL=http://127.0.0.1:8000 node scripts/bench_api_latency.mjs
```

3. Inspect `/health/db` for connect vs query breakdown:

```bash
curl -s http://127.0.0.1:8000/health/db | jq
```

### P1.5-S1 baseline (2026-05-23, pre-remediation)

Lighthouse mobile traces (`Page Load Performance/`) showed ~8s API wait via Vercel proxy. Local bench with S1 instrumentation (direct Supabase `:5432`, no pool) on 2026-05-23:

| Endpoint | Path | wall p95 (ms) | db_connect p95 (ms) | db_query p95 (ms) | connections |
|----------|------|---------------|---------------------|-------------------|-------------|
| Feed | direct (local) | 999 | 794 | 195 | 3 |
| Feed | proxy (prod) | 6501 | — (pre-S1 deploy) | — | — |
| Card | direct (local) | 1285 | 1029 | 249 | 4 |
| Card | proxy (prod) | 8599 | — (pre-S1 deploy) | — | — |

**Signal:** `db_connect_ms` dominates `db_query_ms`; multiple connections per request (3 feed / 4 card). Re-run after S2 (pool) and S3 (query consolidation) deploy.

## Lighthouse (P1.5-S9)

Documented in P1.5-S9 — run mobile Lighthouse against production `/pulse` and `/thread/{cardId}` after SSR work lands.
