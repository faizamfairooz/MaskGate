"""
PostgreSQL Connector for MaskGate
Handles database connection, query execution, and basic operations
"""

import psycopg2
from psycopg2 import OperationalError, sql
from typing import List, Dict, Any, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgreSQLConnector:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self, host: str = "localhost", port: int = 5432, 
                 database: str = "postgres", user: str = "postgres", 
                 password: str = ""):
        """
        Initialize database connection parameters
        
        Args:
            host: Database host address
            port: Database port (default 5432)
            database: Database name
            user: Database username
            password: Database password
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
        
    def connect(self) -> bool:
        """
        Establish connection to PostgreSQL database
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            logger.info(f"✅ Connected to PostgreSQL: {self.host}:{self.port}/{self.database}")
            return True
            
        except OperationalError as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection safely"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
                logger.info("🔌 Disconnected from PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Error disconnecting: {e}")
    
    def test_connection(self) -> bool:
        """
        Test if connection is still alive
        
        Returns:
            True if connection is active, False otherwise
        """
        try:
            self.cursor.execute("SELECT 1;")
            self.cursor.fetchone()
            return True
        except Exception:
            return False
    
    def execute_query(self, query: str, params: Tuple = None, 
                     fetch: bool = True) -> Optional[List[Tuple]]:
        """
        Execute a SQL query safely
        
        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
            fetch: Whether to fetch results (True for SELECT, False for INSERT/UPDATE/DELETE)
            
        Returns:
            Query results if fetch=True, None otherwise
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if fetch:
                results = self.cursor.fetchall()
                return results
            else:
                self.connection.commit()
                return None
                
        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            logger.error(f"   Query: {query}")
            self.connection.rollback()
            return None
    
    def get_databases(self) -> List[str]:
        """
        Get list of all databases
        
        Returns:
            List of database names
        """
        query = """
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false 
            ORDER BY datname;
        """
        results = self.execute_query(query)
        return [row[0] for row in results] if results else []
    
    def get_schemas(self) -> List[str]:
        """
        Get list of all schemas in current database
        
        Returns:
            List of schema names
        """
        query = """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name;
        """
        results = self.execute_query(query)
        return [row[0] for row in results] if results else []
    
    def get_tables(self, schema: str = "public") -> List[str]:
        """
        Get list of all tables in a schema
        
        Args:
            schema: Schema name (default 'public')
            
        Returns:
            List of table names
        """
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        results = self.execute_query(query, (schema,))
        return [row[0] for row in results] if results else []
    
    def get_columns(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """
        Get column information for a table
        
        Args:
            table_name: Name of the table
            schema: Schema name (default 'public')
            
        Returns:
            List of dictionaries with column info (name, type, nullable, etc.)
        """
        query = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s 
            AND table_name = %s
            ORDER BY ordinal_position;
        """
        results = self.execute_query(query, (schema, table_name))
        
        if not results:
            return []
        
        columns = []
        for row in results:
            columns.append({
                "column_name": row[0],
                "data_type": row[1],
                "max_length": row[2],
                "is_nullable": row[3],
                "default_value": row[4]
            })
        
        return columns
    
    def get_primary_keys(self, table_name: str, schema: str = "public") -> List[str]:
        """
        Get primary key columns for a table
        
        Args:
            table_name: Name of the table
            schema: Schema name
            
        Returns:
            List of primary key column names
        """
        query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s
            ORDER BY kcu.ordinal_position;
        """
        results = self.execute_query(query, (schema, table_name))
        return [row[0] for row in results] if results else []
    
    def get_foreign_keys(self, table_name: str, schema: str = "public") -> List[Dict[str, str]]:
        """
        Get foreign key relationships for a table
        
        Args:
            table_name: Name of the table
            schema: Schema name
            
        Returns:
            List of dictionaries with FK info
        """
        query = """
            SELECT
                kcu.column_name,
                ccu.table_schema AS referenced_schema,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s;
        """
        results = self.execute_query(query, (schema, table_name))
        
        if not results:
            return []
        
        fks = []
        for row in results:
            fks.append({
                "column": row[0],
                "referenced_schema": row[1],
                "referenced_table": row[2],
                "referenced_column": row[3]
            })
        
        return fks
    
    def get_sample_data(self, table_name: str, schema: str = "public", 
                        limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sample rows from a table
        
        Args:
            table_name: Name of the table
            schema: Schema name
            limit: Number of sample rows
            
        Returns:
            List of dictionaries with sample data
        """
        # Get column names first
        columns = self.get_columns(table_name, schema)
        column_names = [col["column_name"] for col in columns]
        
        # Build safe query with proper quoting
        query = sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
            sql.Identifier(schema),
            sql.Identifier(table_name)
        )
        
        results = self.execute_query(query, (limit,))
        
        if not results:
            return []
        
        # Convert to list of dictionaries
        samples = []
        for row in results:
            sample = {}
            for i, column_name in enumerate(column_names):
                sample[column_name] = str(row[i]) if row[i] is not None else None
            samples.append(sample)
        
        return samples
    
    def get_full_schema(self, schema: str = "public") -> Dict[str, Any]:
        """
        Get complete schema information for MaskGate
        
        Returns:
            Dictionary with complete database schema
        """
        full_schema = {
            "database": self.database,
            "schemas": [],
            "tables": {}
        }
        
        tables = self.get_tables(schema)
        
        for table in tables:
            table_info = {
                "columns": self.get_columns(table, schema),
                "primary_keys": self.get_primary_keys(table, schema),
                "foreign_keys": self.get_foreign_keys(table, schema),
                "sample_data": self.get_sample_data(table, schema)
            }
            full_schema["tables"][table] = table_info
        
        return full_schema


# ============================================================
# Quick test function
# ============================================================
def test_connector():
    """Test the PostgreSQL connector with a sample database"""
    
    # Connection parameters - update these for your setup
    db = PostgreSQLConnector(
        host="localhost",
        port=5432,
        database="testdb",
        user="postgres",
        password="secret"
    )
    
    # Connect
    if not db.connect():
        print("Cannot proceed without database connection")
        return
    
    # Test basic operations
    print("\n" + "="*50)
    print("DATABASE CONNECTION TEST")
    print("="*50)
    
    # Get databases
    databases = db.get_databases()
    print(f"\n📊 Databases found: {databases}")
    
    # Get schemas
    schemas = db.get_schemas()
    print(f"\n📁 Schemas: {schemas}")
    
    # Get tables
    tables = db.get_tables()
    print(f"\n📋 Tables in 'public': {tables}")
    
    # Get columns for each table
    for table in tables:
        print(f"\n🔍 Columns in '{table}':")
        columns = db.get_columns(table)
        for col in columns:
            pk = "🔑" if col["column_name"] in db.get_primary_keys(table) else "  "
            nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
            print(f"  {pk} {col['column_name']} ({col['data_type']}) {nullable}")
    
    # Get sample data
    if tables:
        print(f"\n📝 Sample data from '{tables[0]}':")
        samples = db.get_sample_data(tables[0])
        for sample in samples:
            print(f"  {sample}")
    
    # Test full schema export
    print("\n📦 Full schema structure:")
    full_schema = db.get_full_schema()
    print(f"  Tables: {list(full_schema['tables'].keys())}")
    
    # Clean up
    db.disconnect()
    print("\n✅ Test completed")


if __name__ == "__main__":
    test_connector()