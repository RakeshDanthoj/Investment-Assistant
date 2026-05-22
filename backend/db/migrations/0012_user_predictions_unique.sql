-- P1-S12: ensure one prediction per (user_id, card_id).
-- Idempotent — constraint may already exist from 0004_core_tables.sql.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'user_predictions_user_card_key'
      AND conrelid = 'public.user_predictions'::regclass
  ) THEN
    ALTER TABLE public.user_predictions
      ADD CONSTRAINT user_predictions_user_card_key UNIQUE (user_id, card_id);
  END IF;
END $$;
