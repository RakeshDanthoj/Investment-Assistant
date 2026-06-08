"""The Map — sector index and detail payloads (P2-S11)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from psycopg.rows import dict_row

from app.db.connection import connection
from app.services.factor_db import freshness_for_retrieved_at
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
class SectorSummary:
    slug: str
    name: str
    instrument_count: int
    cover_accent: str


def list_sectors() -> list[SectorSummary]:
    stmt = """
    SELECT slug, name, instrument_count
    FROM public.map_sector_list_v
    ORDER BY name
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


def _normalize_modules(raw_modules: Any) -> list[dict[str, Any]]:
    modules = raw_modules or []
    if not isinstance(modules, list):
        return []
    return [
        {
            "id": str(m["id"]),
            "sector_slug": m.get("sector_slug"),
            "title": str(m["title"]),
            "body": str(m["body"]),
            "linked_gap_types": list(m.get("linked_gap_types") or []),
            "sort_order": int(m["sort_order"]),
        }
        for m in modules
    ]


def fetch_sector_summary(*, sector_slug: str) -> dict[str, Any]:
    slug = sector_slug.strip().lower()
    if not slug:
        raise ValueError("sector_slug is required")

    stmt = """
    SELECT slug, name, instrument_count, modules
    FROM public.map_sector_summary_v
    WHERE slug = %s
    LIMIT 1
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (slug,))
        row = cur.fetchone()

    if not row:
        raise LookupError(f"sector not found: {slug}")

    return {
        "sector": {"slug": str(row["slug"]), "name": str(row["name"])},
        "instrument_count": int(row["instrument_count"]),
        "modules": _normalize_modules(row.get("modules")),
        "cover_accent": SECTOR_COVER_ACCENTS.get(slug, "slate"),
    }


def _reshape_sensitivity_rows(
    rows: Any,
    *,
    reference: datetime | None = None,
) -> dict[str, dict[str, dict[str, Any]]]:
    ref = reference if reference is not None else datetime.now(UTC)
    if not isinstance(rows, list):
        return {}

    sensitivities: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        tick = str(row["ticker"])
        factor_slug = str(row["factor_slug"])
        retrieved_at = row["retrieved_at"]
        if isinstance(retrieved_at, str):
            retrieved_at = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
        sensitivities.setdefault(tick, {})[factor_slug] = {
            "sensitivity": int(row["sensitivity"]),
            "mmj_tag": str(row["mmj_tag"]),
            "source_url": str(row["source_url"]),
            "retrieved_at": retrieved_at.isoformat(),
            "freshness": freshness_for_retrieved_at(retrieved_at, reference=ref),
        }
    return sensitivities


def fetch_sector_matrix(*, sector_slug: str) -> dict[str, Any]:
    slug = sector_slug.strip().lower()
    if not slug:
        raise ValueError("sector_slug is required")

    stmt = """
    SELECT sector, factors, instruments, sensitivity_rows
    FROM public.map_sector_matrix_v
    WHERE sector_slug = %s
    LIMIT 1
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (slug,))
        row = cur.fetchone()

    if not row:
        raise LookupError(f"sector not found: {slug}")

    instruments_raw = row.get("instruments") or []
    if not isinstance(instruments_raw, list):
        instruments_raw = []

    all_instruments = [
        {
            "id": str(inst["id"]),
            "ticker": str(inst["ticker"]),
            "display_name": str(inst["display_name"]),
        }
        for inst in instruments_raw
    ]
    preview_instruments = all_instruments[:MATRIX_PREVIEW_INSTRUMENT_LIMIT]
    tickers = {inst["ticker"] for inst in preview_instruments}

    all_sensitivities = _reshape_sensitivity_rows(row.get("sensitivity_rows"))
    sensitivities = {t: all_sensitivities.get(t, {}) for t in tickers if t in all_sensitivities}

    factors_raw = row.get("factors") or []
    factors = factors_raw if isinstance(factors_raw, list) else []

    sector_raw = row.get("sector") or {}
    return {
        "sector": {
            "slug": str(sector_raw.get("slug", slug)),
            "name": str(sector_raw.get("name", slug)),
        },
        "factors": factors,
        "instruments": preview_instruments,
        "instrument_count": len(all_instruments),
        "sensitivities": sensitivities,
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
