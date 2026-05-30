"""Load critical market fact definitions (P3-S1f / G-06)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "critical_facts.yaml"


@dataclass(frozen=True)
class StalenessThresholds:
    fresh_max_hours: float
    stale_max_hours: float


@dataclass(frozen=True)
class CriticalFactDefinition:
    fact_id: str
    label: str
    critical: bool
    chain: tuple[str, ...]
    yfinance_symbol: str | None = None
    config_fallback_value: str | None = None
    config_fallback_observed_hours_ago: float | None = None


@dataclass(frozen=True)
class CriticalFactsConfig:
    staleness: StalenessThresholds
    facts: tuple[CriticalFactDefinition, ...]

    def fact_by_id(self, fact_id: str) -> CriticalFactDefinition | None:
        for fact in self.facts:
            if fact.fact_id == fact_id:
                return fact
        return None

    @property
    def critical_fact_ids(self) -> tuple[str, ...]:
        return tuple(f.fact_id for f in self.facts if f.critical)


def _parse_config(raw: object) -> CriticalFactsConfig:
    if not isinstance(raw, dict):
        raise ValueError("critical_facts.yaml must be a mapping")

    staleness_raw = raw.get("staleness")
    if not isinstance(staleness_raw, dict):
        raise ValueError("staleness section required")
    staleness = StalenessThresholds(
        fresh_max_hours=float(staleness_raw["fresh_max_hours"]),
        stale_max_hours=float(staleness_raw["stale_max_hours"]),
    )
    if staleness.fresh_max_hours <= 0 or staleness.stale_max_hours <= staleness.fresh_max_hours:
        raise ValueError("staleness thresholds must be positive with stale > fresh")

    facts_raw = raw.get("facts")
    if not isinstance(facts_raw, dict) or not facts_raw:
        raise ValueError("facts section required")
    if len(facts_raw) > 5:
        raise ValueError("critical_facts.yaml allows at most 5 facts")

    facts: list[CriticalFactDefinition] = []
    for fact_id, body in facts_raw.items():
        if not isinstance(body, dict):
            raise ValueError(f"fact {fact_id} must be a mapping")
        chain_raw = body.get("chain")
        if not isinstance(chain_raw, list) or not chain_raw:
            raise ValueError(f"fact {fact_id} needs a non-empty chain")
        chain = tuple(str(step).strip() for step in chain_raw if str(step).strip())
        facts.append(
            CriticalFactDefinition(
                fact_id=str(fact_id),
                label=str(body["label"]),
                critical=bool(body.get("critical", True)),
                chain=chain,
                yfinance_symbol=(
                    str(body["yfinance_symbol"]) if body.get("yfinance_symbol") else None
                ),
                config_fallback_value=(
                    str(body["config_fallback_value"])
                    if body.get("config_fallback_value")
                    else None
                ),
                config_fallback_observed_hours_ago=(
                    float(body["config_fallback_observed_hours_ago"])
                    if body.get("config_fallback_observed_hours_ago") is not None
                    else None
                ),
            )
        )

    return CriticalFactsConfig(staleness=staleness, facts=tuple(facts))


@lru_cache(maxsize=1)
def load_critical_facts_config() -> CriticalFactsConfig:
    text = _CONFIG_PATH.read_text(encoding="utf-8")
    return _parse_config(yaml.safe_load(text))


def clear_critical_facts_config_cache() -> None:
    load_critical_facts_config.cache_clear()


__all__ = [
    "CriticalFactDefinition",
    "CriticalFactsConfig",
    "StalenessThresholds",
    "clear_critical_facts_config_cache",
    "load_critical_facts_config",
]
