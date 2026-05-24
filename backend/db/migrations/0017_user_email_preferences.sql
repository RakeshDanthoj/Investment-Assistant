-- P2-S10 — Email notifications for fired signals (prefs + unsubscribe tokens + send log).

CREATE TABLE IF NOT EXISTS public.user_email_preferences (
  user_id uuid PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
  signal_fired_enabled boolean NOT NULL DEFAULT true,
  updated_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.user_email_preferences IS
  'Per-user email channel preferences; default opt-in for Phase 2 testers.';

CREATE TABLE IF NOT EXISTS public.unsubscribe_tokens (
  token uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  used_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_unsubscribe_tokens_user_id
  ON public.unsubscribe_tokens (user_id);

COMMENT ON TABLE public.unsubscribe_tokens IS
  'Single-shot unsubscribe tokens embedded in signal-fired emails.';

CREATE TABLE IF NOT EXISTS public.signal_email_log (
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  signal_id uuid NOT NULL REFERENCES public.signals (id) ON DELETE CASCADE,
  sent_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, signal_id)
);

COMMENT ON TABLE public.signal_email_log IS
  'Idempotent send log — at most one signal-fired email per (user, signal).';
