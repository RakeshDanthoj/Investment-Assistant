"""Pattern-mining reasoning gaps over graded predictions (P2-S4)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.services.reasoning_gap_map import (
    GAP_TYPE_LABELS,
    GapTypeSlug,
    resolve_module_for_gap_type,
)

MIN_GRADED_RESOLVED = 3
MIN_PATTERN_RATE = 0.25
SECTOR_CONCENTRATION_THRESHOLD = 0.6

_GRADED_ACCURACY = frozenset({"correct", "partial", "incorrect"})


@dataclass(frozen=True)
class GradedPredictionRow:
    mechanism_accuracy: str | None
    business_accuracy: str | None
    market_accuracy: str | None
    sector_slug: str | None


@dataclass(frozen=True)
class ReasoningGap:
    gap_type: GapTypeSlug
    gap_name: str
    pattern_explanation: str
    linked_map_module_id: UUID
    linked_map_module_name: str


@dataclass(frozen=True)
class GapTypeScore:
    gap_type: GapTypeSlug
    score: float
    pattern_explanation: str


def infer_gap_type_for_prediction(
    mechanism_accuracy: str | None,
    business_accuracy: str | None,
    market_accuracy: str | None,
) -> GapTypeSlug | None:
    """Per-prediction gap type for expanded card Map links (not sector concentration)."""
    mech = mechanism_accuracy if mechanism_accuracy in _GRADED_ACCURACY else None
    biz = business_accuracy if business_accuracy in _GRADED_ACCURACY else None
    market = market_accuracy if market_accuracy in _GRADED_ACCURACY else None
    if mech == "correct" and market in ("incorrect", "partial"):
        return "direction_magnitude_mismatch"
    if biz == "correct" and mech in ("incorrect", "partial"):
        return "narrative_anchoring"
    return None


def _graded_count(rows: list[GradedPredictionRow]) -> int:
    return len(rows)


def _score_direction_magnitude(rows: list[GradedPredictionRow]) -> GapTypeScore | None:
    eligible = [
        r
        for r in rows
        if r.mechanism_accuracy in _GRADED_ACCURACY and r.market_accuracy in _GRADED_ACCURACY
    ]
    if not eligible:
        return None
    hits = sum(
        1
        for r in eligible
        if r.mechanism_accuracy == "correct"
        and r.market_accuracy in ("incorrect", "partial")
    )
    rate = hits / len(eligible)
    if rate < MIN_PATTERN_RATE:
        return None
    pct = round(rate * 100)
    return GapTypeScore(
        gap_type="direction_magnitude_mismatch",
        score=rate,
        pattern_explanation=(
            f"In {hits} of your last {len(eligible)} resolved predictions ({pct}%), "
            "mechanism was correct but market reaction was partial or incorrect — "
            "you are reading the transmission chain but mis-sizing how prices react."
        ),
    )


def _score_narrative_anchoring(rows: list[GradedPredictionRow]) -> GapTypeScore | None:
    eligible = [
        r
        for r in rows
        if r.mechanism_accuracy in _GRADED_ACCURACY and r.business_accuracy in _GRADED_ACCURACY
    ]
    if not eligible:
        return None
    hits = sum(
        1
        for r in eligible
        if r.business_accuracy == "correct" and r.mechanism_accuracy in ("incorrect", "partial")
    )
    rate = hits / len(eligible)
    if rate < MIN_PATTERN_RATE:
        return None
    pct = round(rate * 100)
    return GapTypeScore(
        gap_type="narrative_anchoring",
        score=rate,
        pattern_explanation=(
            f"In {hits} of your last {len(eligible)} resolved predictions ({pct}%), "
            "the business-impact read landed while mechanism was partial or incorrect — "
            "a sign you may be anchoring on narrative rather than tracing the causal chain."
        ),
    )


def _score_sector_concentration(rows: list[GradedPredictionRow]) -> GapTypeScore | None:
    sectors = [r.sector_slug for r in rows if r.sector_slug]
    if len(sectors) < MIN_GRADED_RESOLVED:
        return None
    counts = Counter(sectors)
    top_slug, top_count = counts.most_common(1)[0]
    rate = top_count / len(sectors)
    if rate < SECTOR_CONCENTRATION_THRESHOLD:
        return None
    pct = round(rate * 100)
    sector_label = top_slug.replace("_", " ").title()
    return GapTypeScore(
        gap_type="sector_concentration",
        score=rate,
        pattern_explanation=(
            f"{pct}% of your recent resolved predictions ({top_count} of {len(sectors)}) "
            f"cluster in {sector_label} — rotate through another sector on The Map "
            "before your next batch so accuracy reflects reasoning, not sector beta."
        ),
    )


def score_gap_types(rows: list[GradedPredictionRow]) -> list[GapTypeScore]:
    """Score all taxonomy gaps; higher score = stronger pattern."""
    candidates: list[GapTypeScore] = []
    scorers = (
        _score_direction_magnitude,
        _score_narrative_anchoring,
        _score_sector_concentration,
    )
    for scorer in scorers:
        result = scorer(rows)
        if result is not None:
            candidates.append(result)
    return sorted(candidates, key=lambda g: (-g.score, g.gap_type))


def fetch_graded_resolved_predictions(user_id: UUID) -> list[GradedPredictionRow]:
    stmt = """
    SELECT
      up.mechanism_accuracy,
      up.business_accuracy,
      up.market_accuracy,
      (
        SELECT s.slug
        FROM public.instrument_assessments ia
        INNER JOIN public.instruments i
          ON i.ticker = ia.instrument_id AND i.exchange = 'NSE'
        INNER JOIN public.sectors s ON s.id = i.sector_id
        WHERE ia.card_id = c.id
        ORDER BY ia.created_at ASC
        LIMIT 1
      ) AS sector_slug
    FROM public.user_predictions up
    INNER JOIN public.cards c ON c.id = up.card_id
    WHERE up.user_id = %s::uuid
      AND c.lifecycle_state::text = 'resolved'
      AND up.mechanism_accuracy IS NOT NULL
    ORDER BY up.logged_at DESC
    LIMIT 50
    """
    rows: list[GradedPredictionRow] = []
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(user_id),))
        for row in cur.fetchall():
            rows.append(
                GradedPredictionRow(
                    mechanism_accuracy=row.get("mechanism_accuracy"),
                    business_accuracy=row.get("business_accuracy"),
                    market_accuracy=row.get("market_accuracy"),
                    sector_slug=row.get("sector_slug"),
                )
            )
    return rows


def analyse_from_history(history: list[GradedPredictionRow]) -> list[ReasoningGap]:
    """Score pre-fetched history (used by analyse and tests)."""
    if _graded_count(history) < MIN_GRADED_RESOLVED:
        return []

    scored = score_gap_types(history)[:3]
    gaps: list[ReasoningGap] = []
    for item in scored:
        module = resolve_module_for_gap_type(item.gap_type)
        if module is None:
            continue
        gaps.append(
            ReasoningGap(
                gap_type=item.gap_type,
                gap_name=GAP_TYPE_LABELS[item.gap_type],
                pattern_explanation=item.pattern_explanation,
                linked_map_module_id=module.id,
                linked_map_module_name=module.title,
            )
        )
    return gaps


def analyse(user_id: UUID) -> list[ReasoningGap]:
    """
    Return up to three reasoning gaps with Map module links.
    Empty when history is insufficient or no pattern clears the threshold.
    """
    return analyse_from_history(fetch_graded_resolved_predictions(user_id))


def analyse_with_meta(user_id: UUID) -> tuple[list[ReasoningGap], bool]:
    """Return gaps and whether history is too short to show the panel."""
    history = fetch_graded_resolved_predictions(user_id)
    insufficient = _graded_count(history) < MIN_GRADED_RESOLVED
    return analyse_from_history(history), insufficient


def recompute_for_user(user_id: UUID) -> list[ReasoningGap]:
    """On-demand / post-grade refresh hook (compute-only; no cache table)."""
    return analyse(user_id)


__all__ = [
    "MIN_GRADED_RESOLVED",
    "GradedPredictionRow",
    "ReasoningGap",
    "analyse",
    "analyse_from_history",
    "analyse_with_meta",
    "fetch_graded_resolved_predictions",
    "infer_gap_type_for_prediction",
    "recompute_for_user",
    "score_gap_types",
]
