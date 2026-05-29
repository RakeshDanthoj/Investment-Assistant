-- P3-S0 / G-13: synthetic historical seed columns, dedup/confidence fields, triple-layer RLS baseline.

-- events: isolation + Phase 3 confidence / dedup columns
ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS is_synthetic boolean NOT NULL DEFAULT false;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS confidence_raw numeric(4, 3);

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS confidence_effective numeric(4, 3);

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS is_major boolean NOT NULL DEFAULT false;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS is_major_override boolean;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS is_major_override_by uuid;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS is_major_override_at timestamptz;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS dedup_key text;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS external_id text;

CREATE UNIQUE INDEX IF NOT EXISTS idx_events_external_id
  ON public.events (external_id)
  WHERE external_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_events_dedup_key
  ON public.events (dedup_key)
  WHERE dedup_key IS NOT NULL;

-- child / related tables
ALTER TABLE public.signals
  ADD COLUMN IF NOT EXISTS is_synthetic boolean NOT NULL DEFAULT false;

ALTER TABLE public.track_record
  ADD COLUMN IF NOT EXISTS is_synthetic boolean NOT NULL DEFAULT false;

ALTER TABLE public.user_predictions
  ADD COLUMN IF NOT EXISTS is_synthetic boolean NOT NULL DEFAULT false;

-- FoW dampener history (effective score snapshots; PRD2 §6)
CREATE TABLE IF NOT EXISTS public.card_confidence_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL REFERENCES public.cards (id) ON DELETE CASCADE,
  confidence_raw numeric(4, 3),
  confidence_effective numeric(4, 3),
  fog_active boolean NOT NULL DEFAULT false,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  is_synthetic boolean NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_card_confidence_history_card_id
  ON public.card_confidence_history (card_id, recorded_at DESC);

COMMENT ON TABLE public.card_confidence_history IS
  'Append-only confidence snapshots when FoW dampener applies (PRD2); never mutates events.confidence_raw.';

-- RLS: hide synthetic rows from authenticated (PostgREST / direct JWT reads)
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS events_hide_synthetic ON public.events;
CREATE POLICY events_hide_synthetic
  ON public.events
  FOR SELECT
  TO authenticated
  USING (NOT is_synthetic);

ALTER TABLE public.signals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS signals_hide_synthetic ON public.signals;
CREATE POLICY signals_hide_synthetic
  ON public.signals
  FOR SELECT
  TO authenticated
  USING (NOT is_synthetic);

ALTER TABLE public.user_predictions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS user_predictions_hide_synthetic ON public.user_predictions;
CREATE POLICY user_predictions_hide_synthetic
  ON public.user_predictions
  FOR SELECT
  TO authenticated
  USING (NOT is_synthetic);

ALTER TABLE public.card_confidence_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS card_confidence_history_hide_synthetic ON public.card_confidence_history;
CREATE POLICY card_confidence_history_hide_synthetic
  ON public.card_confidence_history
  FOR SELECT
  TO authenticated
  USING (NOT is_synthetic);

-- track_record: tighten authenticated read (was USING (true))
DROP POLICY IF EXISTS track_record_select_authenticated ON public.track_record;
CREATE POLICY track_record_select_authenticated
  ON public.track_record
  FOR SELECT
  TO authenticated
  USING (NOT is_synthetic);
