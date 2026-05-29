-- P2.5-S2: indexes for Pulse feed and Thread card-detail read paths.

-- Feed: lifecycle filter + created_at sort (visible cards only).
CREATE INDEX IF NOT EXISTS idx_cards_visible_feed_created
  ON public.cards (created_at DESC)
  WHERE lifecycle_state IN (
    'published'::public.lifecycle_state,
    'active'::public.lifecycle_state,
    'signal_triggered'::public.lifecycle_state,
    'thesis_confirmed'::public.lifecycle_state,
    'thesis_weakened'::public.lifecycle_state,
    'resolved'::public.lifecycle_state
  );

CREATE INDEX IF NOT EXISTS idx_cards_lifecycle_created
  ON public.cards (lifecycle_state, created_at DESC);

-- Fog-of-War scan: active / signal_triggered majors.
CREATE INDEX IF NOT EXISTS idx_cards_fog_lifecycle
  ON public.cards (lifecycle_state, event_id)
  WHERE lifecycle_state IN (
    'active'::public.lifecycle_state,
    'signal_triggered'::public.lifecycle_state
  );

-- Events joined on feed + FoW with synthetic filter and category filter.
CREATE INDEX IF NOT EXISTS idx_events_not_synthetic_category
  ON public.events (category)
  WHERE is_synthetic IS NOT TRUE;

CREATE INDEX IF NOT EXISTS idx_events_major_not_synthetic
  ON public.events (confidence_score DESC, category)
  WHERE is_synthetic IS NOT TRUE
    AND confidence_score >= 70;

-- Feed instrument batch: version = 1 only.
CREATE INDEX IF NOT EXISTS idx_instrument_assessments_card_v1
  ON public.instrument_assessments (card_id)
  WHERE version = 1;
