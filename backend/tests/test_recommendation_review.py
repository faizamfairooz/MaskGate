import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.masking import MaskingPolicy, MaskingRecommendation
from app.services.masking_service import MaskingService
from app.ai.llm_schemas import ColumnRecommendation, SensitivityLevel, MaskingStrategyRecommendation
from app.schemas.database import ColumnSchema, TableSchema


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def masking_service():
    return MaskingService()


class TestRecommendationReviewUnit:
    """Unit tests for recommendation review logic in MaskingService."""

    def test_approve_recommendation_creates_active_policy(self, masking_service):
        rec = MaskingRecommendation(
            id=101,
            schema_name="public",
            table_name="patients",
            column_name="email",
            data_type="varchar",
            sensitivity="HIGH",
            recommended_strategy="email_mask",
            rationale="Contains patient email addresses",
            source="llm",
            status="PENDING",
        )

        with patch.object(masking_service.recommendation_repo, "get", return_value=rec), \
             patch.object(masking_service, "validate_table_and_column") as mock_validate, \
             patch.object(masking_service.policy_manager, "find_active_policy", return_value=None), \
             patch.object(masking_service.policy_manager, "create_policy") as mock_create_policy, \
             patch.object(masking_service.recommendation_repo, "update_status") as mock_update_status:

            expected_policy = MaskingPolicy(
                id=1,
                name="patients.email",
                description="Contains patient email addresses",
                schema_name="public",
                table_name="patients",
                column_name="email",
                strategy="email_mask",
                sensitivity="HIGH",
                status="ACTIVE",
                source="ai_recommendation",
                is_active=True,
            )
            mock_create_policy.return_value = expected_policy

            result = masking_service.approve_recommendation(101)

            assert result.status == "ACTIVE"
            assert result.table_name == "patients"
            assert result.column_name == "email"
            assert result.strategy == "email_mask"
            mock_validate.assert_called_once_with("patients", "email", schema_name="public")
            mock_update_status.assert_called_once_with(101, "APPROVED")
            mock_create_policy.assert_called_once()

    def test_reject_recommendation_does_not_create_policy(self, masking_service):
        rec = MaskingRecommendation(
            id=102,
            schema_name="public",
            table_name="patients",
            column_name="phone",
            sensitivity="HIGH",
            recommended_strategy="phone_mask",
            status="PENDING",
        )

        with patch.object(masking_service.recommendation_repo, "get", return_value=rec), \
             patch.object(masking_service.policy_manager, "create_policy") as mock_create_policy, \
             patch.object(masking_service.recommendation_repo, "update_status") as mock_update_status:

            rejected_rec = MaskingRecommendation(
                id=102,
                schema_name="public",
                table_name="patients",
                column_name="phone",
                sensitivity="HIGH",
                recommended_strategy="phone_mask",
                status="REJECTED",
            )
            mock_update_status.return_value = rejected_rec

            result = masking_service.reject_recommendation(102)

            assert result.status == "REJECTED"
            mock_update_status.assert_called_once_with(102, "REJECTED")
            mock_create_policy.assert_not_called()

    def test_approve_nonexistent_recommendation_raises_error(self, masking_service):
        with patch.object(masking_service.recommendation_repo, "get", return_value=None):
            with pytest.raises(ValueError, match="Recommendation 999 not found"):
                masking_service.approve_recommendation(999)

    def test_approve_already_approved_or_rejected_recommendation_raises_error(self, masking_service):
        rec = MaskingRecommendation(
            id=103,
            table_name="patients",
            column_name="email",
            sensitivity="HIGH",
            recommended_strategy="email_mask",
            status="APPROVED",
        )
        with patch.object(masking_service.recommendation_repo, "get", return_value=rec):
            with pytest.raises(ValueError, match="not pending"):
                masking_service.approve_recommendation(103)

    def test_reject_already_rejected_recommendation_raises_error(self, masking_service):
        rec = MaskingRecommendation(
            id=104,
            table_name="patients",
            column_name="email",
            sensitivity="HIGH",
            recommended_strategy="email_mask",
            status="REJECTED",
        )
        with patch.object(masking_service.recommendation_repo, "get", return_value=rec):
            with pytest.raises(ValueError, match="not pending"):
                masking_service.reject_recommendation(104)

    def test_approve_rejects_nonexistent_table(self, masking_service):
        rec = MaskingRecommendation(
            id=105,
            schema_name="public",
            table_name="ghost_table",
            column_name="email",
            sensitivity="HIGH",
            recommended_strategy="email_mask",
            status="PENDING",
        )
        with patch.object(masking_service.recommendation_repo, "get", return_value=rec), \
             patch("app.services.masking_service.db.table_exists", return_value=False):
            with pytest.raises(ValueError, match="Table 'ghost_table' does not exist"):
                masking_service.approve_recommendation(105)

    def test_approve_rejects_nonexistent_column(self, masking_service):
        rec = MaskingRecommendation(
            id=106,
            schema_name="public",
            table_name="patients",
            column_name="nonexistent_col",
            sensitivity="HIGH",
            recommended_strategy="email_mask",
            status="PENDING",
        )
        with patch.object(masking_service.recommendation_repo, "get", return_value=rec), \
             patch("app.services.masking_service.db.table_exists", return_value=True), \
             patch("app.services.masking_service.db.get_table_schema", return_value=[{"column_name": "id"}, {"column_name": "full_name"}]):
            with pytest.raises(ValueError, match="Column 'nonexistent_col' does not exist in table 'patients'"):
                masking_service.approve_recommendation(106)

    def test_approve_rejects_duplicate_active_policy(self, masking_service):
        rec = MaskingRecommendation(
            id=107,
            schema_name="public",
            table_name="patients",
            column_name="email",
            sensitivity="HIGH",
            recommended_strategy="email_mask",
            status="PENDING",
        )
        existing_policy = MaskingPolicy(
            id=5,
            name="patients.email",
            schema_name="public",
            table_name="patients",
            column_name="email",
            strategy="email_mask",
            status="ACTIVE",
        )
        with patch.object(masking_service.recommendation_repo, "get", return_value=rec), \
             patch.object(masking_service, "validate_table_and_column"), \
             patch.object(masking_service.policy_manager, "find_active_policy", return_value=existing_policy):
            with pytest.raises(ValueError, match="An active masking policy already exists for patients.email"):
                masking_service.approve_recommendation(107)

    def test_approve_rejects_invalid_strategy(self, masking_service):
        rec = MaskingRecommendation(
            id=108,
            schema_name="public",
            table_name="patients",
            column_name="email",
            sensitivity="HIGH",
            recommended_strategy="COMPLETELY_INVALID_STRATEGY",
            status="PENDING",
        )
        with patch.object(masking_service.recommendation_repo, "get", return_value=rec), \
             patch.object(masking_service, "validate_table_and_column"):
            with pytest.raises(ValueError, match="Invalid masking strategy 'COMPLETELY_INVALID_STRATEGY'"):
                masking_service.approve_recommendation(108)

    def test_get_all_policies_returns_only_active_policies(self, masking_service):
        with patch.object(masking_service.policy_manager, "get_all_policies") as mock_get_policies:
            active_policy = MaskingPolicy(
                id=1,
                name="patients.email",
                table_name="patients",
                column_name="email",
                strategy="email_mask",
                status="ACTIVE",
            )
            mock_get_policies.return_value = [active_policy]

            policies = masking_service.get_all_policies(status="ACTIVE")

            assert len(policies) == 1
            assert policies[0].status == "ACTIVE"
            mock_get_policies.assert_called_once_with(status="ACTIVE")

    def test_analyze_and_queue_recommendations(self, masking_service):
        mock_col_recs = [
            ColumnRecommendation(
                table="patients",
                column="email",
                sensitivity=SensitivityLevel.HIGH,
                data_type="varchar",
                recommended_strategy=MaskingStrategyRecommendation.EMAIL,
                rationale="Email address",
                source="llm",
            )
        ]
        mock_table_schema = TableSchema(
            table_name="patients",
            columns=[ColumnSchema(column_name="email", data_type="varchar", is_nullable=False)],
        )

        with patch("app.services.schema_service.SchemaService.get_all_tables", return_value=["patients"]), \
             patch("app.services.schema_service.SchemaService.get_table_schema", return_value=mock_table_schema), \
             patch("app.ai.schema_analyzer.SchemaAnalyzer.analyze_table_schema", return_value=mock_col_recs), \
             patch.object(masking_service.recommendation_repo, "create") as mock_create_rec:

            mock_create_rec.return_value = MaskingRecommendation(
                id=1,
                schema_name="public",
                table_name="patients",
                column_name="email",
                data_type="varchar",
                sensitivity="HIGH",
                recommended_strategy="EMAIL",
                rationale="Email address",
                source="llm",
                status="PENDING",
            )

            result = masking_service.analyze_and_queue_recommendations(schema_name="public")

            assert len(result) == 1
            assert result[0].status == "PENDING"
            assert result[0].column_name == "email"
            mock_create_rec.assert_called_once()


