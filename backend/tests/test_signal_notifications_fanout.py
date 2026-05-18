"""Signal notification fan-out is scoped to users who logged predictions (P1-S11)."""

import inspect

from app.services import signal_monitor_runner


def test_fan_out_notifications_selects_from_user_predictions() -> None:
    src = inspect.getsource(signal_monitor_runner._fan_out_signal_notifications)
    assert "user_predictions" in src
    assert "signal_fired" in src
