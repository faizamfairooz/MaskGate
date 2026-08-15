from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.services.schema_service import SchemaService
from app.schemas.database import DatabaseSchema, TableSchema
from app.schemas.masking import MaskingRecommendation
from app.ai.schema_analyzer import SchemaAnalyzer

router = APIRouter()

schema_service = SchemaService()
schema_analyzer = SchemaAnalyzer()


class AnalyzeSchemaRequest(BaseModel):
    model_config = {"populate_by_name": True}
    table_name: Optional[str] = None
    schema_name: str = Field(default="public", alias="schema")



@router.get("", response_model=DatabaseSchema)
async def get_full_schema(schema: str = "public"):
    """Get full database schema with all tables, columns, and relationships."""
    try:
        return schema_service.get_full_schema(schema=schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {str(e)}")


@router.get("/schemas", response_model=List[str])
async def get_schemas():
    """Get list of user-visible database schemas."""
    try:
        return schema_service.get_schemas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schemas: {str(e)}")


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


@router.post("/analyze", response_model=List[MaskingRecommendation])
async def analyze_schema(request: Optional[AnalyzeSchemaRequest] = None):
    """Analyze schema/tables with GenAI/rules and generate masking recommendations."""
    try:
        req = request or AnalyzeSchemaRequest()
        target_schema = req.schema_name
        results: List[MaskingRecommendation] = []
        if req.table_name:
            table_schema = schema_service.get_table_schema(req.table_name, schema=target_schema)
            recs = schema_analyzer.analyze_and_persist_recommendations(req.table_name, table_schema.columns)
            results.extend(recs)
        else:
            tables = schema_service.get_all_tables(schema=target_schema)
            for tbl in tables:
                table_schema = schema_service.get_table_schema(tbl, schema=target_schema)
                recs = schema_analyzer.analyze_and_persist_recommendations(tbl, table_schema.columns)
                results.extend(recs)
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze schema: {str(e)}")

