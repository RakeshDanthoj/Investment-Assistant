-- P3-S1c / G-03: post-ingest dedup merge columns, editorial guardrail, cross-category review queue.

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS source_count integer NOT NULL DEFAULT 1;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS sources jsonb NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS force_editorial_review boolean NOT NULL DEFAULT false;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS collision_fingerprint text;

CREATE INDEX IF NOT EXISTS idx_events_collision_fingerprint
  ON public.events (collision_fingerprint)
  WHERE collision_fingerprint IS NOT NULL;

ALTER TABLE public.events
  ADD CONSTRAINT events_source_count_positive CHECK (source_count >= 1);

CREATE TABLE IF NOT EXISTS public.dedup_review_queue (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_ids uuid[] NOT NULL,
  reason text NOT NULL,
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'merged', 'dismissed')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dedup_review_queue_status
  ON public.dedup_review_queue (status, created_at DESC);

COMMENT ON TABLE public.dedup_review_queue IS
  'Cross-category same-window collisions flagged for Sunday editorial review (G-03).';

COMMENT ON COLUMN public.events.collision_fingerprint IS
  'sha256(entity|4h_window|headline_hash) — category-agnostic collision probe.';

COMMENT ON COLUMN public.events.force_editorial_review IS
  'Set when source_count > 5 (G-03 guardrail) regardless of confidence score.';
