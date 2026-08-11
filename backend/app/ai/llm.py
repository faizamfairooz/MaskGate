import json
from typing import List, Optional

from app.ai.llm_schemas import ColumnRecommendation, SchemaAnalysisLLMResult
from app.config.settings import settings


class LLMClient:
    """LangChain-backed LLM gateway (no SQL or policy bypass)."""

    def __init__(self):
        self._llm = None
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        if settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI

                self._llm = ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                    api_key=settings.OPENAI_API_KEY,
                )
            except Exception:
                self._llm = None

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

Use recommended_strategy from: redaction, partial_mask, hash, email_mask, phone_mask,
ssn_mask, credit_card_mask, date_mask, generalization.
Use sensitivity: low, medium, or high.
Only include columns that need masking."""

        try:
            structured = self._llm.with_structured_output(SchemaAnalysisLLMResult)
            result: SchemaAnalysisLLMResult = structured.invoke(prompt)
            result.table_name = table_name
            return result
        except Exception:
            return self._parse_fallback(prompt, table_name)

    def _parse_fallback(self, prompt: str, table_name: str) -> Optional[SchemaAnalysisLLMResult]:
        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            data = json.loads(content)
            return SchemaAnalysisLLMResult.model_validate(data)
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


llm_client = LLMClient()
