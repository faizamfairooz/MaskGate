from typing import List, Dict, Any, Optional
from app.ai.llm import llm_client
import re


class SensitiveDataDetector:
    """Detects sensitive data in database records using pattern matching and LLM analysis."""

    # Patterns for detecting sensitive data in values
    DATA_PATTERNS = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'phone': r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        'ssn': r'\d{3}[-.\s]?\d{2}[-.\s]?\d{4}',
        'credit_card': r'\b(?:\d[ -]*?){13,16}\b',
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'url': r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .-]*/?'
    }

    def __init__(self):
        self.use_llm = llm_client.is_available()

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
