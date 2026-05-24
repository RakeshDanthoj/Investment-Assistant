"""Reasoning-gap taxonomy → Map module links (P2-S4 / P2-S11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection

GapTypeSlug = Literal[
    "direction_magnitude_mismatch",
    "narrative_anchoring",
    "sector_concentration",
]

GAP_TYPE_LABELS: dict[GapTypeSlug, str] = {
    "direction_magnitude_mismatch": "Direction-correct, magnitude-wrong",
    "narrative_anchoring": "Anchored on narrative",
    "sector_concentration": "Sector concentration in your predictions",
}

ALL_GAP_TYPES: tuple[GapTypeSlug, ...] = tuple(GAP_TYPE_LABELS.keys())


@dataclass(frozen=True)
class MapModuleLink:
    id: UUID
    title: str
    sector_slug: str | None


def resolve_modules_for_gap_types(
    gap_types: list[str],
) -> dict[str, MapModuleLink]:
    """Return at most one Map module per requested gap type slug."""
    requested = [g.strip() for g in gap_types if g and g.strip()]
    if not requested:
        return {}

    stmt = """
    SELECT id, title, sector_slug, linked_gap_types
    FROM public.map_modules
    WHERE linked_gap_types && %s::text[]
    ORDER BY sort_order, title
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (requested,))
        rows = cur.fetchall()

    out: dict[str, MapModuleLink] = {}
    for row in rows:
        linked = row.get("linked_gap_types") or []
        for gap in linked:
            if gap not in requested or gap in out:
                continue
            out[gap] = MapModuleLink(
                id=row["id"],
                title=str(row["title"]),
                sector_slug=row.get("sector_slug"),
            )
    return out


def resolve_module_for_gap_type(gap_type: str) -> MapModuleLink | None:
    return resolve_modules_for_gap_types([gap_type]).get(gap_type.strip())
