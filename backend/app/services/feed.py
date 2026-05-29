"""Pulse feed queries + Fog of War detection (P1-S9)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from psycopg import Connection
from psycopg.rows import dict_row

from app.core.settings import get_settings
from app.db.connection import connection
from app.db.queries.base import SyntheticFilterMixin
from app.services.feed_ranker import rerank

# Major events: editor/model confidence on the parent event row.
MAJOR_EVENT_MIN_CONFIDENCE = 70

VISIBLE_CARD_STATES: tuple[str, ...] = (
    "published",
    "active",
    "signal_triggered",
    "thesis_confirmed",
    "thesis_weakened",
    "resolved",
)

FOG_LIFECYCLE: frozenset[str] = frozenset({"active", "signal_triggered"})

# First-paint feed cap (was 100); aligns with Pulse UI and reduces row/payload cost.
FEED_ROW_LIMIT = 60
# SQL pre-truncates insight text; build_card_payload trims to 320 chars for API.
FEED_INSIGHT_SQL_CHARS = 400

_HORIZON_DAYS: dict[str, int | None] = {
    "under_1y": 365,
    "1_3y": 3 * 365,
    "3_7y": 7 * 365,
    "7_plus": None,
}


@dataclass(frozen=True)
class SessionProfileRow:
    horizon: str
    mode: str


def horizon_cutoff(horizon: str, *, now: datetime | None = None) -> datetime | None:
    """Return earliest card `created_at` to include, or None for all time."""
    days = _HORIZON_DAYS.get(horizon)
    if days is None:
        return None
    ts = now or datetime.now(tz=UTC)
    return ts - timedelta(days=days)


def detect_fog_of_war(
    *,
    major_active_cards: Sequence[tuple[str, str]],
) -> bool:
    """
    True when ≥3 major cards are in an interactive lifecycle and at least one
    event category appears more than once (overlap / compounding context).
    Each tuple is (card_lifecycle_state, event_category).
    """
    relevant = [
        (life, cat)
        for life, cat in major_active_cards
        if life in FOG_LIFECYCLE
    ]
    if len(relevant) < 3:
        return False
    cat_counts: dict[str, int] = {}
    for _, cat in relevant:
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    return max(cat_counts.values(), default=0) >= 2


def _fetch_session_profile_conn(
    conn: Connection,
    session_id: UUID,
) -> SessionProfileRow | None:
    stmt = """
    SELECT horizon, mode
    FROM public.session_profiles
    WHERE session_id = %s
    LIMIT 1
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(session_id),))
        row = cur.fetchone()
    if not row:
        return None
    return SessionProfileRow(horizon=str(row["horizon"]), mode=str(row["mode"]))


def fetch_session_profile(session_id: UUID | None) -> SessionProfileRow | None:
    if session_id is None:
        return None
    with connection() as conn:
        return _fetch_session_profile_conn(conn, session_id)


def _fetch_fog_of_war_conn(conn: Connection) -> bool:
    """Aggregate in SQL instead of fetching every major active row (P2.5-S2)."""
    synth = SyntheticFilterMixin.events_not_synthetic("e")
    stmt = f"""
    WITH relevant AS (
      SELECT e.category::text AS category
      FROM public.cards c
      INNER JOIN public.events e ON e.id = c.event_id AND {synth}
      WHERE c.lifecycle_state = ANY(%s::public.lifecycle_state[])
        AND e.confidence_score >= %s
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
    states = list(FOG_LIFECYCLE)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (states, MAJOR_EVENT_MIN_CONFIDENCE))
        row = cur.fetchone()
    if not row:
        return False
    return bool(row["fog_of_war"])


def fetch_fog_of_war_flag() -> bool:
    with connection() as conn:
        return _fetch_fog_of_war_conn(conn)


def _assessments_for_cards_conn(
    conn: Connection,
    card_ids: list[str],
) -> dict[str, list[dict[str, str]]]:
    if not card_ids:
        return {}
    stmt = """
    SELECT card_id::text, instrument_id, signal_type
    FROM public.instrument_assessments
    WHERE card_id = ANY(%s::uuid[])
      AND version = 1
    ORDER BY instrument_id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (card_ids,))
        rows = cur.fetchall()
    out: dict[str, list[dict[str, str]]] = {cid: [] for cid in card_ids}
    for r in rows:
        cid = str(r["card_id"])
        out.setdefault(cid, []).append(
            {
                "instrument_id": str(r["instrument_id"]),
                "signal_type": str(r["signal_type"]),
            }
        )
    return out


def _assessments_for_cards(card_ids: list[str]) -> dict[str, list[dict[str, str]]]:
    with connection() as conn:
        return _assessments_for_cards_conn(conn, card_ids)


