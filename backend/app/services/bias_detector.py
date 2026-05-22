"""Bias audit detectors + persistence (PRD §6.5, P1-S13)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.services.card_repository import fetch_card_detail_for_review
from app.services.feed import confidence_tier

BIAS_RECENCY = "recency"
BIAS_SECTOR_CONCENTRATION = "sector_concentration"
BIAS_NARRATIVE = "narrative"
BIAS_SURVIVORSHIP = "survivorship"
BIAS_ANCHORING = "anchoring"

CARD_TRACKED_TYPES: tuple[str, ...] = (
    BIAS_RECENCY,
    BIAS_SECTOR_CONCENTRATION,
    BIAS_NARRATIVE,
    BIAS_SURVIVORSHIP,
    BIAS_ANCHORING,
)

_PUBLISHED_LIFECYCLES: tuple[str, ...] = (
    "published",
    "active",
    "signal_triggered",
    "thesis_confirmed",
    "thesis_weakened",
    "resolved",
)

_BIAS_LABELS: dict[str, str] = {
    BIAS_RECENCY: "Recency bias",
    BIAS_SECTOR_CONCENTRATION: "Sector concentration bias",
    BIAS_NARRATIVE: "Narrative bias",
    BIAS_SURVIVORSHIP: "Survivorship bias",
    BIAS_ANCHORING: "Anchoring bias",
}

_HISTORICAL_RE = re.compile(
    r"\b(historical|backtest|since\s+20\d{2}|over the (?:past|last)\s+\d+\s+years?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BiasFinding:
    bias_type: str
    severity: str
    description: str


def _normalize_evidence_layer(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    return {}


def detect_recency(
    evidence_layer: dict[str, Any],
    *,
    ref: datetime | None = None,
) -> BiasFinding | None:
    """Flag when >60% of Evidence sources are from the last 30 days."""
    from app.services.card_detail import build_evidence_rows

    reference = ref or datetime.now(tz=UTC)
    rows = build_evidence_rows(evidence_layer, ref=reference)
    dated = [
        r
        for r in rows
        if r.get("retrieved_at")
    ]
    if not dated:
        return BiasFinding(
            BIAS_RECENCY,
            "monitored",
            "Watching whether near-term headlines overweight versus slower fundamentals.",
        )

    cutoff = reference - timedelta(days=30)
    recent = 0
    for row in dated:
        raw = row.get("retrieved_at")
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
        except ValueError:
            continue
        if dt >= cutoff:
            recent += 1

    share = recent / len(dated)
    if share > 0.6:
        pct = int(round(share * 100))
        return BiasFinding(
            BIAS_RECENCY,
            "flagged",
            (
                f"{pct}% of Evidence sources were retrieved in the last 30 days — "
                "recent headlines may be overweighted versus slower-moving fundamentals."
            ),
        )
    return BiasFinding(
        BIAS_RECENCY,
        "monitored",
        "Evidence sources are spread across time; recency concentration is within normal bounds.",
    )


def detect_sector_concentration(
    card_id: UUID,
    event_category: str,
) -> BiasFinding | None:
    """Flag when the 3 most recently published cards share the same event category."""
    stmt = """
    SELECT e.category::text AS category
    FROM public.cards c
    INNER JOIN public.events e ON e.id = c.event_id
    WHERE c.lifecycle_state::text = ANY(%s)
    ORDER BY c.created_at DESC
    LIMIT 3
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (list(_PUBLISHED_LIFECYCLES),))
        rows = cur.fetchall()

    if len(rows) < 3:
        return BiasFinding(
            BIAS_SECTOR_CONCENTRATION,
            "monitored",
            "Watching whether consecutive cards cluster on the same event category.",
        )

    categories = [str(r["category"]) for r in rows]
    if len(set(categories)) == 1 and categories[0] == event_category.strip():
        label = categories[0].replace("_", " ")
        return BiasFinding(
            BIAS_SECTOR_CONCENTRATION,
            "flagged",
            (
                f"The last three published cards all cover the {label} category — "
                "editorial attention may be clustering away from other themes."
            ),
        )
    return BiasFinding(
        BIAS_SECTOR_CONCENTRATION,
        "monitored",
        "Recent published cards span more than one event category.",
    )


def detect_narrative(
    event_confidence_score: int | None,
    evidence_layer: dict[str, Any],
) -> BiasFinding:
    """Flag when direction confidence is high but Evidence has fewer than 3 sources."""
    from app.services.card_detail import build_evidence_rows

    rows = build_evidence_rows(evidence_layer)
    source_count = len(rows)
    tier = confidence_tier(event_confidence_score)
    if tier == "high" and source_count < 3:
        return BiasFinding(
            BIAS_NARRATIVE,
            "flagged",
            (
                f"Direction confidence is {tier} while only {source_count} "
                "Evidence source(s) are cited — the storyline may run ahead of the proof trail."
            ),
        )
    if tier == "high":
        return BiasFinding(
            BIAS_NARRATIVE,
            "monitored",
            f"High direction confidence is backed by {source_count} Evidence source(s).",
        )
    return BiasFinding(
        BIAS_NARRATIVE,
        "monitored",
        "Watching whether a compelling storyline outpaces cited Evidence sources.",
    )


