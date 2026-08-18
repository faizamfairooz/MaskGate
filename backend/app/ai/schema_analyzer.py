from typing import Any, Dict, List, Optional
import re
import logging

from app.ai.llm import llm_client
from app.ai.llm_schemas import (
    ColumnRecommendation,
    SensitivityLevel,
    MaskingStrategyRecommendation,
)
from app.schemas.database import ColumnSchema

logger = logging.getLogger(__name__)


class SchemaAnalyzer:
    """Analyzes database schema metadata to identify sensitive columns and recommend masking strategies."""

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
        "ip": r"ip_address|\bip\b",
        "account": r"account|account_number",
    }

    SENSITIVITY_MAP = {
        "email": SensitivityLevel.HIGH,
        "phone": SensitivityLevel.HIGH,
        "ssn": SensitivityLevel.HIGH,
        "credit_card": SensitivityLevel.HIGH,
        "password": SensitivityLevel.HIGH,
        "address": SensitivityLevel.HIGH,
        "name": SensitivityLevel.MEDIUM,
        "dob": SensitivityLevel.HIGH,
        "income": SensitivityLevel.MEDIUM,
        "ip": SensitivityLevel.MEDIUM,
        "account": SensitivityLevel.HIGH,
    }

    STRATEGY_MAP = {
        "email": MaskingStrategyRecommendation.EMAIL,
        "phone": MaskingStrategyRecommendation.PHONE_LAST4,
        "ssn": MaskingStrategyRecommendation.REDACT,
        "credit_card": MaskingStrategyRecommendation.REDACT,
        "password": MaskingStrategyRecommendation.REDACT,
        "name": MaskingStrategyRecommendation.PARTIAL,
        "address": MaskingStrategyRecommendation.PARTIAL,
        "dob": MaskingStrategyRecommendation.PARTIAL,
        "income": MaskingStrategyRecommendation.PARTIAL,
        "ip": MaskingStrategyRecommendation.PARTIAL,
        "account": MaskingStrategyRecommendation.REDACT,
    }

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
                            ).value,
                        }
                    )
                    break

        return analysis

    def analyze_table_schema(
        self, table_name: str, columns: List[ColumnSchema]
    ) -> List[ColumnRecommendation]:
        """
        Analyze table schema metadata via LangChain LLM with fallback to deterministic heuristics.
        
        Cross-validates every recommendation against actual table schema columns.
        Never sends database row values to the LLM.
        """
        if not columns:
            return []

        known_columns = {col.column_name: col.data_type for col in columns}
        safe_meta = [(col.column_name, col.data_type) for col in columns]

        # 1. Attempt LLM analysis if available
        if llm_client.is_available():
            try:
                llm_result = llm_client.analyze_schema_metadata(table_name, safe_meta)
                if llm_result and llm_result.recommendations:
                    valid_recs: List[ColumnRecommendation] = []
                    for item in llm_result.recommendations:
                        # Schema cross-validation: reject hallucinated or nonexistent columns
                        if item.column not in known_columns:
                            logger.warning(
                                f"Rejected LLM recommendation for nonexistent column: {item.column} in table {table_name}"
                            )
                            continue
                        
                        item.table = table_name
                        item.data_type = known_columns[item.column]
                        item.source = "llm"
                        valid_recs.append(item)

                    if valid_recs:
                        return valid_recs
            except Exception as e:
                logger.warning(f"LLM schema analysis failed: {e}. Falling back to heuristics.")

        # 2. Deterministic heuristic fallback
        return self.heuristic_analysis(table_name, columns)

    def heuristic_analysis(
        self, table_name: str, columns: List[ColumnSchema]
    ) -> List[ColumnRecommendation]:
        """Deterministic pattern-based recommendation fallback."""
        recommendations: List[ColumnRecommendation] = []
        for column in columns:
            column_lower = column.column_name.lower()
            matched_type = None
            for data_type_pattern, pattern in self.SENSITIVE_PATTERNS.items():
                if re.search(pattern, column_lower):
                    matched_type = data_type_pattern
                    break

            if matched_type:
                sensitivity = self.SENSITIVITY_MAP.get(matched_type, SensitivityLevel.MEDIUM)
                strategy = self.STRATEGY_MAP.get(matched_type, MaskingStrategyRecommendation.REDACT)
                recommendations.append(
                    ColumnRecommendation(
                        table=table_name,
                        column=column.column_name,
                        sensitivity=sensitivity,
                        data_type=column.data_type,
                        recommended_strategy=strategy,
                        rationale=f"Column name matches {matched_type} pattern",
                        source="heuristic_fallback",
                    )
                )
        return recommendations

    def suggest_masking_strategy(
        self, column_name: str, data_type: str
    ) -> MaskingStrategyRecommendation:
        column_lower = column_name.lower()
        for data_type_pattern, pattern in self.SENSITIVE_PATTERNS.items():
            if re.search(pattern, column_lower):
                return self.STRATEGY_MAP.get(data_type_pattern, MaskingStrategyRecommendation.REDACT)

        if "char" in data_type.lower() or "text" in data_type.lower():
            return MaskingStrategyRecommendation.REDACT
        return MaskingStrategyRecommendation.NONE

