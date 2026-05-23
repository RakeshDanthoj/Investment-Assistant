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
2. **Authentication → URL configuration** (required for production magic links):
   - **Site URL**: set to your **production** frontend origin (e.g. `https://investment-assistant-frontend.vercel.app`). If this stays `http://localhost:3000`, magic-link emails from production will redirect to localhost when the requested redirect is not allow-listed.
   - **Redirect URLs** (exact paths; add every host you use):
     - `http://localhost:3000/callback`
     - `https://investment-assistant-frontend.vercel.app/callback` (or your production domain)
     - `https://*.vercel.app/callback` (preview deployments, if supported by your Supabase project)
   - The app sends `emailRedirectTo` as `{origin}/callback?next=...` from the sign-in page (`sign-in-form.tsx`). That full URL must match an entry above (origin + `/callback` prefix is enough; query params are ignored for matching).
3. **Authentication → Email templates**: optional — customise the magic-link email for invited testers. Do not hardcode `localhost` in template links; use `{{ .ConfirmationURL }}`.

**Vercel:** set `NEXT_PUBLIC_SITE_URL` to the same production origin as Supabase Site URL (no trailing slash) so server-side callback redirects stay on the correct host behind the Vercel proxy.

**Symptom:** magic link opens `localhost` after requesting sign-in on production → almost always **Site URL** or missing **Redirect URL** in Supabase, not application code.

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

Lighthouse mobile traces (`Page Load Performance/`) showed ~8s API wait via Vercel proxy. Local bench with S1 - instrumentation (direct Supabase `:5432`, no pool) on 2026-05-23:

| Endpoint | Path | wall p95 (ms) | db_connect p95 (ms) | db_query p95 (ms) | connections |
|----------|------|---------------|---------------------|-------------------|-------------|
| Feed | direct (local) | 999 | 794 | 195 | 3 |
| Feed | proxy (prod) | 6501 | — (pre-S1 deploy) | — | — |
| Card | direct (local) | 1285 | 1029 | 249 | 4 |
| Card | proxy (prod) | 8599 | — (pre-S1 deploy) | — | — |

**Signal:** `db_connect_ms` dominated `db_query_ms`; multiple connections per request (3 feed / 4 card). Re-run after S2 (pool) and S3 (query consolidation) deploy.

### P1.5-S3 post-consolidation (2026-05-23, local direct + pool)

Local bench with S2 pool + S3 single-connection queries (`127.0.0.1:8000`, direct Supabase `:5432`):

| Endpoint | Path | wall p95 (ms) | db_connect p95 (ms) | db_query p95 (ms) | connections |
|----------|------|---------------|---------------------|-------------------|-------------|
| Feed | direct (local) | 207 | 0.0 | 144 | 1 |
| Card | direct (local) | 226 | 0.1 | 194 | 1 |

Production proxy paths still reflect pre-S3 Render deploy (3–4 connections); redeploy backend to pick up S3.

## HTTP caching (P1.5-S4)

Published Pulse feed and Thread card detail responses include:

```http
Cache-Control: private, max-age=60, stale-while-revalidate=300
```

Draft cards, admin/editorial routes (`/api/admin/*`, `/admin/*`), and 404 card responses use `Cache-Control: no-store`. Client refetch paths (Pulse category filter, Thread Current/Original toggle, retry) intentionally keep `fetch(..., { cache: "no-store" })` so interactive updates bypass cache.

### Verify cache headers (local)

```bash
curl -i http://127.0.0.1:8000/api/feed | findstr /i "cache-control"
curl -i "http://127.0.0.1:8000/api/cards/<published-card-id>" | findstr /i "cache-control"
curl -i "http://127.0.0.1:8000/api/admin/cards/<draft-card-id>" | findstr /i "cache-control"
```

On bash/macOS, replace `findstr /i` with `grep -i`.

### Verify browser cache hit

