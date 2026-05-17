"""RBI RSS press-release feed."""

from __future__ import annotations

import calendar
import time
from datetime import UTC, datetime, timedelta

import feedparser
import httpx

from app.sources.base import AdapterSource, RawEvent, SourceAdapter, SourceFailure, window_start

# Official RBI communications RSS landing (handles redirects to feed payload).
RBI_RSS_FEED = "https://rbi.org.in/pressreleases_rss.aspx"


class RBIRSSSourceAdapter(SourceAdapter):
    adapter_source = AdapterSource.RBI_RSS

    def fetch(self, window: timedelta) -> list[RawEvent]:
        cutoff = window_start(window)
        try:
            rss_bytes = httpx.get(RBI_RSS_FEED, timeout=35.0, follow_redirects=True).content
        except httpx.HTTPError as exc:
            raise SourceFailure("rbi rss download failed") from exc

        feed = feedparser.parse(rss_bytes)
        if getattr(feed, "bozo_exception", None) is not None and not feed.entries:
            raise SourceFailure("rbi rss parse failed")

        rows: list[RawEvent] = []
        seen: set[str] = set()
        for entry in feed.entries[:200]:
            link = entry.get("link") or ""
            title = entry.get("title") or "(RBI announcement)"
            if not link.strip():
                continue

            canon = self.canonical_url_from(link.strip())
            if canon in seen:
                continue

            summary = str(entry.summary)[:2000] if entry.get("summary") else None
            tup = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)

            dt: datetime | None = None
            if isinstance(tup, time.struct_time) and tup.tm_year >= 1900:
                dt = datetime.fromtimestamp(calendar.timegm(tup), tz=UTC)

            if dt and dt < cutoff:
                continue

            rows.append(
                RawEvent(
                    title=title.strip(),
                    canonical_url=canon,
                    published_at=dt,
                    excerpt=summary,
                )
            )
            seen.add(canon)

        return rows
