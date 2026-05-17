from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from app.services.news_api_budget import reserve_news_api_call
from app.sources.base import AdapterSource, RawEvent, SourceAdapter, window_start

NEWS_URL = "https://newsapi.org/v2/everything"

NEWS_SEARCH_Q = "(India OR indian OR RBI OR Sensex OR Nifty OR NSE OR BSE)"


class NewsAPISourceAdapter(SourceAdapter):
    """NewsAPI headline fetch with daily quota enforced server-side."""

    adapter_source = AdapterSource.NEWSAPI

    def __init__(self, *, api_key: str) -> None:
        self._api_key = api_key.strip()

    def fetch(self, window: timedelta) -> list[RawEvent]:
        if not self._api_key:
            return []
        if not reserve_news_api_call():
            return []

        cutoff = window_start(window)
        params = {
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 45,
            "q": NEWS_SEARCH_Q,
            "from": cutoff.date().isoformat(),
        }

        resp = httpx.get(
            NEWS_URL,
            params=params,
            headers={"X-Api-Key": self._api_key},
            timeout=35.0,
        )
        resp.raise_for_status()
        blob = resp.json()
        rows: list[RawEvent] = []
        seen: set[str] = set()

        for art in blob.get("articles") or []:
            link = art.get("url") or ""
            title = art.get("title") or "(untitled headline)"
            if not link.strip():
                continue
            canon = self.canonical_url_from(link)
            published = _parse_article_time(art.get("publishedAt"))
            if published is None:
                pass
            else:
                au = published if published.tzinfo else published.replace(tzinfo=UTC)
                if au < cutoff.replace(tzinfo=UTC):
                    continue
            if canon in seen:
                continue
            seen.add(canon)

            excerpt = art.get("description") or ""
            rows.append(
                RawEvent(
                    title=title,
                    canonical_url=canon,
                    published_at=published,
                    excerpt=excerpt.strip()[:2000],
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
