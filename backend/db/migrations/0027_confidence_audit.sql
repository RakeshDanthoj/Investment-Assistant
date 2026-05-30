-- P3-S1g: confidence audit trail + factor match count on events.

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS factor_db_match_count smallint NOT NULL DEFAULT 0;

COMMENT ON COLUMN public.events.factor_db_match_count IS
  'Count of macro factors matched by the rule-based scorer (P3-S1g).';

CREATE TABLE IF NOT EXISTS public.confidence_score_audit (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id uuid NOT NULL REFERENCES public.events (id) ON DELETE CASCADE,
  confidence_raw numeric(4, 3) NOT NULL,
  confidence_effective numeric(4, 3) NOT NULL,
  inputs_json jsonb NOT NULL,
  scorer_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_confidence_score_audit_event_id
  ON public.confidence_score_audit (event_id, created_at DESC);

COMMENT ON TABLE public.confidence_score_audit IS
  'Append-only scorer inputs per event upsert (P3-S1g reproducibility).';
