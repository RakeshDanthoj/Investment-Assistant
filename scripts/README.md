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
