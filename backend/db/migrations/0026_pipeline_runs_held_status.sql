-- P3-S1f / P3-T2: allow critical-fact hold status on pipeline_runs telemetry.

ALTER TABLE public.pipeline_runs
  DROP CONSTRAINT IF EXISTS pipeline_runs_status_check;

ALTER TABLE public.pipeline_runs
  ADD CONSTRAINT pipeline_runs_status_check
  CHECK (status IN ('ok', 'error', 'held'));

COMMENT ON COLUMN public.pipeline_runs.status IS
  'ok = success; error = pipeline failure; held = blocked by critical-facts gate (P3-S1f).';
