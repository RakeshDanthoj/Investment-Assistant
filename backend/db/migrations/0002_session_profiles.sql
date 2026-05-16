-- P1-S2: session-scoped onboarding outcome (no amount column — PRD §11.1).
-- Run in Supabase SQL editor or via migration runner.

create extension if not exists "pgcrypto";

create table if not exists public.session_profiles (
  session_id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users (id) on delete cascade,
  status text not null
    check (status in ('starting_fresh', 'has_investments', 'curious')),
  horizon text not null
    check (horizon in ('under_1y', '1_3y', '3_7y', '7_plus')),
  cadence text not null
    check (cadence in ('monthly', 'one_time')),
  mode text not null
    check (mode in ('portfolio_builder', 'portfolio_protector', 'curious')),
  created_at timestamptz not null default now()
);

create index if not exists session_profiles_user_id_idx
  on public.session_profiles (user_id);

alter table public.session_profiles enable row level security;

-- Authenticated users: only their rows (when user_id is set).
create policy "session_profiles_select_own"
  on public.session_profiles for select
  using (auth.uid() is not null and user_id = auth.uid());

create policy "session_profiles_update_own"
  on public.session_profiles for update
  using (auth.uid() is not null and user_id = auth.uid())
  with check (auth.uid() is not null and user_id = auth.uid());

-- Pre-auth onboarding rows are inserted with service role (bypasses RLS).
-- After magic-link (P1-S3), optionally attach user_id via a separate flow.

comment on table public.session_profiles is
  'Onboarding outcome: mode + horizon stored server-side; amount is never persisted.';
