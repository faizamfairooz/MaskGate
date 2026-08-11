import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.schema_service import SchemaService
from app.schemas.database import ColumnSchema, TableSchema, DatabaseSchema


@pytest.fixture
def schema_service():
    return SchemaService()


@pytest.mark.integration
def test_schema_service_creation(schema_service):
    assert schema_service is not None


@pytest.mark.integration
def test_get_all_tables(schema_service):
    """Test retrieving list of tables."""
    tables = schema_service.get_all_tables()
    assert isinstance(tables, list)
    # Should have sample tables from schema.sql
    expected_tables = {"customers", "orders", "employees"}
    assert expected_tables.issubset(set(tables))


@pytest.mark.integration
def test_get_full_schema(schema_service):
    """Test retrieving complete database schema."""
    schema = schema_service.get_full_schema()
    assert isinstance(schema, DatabaseSchema)
    assert len(schema.tables) > 0
    
    # Check that metadata tables are excluded
    table_names = {t.table_name for t in schema.tables}
    assert "users" not in table_names
    assert "masking_policies" not in table_names


@pytest.mark.integration
def test_get_table_schema(schema_service):
    """Test retrieving schema for a specific table."""
    table_schema = schema_service.get_table_schema("customers")
    assert isinstance(table_schema, TableSchema)
    assert table_schema.table_name == "customers"
    assert len(table_schema.columns) > 0
    
    # Check for expected columns
    column_names = {col.column_name for col in table_schema.columns}
    assert "id" in column_names
    assert "email" in column_names
    assert "first_name" in column_names


@pytest.mark.integration
def test_table_schema_with_primary_key(schema_service):
    """Test that primary key information is included."""
    table_schema = schema_service.get_table_schema("customers")
    assert "id" in table_schema.primary_keys
    
    # Check that id column is marked as primary key
    id_column = next(col for col in table_schema.columns if col.column_name == "id")
    assert id_column.is_primary_key is True


@pytest.mark.integration
def test_table_schema_with_foreign_keys(schema_service):
    """Test that foreign key information is included."""
    table_schema = schema_service.get_table_schema("orders")
    assert len(table_schema.foreign_keys) > 0
    
    # Check for user_id foreign key
    user_fk = next(
        (fk for fk in table_schema.foreign_keys if fk.column_name == "user_id"),
        None
    )
    assert user_fk is not None
    assert user_fk.foreign_table_name == "users"
    assert user_fk.foreign_column_name == "id"


@pytest.mark.integration
def test_nonexistent_table(schema_service):
    """Test error handling for nonexistent table."""
    with pytest.raises(ValueError, match="does not exist"):
        schema_service.get_table_schema("nonexistent_table")


@pytest.mark.integration
def test_column_schema_types(schema_service):
    """Test that column data types are correctly captured."""
    table_schema = schema_service.get_table_schema("customers")
    
    # Find email column
    email_col = next(col for col in table_schema.columns if col.column_name == "email")
    assert email_col.data_type == "character varying"
    assert email_col.is_nullable is False
    
    # Find phone column (nullable)
    phone_col = next(col for col in table_schema.columns if col.column_name == "phone")
    assert phone_col.is_nullable is True
