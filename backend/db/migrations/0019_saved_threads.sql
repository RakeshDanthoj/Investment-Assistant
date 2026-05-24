-- P2-S8: Lens cards saved to personal Thread collection

CREATE TABLE IF NOT EXISTS public.saved_threads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  card_id uuid NOT NULL REFERENCES public.cards (id) ON DELETE CASCADE,
  saved_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, card_id)
);

CREATE INDEX IF NOT EXISTS saved_threads_user_saved_idx
  ON public.saved_threads (user_id, saved_at DESC);

COMMENT ON TABLE public.saved_threads IS
  'User-saved Lens (or other) cards surfaced in Thread sidebar Saved sub-nav.';
