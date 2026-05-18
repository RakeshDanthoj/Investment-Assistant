"""Log learner predictions (P1-S10 bridge ahead of full P1-S12 dual-write)."""

from __future__ import annotations

from uuid import UUID

from psycopg import errors as pg_errors

from app.db.connection import connection
from app.services.card_repository import fetch_card_detail_for_review


class PredictionLogError(ValueError):
    """Business validation failure for prediction logging."""


def assert_card_exists(card_id: UUID) -> None:
    if fetch_card_detail_for_review(card_id) is None:
        raise PredictionLogError("card_not_found")


def log_prediction(*, user_id: UUID, card_id: UUID, prediction_text: str) -> None:
    text = prediction_text.strip()
    if len(text) < 8:
        raise PredictionLogError("prediction_text_too_short")
    if len(text) > 2000:
        raise PredictionLogError("prediction_text_too_long")

    assert_card_exists(card_id)

    stmt = """
    INSERT INTO public.user_predictions (user_id, card_id, prediction_text)
    VALUES (%s, %s, %s)
    """
    with connection() as conn, conn.cursor() as cur:
        try:
            cur.execute(stmt, (str(user_id), str(card_id), text))
        except pg_errors.UniqueViolation as exc:
            raise PredictionLogError("duplicate_prediction") from exc
        except pg_errors.ForeignKeyViolation as exc:
            raise PredictionLogError("user_or_card_invalid") from exc


__all__ = ["PredictionLogError", "log_prediction"]
