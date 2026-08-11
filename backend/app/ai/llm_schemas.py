from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class SensitivityLevel(str, Enum):
    """Sensitivity levels for data classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ColumnRecommendation(BaseModel):
    column: str = Field(description="Column name")
    sensitivity: SensitivityLevel = Field(description="low, medium, or high")
    recommended_strategy: str = Field(
        description="Masking strategy key e.g. email_mask, phone_mask, redaction"
    )
    rationale: str = Field(description="Brief reason for the recommendation")


class SchemaAnalysisLLMResult(BaseModel):
    table_name: str
    recommendations: List[ColumnRecommendation]
