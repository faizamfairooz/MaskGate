from typing import List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SensitivityLevel(str, Enum):
    """Sensitivity levels for data classification."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ConfidenceLevel(str, Enum):
    """Confidence levels for runtime sensitive data detection."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MaskingStrategyRecommendation(str, Enum):
    """Masking strategies recommended by LLM / Heuristics."""
    NONE = "NONE"
    REDACT = "REDACT"
    PARTIAL = "PARTIAL"
    EMAIL = "EMAIL"
    PHONE_LAST4 = "PHONE_LAST4"


class ColumnRecommendation(BaseModel):
    """Structured column masking recommendation."""
    table: str = Field(description="Table name")
    column: str = Field(description="Column name")
    sensitivity: SensitivityLevel = Field(description="HIGH, MEDIUM, or LOW")
    data_type: str = Field(default="text", description="PostgreSQL data type")
    recommended_strategy: MaskingStrategyRecommendation = Field(
        description="Recommended masking strategy: NONE, REDACT, PARTIAL, EMAIL, PHONE_LAST4"
    )
    confidence: Optional[ConfidenceLevel] = Field(
        default=ConfidenceLevel.HIGH, description="Confidence level: HIGH, MEDIUM, LOW"
    )
    rationale: Optional[str] = Field(default="", description="Brief reason for the recommendation")
    source: Optional[str] = Field(
        default="llm", description="Source of recommendation: 'llm' or 'heuristic_fallback'"
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ConfidenceLevel.__members__:
                return ConfidenceLevel(v_upper)
        return v

    @field_validator("sensitivity", mode="before")
    @classmethod
    def normalize_sensitivity(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in SensitivityLevel.__members__:
                return SensitivityLevel(v_upper)
        return v

    @field_validator("recommended_strategy", mode="before")
    @classmethod
    def normalize_strategy(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            strategy_alias_map = {
                "NONE": "NONE",
                "NO_MASK": "NONE",
                "REDACT": "REDACT",
                "REDACTION": "REDACT",
                "PARTIAL": "PARTIAL",
                "PARTIAL_MASK": "PARTIAL",
                "EMAIL": "EMAIL",
                "EMAIL_MASK": "EMAIL",
                "PHONE": "PHONE_LAST4",
                "PHONE_MASK": "PHONE_LAST4",
                "PHONE_LAST4": "PHONE_LAST4",
                "LAST4": "PHONE_LAST4",
                "SSN_MASK": "REDACT",
                "CREDIT_CARD_MASK": "REDACT",
                "HASH": "REDACT",
            }
            mapped = strategy_alias_map.get(v_upper, v_upper)
            if mapped in MaskingStrategyRecommendation.__members__:
                return MaskingStrategyRecommendation(mapped)
        return v


class SchemaAnalysisLLMResult(BaseModel):
    table_name: str
    recommendations: List[ColumnRecommendation]


class SensitiveValueDetection(BaseModel):
    """Detection of a specific sensitive value in the data."""
    row_index: int = Field(description="Index of the row containing the sensitive value")
    column_name: str = Field(description="Name of the column containing the sensitive value")
    sensitivity: SensitivityLevel = Field(default=SensitivityLevel.HIGH, description="Sensitivity level")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.HIGH, description="Confidence level")
    data_type: str = Field(description="Type of sensitive data (e.g., email, phone, ssn, custom)")
    recommended_strategy: str = Field(
        description="Recommended masking strategy for this value"
    )
    rationale: str = Field(default="", description="Brief explanation of why this is sensitive")

    @field_validator("sensitivity", mode="before")
    @classmethod
    def normalize_sensitivity(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in SensitivityLevel.__members__:
                return SensitivityLevel(v_upper)
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ConfidenceLevel.__members__:
                return ConfidenceLevel(v_upper)
        return v


class RuntimeDetectionResult(BaseModel):
    """Structured result from runtime sensitive data detection."""
    has_sensitive_data: bool = Field(description="Whether sensitive data was detected")
    detections: List[SensitiveValueDetection] = Field(
        default_factory=list,
        description="List of detected sensitive values",
    )
    summary: str = Field(default="", description="Brief summary of findings")
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.HIGH,
        description="Overall confidence level: HIGH, MEDIUM, or LOW",
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ConfidenceLevel.__members__:
                return ConfidenceLevel(v_upper)
        return v
