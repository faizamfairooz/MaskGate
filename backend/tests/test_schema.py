import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.schema_service import SchemaService
from app.schemas.database import ColumnSchema, TableSchema, DatabaseSchema


from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def schema_service():
    return SchemaService()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.integration
def test_schema_service_creation(schema_service):
    assert schema_service is not None


@pytest.mark.integration
def test_get_schemas(schema_service):
    """Test retrieving list of schemas."""
    schemas = schema_service.get_schemas()
    assert isinstance(schemas, list)
    assert "public" in schemas


@pytest.mark.integration
def test_get_all_tables(schema_service):
    """Test retrieving list of tables."""
    tables = schema_service.get_all_tables()
    assert isinstance(tables, list)
    # Should have sample tables from schema.sql
    expected_tables = {"patients", "medical_records", "appointments"}
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
    table_schema = schema_service.get_table_schema("patients")
    assert isinstance(table_schema, TableSchema)
    assert table_schema.table_name == "patients"
    assert len(table_schema.columns) > 0
    
    # Check for expected columns
    column_names = {col.column_name for col in table_schema.columns}
    assert "patient_id" in column_names
    assert "email" in column_names
    assert "full_name" in column_names


@pytest.mark.integration
def test_table_schema_with_primary_key(schema_service):
    """Test that primary key information is included."""
    table_schema = schema_service.get_table_schema("patients")
    assert "patient_id" in table_schema.primary_keys
    
    # Check that patient_id column is marked as primary key
    id_column = next(col for col in table_schema.columns if col.column_name == "patient_id")
    assert id_column.is_primary_key is True


@pytest.mark.integration
def test_table_schema_with_foreign_keys(schema_service):
    """Test that foreign key information is included."""
    table_schema = schema_service.get_table_schema("medical_records")
    assert len(table_schema.foreign_keys) > 0
    
    # Check for patient_id foreign key
    patient_fk = next(
        (fk for fk in table_schema.foreign_keys if fk.column_name == "patient_id"),
        None
    )
    assert patient_fk is not None
    assert patient_fk.foreign_table_name == "patients"
    assert patient_fk.foreign_column_name == "patient_id"


@pytest.mark.integration
def test_nonexistent_table(schema_service):
    """Test error handling for nonexistent table."""
    with pytest.raises(ValueError, match="does not exist"):
        schema_service.get_table_schema("nonexistent_table")


@pytest.mark.integration
def test_column_schema_types(schema_service):
    """Test that column data types are correctly captured."""
    table_schema = schema_service.get_table_schema("patients")
    
    # Find email column
    email_col = next(col for col in table_schema.columns if col.column_name == "email")
    assert email_col.data_type == "character varying"
    assert email_col.is_nullable is True
    
    # Find full_name column (not nullable)
    name_col = next(col for col in table_schema.columns if col.column_name == "full_name")
    assert name_col.is_nullable is False


@pytest.mark.integration
def test_api_get_schemas(client):
    """Test GET /api/v1/schema/schemas endpoint."""
    response = client.get("/api/v1/schema/schemas")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "public" in data


@pytest.mark.integration
def test_api_get_tables(client):
    """Test GET /api/v1/schema/tables endpoint."""
    response = client.get("/api/v1/schema/tables")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "patients" in data


@pytest.mark.integration
def test_api_get_full_schema(client):
    """Test GET /api/v1/schema endpoint."""
    response = client.get("/api/v1/schema")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert len(data["tables"]) > 0
    table_names = [t["table_name"] for t in data["tables"]]
    assert "patients" in table_names


@pytest.mark.integration
def test_api_get_table_schema(client):
    """Test GET /api/v1/schema/tables/{table_name} endpoint."""
    response = client.get("/api/v1/schema/tables/patients")
    assert response.status_code == 200
    data = response.json()
    assert data["table_name"] == "patients"
    assert "columns" in data
    assert "primary_keys" in data
    assert "foreign_keys" in data


@pytest.mark.integration
def test_api_get_table_schema_not_found(client):
    """Test GET /api/v1/schema/tables/{table_name} with nonexistent table."""
    response = client.get("/api/v1/schema/tables/nonexistent_table")
    assert response.status_code == 404


@pytest.mark.integration
def test_api_analyze_schema_endpoint(client):
    """Test POST /api/v1/schema/analyze endpoint."""
    response = client.post("/api/v1/schema/analyze", json={"table_name": "patients"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Check that recommendations have table_name and column_name
    assert all(r["table_name"] == "patients" for r in data)
    assert any(r["column_name"] == "email" for r in data)


