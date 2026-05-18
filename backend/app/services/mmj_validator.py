"""MMJ tag enforcement for quantitative prose (PRD §6.2 / §6.3)."""

from __future__ import annotations

import re

_HAS_DIGIT = re.compile(r"\d")
_MMJ_TAG = re.compile(
    r"\[(MEASURED|MODELLED|JUDGED)]",
    re.IGNORECASE,
)


def _split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+", text.strip())
    return [c.strip() for c in chunks if c.strip()]


def validate_mmj_tags(*, prose: str) -> None:
    """
    Any sentence containing a digit must include at least one MMJ tag in that sentence.
    """
    for sentence in _split_sentences(prose):
        if not _HAS_DIGIT.search(sentence):
            continue
        if not _MMJ_TAG.search(sentence):
            raise ValueError(
                "quantitative sentence missing [MEASURED]/[MODELLED]/[JUDGED] tag: "
                + sentence[:240]
            )
