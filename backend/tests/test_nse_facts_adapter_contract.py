"""Contract tests for NSE market-fact adapters (offline fixtures) — P2-S14."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

from app.services.market_facts_adapters import fetch_nse_announcement_facts
from app.sources.nse_announcements import NSEAnnouncementsSourceAdapter
from app.sources.nse_datetime import parse_nse_observed_at
from app.sources.nse_index import NSEIndexSnapshotAdapter


def test_parse_nse_observed_at_ist_to_utc() -> None:
    parsed = parse_nse_observed_at("01-Jan-2024 15:30:00")
    assert parsed is not None
    assert parsed.tzinfo is not None


def test_nse_adapter_reads_list_records_with_published_at() -> None:
    payload = [
        {
            "sm_name": "ACME BANK",
            "symbol": "ACME",
            "an_dt": "01-Jan-2024 10:00:00",
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
    with patch("httpx.Client", return_value=FakeClientCtx()):
        rows = ad.fetch(timedelta(hours=6), period="1D")
    assert len(rows) == 1
    assert rows[0].published_at is not None


def test_fetch_nse_announcement_facts_maps_to_market_fact() -> None:
    payload = [
        {
            "sm_name": "ACME BANK",
            "symbol": "ACME",
            "an_dt": "24-May-2026 09:00:00",
            "sub": "results board meeting india manufacturing",
            "attchmntFile": "https://nse.example.com/pdf/2.pdf",
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

    with patch("httpx.Client", return_value=FakeClientCtx()):
        facts = fetch_nse_announcement_facts()
    assert len(facts) == 1
    assert facts[0].source_id.startswith("nse:")
    assert "board meeting" in facts[0].summary.lower()


def test_nse_index_adapter_fixture() -> None:
    payload = {
        "data": [
            {"index": "NIFTY 50", "last": 24150.5, "percentChange": 0.42},
            {"index": "S&P BSE SENSEX", "last": 79500.0, "percentChange": -0.10},
            {"index": "NIFTY BANK", "last": 52000.0, "percentChange": 0.1},
        ]
    }

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
            if "allIndices" in url:
                return data
            return warmup

    ad = NSEIndexSnapshotAdapter()
    with patch("httpx.Client", return_value=FakeClientCtx()):
        rows = ad.fetch(timedelta(hours=1))
    assert len(rows) == 2
    assert any("NIFTY 50" in r.title for r in rows)
    assert any("sensex" in r.title.lower() for r in rows)
