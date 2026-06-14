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


def repair_mmj_tags(*, prose: str, default_tag: str = "JUDGED") -> str:
    """
    Append an MMJ tag to quantitative sentences that lack one.

    Used for hypothetical monitor strings (entry/exit conditions) where [JUDGED]
    is the correct provenance when the model omits a tag.
    """
    tag = f"[{default_tag}]"
    repaired: list[str] = []
    for sentence in _split_sentences(prose):
        if _HAS_DIGIT.search(sentence) and not _MMJ_TAG.search(sentence):
            stripped = sentence.rstrip()
            if stripped.endswith((".", "!", "?")):
                stripped = stripped[:-1].rstrip()
            repaired.append(f"{stripped} {tag}.")
        else:
            repaired.append(sentence)
    return " ".join(repaired)


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
