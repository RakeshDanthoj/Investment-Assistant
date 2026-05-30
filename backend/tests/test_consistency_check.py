"""Post-regen consistency check (P3-S1k)."""

from app.services.consistency_check import check_after_regen


def test_consistency_pass_when_regen_reuses_approved_ticker() -> None:
    card = {
        "insight_layer": "HDFCBANK sensitivity remains the focus [MEASURED].",
        "context_layer": "The -4 matrix reading anchors the story [MEASURED].",
        "evidence_layer": {
            "markdown": "HDFCBANK | crude_oil | sensitivity=-4",
            "matrix_snapshot": {"sensitivities": {"HDFCBANK": {}}},
        },
        "dissenting_view": "Counter view on transmission lag.",
        "framework_behind_this": "**Pattern**\n\nFramework text.",
        "instrument_assessments": [{"instrument_id": "HDFCBANK"}],
    }
    result = check_after_regen(
        card=card,
        regen_section="insight",
        regen_text="HDFCBANK remains central with the same -4 anchor [MEASURED].",
    )
    assert result.status == "PASS"


def test_consistency_fail_on_new_ticker() -> None:
    card = {
        "insight_layer": "HDFCBANK sensitivity remains the focus [MEASURED].",
        "context_layer": "The -4 matrix reading anchors the story [MEASURED].",
        "evidence_layer": {"markdown": "HDFCBANK | crude_oil | sensitivity=-4"},
        "dissenting_view": "Counter view on transmission lag.",
        "framework_behind_this": "**Pattern**\n\nFramework text.",
        "instrument_assessments": [{"instrument_id": "HDFCBANK"}],
    }
    result = check_after_regen(
        card=card,
        regen_section="context",
        regen_text="ICICIBANK could diverge from HDFCBANK on funding costs [JUDGED].",
    )
    assert result.status == "FAIL"
    assert any(c.entity == "ICICIBANK" for c in result.conflicts)
