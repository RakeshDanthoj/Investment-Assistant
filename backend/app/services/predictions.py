"""User prediction logging with append-only track_record dual-write (P1-S12)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from psycopg import errors as pg_errors
from psycopg.rows import dict_row

from app.db.connection import connection
from app.services.card_repository import fetch_card_detail_for_review


class PredictionError(ValueError):
    """Business validation failure for prediction logging."""


class DuplicatePredictionError(PredictionError):
    def __init__(self, prediction_text: str) -> None:
        self.prediction_text = prediction_text
        super().__init__("duplicate_prediction")


@dataclass(frozen=True)
class UserPredictionRow:
    card_id: UUID
    prediction_text: str
    logged_at: datetime


def assert_card_exists(card_id: UUID) -> None:
    if fetch_card_detail_for_review(card_id) is None:
        raise PredictionError("card_not_found")


def fetch_existing_prediction(*, user_id: UUID, card_id: UUID) -> str | None:
    stmt = """
    SELECT prediction_text
    FROM public.user_predictions
    WHERE user_id = %s::uuid AND card_id = %s::uuid
    """
    with connection() as conn, conn.cursor() as cur:
        cur.execute(stmt, (str(user_id), str(card_id)))
        row = cur.fetchone()
    if row is None:
        return None
    return str(row[0])


def log(*, user_id: UUID, card_id: UUID, prediction_text: str) -> None:
    text = prediction_text.strip()
    if len(text) < 8:
        raise PredictionError("prediction_text_too_short")
    if len(text) > 2000:
        raise PredictionError("prediction_text_too_long")

    assert_card_exists(card_id)

    track_payload = {
        "kind": "user_prediction",
        "user_id": str(user_id),
        "prediction_text": text,
        "source": "prediction_logger",
    }

    with connection() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO public.user_predictions (user_id, card_id, prediction_text)
                VALUES (%s::uuid, %s::uuid, %s)
                """,
                (str(user_id), str(card_id), text),
            )
            cur.execute(
                """
                INSERT INTO public.track_record (card_id, payload)
                VALUES (%s::uuid, %s::jsonb)
                """,
                (str(card_id), json.dumps(track_payload)),
            )
        except pg_errors.ForeignKeyViolation as exc:
            raise PredictionError("user_or_card_invalid") from exc
        except pg_errors.UniqueViolation as exc:
            existing = fetch_existing_prediction(user_id=user_id, card_id=card_id)
            if existing is not None:
                raise DuplicatePredictionError(existing) from exc
            raise PredictionError("duplicate_prediction") from exc
        conn.commit()


def list_for_user(user_id: UUID, *, limit: int = 100) -> list[UserPredictionRow]:
    lim = max(1, min(limit, 200))
    stmt = """
    SELECT card_id, prediction_text, logged_at
    FROM public.user_predictions
    WHERE user_id = %s::uuid
    ORDER BY logged_at DESC
    LIMIT %s
    """
    rows: list[UserPredictionRow] = []
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(user_id), lim))
        for row in cur.fetchall():
            ts = row["logged_at"]
            if isinstance(ts, datetime):
                ts_eff = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
            else:
                continue
            rows.append(
                UserPredictionRow(
                    card_id=UUID(str(row["card_id"])),
                    prediction_text=str(row["prediction_text"]),
                    logged_at=ts_eff,
                )
            )
    return rows


__all__ = [
    "DuplicatePredictionError",
    "PredictionError",
    "UserPredictionRow",
    "assert_card_exists",
    "fetch_existing_prediction",
    "list_for_user",
    "log",
]
