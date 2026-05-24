from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app.services.card_pipeline import draft_card_from_event

EVENT_ID = uuid4()
CARD_ID = uuid4()


def _matrix() -> dict:
    return {
        "sector": {"slug": "banking", "name": "Banking"},
        "factors": [],
        "instruments": [],
        "sensitivities": {
            "HDFCBANK": {
                "crude_oil": {
                    "sensitivity": -4,
                    "mmj_tag": "MEASURED",
                    "source_url": "https://example.com/src",
                    "retrieved_at": "2025-01-01T00:00:00+00:00",
                    "freshness": "green",
                }
            }
        },
    }


def _fake_llm_calls():
    syn = {
        "title": "Test headline",
        "insight_layer": (
            "HDFCBANK shows crude sensitivity near -4 on the seeded matrix [MEASURED]."
        ),
        "context_layer": (
            "That -4 reading is what we surface from the banking slice today [MEASURED]."
        ),
        "instrument_assessments": [
            {
                "instrument_id": "HDFCBANK",
                "signal_type": "watch",
                "reasoning": (
                    "The published -4 score keeps positioning qualitative for now [MEASURED]."
                ),
                "entry_conditions": [],
                "exit_conditions": [],
            }
        ],
        "signals": [{"signal_text": "Watch crude pass-through headlines on large private banks."}],
    }
    dis = {
        "dissenting_view": (
            "The counter-story is transmission lag: funding costs can move on confidence "
            "long before crude pass-through shows up in reported NIMs, because hedging "
            "and stock liquidity buffers delay the recognizable P&L signal in several prior "
            "cycles where markets repriced banks ahead of fundamentals [JUDGED]."
        )
    }
    fw = {
        "pattern_name": "Macro factor matrix priors",
        "framework_behind_this": (
            "Start from observable factor loadings, then narrate transmission with explicit "
            "lags rather than assuming instant pass-through [JUDGED]."
        ),
    }
    usage = {"input_tokens": 100, "output_tokens": 200}
    return [(syn, usage), (dis, usage), (fw, usage)]


class _SeqLlm:
    def __init__(self) -> None:
        self._calls = iter(_fake_llm_calls())

    def complete_json(self, **kwargs):
        return next(self._calls)


@patch("app.services.card_pipeline.insert_draft_card_bundle", return_value=CARD_ID)
@patch("app.services.card_pipeline.consume_slot_or_raise")
@patch("app.services.card_pipeline.check_monthly_budget_or_raise")
@patch("app.services.card_pipeline.fetch_matrix_rows")
@patch("app.services.card_pipeline.fetch_event_row")
def test_draft_card_pipeline_mocked_llm(
    mock_event, mock_matrix, mock_budget, mock_consume, mock_insert
):
    mock_event.return_value = {
        "id": str(EVENT_ID),
        "title": "RBI guidance tweak",
        "category": "rbi_policy",
        "confidence_score": 72,
        "canonical_url": "https://example.com/rbi",
        "event_source": "rbi_rss",
    }
    mock_matrix.return_value = _matrix()
    out = draft_card_from_event(EVENT_ID, llm=_SeqLlm())
    assert out == CARD_ID
    mock_budget.assert_called_once()
    mock_insert.assert_called_once()
    kw = mock_insert.call_args.kwargs
    assert kw["prompt_version"] == "synthesis.v1|dissent.v1|framework.v1"
    assert kw["dissenting_view"]
    assert kw["framework_behind_this"].startswith("**Macro factor matrix priors**")
    assert kw["llm_input_tokens"] == 300
    assert kw["llm_output_tokens"] == 600


MIGRATION = Path(__file__).resolve().parents[1] / "db" / "migrations" / "0008_cards_llm_budget.sql"


def test_cards_migration_has_budget_function() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "create table if not exists public.cards" in sql
    assert "try_consume_llm_card_slot" in sql
    assert "llm_card_daily_usage" in sql
