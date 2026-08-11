from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any

from app.schemas.query import QueryResponse as QueryResponseSchema
from app.services.query_service import QueryService

router = APIRouter()
query_service = QueryService()


class QueryRequest(BaseModel):
    query: str
    apply_masking: bool = True
    mask_suspicious: bool = False


class ValidateQueryRequest(BaseModel):
    query: str


def _run_query(request: QueryRequest) -> QueryResponseSchema:
    return query_service.execute_query(
        query=request.query,
        apply_masking=request.apply_masking,
        mask_suspicious=request.mask_suspicious,
    )


@router.post("", response_model=QueryResponseSchema)
async def execute_query(request: QueryRequest):
    try:
        return _run_query(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.post("/execute", response_model=QueryResponseSchema)
async def execute_query_legacy(request: QueryRequest):
    """Backward-compatible alias."""
    return await execute_query(request)


@router.post("/validate")
async def validate_query(body: ValidateQueryRequest):
    try:
        is_valid, message = query_service.validate_query(body.query)
        return {"valid": is_valid, "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query validation failed: {str(e)}")


@router.get("/history")
async def get_query_history(limit: int = 10):
    try:
        history = query_service.get_query_history(limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve query history: {str(e)}")
