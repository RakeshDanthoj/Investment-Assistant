-- P1-S8 — Editorial publish notifications + optional category subscription on profiles.

ALTER TABLE public.session_profiles
  ADD COLUMN IF NOT EXISTS notify_categories text[];

COMMENT ON COLUMN public.session_profiles.notify_categories IS
  'When NULL or empty, user receives in-app alerts for cards in any event category; '
  'otherwise only when card.event.category matches one of these slugs (text[]).';

CREATE TABLE IF NOT EXISTS public.in_app_notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  card_id uuid NOT NULL REFERENCES public.cards (id) ON DELETE CASCADE,
  kind text NOT NULL DEFAULT 'card_published',
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_in_app_notifications_user_id
  ON public.in_app_notifications (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_in_app_notifications_card_id
  ON public.in_app_notifications (card_id);

COMMENT ON TABLE public.in_app_notifications IS
  'Phase 1 in-app alerts (no outbound push); user_id aligns with session_profiles.user_id / auth.users.';
