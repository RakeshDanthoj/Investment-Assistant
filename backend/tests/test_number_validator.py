from pathlib import Path

import pytest

from app.services.number_validator import validate_numbers_in_evidence


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
