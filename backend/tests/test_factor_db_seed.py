import pytest

from app.db.migrate import apply_migrations
from app.db.seeds import apply_banking_sector_seed


@pytest.fixture(scope="module", autouse=True)
def load_factor_fixture(db_connection) -> None:
    apply_migrations(db_connection)
    apply_banking_sector_seed(db_connection)


def test_banking_sector_has_factors_and_bank_rows(db_connection) -> None:
    with db_connection.cursor() as cur:
        cur.execute("select count(*) from public.factors")
        fc = cur.fetchone()[0]
        assert fc == 8

        cur.execute(
            """
            select count(distinct i.id)
            from public.instruments i
            join public.sectors s on s.id = i.sector_id
            where s.slug = 'banking'
              and upper(i.exchange) = 'NSE'
            """
        )
        ic = cur.fetchone()[0]
        assert ic >= 15

        cur.execute(
            """
            select count(*) from public.instrument_factor_sensitivity s
            join public.instruments i on i.id = s.instrument_id
            join public.sectors sec on sec.id = i.sector_id
            where sec.slug = 'banking'
            """
        )
        sc = cur.fetchone()[0]
        assert sc == fc * ic

        cur.execute(
            """
            select count(*) from public.instrument_factor_sensitivity
            where mmj_tag is null
               or btrim(source_url) = ''
            """
        )
        bad = cur.fetchone()[0]
        assert bad == 0


def test_every_instrument_has_eight_factors(db_connection) -> None:
    with db_connection.cursor() as cur:
        cur.execute(
            """
            select i.ticker, count(distinct f.id) as fc
            from public.instruments i
            join public.sectors sec on sec.id = i.sector_id
            left join public.instrument_factor_sensitivity s on s.instrument_id = i.id
            left join public.factors f on f.id = s.factor_id
            where sec.slug = 'banking'
            group by i.ticker
            having count(distinct f.id) <> 8
            """
        )
        gaps = cur.fetchall()
        assert gaps == []
