-- PI-S0: read views for Map, Mirror, and Lens performance paths.

-- Map index: replaces list_sectors GROUP BY (one query, no Python aggregation).
CREATE OR REPLACE VIEW public.map_sector_list_v AS
SELECT
  s.slug,
  s.name,
  count(i.id)::int AS instrument_count
FROM public.sectors AS s
LEFT JOIN public.instruments AS i ON i.sector_id = s.id
GROUP BY s.slug, s.name;

COMMENT ON VIEW public.map_sector_list_v IS
  'Sector index rows with instrument counts for The Map list screen (PI-S0).';

-- Map sector detail (summary): sector metadata, modules JSON, instrument count — no matrix.
CREATE OR REPLACE VIEW public.map_sector_summary_v AS
SELECT
  s.slug,
  s.name,
  count(DISTINCT i.id)::int AS instrument_count,
  coalesce(
    (
      SELECT json_agg(
        json_build_object(
          'id', mm.id,
          'sector_slug', mm.sector_slug,
          'title', mm.title,
          'body', mm.body,
          'linked_gap_types', mm.linked_gap_types,
          'sort_order', mm.sort_order
        )
        ORDER BY mm.sort_order, mm.title
      )
      FROM public.map_modules AS mm
      WHERE mm.sector_slug = s.slug
    ),
    '[]'::json
  ) AS modules
FROM public.sectors AS s
LEFT JOIN public.instruments AS i ON i.sector_id = s.id
GROUP BY s.slug, s.name;

COMMENT ON VIEW public.map_sector_summary_v IS
  'Per-sector summary payload without sensitivity matrix (PI-S0 / PI-S1).';

-- Map sector matrix: factors, instruments, and flat sensitivity rows as JSON (PI-S1 reshapes).
CREATE OR REPLACE VIEW public.map_sector_matrix_v AS
SELECT
  s.slug AS sector_slug,
  json_build_object('slug', s.slug, 'name', s.name) AS sector,
  (
    SELECT coalesce(
      json_agg(
        json_build_object(
          'slug', f.slug,
          'display_name', f.display_name,
          'sort_order', f.sort_order,
          'description', f.description
        )
        ORDER BY f.sort_order
      ),
      '[]'::json
    )
    FROM public.factors AS f
  ) AS factors,
  coalesce(
    (
      SELECT json_agg(
        json_build_object(
          'id', inst.id,
          'ticker', inst.ticker,
          'display_name', inst.display_name,
          'isin', inst.isin,
          'exchange', inst.exchange
        )
        ORDER BY upper(inst.ticker)
      )
      FROM public.instruments AS inst
      WHERE inst.sector_id = s.id
    ),
    '[]'::json
  ) AS instruments,
  coalesce(
    (
      SELECT json_agg(
        json_build_object(
          'ticker', inst.ticker,
          'factor_slug', fc.slug,
          'sensitivity', sens.sensitivity,
          'mmj_tag', sens.mmj_tag::text,
          'source_url', sens.source_url,
          'retrieved_at', sens.retrieved_at
        )
      )
      FROM public.instruments AS inst
      INNER JOIN public.instrument_factor_sensitivity AS sens
        ON sens.instrument_id = inst.id
      INNER JOIN public.factors AS fc ON fc.id = sens.factor_id
      WHERE inst.sector_id = s.id
    ),
    '[]'::json
  ) AS sensitivity_rows
FROM public.sectors AS s;

COMMENT ON VIEW public.map_sector_matrix_v IS
  'Per-sector matrix payload; sensitivity_rows is reshaped in Python (PI-S0 / PI-S1).';

-- Mirror predictions: joined rows for list + stats (synthetic rows excluded).
CREATE OR REPLACE VIEW public.mirror_user_predictions_v AS
SELECT
  up.id,
  up.user_id,
  up.card_id,
  up.prediction_text,
  up.logged_at,
  up.mechanism_accuracy,
  up.business_accuracy,
  up.market_accuracy,
  up.gap_insight,
  c.title AS card_title,
  c.lifecycle_state::text AS lifecycle_state,
  e.title AS event_title,
  e.category::text AS event_category
FROM public.user_predictions AS up
INNER JOIN public.cards AS c ON c.id = up.card_id
INNER JOIN public.events AS e ON e.id = c.event_id
WHERE up.is_synthetic IS NOT TRUE
  AND e.is_synthetic IS NOT TRUE;

COMMENT ON VIEW public.mirror_user_predictions_v IS
  'Mirror prediction list + stats input with card/event joins (PI-S0 / PI-S2).';

-- Mirror streak: last 14 mechanism grades per user (most recent first).
CREATE OR REPLACE VIEW public.mirror_user_streak_v AS
SELECT
  ranked.user_id,
  ranked.mechanism_accuracy,
  ranked.logged_at,
  ranked.streak_rank
FROM (
  SELECT
    up.user_id,
    up.mechanism_accuracy,
    up.logged_at,
    row_number() OVER (
      PARTITION BY up.user_id
      ORDER BY up.logged_at DESC
    ) AS streak_rank
  FROM public.user_predictions AS up
  WHERE up.is_synthetic IS NOT TRUE
) AS ranked
WHERE ranked.streak_rank <= 14;

COMMENT ON VIEW public.mirror_user_streak_v IS
  'Last 14 mechanism grades per user for Mirror streak grid (PI-S0 / PI-S2).';

-- Mirror gap detector: graded resolved predictions with sector slug (limit 50 via history_rank).
CREATE OR REPLACE VIEW public.mirror_graded_history_v AS
SELECT
  ranked.user_id,
  ranked.mechanism_accuracy,
  ranked.business_accuracy,
  ranked.market_accuracy,
  ranked.sector_slug,
  ranked.logged_at,
  ranked.history_rank
FROM (
  SELECT
    up.user_id,
    up.mechanism_accuracy,
    up.business_accuracy,
    up.market_accuracy,
    up.logged_at,
    (
      SELECT sec.slug
      FROM public.instrument_assessments AS ia
      INNER JOIN public.instruments AS inst
        ON inst.ticker = ia.instrument_id
        AND inst.exchange = 'NSE'
      INNER JOIN public.sectors AS sec ON sec.id = inst.sector_id
      WHERE ia.card_id = c.id
      ORDER BY ia.created_at ASC
      LIMIT 1
    ) AS sector_slug,
    row_number() OVER (
      PARTITION BY up.user_id
      ORDER BY up.logged_at DESC
    ) AS history_rank
  FROM public.user_predictions AS up
  INNER JOIN public.cards AS c ON c.id = up.card_id
  WHERE c.lifecycle_state::text = 'resolved'
    AND up.mechanism_accuracy IS NOT NULL
    AND up.is_synthetic IS NOT TRUE
) AS ranked
WHERE ranked.history_rank <= 50;

COMMENT ON VIEW public.mirror_graded_history_v IS
  'Graded resolved predictions for reasoning-gap analysis (PI-S0 / PI-S2).';

-- Lens: recent queries per user with rank for LIMIT 20 filter.
CREATE OR REPLACE VIEW public.lens_user_queries_v AS
SELECT
  lq.id,
  lq.user_id,
  lq.query,
  lq.sector::text AS sector,
  lq.horizon,
  lq.status::text AS status,
  lq.card_id,
  lq.created_at,
  row_number() OVER (
    PARTITION BY lq.user_id
    ORDER BY lq.created_at DESC
  ) AS recent_rank
FROM public.lens_queries AS lq;

COMMENT ON VIEW public.lens_user_queries_v IS
  'Lens query history with per-user rank; filter recent_rank <= 20 (PI-S0 / PI-S3).';
