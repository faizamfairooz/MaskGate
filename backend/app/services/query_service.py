from datetime import datetime, timezone
from typing import List, Any, Optional, Tuple, Set, Dict
import hashlib
import re
import time

from app.database.postgresql import db
from app.schemas.query import QueryResponse, QueryHistory
from app.services.masking_service import MaskingService
from app.schemas.masking import MaskingRequest
from app.utils.query_parser import SQLQueryParser, TableReference


class QueryService:
    """Service for executing SQL queries with deterministic data masking."""

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
        self.query_parser = SQLQueryParser()
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

        from app.config.settings import settings

        # 1. Discover referenced tables (multi-table / JOIN support)
        tables = self.query_parser.extract_tables(query)

        # 2. Apply safe default LIMIT if outer LIMIT is missing
        default_limit = getattr(settings, "DEFAULT_QUERY_LIMIT", 100)
        executed_query = self.query_parser.apply_default_limit(query, default_limit=default_limit)

        # 3. DO_NOT_SHOW query rewriting before PostgreSQL execution
        if apply_masking and tables:
            table_tuples = [(t.schema_name, t.table_name) for t in tables]
            active_policies = self.masking_service.policy_manager.get_policies_for_tables(table_tuples)
            hidden_by_table: Dict[str, Set[str]] = {}
            for p in active_policies:
                strat = (p.strategy or "").strip().upper()
                if strat in ("DO_NOT_SHOW", "HIDE", "HIDDEN", "DONOTSHOW"):
                    hidden_by_table.setdefault(p.table_name, set()).add(p.column_name)

            if hidden_by_table:
                def _get_table_cols(tbl: str, schema: str) -> List[str]:
                    try:
                        cols = db.get_table_schema(tbl, schema=schema)
                        return [c["column_name"] for c in cols]
                    except Exception:
                        return []

                rewritten, was_rewritten = self.query_parser.rewrite_for_hidden_columns(
                    executed_query, hidden_by_table, _get_table_cols
                )
                if was_rewritten:
                    executed_query = rewritten

        start_time = time.time()
        results = db.execute_query(executed_query)

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
        llm_detection_enabled = False
        llm_detection_summary = None

        if apply_masking or mask_suspicious:
            schema_name, table_name = self._extract_table_and_schema(query)
            table_dicts = [{"schema": t.schema_name, "table": t.table_name} for t in tables] if tables else None

            runtime_enabled = getattr(settings, "ENABLE_RUNTIME_DETECTION", True)
            effective_auto_detect = mask_suspicious and runtime_enabled

            if effective_auto_detect:
                from app.ai.llm import llm_client
                llm_detection_enabled = llm_client.is_available()

            masking_result = self.masking_service.apply_masking(
                MaskingRequest(
                    schema_name=schema_name,
                    table_name=table_name,
                    tables=table_dicts,
                    columns=columns,
                    data=rows,
                    policy_ids=[] if not apply_masking else None,
                    auto_detect=effective_auto_detect,
                )
            )
            masked_data = masking_result.masked_data
            masked_columns = masking_result.masked_columns
            runtime_summary = masking_result.runtime_detection_summary

            # Extract LLM-specific summary if available
            if runtime_summary and "LLM" in runtime_summary:
                llm_detection_summary = runtime_summary

        execution_time = time.time() - start_time
        query_hash = self._generate_query_hash(query)

        self.query_history.append(
            QueryHistory(
                query=query,
                executed_at=datetime.now(timezone.utc),
                execution_time=execution_time,
                row_count=len(masked_data),
                masked=apply_masking,
            )
        )

        return QueryResponse(
            columns=columns,
            rows=masked_data,
            row_count=len(masked_data),
            execution_time=execution_time,
            masked_columns=masked_columns,
            query_hash=query_hash,
            runtime_detection_summary=runtime_summary,
            llm_detection_enabled=llm_detection_enabled,
            llm_detection_summary=llm_detection_summary,
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

    def _extract_table_and_schema(self, query: str) -> Tuple[str, str]:
        """
        Extract schema_name and table_name from simple SELECT queries.
        Supports:
          - table
          - schema.table
        """
        tables = self.query_parser.extract_tables(query)
        if tables:
            return tables[0].schema_name, tables[0].table_name

        query_upper = query.upper()
        if "FROM" in query_upper:
            from_idx = query_upper.index("FROM") + 4
            table_part = query[from_idx:].strip().split()[0]
            clean_part = table_part.replace(";", "").replace('"', "").replace("'", "")
            if "." in clean_part:
                schema_name, table_name = clean_part.split(".", 1)
                return schema_name.strip(), table_name.strip()
            return "public", clean_part.strip()
        return "public", "unknown"

    def _extract_table_name(self, query: str) -> str:
        _, table_name = self._extract_table_and_schema(query)
        return table_name

    def _generate_query_hash(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()

