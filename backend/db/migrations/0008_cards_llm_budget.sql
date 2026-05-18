-- P1-S7 — Event Intelligence Cards parent table + LLM daily generation cap (PRD §12 risk 7).
-- Child tables from 0004 reference card_id; this migration introduces the parent `cards` row.

CREATE TABLE IF NOT EXISTS public.cards (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id uuid NOT NULL REFERENCES public.events (id) ON DELETE CASCADE,
  title text NOT NULL,
  insight_layer text NOT NULL DEFAULT '',
  context_layer text NOT NULL DEFAULT '',
  evidence_layer jsonb NOT NULL DEFAULT '{}'::jsonb,
  dissenting_view text NOT NULL DEFAULT '',
  framework_behind_this text NOT NULL DEFAULT '',
  prompt_version text NOT NULL,
  lifecycle_state public.lifecycle_state NOT NULL DEFAULT 'draft',
  llm_input_tokens integer NOT NULL DEFAULT 0
    CHECK (llm_input_tokens >= 0),
  llm_output_tokens integer NOT NULL DEFAULT 0
    CHECK (llm_output_tokens >= 0),
  llm_cost_usd numeric(14, 6) NOT NULL DEFAULT 0
    CHECK (llm_cost_usd >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cards_event_id ON public.cards (event_id);
CREATE INDEX IF NOT EXISTS idx_cards_lifecycle_state ON public.cards (lifecycle_state);
CREATE INDEX IF NOT EXISTS idx_cards_created_at ON public.cards (created_at DESC);

COMMENT ON TABLE public.cards IS
  'Event Intelligence Card (ICE) — Insight / Context / Evidence + dissent + framework (P1-S7).';

CREATE TABLE IF NOT EXISTS public.llm_card_daily_usage (
  usage_date date PRIMARY KEY,
  generations_count integer NOT NULL DEFAULT 0
    CHECK (generations_count >= 0)
);

COMMENT ON TABLE public.llm_card_daily_usage IS
  'UTC calendar-day counter for LLM card drafts; hard cap 50/day (PRD §12).';

-- Atomic: returns true if a generation slot was consumed, false if at cap.
CREATE OR REPLACE FUNCTION public.try_consume_llm_card_slot(p_max integer DEFAULT 50)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO public AS $$
DECLARE
  d date := (timezone('utc', now()))::date;
  cur integer;
BEGIN
  SELECT generations_count INTO cur
  FROM public.llm_card_daily_usage
  WHERE usage_date = d
  FOR UPDATE;

  IF NOT FOUND THEN
    INSERT INTO public.llm_card_daily_usage (usage_date, generations_count)
    VALUES (d, 1);
    RETURN true;
  END IF;

  IF cur >= p_max THEN
    RETURN false;
  END IF;

  UPDATE public.llm_card_daily_usage
  SET generations_count = generations_count + 1
  WHERE usage_date = d;
  RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION public.try_consume_llm_card_slot(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.try_consume_llm_card_slot(integer) TO service_role;

ALTER TABLE public.signals
  ADD CONSTRAINT signals_card_id_fkey
  FOREIGN KEY (card_id) REFERENCES public.cards (id) ON DELETE CASCADE;

ALTER TABLE public.instrument_assessments
  ADD CONSTRAINT instrument_assessments_card_id_fkey
  FOREIGN KEY (card_id) REFERENCES public.cards (id) ON DELETE CASCADE;
