from typing import List, Dict, Any, Optional
from app.database.base import DatabaseInterface
from app.database.connection import get_database_connection, release_connection

# MaskGate application tables (excluded from developer schema browser by default)
METADATA_TABLES = frozenset({
    "users",
    "masking_policies",
    "masking_recommendations",
    "query_history",
    "schema_analysis_cache",
    "audit_logs",
})


class PostgreSQLDatabase(DatabaseInterface):
    """PostgreSQL implementation of the database interface."""

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries."""
        conn = get_database_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if cursor.description is None:
                    conn.commit()
                    return []
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                    conn.commit()
                return results
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            release_connection(conn)

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT, UPDATE, or DELETE query and return affected rows."""
        conn = get_database_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            release_connection(conn)

    def health_check(self) -> bool:
        """Verify database connectivity."""
        conn = get_database_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        finally:
            release_connection(conn)

    def get_schemas(self) -> List[str]:
        """Get list of user-visible schemas."""
        query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """
        results = self.execute_query(query)
        return [row["schema_name"] for row in results]

    def get_tables(
        self,
        schema: str = "public",
        exclude_metadata: bool = True,
    ) -> List[str]:
        """Get list of all tables in the database."""
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        results = self.execute_query(query, (schema,))
        tables = [row["table_name"] for row in results]
        if exclude_metadata:
            tables = [t for t in tables if t not in METADATA_TABLES]
        return tables

    def get_table_schema(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s
            AND table_schema = %s
            ORDER BY ordinal_position
        """
        return self.execute_query(query, (table_name, schema))

    def get_primary_keys(self, table_name: str, schema: str = "public") -> List[str]:
        """Get primary key columns for a table."""
        query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_name = %s
            AND tc.table_schema = %s
        """
        results = self.execute_query(query, (table_name, schema))
        return [row["column_name"] for row in results]

    def get_foreign_keys(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """Get foreign key relationships for a table."""
        query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
            AND tc.table_schema = %s
        """
        return self.execute_query(query, (table_name, schema))

    def table_exists(self, table_name: str, schema: str = "public") -> bool:
        """Check if a table exists."""
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = %s
                AND table_schema = %s
            )
        """
        result = self.execute_query(query, (table_name, schema))
        return result[0]["exists"] if result else False


# Global database instance
db = PostgreSQLDatabase()
