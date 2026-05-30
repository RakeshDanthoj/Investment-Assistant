"""Market fact freshness tristate + critical fact gate (P3-S1f / G-06)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.services.card_pipeline import draft_card_from_event
from app.services.critical_facts_config import (
    CriticalFactDefinition,
    CriticalFactsConfig,
    StalenessThresholds,
    clear_critical_facts_config_cache,
)
from app.services.market_facts_adapters import (
    CriticalFactsHoldError,
    QuoteObservation,
    assert_critical_facts_available,
    build_quoted_market_facts,
    classify_freshness,
    evaluate_critical_facts_gate,
    resolve_quote_fact,
)

REF = datetime(2026, 5, 31, 12, 0, tzinfo=UTC)


def _test_config() -> CriticalFactsConfig:
    return CriticalFactsConfig(
        staleness=StalenessThresholds(fresh_max_hours=24, stale_max_hours=72),
        facts=(
            CriticalFactDefinition(
                fact_id="inr_usd",
                label="INR/USD",
                critical=True,
                chain=("yfinance", "open_exchange_rates", "rbi_ref"),
                yfinance_symbol="USDINR=X",
            ),
            CriticalFactDefinition(
                fact_id="nifty_50",
                label="Nifty 50",
                critical=True,
                chain=("yfinance", "nse_index"),
                yfinance_symbol="^NSEI",
            ),
        ),
    )


def _chain_map(observations: dict[str, QuoteObservation | None]) -> dict:
    def _yfinance(defn, _ref, _settings):
        return observations.get(defn.fact_id)

    def _open_exchange(defn, _ref, _settings):
        return observations.get(defn.fact_id)

    return {
        "yfinance": _yfinance,
        "open_exchange_rates": _open_exchange,
        "rbi_ref": lambda *_: None,
        "nse_index": lambda *_: None,
    }


def test_classify_freshness_tristate() -> None:
    assert (
        classify_freshness(
            has_value=True,
            observed_at=REF - timedelta(hours=2),
            reference_time=REF,
            fresh_max_hours=24,
            stale_max_hours=72,
        )
        == "fresh"
    )
    assert (
        classify_freshness(
            has_value=True,
            observed_at=REF - timedelta(hours=48),
            reference_time=REF,
            fresh_max_hours=24,
            stale_max_hours=72,
        )
        == "stale"
    )
    assert (
        classify_freshness(
            has_value=False,
            observed_at=None,
            reference_time=REF,
            fresh_max_hours=24,
            stale_max_hours=72,
        )
        == "unavailable"
    )


def test_resolve_quote_fact_uses_fallback_chain() -> None:
    cfg = _test_config()
    inr = cfg.fact_by_id("inr_usd")
    assert inr is not None
    stale_obs = QuoteObservation("84.10", REF - timedelta(hours=30), "open_exchange_rates")

    def _chain(step: str):
        if step == "yfinance":
            return lambda *_: None
        if step == "open_exchange_rates":
            return lambda *_: stale_obs
        return lambda *_: None

    fetchers = {name: _chain(name) for name in ("yfinance", "open_exchange_rates", "rbi_ref")}
    fact = resolve_quote_fact(
        inr,
        reference_time=REF,
        config=cfg,
        chain_fetchers=fetchers,
    )
    assert fact.display_value == "84.10"
    assert fact.freshness_status == "stale"
    assert fact.source == "open_exchange_rates"


def test_unavailable_critical_fact_blocks_gate() -> None:
    cfg = _test_config()
    gate = evaluate_critical_facts_gate(
        reference_time=REF,
        config=cfg,
        chain_fetchers=_chain_map({"inr_usd": None, "nifty_50": None}),
    )
    assert gate.blocked
    assert set(gate.unavailable_critical) == {"inr_usd", "nifty_50"}


def test_stale_critical_fact_allows_gate_with_flag() -> None:
    cfg = _test_config()
    gate = evaluate_critical_facts_gate(
        reference_time=REF,
        config=cfg,
        chain_fetchers=_chain_map(
            {
                "inr_usd": QuoteObservation("84.00", REF - timedelta(hours=1), "yfinance"),
                "nifty_50": QuoteObservation("22,450.00", REF - timedelta(hours=40), "yfinance"),
            }
        ),
    )
    assert not gate.blocked
    assert gate.has_stale_critical
    assert gate.unavailable_critical == ()


def test_assert_critical_facts_available_raises() -> None:
    cfg = _test_config()
    with pytest.raises(CriticalFactsHoldError) as exc:
        assert_critical_facts_available(
            reference_time=REF,
            config=cfg,
            chain_fetchers=_chain_map({"inr_usd": None, "nifty_50": None}),
        )
    assert "inr_usd" in exc.value.unavailable_fact_ids


def test_critical_facts_config_loads_five_facts() -> None:
    clear_critical_facts_config_cache()
    from app.services.critical_facts_config import load_critical_facts_config

    cfg = load_critical_facts_config()
    assert len(cfg.facts) == 5
    assert cfg.critical_fact_ids == (
        "inr_usd",
        "repo_rate",
        "nifty_50",
        "india_vix",
        "fii_net",
    )


@patch("app.services.card_pipeline.insert_draft_card_bundle")
@patch("app.services.card_pipeline.consume_slot_or_raise")
@patch("app.services.card_pipeline.check_monthly_budget_or_raise")
@patch("app.services.card_pipeline.fetch_matrix_rows")
@patch("app.services.card_pipeline.fetch_event_row")
@patch("app.services.card_pipeline.assert_critical_facts_available")
def test_draft_card_held_when_critical_facts_unavailable(
    mock_gate,
    mock_event,
    mock_matrix,
    mock_budget,
    mock_consume,
    mock_insert,
) -> None:
    mock_gate.side_effect = CriticalFactsHoldError(["inr_usd"])
    mock_event.return_value = {
        "id": str(uuid4()),
        "title": "RBI guidance tweak",
        "category": "rbi_policy",
        "confidence_score": 72,
        "canonical_url": "https://example.com/rbi",
        "event_source": "rbi_rss",
    }
    mock_matrix.return_value = {"sector": {}, "factors": [], "instruments": [], "sensitivities": {}}

    with pytest.raises(CriticalFactsHoldError):
        draft_card_from_event(uuid4())

    mock_insert.assert_not_called()
    mock_consume.assert_not_called()


@patch("app.services.card_pipeline.insert_draft_card_bundle")
@patch("app.services.card_pipeline.consume_slot_or_raise")
@patch("app.services.card_pipeline.check_monthly_budget_or_raise")
@patch("app.services.card_pipeline.fetch_matrix_rows")
@patch("app.services.card_pipeline.fetch_event_row")
@patch("app.services.card_pipeline.assert_critical_facts_available")
def test_draft_card_proceeds_when_only_stale_critical_facts(
    mock_gate,
    mock_event,
    mock_matrix,
    mock_budget,
    mock_consume,
    mock_insert,
) -> None:
    from app.services.market_facts_adapters import CriticalFactsGateResult, MarketQuoteFact

    mock_gate.return_value = CriticalFactsGateResult(
        facts=(
            MarketQuoteFact(
                fact_id="inr_usd",
                label="INR/USD",
                display_value="84.00",
                observed_at=REF - timedelta(hours=40),
                source="yfinance",
                freshness_status="stale",
            ),
        ),
        unavailable_critical=(),
        has_stale_critical=True,
    )
    mock_event.return_value = {
        "id": str(uuid4()),
        "title": "RBI guidance tweak",
        "category": "rbi_policy",
        "confidence_score": 72,
        "canonical_url": "https://example.com/rbi",
        "event_source": "rbi_rss",
    }
    mock_matrix.return_value = {"sector": {}, "factors": [], "instruments": [], "sensitivities": {}}

    with patch("app.services.card_pipeline.LlmClient") as mock_llm_cls:
        mock_llm_cls.return_value.complete_json.side_effect = RuntimeError("stop early")
        with pytest.raises(RuntimeError, match="stop early"):
            draft_card_from_event(uuid4())

    mock_consume.assert_called_once()


def test_build_quoted_market_facts_returns_all_configured_rows() -> None:
    cfg = _test_config()
    rows = build_quoted_market_facts(
        reference_time=REF,
        config=cfg,
        chain_fetchers=_chain_map(
            {
                "inr_usd": QuoteObservation("84.00", REF - timedelta(hours=1), "yfinance"),
                "nifty_50": QuoteObservation("22,450", REF - timedelta(hours=1), "yfinance"),
            }
        ),
    )
    assert len(rows) == 2
    assert all(row.freshness_status == "fresh" for row in rows)
