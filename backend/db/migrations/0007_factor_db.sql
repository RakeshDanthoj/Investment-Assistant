-- P1-S5 — Factor Exposure DB (sectors, instruments, 8 macro factors, sensitivities).

create extension if not exists "pgcrypto";

create table if not exists public.sectors (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  created_at timestamptz not null default now()
);

comment on table public.sectors is
  'Industry sectors for Factor DB grouping (Phase 1: Banking seeded).';

create table if not exists public.factors (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  display_name text not null,
  description text not null,
  sort_order smallint not null unique check (sort_order between 1 and 8),
  created_at timestamptz not null default now()
);

comment on table public.factors is
  'Eight macro sensitivity axes per PRD §7.1.';

create table if not exists public.instruments (
  id uuid primary key default gen_random_uuid(),
  sector_id uuid not null references public.sectors (id) on delete restrict,
  ticker text not null,
  exchange text not null default 'NSE',
  isin text,
  display_name text not null,
  created_at timestamptz not null default now(),
  unique (exchange, ticker)
);

create index if not exists instruments_sector_id_idx on public.instruments (sector_id);

create table if not exists public.instrument_factor_sensitivity (
  instrument_id uuid not null references public.instruments (id) on delete cascade,
  factor_id uuid not null references public.factors (id) on delete cascade,
  sensitivity smallint not null check (sensitivity between -5 and 5),
  mmj_tag public.mmj_type not null,
  source_url text not null check (length(btrim(source_url)) > 0),
  retrieved_at timestamptz not null,
  primary key (instrument_id, factor_id)
);

comment on column public.instrument_factor_sensitivity.sensitivity is
  'Signed magnitude: bearish/downside −5 … +5 bullish/upside exposure to the macro factor.';

comment on column public.instrument_factor_sensitivity.mmj_tag is
  'Evidence classification per PRD §6.2 — required on every sensitivity cell.';

create index if not exists instrument_factor_sensitivity_factor_id_idx
  on public.instrument_factor_sensitivity (factor_id);

alter table public.sectors enable row level security;
alter table public.factors enable row level security;
alter table public.instruments enable row level security;
alter table public.instrument_factor_sensitivity enable row level security;

-- No policies: anon/authenticated cannot read via PostgREST; service role bypasses RLS.
