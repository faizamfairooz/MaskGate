from typing import List, Optional

from app.database.repositories import PolicyRepository
from app.schemas.masking import MaskingPolicy


class PolicyManager:
    """Facade for masking policy persistence."""

    def __init__(self, repository: Optional[PolicyRepository] = None):
        self._repo = repository or PolicyRepository()

    def create_policy(self, policy: MaskingPolicy) -> MaskingPolicy:
        return self._repo.create_policy(policy)

    def get_policy(self, policy_id: int) -> Optional[MaskingPolicy]:
        return self._repo.get_policy(policy_id)

    def get_all_policies(self) -> List[MaskingPolicy]:
        return self._repo.get_all_policies()

    def delete_policy(self, policy_id: int) -> bool:
        return self._repo.delete_policy(policy_id)

    def get_policies_for_table(self, table_name: str, columns: List[str]) -> List[MaskingPolicy]:
        return self._repo.get_policies_for_table(table_name, columns)
