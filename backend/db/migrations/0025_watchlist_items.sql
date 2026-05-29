-- P3-S1e / G-05: slow-burn editorial watchlist + seed categories.

CREATE TABLE IF NOT EXISTS public.watchlist_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_description text NOT NULL,
  category text NOT NULL,
  added_at timestamptz NOT NULL DEFAULT now(),
  review_frequency text NOT NULL DEFAULT 'weekly'
    CHECK (review_frequency IN ('daily', 'weekly', 'monthly')),
  last_reviewed_at timestamptz,
  escalation_trigger text,
  status text NOT NULL DEFAULT 'watching'
    CHECK (status IN ('watching', 'escalated', 'closed')),
  escalated_event_id uuid REFERENCES public.events (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_watchlist_items_status
  ON public.watchlist_items (status, added_at DESC);

COMMENT ON TABLE public.watchlist_items IS
  'Slow-burn events for Sunday editorial review (G-05). Manual escalate only in Phase 3.';

COMMENT ON COLUMN public.watchlist_items.escalation_trigger IS
  'Human-readable condition for escalation; auto-monitoring deferred to Phase 4.';

-- Idempotent seeds (fixed ids for stable references in docs/tests).
INSERT INTO public.watchlist_items (
  id,
  event_description,
  category,
  review_frequency,
  escalation_trigger,
  status
) VALUES
  (
    'a1000001-0001-4001-8001-000000000001',
    'Maharashtra state election calendar — market-sensitive outcomes (UP-style swing risk)',
    'india_specific',
    'weekly',
    'Election dates announced or exit polls move Nifty volatility index > 15%',
    'watching'
  ),
  (
    'a1000001-0001-4001-8001-000000000002',
    'Pending SEBI consultation papers affecting F&O / algo trading norms',
    'regulatory',
    'weekly',
    'SEBI publishes final circular or closes consultation with material rule change',
    'watching'
  ),
  (
    'a1000001-0001-4001-8001-000000000003',
    'IMD monsoon 2025 seasonal outlook — April / June / August revision windows',
    'macro',
    'monthly',
    'IMD revises seasonal rainfall forecast downward by more than 5% vs prior',
    'watching'
  ),
  (
    'a1000001-0001-4001-8001-000000000004',
    'Union Budget 2026 cycle — interim vs full budget expectations and capex signals',
    'budget',
    'weekly',
    'Finance Ministry releases budget date or leaked capex/tax measures hit newswires',
    'watching'
  ),
  (
    'a1000001-0001-4001-8001-000000000005',
    'India–China trade dispute / import restrictions on critical industrial inputs',
    'geopolitical',
    'weekly',
    'Commerce Ministry notification on tariffs or sanctions affecting listed importers',
    'watching'
  )
ON CONFLICT (id) DO NOTHING;
