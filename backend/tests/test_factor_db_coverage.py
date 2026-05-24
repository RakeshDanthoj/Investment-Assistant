"""P2-S11 — Factor DB must cover ≥120 NSE instruments × 8 factors with MMJ + source."""

import pytest

from app.db.migrate import apply_migrations
from app.db.seeds import apply_all_factor_db_seeds


@pytest.fixture(scope="module", autouse=True)
def load_full_factor_fixture(db_connection) -> None:
    apply_migrations(db_connection)
    apply_all_factor_db_seeds(db_connection)
    db_connection.commit()


def test_at_least_eight_sectors_seeded(db_connection) -> None:
    with db_connection.cursor() as cur:
        cur.execute("select count(*) from public.sectors")
        assert cur.fetchone()[0] >= 8


def test_at_least_120_instruments_with_full_factor_grid(db_connection) -> None:
    with db_connection.cursor() as cur:
        cur.execute("select count(*) from public.factors")
        factor_count = cur.fetchone()[0]
        assert factor_count == 8

        cur.execute(
            """
            select count(*) from (
              select i.id
              from public.instruments i
              join public.instrument_factor_sensitivity ifs
                on ifs.instrument_id = i.id
              where upper(i.exchange) = 'NSE'
              group by i.id
              having count(distinct ifs.factor_id) = 8
            ) fully_covered
            """
        )
        instrument_count = cur.fetchone()[0]
        assert instrument_count >= 120

        cur.execute(
            """
            select count(*) from public.instrument_factor_sensitivity
            where mmj_tag is null or btrim(source_url) = ''
            """
        )
        assert cur.fetchone()[0] == 0

        cur.execute(
            """
            select count(*) from public.instrument_factor_sensitivity
            """
        )
        total_cells = cur.fetchone()[0]
        assert total_cells >= 120 * 8
