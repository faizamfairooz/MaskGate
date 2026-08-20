import time
from typing import Any, Dict, List, Optional

from app.database.postgresql import db
from app.database.repositories import RecommendationRepository
from app.database.db_masking_functions import DBMaskingFunctionManager
from app.masking.engine import MaskingEngine
from app.masking.policies import PolicyManager
from app.schemas.masking import (
    MaskingPolicy,
    MaskingPolicyUpdate,
    MaskingRecommendation,
    MaskingRequest,
    MaskingResult,
)


class MaskingService:
    """Service for managing AI recommendations and approved masking policies."""

    def __init__(self):
        self.engine = MaskingEngine()
        self.policy_manager = PolicyManager()
        self.recommendation_repo = RecommendationRepository()
        self.db_fn_manager = DBMaskingFunctionManager()
        # Initialize base PostgreSQL masking functions and sync active policies
        try:
            self.db_fn_manager.init_base_functions()
            active_policies = self.policy_manager.get_all_policies(status="ACTIVE")
            self.db_fn_manager.sync_all_active_policies(active_policies)
        except Exception:
            pass

    def validate_table_and_column(
        self, table_name: str, column_name: str, schema_name: str = "public"
    ) -> None:
        """Validate that the target schema, table, and column exist in PostgreSQL."""
        if not db.table_exists(table_name, schema=schema_name):
            raise ValueError(f"Table '{table_name}' does not exist in schema '{schema_name}'")

        table_columns = db.get_table_schema(table_name, schema=schema_name)
        existing_cols = {col["column_name"] for col in table_columns}
        if column_name not in existing_cols:
            raise ValueError(
                f"Column '{column_name}' does not exist in table '{table_name}' (schema '{schema_name}')"
            )

    def create_policy(self, policy: MaskingPolicy) -> MaskingPolicy:
        """
        Create or update a masking policy with PostgreSQL table and column validation,
        and generate the corresponding PostgreSQL masking function.
        """
        target_schema = policy.schema_name or "public"
        if not policy.table_name or not policy.table_name.strip():
            raise ValueError("Table name is required")
        if not policy.column_name or not policy.column_name.strip():
            raise ValueError("Column name is required")
        if not policy.strategy or not policy.strategy.strip():
            raise ValueError("Masking strategy is required")

        available_strategies = self.get_available_strategies()
        if policy.strategy.upper() not in [s.upper() for s in available_strategies.keys()]:
            raise ValueError(
                f"Invalid masking strategy '{policy.strategy}'. Must be one of: {list(available_strategies.keys())}"
            )

        self.validate_table_and_column(
            policy.table_name.strip(), policy.column_name.strip(), schema_name=target_schema
        )

        if not policy.name:
            policy.name = f"{policy.table_name}.{policy.column_name}"
        if not policy.source:
            policy.source = "admin_manual"
        policy.status = policy.status or "ACTIVE"
        policy.is_active = True

        created = self.policy_manager.create_policy(policy)
        return created

    def update_policy(
        self, policy_id: int, update_data: MaskingPolicyUpdate | Dict[str, Any]
    ) -> MaskingPolicy:
        """
        Edit an existing masking policy, validate new strategy/parameters,
        and immediately update the corresponding PostgreSQL masking function.
        """
        existing = self.get_policy(policy_id)
        if not existing:
            raise ValueError(f"Policy with ID {policy_id} not found")

        updates = update_data.model_dump(exclude_unset=True) if isinstance(update_data, MaskingPolicyUpdate) else dict(update_data)

        # Validate strategy if being updated
        if "strategy" in updates and updates["strategy"]:
            new_strat = updates["strategy"]
            available_strategies = self.get_available_strategies()
            if new_strat.upper() not in [s.upper() for s in available_strategies.keys()]:
                raise ValueError(
                    f"Invalid masking strategy '{new_strat}'. Must be one of: {list(available_strategies.keys())}"
                )

        updated_policy = self.policy_manager.update_policy(policy_id, updates)
        if not updated_policy:
            raise ValueError(f"Failed to update policy {policy_id}")

        return updated_policy

    def reactivate_policy(self, policy_id: int) -> MaskingPolicy:
        """Reactivate a deactivated policy and recreate its PostgreSQL function."""
        existing = self.get_policy(policy_id)
        if not existing:
            raise ValueError(f"Policy with ID {policy_id} not found")

        reactivated = self.policy_manager.reactivate_policy(policy_id)
        if not reactivated:
            raise ValueError(f"Failed to reactivate policy {policy_id}")

        return reactivated

    def get_all_policies(self, status: Optional[str] = "ACTIVE") -> List[MaskingPolicy]:
        """Retrieve all active masking policies."""
        return self.policy_manager.get_all_policies(status=status)

    def get_policy(self, policy_id: int) -> Optional[MaskingPolicy]:
        return self.policy_manager.get_policy(policy_id)

    def delete_policy(self, policy_id: int) -> None:
        self.policy_manager.delete_policy(policy_id)

    def list_recommendations(
        self,
        status: Optional[str] = None,
        table_name: Optional[str] = None,
        schema_name: Optional[str] = None,
    ) -> List[MaskingRecommendation]:
        return self.recommendation_repo.list_recommendations(
            status=status, table_name=table_name, schema_name=schema_name
        )

    def approve_recommendation(self, rec_id: int) -> MaskingPolicy:
        """
        Approve a pending recommendation:
        1. Verify recommendation exists and is PENDING.
        2. Validate table and column exist in PostgreSQL.
        3. Verify no active duplicate policy already exists.
        4. Create ACTIVE MaskingPolicy.
        5. Create corresponding PostgreSQL stored function.
        6. Update recommendation status to APPROVED.
        """
        rec = self.recommendation_repo.get(rec_id)
        if rec is None:
            raise ValueError(f"Recommendation {rec_id} not found")
        if rec.status.upper() != "PENDING":
            raise ValueError(f"Recommendation {rec_id} is not pending (current status: {rec.status})")

        target_schema = rec.schema_name or "public"
        self.validate_table_and_column(rec.table_name, rec.column_name, schema_name=target_schema)

        available_strategies = self.get_available_strategies()
        if not rec.recommended_strategy or rec.recommended_strategy.upper() not in [
            s.upper() for s in available_strategies.keys()
        ]:
            raise ValueError(
                f"Invalid masking strategy '{rec.recommended_strategy}'. Must be one of: {list(available_strategies.keys())}"
            )

        existing_active = self.policy_manager.find_active_policy(
            table_name=rec.table_name, column_name=rec.column_name, schema_name=target_schema
        )
        if existing_active:
            raise ValueError(
                f"An active masking policy already exists for {rec.table_name}.{rec.column_name}"
            )

        policy = MaskingPolicy(
            name=f"{rec.table_name}.{rec.column_name}",
            description=rec.rationale or "Approved AI recommendation",
            schema_name=target_schema,
            table_name=rec.table_name,
            column_name=rec.column_name,
            strategy=rec.recommended_strategy,
            sensitivity=rec.sensitivity,
            parameters={},
            status="ACTIVE",
            source="ai_recommendation",
            is_active=True,
        )
        created_policy = self.policy_manager.create_policy(policy)
        self.recommendation_repo.update_status(rec_id, "APPROVED")
        return created_policy

    def reject_recommendation(self, rec_id: int) -> MaskingRecommendation:
        """
        Reject a pending recommendation:
        1. Verify recommendation exists and is PENDING.
        2. Update status to REJECTED.
        3. Never create a policy.
        """
        rec = self.recommendation_repo.get(rec_id)
        if rec is None:
            raise ValueError(f"Recommendation {rec_id} not found")
        if rec.status.upper() != "PENDING":
            raise ValueError(f"Recommendation {rec_id} is not pending (current status: {rec.status})")

        updated = self.recommendation_repo.update_status(rec_id, "REJECTED")
        if updated is None:
            raise ValueError(f"Recommendation {rec_id} not found")
        return updated

    def analyze_and_queue_recommendations(
        self, schema_name: str = "public", table_name: Optional[str] = None
    ) -> List[MaskingRecommendation]:
        """
        Trigger AI/heuristic schema analysis and persist structured recommendations
        as PENDING records in PostgreSQL for administrator review.
        """
        from app.services.schema_service import SchemaService
        from app.ai.schema_analyzer import SchemaAnalyzer

        schema_service = SchemaService()
        schema_analyzer = SchemaAnalyzer()

        target_tables = (
            [table_name] if table_name else schema_service.get_all_tables(schema=schema_name)
        )
        queued: List[MaskingRecommendation] = []

        for tbl in target_tables:
            table_schema = schema_service.get_table_schema(tbl, schema=schema_name)
            analysis_recs = schema_analyzer.analyze_table_schema(tbl, table_schema.columns)

            for col_rec in analysis_recs:
                sensitivity_str = (
                    col_rec.sensitivity.value
                    if hasattr(col_rec.sensitivity, "value")
                    else str(col_rec.sensitivity)
                )
                strategy_str = (
                    col_rec.recommended_strategy.value
                    if hasattr(col_rec.recommended_strategy, "value")
                    else str(col_rec.recommended_strategy)
                )
                confidence_str = (
                    col_rec.confidence.value
                    if hasattr(col_rec, "confidence") and hasattr(col_rec.confidence, "value")
                    else str(getattr(col_rec, "confidence", "HIGH") or "HIGH")
                )
                rec = MaskingRecommendation(
                    schema_name=schema_name,
                    table_name=tbl,
                    column_name=col_rec.column,
                    data_type=col_rec.data_type,
                    sensitivity=sensitivity_str,
                    confidence=confidence_str,
                    recommended_strategy=strategy_str,
                    rationale=col_rec.rationale or "",
                    source=col_rec.source or "llm",
                    status="PENDING",
                )
                saved = self.recommendation_repo.create(rec)
                queued.append(saved)

        return queued

    def get_available_strategies(self) -> Dict[str, str]:
        return self.engine.strategy_factory.get_available_strategies()

    def apply_masking(self, request: MaskingRequest) -> MaskingResult:
        start_time = time.time()

        if request.policy_ids is not None:
            policies = []
            for pid in request.policy_ids:
                p = self.get_policy(pid)
                if p:
                    policies.append(p)
        elif request.tables:
            table_tuples = []
            for t in request.tables:
                if isinstance(t, dict):
                    table_tuples.append((t.get("schema") or t.get("schema_name") or "public", t.get("table") or t.get("table_name") or ""))
                elif isinstance(t, (list, tuple)) and len(t) >= 2:
                    table_tuples.append((t[0], t[1]))
                elif isinstance(t, str):
                    table_tuples.append(("public", t))
            policies = self.policy_manager.get_policies_for_tables(table_tuples, request.columns)
        elif request.table_name:
            schema = getattr(request, "schema_name", None) or "public"
            policies = self.policy_manager.get_policies_for_table(
                request.table_name, request.columns, schema_name=schema
            )
        else:
            policies = []

        masked_data, masked_columns, runtime_summary = self.engine.apply_masking(
            data=request.data,
            columns=request.columns,
            policies=policies,
            auto_detect=request.auto_detect,
            already_masked_columns=request.already_masked_columns,
        )

        return MaskingResult(
            original_data=request.data,
            masked_data=masked_data,
            masked_columns=masked_columns,
            policies_applied=[p.id for p in policies if p.id],
            execution_time=time.time() - start_time,
            runtime_detection_summary=runtime_summary,
        )
