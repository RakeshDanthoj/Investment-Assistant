"""Signal monitor persistence + gate audit — P1-S11."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.db.migrate import apply_migrations
from app.models.enums import LifecycleState, SignalState
from app.services.signal_check import MarketFact
from app.services.signal_monitor_runner import run_signal_monitor


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


@pytest.mark.parametrize(
    ("fact_count", "hours_back", "expect_tier", "table_check"),
    [
        (3, 0.5, "high", "track_record"),
        (1, 0.5, "medium", "editorial_signal_queue"),
        (3, 12.0, "low", "digest_log"),
    ],
)
def test_signal_monitor_routes_and_logs_gate(
    db_connection,
    fact_count: int,
    hours_back: float,
    expect_tier: str,
    table_check: str,
) -> None:
    event_id = uuid4()
    card_id = uuid4()
    signal_id = uuid4()
    canon = f"pytest:{uuid4()}@signal.invalid"
    ref = datetime(2026, 5, 18, 10, 30, tzinfo=UTC)
    phrase = (
        "india inflation outlook remains elevated across manufacturing sectors "
        f"headline pytest signalid {signal_id}"
    )
    facts = [
        MarketFact(
            f"src{i}",
            phrase + f" wire {i}",
            ref - timedelta(hours=hours_back, minutes=i),
        )
        for i in range(fact_count)
    ]

    try:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.events (
                  id, title, category, confidence_score, lifecycle_state,
                  canonical_url, event_source, confidence_raw, confidence_effective
                )
                VALUES (%s, %s, 'macro'::event_category, 60, 'published',
                  %s, 'pytest', %s, %s)
                """,
                (
                    str(event_id),
                    "Signal monitor parent event",
                    canon,
                    {"high": 0.80, "medium": 0.60, "low": 0.40}[expect_tier],
                    {"high": 0.80, "medium": 0.60, "low": 0.40}[expect_tier],
                ),
            )
            cur.execute(
                """
                INSERT INTO public.cards (
                  id, event_id, title, insight_layer, context_layer, evidence_layer,
                  dissenting_view, framework_behind_this, prompt_version, lifecycle_state
                )
                VALUES (
                  %s, %s, 'Signal card', 'Insight [MEASURED]', 'Ctx [MEASURED]',
                  '{}'::jsonb, 'Dissent [MEASURED]', 'Fw [MEASURED]', 'pytest', %s
                )
                """,
                (str(card_id), str(event_id), LifecycleState.PUBLISHED.value),
            )
            cur.execute(
                """
                INSERT INTO public.signals (id, card_id, signal_text, state)
                VALUES (%s, %s, %s, %s)
                """,
                (str(signal_id), str(card_id), phrase, SignalState.PENDING.value),
            )
        db_connection.commit()

        summary = run_signal_monitor(
            reference_time=ref,
            skip_market_hours_check=True,
            facts_provider=lambda _rt: facts,
            emit_notifications=False,
            only_card_id=card_id,
        )
        assert summary.skipped_no_db is False
        assert summary.signals_checked >= 1

        with db_connection.cursor() as cur:
            cur.execute(
                """
                SELECT gate FROM public.confidence_gate_log
                WHERE signal_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (str(signal_id),),
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == expect_tier

            if table_check == "track_record":
                cur.execute(
                    "SELECT payload::text FROM public.track_record WHERE card_id = %s",
                    (str(card_id),),
                )
                tr = cur.fetchone()
                assert tr is not None
                assert "signal_auto_update" in tr[0]
                cur.execute(
                    "SELECT editor_override_deadline IS NOT NULL FROM public.cards WHERE id = %s",
                    (str(card_id),),
                )
                assert cur.fetchone()[0] is True
                cur.execute(
                    "SELECT state::text FROM public.signals WHERE id = %s",
                    (str(signal_id),),
                )
                assert cur.fetchone()[0] == SignalState.TRIGGERED.value
            elif table_check == "editorial_signal_queue":
                cur.execute(
                    "SELECT 1 FROM public.editorial_signal_queue WHERE signal_id = %s",
                    (str(signal_id),),
                )
                assert cur.fetchone() is not None
                cur.execute(
                    "SELECT state::text FROM public.signals WHERE id = %s",
                    (str(signal_id),),
                )
                assert cur.fetchone()[0] == SignalState.PENDING.value
            else:
                cur.execute(
                    "SELECT 1 FROM public.digest_log WHERE signal_id = %s",
                    (str(signal_id),),
                )
                assert cur.fetchone() is not None
                cur.execute(
                    "SELECT state::text FROM public.signals WHERE id = %s",
                    (str(signal_id),),
                )
                assert cur.fetchone()[0] == SignalState.PENDING.value
    finally:
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM public.digest_log WHERE signal_id = %s", (str(signal_id),))
            cur.execute("DELETE FROM public.cards WHERE id = %s", (str(card_id),))
            cur.execute("DELETE FROM public.events WHERE id = %s", (str(event_id),))
        db_connection.commit()