def _fetch_feed_bundle_conn(
    conn: Connection,
    *,
    profile: SessionProfileRow | None,
    horizon_override: str | None,
    categories: list[str] | None,
) -> tuple[list[dict[str, Any]], bool]:
    """Single round-trip feed fetch: pulse rows, instruments, and fog flag (P2.5-S2)."""
    eff_horizon = horizon_override or (profile.horizon if profile else None)
    cutoff = horizon_cutoff(eff_horizon) if eff_horizon else None

    synth = SyntheticFilterMixin.events_not_synthetic("e")
    pulse_where = "WHERE c.lifecycle_state = ANY(%s::public.lifecycle_state[])"
    params: list[Any] = [list(VISIBLE_CARD_STATES)]

    if cutoff is not None:
        pulse_where += " AND c.created_at >= %s"
        params.append(cutoff)

    category_clause = ""
    if categories:
        category_clause = " AND e.category = ANY(%s::text[])"
        params.append(categories)

    params.extend([list(FOG_LIFECYCLE), MAJOR_EVENT_MIN_CONFIDENCE])

    stmt = f"""
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
      {pulse_where}
      {category_clause}
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
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, params)
        fetched = cur.fetchall()

    if not fetched:
        return [], False

    fog = bool(fetched[0]["fog_of_war"])
    rows: list[dict[str, Any]] = []
    for row in fetched:
        instruments = row.get("instruments") or []
        if isinstance(instruments, str):
            instruments = json.loads(instruments)
        rows.append(
            {
                "id": row["id"],
                "headline": row["headline"],
                "insight_layer": row["insight_layer"],
                "lifecycle_state": row["lifecycle_state"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "event_id": row["event_id"],
                "event_title": row["event_title"],
                "category": row["category"],
                "confidence_score": row["confidence_score"],
                "instruments": list(instruments) if instruments else [],
            }
        )
    return rows, fog


def _fetch_pulse_rows_conn(
    conn: Connection,
    *,
    profile: SessionProfileRow | None,
    horizon_override: str | None,
    categories: list[str] | None,
) -> tuple[list[dict[str, Any]], SessionProfileRow | None]:
    eff_horizon = horizon_override or (profile.horizon if profile else None)
    cutoff = horizon_cutoff(eff_horizon) if eff_horizon else None

    synth = SyntheticFilterMixin.events_not_synthetic("e")
    base_sql = f"""
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
    INNER JOIN public.events e ON e.id = c.event_id AND {synth}
    WHERE c.lifecycle_state = ANY(%s::public.lifecycle_state[])
    """
    params: list[Any] = [list(VISIBLE_CARD_STATES)]

    if cutoff is not None:
        base_sql += " AND c.created_at >= %s"
        params.append(cutoff)

    if categories:
        base_sql += " AND e.category = ANY(%s::text[])"
        params.append(categories)

    base_sql += f" ORDER BY c.created_at DESC LIMIT {FEED_ROW_LIMIT}"

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(base_sql, params)
        rows = [dict(r) for r in cur.fetchall()]

    card_ids = [r["id"] for r in rows]
    inst_map = _assessments_for_cards_conn(conn, card_ids)
    for r in rows:
        r["instruments"] = inst_map.get(r["id"], [])

    return rows, profile


def fetch_pulse_rows(
    *,
    profile: SessionProfileRow | None,
    horizon_override: str | None,
    categories: list[str] | None,
) -> tuple[list[dict[str, Any]], SessionProfileRow | None]:
    """
    Return card rows for the Pulse plus the effective profile (requested horizon
    wins over stored profile).
    """
    with connection() as conn:
        return _fetch_pulse_rows_conn(
            conn,
            profile=profile,
            horizon_override=horizon_override,
            categories=categories,
        )


def confidence_tier(score: int | None) -> str:
    s = int(score or 0)
    if s >= 70:
        return "high"
    if s >= 40:
        return "moderate"
    return "uncertain"


def tier_label(tier: str) -> str:
    return {"high": "High", "moderate": "Moderate", "uncertain": "Uncertain"}.get(
        tier, "Uncertain"
    )


def build_card_payload(row: dict[str, Any]) -> dict[str, Any]:
    score = row.get("confidence_score")
    direction = confidence_tier(score)
    mag_score = None if score is None else max(0, min(100, int(score) - 12))
    magnitude = confidence_tier(mag_score)

    excerpt = (row.get("insight_layer") or "").strip().replace("\n", " ")
    if len(excerpt) > 320:
        excerpt = excerpt[:317] + "…"

    instruments = row.get("instruments") or []
    if isinstance(instruments, list):
        instruments_out = instruments[:4]
    else:
        instruments_out = []

    return {
        "id": row["id"],
        "headline": row.get("headline") or "",
        "event_context": row.get("event_title") or "",
        "category": row.get("category") or "macro",
        "lifecycle_state": row.get("lifecycle_state") or "published",
        "direction_confidence": {"tier": direction, "label": tier_label(direction)},
        "magnitude_confidence": {"tier": magnitude, "label": tier_label(magnitude)},
        "instruments": instruments_out,
        "insight_excerpt": excerpt,
        "last_reviewed_at": row.get("updated_at"),
        "created_at": row.get("created_at"),
        "event_id": row.get("event_id"),
    }


def build_feed_response(
    *,
    session_id: UUID | None,
    horizon: str | None,
    category: str | None,
    personalisation_token: str | None = None,
) -> dict[str, Any]:
    cat_list: list[str] | None = None
    if category:
        cat_list = [c.strip() for c in category.split(",") if c.strip()]

    with connection() as conn:
        profile = (
            _fetch_session_profile_conn(conn, session_id)
            if session_id is not None
            else None
        )
        rows, fog = _fetch_feed_bundle_conn(
            conn,
            profile=profile,
            horizon_override=horizon,
            categories=cat_list,
        )

    salt = get_settings().personalisation_token_salt.strip()
    rows = rerank(rows, personalisation_token, salt=salt)
    cards = [build_card_payload(r) for r in rows]

    eff_horizon = horizon or (profile.horizon if profile else None)
    meta_profile = None
    if profile is not None:
        meta_profile = {
            "horizon": profile.horizon,
            "mode": profile.mode,
            "effective_horizon": eff_horizon,
        }

    now = datetime.now(tz=UTC)
    return {
        "cards": cards,
        "fog_of_war": fog,
        "profile": meta_profile,
        "last_updated": now.isoformat(),
        "counts": len(cards),
    }
