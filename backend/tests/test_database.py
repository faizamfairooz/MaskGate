import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def db_connection():
    from app.database.connection import close_all_connections, initialize_connection_pool
    from app.database.postgresql import db

    initialize_connection_pool()
    yield db
    close_all_connections()


def test_health_check(db_connection):
    assert db_connection.health_check() is True


def test_get_tables(db_connection):
    tables = db_connection.get_tables(exclude_metadata=True)
    assert isinstance(tables, list)


def test_table_exists(db_connection):
    exists = db_connection.table_exists("customers")
    assert isinstance(exists, bool)
