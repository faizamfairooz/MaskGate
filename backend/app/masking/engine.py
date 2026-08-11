from typing import List, Any, Optional, Set, Tuple

from app.ai.llm import llm_client
from app.ai.sensitive_data_detector import SensitiveDataDetector
from app.schemas.masking import MaskingPolicy
from app.masking.strategies import MaskingStrategyFactory


class MaskingEngine:
    """Engine for applying masking strategies to data."""

    def __init__(self):
        self.strategy_factory = MaskingStrategyFactory()
        self.detector = SensitiveDataDetector()

    def apply_masking(
        self,
        data: List[List[Any]],
        columns: List[str],
        policies: List[MaskingPolicy],
        auto_detect: bool = False,
    ) -> Tuple[List[List[Any]], List[str], Optional[str]]:
        if not data:
            return data, [], None

        masked_data = [row[:] for row in data]
        masked_columns: Set[str] = set()
        policy_columns = {p.column_name for p in policies}

        for policy in policies:
            if policy.column_name not in columns:
                continue
            col_idx = columns.index(policy.column_name)
            strategy = self.strategy_factory.get_strategy(policy.strategy)
            for row in masked_data:
                row[col_idx] = strategy.mask(row[col_idx], policy.parameters or {})
            masked_columns.add(policy.column_name)

        runtime_summary = None
        if auto_detect:
            runtime_summary = self._apply_runtime_detection(
                masked_data, columns, policy_columns, masked_columns
            )

        return masked_data, list(masked_columns), runtime_summary

    def _apply_runtime_detection(
        self,
        masked_data: List[List[Any]],
        columns: List[str],
        policy_columns: Set[str],
        masked_columns: Set[str],
    ) -> Optional[str]:
        column_stats = []
        for col_idx, column in enumerate(columns):
            if column in policy_columns:
                continue
            column_values = [row[col_idx] for row in masked_data]
            risks = self.detector._analyze_column(column, column_values)
            if risks["risk_level"] > 0:
                strategy_name = self.detector.get_masking_recommendations(
                    column, risks["detected_types"]
                )[0]
                strategy = self.strategy_factory.get_strategy(strategy_name)
                for row in masked_data:
                    row[col_idx] = strategy.mask(row[col_idx], {})
                masked_columns.add(column)
                column_stats.append(
                    {
                        "column": column,
                        "detected_types": risks["detected_types"],
                        "risk_level": risks["risk_level"],
                    }
                )

        return llm_client.summarize_runtime_detection(column_stats)

    def apply_single_masking(self, value: Any, policy: MaskingPolicy) -> Any:
        strategy = self.strategy_factory.get_strategy(policy.strategy)
        return strategy.mask(value, policy.parameters or {})

    def validate_policy(self, policy: MaskingPolicy) -> bool:
        try:
            strategy = self.strategy_factory.get_strategy(policy.strategy)
            return strategy.validate_parameters(policy.parameters or {})
        except Exception:
            return False
