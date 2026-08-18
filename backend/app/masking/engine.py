import copy
from typing import List, Any, Optional, Set, Tuple

from app.schemas.masking import MaskingPolicy
from app.masking.strategies import MaskingStrategyFactory


class MaskingEngine:
    """Deterministic data masking engine for query results."""

    def __init__(self):
        self.strategy_factory = MaskingStrategyFactory()

    def apply_masking(
        self,
        data: List[List[Any]],
        columns: List[str],
        policies: List[MaskingPolicy],
        auto_detect: bool = False,
    ) -> Tuple[List[List[Any]], List[str], Optional[str]]:
        """
        Apply active deterministic masking policies to query result rows in-memory.
        Does not mutate the original data list.
        """
        if not data or not columns:
            return [list(row) for row in data] if data else [], [], None

        # Guarantee zero mutation of the input dataset
        masked_data = [list(row) for row in data]
        masked_columns: Set[str] = set()

        # Build column index lookup (case-insensitive for robust SQL column matching)
        col_name_to_indices = {}
        for idx, col in enumerate(columns):
            norm_col = col.strip().lower()
            if norm_col not in col_name_to_indices:
                col_name_to_indices[norm_col] = []
            col_name_to_indices[norm_col].append(idx)

        # Filter strictly active policies
        active_policies = [
            p for p in policies
            if getattr(p, "is_active", True) and (getattr(p, "status", "ACTIVE") or "").upper() == "ACTIVE"
        ]

        for policy in active_policies:
            policy_col_norm = (policy.column_name or "").strip().lower()
            if policy_col_norm not in col_name_to_indices:
                continue

            target_indices = col_name_to_indices[policy_col_norm]
            try:
                strategy = self.strategy_factory.get_strategy(policy.strategy)
            except ValueError:
                # If strategy is unrecognized, skip safely without breaking query execution
                continue

            for row in masked_data:
                for col_idx in target_indices:
                    if col_idx < len(row):
                        try:
                            row[col_idx] = strategy.mask(row[col_idx], policy.parameters or {})
                        except Exception:
                            # Graceful fallback on unexpected error
                            pass

            for col_idx in target_indices:
                masked_columns.add(columns[col_idx])

        runtime_summary = None
        if auto_detect:
            runtime_summary = self._apply_runtime_detection(
                masked_data, columns, {p.column_name for p in active_policies}, masked_columns
            )

        return masked_data, list(masked_columns), runtime_summary

    def _apply_runtime_detection(
        self,
        masked_data: List[List[Any]],
        columns: List[str],
        policy_columns: Set[str],
        masked_columns: Set[str],
    ) -> Optional[str]:
        """
        Stage 2 runtime detection layer when auto_detect is enabled.
        Executes local regex detection at the cell level.
        """
        try:
            from app.config.settings import settings
            if not getattr(settings, "ENABLE_RUNTIME_DETECTION", True):
                return None

            from app.ai.sensitive_data_detector import SensitiveDataDetector

            detector = SensitiveDataDetector()

            # Normalized set of columns already masked in Stage 1
            norm_policy_columns = {p.strip().lower() for p in policy_columns if p}

            # Identify unmasked column indices
            unmasked_col_indices = [
                idx for idx, col in enumerate(columns)
                if col.strip().lower() not in norm_policy_columns
            ]

            if not unmasked_col_indices:
                return None

            # Stage 2A: Local regex detection (Cell-Level)
            local_detected_cells = detector.detect_local_cells(
                masked_data, columns, unmasked_col_indices=unmasked_col_indices
            )

            pattern_cell_count = 0
            detected_types = set()

            for row_idx, col_idx, data_type, strategy_name in local_detected_cells:
                if row_idx < len(masked_data) and col_idx < len(masked_data[row_idx]):
                    try:
                        strategy = self.strategy_factory.get_strategy(strategy_name)
                        masked_data[row_idx][col_idx] = strategy.mask(
                            masked_data[row_idx][col_idx], {}
                        )
                        masked_columns.add(columns[col_idx])
                        pattern_cell_count += 1
                        detected_types.add(data_type)
                    except ValueError:
                        pass

            # Stage 2B: Optional targeted LLM analysis
            llm_cell_count = 0
            llm_result = None

            if detector.use_llm and len(masked_data) > 0:
                already_masked = list(masked_columns)
                llm_result, llm_operations = detector.detect_runtime_sensitive_data(
                    masked_data, columns, already_masked
                )

                if llm_result and llm_operations:
                    for row_idx, col_idx, strategy_name in llm_operations:
                        if row_idx < len(masked_data) and col_idx < len(masked_data[row_idx]):
                            try:
                                strategy = self.strategy_factory.get_strategy(strategy_name)
                                masked_data[row_idx][col_idx] = strategy.mask(
                                    masked_data[row_idx][col_idx], {}
                                )
                                masked_columns.add(columns[col_idx])
                                llm_cell_count += 1
                            except ValueError:
                                pass

            # Build comprehensive runtime summary
            summary_parts = []
            if pattern_cell_count > 0:
                types_str = ", ".join(sorted(detected_types))
                summary_parts.append(f"Pattern matching: {pattern_cell_count} cells masked ({types_str})")
            if llm_cell_count > 0:
                summary_parts.append(f"LLM detection: {llm_cell_count} cells masked")
            if llm_result and getattr(llm_result, "summary", ""):
                summary_parts.append(f"LLM summary: {llm_result.summary}")
                conf_val = getattr(llm_result.confidence, "value", str(llm_result.confidence))
                summary_parts.append(f"LLM confidence: {conf_val}")

            return " | ".join(summary_parts) if summary_parts else None
        except Exception:
            return None

    def apply_single_masking(self, value: Any, policy: MaskingPolicy) -> Any:
        strategy = self.strategy_factory.get_strategy(policy.strategy)
        return strategy.mask(value, policy.parameters or {})

    def validate_policy(self, policy: MaskingPolicy) -> bool:
        try:
            strategy = self.strategy_factory.get_strategy(policy.strategy)
            return strategy.validate_parameters(policy.parameters or {})
        except Exception:
            return False
