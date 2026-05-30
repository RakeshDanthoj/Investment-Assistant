"""SEBI language compliance scan with YAML-driven patterns and allowlist (P3-S1j / G-15)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "sebi_compliance_patterns.yaml"


@dataclass(frozen=True)
class PatternRule:
    rule_id: str
    pattern: str
    description: str
    compiled: re.Pattern[str]


@dataclass(frozen=True)
class SebiPatternsConfig:
    blocked: tuple[PatternRule, ...]
    allowlist: tuple[PatternRule, ...]


@dataclass(frozen=True)
class SebiViolation:
    rule_id: str
    description: str
    matched_text: str
    context: str


@dataclass
class SebiComplianceResult:
    status: Literal["PASS", "FAIL"]
    violations: list[SebiViolation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "violations": [asdict(item) for item in self.violations],
        }


def _compile_rule(*, rule_id: str, pattern: str, description: str) -> PatternRule:
    return PatternRule(
        rule_id=rule_id,
        pattern=pattern,
        description=description,
        compiled=re.compile(pattern, re.IGNORECASE),
    )


def _parse_config(raw: object) -> SebiPatternsConfig:
    if not isinstance(raw, dict):
        raise ValueError("sebi_compliance_patterns.yaml must be a mapping")

    blocked: list[PatternRule] = []
    for entry in raw.get("blocked_patterns") or []:
        if not isinstance(entry, dict):
            raise ValueError("blocked_patterns entries must be mappings")
        blocked.append(
            _compile_rule(
                rule_id=str(entry["id"]),
                pattern=str(entry["pattern"]),
                description=str(entry.get("description") or entry["id"]),
            )
        )

    allowlist: list[PatternRule] = []
    for entry in raw.get("allowlist_patterns") or []:
        if not isinstance(entry, dict):
            raise ValueError("allowlist_patterns entries must be mappings")
        allowlist.append(
            _compile_rule(
                rule_id=str(entry["id"]),
                pattern=str(entry["pattern"]),
                description=str(entry.get("description") or entry["id"]),
            )
        )

    if not blocked:
        raise ValueError("blocked_patterns must not be empty")

    return SebiPatternsConfig(blocked=tuple(blocked), allowlist=tuple(allowlist))


@lru_cache(maxsize=1)
def load_sebi_patterns_config() -> SebiPatternsConfig:
    text = _CONFIG_PATH.read_text(encoding="utf-8")
    return _parse_config(yaml.safe_load(text))


def clear_sebi_patterns_config_cache() -> None:
    load_sebi_patterns_config.cache_clear()


def _collect_card_text(card: dict[str, Any]) -> str:
    parts = [
        str(card.get("title") or ""),
        str(card.get("insight_layer") or ""),
        str(card.get("context_layer") or ""),
        str(card.get("dissenting_view") or ""),
        str(card.get("framework_behind_this") or ""),
    ]

    assessments = card.get("instrument_assessments")
    if isinstance(assessments, list):
        for row in assessments:
            if not isinstance(row, dict):
                continue
            parts.extend(
                str(row.get(key) or "")
                for key in (
                    "reasoning",
                    "entry_conditions",
                    "exit_conditions",
                    "signal_label",
                )
            )

    return "\n".join(part for part in parts if part.strip())


def _is_allowlisted(*, text: str, start: int, end: int, allowlist: tuple[PatternRule, ...]) -> bool:
    window_start = max(0, start - 40)
    window_end = min(len(text), end + 40)
    context = text[window_start:window_end]
    return any(rule.compiled.search(context) for rule in allowlist)


def scan_text(text: str, *, config: SebiPatternsConfig | None = None) -> SebiComplianceResult:
    cfg = config or load_sebi_patterns_config()
    violations: list[SebiViolation] = []
    seen: set[tuple[str, int, int]] = set()

    for rule in cfg.blocked:
        for match in rule.compiled.finditer(text):
            span = (rule.rule_id, match.start(), match.end())
            if span in seen:
                continue
            if _is_allowlisted(
                text=text,
                start=match.start(),
                end=match.end(),
                allowlist=cfg.allowlist,
            ):
                continue
            seen.add(span)
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            violations.append(
                SebiViolation(
                    rule_id=rule.rule_id,
                    description=rule.description,
                    matched_text=match.group(0),
                    context=text[start:end].strip(),
                )
            )

    if violations:
        return SebiComplianceResult(status="FAIL", violations=violations)
    return SebiComplianceResult(status="PASS", violations=[])


def scan_card(card: dict[str, Any]) -> SebiComplianceResult:
    return scan_text(_collect_card_text(card))


__all__ = [
    "SebiComplianceResult",
    "SebiPatternsConfig",
    "SebiViolation",
    "clear_sebi_patterns_config_cache",
    "load_sebi_patterns_config",
    "scan_card",
    "scan_text",
]
