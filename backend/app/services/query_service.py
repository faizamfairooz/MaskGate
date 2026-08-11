from datetime import datetime
from typing import List, Any, Optional
import hashlib
import re
import time

from app.database.postgresql import db
from app.schemas.query import QueryResponse, QueryHistory
from app.services.masking_service import MaskingService
from app.schemas.masking import MaskingRequest


class QueryService:
    """Service for executing SQL queries with optional data masking."""

    DANGEROUS_KEYWORDS = (
        "DROP",
        "DELETE",
        "TRUNCATE",
        "ALTER",
        "CREATE",
        "GRANT",
        "REVOKE",
        "INSERT",
        "UPDATE",
    )

    def __init__(self):
        self.masking_service = MaskingService()
        self.query_history: List[QueryHistory] = []

    def execute_query(
        self,
        query: str,
        apply_masking: bool = True,
        mask_suspicious: bool = False,
    ) -> QueryResponse:
        is_valid, message = self.validate_query(query)
        if not is_valid:
            raise ValueError(message)

        start_time = time.time()
        results = db.execute_query(query)

        if not results:
            return QueryResponse(
                columns=[],
                rows=[],
                row_count=0,
                execution_time=time.time() - start_time,
                masked_columns=[],
            )

        columns = list(results[0].keys())
        rows = [list(row.values()) for row in results]
        masked_columns: List[str] = []
        masked_data = rows
        runtime_summary = None

        if apply_masking:
            masking_result = self.masking_service.apply_masking(
                MaskingRequest(
                    table_name=self._extract_table_name(query),
                    columns=columns,
                    data=rows,
                    auto_detect=mask_suspicious,
                )
            )
            masked_data = masking_result.masked_data
            masked_columns = masking_result.masked_columns
            runtime_summary = masking_result.runtime_detection_summary

        execution_time = time.time() - start_time
        query_hash = self._generate_query_hash(query)

        self.query_history.append(
            QueryHistory(
                query=query,
                executed_at=datetime.utcnow(),
                execution_time=execution_time,
                row_count=len(rows),
                masked=apply_masking,
            )
        )

        return QueryResponse(
            columns=columns,
            rows=masked_data,
            row_count=len(rows),
            execution_time=execution_time,
            masked_columns=masked_columns,
            query_hash=query_hash,
            runtime_detection_summary=runtime_summary,
        )

    def validate_query(self, query: str) -> tuple[bool, str]:
        normalized = query.strip()
        if not normalized:
            return False, "Query is empty"

        upper = re.sub(r"\s+", " ", normalized.upper())
        if upper.startswith("WITH"):
            if "SELECT" not in upper:
                return False, "Query must contain SELECT"
        elif not upper.startswith("SELECT"):
            return False, "Only SELECT queries are allowed"

        for keyword in self.DANGEROUS_KEYWORDS:
            if re.search(rf"\b{keyword}\b", upper):
                if keyword != "SELECT":
                    return False, f"Query contains disallowed keyword: {keyword}"

        if ";" in normalized.rstrip(";"):
            return False, "Multiple statements are not allowed"

        return True, "Query is valid"

    def get_query_history(self, limit: int = 10) -> List[QueryHistory]:
        return self.query_history[-limit:]

    def _extract_table_name(self, query: str) -> str:
        query_upper = query.upper()
        if "FROM" in query_upper:
            from_idx = query_upper.index("FROM") + 4
            table_part = query[from_idx:].strip().split()[0]
            return table_part.replace(";", "").replace('"', "").replace("'", "")
        return "unknown"

    def _generate_query_hash(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()
