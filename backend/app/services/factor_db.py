"""Factor Exposure DB lookups (PRD §7.1) and Evidence freshness tiers (PRD §5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection

FreshnessTone = Literal["green", "amber", "red"]


def freshness_for_retrieved_at(
    retrieved_at: datetime, *, reference: datetime | None = None
) -> FreshnessTone:
    """
    Evidence freshness dot (PRD §5 / §8 Evidence): green ≤6mo, amber 6–18mo, red >18mo.
    Thresholds approximate months as fixed day counts from the PRD wording.
    """
    ref = reference if reference is not None else datetime.now(UTC)
    if retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.replace(tzinfo=UTC)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=UTC)

    delta = ref - retrieved_at
    days = delta.days

    green_max = round(365.25 * 0.5)  # ≈ six months
    amber_max = round(365.25 * 1.5)  # ≈ eighteen months

    if days <= green_max:
        return "green"
    if days <= amber_max:
        return "amber"
    return "red"


@dataclass(frozen=True)
class SensitivityLookup:
    ticker: str
    factor_slug: str
    sensitivity: int
    mmj_tag: str
    source_url: str
    retrieved_at: datetime
    freshness: FreshnessTone
    instrument_display_name: str


def lookup_sensitivity(
    *,
    instrument_ticker: str,
    factor_slug: str,
    reference_now: datetime | None = None,
) -> SensitivityLookup | None:
    q = instrument_ticker.strip().upper()
    f = factor_slug.strip().lower()
    if not q or not f:
        return None

    stmt = """
    SELECT
      i.ticker,
      fc.slug AS factor_slug,
      s.sensitivity,
      s.mmj_tag::text AS mmj_tag,
      s.source_url,
      s.retrieved_at,
      i.display_name AS instrument_display_name
    FROM public.instrument_factor_sensitivity AS s
    JOIN public.instruments AS i ON i.id = s.instrument_id
    JOIN public.factors AS fc ON fc.id = s.factor_id
    WHERE upper(i.exchange) = 'NSE' AND upper(i.ticker) = upper(%s) AND fc.slug = %s
    LIMIT 1
    """

    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (q, f))
        row = cur.fetchone()
        if not row:
            return None

    rt = row["retrieved_at"]
    freshness = freshness_for_retrieved_at(rt, reference=reference_now)
    return SensitivityLookup(
        ticker=str(row["ticker"]),
        factor_slug=str(row["factor_slug"]),
        sensitivity=int(row["sensitivity"]),
        mmj_tag=str(row["mmj_tag"]),
        source_url=str(row["source_url"]),
        retrieved_at=rt,
        freshness=freshness,
        instrument_display_name=str(row["instrument_display_name"]),
    )


def _json_safe_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize DB row values for JSON/API consumers (e.g. UUID → str)."""
    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, UUID):
            out[key] = str(value)
        else:
            out[key] = value
    return out


def fetch_matrix_rows(*, sector_slug: str) -> dict[str, Any]:
    """
    Matrix payload for admin JSON: sector, factors, instruments, sensitivities map.
    """
    sector = sector_slug.strip().lower()
    if not sector:
        raise ValueError("sector_slug is required")

    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT slug, name
            FROM public.sectors
            WHERE slug = %s
            LIMIT 1
            """,
            (sector,),
        )
        sector_row = cur.fetchone()
        if not sector_row:
            raise LookupError(f"sector not found: {sector}")

        cur.execute(
            """
            SELECT slug, display_name, sort_order, description
            FROM public.factors
            ORDER BY sort_order
            """
        )
        factor_rows = cur.fetchall()

        cur.execute(
            """
            SELECT i.id, i.ticker, i.display_name, i.isin, i.exchange
            FROM public.instruments AS i
            JOIN public.sectors AS s ON s.id = i.sector_id
            WHERE s.slug = %s
            ORDER BY upper(i.ticker)
            """,
            (sector,),
        )
        instruments = cur.fetchall()

        cur.execute(
            """
            SELECT i.ticker, f.slug AS factor_slug, s.sensitivity, s.mmj_tag::text AS mmj_tag,
                   s.source_url, s.retrieved_at
            FROM public.instrument_factor_sensitivity AS s
            JOIN public.instruments AS i ON i.id = s.instrument_id
            JOIN public.factors AS f ON f.id = s.factor_id
            JOIN public.sectors AS sec ON sec.id = i.sector_id
            WHERE sec.slug = %s
            """,
            (sector,),
        )
        sense_rows = cur.fetchall()

    ref = datetime.now(UTC)

    sensitivities: dict[str, dict[str, Any]] = {}
    for r in sense_rows:
        tick = str(r["ticker"])
        fslug = str(r["factor_slug"])
        retrieved_at = r["retrieved_at"]
        sensitivities.setdefault(tick, {})[fslug] = {
            "sensitivity": int(r["sensitivity"]),
            "mmj_tag": str(r["mmj_tag"]),
            "source_url": str(r["source_url"]),
            "retrieved_at": retrieved_at.isoformat(),
            "freshness": freshness_for_retrieved_at(retrieved_at, reference=ref),
        }

    return {
        "sector": {"slug": str(sector_row["slug"]), "name": str(sector_row["name"])},
        "factors": [_json_safe_row(dict(r)) for r in factor_rows],
        "instruments": [_json_safe_row(dict(r)) for r in instruments],
        "sensitivities": sensitivities,
    }
