"""Load and validate NewsAPI factor keyword config (P3-S1d)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "newsapi_keywords.yaml"


@dataclass(frozen=True)
class FactorKeywordSet:
    slug: str
    daily_calls: int
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class NewsApiSchedulerConfig:
    mode: str
    max_daily_calls: int
    factors: tuple[FactorKeywordSet, ...]

    @property
    def factor_order(self) -> tuple[str, ...]:
        return tuple(f.slug for f in self.factors)

    @property
    def daily_budgets(self) -> dict[str, int]:
        return {f.slug: f.daily_calls for f in self.factors}

    def factor_by_slug(self, slug: str) -> FactorKeywordSet | None:
        for factor in self.factors:
            if factor.slug == slug:
                return factor
        return None

    def build_query(self, slug: str) -> str:
        factor = self.factor_by_slug(slug)
        if factor is None:
            raise KeyError(slug)
        quoted = [f'"{kw}"' if " " in kw else kw for kw in factor.keywords]
        return " OR ".join(quoted)


def _parse_config(raw: object) -> NewsApiSchedulerConfig:
    if not isinstance(raw, dict):
        raise ValueError("newsapi_keywords.yaml must be a mapping")
    scheduler = raw.get("scheduler")
    if not isinstance(scheduler, dict):
        raise ValueError("scheduler section required")
    mode = str(scheduler.get("mode", "round_robin"))
    max_daily = int(scheduler["max_daily_calls"])

    factors_raw = raw.get("factors")
    if not isinstance(factors_raw, dict) or not factors_raw:
        raise ValueError("factors section required")

    factors: list[FactorKeywordSet] = []
    total_budget = 0
    for slug, body in factors_raw.items():
        if not isinstance(body, dict):
            raise ValueError(f"factor {slug} must be a mapping")
        daily_calls = int(body["daily_calls"])
        keywords_raw = body.get("keywords")
        if not isinstance(keywords_raw, list) or not keywords_raw:
            raise ValueError(f"factor {slug} needs keywords")
        keywords = tuple(str(k).strip() for k in keywords_raw if str(k).strip())
        factors.append(FactorKeywordSet(slug=slug, daily_calls=daily_calls, keywords=keywords))
        total_budget += daily_calls

    if total_budget != max_daily:
        raise ValueError(
            f"factor daily_calls sum {total_budget} must equal max_daily_calls {max_daily}"
        )
    if len(factors) != 8:
        raise ValueError(f"expected 8 factors, got {len(factors)}")

    return NewsApiSchedulerConfig(mode=mode, max_daily_calls=max_daily, factors=tuple(factors))


@lru_cache(maxsize=1)
def load_newsapi_config() -> NewsApiSchedulerConfig:
    text = _CONFIG_PATH.read_text(encoding="utf-8")
    return _parse_config(yaml.safe_load(text))


def clear_newsapi_config_cache() -> None:
    load_newsapi_config.cache_clear()
