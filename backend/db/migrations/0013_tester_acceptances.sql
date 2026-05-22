-- P1-S14: signed tester briefing acceptance (checkbox + timestamp + IP surrogate).

create table if not exists public.tester_acceptances (
  user_id uuid primary key references auth.users (id) on delete cascade,
  accepted_at timestamptz not null default now(),
  ip text
);

create index if not exists tester_acceptances_accepted_at_idx
  on public.tester_acceptances (accepted_at desc);

alter table public.tester_acceptances enable row level security;

create policy "tester_acceptances_select_own"
  on public.tester_acceptances for select
  using (auth.uid() is not null and user_id = auth.uid());

create policy "tester_acceptances_insert_own"
  on public.tester_acceptances for insert
  with check (auth.uid() is not null and user_id = auth.uid());

comment on table public.tester_acceptances is
  'Mandatory tester briefing acceptance — one row per invited user; append-only in V1.';
