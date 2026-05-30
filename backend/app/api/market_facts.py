"""Public market fact chips with freshness metadata (P3-S1f)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.market_facts_adapters import (
    FreshnessStatus,
    evaluate_critical_facts_gate,
)

router = APIRouter(tags=["market-facts"])


class MarketFactChip(BaseModel):
    fact_id: str
    label: str
    display_value: str
    observed_at: datetime
    source: str
    freshness_status: FreshnessStatus


class MarketFactsResponse(BaseModel):
    facts: list[MarketFactChip]
    degraded: bool = Field(
        description="True when any critical fact is stale or unavailable.",
    )
    unavailable_critical: list[str] = Field(
        default_factory=list,
        description="Critical fact IDs that are unavailable (card pipeline held).",
    )
    has_stale_critical: bool = False
    reference_time: datetime


@router.get("/market-facts", response_model=MarketFactsResponse)
def get_market_facts() -> MarketFactsResponse:
    ref = datetime.now(tz=UTC)
    gate = evaluate_critical_facts_gate(reference_time=ref)
    return MarketFactsResponse(
        facts=[
            MarketFactChip(
                fact_id=f.fact_id,
                label=f.label,
                display_value=f.display_value,
                observed_at=f.observed_at,
                source=f.source,
                freshness_status=f.freshness_status,
            )
            for f in gate.facts
        ],
        degraded=bool(gate.unavailable_critical or gate.has_stale_critical),
        unavailable_critical=list(gate.unavailable_critical),
        has_stale_critical=gate.has_stale_critical,
        reference_time=ref,
    )
