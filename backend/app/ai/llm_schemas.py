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


class SensitiveValueDetection(BaseModel):
    """Detection of a specific sensitive value in the data."""
    row_index: int = Field(description="Index of the row containing the sensitive value")
    column_name: str = Field(description="Name of the column containing the sensitive value")
    sensitivity: SensitivityLevel = Field(description="Sensitivity level")
    data_type: str = Field(description="Type of sensitive data (e.g., email, phone, ssn, custom)")
    recommended_strategy: str = Field(
        description="Recommended masking strategy for this value"
    )
    rationale: str = Field(description="Brief explanation of why this is sensitive")


class RuntimeDetectionResult(BaseModel):
    """Structured result from LLM-based runtime sensitive data detection."""
    has_sensitive_data: bool = Field(description="Whether sensitive data was detected")
    detections: List[SensitiveValueDetection] = Field(
        description="List of detected sensitive values"
    )
    summary: str = Field(description="Brief summary of findings")
    confidence: str = Field(description="Confidence level: high, medium, or low")
