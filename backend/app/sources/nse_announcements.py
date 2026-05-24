"""NSE/BSE announcements adapter via public disclosures (empty on scrape failure — PRD §7.3)."""

from __future__ import annotations

import json
from datetime import timedelta
from urllib.parse import urlencode

import httpx

from app.sources.base import AdapterSource, RawEvent, SourceAdapter, SourceFailure
from app.sources.nse_datetime import parse_nse_observed_at

NSE_ORIGIN = "https://www.nseindia.com"
NSE_API = "https://www.nseindia.com/api/corporate-announcements"

_DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-GB,en-US;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124 Safari/537.36"
    ),
}


class NSEAnnouncementsSourceAdapter(SourceAdapter):
    """Best-effort NSE JSON feed — exchange hardening occasionally blocks scripted access."""

    adapter_source = AdapterSource.NSE_BSE

    def fetch(
        self,
        window: timedelta,
        *,
        period: str | None = None,
    ) -> list[RawEvent]:
        del window
        params = {"index": "equities", "period": period or "1W"}
        qs = urlencode(params)
        url = f"{NSE_API}?{qs}"

        with httpx.Client(timeout=40.0, headers=_DEFAULT_HEADERS, follow_redirects=True) as client:
            try:
                warm = client.get(NSE_ORIGIN + "/")
                warm.raise_for_status()
            except httpx.HTTPError as exc:
                raise SourceFailure("nse warmup failed") from exc

            cookies = dict(warm.cookies.items())
            try:
                response = client.get(url, cookies=cookies)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise SourceFailure("nse announcements request failed") from exc

            try:
                payload = response.json()
            except json.JSONDecodeError as exc:
                raise SourceFailure("nse announcements json invalid") from exc

        announcements = _unwrap_announcement_rows(payload)
        rows: list[RawEvent] = []
        seen: set[str] = set()

        for ann in announcements:
            issuer = (
                ann.get("sm_name")
                or ann.get("compName")
                or ann.get("symbol")
                or "NSE issuer"
            )
            line = (
                ann.get("sub")
                or ann.get("subject")
                or ann.get("desc")
                or ann.get("attchmntText")
                or "Corporate announcement"
            )
            headline = f"{issuer}: {line}"

            raw_link_text = ""
            for key in ("attchmntFile", "pdfLink", "fileLink", "attchmntText"):
                val = ann.get(key)
                if isinstance(val, str) and val.strip():
                    raw_link_text = val.strip()
                    break

            an_dt_raw = ann.get("an_dt") or ann.get("broadcast_dttm") or ""
            symbol = ann.get("symbol") or ""

            deterministic = "|".join(
                str(sym).strip()
                for sym in (symbol, str(an_dt_raw), str(line), raw_link_text)
                if sym
            )
            canon = self.canonical_url_from(f"https://nseindia.com/corp/{deterministic}")

            excerpt_bits = [str(sym) for sym in (an_dt_raw, raw_link_text) if sym][:2]
            excerpt = " · ".join(excerpt_bits)[:2000] if excerpt_bits else None

            published_at = parse_nse_observed_at(str(an_dt_raw) if an_dt_raw else None)

            if canon in seen:
                continue
            seen.add(canon)
            rows.append(
                RawEvent(
                    title=headline.strip()[:2000],
                    canonical_url=canon,
                    published_at=published_at,
                    excerpt=excerpt,
                )
            )

        return rows


def _unwrap_announcement_rows(blob: object) -> list[dict]:
    if isinstance(blob, list):
        return [row for row in blob if isinstance(row, dict)]

    if isinstance(blob, dict):
        for key in ("data", "recentList", "activeTable", "annTable"):
            body = blob.get(key)
            if isinstance(body, list):
                rows = [row for row in body if isinstance(row, dict)]
                if rows:
                    return rows

    return []
