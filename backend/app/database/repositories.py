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
                (name, description, table_name, column_name, strategy, parameters, status, source, is_active)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, TRUE)
            ON CONFLICT (table_name, column_name) DO UPDATE
            SET name = EXCLUDED.name,
                description = EXCLUDED.description,
                strategy = EXCLUDED.strategy,
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
                policy.name,
                policy.description,
                policy.table_name,
                policy.column_name,
                policy.strategy,
                params_json,
                policy.status or "approved",
                policy.source or "manual",
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

    def get_all_policies(self) -> List[MaskingPolicy]:
        rows = db.execute_query(
            "SELECT * FROM masking_policies WHERE is_active = TRUE ORDER BY id"
        )
        return [self._row_to_policy(r) for r in rows]

    def delete_policy(self, policy_id: int) -> bool:
        count = db.execute_update(
            "UPDATE masking_policies SET is_active = FALSE WHERE id = %s",
            (policy_id,),
        )
        return count > 0

    def get_policies_for_table(self, table_name: str, columns: List[str]) -> List[MaskingPolicy]:
        if not columns:
            return []
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"""
            SELECT * FROM masking_policies
            WHERE is_active = TRUE
              AND table_name = %s
              AND column_name IN ({placeholders})
        """
        rows = db.execute_query(query, (table_name, *columns))
        return [self._row_to_policy(r) for r in rows]

    def _row_to_policy(self, row: Dict[str, Any]) -> MaskingPolicy:
        params = row.get("parameters")
        if isinstance(params, str):
            params = json.loads(params)
        return MaskingPolicy(
            id=row["id"],
            name=row["name"],
            description=row.get("description") or "",
            table_name=row["table_name"],
            column_name=row["column_name"],
            strategy=row["strategy"],
            parameters=params or {},
            status=row.get("status") or "approved",
            source=row.get("source") or "manual",
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


class RecommendationRepository:
    """PostgreSQL-backed AI recommendation queue."""

    def create(self, rec: MaskingRecommendation) -> MaskingRecommendation:
        query = """
            INSERT INTO masking_recommendations
                (table_name, column_name, sensitivity, recommended_strategy, rationale, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """
        rows = db.execute_query(
            query,
            (
                rec.table_name,
                rec.column_name,
                rec.sensitivity,
                rec.recommended_strategy,
                rec.rationale,
                rec.status or "pending",
            ),
        )
        if rows:
            rec.id = rows[0]["id"]
            rec.created_at = rows[0]["created_at"]
            rec.updated_at = rows[0]["updated_at"]
        return rec

    def list_recommendations(
        self,
        status: Optional[str] = None,
        table_name: Optional[str] = None,
    ) -> List[MaskingRecommendation]:
        conditions = []
        params: List[Any] = []
        if status:
            conditions.append("status = %s")
            params.append(status)
        if table_name:
            conditions.append("table_name = %s")
            params.append(table_name)
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
            (status, rec_id),
        )
        return self.get(rec_id)

    def _row_to_rec(self, row: Dict[str, Any]) -> MaskingRecommendation:
        return MaskingRecommendation(
            id=row["id"],
            table_name=row["table_name"],
            column_name=row["column_name"],
            sensitivity=row["sensitivity"],
            recommended_strategy=row["recommended_strategy"],
            rationale=row.get("rationale"),
            status=row.get("status") or "pending",
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
