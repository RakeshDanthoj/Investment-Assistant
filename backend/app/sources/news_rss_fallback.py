"""RSS fallback when NewsAPI rate-limits (PRD2 §4.4 — ET Markets, Mint)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import feedparser
import httpx

from app.sources.base import RawEvent, window_start

_LOG = logging.getLogger(__name__)

# PRD2 market-news fallback chain (after NewsAPI 429).
_FALLBACK_FEEDS: tuple[tuple[str, str], ...] = (
    (
        "et_markets",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    ),
    (
        "mint_markets",
        "https://www.livemint.com/rss/markets",
    ),
)


def fetch_rss_market_headlines(
    window: timedelta,
    *,
    keyword_query: str | None = None,
) -> list[RawEvent]:
    """
    Pull recent headlines from ET Markets and Mint RSS feeds.

    Optional ``keyword_query`` filters titles/descriptions by any keyword token (case-insensitive).
    """
    cutoff = window_start(window)
    tokens = _query_tokens(keyword_query)
    rows: list[RawEvent] = []
    seen: set[str] = set()

    for feed_name, url in _FALLBACK_FEEDS:
        try:
            payload = httpx.get(url, timeout=35.0, follow_redirects=True).content
            parsed = feedparser.parse(payload)
        except Exception as exc:
            _LOG.warning(
                "news_rss_fallback.feed_failed",
                extra={"feed": feed_name, "error": str(exc)},
            )
            continue

        for entry in parsed.entries or []:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            if tokens and not _matches_tokens(title, entry.get("summary") or "", tokens=tokens):
                continue
            canon = link.lower().split("#", 1)[0]
            if canon in seen:
                continue
            published = _entry_published(entry)
            if published is not None:
                pub = published if published.tzinfo else published.replace(tzinfo=UTC)
                if pub < cutoff.replace(tzinfo=UTC):
                    continue
            seen.add(canon)
            excerpt = (entry.get("summary") or "")[:2000]
            rows.append(
                RawEvent(
                    title=title,
                    canonical_url=canon,
                    published_at=published,
                    excerpt=excerpt.strip() or None,
                )
            )

    return rows


def _query_tokens(keyword_query: str | None) -> tuple[str, ...]:
    if not keyword_query:
        return ()
    raw = keyword_query.replace('"', " ").replace(" OR ", " ")
    return tuple(t.lower() for t in raw.split() if len(t) >= 3)


def _matches_tokens(title: str, summary: str, *, tokens: tuple[str, ...]) -> bool:
    blob = f"{title} {summary}".lower()
    return any(token in blob for token in tokens)


def _entry_published(entry: object) -> datetime | None:
    if not hasattr(entry, "get"):
        return None
    published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if published_parsed:
        try:
            return datetime(*published_parsed[:6], tzinfo=UTC)
        except (TypeError, ValueError):
            return None
    raw = entry.get("published") or entry.get("updated")
    if not raw or not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
