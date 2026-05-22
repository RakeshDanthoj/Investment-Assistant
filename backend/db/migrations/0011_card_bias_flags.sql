-- P1-S13 — Per-card bias audit flags (PRD §6.5)

CREATE TABLE IF NOT EXISTS public.card_bias_flags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL REFERENCES public.cards (id) ON DELETE CASCADE,
  bias_type text NOT NULL,
  severity text NOT NULL CHECK (severity IN ('flagged', 'monitored')),
  description text NOT NULL,
  detected_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT card_bias_flags_card_type_key UNIQUE (card_id, bias_type)
);

CREATE INDEX IF NOT EXISTS idx_card_bias_flags_card_id
  ON public.card_bias_flags (card_id);

CREATE INDEX IF NOT EXISTS idx_card_bias_flags_detected_at
  ON public.card_bias_flags (detected_at DESC);

COMMENT ON TABLE public.card_bias_flags IS
  'Bias audit findings surfaced in Thread aside (recency, sector concentration, narrative, etc.).';
