"""Grade-on-resolve triggers notification fan-out (P2-S3)."""

import inspect

from app.jobs import grade_on_resolve


def test_grade_predictions_calls_fan_out_when_users_graded() -> None:
    src = inspect.getsource(grade_on_resolve.grade_predictions_for_card)
    assert "fan_out_on_grade" in src
    assert "graded_user_ids" in src
