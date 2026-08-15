import time
from typing import Any, Dict, List, Optional

from app.database.repositories import RecommendationRepository
from app.masking.engine import MaskingEngine
from app.masking.policies import PolicyManager
from app.schemas.masking import (
    MaskingPolicy,
    MaskingRecommendation,
    MaskingRequest,
    MaskingResult,
)


class MaskingService:
    """Service for managing and applying data masking policies."""

    def __init__(self):
        self.engine = MaskingEngine()
        self.policy_manager = PolicyManager()
        self.recommendation_repo = RecommendationRepository()

    def create_policy(
        self,
        name: str,
        description: str,
        table_name: str,
        column_name: str,
        strategy: str,
        parameters: Optional[Dict[str, Any]] = None,
        source: str = "manual",
    ) -> MaskingPolicy:
        policy = MaskingPolicy(
            name=name,
            description=description,
            table_name=table_name,
            column_name=column_name,
            strategy=strategy,
            parameters=parameters or {},
            source=source,
            status="approved",
        )
        return self.policy_manager.create_policy(policy)

    def get_all_policies(self) -> List[MaskingPolicy]:
        return self.policy_manager.get_all_policies()

    def get_policy(self, policy_id: int) -> Optional[MaskingPolicy]:
        return self.policy_manager.get_policy(policy_id)

    def delete_policy(self, policy_id: int) -> None:
        self.policy_manager.delete_policy(policy_id)

    def list_recommendations(
        self,
        status: Optional[str] = None,
        table_name: Optional[str] = None,
    ) -> List[MaskingRecommendation]:
        return self.recommendation_repo.list_recommendations(status=status, table_name=table_name)

    def approve_recommendation(self, rec_id: int) -> MaskingPolicy:
        rec = self.recommendation_repo.get(rec_id)
        if rec is None:
            raise ValueError(f"Recommendation {rec_id} not found")
        if rec.status != "pending":
            raise ValueError(f"Recommendation {rec_id} is not pending")

        policy = self.create_policy(
            name=f"{rec.table_name}.{rec.column_name}",
            description=rec.rationale or "Approved AI recommendation",
            table_name=rec.table_name,
            column_name=rec.column_name,
            strategy=rec.recommended_strategy,
            source="ai_recommendation",
        )
        self.recommendation_repo.update_status(rec_id, "approved")
        return policy

    def reject_recommendation(self, rec_id: int) -> MaskingRecommendation:
        rec = self.recommendation_repo.get(rec_id)
        if rec is None:
            raise ValueError(f"Recommendation {rec_id} not found")
        updated = self.recommendation_repo.update_status(rec_id, "rejected")
        if updated is None:
            raise ValueError(f"Recommendation {rec_id} not found")
        return updated

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
        else:
            policies = self.policy_manager.get_policies_for_table(
                request.table_name, request.columns
            )

        masked_data, masked_columns, runtime_summary = self.engine.apply_masking(
            data=request.data,
            columns=request.columns,
            policies=policies,
            auto_detect=request.auto_detect,
        )

        return MaskingResult(
            original_data=request.data,
            masked_data=masked_data,
            masked_columns=masked_columns,
            policies_applied=[p.id for p in policies if p.id],
            execution_time=time.time() - start_time,
            runtime_detection_summary=runtime_summary,
        )
