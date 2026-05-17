from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import ClassVar
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


@dataclass(frozen=True)
class RawEvent:
    """Normalized item from an external provider before persistence."""

    title: str
    canonical_url: str
    published_at: datetime | None
    excerpt: str | None = None


class SourceFailure(RuntimeError):
    """Raised when a source adapter cannot honour the request (treat as empty snapshot)."""


class AdapterSource(StrEnum):
    NEWSAPI = "newsapi"
    RBI_RSS = "rbi_rss"
    NSE_BSE = "nse_bse"


def normalize_canonical_url(url: str) -> str:
    """Strip trackers and insignificant parts for stable dedupe keys."""
    raw = url.strip()
    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        return raw.lower()
    q = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if not k.lower().startswith("utm_")
    ]
    rebuilt = parsed._replace(
        fragment="",
        query=urlencode(q),
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=parsed.path or "",
    )
    return urlunparse(rebuilt)


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def window_start(window: timedelta) -> datetime:
    return utc_now() - window


class SourceAdapter(ABC):
    """Implement one concrete class per feed; callers merge results."""

    adapter_source: ClassVar[AdapterSource]

    def canonical_url_from(self, url: str) -> str:
        return normalize_canonical_url(url)

    @abstractmethod
    def fetch(self, window: timedelta) -> list[RawEvent]:
        """Pull recent items within the trailing time window."""
