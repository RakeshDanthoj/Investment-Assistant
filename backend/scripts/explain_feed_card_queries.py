#!/usr/bin/env python3
"""EXPLAIN (ANALYZE, BUFFERS) for Pulse feed and Thread card-detail read paths (P2.5-S2)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "backend"))


def main() -> int:
    import psycopg
    from psycopg.rows import dict_row

    from app.core.settings import get_settings
    from app.db.queries.base import SyntheticFilterMixin
    from app.services.feed import (
        FEED_INSIGHT_SQL_CHARS,
        FEED_ROW_LIMIT,
        FOG_LIFECYCLE,
        MAJOR_EVENT_MIN_CONFIDENCE,
        VISIBLE_CARD_STATES,
    )

    url = get_settings().supabase_db_url.strip()
    if not url:
        print("SUPABASE_DB_URL is not set in .env.local", file=sys.stderr)
        return 1

    synth = SyntheticFilterMixin.events_not_synthetic("e")
    lifecycle_states = list(VISIBLE_CARD_STATES)
    fog_states = list(FOG_LIFECYCLE)

    feed_bundle_sql = f"""
    WITH pulse_rows AS (
      SELECT
        c.id,
        c.title,
        LEFT(
          regexp_replace(c.insight_layer, E'[\\n\\r]+', ' ', 'g'),
          {FEED_INSIGHT_SQL_CHARS}
        ) AS insight_layer,
        c.lifecycle_state::text AS lifecycle_state,
        c.created_at,
        c.updated_at,
        e.id AS event_id,
        e.title AS event_title,
        e.category::text AS category,
        e.confidence_score AS confidence_score
      FROM public.cards c
      INNER JOIN public.events e ON e.id = c.event_id AND {synth}
      WHERE c.lifecycle_state = ANY(%s::public.lifecycle_state[])
      ORDER BY c.created_at DESC
      LIMIT {FEED_ROW_LIMIT}
    ),
    instruments AS (
      SELECT
        ia.card_id,
        json_agg(
          json_build_object(
            'instrument_id', ia.instrument_id,
            'signal_type', ia.signal_type
          )
          ORDER BY ia.instrument_id
        ) AS instruments
      FROM public.instrument_assessments ia
      WHERE ia.card_id IN (SELECT id FROM pulse_rows)
        AND ia.version = 1
      GROUP BY ia.card_id
    ),
    fog_relevant AS (
      SELECT e.category::text AS category
      FROM public.cards c
      INNER JOIN public.events e ON e.id = c.event_id AND {synth}
      WHERE c.lifecycle_state = ANY(%s::public.lifecycle_state[])
        AND e.confidence_score >= %s
    ),
    fog AS (
      SELECT
        (SELECT COUNT(*)::int FROM fog_relevant) >= 3
        AND COALESCE(
          (SELECT MAX(n) FROM (
            SELECT COUNT(*)::int AS n FROM fog_relevant GROUP BY category
          ) counts),
          0
        ) >= 2 AS fog_of_war
    )
    SELECT
      pr.id::text AS id,
      pr.title AS headline,
      pr.insight_layer,
      pr.lifecycle_state,
      pr.created_at,
      pr.updated_at,
      pr.event_id::text AS event_id,
      pr.event_title,
      pr.category,
      pr.confidence_score,
      COALESCE(i.instruments, '[]'::json) AS instruments,
      f.fog_of_war
    FROM pulse_rows pr
    LEFT JOIN instruments i ON i.card_id = pr.id
    CROSS JOIN fog f
    ORDER BY pr.created_at DESC
    """

    feed_sql = f"""
    SELECT
      c.id::text AS id,
      c.title AS headline,
      LEFT(
        regexp_replace(c.insight_layer, E'[\\n\\r]+', ' ', 'g'),
        {FEED_INSIGHT_SQL_CHARS}
      ) AS insight_layer,
      c.lifecycle_state::text AS lifecycle_state,
      c.created_at,
      c.updated_at,
      e.id::text AS event_id,
      e.title AS event_title,
      e.category::text AS category,
      e.confidence_score AS confidence_score
    FROM public.cards c
    INNER JOIN public.events e ON e.id = c.event_id
    WHERE c.lifecycle_state = ANY(%s::public.lifecycle_state[])
      AND {synth}
    ORDER BY c.created_at DESC
    LIMIT {FEED_ROW_LIMIT}
    """

    fog_sql = f"""
    WITH relevant AS (
      SELECT e.category::text AS category
      FROM public.cards c
      INNER JOIN public.events e ON e.id = c.event_id
      WHERE c.lifecycle_state = ANY(%s::public.lifecycle_state[])
        AND e.confidence_score >= %s
        AND {synth}
    )
    SELECT
      (SELECT COUNT(*)::int FROM relevant) >= 3
      AND COALESCE(
        (SELECT MAX(n) FROM (
          SELECT COUNT(*)::int AS n FROM relevant GROUP BY category
        ) counts),
        0
      ) >= 2 AS fog_of_war
    """

    card_sql = f"""
    SELECT
      c.id AS card_id,
      c.event_id,
      c.title,
      c.insight_layer,
      c.context_layer,
      c.evidence_layer,
      c.dissenting_view,
      c.framework_behind_this,
      c.prompt_version,
      c.lifecycle_state,
      c.created_at AS card_created_at,
      e.title AS event_title,
      e.category::text AS event_category,
      e.confidence_score AS event_confidence_score,
      e.lifecycle_state::text AS event_lifecycle_state,
      e.canonical_url AS event_canonical_url,
      COALESCE(
        (
          SELECT jsonb_agg(
            jsonb_build_object(
              'signal_text', s.signal_text,
              'state', s.state::text
            )
            ORDER BY s.created_at ASC
          )
          FROM public.signals s
          WHERE s.card_id = c.id
        ),
        '[]'::jsonb
      ) AS signals,
      COALESCE(
        (
          SELECT jsonb_agg(
            jsonb_build_object(
              'instrument_id', ia.instrument_id,
              'signal_type', ia.signal_type,
              'reasoning', ia.reasoning,
              'entry_conditions', ia.entry_conditions,
              'exit_conditions', ia.exit_conditions
            )
            ORDER BY ia.created_at ASC
          )
          FROM public.instrument_assessments ia
          WHERE ia.card_id = c.id
        ),
        '[]'::jsonb
      ) AS instruments,
      COALESCE(
        (
          SELECT jsonb_agg(
            jsonb_build_object(
              'bias_type', bf.bias_type,
              'severity', bf.severity,
              'description', bf.description,
              'detected_at', bf.detected_at
            )
            ORDER BY bf.bias_type
          )
          FROM public.card_bias_flags bf
          WHERE bf.card_id = c.id
        ),
        '[]'::jsonb
      ) AS bias_flags
    FROM public.cards c
    INNER JOIN public.events e ON e.id = c.event_id
    WHERE c.id = %s
      AND {synth}
    LIMIT 1
    """

    assessments_sql = """
    SELECT card_id::text, instrument_id, signal_type
    FROM public.instrument_assessments
    WHERE card_id = ANY(%s::uuid[])
      AND version = 1
    ORDER BY instrument_id
    """

    out: dict[str, object] = {"queries": []}

    with psycopg.connect(url) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT c.id::text AS id
            FROM public.cards c
            WHERE c.lifecycle_state = ANY(%s::public.lifecycle_state[])
            ORDER BY c.created_at DESC
            LIMIT 1
            """,
            (lifecycle_states,),
        )
        sample = cur.fetchone()
        if not sample:
            print("No visible cards in database — cannot EXPLAIN card detail.", file=sys.stderr)
            return 1
        card_id = sample["id"]

        cur.execute(
            """
            SELECT card_id::text AS id
            FROM public.instrument_assessments
            WHERE version = 1
            ORDER BY card_id
            LIMIT 60
            """
        )
        card_ids = [row["id"] for row in cur.fetchall()]

        plans: list[tuple[str, str, tuple[object, ...]]] = [
            (
                "feed_bundle_single_round_trip",
                feed_bundle_sql,
                (lifecycle_states, fog_states, MAJOR_EVENT_MIN_CONFIDENCE),
            ),
            ("feed_pulse_rows_legacy", feed_sql, (lifecycle_states,)),
            ("feed_fog_of_war", fog_sql, (fog_states, MAJOR_EVENT_MIN_CONFIDENCE)),
            ("feed_instrument_batch", assessments_sql, (card_ids,)),
            ("card_detail_bundle", card_sql, (card_id,)),
        ]

        for label, sql, params in plans:
            with conn.cursor() as plan_cur:
                plan_cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {sql}", params)
                plan_lines = [row[0] for row in plan_cur.fetchall()]
            out["queries"].append({"label": label, "plan": plan_lines})

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
