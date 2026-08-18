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

    def find_active_policy(
        self, table_name: str, column_name: str, schema_name: str = "public"
    ) -> Optional[MaskingPolicy]:
        return self._repo.find_active_policy(table_name, column_name, schema_name)

    def get_all_policies(self, status: Optional[str] = "ACTIVE") -> List[MaskingPolicy]:
        return self._repo.get_all_policies(status=status)

    def delete_policy(self, policy_id: int) -> bool:
        return self._repo.delete_policy(policy_id)

    def get_policies_for_table(
        self, table_name: str, columns: List[str], schema_name: str = "public"
    ) -> List[MaskingPolicy]:
        return self._repo.get_policies_for_table(table_name, columns, schema_name)
