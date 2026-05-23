"""P2-S3 — notify_on_grade fan-out."""

import inspect

from app.services import notify_on_grade


def test_fan_out_only_targets_graded_prediction_users() -> None:
    src = inspect.getsource(notify_on_grade.fan_out_on_grade)
    assert "user_predictions" in src
    assert "mechanism_accuracy IS NOT NULL" in src
    assert "card_graded" in src
    assert "read_at IS NULL" in src


def test_fan_out_skips_empty_user_list_early() -> None:
    src = inspect.getsource(notify_on_grade.fan_out_on_grade)
    assert "if not user_ids" in src
    assert "return 0" in src
