-- P2-S13 — Per-user Lens rate limit + pipeline run observability.

CREATE TABLE IF NOT EXISTS public.lens_user_daily_usage (
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  usage_date date NOT NULL,
  query_count integer NOT NULL DEFAULT 0 CHECK (query_count >= 0),
  PRIMARY KEY (user_id, usage_date)
);

COMMENT ON TABLE public.lens_user_daily_usage IS
  'UTC calendar-day Lens query counter per user; default cap 10/day (P2-S13).';

CREATE OR REPLACE FUNCTION public.try_consume_lens_query_slot(
  p_user_id uuid,
  p_max integer DEFAULT 10
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO public AS $$
DECLARE
  d date := (timezone('utc', now()))::date;
  cur integer;
BEGIN
  SELECT query_count INTO cur
  FROM public.lens_user_daily_usage
  WHERE user_id = p_user_id AND usage_date = d
  FOR UPDATE;

  IF NOT FOUND THEN
    INSERT INTO public.lens_user_daily_usage (user_id, usage_date, query_count)
    VALUES (p_user_id, d, 1);
    RETURN true;
  END IF;

  IF cur >= p_max THEN
    RETURN false;
  END IF;

  UPDATE public.lens_user_daily_usage
  SET query_count = query_count + 1
  WHERE user_id = p_user_id AND usage_date = d;
  RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION public.try_consume_lens_query_slot(uuid, integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.try_consume_lens_query_slot(uuid, integer) TO service_role;

CREATE TABLE IF NOT EXISTS public.pipeline_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  pipeline text NOT NULL,
  prompt_version text NOT NULL DEFAULT '',
  input_tokens integer NOT NULL DEFAULT 0 CHECK (input_tokens >= 0),
  output_tokens integer NOT NULL DEFAULT 0 CHECK (output_tokens >= 0),
  duration_ms integer NOT NULL DEFAULT 0 CHECK (duration_ms >= 0),
  status text NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'error')),
  error_message text,
  context jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_created_at
  ON public.pipeline_runs (created_at DESC);

COMMENT ON TABLE public.pipeline_runs IS
  'Structured pipeline telemetry for admin metrics and JSON logs (P2-S13).';
