from fastapi import APIRouter, HTTPException
from typing import List

from app.services.schema_service import SchemaService
from app.schemas.database import DatabaseSchema, TableSchema

router = APIRouter()
schema_service = SchemaService()


@router.get("", response_model=DatabaseSchema)
async def get_full_schema(schema: str = "public"):
    """Get full database schema with all tables, columns, and relationships."""
    try:
        return schema_service.get_full_schema(schema=schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {str(e)}")


@router.get("/tables", response_model=List[str])
async def get_tables(schema: str = "public"):
    """Get list of all tables in the database."""
    try:
        return schema_service.get_all_tables(schema=schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tables: {str(e)}")


@router.get("/tables/{table_name}", response_model=TableSchema)
async def get_table_schema(table_name: str, schema: str = "public"):
    """Get detailed schema information for a specific table."""
    try:
        return schema_service.get_table_schema(table_name, schema=schema)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve table schema: {str(e)}")
