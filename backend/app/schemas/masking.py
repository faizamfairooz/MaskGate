from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class MaskingPolicy(BaseModel):
    """Represents a data masking policy."""
    id: Optional[int] = None
    name: str
    description: str
    table_name: str
    column_name: str
    strategy: str
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = "approved"
    source: Optional[str] = "manual"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MaskingRecommendation(BaseModel):
    """AI-generated masking recommendation awaiting admin review."""
    id: Optional[int] = None
    table_name: str
    column_name: str
    sensitivity: str
    recommended_strategy: str
    rationale: Optional[str] = None
    status: Optional[str] = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MaskingRequest(BaseModel):
    """Request to apply masking to data."""
    table_name: str
    columns: List[str]
    data: List[List[Any]]
    policy_ids: Optional[List[int]] = None
    auto_detect: bool = False


class MaskingResult(BaseModel):
    """Result of applying masking to data."""
    original_data: List[List[Any]]
    masked_data: List[List[Any]]
    masked_columns: List[str]
    policies_applied: List[int]
    execution_time: float
    runtime_detection_summary: Optional[str] = None


class MaskingStrategy(BaseModel):
    """Information about a masking strategy."""
    name: str
    description: str
    parameters: Dict[str, Any]
