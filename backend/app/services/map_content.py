"""The Map — sector index and detail payloads (P2-S11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.services import factor_db as factor_db_svc
from app.services.reasoning_gap_map import resolve_modules_for_gap_types

SECTOR_COVER_ACCENTS: dict[str, str] = {
    "banking": "sky",
    "it": "violet",
    "energy": "amber",
    "fmcg": "emerald",
    "auto": "rose",
    "pharma": "teal",
    "metals": "slate",
    "telecom": "indigo",
    "infra": "orange",
}

MATRIX_PREVIEW_INSTRUMENT_LIMIT = 12


@dataclass(frozen=True)
class MapModuleRow:
    id: UUID
    sector_slug: str | None
    title: str
    body: str
    linked_gap_types: list[str]
    sort_order: int


@dataclass(frozen=True)
class SectorSummary:
    slug: str
    name: str
    instrument_count: int
    cover_accent: str


def list_sectors() -> list[SectorSummary]:
    stmt = """
    SELECT s.slug, s.name, count(i.id)::int AS instrument_count
    FROM public.sectors AS s
    LEFT JOIN public.instruments AS i ON i.sector_id = s.id
    GROUP BY s.slug, s.name
    ORDER BY s.name
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt)
        rows = cur.fetchall()

    return [
        SectorSummary(
            slug=str(r["slug"]),
            name=str(r["name"]),
            instrument_count=int(r["instrument_count"]),
            cover_accent=SECTOR_COVER_ACCENTS.get(str(r["slug"]), "slate"),
        )
        for r in rows
    ]


def _fetch_modules(*, sector_slug: str | None = None) -> list[MapModuleRow]:
    if sector_slug is not None:
        stmt = """
        SELECT id, sector_slug, title, body, linked_gap_types, sort_order
        FROM public.map_modules
        WHERE sector_slug = %s
        ORDER BY sort_order, title
        """
        params: tuple[str, ...] = (sector_slug,)
    else:
        stmt = """
        SELECT id, sector_slug, title, body, linked_gap_types, sort_order
        FROM public.map_modules
        ORDER BY sort_order, title
        """
        params = ()

    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, params)
        rows = cur.fetchall()

    return [
        MapModuleRow(
            id=r["id"],
            sector_slug=r.get("sector_slug"),
            title=str(r["title"]),
            body=str(r["body"]),
            linked_gap_types=list(r.get("linked_gap_types") or []),
            sort_order=int(r["sort_order"]),
        )
        for r in rows
    ]


def fetch_sector_detail(*, sector_slug: str) -> dict[str, Any]:
    slug = sector_slug.strip().lower()
    if not slug:
        raise ValueError("sector_slug is required")

    matrix = factor_db_svc.fetch_matrix_rows(sector_slug=slug)
    instruments = matrix["instruments"][:MATRIX_PREVIEW_INSTRUMENT_LIMIT]
    tickers = {str(i["ticker"]) for i in instruments}
    sensitivities = {
        t: matrix["sensitivities"].get(t, {}) for t in tickers if t in matrix["sensitivities"]
    }

    modules = _fetch_modules(sector_slug=slug)
    return {
        "sector": matrix["sector"],
        "factors": matrix["factors"],
        "instruments": instruments,
        "instrument_count": len(matrix["instruments"]),
        "sensitivities": sensitivities,
        "modules": [
            {
                "id": str(m.id),
                "sector_slug": m.sector_slug,
                "title": m.title,
                "body": m.body,
                "linked_gap_types": m.linked_gap_types,
                "sort_order": m.sort_order,
            }
            for m in modules
        ],
        "cover_accent": SECTOR_COVER_ACCENTS.get(slug, "slate"),
    }


def fetch_module_by_id(module_id: str) -> dict[str, Any] | None:
    stmt = """
    SELECT id, sector_slug, title, body, linked_gap_types, sort_order
    FROM public.map_modules
    WHERE id = %s
    LIMIT 1
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (module_id,))
        row = cur.fetchone()
    if not row:
        return None
    sector_slug = row.get("sector_slug")
    return {
        "id": str(row["id"]),
        "sector_slug": sector_slug,
        "title": str(row["title"]),
        "body": str(row["body"]),
        "linked_gap_types": list(row.get("linked_gap_types") or []),
        "sort_order": int(row["sort_order"]),
        "href": (
            f"/map/{sector_slug}" if sector_slug else f"/map?module={row['id']}"
        ),
    }


def modules_for_gap_types(gap_types: list[str]) -> list[dict[str, Any]]:
    links = resolve_modules_for_gap_types(gap_types)
    return [
        {
            "gap_type": gap,
            "gap_label": gap,
            "module": {
                "id": str(link.id),
                "title": link.title,
                "sector_slug": link.sector_slug,
                "href": (
                    f"/map/{link.sector_slug}"
                    if link.sector_slug
                    else f"/map?module={link.id}"
                ),
            },
        }
        for gap, link in links.items()
    ]
