"""Rule-based event confidence scorer (P3-S1g / G-01, G-02)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlparse
from uuid import UUID

from psycopg.rows import dict_row

from app.core.confidence_config import (
    CALIBRATION_STATUS,
    DEFAULT_SOURCE_QUALITY,
    FOG_ACTIVE_MAJOR_THRESHOLD,
    FOG_DAMPENER,
    FORCE_REVIEW_SOURCE_THRESHOLD,
    IS_MAJOR_MIN_FACTOR_MATCHES,
    IS_MAJOR_MIN_RAW,
    MAJOR_CATEGORIES,
    SCORER_VERSION,
    SOURCE_COUNT_CAP,
    SOURCE_QUALITY_BY_ADAPTER,
    SOURCE_QUALITY_BY_DOMAIN,
    THRESHOLDS,
    UNIQUE_PUBLISHER_CAP,
    WEIGHTS,
)
from app.db.connection import connection
from app.models.enums import EventCategory
from app.services.event_factor_match import compute_factor_match

_LOG = logging.getLogger(__name__)

ConfidenceTier = Literal["high", "medium", "low"]

FOG_LIFECYCLE_STATES: tuple[str, ...] = ("active", "signal_triggered")


@dataclass(frozen=True)
class ScorerInput:
    """Normalized inputs for one confidence computation."""

    source_count: int
    primary_source: str
    source_quality: float
    factor_match_strength: float
    factor_db_match_count: int
    matched_factor_slugs: tuple[str, ...]
    recency_score: float
    unique_publisher_score: float
    unique_publisher_count: int
    category: str
    first_seen_at: datetime
    sources: tuple[dict[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ConfidenceResult:
    raw: float
    effective: float
    tier: ConfidenceTier
    is_major: bool
    fog_active: bool
    inputs: ScorerInput
    breakdown: dict[str, dict[str, Any]]
    force_editorial_review: bool


def publisher_domain(url: str) -> str:
    netloc = urlparse(url.strip()).netloc.lower()
    if netloc.startswith("www."):
        return netloc[4:]
    return netloc


def source_quality_for(*, event_source: str, canonical_url: str | None) -> float:
    adapter = event_source.strip().lower()
    if adapter in SOURCE_QUALITY_BY_ADAPTER:
        return SOURCE_QUALITY_BY_ADAPTER[adapter]
    if canonical_url:
        domain = publisher_domain(canonical_url)
        for key, weight in SOURCE_QUALITY_BY_DOMAIN.items():
            if domain == key or domain.endswith("." + key):
                return weight
    return DEFAULT_SOURCE_QUALITY


def recency_score(*, first_seen_at: datetime, reference: datetime | None = None) -> float:
    ref = reference or datetime.now(tz=UTC)
    if first_seen_at.tzinfo is None:
        first_seen_at = first_seen_at.replace(tzinfo=UTC)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=UTC)
    age_hours = (ref - first_seen_at).total_seconds() / 3600.0
    if age_hours <= 4:
        return 1.0
    if age_hours <= 12:
        return 0.7
    if age_hours <= 24:
        return 0.4
    return 0.1


def unique_publisher_count(sources: list[dict[str, Any]] | None) -> int:
    domains: set[str] = set()
    for entry in sources or []:
        url = str(entry.get("canonical_url") or entry.get("source_url") or "")
        if not url:
            continue
        domain = publisher_domain(url)
        if domain:
            domains.add(domain)
    return len(domains)


def unique_publisher_score(count: int) -> float:
    return min(max(count, 0) / float(UNIQUE_PUBLISHER_CAP), 1.0)


def source_count_score(count: int) -> float:
    return min(max(count, 0) / float(SOURCE_COUNT_CAP), 1.0)


def tier_from_score(score: float) -> ConfidenceTier:
    if score >= THRESHOLDS["high"]:
        return "high"
    if score >= THRESHOLDS["medium_low"]:
        return "medium"
    return "low"


def compute_is_major(
    *,
    raw: float,
    factor_db_match_count: int,
    category: str | EventCategory,
) -> bool:
    cat = EventCategory(category) if isinstance(category, str) else category
    return (
        raw >= IS_MAJOR_MIN_RAW
        and factor_db_match_count >= IS_MAJOR_MIN_FACTOR_MATCHES
        and cat in MAJOR_CATEGORIES
    )


def _weighted_raw(inp: ScorerInput) -> float:
    components = {
        "source_count": source_count_score(inp.source_count),
        "source_quality": min(max(inp.source_quality, 0.0), 1.0),
        "factor_db_match": min(max(inp.factor_match_strength, 0.0), 1.0),
        "recency": min(max(inp.recency_score, 0.0), 1.0),
        "unique_publisher": min(max(inp.unique_publisher_score, 0.0), 1.0),
    }
    total = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)
    return round(min(max(total, 0.0), 1.0), 3)


def build_breakdown(inp: ScorerInput, *, raw: float) -> dict[str, dict[str, Any]]:
    return {
        "source_count": {
            "value": round(source_count_score(inp.source_count), 3),
            "weight": WEIGHTS["source_count"],
            "detail": f"{inp.source_count} sources post-dedup",
        },
        "source_quality": {
            "value": round(min(max(inp.source_quality, 0.0), 1.0), 3),
            "weight": WEIGHTS["source_quality"],
            "detail": f"primary_source={inp.primary_source}",
        },
        "factor_db_match": {
            "value": round(inp.factor_match_strength, 3),
            "weight": WEIGHTS["factor_db_match"],
            "detail": (
                f"{inp.factor_db_match_count} factors"
                + (
                    f" ({', '.join(inp.matched_factor_slugs)})"
                    if inp.matched_factor_slugs
                    else ""
                )
            ),
        },
        "recency": {
            "value": round(inp.recency_score, 3),
            "weight": WEIGHTS["recency"],
            "detail": f"first_seen={inp.first_seen_at.isoformat()}",
        },
        "unique_publisher": {
            "value": round(inp.unique_publisher_score, 3),
            "weight": WEIGHTS["unique_publisher"],
            "detail": f"{inp.unique_publisher_count} publishers (domain-level)",
        },
        "confidence_raw": {"value": raw, "weight": 1.0, "detail": "weighted sum"},
        "calibration_status": {
            "value": 0.0,
            "weight": 0.0,
            "detail": CALIBRATION_STATUS,
        },
    }


def build_scorer_input(
    *,
    title: str,
    category: str | EventCategory,
    event_source: str,
    canonical_url: str | None,
    source_count: int,
    sources: list[dict[str, Any]] | None,
    first_seen_at: datetime,
    body: str | None = None,
    reference: datetime | None = None,
) -> ScorerInput:
    strength, factor_count, slugs = compute_factor_match(
        title=title,
        body=body,
        category=category,
    )
    pub_count = unique_publisher_count(sources)
    quality = source_quality_for(event_source=event_source, canonical_url=canonical_url)
    return ScorerInput(
        source_count=source_count,
        primary_source=event_source,
        source_quality=quality,
        factor_match_strength=strength,
        factor_db_match_count=factor_count,
        matched_factor_slugs=tuple(slugs),
        recency_score=recency_score(first_seen_at=first_seen_at, reference=reference),
        unique_publisher_score=unique_publisher_score(pub_count),
        unique_publisher_count=pub_count,
        category=category.value if isinstance(category, EventCategory) else category,
        first_seen_at=first_seen_at,
        sources=tuple(sources or []),
    )


def compute_confidence(
    inp: ScorerInput,
    *,
    fog_active: bool,
) -> ConfidenceResult:
    raw = _weighted_raw(inp)
    effective = round(raw * (FOG_DAMPENER if fog_active else 1.0), 3)
    tier = tier_from_score(effective)
    is_major = compute_is_major(
        raw=raw,
        factor_db_match_count=inp.factor_db_match_count,
        category=inp.category,
    )
    return ConfidenceResult(
        raw=raw,
        effective=effective,
        tier=tier,
        is_major=is_major,
        fog_active=fog_active,
        inputs=inp,
        breakdown=build_breakdown(inp, raw=raw),
        force_editorial_review=inp.source_count > FORCE_REVIEW_SOURCE_THRESHOLD,
    )


def fetch_fog_active(*, exclude_event_id: UUID | None = None) -> bool:
    """True when ≥3 active is_major events (FoW dampener applies to new scores)."""
    extra = ""
    params: list[Any] = [list(FOG_LIFECYCLE_STATES), FOG_ACTIVE_MAJOR_THRESHOLD]
    if exclude_event_id is not None:
        extra = " AND id <> %s::uuid"
        params.append(str(exclude_event_id))
    stmt = f"""
    SELECT COUNT(*)::int AS n
    FROM public.events
    WHERE is_major = TRUE
      AND lifecycle_state::text = ANY(%s)
      AND COALESCE(is_major_override, is_major) = TRUE
      {extra}
    """
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(stmt, tuple(params))
            row = cur.fetchone()
    except RuntimeError:
        return False
    if not row:
        return False
    return int(row["n"]) >= FOG_ACTIVE_MAJOR_THRESHOLD


def _inputs_to_audit_json(inp: ScorerInput, result: ConfidenceResult) -> dict[str, Any]:
    return {
        "source_count": inp.source_count,
        "primary_source": inp.primary_source,
        "source_quality": inp.source_quality,
        "factor_match_strength": inp.factor_match_strength,
        "factor_db_match_count": inp.factor_db_match_count,
        "matched_factor_slugs": list(inp.matched_factor_slugs),
        "recency_score": inp.recency_score,
        "unique_publisher_count": inp.unique_publisher_count,
        "unique_publisher_score": inp.unique_publisher_score,
        "category": inp.category,
        "first_seen_at": inp.first_seen_at.isoformat(),
        "fog_active": result.fog_active,
        "tier": result.tier,
        "breakdown": result.breakdown,
    }


def write_confidence_audit(
    cur: Any,
    *,
    event_id: UUID,
    result: ConfidenceResult,
) -> None:
    cur.execute(
        """
        INSERT INTO public.confidence_score_audit (
          event_id, confidence_raw, confidence_effective, inputs_json, scorer_version
        )
        VALUES (%s::uuid, %s, %s, %s::jsonb, %s)
        """,
        (
            str(event_id),
            result.raw,
            result.effective,
            json.dumps(_inputs_to_audit_json(result.inputs, result)),
            SCORER_VERSION,
        ),
    )


def apply_confidence_to_event_row(
    cur: Any,
    *,
    event_id: UUID,
    title: str,
    category: str,
    event_source: str,
    canonical_url: str | None,
    source_count: int,
    sources: list[dict[str, Any]] | None,
    first_seen_at: datetime,
    body: str | None = None,
    reference: datetime | None = None,
    respect_major_override: bool = True,
) -> ConfidenceResult:
    fog_active = fetch_fog_active(exclude_event_id=event_id)
    inp = build_scorer_input(
        title=title,
        category=category,
        event_source=event_source,
        canonical_url=canonical_url,
        source_count=source_count,
        sources=sources,
        first_seen_at=first_seen_at,
        body=body,
        reference=reference,
    )
    result = compute_confidence(inp, fog_active=fog_active)

    if respect_major_override:
        cur.execute(
            """
            UPDATE public.events
            SET confidence_raw = %s,
                confidence_effective = %s,
                factor_db_match_count = %s,
                is_major = CASE
                  WHEN is_major_override IS NOT NULL THEN is_major_override
                  ELSE %s
                END,
                force_editorial_review = %s
            WHERE id = %s::uuid
            """,
            (
                result.raw,
                result.effective,
                inp.factor_db_match_count,
                result.is_major,
                result.force_editorial_review,
                str(event_id),
            ),
        )
    else:
        cur.execute(
            """
            UPDATE public.events
            SET confidence_raw = %s,
                confidence_effective = %s,
                factor_db_match_count = %s,
                is_major = %s,
                force_editorial_review = %s
            WHERE id = %s::uuid
            """,
            (
                result.raw,
                result.effective,
                inp.factor_db_match_count,
                result.is_major,
                result.force_editorial_review,
                str(event_id),
            ),
        )
    write_confidence_audit(cur, event_id=event_id, result=result)
    return result


def apply_confidence_to_event(
    event_id: UUID,
    *,
    reference: datetime | None = None,
) -> ConfidenceResult | None:
    """Load event by id, recompute confidence, persist audit row."""
    stmt = """
    SELECT
      id, title, category::text AS category, event_source, canonical_url,
      source_count, sources, created_at, is_major_override
    FROM public.events
    WHERE id = %s::uuid
    LIMIT 1
    """
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(stmt, (str(event_id),))
            row = cur.fetchone()
            if not row:
                return None
            sources = row["sources"]
            if isinstance(sources, str):
                sources = json.loads(sources)
            result = apply_confidence_to_event_row(
                cur,
                event_id=event_id,
                title=str(row["title"]),
                category=str(row["category"]),
                event_source=str(row["event_source"] or ""),
                canonical_url=row.get("canonical_url"),
                source_count=int(row["source_count"] or 1),
                sources=list(sources or []),
                first_seen_at=row["created_at"],
                reference=reference,
            )
            conn.commit()
    except RuntimeError as exc:
        _LOG.warning(
            "confidence_scorer.apply_failed",
            extra={"event_id": str(event_id), "error": repr(exc)},
        )
        return None
    return result


def build_confidence_breakdown_payload(
    event_id: UUID,
    *,
    reference: datetime | None = None,
) -> dict[str, Any] | None:
    """API payload for GET /api/events/{id}/confidence-breakdown."""
    stmt = """
    SELECT
      e.id,
      e.title,
      e.category::text AS category,
      e.event_source,
      e.canonical_url,
      e.source_count,
      e.sources,
      e.created_at,
      e.confidence_raw,
      e.confidence_effective,
      e.force_editorial_review,
      e.is_major_override
    FROM public.events e
    WHERE e.id = %s::uuid
    LIMIT 1
    """
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(stmt, (str(event_id),))
            row = cur.fetchone()
            if not row:
                return None
            sources = row["sources"]
            if isinstance(sources, str):
                sources = json.loads(sources)
            fog_active = fetch_fog_active(exclude_event_id=event_id)
            inp = build_scorer_input(
                title=str(row["title"]),
                category=str(row["category"]),
                event_source=str(row["event_source"] or ""),
                canonical_url=row.get("canonical_url"),
                source_count=int(row["source_count"] or 1),
                sources=list(sources or []),
                first_seen_at=row["created_at"],
                reference=reference,
            )
            result = compute_confidence(inp, fog_active=fog_active)
    except RuntimeError:
        return None

    source_list = []
    for entry in inp.sources:
        url = str(entry.get("canonical_url") or entry.get("source_url") or "")
        source_list.append(
            {
                "name": entry.get("event_source") or publisher_domain(url) or "unknown",
                "url": url,
                "retrieved_at": entry.get("retrieved_at"),
            }
        )

    return {
        "event_id": str(event_id),
        "confidence_raw": result.raw,
        "confidence_effective": result.effective,
        "tier": result.tier,
        "fog_active": result.fog_active,
        "fog_dampener": FOG_DAMPENER if result.fog_active else None,
        "calibration_status": CALIBRATION_STATUS,
        "scorer_version": SCORER_VERSION,
        "is_major": result.is_major,
        "force_editorial_review": result.force_editorial_review,
        "inputs": {
            k: v
            for k, v in result.breakdown.items()
            if k not in ("confidence_raw", "calibration_status")
        },
        "sources": source_list,
    }
