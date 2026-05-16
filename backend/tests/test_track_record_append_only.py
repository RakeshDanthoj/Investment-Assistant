from uuid import uuid4

import psycopg
import pytest

from app.db.migrate import apply_migrations


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection) -> None:
    apply_migrations(db_connection)


def _assert_mutation_denied(cur, sql: str, params: tuple) -> None:
    cur.execute("SAVEPOINT mutation_attempt")
    with pytest.raises(psycopg.Error) as exc_info:
        cur.execute(sql, params)
    assert exc_info.value.sqlstate in {"42501", "P0001"}
    cur.execute("ROLLBACK TO SAVEPOINT mutation_attempt")


def test_track_record_update_is_denied(db_connection) -> None:
    card_id = uuid4()
    row_id = uuid4()

    with db_connection.transaction():
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.track_record (id, card_id, payload)
                VALUES (%s, %s, %s::jsonb)
                """,
                (row_id, card_id, '{"source": "pytest"}'),
            )
            _assert_mutation_denied(
                cur,
                """
                UPDATE public.track_record
                SET payload = '{"tampered": true}'::jsonb
                WHERE id = %s
                """,
                (row_id,),
            )


def test_track_record_delete_is_denied(db_connection) -> None:
    card_id = uuid4()
    row_id = uuid4()

    with db_connection.transaction():
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.track_record (id, card_id, payload)
                VALUES (%s, %s, %s::jsonb)
                """,
                (row_id, card_id, '{"source": "pytest"}'),
            )
            _assert_mutation_denied(
                cur,
                "DELETE FROM public.track_record WHERE id = %s",
                (row_id,),
            )
