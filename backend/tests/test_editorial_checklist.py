"""Editorial checklist — four automated + one manual gate (P3-S1j / G-15)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.editorial_checklist import (
    DISSENT_MIN_CHARS,
    EditorialChecklistFailedError,
    assert_automated_pass,
    check_card,
)
from app.services.sebi_compliance_scan import scan_text

_LONG_DISSENT = "x" * (DISSENT_MIN_CHARS + 1)


def _base_card(**overrides: object) -> dict:
    card = {
        "title": "Macro card [MEASURED]",
        "insight_layer": "Insight body cites 4 on crude axis [MEASURED].",
        "context_layer": "Context explains transmission [JUDGED].",
        "dissenting_view": _LONG_DISSENT,
        "framework_behind_this": "Framework notes [MEASURED].",
        "evidence_layer": {
            "markdown": "sensitivity is 4 on crude axis for the name.",
            "sources": [
                {
                    "id": "src-1",
                    "source_url": "https://example.com/report",
                    "retrieved_at": datetime.now(UTC).isoformat(),
                    "mmj_tag": "MEASURED",
                    "source_excerpt": "sensitivity is 4 on crude axis",
                }
            ],
        },
    }
    card.update(overrides)
    return card


def test_checklist_all_automated_pass_on_happy_path() -> None:
    result = check_card(_base_card())
    automated = [item for item in result.items if item.automated]
    assert len(automated) == 4
    assert all(item.status == "PASS" for item in automated)
    assert result.all_automated_pass is True
    assert result.items[-1].key == "plain_english"
    assert result.items[-1].automated is False


def test_dissent_length_gate_fails_when_too_short() -> None:
    result = check_card(_base_card(dissenting_view="Too short."))
    dissent = next(item for item in result.items if item.key == "dissent")
    assert dissent.status == "FAIL"
    assert result.all_automated_pass is False


def test_evidence_freshness_blocks_rows_older_than_eighteen_months() -> None:
    stale = datetime.now(UTC) - timedelta(days=600)
    card = _base_card(
        evidence_layer={
            "sources": [
                {
                    "id": "old-src",
                    "source_url": "https://example.com/old",
                    "retrieved_at": stale.isoformat(),
                    "mmj_tag": "MEASURED",
                    "source_excerpt": "4 on crude axis",
                }
            ]
        }
    )
    result = check_card(card)
    freshness = next(item for item in result.items if item.key == "evidence_freshness")
    assert freshness.status == "FAIL"
    assert freshness.details is not None
    assert freshness.details["stale_rows"]


def test_sebi_scan_blocks_buy_language() -> None:
    result = scan_text("Analysts should buy this name on dips.")
    assert result.status == "FAIL"
    assert any(v.rule_id == "buy_recommendation" for v in result.violations)


def test_sebi_scan_allows_repo_rate_hold_phrase() -> None:
    result = scan_text("RBI kept the repo rate hold unchanged at the MPC meeting.")
    assert result.status == "PASS"


def test_sebi_scan_allows_hold_rate_phrase() -> None:
    result = scan_text("The MPC may hold rates steady while inflation cools.")
    assert result.status == "PASS"


def test_checklist_sebi_item_fails_when_buy_present() -> None:
    card = _base_card(insight_layer="Investors should buy the dip on this name [JUDGED].")
    result = check_card(card)
    sebi = next(item for item in result.items if item.key == "sebi_compliance")
    assert sebi.status == "FAIL"


def test_assert_automated_pass_raises_on_failure() -> None:
    with pytest.raises(EditorialChecklistFailedError):
        assert_automated_pass(_base_card(dissenting_view="short"))


def test_assert_automated_pass_succeeds_on_happy_path() -> None:
    assert_automated_pass(_base_card())
