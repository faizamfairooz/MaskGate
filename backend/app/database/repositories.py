import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.database.postgresql import db
from app.schemas.masking import MaskingPolicy, MaskingRecommendation


class PolicyRepository:
    """PostgreSQL-backed masking policy storage."""

    def create_policy(self, policy: MaskingPolicy) -> MaskingPolicy:
        query = """
            INSERT INTO masking_policies
                (name, description, schema_name, table_name, column_name, strategy, sensitivity, parameters, status, source, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, TRUE)
            ON CONFLICT (table_name, column_name) DO UPDATE
            SET name = EXCLUDED.name,
                description = EXCLUDED.description,
                schema_name = EXCLUDED.schema_name,
                strategy = EXCLUDED.strategy,
                sensitivity = EXCLUDED.sensitivity,
                parameters = EXCLUDED.parameters,
                status = EXCLUDED.status,
                source = EXCLUDED.source,
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, created_at, updated_at
        """
        params_json = json.dumps(policy.parameters or {})
        rows = db.execute_query(
            query,
            (
                policy.name or f"{policy.table_name}.{policy.column_name}",
                policy.description or "",
                policy.schema_name or "public",
                policy.table_name,
                policy.column_name,
                policy.strategy,
                policy.sensitivity or "MEDIUM",
                params_json,
                policy.status or "ACTIVE",
                policy.source or "ai_recommendation",
            ),
        )
        if rows:
            policy.id = rows[0]["id"]
            policy.created_at = rows[0]["created_at"]
            policy.updated_at = rows[0]["updated_at"]
            if policy.is_active and (policy.status or "ACTIVE").upper() == "ACTIVE":
                try:
                    from app.database.db_masking_functions import DBMaskingFunctionManager
                    DBMaskingFunctionManager.create_or_replace_policy_function(policy)
                except Exception as e:
                    # Roll back inserted policy row to prevent inconsistent orphaned active policy
                    db.execute_update("DELETE FROM masking_policies WHERE id = %s", (policy.id,))
                    raise RuntimeError(f"Database masking function creation failed for policy {policy.id}: {e}")
        return policy

    def get_policy(self, policy_id: int) -> Optional[MaskingPolicy]:
        rows = db.execute_query(
            "SELECT * FROM masking_policies WHERE id = %s",
            (policy_id,),
        )
        return self._row_to_policy(rows[0]) if rows else None

    def find_active_policy(
        self, table_name: str, column_name: str, schema_name: str = "public"
    ) -> Optional[MaskingPolicy]:
        rows = db.execute_query(
            """
            SELECT * FROM masking_policies
            WHERE is_active = TRUE
              AND UPPER(status) = 'ACTIVE'
              AND table_name = %s
              AND column_name = %s
              AND COALESCE(schema_name, 'public') = %s
            LIMIT 1
            """,
            (table_name, column_name, schema_name),
        )
        return self._row_to_policy(rows[0]) if rows else None

    def get_all_policies(self, status: Optional[str] = "ACTIVE") -> List[MaskingPolicy]:
        if status:
            rows = db.execute_query(
                "SELECT * FROM masking_policies WHERE is_active = TRUE AND UPPER(status) = %s ORDER BY id",
                (status.upper(),),
            )
        else:
            rows = db.execute_query(
                "SELECT * FROM masking_policies WHERE is_active = TRUE ORDER BY id"
            )
        return [self._row_to_policy(r) for r in rows]

    def update_policy(self, policy_id: int, updates: Dict[str, Any]) -> Optional[MaskingPolicy]:
        existing = self.get_policy(policy_id)
        if not existing:
            return None

        set_clauses = []
        params = []

        if "name" in updates and updates["name"] is not None:
            set_clauses.append("name = %s")
            params.append(updates["name"])
        if "description" in updates and updates["description"] is not None:
            set_clauses.append("description = %s")
            params.append(updates["description"])
        if "strategy" in updates and updates["strategy"] is not None:
            set_clauses.append("strategy = %s")
            params.append(updates["strategy"])
        if "sensitivity" in updates and updates["sensitivity"] is not None:
            set_clauses.append("sensitivity = %s")
            params.append(updates["sensitivity"])
        if "parameters" in updates and updates["parameters"] is not None:
            set_clauses.append("parameters = %s::jsonb")
            params.append(json.dumps(updates["parameters"]))
        if "status" in updates and updates["status"] is not None:
            set_clauses.append("status = %s")
            params.append(updates["status"])
        if "is_active" in updates and updates["is_active"] is not None:
            set_clauses.append("is_active = %s")
            params.append(bool(updates["is_active"]))

        if not set_clauses:
            return existing

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(policy_id)

        query = f"""
            UPDATE masking_policies
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING *
        """
        rows = db.execute_query(query, tuple(params))
        updated = self._row_to_policy(rows[0]) if rows else None
        if updated:
            from app.database.db_masking_functions import DBMaskingFunctionManager
            if updated.is_active and (updated.status or "ACTIVE").upper() == "ACTIVE":
                try:
                    DBMaskingFunctionManager.create_or_replace_policy_function(updated)
                except Exception as e:
                    # Rollback database policy to existing state
                    self._restore_policy(existing)
                    if existing.is_active and (existing.status or "ACTIVE").upper() == "ACTIVE":
                        try:
                            DBMaskingFunctionManager.create_or_replace_policy_function(existing)
                        except Exception:
                            pass
                    raise RuntimeError(f"Database masking function update failed for policy {policy_id}: {e}")
            else:
                DBMaskingFunctionManager.drop_policy_function(policy_id)
        return updated

    def _restore_policy(self, policy: MaskingPolicy) -> None:
        """Rollback helper to restore policy state after failed DB function update."""
        if not policy.id:
            return
        query = """
            UPDATE masking_policies
            SET name = %s,
                description = %s,
                schema_name = %s,
                table_name = %s,
                column_name = %s,
                strategy = %s,
                sensitivity = %s,
                parameters = %s::jsonb,
                status = %s,
                source = %s,
                is_active = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        db.execute_query(
            query,
            (
                policy.name,
                policy.description,
                policy.schema_name or "public",
                policy.table_name,
                policy.column_name,
                policy.strategy,
                policy.sensitivity or "MEDIUM",
                json.dumps(policy.parameters or {}),
                policy.status or "ACTIVE",
                policy.source or "ai_recommendation",
                bool(policy.is_active),
                policy.id,
            ),
        )

    def reactivate_policy(self, policy_id: int) -> Optional[MaskingPolicy]:
        rows = db.execute_query(
            """
            UPDATE masking_policies
            SET is_active = TRUE, status = 'ACTIVE', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
            """,
            (policy_id,),
        )
        reactivated = self._row_to_policy(rows[0]) if rows else None
        if reactivated:
            from app.database.db_masking_functions import DBMaskingFunctionManager
            try:
                DBMaskingFunctionManager.create_or_replace_policy_function(reactivated)
            except Exception as e:
                # Rollback to disabled state
                db.execute_update(
                    "UPDATE masking_policies SET is_active = FALSE, status = 'DISABLED', updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (policy_id,),
                )
                raise RuntimeError(f"Database masking function recreation failed during reactivation for policy {policy_id}: {e}")
        return reactivated

    def delete_policy(self, policy_id: int) -> bool:
        count = db.execute_update(
            "UPDATE masking_policies SET is_active = FALSE, status = 'DISABLED', updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (policy_id,),
        )
        if count > 0:
            from app.database.db_masking_functions import DBMaskingFunctionManager
            DBMaskingFunctionManager.drop_policy_function(policy_id)
        return count > 0

    def get_policies_for_table(
        self, table_name: str, columns: List[str], schema_name: str = "public"
    ) -> List[MaskingPolicy]:
        return self.get_policies_for_tables([(schema_name, table_name)], columns)

    def get_policies_for_tables(
        self, tables: List[Tuple[str, str]], columns: Optional[List[str]] = None
    ) -> List[MaskingPolicy]:
        if not tables:
            return []
        table_conditions = []
        params: List[Any] = []
        for schema_name, table_name in tables:
            table_conditions.append("(table_name = %s AND COALESCE(schema_name, 'public') = %s)")
            params.extend([table_name, schema_name or "public"])

        tables_clause = " OR ".join(table_conditions)
        cols_clause = ""
        if columns:
            placeholders = ", ".join(["%s"] * len(columns))
            cols_clause = f"AND LOWER(column_name) IN ({placeholders})"
            params.extend([c.lower() for c in columns])

        query = f"""
            SELECT * FROM masking_policies
            WHERE is_active = TRUE
              AND UPPER(status) = 'ACTIVE'
              AND ({tables_clause})
              {cols_clause}
            ORDER BY id
        """
        rows = db.execute_query(query, tuple(params))
        return [self._row_to_policy(r) for r in rows]

    def _row_to_policy(self, row: Dict[str, Any]) -> MaskingPolicy:
        params = row.get("parameters")
        if isinstance(params, str):
            params = json.loads(params)
        return MaskingPolicy(
            id=row["id"],
            name=row["name"],
            description=row.get("description") or "",
            schema_name=row.get("schema_name") or "public",
            table_name=row["table_name"],
            column_name=row["column_name"],
            strategy=row["strategy"],
            sensitivity=row.get("sensitivity") or "MEDIUM",
            parameters=params or {},
            status=row.get("status") or "ACTIVE",
            source=row.get("source") or "ai_recommendation",
            is_active=bool(row.get("is_active", True)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


class RecommendationRepository:
    """PostgreSQL-backed AI recommendation queue."""

    def create(self, rec: MaskingRecommendation) -> MaskingRecommendation:
        query = """
            INSERT INTO masking_recommendations
                (schema_name, table_name, column_name, data_type, sensitivity, confidence, recommended_strategy, rationale, source, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """
        rows = db.execute_query(
            query,
            (
                rec.schema_name or "public",
                rec.table_name,
                rec.column_name,
                rec.data_type or "text",
                rec.sensitivity or "MEDIUM",
                rec.confidence or "HIGH",
                rec.recommended_strategy,
                rec.rationale or "",
                rec.source or "llm",
                rec.status or "PENDING",
            ),
        )
        if rows:
            rec.id = rows[0]["id"]
            rec.created_at = rows[0]["created_at"]
            rec.updated_at = rows[0]["updated_at"]
        return rec

    def create_bulk(self, recs: List[MaskingRecommendation]) -> List[MaskingRecommendation]:
        created = []
        for rec in recs:
            created.append(self.create(rec))
        return created

    def list_recommendations(
        self,
        status: Optional[str] = None,
        table_name: Optional[str] = None,
        schema_name: Optional[str] = None,
    ) -> List[MaskingRecommendation]:
        conditions = []
        params: List[Any] = []
        if status:
            conditions.append("UPPER(status) = %s")
            params.append(status.upper())
        if table_name:
            conditions.append("table_name = %s")
            params.append(table_name)
        if schema_name:
            conditions.append("COALESCE(schema_name, 'public') = %s")
            params.append(schema_name)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = db.execute_query(
            f"SELECT * FROM masking_recommendations {where} ORDER BY id DESC",
            tuple(params) if params else None,
        )
        return [self._row_to_rec(r) for r in rows]

    def get(self, rec_id: int) -> Optional[MaskingRecommendation]:
        rows = db.execute_query(
            "SELECT * FROM masking_recommendations WHERE id = %s",
            (rec_id,),
        )
        return self._row_to_rec(rows[0]) if rows else None

    def update_status(self, rec_id: int, status: str) -> Optional[MaskingRecommendation]:
        db.execute_update(
            """
            UPDATE masking_recommendations
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (status.upper(), rec_id),
        )
        return self.get(rec_id)

    def _row_to_rec(self, row: Dict[str, Any]) -> MaskingRecommendation:
        return MaskingRecommendation(
            id=row["id"],
            schema_name=row.get("schema_name") or "public",
            table_name=row["table_name"],
            column_name=row["column_name"],
            data_type=row.get("data_type") or "text",
            sensitivity=row.get("sensitivity") or "MEDIUM",
            confidence=row.get("confidence") or "HIGH",
            recommended_strategy=row["recommended_strategy"],
            rationale=row.get("rationale") or "",
            source=row.get("source") or "llm",
            status=row.get("status") or "PENDING",
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
