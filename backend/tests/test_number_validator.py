
import pytest

from app.services.number_validator import (
    NumberValidationFailedError,
    check,
    validate_numbers_in_evidence,
)


def test_rejects_hallucinated_number() -> None:
    corpus = "sensitivity for hdfcbank on crude_oil axis is -4 per factor database snapshot."
    with pytest.raises(ValueError, match="numeric token"):
        validate_numbers_in_evidence(
            prose="Some analysts cite a 99.9% certainty about moves [JUDGED].",
            evidence_corpus=corpus,
        )


def test_accepts_grounded_number_with_mmj() -> None:
    corpus = "sensitivity for hdfcbank on crude_oil axis is -4 per factor database snapshot."
    validate_numbers_in_evidence(
        prose="The matrix flags about -4 on crude for this name [MEASURED].",
        evidence_corpus=corpus,
    )


def test_check_returns_structured_fail_with_sentence() -> None:
    evidence = {
        "markdown": (
            "sensitivity for hdfcbank on crude_oil axis is -4 per factor database snapshot."
        ),
    }
    result = check(
        insight="Some analysts cite a 99.9% certainty about moves [JUDGED].",
        context="",
        evidence_layer=evidence,
    )
    assert result.status == "FAIL"
    assert len(result.ungrounded) == 1
    assert result.ungrounded[0].number == "99.9%"
    assert "99.9%" in result.ungrounded[0].sentence
    assert result.ungrounded[0].index == 0


def test_check_passes_when_numbers_grounded() -> None:
    evidence = {
        "markdown": (
            "sensitivity for hdfcbank on crude_oil axis is -4 per factor database snapshot."
        ),
    }
    result = check(
        insight="The matrix flags about -4 on crude for this name [MEASURED].",
        context="No extra numbers here [MEASURED].",
        evidence_layer=evidence,
    )
    assert result.status == "PASS"
    assert result.ungrounded == []


def test_check_reports_missing_provenance() -> None:
    evidence = {
        "sources": [
            {
                "id": "src-1",
                "claim": "Repo rate held at 6.5%",
                "source_name": "RBI",
            }
        ],
    }
    result = check(
        insight="Policy held at 6.5% [MEASURED].",
        context="",
        evidence_layer=evidence,
    )
    assert result.status == "FAIL"
    assert result.missing_provenance
    assert result.missing_provenance[0].evidence_id == "src-1"
    assert "source_url" in result.missing_provenance[0].missing_fields
    assert "retrieved_at" in result.missing_provenance[0].missing_fields
    assert "mmj_tag" in result.missing_provenance[0].missing_fields


def test_comparative_quantifiers_are_soft_warnings_only() -> None:
    evidence = {"markdown": "No numeric tokens in this evidence corpus."}
    result = check(
        insight="Inflation doubled versus last year [JUDGED].",
        context="This is a record high for the sector [JUDGED].",
        evidence_layer=evidence,
    )
    assert result.status == "PASS"
    assert len(result.comparative_flags) >= 2
    assert any("doubled" in flag.lower() for flag in result.comparative_flags)


def test_accepts_ordered_list_markers_without_grounding() -> None:
    evidence = {"markdown": "No numeric evidence required for list markers."}
    result = check(
        insight="",
        context=(
            "1. Step one explains the mechanism [MEASURED].\n"
            "2. Step two adds detail [MEASURED]."
        ),
        evidence_layer=evidence,
    )
    assert result.status == "PASS"
    assert result.ungrounded == []


def test_number_validation_failed_error_carries_result() -> None:
    result = check(
        insight="Unsupported 42% move [JUDGED].",
        context="",
        evidence_layer={"markdown": "no matching numbers"},
    )
    exc = NumberValidationFailedError(result)
    assert exc.result.status == "FAIL"
    assert exc.result.ungrounded
