-- FinnWise P1-S4: Postgres enums (PRD §6.2, §7.2, Living Card lifecycle §5 Screen 3)

DO $$ BEGIN
  CREATE TYPE public.mmj_type AS ENUM (
    'MEASURED',
    'MODELLED',
    'JUDGED'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE public.lifecycle_state AS ENUM (
    'draft',
    'published',
    'active',
    'signal_triggered',
    'thesis_confirmed',
    'thesis_weakened',
    'resolved',
    'archived'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE public.signal_state AS ENUM (
    'pending',
    'triggered',
    'resolved'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE public.event_category AS ENUM (
    'macro',
    'rbi_policy',
    'regulatory',
    'india_specific',
    'geopolitical',
    'budget'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;
