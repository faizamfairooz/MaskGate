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

    def _split_projections(self, proj_str: str) -> List[str]:
        """Split projection string on top-level commas outside parentheses and quotes."""
        items = []
        current = []
        paren_depth = 0
        in_quote = False
        quote_char = ""

        for char in proj_str:
            if char in ("'", '"'):
                if in_quote and char == quote_char:
                    in_quote = False
                elif not in_quote:
                    in_quote = True
                    quote_char = char
                current.append(char)
            elif in_quote:
                current.append(char)
            elif char == "(":
                paren_depth += 1
                current.append(char)
            elif char == ")":
                paren_depth = max(0, paren_depth - 1)
                current.append(char)
            elif char == "," and paren_depth == 0:
                item = "".join(current).strip()
                if item:
                    items.append(item)
                current = []
            else:
                current.append(char)

        last = "".join(current).strip()
        if last:
            items.append(last)

        return items

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

    def rewrite_query_for_db_masking(
        self,
        query: str,
        active_policies: List[Any],
        get_table_columns_fn: Callable[[str, str], List[str]],
    ) -> Tuple[str, List[str], bool]:
        """
        Rewrites a SELECT query so that PostgreSQL executes stored masking functions
        directly for columns protected by active masking policies.

        Returns: (rewritten_query, db_masked_columns, was_rewritten)
        """
        if not active_policies:
            return query, [], False

        tables = self.extract_tables(query)
        if not tables:
            return query, [], False

        # Build policy lookup and ensure DB functions exist
        policy_map: Dict[Tuple[str, str], Any] = {}
        col_policy_map: Dict[str, Any] = {}
        for p in active_policies:
            t_name = (p.table_name or "").strip().lower()
            c_name = (p.column_name or "").strip().lower()
            policy_map[(t_name, c_name)] = p
            col_policy_map[c_name] = p
            if getattr(p, "is_active", True) and (getattr(p, "status", "ACTIVE") or "").upper() == "ACTIVE" and p.id:
                try:
                    from app.database.db_masking_functions import DBMaskingFunctionManager
                    DBMaskingFunctionManager.create_or_replace_policy_function(p)
                except Exception:
                    pass

        alias_to_table: Dict[str, TableReference] = {}
        for t in tables:
            if t.alias:
                alias_to_table[t.alias.lower()] = t
            alias_to_table[t.table_name.lower()] = t

        # Locate SELECT ... FROM
        cleaned = self._remove_comments_and_strings(query)
        select_match = re.search(r"^\s*SELECT\s+(DISTINCT\s+)?(.*?)\s+FROM\b", cleaned, re.IGNORECASE | re.DOTALL)
        if not select_match:
            return query, [], False

        distinct_part = select_match.group(1) or ""
        proj_str = select_match.group(2).strip()
        from_idx = select_match.end() - 4  # index of FROM in cleaned query

        raw_select_match = re.search(r"^\s*SELECT\s+(DISTINCT\s+)?(.*?)\s+FROM\b", query, re.IGNORECASE | re.DOTALL)
        if not raw_select_match:
            return query, [], False

        proj_items = self._split_projections(proj_str)
        if not proj_items:
            return query, [], False

        new_proj_parts: List[str] = []
        db_masked_columns: List[str] = []
        any_modified = False

        for item in proj_items:
            item_clean = item.strip()

            # Case A: Wildcard `*`
            if item_clean == "*":
                expanded_cols: List[str] = []
                for tbl in tables:
                    all_cols = get_table_columns_fn(tbl.table_name, tbl.schema_name)
                    prefix = f"{tbl.alias}." if tbl.alias else (f"{tbl.table_name}." if len(tables) > 1 else "")
                    for col in all_cols:
                        policy = policy_map.get((tbl.table_name.lower(), col.lower()))
                        if policy and getattr(policy, "is_active", True) and (getattr(policy, "status", "ACTIVE") or "").upper() == "ACTIVE":
                            if not isinstance(policy.id, int) or isinstance(policy.id, bool) or policy.id <= 0:
                                expanded_cols.append(f"{prefix}{col}")
                                continue
                            strat = (policy.strategy or "").strip().upper()
                            if strat in ("DO_NOT_SHOW", "HIDE", "HIDDEN", "DONOTSHOW"):
                                # Omit hidden columns from SELECT *
                                db_masked_columns.append(col)
                                any_modified = True
                                continue
                            else:
                                fn_name = f"maskgate_policy_{policy.id}"
                                expanded_cols.append(f"{fn_name}({prefix}{col}::text) AS {col}")
                                db_masked_columns.append(col)
                                any_modified = True
                        else:
                            expanded_cols.append(f"{prefix}{col}")

                if expanded_cols:
                    new_proj_parts.append(", ".join(expanded_cols))
                    any_modified = True
                continue

            # Case B: Table-specific wildcard `alias.*` or `table.*`
            tbl_star_match = re.match(r"^([a-zA-Z0-9_\"]+)\.\*$", item_clean)
            if tbl_star_match:
                tbl_key = tbl_star_match.group(1).replace('"', "").lower()
                matched_tbl = alias_to_table.get(tbl_key)
                if matched_tbl:
                    all_cols = get_table_columns_fn(matched_tbl.table_name, matched_tbl.schema_name)
                    prefix = f"{tbl_star_match.group(1)}."
                    expanded_cols = []
                    for col in all_cols:
                        policy = policy_map.get((matched_tbl.table_name.lower(), col.lower()))
                        if policy and getattr(policy, "is_active", True) and (getattr(policy, "status", "ACTIVE") or "").upper() == "ACTIVE":
                            if not isinstance(policy.id, int) or isinstance(policy.id, bool) or policy.id <= 0:
                                expanded_cols.append(f"{prefix}{col}")
                                continue
                            strat = (policy.strategy or "").strip().upper()
                            if strat in ("DO_NOT_SHOW", "HIDE", "HIDDEN", "DONOTSHOW"):
                                db_masked_columns.append(col)
                                any_modified = True
                                continue
                            else:
                                fn_name = f"maskgate_policy_{policy.id}"
                                expanded_cols.append(f"{fn_name}({prefix}{col}::text) AS {col}")
                                db_masked_columns.append(col)
                                any_modified = True
                        else:
                            expanded_cols.append(f"{prefix}{col}")
                    if expanded_cols:
                        new_proj_parts.append(", ".join(expanded_cols))
                        any_modified = True
                        continue

            # Case C: Explicit single column reference (e.g. `col`, `t.col`, `col AS c`, `t.col AS c`)
            col_match = re.match(
                r"^(?:(?P<tbl>[a-zA-Z0-9_\"]+)\.)?(?P<col>[a-zA-Z0-9_\"]+)(?:\s+(?:AS\s+)?(?P<alias>[a-zA-Z0-9_\"]+))?$",
                item_clean,
                re.IGNORECASE,
            )
            if col_match:
                prefix = col_match.group("tbl")
                col_name = col_match.group("col").replace('"', "")
                alias_name = col_match.group("alias")
                effective_alias = alias_name.replace('"', "") if alias_name else col_name

                # Resolve target policy
                policy = None
                if prefix:
                    prefix_clean = prefix.replace('"', "").lower()
                    matched_tbl = alias_to_table.get(prefix_clean)
                    if matched_tbl:
                        policy = policy_map.get((matched_tbl.table_name.lower(), col_name.lower()))
                else:
                    # Search across tables
                    for tbl in tables:
                        candidate = policy_map.get((tbl.table_name.lower(), col_name.lower()))
                        if candidate:
                            policy = candidate
                            break
                    if not policy:
                        policy = col_policy_map.get(col_name.lower())

                if policy and getattr(policy, "is_active", True) and (getattr(policy, "status", "ACTIVE") or "").upper() == "ACTIVE":
                    if not isinstance(policy.id, int) or isinstance(policy.id, bool) or policy.id <= 0:
                        new_proj_parts.append(item_clean)
                        continue
                    strat = (policy.strategy or "").strip().upper()
                    target_expr = f"{prefix}.{col_name}" if prefix else col_name
                    if strat in ("DO_NOT_SHOW", "HIDE", "HIDDEN", "DONOTSHOW"):
                        new_proj_parts.append(f"'[HIDDEN]'::text AS {effective_alias}")
                        db_masked_columns.append(effective_alias)
                        any_modified = True
                    else:
                        fn_name = f"maskgate_policy_{policy.id}"
                        new_proj_parts.append(f"{fn_name}({target_expr}::text) AS {effective_alias}")
                        db_masked_columns.append(effective_alias)
                        any_modified = True
                    continue

            # Case D: Other expressions (keep untouched)
            new_proj_parts.append(item_clean)

        if any_modified and new_proj_parts:
            new_proj_str = ", ".join(new_proj_parts)
            # Find the projection range in original query
            start_pos = raw_select_match.start(2)
            end_pos = raw_select_match.end(2)
            rewritten_query = query[:start_pos] + new_proj_str + query[end_pos:]
            return rewritten_query, db_masked_columns, True

        return query, [], False

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
