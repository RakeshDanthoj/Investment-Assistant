"""P3-S0: idempotent synthetic seed (G-13)."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from app.db.migrate import apply_migrations
from app.db.synthetic_seed import seed_events


@contextmanager
def _use_db_connection(db_connection):
    @contextmanager
    def _connection_override():
        yield db_connection

    with patch("app.db.synthetic_seed.connection", _connection_override):
        with patch("app.db.connection.connection", _connection_override):
            yield


@pytest.mark.integration
def test_synthetic_seed_is_idempotent(db_connection) -> None:
    apply_migrations(db_connection)

    with _use_db_connection(db_connection):
        first = seed_events(apply_migration=False)
        second = seed_events(apply_migration=False)

    assert first["total"] == 20
    assert first["inserted"] + first["updated"] == 20
    assert second["inserted"] == 0
    assert second["updated"] == 20

    with db_connection.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.events WHERE is_synthetic = TRUE")
        total = cur.fetchone()[0]
        cur.execute(
            """
            SELECT count(*) FROM public.events
            WHERE is_synthetic = TRUE AND is_major = TRUE
            """
        )
        major = cur.fetchone()[0]

    assert total == 20
    assert major == 7
