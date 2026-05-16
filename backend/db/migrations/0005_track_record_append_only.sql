-- FinnWise P1-S4: append-only enforcement for track_record (PRD §6.4, §11.1)

ALTER TABLE public.track_record ENABLE ROW LEVEL SECURITY;

REVOKE UPDATE, DELETE ON public.track_record FROM PUBLIC;
REVOKE UPDATE, DELETE ON public.track_record FROM anon;
REVOKE UPDATE, DELETE ON public.track_record FROM authenticated;
REVOKE UPDATE, DELETE ON public.track_record FROM service_role;

DROP POLICY IF EXISTS track_record_select_authenticated ON public.track_record;
CREATE POLICY track_record_select_authenticated
  ON public.track_record
  FOR SELECT
  TO authenticated
  USING (true);

DROP POLICY IF EXISTS track_record_insert_authenticated ON public.track_record;
CREATE POLICY track_record_insert_authenticated
  ON public.track_record
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

DROP POLICY IF EXISTS track_record_select_service_role ON public.track_record;
CREATE POLICY track_record_select_service_role
  ON public.track_record
  FOR SELECT
  TO service_role
  USING (true);

DROP POLICY IF EXISTS track_record_insert_service_role ON public.track_record;
CREATE POLICY track_record_insert_service_role
  ON public.track_record
  FOR INSERT
  TO service_role
  WITH CHECK (true);

-- Explicit deny policies (no permissive UPDATE/DELETE policies exist; these document intent)
DROP POLICY IF EXISTS track_record_deny_update ON public.track_record;
CREATE POLICY track_record_deny_update
  ON public.track_record
  FOR UPDATE
  TO authenticated, service_role, anon
  USING (false);

DROP POLICY IF EXISTS track_record_deny_delete ON public.track_record;
CREATE POLICY track_record_deny_delete
  ON public.track_record
  FOR DELETE
  TO authenticated, service_role, anon
  USING (false);

CREATE OR REPLACE FUNCTION public.deny_track_record_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  RAISE EXCEPTION 'track_record is append-only: % is not permitted', TG_OP
    USING ERRCODE = '42501';
END;
$$;

DROP TRIGGER IF EXISTS track_record_deny_update ON public.track_record;
CREATE TRIGGER track_record_deny_update
  BEFORE UPDATE ON public.track_record
  FOR EACH ROW
  EXECUTE FUNCTION public.deny_track_record_mutation();

DROP TRIGGER IF EXISTS track_record_deny_delete ON public.track_record;
CREATE TRIGGER track_record_deny_delete
  BEFORE DELETE ON public.track_record
  FOR EACH ROW
  EXECUTE FUNCTION public.deny_track_record_mutation();
