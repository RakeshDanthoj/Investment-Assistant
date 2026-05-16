-- FinnWise P1-S4: Tier 2 analytical tables (PRD §7.2)

CREATE TABLE IF NOT EXISTS public.events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  category public.event_category NOT NULL,
  source_url text,
  confidence_score smallint NOT NULL
    CHECK (confidence_score >= 0 AND confidence_score <= 100),
  lifecycle_state public.lifecycle_state NOT NULL DEFAULT 'draft',
  prompt_version text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_lifecycle_state ON public.events (lifecycle_state);
CREATE INDEX IF NOT EXISTS idx_events_category ON public.events (category);

CREATE TABLE IF NOT EXISTS public.signals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL,
  signal_text text NOT NULL,
  state public.signal_state NOT NULL DEFAULT 'pending',
  triggered_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_signals_card_id ON public.signals (card_id);
CREATE INDEX IF NOT EXISTS idx_signals_state ON public.signals (state);

CREATE TABLE IF NOT EXISTS public.instrument_assessments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL,
  version integer NOT NULL DEFAULT 1,
  instrument_id text NOT NULL,
  signal_type text NOT NULL,
  reasoning text,
  entry_conditions text[] NOT NULL DEFAULT '{}',
  exit_conditions text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT instrument_assessments_card_instrument_version_key
    UNIQUE (card_id, instrument_id, version)
);

CREATE INDEX IF NOT EXISTS idx_instrument_assessments_card_id
  ON public.instrument_assessments (card_id);

CREATE TABLE IF NOT EXISTS public.user_predictions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  card_id uuid NOT NULL,
  prediction_text text NOT NULL,
  logged_at timestamptz NOT NULL DEFAULT now(),
  mechanism_accuracy text,
  business_accuracy text,
  market_accuracy text,
  CONSTRAINT user_predictions_user_card_key UNIQUE (user_id, card_id)
);

CREATE INDEX IF NOT EXISTS idx_user_predictions_user_id ON public.user_predictions (user_id);
CREATE INDEX IF NOT EXISTS idx_user_predictions_card_id ON public.user_predictions (card_id);

CREATE TABLE IF NOT EXISTS public.track_record (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  logged_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_track_record_card_id ON public.track_record (card_id);
CREATE INDEX IF NOT EXISTS idx_track_record_logged_at ON public.track_record (logged_at DESC);
