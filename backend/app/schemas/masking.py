from pydantic import BaseModel, Field, AliasChoices
from typing import Optional, Dict, Any, List
from datetime import datetime


class MaskingPolicy(BaseModel):
    """Represents a data masking policy."""
    model_config = {"populate_by_name": True}

    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = ""
    schema_name: str = Field(
        default="public",
        validation_alias=AliasChoices("schema", "schema_name"),
    )
    table_name: str = Field(
        default="",
        validation_alias=AliasChoices("table", "table_name"),
    )
    column_name: str = Field(
        default="",
        validation_alias=AliasChoices("column", "column_name"),
    )
    strategy: str = Field(
        default="",
        validation_alias=AliasChoices("strategy", "masking_strategy", "recommended_strategy"),
    )
    sensitivity: Optional[str] = "MEDIUM"
    parameters: Optional[Dict[str, Any]] = None
    status: str = "ACTIVE"
    source: Optional[str] = "ai_recommendation"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MaskingRecommendation(BaseModel):
    """AI-generated masking recommendation awaiting admin review."""
    model_config = {"populate_by_name": True}

    id: Optional[int] = None
    schema_name: str = Field(
        default="public",
        validation_alias=AliasChoices("schema", "schema_name"),
    )
    table_name: str = Field(
        default="",
        validation_alias=AliasChoices("table", "table_name"),
    )
    column_name: str = Field(
        default="",
        validation_alias=AliasChoices("column", "column_name"),
    )
    data_type: Optional[str] = "text"
    sensitivity: str = "MEDIUM"
    recommended_strategy: str = Field(
        default="",
        validation_alias=AliasChoices("strategy", "recommended_strategy", "masking_strategy"),
    )
    rationale: Optional[str] = None
    source: Optional[str] = "llm"
    status: str = "PENDING"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MaskingRequest(BaseModel):
    """Request to apply masking to data."""
    schema_name: Optional[str] = "public"
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
