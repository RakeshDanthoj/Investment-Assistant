-- P2-S2: Mirror gap insight text (accuracy cols already in 0004_core_tables.sql)

ALTER TABLE public.user_predictions
  ADD COLUMN IF NOT EXISTS gap_insight text;

COMMENT ON COLUMN public.user_predictions.gap_insight IS
  'Plain-English reasoning gap vs Original View; populated by prediction_grader on card resolve.';
