"""Unit tests per external source adapter shape (offline fixtures)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

from app.sources.newsapi import NewsAPISourceAdapter
from app.sources.nse_announcements import NSEAnnouncementsSourceAdapter
from app.sources.rbi_rss import RBIRSSSourceAdapter

MINIMAL_RSS = b"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>RBI Tests</title>
    <item>
      <title>Policy repo unchanged</title>
      <link>https://example.com/rbi/policy-001</link>
      <description>Snippet</description>
      <pubDate>Fri, 16 May 2026 08:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_rbi_adapter_parses_minimal_fixture() -> None:
    rb = RBIRSSSourceAdapter()
    fake = MagicMock()
    fake.content = MINIMAL_RSS
    with patch("httpx.get", return_value=fake):
        rows = rb.fetch(timedelta(days=365))
    assert len(rows) == 1
    assert "Policy" in rows[0].title
    assert "policy-001" in rows[0].canonical_url


def test_newsapi_adapter_normalizes_tracking_params() -> None:
    fixture = {
        "articles": [
            {
                "title": "India markets drift",
                "url": "https://news.example.com/a?utm_medium=social",
                "publishedAt": "2026-05-01T12:00:00Z",
                "description": "desc",
            }
        ]
    }
    rsp = MagicMock()
    rsp.json.return_value = fixture
    rsp.raise_for_status.return_value = None

    nr = NewsAPISourceAdapter(api_key="k")
    with (
        patch("app.sources.newsapi.reserve_news_api_call", return_value=True),
        patch("httpx.get", return_value=rsp),
    ):
        rows = nr.fetch(timedelta(days=365))
    assert rows
    assert "utm_medium" not in rows[0].canonical_url


def test_nse_adapter_reads_list_records() -> None:
    payload = [
        {
            "sm_name": "ACME BANK",
            "symbol": "ACME",
            "an_dt": "01-Jan-2024",
            "sub": "board meeting",
            "attchmntFile": "https://nse.example.com/pdf/1.pdf",
        }
    ]

    class FakeClientCtx:
        def __enter__(self) -> FakeClientCtx:
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

        def get(self, url: str, **_kwargs: object) -> MagicMock:
            warmup = MagicMock()
            warmup.raise_for_status.return_value = None
            warmup.cookies.items.return_value = []
            data = MagicMock()
            data.json.return_value = payload
            data.raise_for_status.return_value = None

            if "corporate-announcements" in url:
                return data
            return warmup

    ad = NSEAnnouncementsSourceAdapter()
    fake_ctx = FakeClientCtx()
    with patch("httpx.Client", return_value=fake_ctx):
        rows = ad.fetch(timedelta(days=365))
    assert len(rows) == 1
    assert "board meeting" in rows[0].title
