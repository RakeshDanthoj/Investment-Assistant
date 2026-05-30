"""Ensure Insight/Context numerics appear in the Evidence corpus (PRD §6.3, G-07)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

_LOG = logging.getLogger(__name__)

# Currency, percentages, and standalone numeric tokens (conservative).
_NUMERIC_TOKEN = re.compile(
    r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d+)?|\d[\d,]*(?:\.\d+)?%|(?<!\w)\d[\d,]*(?:\.\d+)?(?!\w)",
    re.IGNORECASE,
)

_COMPARATIVE_QUANTIFIERS = re.compile(
    r"\b(doubled|tripled|quadrupled|record\s+high|record\s+low|all[- ]time\s+high|"
    r"all[- ]time\s+low|historic\s+high|historic\s+low)\b",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class UngroundedNumber:
    sentence: str
    number: str
    index: int


@dataclass(frozen=True)
class MissingProvenance:
    evidence_id: str
    missing_fields: list[str]


@dataclass
class NumberValidationResult:
    status: Literal["PASS", "FAIL"]
    ungrounded: list[UngroundedNumber] = field(default_factory=list)
    missing_provenance: list[MissingProvenance] = field(default_factory=list)
    comparative_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ungrounded": [asdict(item) for item in self.ungrounded],
            "missing_provenance": [asdict(item) for item in self.missing_provenance],
            "comparative_flags": self.comparative_flags,
        }


class NumberValidationFailedError(ValueError):
    """Raised when publish is blocked by the number validator hard gate."""

    def __init__(self, result: NumberValidationResult) -> None:
        self.result = result
        super().__init__("number validator failed")


def normalize_numeric_token(raw: str) -> str:
    s = raw.strip()
    s = s.replace(",", "")
    s = re.sub(r"^(?:₹|Rs\.?|INR)\s*", "", s, flags=re.IGNORECASE)
    return s.strip().lower()


def extract_numeric_tokens(text: str) -> list[str]:
    return [normalized for _, normalized in _extract_numeric_spans(text)]


def _should_skip_numeric_match(sentence: str, match: re.Match[str]) -> bool:
    """Skip ordered-list markers such as '1.' at the start of a step sentence."""
    display = match.group(0).strip()
    if not re.fullmatch(r"\d{1,2}", display):
        return False
    end = match.end()
    if end < len(sentence) and sentence[end] == ".":
        after = sentence[end + 1 : end + 2]
        if not after or after.isspace():
            return True
    return False


def _extract_numeric_spans(text: str) -> list[tuple[str, str]]:
    """Return (display_token, normalized_token) pairs preserving match order."""
    out: list[tuple[str, str]] = []
    for match in _NUMERIC_TOKEN.finditer(text):
        if _should_skip_numeric_match(text, match):
            continue
        display = match.group(0).strip()
        out.append((display, normalize_numeric_token(display)))
    return out


def evidence_corpus(evidence_layer: dict[str, Any]) -> str:
    parts = [
        str(evidence_layer.get("markdown") or ""),
        str(evidence_layer.get("macro_stub") or ""),
        json.dumps(evidence_layer.get("matrix_snapshot") or {}, sort_keys=True),
        json.dumps(evidence_layer.get("event_snapshot") or {}, sort_keys=True),
    ]
    sources = evidence_layer.get("sources")
    if isinstance(sources, list):
        for item in sources:
            if isinstance(item, dict):
                parts.append(str(item.get("claim") or item.get("title") or ""))
                parts.append(str(item.get("source_excerpt") or ""))
    return "\n\n".join(parts).replace(",", "").lower()


def _split_sentences(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    parts = _SENTENCE_SPLIT.split(stripped)
    return [part.strip() for part in parts if part.strip()]


def _collect_provenance_rows(evidence_layer: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    sources = evidence_layer.get("sources")
    if isinstance(sources, list):
        for idx, item in enumerate(sources):
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "evidence_id": str(item.get("id") or f"source-{idx}"),
                    "source_url": str(item.get("source_url") or item.get("url") or "").strip(),
                    "retrieved_at": item.get("retrieved_at") or item.get("date_retrieved"),
                    "mmj_tag": str(
                        item.get("mmj_tag") or item.get("mmj_type") or item.get("mmj") or ""
                    ).strip(),
                    "source_excerpt": str(
                        item.get("source_excerpt") or item.get("claim") or item.get("title") or ""
                    ),
                }
            )

    ms = evidence_layer.get("matrix_snapshot") or {}
    sens = ms.get("sensitivities") or {}
    if isinstance(sens, dict):
        for ticker, factors in sens.items():
            if not isinstance(factors, dict):
                continue
            for fslug, cell in factors.items():
                if not isinstance(cell, dict):
                    continue
                rows.append(
                    {
                        "evidence_id": f"matrix:{ticker}:{fslug}",
                        "source_url": str(cell.get("source_url") or "").strip(),
                        "retrieved_at": cell.get("retrieved_at"),
                        "mmj_tag": str(cell.get("mmj_tag") or "").strip(),
                        "source_excerpt": (
                            f"{ticker} | {fslug} | sensitivity={cell.get('sensitivity')}"
                        ),
                    }
                )

    return rows


def _find_missing_provenance(evidence_layer: dict[str, Any]) -> list[MissingProvenance]:
    rows = _collect_provenance_rows(evidence_layer)
    missing: list[MissingProvenance] = []
    for row in rows:
        absent: list[str] = []
        if not row.get("source_url"):
            absent.append("source_url")
        if not row.get("retrieved_at"):
            absent.append("retrieved_at")
        if not row.get("mmj_tag"):
            absent.append("mmj_tag")
        if absent:
            missing.append(
                MissingProvenance(evidence_id=str(row["evidence_id"]), missing_fields=absent)
            )
    return missing


def _find_ungrounded(*, prose: str, corpus_norm: str) -> list[UngroundedNumber]:
    sentences = _split_sentences(prose)
    if not sentences and prose.strip():
        sentences = [prose.strip()]

    ungrounded: list[UngroundedNumber] = []
    seen: set[tuple[int, str]] = set()
    for index, sentence in enumerate(sentences):
        for display, normalized in _extract_numeric_spans(sentence):
            key = (index, normalized)
            if key in seen:
                continue
            seen.add(key)
            if normalized not in corpus_norm:
                ungrounded.append(
                    UngroundedNumber(sentence=sentence, number=display, index=index)
                )
    return ungrounded


def _detect_comparative_flags(*texts: str) -> list[str]:
    flags: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for match in _COMPARATIVE_QUANTIFIERS.finditer(text):
            phrase = match.group(0).strip()
            low = phrase.lower()
            if low in seen:
                continue
            seen.add(low)
            flags.append(phrase)
    return flags


def check(
    *,
    insight: str,
    context: str,
    evidence_layer: dict[str, Any],
) -> NumberValidationResult:
    """
    Hard publish gate: every numeric token in Insight/Context must appear in Evidence,
    and every structured Evidence row must carry source_url, retrieved_at, and mmj_tag.
    Comparative quantifiers are soft warnings only (logged, non-blocking).
    """
    layer = evidence_layer if isinstance(evidence_layer, dict) else {}
    corpus_norm = evidence_corpus(layer)
    combined = f"{insight}\n{context}".strip()

    comparative_flags = _detect_comparative_flags(insight, context)
    if comparative_flags:
        _LOG.info(
            "number_validator comparative quantifier soft flags card_id=unknown phrases=%s",
            comparative_flags,
        )

    ungrounded = _find_ungrounded(prose=combined, corpus_norm=corpus_norm)
    missing_provenance = _find_missing_provenance(layer)

    if ungrounded or missing_provenance:
        return NumberValidationResult(
            status="FAIL",
            ungrounded=ungrounded,
            missing_provenance=missing_provenance,
            comparative_flags=comparative_flags,
        )
    return NumberValidationResult(status="PASS", comparative_flags=comparative_flags)


def check_card(card: dict[str, Any]) -> NumberValidationResult:
    """Validate ICE layers on a card detail/review row."""
    evidence = card.get("evidence_layer")
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence) if evidence.strip() else {}
        except json.JSONDecodeError:
            evidence = {}
    if not isinstance(evidence, dict):
        evidence = {}

    return check(
        insight=str(card.get("insight_layer") or ""),
        context=str(card.get("context_layer") or ""),
        evidence_layer=evidence,
    )


def validate_numbers_in_evidence(*, prose: str, evidence_corpus: str) -> None:
    """
    Raises ValueError listing the first offending token not found in evidence_corpus
    (after normalising commas; case-insensitive substring match on corpus).
    """
    corpus_norm = evidence_corpus.replace(",", "").lower()
    seen: set[str] = set()
    for _, token in _extract_numeric_spans(prose):
        if token in seen:
            continue
        seen.add(token)
        if token not in corpus_norm:
            raise ValueError(f"numeric token not grounded in evidence: {token!r}")


def assert_numbers_in_evidence(*, prose: str, evidence_layer: dict[str, Any]) -> None:
    """Pipeline helper — raises ValueError on first ungrounded token."""
    layer = evidence_layer if isinstance(evidence_layer, dict) else {}
    validate_numbers_in_evidence(prose=prose, evidence_corpus_text=evidence_corpus(layer))
