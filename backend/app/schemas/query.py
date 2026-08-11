from pydantic import BaseModel
from typing import List, Any, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """Request to execute a SQL query."""
    query: str
    params: Optional[tuple] = None
    apply_masking: bool = True
    mask_suspicious: bool = False


class QueryResponse(BaseModel):
    """Response from a SQL query execution."""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time: float
    masked_columns: List[str]
    query_hash: Optional[str] = None
    runtime_detection_summary: Optional[str] = None


class QueryHistory(BaseModel):
    """Record of a query execution."""
    id: Optional[int] = None
    query: str
    executed_at: datetime
    execution_time: float
    row_count: int
    masked: bool


class QueryValidation(BaseModel):
    """Result of query validation."""
    is_valid: bool
    message: str
    suggested_fix: Optional[str] = None
