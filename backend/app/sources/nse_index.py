"""NSE benchmark index snapshot lines for signal-monitor corroboration (P2-S14)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import httpx

from app.sources.base import AdapterSource, RawEvent, SourceAdapter, SourceFailure

NSE_ORIGIN = "https://www.nseindia.com"
NSE_INDEX_API = "https://www.nseindia.com/api/allIndices"

_DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-GB,en-US;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124 Safari/537.36"
    ),
}


class NSEIndexSnapshotAdapter(SourceAdapter):
    """Nifty 50 / Sensex level lines — best-effort; empty on scrape failure."""

    adapter_source = AdapterSource.NSE_BSE

    def fetch(self, window: timedelta) -> list[RawEvent]:
        del window
        with httpx.Client(timeout=25.0, headers=_DEFAULT_HEADERS, follow_redirects=True) as client:
            try:
                warm = client.get(NSE_ORIGIN + "/")
                warm.raise_for_status()
            except httpx.HTTPError as exc:
                raise SourceFailure("nse index warmup failed") from exc

            cookies = dict(warm.cookies.items())
            try:
                response = client.get(NSE_INDEX_API, cookies=cookies)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise SourceFailure("nse index request failed") from exc

            try:
                payload = response.json()
            except json.JSONDecodeError as exc:
                raise SourceFailure("nse index json invalid") from exc

        rows = _unwrap_index_rows(payload)
        observed = datetime.now(tz=UTC)
        out: list[RawEvent] = []
        seen: set[str] = set()

        for row in rows:
            label = str(
                row.get("index")
                or row.get("indexName")
                or row.get("indexSymbol")
                or ""
            ).strip()
            if not label:
                continue
            norm = label.lower()
            if "nifty 50" not in norm and "sensex" not in norm:
                continue

            last = row.get("last") or row.get("lastPrice") or row.get("previousClose")
            pct = row.get("percentChange") or row.get("pChange") or row.get("variation")
            try:
                last_f = float(last) if last is not None else None
            except (TypeError, ValueError):
                last_f = None
            try:
                pct_f = float(pct) if pct is not None else None
            except (TypeError, ValueError):
                pct_f = None

            parts = [label]
            if last_f is not None:
                parts.append(f"level {last_f:,.2f}")
            if pct_f is not None:
                sign = "+" if pct_f >= 0 else ""
                parts.append(f"({sign}{pct_f:.2f}% session move)")
            title = " — ".join(parts)

            slug = norm.replace(" ", "-").replace("&", "and")[:40]
            canon = self.canonical_url_from(f"https://nseindia.com/index/{slug}")
            if canon in seen:
                continue
            seen.add(canon)
            out.append(
                RawEvent(
                    title=title[:2000],
                    canonical_url=canon,
                    published_at=observed,
                    excerpt=None,
                )
            )

        return out


def _unwrap_index_rows(blob: object) -> list[dict]:
    if isinstance(blob, list):
        return [row for row in blob if isinstance(row, dict)]
    if isinstance(blob, dict):
        for key in ("data", "indices", "indexList"):
            body = blob.get(key)
            if isinstance(body, list):
                return [row for row in body if isinstance(row, dict)]
    return []
