from typing import List, Dict, Any, Optional, Tuple
from app.ai.llm import llm_client
from app.ai.llm_schemas import RuntimeDetectionResult
import re


class SensitiveDataDetector:
    """Detects sensitive data in database records using pattern matching and LLM analysis."""

    # Patterns for detecting sensitive data in values (ordered by specificity)
    DATA_PATTERNS = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'credit_card': r'\b(?:\d[ -]*?){13,16}\b',
        'ssn': r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
        'phone': r'(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)',
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'url': r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .-]*/?'
    }

    PATTERN_STRATEGIES = {
        'email': 'EMAIL',
        'phone': 'PHONE_LAST4',
        'ssn': 'REDACT',
        'credit_card': 'REDACT',
        'ip_address': 'REDACT',
        'url': 'REDACT',
    }

    def __init__(self):
        self.use_llm = llm_client.is_available()

    def detect_local_cells(
        self,
        data: List[List[Any]],
        columns: List[str],
        unmasked_col_indices: Optional[List[int]] = None,
    ) -> List[Tuple[int, int, str, str]]:
        """
        Detect obvious PII patterns in unmasked cells locally.

        Returns:
            List of (row_index, column_index, detected_type, masking_strategy)
        """
        if not data or not columns:
            return []

        if unmasked_col_indices is None:
            unmasked_col_indices = list(range(len(columns)))

        detected_cells: List[Tuple[int, int, str, str]] = []
        for row_idx, row in enumerate(data):
            for col_idx in unmasked_col_indices:
                if col_idx >= len(row) or row[col_idx] is None:
                    continue
                cell_str = str(row[col_idx]).strip()
                if not cell_str:
                    continue

                for data_type, pattern in self.DATA_PATTERNS.items():
                    if re.search(pattern, cell_str):
                        strategy = self.PATTERN_STRATEGIES.get(data_type, 'REDACT')
                        detected_cells.append((row_idx, col_idx, data_type, strategy))
                        break  # Match primary pattern per cell

        return detected_cells

    def detect_sensitive_data(
        self,
        data: List[List[Any]],
        columns: List[str]
    ) -> Dict[str, Any]:
        """Detect sensitive data in the provided dataset."""
        results = {
            'total_rows': len(data),
            'sensitive_findings': [],
            'column_risks': {},
            'high_risk_rows': []
        }

        # Analyze each column
        for col_idx, column in enumerate(columns):
            column_values = [row[col_idx] for row in data if row[col_idx] is not None]
            column_risks = self._analyze_column(column, column_values)
            
            if column_risks['risk_level'] > 0:
                results['column_risks'][column] = column_risks

        # Identify high-risk rows
        results['high_risk_rows'] = self._identify_high_risk_rows(data, columns)

        # Use LLM for deeper analysis if available
        if self.use_llm and len(data) > 0:
            results['llm_analysis'] = self._get_llm_analysis(data, columns)

        return results

    def _analyze_column(self, column_name: str, values: List[Any]) -> Dict[str, Any]:
        """Analyze a single column for sensitive data patterns."""
        risks = {
            'column': column_name,
            'risk_level': 0,
            'detected_types': [],
            'sample_matches': []
        }

        text_values = [str(v) for v in values]

        for data_type, pattern in self.DATA_PATTERNS.items():
            matches = []
            for value in text_values:
                if re.search(pattern, value):
                    matches.append(value[:50] + '...' if len(value) > 50 else value)

            if matches:
                risks['detected_types'].append(data_type)
                risks['sample_matches'].extend(matches[:3])  # Limit samples
                risks['risk_level'] += 1

        return risks

    def _identify_high_risk_rows(
        self,
        data: List[List[Any]],
        columns: List[str]
    ) -> List[int]:
        """Identify row indices that contain multiple sensitive data points."""
        high_risk_rows = []

        for row_idx, row in enumerate(data):
            sensitive_count = 0
            for col_idx, value in enumerate(row):
                if value is None:
                    continue
                value_str = str(value)
                for pattern in self.DATA_PATTERNS.values():
                    if re.search(pattern, value_str):
                        sensitive_count += 1
                        break

            if sensitive_count >= 2:  # Threshold for high-risk
                high_risk_rows.append(row_idx)

        return high_risk_rows

    def _get_llm_analysis(
        self,
        data: List[List[Any]],
        columns: List[str]
    ) -> str:
        """Get LLM-based analysis of the data."""
        # Sample first few rows for analysis
        sample_size = min(5, len(data))
        sample_data = data[:sample_size]

        data_description = "Columns: " + ", ".join(columns) + "\n"
        data_description += "Sample data:\n"
        for row in sample_data:
            data_description += str(row) + "\n"

        prompt = f"""
        Analyze the following data for privacy and security concerns.
        Identify:
        1. Types of sensitive data present
        2. Privacy risks
        3. Recommended actions
        
        {data_description}
        """

        try:
            return llm_client.generate_response(prompt, max_tokens=500)
        except Exception as e:
            return f"LLM analysis failed: {str(e)}"

    def get_masking_recommendations(
        self,
        column_name: str,
        detected_types: List[str]
    ) -> List[str]:
        """Get masking recommendations based on detected data types."""
        recommendations = []

        type_to_strategy = {
            'email': 'email_mask',
            'phone': 'phone_mask',
            'ssn': 'ssn_mask',
            'credit_card': 'credit_card_mask',
            'ip_address': 'redaction',
            'url': 'redaction'
        }

        for data_type in detected_types:
            if data_type in type_to_strategy:
                recommendations.append(type_to_strategy[data_type])

        return recommendations if recommendations else ['redaction']

    def detect_runtime_sensitive_data(
        self,
        data: List[List[Any]],
        columns: List[str],
        already_masked_columns: List[str],
    ) -> Tuple[RuntimeDetectionResult, List[Tuple[int, int, str]]]:
        """
        Perform LLM-based runtime sensitive data detection.
        Validates detections to ensure only legitimate, bounded cell operations are returned.

        Args:
            data: Query result rows (may already be partially masked)
            columns: Column names
            already_masked_columns: Columns already protected by policies

        Returns:
            Tuple of (LLM detection result, list of (row_idx, col_idx, strategy) to apply)
        """
        from app.masking.strategies import MaskingStrategyFactory
        strategy_factory = MaskingStrategyFactory()

        # Use LLM for structured detection
        try:
            llm_result = llm_client.detect_runtime_sensitive_data(
                data, columns, already_masked_columns
            )
        except Exception:
            llm_result = None

        if not llm_result:
            empty_result = RuntimeDetectionResult(
                has_sensitive_data=False,
                detections=[],
                summary="LLM detection unavailable - pattern matching only",
                confidence="LOW"
            )
            return empty_result, []

        # Normalized lookup for columns
        col_lookup = {col.strip().lower(): idx for idx, col in enumerate(columns)}
        masked_set = {c.strip().lower() for c in already_masked_columns if c}

        # Convert and validate LLM detections to actionable masking operations
        masking_operations = []
        valid_detections = []

        for detection in llm_result.detections:
            col_norm = (detection.column_name or "").strip().lower()
            if col_norm not in col_lookup:
                continue  # Reject hallucinated column

            if col_norm in masked_set:
                continue  # Reject detection on already-masked column

            col_idx = col_lookup[col_norm]
            row_idx = detection.row_index

            # Reject out-of-bounds row index
            if row_idx < 0 or row_idx >= len(data):
                continue

            # Validate or normalize strategy
            strat = detection.recommended_strategy or "REDACT"
            try:
                strategy_factory.get_strategy(strat)
                valid_strat = strat
            except ValueError:
                valid_strat = "REDACT"

            masking_operations.append((row_idx, col_idx, valid_strat))
            valid_detections.append(detection)

        # Update detections to only valid detections
        llm_result.detections = valid_detections
        if not valid_detections and llm_result.has_sensitive_data:
            llm_result.has_sensitive_data = False

        return llm_result, masking_operations
