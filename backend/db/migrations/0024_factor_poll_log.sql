-- P3-S1d — NewsAPI factor poll audit log (G-04).

CREATE TABLE IF NOT EXISTS public.factor_poll_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  factor_id uuid NOT NULL REFERENCES public.factors (id) ON DELETE RESTRICT,
  polled_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL CHECK (status IN ('ok', 'empty', 'error')),
  article_count smallint NOT NULL DEFAULT 0
    CONSTRAINT factor_poll_log_article_count_nonneg CHECK (article_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_factor_poll_log_polled_at
  ON public.factor_poll_log (polled_at DESC);

CREATE INDEX IF NOT EXISTS idx_factor_poll_log_factor_polled
  ON public.factor_poll_log (factor_id, polled_at DESC);

COMMENT ON TABLE public.factor_poll_log IS
  'NewsAPI round-robin factor polls: status ok|empty|error and article_count per tick (G-04).';

ALTER TABLE public.factor_poll_log ENABLE ROW LEVEL SECURITY;
