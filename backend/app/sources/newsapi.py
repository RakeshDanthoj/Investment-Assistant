"""NewsAPI adapter with factor round-robin scheduler (P3-S1d)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from app.services.factor_poll_log import (
    factor_poll_counts_today,
    last_polled_factor_slug,
    record_factor_poll,
)
from app.services.news_api_budget import reserve_news_api_call
from app.services.newsapi_config import load_newsapi_config
from app.services.newsapi_scheduler import resolve_next_factor
from app.sources.base import AdapterSource, RawEvent, SourceAdapter, window_start
from app.sources.news_rss_fallback import fetch_rss_market_headlines

_LOG = logging.getLogger(__name__)

NEWS_URL = "https://newsapi.org/v2/everything"

PollStatus = str  # ok | empty | error


@dataclass(frozen=True)
class NewsApiPollResult:
    """Outcome of one detection-cron NewsAPI tick (for tests and digest)."""

    factor_slug: str | None
    poll_status: PollStatus | None
    article_count: int
    used_rss_fallback: bool


class NewsAPISourceAdapter(SourceAdapter):
    """NewsAPI headline fetch: one macro factor per tick, daily budgets, poll audit log."""

    adapter_source = AdapterSource.NEWSAPI

    def __init__(self, *, api_key: str) -> None:
        self._api_key = api_key.strip()
        self._last_poll: NewsApiPollResult | None = None

    @property
    def last_poll(self) -> NewsApiPollResult | None:
        return self._last_poll

    def fetch(self, window: timedelta) -> list[RawEvent]:
        self._last_poll = None
        if not self._api_key:
            return []

        config = load_newsapi_config()
        factor_slug = resolve_next_factor(
            last_polled_slug=last_polled_factor_slug(),
            counts_today=factor_poll_counts_today(),
            config=config,
        )
        if factor_slug is None:
            _LOG.info("newsapi.scheduler.all_budgets_exhausted")
            return []

        if not reserve_news_api_call(ceiling=config.max_daily_calls):
            _LOG.warning("newsapi.scheduler.global_budget_exhausted")
            return []

        query = config.build_query(factor_slug)
        poll_status, articles, used_fallback = self._poll_newsapi_or_fallback(
            window,
            query=query,
        )
        article_count = len(articles)
        record_factor_poll(
            factor_slug=factor_slug,
            status=poll_status,
            article_count=article_count,
        )
        self._last_poll = NewsApiPollResult(
            factor_slug=factor_slug,
            poll_status=poll_status,
            article_count=article_count,
            used_rss_fallback=used_fallback,
        )
        _LOG.info(
            "newsapi.poll_status",
            extra={
                "factor": factor_slug,
                "poll_status": poll_status,
                "article_count": article_count,
                "rss_fallback": used_fallback,
            },
        )
        return articles

    def _poll_newsapi_or_fallback(
        self,
        window: timedelta,
        *,
        query: str,
    ) -> tuple[PollStatus, list[RawEvent], bool]:
        cutoff = window_start(window)
        params = {
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 45,
            "q": query,
            "from": cutoff.date().isoformat(),
        }

        try:
            resp = httpx.get(
                NEWS_URL,
                params=params,
                headers={"X-Api-Key": self._api_key},
                timeout=35.0,
            )
        except httpx.HTTPError:
            return "error", [], False

        if resp.status_code == 429:
            _LOG.warning("newsapi.rate_limited", extra={"status": 429})
            fallback_rows = fetch_rss_market_headlines(window, keyword_query=query)
            status: PollStatus = "ok" if fallback_rows else "empty"
            return status, fallback_rows, True

        if resp.status_code >= 500:
            return "error", [], False

        if resp.status_code >= 400:
            return "error", [], False

        try:
            blob = resp.json()
        except ValueError:
            return "error", [], False

        rows = _articles_from_blob(blob, cutoff=cutoff, canonicalize=self.canonical_url_from)
        if rows:
            return "ok", rows, False
        return "empty", [], False


def _articles_from_blob(
    blob: object,
    *,
    cutoff: datetime,
    canonicalize,
) -> list[RawEvent]:
    if not isinstance(blob, dict):
        return []
    rows: list[RawEvent] = []
    seen: set[str] = set()

    for art in blob.get("articles") or []:
        if not isinstance(art, dict):
            continue
        link = art.get("url") or ""
        title = art.get("title") or "(untitled headline)"
        if not str(link).strip():
            continue
        canon = canonicalize(str(link))
        published = _parse_article_time(art.get("publishedAt"))
        if published is not None:
            au = published if published.tzinfo else published.replace(tzinfo=UTC)
            if au < cutoff.replace(tzinfo=UTC):
                continue
        if canon in seen:
            continue
        seen.add(canon)

        excerpt = art.get("description") or ""
        rows.append(
            RawEvent(
                title=str(title),
                canonical_url=canon,
                published_at=published,
                excerpt=str(excerpt).strip()[:2000] or None,
            )
        )

    return rows


def _parse_article_time(raw: object) -> datetime | None:
    if not raw or not isinstance(raw, str):
        return None
    try:
        normalized = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None
