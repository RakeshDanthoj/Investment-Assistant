"""NewsAPI factor scheduler — cap, rotation, poll status (P3-S1d)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.newsapi_config import (
    FactorKeywordSet,
    NewsApiSchedulerConfig,
    clear_newsapi_config_cache,
)
from app.services.newsapi_scheduler import pick_next_factor_slug, resolve_next_factor
from app.sources.newsapi import NewsAPISourceAdapter, _articles_from_blob


@pytest.fixture(autouse=True)
def _clear_config_cache() -> None:
    clear_newsapi_config_cache()
    yield
    clear_newsapi_config_cache()


def _test_config() -> NewsApiSchedulerConfig:
    factors = tuple(
        FactorKeywordSet(slug=slug, daily_calls=budget, keywords=(slug.replace("_", " "),))
        for slug, budget in (
            ("crude_oil", 2),
            ("dollar_rupee", 1),
            ("domestic_interest_rates", 1),
            ("global_risk_sentiment", 1),
            ("monsoon_index", 1),
            ("government_capex", 1),
            ("gst_collections_trend", 1),
            ("sector_regulatory_environment", 1),
        )
    )
    return NewsApiSchedulerConfig(mode="round_robin", max_daily_calls=9, factors=factors)


def test_config_yaml_budgets_sum_to_100() -> None:
    from app.services.newsapi_config import load_newsapi_config

    cfg = load_newsapi_config()
    assert cfg.max_daily_calls == 100
    assert sum(cfg.daily_budgets.values()) == 100
    assert len(cfg.factor_order) == 8


def test_pick_next_factor_rotates_after_last_polled() -> None:
    order = ("a", "b", "c")
    budgets = {"a": 5, "b": 5, "c": 5}
    assert pick_next_factor_slug(
        factor_order=order,
        last_polled_slug=None,
        counts_today={},
        daily_budgets=budgets,
    ) == "a"
    assert pick_next_factor_slug(
        factor_order=order,
        last_polled_slug="a",
        counts_today={},
        daily_budgets=budgets,
    ) == "b"
    assert pick_next_factor_slug(
        factor_order=order,
        last_polled_slug="c",
        counts_today={},
        daily_budgets=budgets,
    ) == "a"


def test_pick_next_factor_skips_exhausted_budget() -> None:
    order = ("a", "b", "c")
    budgets = {"a": 1, "b": 5, "c": 5}
    assert pick_next_factor_slug(
        factor_order=order,
        last_polled_slug=None,
        counts_today={"a": 1},
        daily_budgets=budgets,
    ) == "b"


def test_resolve_next_respects_per_factor_cap() -> None:
    cfg = _test_config()
    counts = {slug: cfg.daily_budgets[slug] for slug in cfg.factor_order}
    assert (
        resolve_next_factor(last_polled_slug="crude_oil", counts_today=counts, config=cfg)
        is None
    )


def test_classify_empty_vs_ok_vs_error() -> None:
    from app.sources.base import window_start

    adapter = NewsAPISourceAdapter(api_key="key")
    empty_blob = {"articles": []}
    assert not _articles_from_blob(
        empty_blob,
        cutoff=window_start(timedelta(days=365)),
        canonicalize=adapter.canonical_url_from,
    )

    # direct status via mocked HTTP
    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.json.return_value = {
        "articles": [
            {
                "title": "RBI holds repo",
                "url": "https://news.example.com/rbi",
                "publishedAt": "2026-05-30T12:00:00Z",
                "description": "x",
            }
        ]
    }

    with patch("httpx.get", return_value=ok_resp):
        status, rows, fallback = adapter._poll_newsapi_or_fallback(
            timedelta(hours=4),
            query='"RBI rate"',
        )
    assert status == "ok"
    assert len(rows) == 1
    assert fallback is False

    err_resp = MagicMock()
    err_resp.status_code = 503
    with patch("httpx.get", return_value=err_resp):
        status, rows, fallback = adapter._poll_newsapi_or_fallback(
            timedelta(hours=4),
            query="India",
        )
    assert status == "error"
    assert rows == []
    assert fallback is False

    rate_resp = MagicMock()
    rate_resp.status_code = 429
    with (
        patch("httpx.get", return_value=rate_resp),
        patch(
            "app.sources.newsapi.fetch_rss_market_headlines",
            return_value=[],
        ),
    ):
        status, rows, fallback = adapter._poll_newsapi_or_fallback(
            timedelta(hours=4),
            query="India",
        )
    assert status == "empty"
    assert fallback is True


def test_adapter_fetch_logs_poll_and_respects_budget() -> None:
    fixture = {
        "articles": [
            {
                "title": "India markets",
                "url": "https://news.example.com/a",
                "publishedAt": "2026-05-30T12:00:00Z",
                "description": "d",
            }
        ]
    }
    rsp = MagicMock()
    rsp.status_code = 200
    rsp.json.return_value = fixture

    nr = NewsAPISourceAdapter(api_key="k")
    with (
        patch("app.sources.newsapi.load_newsapi_config", return_value=_test_config()),
        patch("app.sources.newsapi.last_polled_factor_slug", return_value=None),
        patch("app.sources.newsapi.factor_poll_counts_today", return_value={}),
        patch("app.sources.newsapi.reserve_news_api_call", return_value=True),
        patch("app.sources.newsapi.record_factor_poll") as log_poll,
        patch("httpx.get", return_value=rsp),
    ):
        rows = nr.fetch(timedelta(hours=4))

    assert rows
    assert nr.last_poll is not None
    assert nr.last_poll.poll_status == "ok"
    assert nr.last_poll.factor_slug == "crude_oil"
    log_poll.assert_called_once()
    assert log_poll.call_args.kwargs["status"] == "ok"
    assert log_poll.call_args.kwargs["article_count"] == 1


def test_adapter_skips_when_global_budget_exhausted() -> None:
    nr = NewsAPISourceAdapter(api_key="k")
    with (
        patch("app.sources.newsapi.load_newsapi_config", return_value=_test_config()),
        patch("app.sources.newsapi.last_polled_factor_slug", return_value=None),
        patch("app.sources.newsapi.factor_poll_counts_today", return_value={}),
        patch("app.sources.newsapi.reserve_news_api_call", return_value=False),
        patch("app.sources.newsapi.record_factor_poll") as log_poll,
    ):
        rows = nr.fetch(timedelta(hours=4))
    assert rows == []
    log_poll.assert_not_called()


def test_full_rotation_eight_ticks_without_exceeding_factor_budgets() -> None:
    cfg = _test_config()
    counts: dict[str, int] = {}
    last: str | None = None
    ticks = 0
    while ticks < 20:
        slug = resolve_next_factor(last_polled_slug=last, counts_today=counts, config=cfg)
        if slug is None:
            break
        counts[slug] = counts.get(slug, 0) + 1
        last = slug
        ticks += 1
    assert ticks == 9
    for factor_slug, budget in cfg.daily_budgets.items():
        assert counts.get(factor_slug, 0) <= budget
