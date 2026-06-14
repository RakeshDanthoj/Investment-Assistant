import pytest

from app.services.mmj_validator import repair_mmj_tags, validate_mmj_tags


def test_mmj_missing_on_quant_sentence() -> None:
    with pytest.raises(ValueError, match="missing"):
        validate_mmj_tags(prose="Inflation printed at 5.2% last quarter.")


def test_mmj_present() -> None:
    validate_mmj_tags(prose="Inflation printed at 5.2% last quarter [MEASURED].")


def test_mmj_split_sentences() -> None:
    validate_mmj_tags(
        prose="First line without digits. Second line shows 3 [MEASURED] which is allowed."
    )


def test_repair_mmj_tags_appends_judged_to_quant_sentence() -> None:
    repaired = repair_mmj_tags(
        prose="Repo rate reduction of 25 basis points or more",
    )
    assert repaired == "Repo rate reduction of 25 basis points or more [JUDGED]."
    validate_mmj_tags(prose=repaired)


def test_repair_mmj_tags_leaves_tagged_sentence_unchanged() -> None:
    original = "Sensitivity near -4 on the matrix [MEASURED]."
    assert repair_mmj_tags(prose=original) == original


def test_repair_mmj_tags_leaves_non_quant_sentence_unchanged() -> None:
    original = "Further policy tightening signal from RBI"
    assert repair_mmj_tags(prose=original) == original


def test_repair_mmj_tags_uses_measured_for_evidence_layers() -> None:
    repaired = repair_mmj_tags(
        prose="HDFCBANK shows crude sensitivity near -4 on the seeded matrix",
        default_tag="MEASURED",
    )
    assert repaired == "HDFCBANK shows crude sensitivity near -4 on the seeded matrix [MEASURED]."
    validate_mmj_tags(prose=repaired)
