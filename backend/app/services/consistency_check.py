"""Post-regen consistency check — entity references vs approved sections (G-09)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

_TICKER = re.compile(r"\b[A-Z]{2,12}\b")

# Common uppercase tokens that are not NSE tickers.
_TICKER_BLOCKLIST = frozenset(
    {
        "ICE",
        "MMJ",
        "NIM",
        "NSE",
        "RBI",
        "SEBI",
        "USD",
        "INR",
        "GDP",
        "CPI",
        "API",
        "URL",
        "PRD",
        "PASS",
        "FAIL",
        "TRUE",
        "FALSE",
        "JSON",
        "LLM",
    }
)

SectionKey = Literal["insight", "context", "evidence", "dissent", "framework"]


@dataclass(frozen=True)
class ConsistencyConflict:
    entity: str
    message: str


@dataclass
class ConsistencyCheckResult:
    status: Literal["PASS", "FAIL"]
    conflicts: list[ConsistencyConflict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "conflicts": [asdict(item) for item in self.conflicts],
        }


def _extract_tickers(text: str) -> set[str]:
    found: set[str] = set()
    for match in _TICKER.finditer(text):
        token = match.group(0)
        if token not in _TICKER_BLOCKLIST:
            found.add(token)
    return found


def _section_text(card: dict[str, Any], section: SectionKey) -> str:
    if section == "insight":
        return str(card.get("insight_layer") or "")
    if section == "context":
        return str(card.get("context_layer") or "")
    if section == "dissent":
        return str(card.get("dissenting_view") or "")
    if section == "framework":
        return str(card.get("framework_behind_this") or "")
    evidence = card.get("evidence_layer")
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence) if evidence.strip() else {}
        except json.JSONDecodeError:
            evidence = {}
    if not isinstance(evidence, dict):
        evidence = {}
    parts = [
        str(evidence.get("markdown") or ""),
        str(evidence.get("macro_stub") or ""),
        json.dumps(evidence.get("matrix_snapshot") or {}, sort_keys=True),
    ]
    return "\n".join(parts)


def _approved_entities(card: dict[str, Any], *, exclude: SectionKey) -> set[str]:
    entities: set[str] = set()
    for section in ("insight", "context", "evidence", "dissent", "framework"):
        if section == exclude:
            continue
        entities |= _extract_tickers(_section_text(card, section))
    for row in card.get("instrument_assessments") or []:
        if isinstance(row, dict):
            ticker = str(row.get("instrument_id") or "").strip().upper()
            if ticker:
                entities.add(ticker)
    return entities


def check_after_regen(
    *,
    card: dict[str, Any],
    regen_section: SectionKey,
    regen_text: str,
) -> ConsistencyCheckResult:
    """
    Flag tickers introduced in the regenerated section that do not appear in
    any approved section or the evidence corpus.
    """
    approved = _approved_entities(card, exclude=regen_section)
    evidence_entities = _extract_tickers(_section_text(card, "evidence"))
    allowed = approved | evidence_entities

    regen_entities = _extract_tickers(regen_text)
    conflicts: list[ConsistencyConflict] = []
    for entity in sorted(regen_entities):
        if entity not in allowed:
            conflicts.append(
                ConsistencyConflict(
                    entity=entity,
                    message=(
                        f"{entity} appears in regenerated {regen_section} "
                        "but not in approved sections or evidence"
                    ),
                )
            )

    if conflicts:
        return ConsistencyCheckResult(status="FAIL", conflicts=conflicts)
    return ConsistencyCheckResult(status="PASS")


__all__ = [
    "ConsistencyCheckResult",
    "ConsistencyConflict",
    "SectionKey",
    "check_after_regen",
]