1. Open DevTools → Network, disable "Disable cache".
2. Load `/pulse` twice within 60s (or curl the Render direct feed URL twice).
3. Second response should show `(disk cache)` or `(memory cache)` when fetched from the browser without `cache: "no-store"`.

SSR fetches in P1.5-S5/S6 use `revalidate: 60` instead of `no-store` so first paint can benefit from the same freshness window.

### bf-cache trade-off (acceptable)

Lighthouse may flag **"Page prevented back/forward cache restoration"** because client refetch paths use `Cache-Control: no-store`. This is intentional: editorial freshness and filter/view toggles must not serve stale JSON. The warning is acceptable for Phase 1.5; published read paths still cache for 60s where safe.

## Lighthouse (P1.5-S9 / S9b)

Lighthouse budgets for **Pulse** (`/pulse`) and **Thread** (`/thread/{cardId}`) on production (or staging). Supports **mobile** (default) and **desktop** (`--desktop` / `pnpm perf:lighthouse:desktop`).

### Budgets — mobile (Phase 1.5 Definition of Done)

| Metric | Threshold |
|--------|-----------|
| Performance score | ≥ 90 |
| Total Blocking Time | < 200 ms |
| Speed Index | < 3400 ms |

### Budgets — desktop (P1.5-S9b; enforced in CI)

| Metric | Threshold |
|--------|-----------|
| Performance score | ≥ 90 |
| Total Blocking Time | < 150 ms |
| Speed Index | < 2400 ms |

Override desktop thresholds with `LIGHTHOUSE_DESKTOP_MIN_PERFORMANCE`, `LIGHTHOUSE_DESKTOP_MAX_TBT_MS`, `LIGHTHOUSE_DESKTOP_MAX_SPEED_INDEX_MS`.

### Local vs production Lighthouse (important)

**Do not benchmark `next dev` (`pnpm dev`) for performance scores.** The dev server serves large unminified chunks (often 2–3 MB vs ~350 KB on Vercel), which inflates TBT and Time to Interactive even when FCP/LCP look fast.

| Environment | Typical Pulse desktop score | Notes |
|-------------|----------------------------|--------|
| `http://localhost:3000` + **`next dev`** | ~70 | Dev bundles + optional client refetch to `127.0.0.1:8000` |
| `http://localhost:3000` + **`next build` / `next start`** | Closer to prod | Use for local parity checks |
| Vercel production | 98–100 (May 2026 baseline) | What CI audits |

For production-like local numbers:

```bash
cd frontend
pnpm build
pnpm start
# In another terminal, from repo root:
pnpm perf:lighthouse:desktop
```

### Production desktop baselines (P1.5-S9b.4, 23-05-2026)

Committed evidence under `Page Load Performance/New loads/` (DevTools export, desktop profile):

| Surface | File | Performance | TBT | Speed Index | Desktop budget |
|---------|------|-------------|-----|-------------|----------------|
| Pulse | `investment-assistant-frontend.vercel.app-20260523T200644-desktop-pulse.json` | 98 | 20 ms | 1600 ms | Pass |
| Thread | `investment-assistant-frontend.vercel.app-20260523T200724- desktop -thread.json` | 100 | 0 ms | 980 ms | Pass |

Card id in Thread trace: `8e17ca99-b0b7-40aa-81e0-29c9308673cc`. No desktop budget tightening was required — current `DESKTOP_BUDGETS` (90 / 150 ms / 2400 ms) already pass with headroom.

Re-assert saved JSON without Chrome:

