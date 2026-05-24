"""The Map — sector learning surface (P2-S11)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import User, get_current_user
from app.services import map_content as map_svc
from app.services.reasoning_gap_map import ALL_GAP_TYPES, GAP_TYPE_LABELS

router = APIRouter(prefix="/map", tags=["map"])


class SectorSummaryItem(BaseModel):
    slug: str
    name: str
    instrument_count: int
    cover_accent: str


class SectorListResponse(BaseModel):
    sectors: list[SectorSummaryItem]


class MapModuleItem(BaseModel):
    id: UUID
    sector_slug: str | None = None
    title: str
    body: str
    linked_gap_types: list[str] = Field(default_factory=list)
    sort_order: int


class SectorDetailResponse(BaseModel):
    sector: dict[str, Any]
    factors: list[dict[str, Any]]
    instruments: list[dict[str, Any]]
    instrument_count: int
    sensitivities: dict[str, dict[str, dict[str, Any]]]
    modules: list[MapModuleItem]
    cover_accent: str


class GapModuleLinkItem(BaseModel):
    gap_type: str
    gap_label: str
    module: dict[str, Any]


class GapModulesResponse(BaseModel):
    items: list[GapModuleLinkItem]


@router.get("/sectors", response_model=SectorListResponse)
def list_map_sectors(_: User = Depends(get_current_user)) -> SectorListResponse:
    try:
        rows = map_svc.list_sectors()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from None

    return SectorListResponse(
        sectors=[
            SectorSummaryItem(
                slug=r.slug,
                name=r.name,
                instrument_count=r.instrument_count,
                cover_accent=r.cover_accent,
            )
            for r in rows
        ]
    )


@router.get("/sectors/{slug}", response_model=SectorDetailResponse)
def get_map_sector(slug: str, _: User = Depends(get_current_user)) -> SectorDetailResponse:
    try:
        data = map_svc.fetch_sector_detail(sector_slug=slug)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from None
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SectorDetailResponse(**data)


@router.get("/modules/by-gap-type", response_model=GapModulesResponse)
def get_modules_by_gap_type(
    gap_type: list[str] = Query(
        default=[],
        description="Reasoning gap type slugs (P2-S4). Defaults to full taxonomy when empty.",
    ),
    _: User = Depends(get_current_user),
) -> GapModulesResponse:
    types = gap_type if gap_type else list(ALL_GAP_TYPES)
    try:
        items = map_svc.modules_for_gap_types(types)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from None

    return GapModulesResponse(
        items=[
            GapModuleLinkItem(
                gap_type=item["gap_type"],
                gap_label=GAP_TYPE_LABELS.get(item["gap_type"], item["gap_type"]),  # type: ignore[arg-type]
                module=item["module"],
            )
            for item in items
        ]
    )


@router.get("/modules/{module_id}", response_model=MapModuleItem)
def get_map_module(module_id: UUID, _: User = Depends(get_current_user)) -> MapModuleItem:
    try:
        row = map_svc.fetch_module_by_id(str(module_id))
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from None
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return MapModuleItem(
        id=UUID(row["id"]),
        sector_slug=row.get("sector_slug"),
        title=row["title"],
        body=row["body"],
        linked_gap_types=row.get("linked_gap_types") or [],
        sort_order=row["sort_order"],
    )