def detect_survivorship(
    insight_layer: str,
    context_layer: str,
    evidence_layer: dict[str, Any],
) -> BiasFinding:
    """Lightweight V1: flag historical framing without an explicit delisting caveat."""
    blob = "\n".join(
        [
            insight_layer,
            context_layer,
            str(evidence_layer.get("markdown") or ""),
        ]
    )
    if _HISTORICAL_RE.search(blob):
        return BiasFinding(
            BIAS_SURVIVORSHIP,
            "flagged",
            (
                "This card references historical performance — analysis may reflect "
                "companies that still exist today and understate failures that delisted."
            ),
        )
    return BiasFinding(
        BIAS_SURVIVORSHIP,
        "monitored",
        "No historical backtest framing detected on this card.",
    )


def detect_anchoring() -> BiasFinding:
    """V1: anchoring is monitored; dissent uses a separate LLM prompt (PRD §6.4)."""
    return BiasFinding(
        BIAS_ANCHORING,
        "monitored",
        (
            "Dissent is generated via a separate LLM call with its own prompt to reduce "
            "anchoring on the primary Insight narrative."
        ),
    )


def run_detectors_for_card(detail: dict[str, Any]) -> list[BiasFinding]:
    card_id = UUID(str(detail["card_id"]))
    evidence_layer = _normalize_evidence_layer(detail.get("evidence_layer"))
    score = detail.get("event_confidence_score")
    score_i = int(score) if score is not None else None

    findings: list[BiasFinding] = []
    recency = detect_recency(evidence_layer)
    if recency:
        findings.append(recency)
    sector = detect_sector_concentration(card_id, str(detail.get("event_category") or ""))
    if sector:
        findings.append(sector)
    findings.append(detect_narrative(score_i, evidence_layer))
    findings.append(
        detect_survivorship(
            str(detail.get("insight_layer") or ""),
            str(detail.get("context_layer") or ""),
            evidence_layer,
        )
    )
    findings.append(detect_anchoring())
    return findings


def persist_bias_flags(card_id: UUID, findings: Sequence[BiasFinding]) -> None:
    with connection() as conn, conn.cursor() as cur:
        with conn.transaction():
            cur.execute(
                "DELETE FROM public.card_bias_flags WHERE card_id = %s",
                (str(card_id),),
            )
            for f in findings:
                cur.execute(
                    """
                    INSERT INTO public.card_bias_flags (
                      card_id, bias_type, severity, description
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (str(card_id), f.bias_type, f.severity, f.description),
                )


def fetch_bias_flag_rows(card_id: UUID) -> list[dict[str, Any]]:
    stmt = """
    SELECT bias_type, severity, description, detected_at
    FROM public.card_bias_flags
    WHERE card_id = %s
    ORDER BY bias_type
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(card_id),))
        return [dict(r) for r in cur.fetchall()]


def build_bias_audit(
    findings: Sequence[BiasFinding] | Sequence[dict[str, Any]] | None = None,
    *,
    card_id: UUID | None = None,
) -> dict[str, Any]:
    """Shape bias flags for Thread `bias_audit` JSON."""
    rows: list[dict[str, Any]]
    if findings is not None:
        if findings and isinstance(findings[0], BiasFinding):
            rows = [
                {
                    "bias_type": f.bias_type,
                    "severity": f.severity,
                    "description": f.description,
                }
                for f in findings
            ]
        else:
            rows = list(findings)
    elif card_id is not None:
        rows = fetch_bias_flag_rows(card_id)
    else:
        rows = []

    flags: list[dict[str, Any]] = []
    monitored: list[dict[str, Any]] = []
    for row in rows:
        bias_type = str(row.get("bias_type") or "")
        entry = {
            "id": bias_type,
            "label": _BIAS_LABELS.get(bias_type, bias_type.replace("_", " ").title()),
            "status": str(row.get("severity") or "monitored"),
            "detail": str(row.get("description") or ""),
        }
        if entry["status"] == "flagged":
            flags.append(entry)
        else:
            monitored.append(entry)

    return {"flags": flags, "monitored": monitored}


def detect_all(card_id: UUID) -> list[BiasFinding]:
    """Run all per-card detectors, persist to `card_bias_flags`, return findings."""
    detail = fetch_card_detail_for_review(card_id)
    if detail is None:
        raise LookupError(f"card not found: {card_id}")
    findings = run_detectors_for_card(detail)
    persist_bias_flags(card_id, findings)
    return findings


__all__ = [
    "BiasFinding",
    "build_bias_audit",
    "detect_all",
    "detect_anchoring",
    "detect_narrative",
    "detect_recency",
    "detect_sector_concentration",
    "detect_survivorship",
    "fetch_bias_flag_rows",
    "persist_bias_flags",
    "run_detectors_for_card",
]
