"""Signal-fired email fan-out scope and opt-in rules (P2-S10)."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

from app.services import email_on_signal


def test_fan_out_queries_predictions_and_saved_threads() -> None:
    src = inspect.getsource(email_on_signal._stakeholder_user_ids)
    assert "user_predictions" in src
    assert "saved_threads" in src


def test_fan_out_respects_opt_in_and_dedupes() -> None:
    src = inspect.getsource(email_on_signal.fan_out)
    assert "_is_opted_in" in src
    assert "_already_sent" in src
    assert "signal_email_log" in src


def test_high_path_triggers_email_fan_out() -> None:
    from app.services import signal_monitor_runner

    src = inspect.getsource(signal_monitor_runner._high_path)
    assert "fan_out_signal_emails" in src


def test_fan_out_skips_opted_out_user(monkeypatch) -> None:
    cur = MagicMock()
    user_id = "11111111-1111-1111-1111-111111111111"
    card_id = "22222222-2222-2222-2222-222222222222"
    signal_id = "33333333-3333-3333-3333-333333333333"

    def fake_stakeholders(_cur, *, card_id: str) -> set[str]:
        assert card_id == card_id
        return {user_id}

    def fake_opted_in(_cur, uid: str) -> bool:
        return uid != user_id

    monkeypatch.setattr(email_on_signal, "_stakeholder_user_ids", fake_stakeholders)
    monkeypatch.setattr(email_on_signal, "_is_opted_in", fake_opted_in)
    monkeypatch.setattr(email_on_signal.email_client, "send", MagicMock())

    sent = email_on_signal.fan_out(
        cur,
        card_id=card_id,
        signal_id=signal_id,
        card_title="Test card",
    )
    assert sent == 0
    email_on_signal.email_client.send.assert_not_called()


def test_fan_out_sends_to_opted_in_user(monkeypatch) -> None:
    cur = MagicMock()
    user_id = "11111111-1111-1111-1111-111111111111"
    card_id = "22222222-2222-2222-2222-222222222222"
    signal_id = "33333333-3333-3333-3333-333333333333"

    monkeypatch.setattr(
        email_on_signal,
        "_stakeholder_user_ids",
        lambda _cur, *, card_id: {user_id},
    )
    monkeypatch.setattr(email_on_signal, "_is_opted_in", lambda _cur, _uid: True)
    monkeypatch.setattr(email_on_signal, "_already_sent", lambda _cur, **_: False)
    monkeypatch.setattr(email_on_signal, "_lookup_email", lambda _cur, _uid: "user@finnwise.test")
    monkeypatch.setattr(
        email_on_signal,
        "_create_unsubscribe_token",
        lambda _cur, _uid: "token-abc",
    )
    monkeypatch.setattr(email_on_signal.email_client, "send", lambda **_: True)

    sent = email_on_signal.fan_out(
        cur,
        card_id=card_id,
        signal_id=signal_id,
        card_title="Aviation margins",
    )
    assert sent == 1
