import json
from typing import List, Optional

from app.ai.llm_schemas import (
    ColumnRecommendation,
    SchemaAnalysisLLMResult,
    RuntimeDetectionResult,
)
from app.config.settings import settings


class LLMClient:
    """LangChain-backed LLM gateway (no SQL or policy bypass)."""

    def __init__(self):
        self._llm = None
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        
        # Try OpenAI first if a real key is provided
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your_"):
            try:
                from langchain_openai import ChatOpenAI

                self._llm = ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                    api_key=settings.OPENAI_API_KEY,
                )
            except Exception:
                self._llm = None
        
        # Fallback to Google AI Studio (Gemini)
        if self._llm is None and settings.GOOGLE_API_KEY and not settings.GOOGLE_API_KEY.startswith("your_"):
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                self._llm = ChatGoogleGenerativeAI(
                    model="gemini-3.5-flash",
                    temperature=self.temperature,
                    google_api_key=settings.GOOGLE_API_KEY,
                )
                self._is_google = True
            except Exception:
                self._llm = None
                self._is_google = False
        else:
            self._is_google = False

    def is_available(self) -> bool:
        return self._llm is not None

    def analyze_schema_metadata(
        self, table_name: str, columns: List[tuple[str, str]]
    ) -> Optional[SchemaAnalysisLLMResult]:
        """
        Analyze column metadata only (no row data).
        Returns structured recommendations or None if LLM unavailable.
        """
        if not self.is_available():
            return None

        schema_lines = "\n".join(f"- {name} ({dtype})" for name, dtype in columns)
        prompt = f"""You are a database privacy analyst. Given ONLY this table metadata, recommend masking
for columns that may hold sensitive or personally identifiable information.

Table: {table_name}
Columns:
{schema_lines}

Use recommended_strategy from: redaction, partial_mask, hash, email_mask, phone_mask, ssn_mask, credit_card_mask, date_mask, generalization.
Use sensitivity: low, medium, or high.
Only include columns that need masking.

Output JSON in this format:
{{
  "table_name": "{table_name}",
  "recommendations": [
    {{
      "column": "column_name",
      "sensitivity": "high",
      "recommended_strategy": "email_mask",
      "rationale": "reason"
    }}
  ]
}}"""

        if getattr(self, "_is_google", False):
            return self._parse_fallback(prompt, table_name)

        try:
            structured = self._llm.with_structured_output(SchemaAnalysisLLMResult)
            result: SchemaAnalysisLLMResult = structured.invoke(prompt)
            result.table_name = table_name
            return result
        except Exception:
            return self._parse_fallback(prompt, table_name)

    @staticmethod
    def _extract_json_text(content: str) -> str:
        text = content.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        return text

    def _parse_fallback(self, prompt: str, table_name: str) -> Optional[SchemaAnalysisLLMResult]:
        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            clean_json = self._extract_json_text(content)
            data = json.loads(clean_json)
            result = SchemaAnalysisLLMResult.model_validate(data)
            result.table_name = table_name
            return result
        except Exception:
            return None

    def summarize_runtime_detection(
        self, column_stats: List[dict]
    ) -> Optional[str]:
        """Optional summary from aggregated detection stats (no raw cell values)."""
        if not self.is_available() or not column_stats:
            return None
        stats_text = json.dumps(column_stats, indent=2)
        prompt = f"""Summarize privacy risks from this aggregated column detection report.
Do not invent specific values. Keep under 120 words.

{stats_text}"""
        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            return str(content)
        except Exception:
            return None

    def detect_runtime_sensitive_data(
        self,
        data: List[List[Any]],
        columns: List[str],
        already_masked_columns: List[str],
    ) -> Optional[RuntimeDetectionResult]:
        """
        Detect sensitive data in query results using LLM analysis.
        This is a secondary safety layer after deterministic masking.

        Args:
            data: Query result rows (already masked by deterministic policies)
            columns: Column names
            already_masked_columns: Columns already protected by policies

        Returns:
            Structured detection results or None if LLM unavailable
        """
        if not self.is_available() or not data:
            return None

        # Sample data to avoid sending too much to LLM
        sample_size = min(10, len(data))
        sample_data = data[:sample_size]

        # Build data description (avoid sending full values)
        data_description = "Columns: " + ", ".join(columns) + "\n"
        data_description += "Already masked columns: " + ", ".join(already_masked_columns) + "\n"
        data_description += "Sample data (already masked):\n"

        for row_idx, row in enumerate(sample_data):
            row_repr = []
            for col_idx, value in enumerate(row):
                # Truncate long values and avoid sending full sensitive content
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:25] + "..." + value_str[-25:]
                row_repr.append(f"{columns[col_idx]}={value_str}")
            data_description += f"Row {row_idx}: " + ", ".join(row_repr) + "\n"

        prompt = f"""You are a data privacy analyst. Analyze this query result data for sensitive information
that may NOT have been covered by existing masking policies.

IMPORTANT:
- This is a SECONDARY detection layer - deterministic policies have already been applied
- Focus on finding sensitive data in columns that are NOT already masked
- Never suggest executing SQL or modifying data
- Be conservative - if unsure, flag as potentially sensitive

Look for:
- Email addresses, phone numbers, SSNs, credit card numbers
- Personal identifiers, addresses, names
- Financial information, medical data
- Any other PII or sensitive information

{data_description}

Return structured findings with:
- row_index: the row number where sensitive data was found
- column_name: the column containing sensitive data
- sensitivity: low, medium, or high
- data_type: type of sensitive data (email, phone, ssn, custom, etc.)
- recommended_strategy: one of: redaction, partial_mask, email_mask, phone_mask, ssn_mask, credit_card_mask, hash
- rationale: brief explanation
- summary: overall summary
- confidence: high, medium, or low

If no sensitive data is found, set has_sensitive_data to false and provide an empty detections list."""

        if getattr(self, "_is_google", False):
            return self._parse_runtime_detection_fallback(prompt)

        try:
            structured = self._llm.with_structured_output(RuntimeDetectionResult)
            result: RuntimeDetectionResult = structured.invoke(prompt)
            return result
        except Exception:
            # Fallback: try parsing as JSON
            return self._parse_runtime_detection_fallback(prompt)

    def _parse_runtime_detection_fallback(
        self, prompt: str
    ) -> Optional[RuntimeDetectionResult]:
        """Fallback parsing for runtime detection when structured output fails."""
        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            clean_json = self._extract_json_text(content)
            data = json.loads(clean_json)
            return RuntimeDetectionResult.model_validate(data)
        except Exception:
            return None


llm_client = LLMClient()
