-- P2-S6: Lens on-demand query history and generation queue

DO $$ BEGIN
  CREATE TYPE public.lens_query_status AS ENUM (
    'queued',
    'running',
    'done',
    'failed'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS public.lens_queries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  query text NOT NULL,
  sector public.event_category,
  horizon text CHECK (
    horizon IS NULL
    OR horizon IN ('under_1y', '1_3y', '3_7y', '7_plus')
  ),
  status public.lens_query_status NOT NULL DEFAULT 'queued',
  card_id uuid REFERENCES public.cards (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS lens_queries_user_created_idx
  ON public.lens_queries (user_id, created_at DESC);

COMMENT ON TABLE public.lens_queries IS
  'User-submitted Lens questions; pipeline generation is wired in P2-S7.';
