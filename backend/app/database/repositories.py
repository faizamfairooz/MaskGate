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

    def delete_policy(self, policy_id: int) -> bool:
        count = db.execute_update(
            "UPDATE masking_policies SET is_active = FALSE, status = 'DISABLED', updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (policy_id,),
        )
        return count > 0

    def get_policies_for_table(
        self, table_name: str, columns: List[str], schema_name: str = "public"
    ) -> List[MaskingPolicy]:
        if not columns:
            return []
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"""
            SELECT * FROM masking_policies
            WHERE is_active = TRUE
              AND UPPER(status) = 'ACTIVE'
              AND table_name = %s
              AND COALESCE(schema_name, 'public') = %s
              AND LOWER(column_name) IN ({placeholders})
        """
        lowered_cols = [c.lower() for c in columns]
        rows = db.execute_query(query, (table_name, schema_name, *lowered_cols))
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
                (schema_name, table_name, column_name, data_type, sensitivity, recommended_strategy, rationale, source, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            recommended_strategy=row["recommended_strategy"],
            rationale=row.get("rationale") or "",
            source=row.get("source") or "llm",
            status=row.get("status") or "PENDING",
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
