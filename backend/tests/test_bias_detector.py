"""Bias detector unit tests — one scenario per detector (P1-S13)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.db.migrate import apply_migrations
from app.services.bias_detector import (
    BiasFinding,
    build_bias_audit,
    detect_all,
    detect_anchoring,
    detect_narrative,
    detect_recency,
    detect_sector_concentration,
    detect_survivorship,
)
from app.services.card_detail import build_evidence_rows


def _evidence_with_dates(days_ago: list[int]) -> dict:
    ref = datetime.now(tz=UTC)
    sources = []
    for d in days_ago:
        retrieved = (ref - timedelta(days=d)).isoformat()
        sources.append(
            {
                "claim": f"Claim {d}d",
                "source_name": "Reuters",
                "retrieved_at": retrieved,
                "mmj_type": "MEASURED",
            }
        )
    return {"sources": sources}


def test_detect_recency_flags_when_majority_recent() -> None:
    layer = _evidence_with_dates([5, 7, 10, 12, 400])
    finding = detect_recency(layer)
    assert finding is not None
    assert finding.severity == "flagged"
    assert finding.bias_type == "recency"


def test_detect_recency_monitored_when_sources_balanced() -> None:
    layer = _evidence_with_dates([10, 200, 400])
    finding = detect_recency(layer)
    assert finding is not None
    assert finding.severity == "monitored"


def test_detect_narrative_flags_high_confidence_few_sources() -> None:
    layer = {"sources": [{"claim": "A", "source_name": "Mint", "mmj_type": "MEASURED"}]}
    finding = detect_narrative(85, layer)
    assert finding.severity == "flagged"


def test_detect_narrative_monitored_when_enough_sources() -> None:
    layer = _evidence_with_dates([1, 2, 3])
    finding = detect_narrative(85, layer)
    assert finding.severity == "monitored"


def test_detect_survivorship_flags_historical_framing() -> None:
    finding = detect_survivorship(
        "Returns since 2010 look strong [MEASURED]",
        "",
        {},
    )
    assert finding.severity == "flagged"


def test_detect_survivorship_monitored_without_historical_framing() -> None:
    finding = detect_survivorship("Near-term liquidity stress [MEASURED]", "", {})
    assert finding.severity == "monitored"


def test_detect_anchoring_always_monitored() -> None:
    finding = detect_anchoring()
    assert finding.severity == "monitored"
    assert "separate" in finding.description.lower()


def test_build_evidence_rows_skips_llm_sources_for_narrative_count() -> None:
    layer = {
        "sources": [
            {"claim": "Real", "source_name": "Mint", "mmj_type": "MEASURED"},
            {"claim": "Skip", "source_name": "Gemini synthesis", "mmj_type": "MEASURED"},
        ]
    }
    assert len(build_evidence_rows(layer)) == 1


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


def test_detect_sector_concentration_flags_three_same_category(db_connection) -> None:
    card_ids: list[str] = []
    event_ids: list[str] = []
    try:
        for _ in range(3):
            event_id = uuid4()
            card_id = uuid4()
            event_ids.append(str(event_id))
            card_ids.append(str(card_id))
            with db_connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.events (
                      id, title, category, confidence_score, lifecycle_state,
                      canonical_url, event_source
                    )
                    VALUES (%s, %s, 'macro'::event_category, 60, 'published',
                      %s, 'pytest')
                    """,
                    (str(event_id), f"evt {event_id}", f"pytest:{event_id}@x.invalid"),
                )
                cur.execute(
                    """
                    INSERT INTO public.cards (
                      id, event_id, title, insight_layer, context_layer, evidence_layer,
                      dissenting_view, framework_behind_this, prompt_version, lifecycle_state
                    )
                    VALUES (
                      %s, %s, 'Card', 'Body [MEASURED]', 'Ctx', '{}'::jsonb,
                      'Dissent', 'Fw', 'pytest', 'published'
                    )
                    """,
                    (str(card_id), str(event_id)),
                )
        db_connection.commit()

        finding = detect_sector_concentration(UUID(card_ids[-1]), "macro")
        assert finding is not None
        assert finding.severity == "flagged"
    finally:
        with db_connection.cursor() as cur:
            for cid in card_ids:
                cur.execute("DELETE FROM public.card_bias_flags WHERE card_id = %s", (cid,))
                cur.execute("DELETE FROM public.cards WHERE id = %s", (cid,))
            for eid in event_ids:
                cur.execute("DELETE FROM public.events WHERE id = %s", (eid,))
        db_connection.commit()


def test_detect_all_persists_and_build_bias_audit(db_connection) -> None:
    event_id = uuid4()
    card_id = uuid4()
    recent_layer = _evidence_with_dates([1, 2, 3, 4, 5])
    try:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.events (
                  id, title, category, confidence_score, lifecycle_state,
                  canonical_url, event_source
                )
                VALUES (%s, %s, 'macro'::event_category, 85, 'published',
                  %s, 'pytest')
                """,
                (str(event_id), "Bias detect event", f"pytest:{event_id}@x.invalid"),
            )
            cur.execute(
                """
                INSERT INTO public.cards (
                  id, event_id, title, insight_layer, context_layer, evidence_layer,
                  dissenting_view, framework_behind_this, prompt_version, lifecycle_state
                )
                VALUES (
                  %s, %s, 'Card', 'Body [MEASURED]', 'Ctx', %s::jsonb,
                  'Dissent', 'Fw', 'pytest', 'published'
                )
                """,
                (str(card_id), str(event_id), __import__("json").dumps(recent_layer)),
            )
        db_connection.commit()

        findings = detect_all(card_id)
        assert len(findings) >= 5
        audit = build_bias_audit(card_id=card_id)
        assert "flags" in audit and "monitored" in audit
        flagged_types = {f["id"] for f in audit["flags"]}
        assert "recency" in flagged_types or "narrative" in flagged_types
    finally:
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM public.card_bias_flags WHERE card_id = %s", (str(card_id),))
            cur.execute("DELETE FROM public.cards WHERE id = %s", (str(card_id),))
            cur.execute("DELETE FROM public.events WHERE id = %s", (str(event_id),))
        db_connection.commit()


def test_build_bias_audit_splits_flagged_and_monitored() -> None:
    findings = [
        BiasFinding("recency", "flagged", "Too recent."),
        BiasFinding("anchoring", "monitored", "Separate dissent prompt."),
    ]
    audit = build_bias_audit(findings)
    assert len(audit["flags"]) == 1
    assert audit["flags"][0]["id"] == "recency"
    assert len(audit["monitored"]) == 1
    assert audit["monitored"][0]["id"] == "anchoring"
