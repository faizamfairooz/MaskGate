from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class DatabaseInterface(ABC):
    """Abstract base class for database operations."""

    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        pass

    @abstractmethod
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT, UPDATE, or DELETE query and return affected rows."""
        pass

    @abstractmethod
    def get_schemas(self) -> List[str]:
        """Get list of user-visible schemas."""
        pass

    @abstractmethod
    def get_tables(self, schema: str = "public") -> List[str]:
        """Get list of all tables in the database."""
        pass

    @abstractmethod
    def get_table_schema(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        pass

    @abstractmethod
    def get_primary_keys(self, table_name: str, schema: str = "public") -> List[str]:
        """Get primary key columns for a table."""
        pass

    @abstractmethod
    def get_foreign_keys(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """Get foreign key relationships for a table."""
        pass

    @abstractmethod
    def table_exists(self, table_name: str, schema: str = "public") -> bool:
        """Check if a table exists."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify database connectivity."""
        pass
