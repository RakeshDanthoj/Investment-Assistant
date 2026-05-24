-- P2-S11 — The Map educational modules linked to sectors and reasoning-gap types.

create table if not exists public.map_modules (
  id uuid primary key default gen_random_uuid(),
  sector_slug text references public.sectors (slug) on delete cascade,
  title text not null,
  body text not null,
  linked_gap_types text[] not null default '{}',
  sort_order smallint not null default 0,
  created_at timestamptz not null default now()
);

comment on table public.map_modules is
  'Sector learning modules for The Map; linked_gap_types supports P2-S4 reasoning-gap routing.';

create index if not exists map_modules_sector_slug_idx on public.map_modules (sector_slug);
create index if not exists map_modules_linked_gap_types_gin_idx
  on public.map_modules using gin (linked_gap_types);

alter table public.map_modules enable row level security;
