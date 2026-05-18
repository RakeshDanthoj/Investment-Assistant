"""NSE/BSE cash-session window for signal monitor (P1-S11)."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.services.signal_monitor_runner import ist_market_session_open

IST = ZoneInfo("Asia/Kolkata")


def _ist(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(IST)


def test_weekend_closed() -> None:
    # Saturday 2026-05-16 10:00 IST
    ref = datetime(2026, 5, 16, 4, 30, tzinfo=UTC)
    assert _ist(ref).weekday() == 5
    assert ist_market_session_open(ref) is False


def test_monday_before_open_closed() -> None:
    ref = datetime(2026, 5, 18, 3, 44, tzinfo=UTC)  # 09:14 IST
    assert _ist(ref).hour == 9 and _ist(ref).minute == 14
    assert ist_market_session_open(ref) is False


def test_monday_open_inclusive_start() -> None:
    ref = datetime(2026, 5, 18, 3, 45, tzinfo=UTC)  # 09:15 IST
    assert ist_market_session_open(ref) is True


def test_monday_open_mid_session() -> None:
    ref = datetime(2026, 5, 18, 8, 0, tzinfo=UTC)  # 13:30 IST
    assert ist_market_session_open(ref) is True


def test_monday_close_inclusive_end() -> None:
    ref = datetime(2026, 5, 18, 10, 0, tzinfo=UTC)  # 15:30 IST
    assert ist_market_session_open(ref) is True


def test_monday_after_close() -> None:
    ref = datetime(2026, 5, 18, 10, 1, tzinfo=UTC)  # 15:31 IST
    assert ist_market_session_open(ref) is False
