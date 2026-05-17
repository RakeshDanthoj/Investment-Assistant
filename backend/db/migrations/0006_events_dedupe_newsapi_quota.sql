-- P1-S6: dedupe events by adapter + canonical URL; NewsAPI daily quota tracking (PRD §7.3).

CREATE TABLE IF NOT EXISTS public.news_api_daily_usage (
  usage_date date PRIMARY KEY,
  api_call_count smallint NOT NULL DEFAULT 0
    CONSTRAINT news_api_daily_usage_count_nonneg CHECK (api_call_count >= 0)
);

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS event_source text;

ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS canonical_url text;

-- Backfill for any pre-P1-S6 rows (prefer existing source_url).
UPDATE public.events
SET
  canonical_url =
    CASE
      WHEN canonical_url IS NOT NULL AND canonical_url <> '' THEN canonical_url
      WHEN source_url IS NOT NULL AND source_url <> '' THEN source_url
      ELSE canonical_url
    END,
  event_source = COALESCE(NULLIF(TRIM(event_source), ''), 'legacy')
WHERE canonical_url IS NULL
   OR canonical_url = ''
   OR event_source IS NULL;

-- Rows that still lack a canonical URL get a deterministic synthetic key (migration-only legacy).
UPDATE public.events
SET canonical_url = 'legacy:no-url:' || id::text
WHERE canonical_url IS NULL OR canonical_url = '';

ALTER TABLE public.events
  ALTER COLUMN canonical_url SET NOT NULL;

ALTER TABLE public.events
  ALTER COLUMN event_source SET NOT NULL;

DROP INDEX IF EXISTS events_source_canonical_uidx;
CREATE UNIQUE INDEX events_source_canonical_uidx ON public.events (event_source, canonical_url);

-- Atomic budget check + increment per calendar day UTC (stay under NewsAPI free tier; PRD §7.3).
CREATE OR REPLACE FUNCTION public.try_newsapi_call_budget(p_max smallint DEFAULT 99)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO public AS $$
DECLARE
  d date := (timezone('utc', now()))::date;
  cur smallint;
BEGIN
  SELECT api_call_count INTO cur FROM public.news_api_daily_usage WHERE usage_date = d FOR UPDATE;
  IF NOT FOUND THEN
    INSERT INTO public.news_api_daily_usage (usage_date, api_call_count) VALUES (d, 1);
    RETURN true;
  END IF;
  IF cur >= p_max THEN
    RETURN false;
  END IF;
  UPDATE public.news_api_daily_usage SET api_call_count = api_call_count + 1 WHERE usage_date = d;
  RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION public.try_newsapi_call_budget(smallint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.try_newsapi_call_budget(smallint) TO service_role;
