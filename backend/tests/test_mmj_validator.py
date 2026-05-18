import pytest

from app.services.mmj_validator import validate_mmj_tags


def test_mmj_missing_on_quant_sentence() -> None:
    with pytest.raises(ValueError, match="missing"):
        validate_mmj_tags(prose="Inflation printed at 5.2% last quarter.")


def test_mmj_present() -> None:
    validate_mmj_tags(prose="Inflation printed at 5.2% last quarter [MEASURED].")


def test_mmj_split_sentences() -> None:
    validate_mmj_tags(
        prose="First line without digits. Second line shows 3 [MEASURED] which is allowed."
    )
