import pytest

from app.core.settings import get_settings
from app.db.connection import close_db_pool


@pytest.fixture(autouse=True)
def _reset_settings_and_db_pool():
    """Prevent cross-test pollution from cached settings or a stale connection pool."""
    get_settings.cache_clear()
    close_db_pool()
    yield
    get_settings.cache_clear()
    close_db_pool()


@pytest.fixture(scope="session")
def database_url() -> str:
    url = get_settings().supabase_db_url
    if not url:
        pytest.skip("SUPABASE_DB_URL not set in .env.local — skipping DB integration tests")
    return url


@pytest.fixture(scope="session")
def db_connection(database_url: str):
    import psycopg

    with psycopg.connect(database_url) as conn:
        yield conn
