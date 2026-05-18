-- P1-S11 — Signal monitoring, confidence gate audit trail, digest, editorial queue.

ALTER TABLE public.cards
  ADD COLUMN IF NOT EXISTS editor_override_deadline timestamptz NULL;

COMMENT ON COLUMN public.cards.editor_override_deadline IS
  'After a high-confidence auto-update, editors may override until this timestamp (UTC).';

CREATE TABLE IF NOT EXISTS public.confidence_gate_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL REFERENCES public.cards (id) ON DELETE CASCADE,
  signal_id uuid NOT NULL REFERENCES public.signals (id) ON DELETE CASCADE,
  gate text NOT NULL CHECK (gate IN ('high', 'medium', 'low')),
  reason text NOT NULL,
  sources jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_confidence_gate_log_card_id
  ON public.confidence_gate_log (card_id, created_at DESC);

COMMENT ON TABLE public.confidence_gate_log IS
  'Append-only audit of High/Medium/Low routing for override-rate analysis (PRD §13).';

CREATE TABLE IF NOT EXISTS public.digest_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid REFERENCES public.cards (id) ON DELETE SET NULL,
  signal_id uuid REFERENCES public.signals (id) ON DELETE SET NULL,
  gate text NOT NULL DEFAULT 'low',
  summary text NOT NULL DEFAULT '',
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_digest_log_created_at
  ON public.digest_log (created_at DESC);

COMMENT ON TABLE public.digest_log IS
  'Low-confidence signal hits: internal digest only, no card mutation.';

CREATE TABLE IF NOT EXISTS public.editorial_signal_queue (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL REFERENCES public.cards (id) ON DELETE CASCADE,
  signal_id uuid NOT NULL REFERENCES public.signals (id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'dismissed', 'resolved')),
  gate text NOT NULL DEFAULT 'medium',
  reason text NOT NULL DEFAULT '',
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT editorial_signal_queue_card_signal_key UNIQUE (card_id, signal_id)
);

CREATE INDEX IF NOT EXISTS idx_editorial_signal_queue_pending
  ON public.editorial_signal_queue (status, created_at DESC)
  WHERE status = 'pending';

COMMENT ON TABLE public.editorial_signal_queue IS
  'Medium-confidence signal hits awaiting editorial review before card changes.';
