import psycopg2
from psycopg2 import pool
from app.config.settings import settings

# Connection pool
connection_pool = None


def initialize_connection_pool():
    """Initialize the database connection pool."""
    global connection_pool
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )


def get_database_connection():
    """Get a connection from the pool."""
    global connection_pool
    if connection_pool is None:
        initialize_connection_pool()
    return connection_pool.getconn()


def release_connection(connection):
    """Release a connection back to the pool."""
    global connection_pool
    if connection_pool:
        connection_pool.putconn(connection)


def close_all_connections():
    """Close all connections in the pool."""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        connection_pool = None
