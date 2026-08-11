from typing import Any, Dict, List, Optional

from app.ai.llm import llm_client
from app.database.repositories import RecommendationRepository
from app.schemas.database import ColumnSchema
from app.schemas.masking import MaskingRecommendation
import re


class SchemaAnalyzer:
    """Analyzes database schemas to identify patterns and sensitive data."""

    SENSITIVE_PATTERNS = {
        "email": r"email|mail",
        "phone": r"phone|mobile|telephone",
        "ssn": r"ssn|social_security|social",
        "credit_card": r"credit|card|cc_number|cvv",
        "password": r"password|passwd|pwd",
        "address": r"address|street|city|state|zip|postal",
        "name": r"name|first_name|last_name|full_name",
        "dob": r"dob|birth|birthday",
        "income": r"income|salary|wage",
        "ip": r"ip_address|ip",
        "account": r"account|account_number",
    }

    SENSITIVITY_MAP = {
        "email": "high",
        "phone": "high",
        "ssn": "high",
        "credit_card": "high",
        "password": "high",
        "address": "high",
        "name": "medium",
        "dob": "high",
        "income": "medium",
        "ip": "medium",
        "account": "high",
    }

    def __init__(self, recommendation_repo: Optional[RecommendationRepository] = None):
        self.recommendation_repo = recommendation_repo or RecommendationRepository()

    def detect_sensitive_columns(self, columns: List[ColumnSchema]) -> List[str]:
        sensitive_columns = []
        for column in columns:
            column_name = column.column_name.lower()
            for pattern in self.SENSITIVE_PATTERNS.values():
                if re.search(pattern, column_name):
                    sensitive_columns.append(column.column_name)
                    break
        return sensitive_columns

    def analyze_column_patterns(self, columns: List[ColumnSchema]) -> Dict[str, Any]:
        analysis: Dict[str, Any] = {
            "total_columns": len(columns),
            "sensitive_count": 0,
            "recommendations": [],
            "data_types": {},
        }

        for column in columns:
            data_type = column.data_type
            analysis["data_types"][data_type] = analysis["data_types"].get(data_type, 0) + 1

            column_name = column.column_name.lower()
            for data_type_pattern, pattern in self.SENSITIVE_PATTERNS.items():
                if re.search(pattern, column_name):
                    analysis["sensitive_count"] += 1
                    analysis["recommendations"].append(
                        {
                            "column": column.column_name,
                            "type": data_type_pattern,
                            "recommendation": self.suggest_masking_strategy(
                                column.column_name, column.data_type
                            ),
                        }
                    )
                    break

        return analysis

    def analyze_and_persist_recommendations(
        self, table_name: str, columns: List[ColumnSchema]
    ) -> List[MaskingRecommendation]:
        """Rule-based + optional LLM recommendations stored as pending."""
        saved: List[MaskingRecommendation] = []
        llm_result = llm_client.analyze_schema_metadata(
            table_name,
            [(c.column_name, c.data_type) for c in columns],
        )

        if llm_result and llm_result.recommendations:
            for item in llm_result.recommendations:
                rec = MaskingRecommendation(
                    table_name=table_name,
                    column_name=item.column,
                    sensitivity=str(item.sensitivity.value if hasattr(item.sensitivity, 'value') else item.sensitivity),
                    recommended_strategy=item.recommended_strategy,
                    rationale=item.rationale,
                    status="pending",
                )
                saved.append(self.recommendation_repo.create(rec))
            return saved

        for column in columns:
            column_lower = column.column_name.lower()
            for data_type_pattern, pattern in self.SENSITIVE_PATTERNS.items():
                if re.search(pattern, column_lower):
                    rec = MaskingRecommendation(
                        table_name=table_name,
                        column_name=column.column_name,
                        sensitivity=self.SENSITIVITY_MAP.get(data_type_pattern, "medium"),
                        recommended_strategy=self.suggest_masking_strategy(
                            column.column_name, column.data_type
                        ),
                        rationale=f"Column name matches {data_type_pattern} pattern",
                        status="pending",
                    )
                    saved.append(self.recommendation_repo.create(rec))
                    break

        return saved

    def suggest_masking_strategy(self, column_name: str, data_type: str) -> str:
        column_lower = column_name.lower()
        strategy_mapping = {
            "email": "email_mask",
            "phone": "phone_mask",
            "ssn": "ssn_mask",
            "credit_card": "credit_card_mask",
            "password": "hash",
            "name": "partial_mask",
            "address": "partial_mask",
            "dob": "date_mask",
            "income": "generalization",
        }

        for data_type_pattern, pattern in self.SENSITIVE_PATTERNS.items():
            if re.search(pattern, column_lower):
                return strategy_mapping.get(data_type_pattern, "redaction")

        if "char" in data_type.lower() or "text" in data_type.lower():
            return "redaction"
        if "int" in data_type.lower() or "numeric" in data_type.lower():
            return "noise_addition"
        return "redaction"