class TestRecommendationReviewAPI:
    """Integration API tests for recommendation display, approve, reject, and policy endpoints."""

    def test_api_list_recommendations(self, client):
        sample_recs = [
            MaskingRecommendation(
                id=1,
                table_name="patients",
                column_name="email",
                data_type="varchar",
                sensitivity="HIGH",
                recommended_strategy="email_mask",
                rationale="PII email",
                source="llm",
                status="PENDING",
            ),
            MaskingRecommendation(
                id=2,
                table_name="patients",
                column_name="phone",
                data_type="varchar",
                sensitivity="HIGH",
                recommended_strategy="phone_mask",
                rationale="PII phone",
                source="heuristic_fallback",
                status="PENDING",
            ),
        ]
        with patch("app.api.routes.masking.masking_service.list_recommendations", return_value=sample_recs) as mock_list:
            response = client.get("/api/v1/masking/recommendations?status=PENDING")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["table_name"] == "patients"
            assert data[0]["column_name"] == "email"
            assert data[0]["data_type"] == "varchar"
            assert data[0]["sensitivity"] == "HIGH"
            assert data[0]["confidence"] == "HIGH"
            assert data[0]["recommended_strategy"] == "email_mask"
            assert data[0]["rationale"] == "PII email"
            assert data[0]["source"] == "llm"
            assert data[0]["status"] == "PENDING"
            mock_list.assert_called_once_with(status="PENDING", table_name=None, schema_name=None)

    def test_api_approve_recommendation_success(self, client):
        approved_policy = MaskingPolicy(
            id=10,
            name="patients.email",
            description="PII email",
            schema_name="public",
            table_name="patients",
            column_name="email",
            strategy="email_mask",
            sensitivity="HIGH",
            status="ACTIVE",
            source="ai_recommendation",
            is_active=True,
        )
        with patch("app.api.routes.masking.masking_service.approve_recommendation", return_value=approved_policy) as mock_approve:
            response = client.post("/api/v1/masking/recommendations/1/approve")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 10
            assert data["status"] == "ACTIVE"
            assert data["table_name"] == "patients"
            assert data["column_name"] == "email"
            mock_approve.assert_called_once_with(1)

    def test_api_approve_recommendation_not_found(self, client):
        with patch("app.api.routes.masking.masking_service.approve_recommendation", side_effect=ValueError("Recommendation 999 not found")):
            response = client.post("/api/v1/masking/recommendations/999/approve")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_api_approve_recommendation_validation_error(self, client):
        with patch("app.api.routes.masking.masking_service.approve_recommendation", side_effect=ValueError("An active masking policy already exists for patients.email")):
            response = client.post("/api/v1/masking/recommendations/1/approve")
            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]

    def test_api_reject_recommendation_success(self, client):
        rejected_rec = MaskingRecommendation(
            id=2,
            table_name="patients",
            column_name="phone",
            sensitivity="HIGH",
            recommended_strategy="phone_mask",
            status="REJECTED",
        )
        with patch("app.api.routes.masking.masking_service.reject_recommendation", return_value=rejected_rec) as mock_reject:
            response = client.post("/api/v1/masking/recommendations/2/reject")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 2
            assert data["status"] == "REJECTED"
            mock_reject.assert_called_once_with(2)

    def test_api_reject_recommendation_not_found(self, client):
        with patch("app.api.routes.masking.masking_service.reject_recommendation", side_effect=ValueError("Recommendation 999 not found")):
            response = client.post("/api/v1/masking/recommendations/999/reject")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_api_get_policies_returns_active(self, client):
        policies = [
            MaskingPolicy(
                id=1,
                name="patients.email",
                schema_name="public",
                table_name="patients",
                column_name="email",
                strategy="email_mask",
                sensitivity="HIGH",
                status="ACTIVE",
                is_active=True,
            )
        ]
        with patch("app.api.routes.masking.masking_service.get_all_policies", return_value=policies) as mock_get:
            response = client.get("/api/v1/masking/policies")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == "ACTIVE"
            mock_get.assert_called_once_with(status="ACTIVE")

    def test_api_analyze_and_queue(self, client):
        queued = [
            MaskingRecommendation(
                id=1,
                schema_name="public",
                table_name="patients",
                column_name="email",
                data_type="varchar",
                sensitivity="HIGH",
                recommended_strategy="email_mask",
                status="PENDING",
            )
        ]
        with patch("app.api.routes.masking.masking_service.analyze_and_queue_recommendations", return_value=queued) as mock_queue:
            response = client.post(
                "/api/v1/masking/recommendations/analyze-and-queue",
                json={"schema": "public", "table_name": "patients"},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == "PENDING"
            mock_queue.assert_called_once_with(schema_name="public", table_name="patients")

    def test_api_approve_recommendation_invalid_strategy(self, client):
        with patch(
            "app.api.routes.masking.masking_service.approve_recommendation",
            side_effect=ValueError("Invalid masking strategy 'UNKNOWN_STRAT'. Must be one of: ['EMAIL', 'PHONE_LAST4']"),
        ):
            response = client.post("/api/v1/masking/recommendations/1/approve")
            assert response.status_code == 400
            assert "Invalid masking strategy" in response.json()["detail"]


class TestWorkflowApprovalRejectionE2E:
    """End-to-end workflow tests for recommendation approval/rejection lifecycle."""

    def test_approval_workflow_activates_deterministic_masking(self, client, masking_service):
        from app.database.postgresql import db
        from app.schemas.masking import MaskingRequest

        # 1. Clean up existing active policy for patients.email if any
        existing_policy = masking_service.policy_manager.find_active_policy("patients", "email")
        if existing_policy:
            masking_service.policy_manager.delete_policy(existing_policy.id)

        # 2. Create a PENDING recommendation
        rec = masking_service.recommendation_repo.create(
            MaskingRecommendation(
                schema_name="public",
                table_name="patients",
                column_name="email",
                data_type="character varying",
                sensitivity="HIGH",
                recommended_strategy="EMAIL",
                rationale="Protect patient emails",
                source="llm",
                status="PENDING",
            )
        )
        assert rec.id is not None
        assert rec.status == "PENDING"

        # 3. Verify recommendation is visible in pending list
        pending_list = masking_service.list_recommendations(status="PENDING", table_name="patients")
        assert any(r.id == rec.id for r in pending_list)

        # 4. Approve recommendation
        approved_policy = masking_service.approve_recommendation(rec.id)
        assert approved_policy.status == "ACTIVE"
        assert approved_policy.is_active is True
        assert approved_policy.strategy == "EMAIL"

        # 5. Verify recommendation state updated to APPROVED
        updated_rec = masking_service.recommendation_repo.get(rec.id)
        assert updated_rec.status == "APPROVED"

        # 6. Verify deterministic masking engine immediately applies the approved policy
        test_data = [[1, "Alice", "alice.smith@example.com"]]
        mask_result = masking_service.apply_masking(
            MaskingRequest(
                schema_name="public",
                table_name="patients",
                columns=["patient_id", "full_name", "email"],
                data=test_data,
                auto_detect=False,
            )
        )
        masked_email = mask_result.masked_data[0][2]
        assert masked_email != "alice.smith@example.com"
        assert "@example.com" in masked_email
        assert "***" in masked_email

        # 7. Clean up created policy
        if approved_policy.id:
            masking_service.delete_policy(approved_policy.id)

    def test_rejection_workflow_does_not_mask(self, client, masking_service):
        from app.schemas.masking import MaskingRequest

        # 1. Clean up existing active policy for patients.phone if any
        existing_policy = masking_service.policy_manager.find_active_policy("patients", "phone")
        if existing_policy:
            masking_service.policy_manager.delete_policy(existing_policy.id)

        # 2. Create a PENDING recommendation
        rec = masking_service.recommendation_repo.create(
            MaskingRecommendation(
                schema_name="public",
                table_name="patients",
                column_name="phone",
                data_type="character varying",
                sensitivity="HIGH",
                recommended_strategy="PHONE_LAST4",
                rationale="Phone number",
                source="llm",
                status="PENDING",
            )
        )
        assert rec.id is not None

        # 3. Reject recommendation
        rejected_rec = masking_service.reject_recommendation(rec.id)
        assert rejected_rec.status == "REJECTED"

        # 4. Verify no active policy exists
        active_policy = masking_service.policy_manager.find_active_policy("patients", "phone")
        assert active_policy is None

        # 5. Verify deterministic masking leaves data unmasked
        test_data = [[1, "555-987-6543"]]
        mask_result = masking_service.apply_masking(
            MaskingRequest(
                schema_name="public",
                table_name="patients",
                columns=["patient_id", "phone"],
                data=test_data,
                auto_detect=False,
            )
        )
        assert mask_result.masked_data[0][1] == "555-987-6543"

    def test_approval_rejects_invalid_table_or_column(self, masking_service):
        # Create recommendation with non-existent table
        bad_table_rec = masking_service.recommendation_repo.create(
            MaskingRecommendation(
                schema_name="public",
                table_name="nonexistent_xyz_tbl",
                column_name="some_col",
                recommended_strategy="EMAIL",
                status="PENDING",
            )
        )
        with pytest.raises(ValueError, match="does not exist"):
            masking_service.approve_recommendation(bad_table_rec.id)

        # Create recommendation with non-existent column
        bad_col_rec = masking_service.recommendation_repo.create(
            MaskingRecommendation(
                schema_name="public",
                table_name="patients",
                column_name="nonexistent_xyz_col",
                recommended_strategy="EMAIL",
                status="PENDING",
            )
        )
        with pytest.raises(ValueError, match="does not exist"):
            masking_service.approve_recommendation(bad_col_rec.id)

    def test_approval_rejects_invalid_strategy(self, masking_service):
        bad_strat_rec = masking_service.recommendation_repo.create(
            MaskingRecommendation(
                schema_name="public",
                table_name="patients",
                column_name="email",
                recommended_strategy="INVALID_CUSTOM_STRATEGY",
                status="PENDING",
            )
        )
        with pytest.raises(ValueError, match="Invalid masking strategy"):
            masking_service.approve_recommendation(bad_strat_rec.id)
