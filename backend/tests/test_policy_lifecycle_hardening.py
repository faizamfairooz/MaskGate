"""
Agent #24 — Policy Editing & PostgreSQL Function Lifecycle Hardening Test Suite.

Exhaustively tests and verifies:
1. CREATE (synchronization between masking_policies + PostgreSQL function maskgate_policy_<id>)
2. EDIT STRATEGY (EMAIL -> REDACT, replace function, immediate query effect)
3. EDIT PARAMETERS (PARTIAL visible_chars=2 -> 4, function changes, query output changes)
4. DEACTIVATE (policy becomes inactive, DB function removed, query returns raw data)
5. REACTIVATE (policy becomes ACTIVE, DB function recreated, query masking restored)
6. DELETE (policy lifecycle state disabled, DB function removed, no obsolete references)
7. AI APPROVE (PENDING -> APPROVE -> ACTIVE policy -> DB function created)
8. AI REJECT (PENDING -> REJECTED -> no policy created, no DB function created)
9. FAILURE HANDLING & ROLLBACK COMPENSATION (state consistency when DB function creation/update fails)
10. SECURITY (strictly validated integer policy IDs only, never allowing user input into function names)
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database.postgresql import db
from app.database.db_masking_functions import DBMaskingFunctionManager
from app.database.repositories import PolicyRepository, RecommendationRepository
from app.schemas.masking import MaskingPolicy, MaskingPolicyUpdate, MaskingRecommendation
from app.services.masking_service import MaskingService
from app.services.query_service import QueryService
from app.utils.query_parser import SQLQueryParser


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def masking_service():
    return MaskingService()


@pytest.fixture
def query_service():
    return QueryService()


@pytest.fixture
def db_fn_manager():
    return DBMaskingFunctionManager()


@pytest.fixture
def rec_repo():
    return RecommendationRepository()


@pytest.fixture
def policy_repo():
    return PolicyRepository()


# ===========================================================================
# 1. CREATE LIFECYCLE
# ===========================================================================

class TestPolicyLifecycleCreate:
    """1. CREATE: Admin creates patients.email -> EMAIL."""

    def test_create_policy_lifecycle_synchronization(self, masking_service, query_service, db_fn_manager):
        # Cleanup any existing policy on patients.email
        existing = masking_service.policy_manager.find_active_policy("patients", "email")
        if existing and existing.id:
            masking_service.delete_policy(existing.id)

        policy = masking_service.create_policy(
            MaskingPolicy(
                name="patients.email",
                schema_name="public",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
                sensitivity="HIGH",
            )
        )
        try:
            # Verify masking_policies row exists, status is ACTIVE, is_active is TRUE
            assert policy.id is not None
            assert policy.is_active is True
            assert (policy.status or "").upper() == "ACTIVE"

            saved_policy = masking_service.get_policy(policy.id)
            assert saved_policy is not None
            assert saved_policy.is_active is True
            assert saved_policy.status == "ACTIVE"
            assert saved_policy.strategy == "EMAIL"

            # Verify PostgreSQL function maskgate_policy_<id>() exists in database
            assert db_fn_manager.function_exists(policy.id) is True

            # Direct execution of the stored function in PostgreSQL
            fn_name = db_fn_manager.get_function_name(policy.id)
            fn_res = db.execute_query(f"SELECT {fn_name}('john.doe@hospital.org') AS val;")
            assert fn_res[0]["val"] == "j***@hospital.org"

            # Query uses the function
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
                resp = query_service.execute_query("SELECT email FROM patients LIMIT 2;", apply_masking=True)

            assert resp.row_count > 0
            assert "email" in resp.masked_columns
            executed_sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
            assert any(f"{fn_name}(email::text)" in sql for sql in executed_sqls)
            assert "***@" in resp.rows[0][0]
        finally:
            masking_service.delete_policy(policy.id)


# ===========================================================================
# 2. EDIT STRATEGY LIFECYCLE
# ===========================================================================

class TestPolicyLifecycleEditStrategy:
    """2. EDIT STRATEGY: EMAIL -> REDACT."""

    def test_edit_strategy_replaces_function_and_updates_query(self, masking_service, query_service, db_fn_manager):
        # 1. Create with EMAIL
        policy = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="email", strategy="EMAIL")
        )
        policy_id = policy.id
        fn_name = db_fn_manager.get_function_name(policy_id)

        try:
            # Query returns EMAIL format
            resp1 = query_service.execute_query("SELECT email FROM patients LIMIT 1;", apply_masking=True)
            assert "***@" in resp1.rows[0][0]

            # 2. Edit strategy to REDACT
            updated = masking_service.update_policy(
                policy_id, MaskingPolicyUpdate(strategy="REDACT", description="Changed to full redaction")
            )

            # Verify same policy ID remains and strategy changed
            assert updated.id == policy_id
            assert updated.strategy == "REDACT"

            # Verify PostgreSQL function was replaced and now executes REDACT
            assert db_fn_manager.function_exists(policy_id) is True
            fn_res = db.execute_query(f"SELECT {fn_name}('john.doe@hospital.org') AS val;")
            assert fn_res[0]["val"] == "*********************"

            # Next query immediately uses REDACT from PostgreSQL
            resp2 = query_service.execute_query("SELECT email FROM patients LIMIT 1;", apply_masking=True)
            email_val = resp2.rows[0][0]
            assert set(email_val) == {"*"}
        finally:
            masking_service.delete_policy(policy_id)


# ===========================================================================
# 3. EDIT PARAMETERS LIFECYCLE
# ===========================================================================

class TestPolicyLifecycleEditParameters:
    """3. EDIT PARAMETERS: PARTIAL visible_chars=2 -> visible_chars=4."""

    def test_edit_parameters_persisted_and_replaces_function(self, masking_service, query_service, db_fn_manager):
        policy = masking_service.create_policy(
            MaskingPolicy(
                table_name="patients",
                column_name="address",
                strategy="PARTIAL",
                parameters={"visible_chars": 2},
            )
        )
        policy_id = policy.id
        fn_name = db_fn_manager.get_function_name(policy_id)

        try:
            # 1. Initially visible_chars=2
            raw_addr = db.execute_query("SELECT address FROM patients WHERE LENGTH(address) > 10 LIMIT 1;")[0]["address"]
            resp1 = query_service.execute_query(
                "SELECT address FROM patients WHERE LENGTH(address) > 10 LIMIT 1;", apply_masking=True
            )
            masked1 = resp1.rows[0][0]
            assert masked1.startswith(raw_addr[:2])
            assert masked1.endswith(raw_addr[-2:])

            # Verify function directly
            res_fn1 = db.execute_query(f"SELECT {fn_name}('1234567890') AS val;")[0]["val"]
            assert res_fn1 == "12******90"

            # 2. Edit parameters to visible_chars=4
            updated = masking_service.update_policy(
                policy_id, MaskingPolicyUpdate(parameters={"visible_chars": 4})
            )
            assert updated.parameters.get("visible_chars") == 4

            # Verify parameters persisted in database
            saved = masking_service.get_policy(policy_id)
            assert saved.parameters.get("visible_chars") == 4

            # Verify function was replaced in PostgreSQL
            res_fn2 = db.execute_query(f"SELECT {fn_name}('1234567890') AS val;")[0]["val"]
            assert res_fn2 == "1234**7890"

            # 3. Next query output changes correctly
            resp2 = query_service.execute_query(
                "SELECT address FROM patients WHERE LENGTH(address) > 10 LIMIT 1;", apply_masking=True
            )
            masked2 = resp2.rows[0][0]
            assert masked2.startswith(raw_addr[:4])
            assert masked2.endswith(raw_addr[-4:])
        finally:
            masking_service.delete_policy(policy_id)


# ===========================================================================
# 4. DEACTIVATE LIFECYCLE
# ===========================================================================

class TestPolicyLifecycleDeactivate:
    """4. DEACTIVATE: Policy becomes inactive, DB function removed, query returns raw data."""

    def test_deactivate_removes_function_and_stops_masking(self, masking_service, query_service, db_fn_manager):
        policy = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="phone", strategy="PHONE_LAST4")
        )
        policy_id = policy.id
        raw_phone = db.execute_query("SELECT phone FROM patients LIMIT 1;")[0]["phone"]

        # Masked initially
        resp1 = query_service.execute_query("SELECT phone FROM patients LIMIT 1;", apply_masking=True)
        assert resp1.rows[0][0] != raw_phone
        assert resp1.rows[0][0].startswith("*")
        assert db_fn_manager.function_exists(policy_id) is True

        # Deactivate policy
        masking_service.delete_policy(policy_id)

        # Verify policy becomes inactive/disabled
        p_after = masking_service.get_policy(policy_id)
        assert p_after.is_active is False
        assert p_after.status == "DISABLED"

        # Verify DB function is removed from PostgreSQL
        assert db_fn_manager.function_exists(policy_id) is False

        # Verify query no longer applies policy and returns raw unmasked data
        with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
            resp2 = query_service.execute_query("SELECT phone FROM patients LIMIT 1;", apply_masking=True)
        assert resp2.rows[0][0] == raw_phone
        assert "phone" not in resp2.masked_columns

        executed_sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
        matching_q = next((sql for sql in executed_sqls if "FROM patients" in sql and "SELECT phone" in sql), "")
        assert f"maskgate_policy_{policy_id}" not in matching_q


# ===========================================================================
# 5. REACTIVATE LIFECYCLE
# ===========================================================================

class TestPolicyLifecycleReactivate:
    """5. REACTIVATE: Policy becomes ACTIVE, DB function recreated, query masking works again."""

    def test_reactivate_recreates_function_and_restores_masking(self, masking_service, query_service, db_fn_manager):
        policy = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="phone", strategy="PHONE_LAST4")
        )
        policy_id = policy.id
        raw_phone = db.execute_query("SELECT phone FROM patients LIMIT 1;")[0]["phone"]

        try:
            # Deactivate first
            masking_service.delete_policy(policy_id)
            assert db_fn_manager.function_exists(policy_id) is False

            # Reactivate
            reactivated = masking_service.reactivate_policy(policy_id)
            assert reactivated.is_active is True
            assert reactivated.status == "ACTIVE"

            # DB function is recreated in PostgreSQL
            assert db_fn_manager.function_exists(policy_id) is True

            # Direct function execution works
            fn_name = db_fn_manager.get_function_name(policy_id)
            fn_res = db.execute_query(f"SELECT {fn_name}('0771234567') AS val;")
            assert fn_res[0]["val"] == "******4567"

            # Next query applies masking again
            resp = query_service.execute_query("SELECT phone FROM patients LIMIT 1;", apply_masking=True)
            assert resp.rows[0][0] != raw_phone
            assert resp.rows[0][0].startswith("*")
            assert "phone" in resp.masked_columns
        finally:
            masking_service.delete_policy(policy_id)


# ===========================================================================
# 6. DELETE LIFECYCLE
# ===========================================================================

class TestPolicyLifecycleDelete:
    """6. DELETE: Correct lifecycle state, associated DB function removed, no obsolete reference."""

    def test_delete_policy_cleans_up_function_completely(self, masking_service, query_service, db_fn_manager):
        policy = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="emergency_contact", strategy="DO_NOT_SHOW")
        )
        policy_id = policy.id

        assert db_fn_manager.function_exists(policy_id) is True

        # Delete
        masking_service.delete_policy(policy_id)

        # Policy lifecycle state
        p = masking_service.get_policy(policy_id)
        assert p.is_active is False
        assert p.status == "DISABLED"

        # Function removed
        assert db_fn_manager.function_exists(policy_id) is False

        # Querying does not reference obsolete function
        with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
            resp = query_service.execute_query("SELECT emergency_contact FROM patients LIMIT 1;", apply_masking=True)

        assert resp.row_count > 0
        executed_sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
        assert not any(f"maskgate_policy_{policy_id}" in sql for sql in executed_sqls)


# ===========================================================================
# 7. AI APPROVE LIFECYCLE
# ===========================================================================

class TestPolicyLifecycleAIApprove:
    """7. AI APPROVE: PENDING -> APPROVE -> ACTIVE policy -> DB function created."""

    def test_ai_approve_creates_active_policy_and_db_function(self, masking_service, query_service, rec_repo, db_fn_manager):
        # Cleanup
        existing = masking_service.policy_manager.find_active_policy("appointments", "doctor_name")
        if existing and existing.id:
            masking_service.delete_policy(existing.id)

        rec = rec_repo.create(
            MaskingRecommendation(
                schema_name="public",
                table_name="appointments",
                column_name="doctor_name",
                data_type="varchar",
                sensitivity="HIGH",
                confidence="HIGH",
                recommended_strategy="REDACT",
                rationale="Doctor name identifier",
                status="PENDING",
            )
        )
        assert rec.id is not None
        assert rec.status == "PENDING"

        created_policy = None
        try:
            # Approve recommendation
            created_policy = masking_service.approve_recommendation(rec.id)

            # 1. Recommendation becomes APPROVED
            rec_after = rec_repo.get(rec.id)
            assert rec_after.status == "APPROVED"

            # 2. ACTIVE policy created
            assert created_policy.id is not None
            assert created_policy.is_active is True
            assert created_policy.status == "ACTIVE"
            assert created_policy.strategy == "REDACT"

            # 3. DB function created in PostgreSQL
            assert db_fn_manager.function_exists(created_policy.id) is True
            fn_name = db_fn_manager.get_function_name(created_policy.id)
            res = db.execute_query(f"SELECT {fn_name}('Dr. Robert') AS val;")
            assert res[0]["val"] == "**********"

            # 4. Query uses function
            resp = query_service.execute_query("SELECT doctor_name FROM appointments LIMIT 1;", apply_masking=True)
            assert set(resp.rows[0][0]) == {"*"}
        finally:
            if created_policy and created_policy.id:
                masking_service.delete_policy(created_policy.id)


# ===========================================================================
# 8. AI REJECT LIFECYCLE
# ===========================================================================

class TestPolicyLifecycleAIReject:
    """8. AI REJECT: PENDING -> REJECTED, no policy created, no DB masking function created."""

    def test_ai_reject_creates_no_policy_and_no_function(self, masking_service, query_service, rec_repo, db_fn_manager):
        existing = masking_service.policy_manager.find_active_policy("appointments", "status")
        if existing and existing.id:
            masking_service.delete_policy(existing.id)

        rec = rec_repo.create(
            MaskingRecommendation(
                schema_name="public",
                table_name="appointments",
                column_name="status",
                data_type="varchar",
                sensitivity="LOW",
                confidence="LOW",
                recommended_strategy="REDACT",
                rationale="Non-sensitive field",
                status="PENDING",
            )
        )

        rejected = masking_service.reject_recommendation(rec.id)
        assert rejected.status == "REJECTED"

        # Verify no policy exists
        active_p = masking_service.policy_manager.find_active_policy("appointments", "status")
        assert active_p is None

        # Verify no DB function created for the recommendation id
        assert db_fn_manager.function_exists(rec.id) is False

        # Query returns unmasked data
        resp = query_service.execute_query("SELECT status FROM appointments LIMIT 1;", apply_masking=True)
        assert "status" not in resp.masked_columns


# ===========================================================================
# 9. FAILURE HANDLING & ROLLBACK COMPENSATION
# ===========================================================================

class TestPolicyLifecycleFailureHandling:
    """Failure handling: database policy state and function state must never silently become inconsistent."""

    def test_create_failure_rolls_back_policy_row(self, masking_service, db_fn_manager, policy_repo):
        """If PostgreSQL function creation fails during create_policy, policy row must be rolled back."""
        with patch.object(
            DBMaskingFunctionManager,
            "create_or_replace_policy_function",
            side_effect=RuntimeError("Simulated PostgreSQL connection failure during CREATE FUNCTION"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                policy_repo.create_policy(
                    MaskingPolicy(table_name="patients", column_name="phone", strategy="PHONE_LAST4")
                )
            assert "Simulated PostgreSQL connection failure" in str(exc_info.value)

        # Verify policy row was NOT left in active state
        active = policy_repo.find_active_policy("patients", "phone")
        assert active is None

    def test_update_failure_rolls_back_to_previous_policy_state(self, masking_service, db_fn_manager, policy_repo):
        """If PostgreSQL function update fails, policy in database is restored to its previous state."""
        # 1. Create a working EMAIL policy
        policy = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="email", strategy="EMAIL")
        )
        policy_id = policy.id

        try:
            # 2. Attempt update to REDACT with a simulated DB function creation failure
            with patch.object(
                DBMaskingFunctionManager,
                "create_or_replace_policy_function",
                side_effect=RuntimeError("Simulated function compile failure"),
            ):
                with pytest.raises(RuntimeError) as exc_info:
                    masking_service.update_policy(policy_id, MaskingPolicyUpdate(strategy="REDACT"))
                assert "Simulated function compile failure" in str(exc_info.value)

            # 3. Verify policy in database was rolled back to EMAIL
            restored = masking_service.get_policy(policy_id)
            assert restored.strategy == "EMAIL"
            assert restored.is_active is True
        finally:
            masking_service.delete_policy(policy_id)

    def test_reactivate_failure_rolls_back_to_disabled(self, masking_service, db_fn_manager):
        """If function recreation fails during reactivation, policy is rolled back to DISABLED."""
        policy = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="phone", strategy="PHONE_LAST4")
        )
        policy_id = policy.id

        # Deactivate
        masking_service.delete_policy(policy_id)
        assert masking_service.get_policy(policy_id).is_active is False

        # Attempt reactivate with function creation failure
        with patch.object(
            DBMaskingFunctionManager,
            "create_or_replace_policy_function",
            side_effect=RuntimeError("Simulated DB recreation error"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                masking_service.reactivate_policy(policy_id)
            assert "Simulated DB recreation error" in str(exc_info.value)

        # Verify policy remains DISABLED
        p = masking_service.get_policy(policy_id)
        assert p.is_active is False
        assert p.status == "DISABLED"


# ===========================================================================
# 10. SECURITY & FUNCTION NAME INVARIANTS
# ===========================================================================

class TestPolicyLifecycleSecurity:
    """Function names must ONLY be generated from validated integer policy IDs."""

    def test_strictly_validated_integer_policy_ids_only(self, db_fn_manager):
        # Valid integer IDs
        assert db_fn_manager.get_function_name(1) == "maskgate_policy_1"
        assert db_fn_manager.get_function_name(42) == "maskgate_policy_42"
        assert db_fn_manager.get_function_name(1000) == "maskgate_policy_1000"

        # Invalid IDs rejected
        with pytest.raises(ValueError):
            db_fn_manager.get_function_name(-1)
        with pytest.raises(ValueError):
            db_fn_manager.get_function_name(0)
        with pytest.raises(ValueError):
            db_fn_manager.get_function_name("1; DROP TABLE users; --")
        with pytest.raises(ValueError):
            db_fn_manager.get_function_name(True)  # Boolean rejected
        with pytest.raises(ValueError):
            db_fn_manager.get_function_name(None)

    def test_user_input_never_becomes_sql_function_name(self, masking_service, query_service):
        """Table names, policy names, or user input strings never become function names."""
        policy = masking_service.create_policy(
            MaskingPolicy(
                name="SELECT * FROM users; -- malicious_name",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
            )
        )
        try:
            fn_name = DBMaskingFunctionManager.get_function_name(policy.id)
            assert fn_name == f"maskgate_policy_{policy.id}"
            assert "malicious_name" not in fn_name
            assert "users" not in fn_name

            # Query rewrite uses maskgate_policy_<int>
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
                query_service.execute_query("SELECT email FROM patients LIMIT 1;", apply_masking=True)

            executed_sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
            assert any(f"maskgate_policy_{policy.id}(email::text)" in sql for sql in executed_sqls)
            assert not any("malicious_name" in sql for sql in executed_sqls)
        finally:
            masking_service.delete_policy(policy.id)
