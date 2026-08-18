from dataclasses import dataclass
from typing import List, Optional, Set, Tuple, Dict, Any, Callable
import re


@dataclass
class TableReference:
    schema_name: str
    table_name: str
    alias: Optional[str] = None


class SQLQueryParser:
    """Safe, deterministic SQL parser and rewriter for MaskGate."""

    JOIN_KEYWORDS = (
        r"\bJOIN\b",
        r"\bLEFT\s+(?:OUTER\s+)?JOIN\b",
        r"\bRIGHT\s+(?:OUTER\s+)?JOIN\b",
        r"\bFULL\s+(?:OUTER\s+)?JOIN\b",
        r"\bINNER\s+JOIN\b",
        r"\bCROSS\s+JOIN\b",
    )

    def extract_tables(self, query: str) -> List[TableReference]:
        """
        Extract all table references (schema, table_name, alias) from a SELECT query.
        Handles FROM clauses, multi-table comma joins, and all JOIN variants.
        """
        tables: List[TableReference] = []
        seen: Set[Tuple[str, str]] = set()

        cleaned_query = self._remove_comments_and_strings(query)

        # 1. Extract FROM clause tables
        # Find FROM ... up to WHERE, GROUP BY, HAVING, ORDER BY, LIMIT, or end of query
        from_matches = re.finditer(r"\bFROM\b\s+([^()]+?)(?=\bWHERE\b|\bGROUP\b|\bHAVING\b|\bORDER\b|\bLIMIT\b|\bWINDOW\b|;|\Z)", cleaned_query, re.IGNORECASE)
        for match in from_matches:
            from_content = match.group(1).strip()
            # Split on commas to get comma-separated table lists (e.g. FROM table1 t1, table2 t2)
            # Also handle JOINs inside FROM clause
            parts = re.split(r",|\b(?:LEFT\s+(?:OUTER\s+)?|RIGHT\s+(?:OUTER\s+)?|FULL\s+(?:OUTER\s+)?|INNER\s+|CROSS\s+)?JOIN\b", from_content, flags=re.IGNORECASE)
            for part in parts:
                table_ref = self._parse_table_token(part)
                if table_ref and (table_ref.schema_name, table_ref.table_name) not in seen:
                    seen.add((table_ref.schema_name, table_ref.table_name))
                    tables.append(table_ref)

        # 2. Extract any explicit JOIN ... ON clauses anywhere in the query
        join_pattern = re.compile(r"\b(?:LEFT\s+(?:OUTER\s+)?|RIGHT\s+(?:OUTER\s+)?|FULL\s+(?:OUTER\s+)?|INNER\s+|CROSS\s+)?JOIN\s+([a-zA-Z0-9_.\"]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_\"]+))?", re.IGNORECASE)
        for match in join_pattern.finditer(cleaned_query):
            raw_table = match.group(1)
            raw_alias = match.group(2)
            schema_name, table_name = self._split_schema_table(raw_table)
            if table_name and (schema_name, table_name) not in seen:
                seen.add((schema_name, table_name))
                tables.append(TableReference(schema_name=schema_name, table_name=table_name, alias=raw_alias.strip('"') if raw_alias else None))

        return tables

    def has_outer_limit(self, query: str) -> bool:
        """
        Check if the query has an outer LIMIT clause (ignoring any subqueries enclosed in parentheses).
        """
        cleaned = self._remove_comments_and_strings(query)
        paren_depth = 0
        tokens = re.split(r"(\(|\)|\s+)", cleaned)

        for i, token in enumerate(tokens):
            if token == "(":
                paren_depth += 1
            elif token == ")":
                paren_depth = max(0, paren_depth - 1)
            elif paren_depth == 0 and token.upper() == "LIMIT":
                return True

        return False

    def apply_default_limit(self, query: str, default_limit: int = 100) -> str:
        """
        Safely applies a default LIMIT to a query if no outer LIMIT is present.
        Preserves WHERE, GROUP BY, HAVING, ORDER BY, JOIN, OFFSET, CTEs, comments, and semicolons.
        """
        if self.has_outer_limit(query):
            return query

        raw = query.rstrip()
        has_semicolon = raw.endswith(";")
        if has_semicolon:
            raw = raw[:-1].rstrip()

        # In PostgreSQL: SELECT ... OFFSET 20 LIMIT 100 or SELECT ... LIMIT 100 are both valid
        rewritten = f"{raw} LIMIT {default_limit}"
        if has_semicolon:
            rewritten += ";"
        return rewritten

    def rewrite_for_hidden_columns(
        self,
        query: str,
        hidden_columns_by_table: Dict[str, Set[str]],
        get_table_columns_fn: Callable[[str, str], List[str]],
    ) -> Tuple[str, bool]:
        """
        Safely rewrites SELECT * queries to explicit permitted column lists when
        hidden (DO_NOT_SHOW) columns exist for the referenced table(s).

        Returns: (rewritten_query, was_rewritten)
        If safe deterministic rewriting cannot be applied, returns (query, False).
        """
        if not hidden_columns_by_table:
            return query, False

        tables = self.extract_tables(query)
        if not tables:
            return query, False

        # Single table SELECT *
        if len(tables) == 1:
            tbl = tables[0]
            hidden_cols = hidden_columns_by_table.get(tbl.table_name, set())
            if not hidden_cols:
                return query, False

            # Check if query is simple SELECT * FROM ...
            cleaned = self._remove_comments_and_strings(query).strip()
            alias_prefix = f"{tbl.alias}\\." if tbl.alias else ""
            match = re.search(r"^\s*SELECT\s+(\*|" + alias_prefix + r"\*)\s+FROM\b", cleaned, re.IGNORECASE)
            if match:
                all_cols = get_table_columns_fn(tbl.table_name, tbl.schema_name)
                if not all_cols:
                    return query, False

                permitted_cols = [col for col in all_cols if col.lower() not in {h.lower() for h in hidden_cols}]
                if not permitted_cols:
                    return query, False

                prefix = f"{tbl.alias}." if tbl.alias else ""
                proj_str = ", ".join(f"{prefix}{col}" for col in permitted_cols)

                star_span = match.span(1)
                rewritten = query[:star_span[0]] + proj_str + query[star_span[1]:]
                return rewritten, True

        # Multi-table SELECT *
        if len(tables) > 1:
            cleaned = self._remove_comments_and_strings(query).strip()
            match = re.search(r"^\s*SELECT\s+\*\s+FROM\b", cleaned, re.IGNORECASE)
            if match:
                projected_parts: List[str] = []
                any_hidden = False
                for tbl in tables:
                    all_cols = get_table_columns_fn(tbl.table_name, tbl.schema_name)
                    hidden_cols = hidden_columns_by_table.get(tbl.table_name, set())
                    if hidden_cols:
                        any_hidden = True
                    permitted = [col for col in all_cols if col.lower() not in {h.lower() for h in hidden_cols}]
                    prefix = f"{tbl.alias}." if tbl.alias else f"{tbl.table_name}."
                    projected_parts.extend(f"{prefix}{col}" for col in permitted)

                if any_hidden and projected_parts:
                    proj_str = ", ".join(projected_parts)
                    select_match = re.search(r"^\s*SELECT\s+\*", query, re.IGNORECASE)
                    if select_match:
                        rewritten = query[:select_match.start()] + f"SELECT {proj_str}" + query[select_match.end():]
                        return rewritten, True

        return query, False

    def _parse_table_token(self, token: str) -> Optional[TableReference]:
        """Parse a table reference string like 'public.users AS u' or 'patients'."""
        token = token.strip()
        if not token or token.upper().startswith(("WHERE", "GROUP", "HAVING", "ORDER", "LIMIT", "ON", "(")):
            return None

        # Remove ON condition if attached
        token = re.split(r"\bON\b", token, flags=re.IGNORECASE)[0].strip()
        parts = token.split()
        if not parts:
            return None

        raw_table = parts[0]
        alias = None
        if len(parts) >= 2:
            if parts[1].upper() == "AS" and len(parts) >= 3:
                alias = parts[2]
            elif parts[1].upper() != "AS":
                alias = parts[1]

        schema_name, table_name = self._split_schema_table(raw_table)
        if not table_name:
            return None
        return TableReference(
            schema_name=schema_name,
            table_name=table_name,
            alias=alias.strip('"') if alias else None,
        )

    def _split_schema_table(self, raw: str) -> Tuple[str, str]:
        clean = raw.replace(";", "").replace('"', "").replace("'", "").strip()
        if "." in clean:
            s, t = clean.split(".", 1)
            return s.strip(), t.strip()
        return "public", clean

    def _remove_comments_and_strings(self, sql: str) -> str:
        """Remove SQL line comments, block comments, and string literals."""
        no_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
        no_line = re.sub(r"--.*$", " ", no_block, flags=re.MULTILINE)
        no_strings = re.sub(r"'(?:''|[^'])*'", "''", no_line)
        return no_strings
