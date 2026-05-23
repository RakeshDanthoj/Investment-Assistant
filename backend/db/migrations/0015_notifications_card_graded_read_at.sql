-- P2-S3 — Resolved-card notifications (card_graded) + read tracking for Mirror badge.

ALTER TABLE public.in_app_notifications
  ADD COLUMN IF NOT EXISTS read_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_in_app_notifications_card_graded_unread
  ON public.in_app_notifications (user_id, created_at DESC)
  WHERE kind = 'card_graded' AND read_at IS NULL;

COMMENT ON COLUMN public.in_app_notifications.read_at IS
  'Set when the user views the graded prediction (viewport intersection on Mirror). NULL = unread.';

COMMENT ON COLUMN public.in_app_notifications.kind IS
  'Notification kind: card_published, signal_fired, card_graded (P2-S3), etc.';