```bash
node scripts/lighthouse.mjs --desktop --assert-report="Page Load Performance/New loads/investment-assistant-frontend.vercel.app-20260523T200644-desktop-pulse.json"
node scripts/lighthouse.mjs --desktop --assert-report="Page Load Performance/New loads/investment-assistant-frontend.vercel.app-20260523T200724- desktop -thread.json"
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `LIGHTHOUSE_BASE_URL` | Frontend origin (default: `https://investment-assistant-frontend.vercel.app`) |
| `LIGHTHOUSE_THREAD_CARD_ID` | Published card UUID for Thread (default: same as `BENCH_CARD_ID` in `bench_api_latency.mjs`) |
| `LIGHTHOUSE_OUTPUT_DIR` | Where to write JSON reports (default: `Page Load Performance/`) |
| `LIGHTHOUSE_MIN_PERFORMANCE` | Override min performance score (default: `90`) |
| `LIGHTHOUSE_MAX_TBT_MS` | Override max TBT (default: `200`) |
| `LIGHTHOUSE_MAX_SPEED_INDEX_MS` | Override max Speed Index (default: `3400`) |
| `LIGHTHOUSE_FORM_FACTOR` | `mobile` (default) or `desktop` |
| `LIGHTHOUSE_DESKTOP_*` | Desktop budget overrides (see table above) |
| `LIGHTHOUSE_SKIP=1` | Skip run (exit 0) |

Optional GitHub secret: `LIGHTHOUSE_THREAD_CARD_ID` — overrides the default card id in CI. If the secret is **empty**, the runner falls back to the default published card (same as local).

On GitHub Actions (`CI=true`), each URL is audited **twice** when the first run fails budgets (guards Lighthouse variance). Override with `LIGHTHOUSE_CI_ATTEMPTS=1` to disable.

### Run locally

From repo root (requires Chrome; installed automatically via `chrome-launcher`):

```bash
pnpm install
pnpm perf:lighthouse              # mobile
pnpm perf:lighthouse:desktop        # desktop
```

From `frontend/`:

```bash
pnpm perf:lighthouse
pnpm perf:lighthouse:desktop
pnpm perf:lighthouse -- --pulse-only
pnpm perf:lighthouse:desktop -- --thread-only
pnpm perf:lighthouse -- --no-save
```

Budget assertion smoke test (no Chrome):

```bash
pnpm perf:lighthouse:budget-test
```

Assert budgets against an existing Lighthouse JSON export:

```bash
node scripts/lighthouse.mjs --assert-report="Page Load Performance/investment-assistant-frontend.vercel.app-20260523T151315-pulse.json"
```

Expect exit code **1** on the baseline Pulse trace (performance 82, Speed Index ~5.8s) — use that to verify CI would fail on regression.

### CI

The **Lighthouse budgets** job in `.github/workflows/ci.yml` runs after the frontend job:

1. `pnpm perf:lighthouse:budget-test` — unit smoke for assertion helpers
2. `pnpm perf:lighthouse -- --no-save` — live **mobile** audits (enforced)
3. `pnpm perf:lighthouse:desktop -- --no-save` — live **desktop** audits (enforced; baselines in `Page Load Performance/New loads/`)

Reports are not committed from CI; save locally with `pnpm perf:lighthouse` / `pnpm perf:lighthouse:desktop` when capturing evidence for **P1.5-S10**.

### P1.5-S10 sign-off evidence (23-05-2026)

| Artifact | Path |
|----------|------|
| Sign-off doc | `docs/Post Implementation documentation/Phase1_P1.5 - Performance remediation Pulse and Thread.md` |
| Before mobile | `Page Load Performance/investment-assistant-frontend.vercel.app-20260523T151315-pulse.json`, `…151456- Thread.json` |
| After mobile (runner) | `Page Load Performance/lighthouse-ci-mobile-…-2026-05-23T1448-pulse.json`, `…-thread.json` |
| After desktop | `Page Load Performance/New loads/…200644-desktop-pulse.json`, `…200724- desktop -thread.json` |

Post-deploy proxy bench (warm p95): feed **1753 ms**, card **1762 ms** — PO accepted at Phase 1.5 close (23-05-2026); optional follow-up. See sign-off doc for full table.

**Phase 1.5 status:** **CLOSED** (Product Owner sign-off 23-05-2026).
