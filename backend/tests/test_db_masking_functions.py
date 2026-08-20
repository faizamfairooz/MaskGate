"""
Comprehensive Test Suite for PostgreSQL DB-Level Masking Functions,
Policy Lifecycle Management, Query Rewriting, and Security Protections.

Deeply verifies the mentor requirement:
"Do masking at DB level by creating functions in the DB so we don't pull all
raw sensitive data into Python and mask it there."
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database.postgresql import db
from app.database.db_masking_functions import DBMaskingFunctionManager
from app.database.repositories import PolicyRepository, RecommendationRepository
from app.schemas.masking import MaskingPolicy, MaskingPolicyUpdate, MaskingRecommendation
from app.services.masking_service import MaskingService
from app.services.query_service import QueryService
from app.utils.query_parser import SQLQueryParser
from app.ai.llm_schemas import RuntimeDetectionResult


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_fn_manager():
    return DBMaskingFunctionManager()


@pytest.fixture
def masking_service():
    return MaskingService()


@pytest.fixture
def query_service():
    return QueryService()


@pytest.fixture
def query_parser():
    return SQLQueryParser()


@pytest.fixture
def policy_repo():
    return PolicyRepository()


@pytest.fixture
def rec_repo():
    return RecommendationRepository()


# ===========================================================================
# 1. Base PostgreSQL Stored Masking Function Unit & Execution Tests
# ===========================================================================

class TestBaseDBMaskingFunctions:
    """Verify PL/pgSQL base masking functions directly against PostgreSQL."""

    def test_init_base_functions(self, db_fn_manager):
        assert db_fn_manager.init_base_functions() is True

    def test_email_function_sql(self, db_fn_manager):
        db_fn_manager.init_base_functions()
        # Standard email
        res = db.execute_query("SELECT maskgate_fn_email('john.smith@gmail.com') AS val;")
        assert res[0]["val"] == "j***@gmail.com"

        # Short local part
        res = db.execute_query("SELECT maskgate_fn_email('a@hospital.org') AS val;")
        assert res[0]["val"] == "a***@hospital.org"

        # Invalid email (no @)
        res = db.execute_query("SELECT maskgate_fn_email('invalidemail') AS val;")
        assert res[0]["val"] == "***@***.***"

        # Empty local part
        res = db.execute_query("SELECT maskgate_fn_email('@domain.com') AS val;")
        assert res[0]["val"] == "@domain.com"

        # Empty string and NULL
        res_empty = db.execute_query("SELECT maskgate_fn_email('') AS val;")
        assert res_empty[0]["val"] == ""

        res_null = db.execute_query("SELECT maskgate_fn_email(NULL) AS val;")
        assert res_null[0]["val"] is None

    def test_phone_last4_function_sql(self, db_fn_manager):
        db_fn_manager.init_base_functions()
        # 10 digits
        res = db.execute_query("SELECT maskgate_fn_phone_last4('0771234567') AS val;")
        assert res[0]["val"] == "******4567"

        # Formatted phone number
        res = db.execute_query("SELECT maskgate_fn_phone_last4('+1 (555) 123-4567') AS val;")
        assert res[0]["val"] == "*******4567"

        # 4 digits exactly
        res = db.execute_query("SELECT maskgate_fn_phone_last4('4567') AS val;")
        assert res[0]["val"] == "4567"

        # Less than 4 digits
        res = db.execute_query("SELECT maskgate_fn_phone_last4('123') AS val;")
        assert res[0]["val"] == "****"

        # Empty string and NULL
        assert db.execute_query("SELECT maskgate_fn_phone_last4('') AS val;")[0]["val"] == ""
        assert db.execute_query("SELECT maskgate_fn_phone_last4(NULL) AS val;")[0]["val"] is None

    def test_partial_function_sql(self, db_fn_manager):
        db_fn_manager.init_base_functions()
        # Default 2 visible chars
        res = db.execute_query("SELECT maskgate_fn_partial('sensitive_text') AS val;")
        assert res[0]["val"] == "se**********xt"

        # Custom visible_chars = 3
        res = db.execute_query("SELECT maskgate_fn_partial('sensitive_text', 3) AS val;")
        assert res[0]["val"] == "sen********ext"

        # Custom visible_chars = 4
        res4 = db.execute_query("SELECT maskgate_fn_partial('sensitive_text', 4) AS val;")
        assert res4[0]["val"] == "sens******text"

        # Short strings
        assert db.execute_query("SELECT maskgate_fn_partial('ab') AS val;")[0]["val"] == "**"
        assert db.execute_query("SELECT maskgate_fn_partial('a') AS val;")[0]["val"] == "**"
        assert db.execute_query("SELECT maskgate_fn_partial('') AS val;")[0]["val"] == ""
        assert db.execute_query("SELECT maskgate_fn_partial(NULL) AS val;")[0]["val"] is None

    def test_redact_function_sql(self, db_fn_manager):
        db_fn_manager.init_base_functions()
        res = db.execute_query("SELECT maskgate_fn_redact('confidential') AS val;")
        assert res[0]["val"] == "************"
        assert db.execute_query("SELECT maskgate_fn_redact('') AS val;")[0]["val"] == ""
        assert db.execute_query("SELECT maskgate_fn_redact(NULL) AS val;")[0]["val"] is None

    def test_hash_function_sql(self, db_fn_manager):
        db_fn_manager.init_base_functions()
        res = db.execute_query("SELECT maskgate_fn_hash('secret_token') AS val;")
        assert len(res[0]["val"]) == 64
        res_md5 = db.execute_query("SELECT maskgate_fn_hash('secret_token', 'md5') AS val;")
        assert len(res_md5[0]["val"]) == 32
        assert db.execute_query("SELECT maskgate_fn_hash(NULL) AS val;")[0]["val"] is None

    def test_none_function_sql(self, db_fn_manager):
        db_fn_manager.init_base_functions()
        res = db.execute_query("SELECT maskgate_fn_none('unmasked_value') AS val;")
        assert res[0]["val"] == "unmasked_value"


# ===========================================================================
# 2. Comprehensive End-to-End Verification of the 14 Required Cases
# ===========================================================================

class TestFourteenVerificationCases:
    """Explicitly tests and proves all 14 DB-level masking cases end-to-end."""

    def test_case_1_select_explicit_protected_column(self, masking_service, query_service):
        """Case 1: SELECT explicit protected column (SELECT email FROM patients;)."""
        policy = masking_service.create_policy(
            MaskingPolicy(
                name="patients_email",
                schema_name="public",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
            )
        )
        try:
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
                response = query_service.execute_query("SELECT email FROM patients LIMIT 3;", apply_masking=True)

            assert response.row_count > 0
            assert "email" in response.masked_columns

            executed_sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
            assert any(f"maskgate_policy_{policy.id}(email::text)" in sql for sql in executed_sqls)

            # Verify the values returned from PostgreSQL were masked in-database
            for row in response.rows:
                if row[0]:
                    assert "***@" in row[0]
        finally:
            masking_service.delete_policy(policy.id)

    def test_case_2_select_wildcard(self, masking_service, query_service):
        """Case 2: SELECT * (SELECT * FROM patients;)."""
        policy = masking_service.create_policy(
            MaskingPolicy(
                name="patients_email",
                schema_name="public",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
            )
        )
        try:
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
                response = query_service.execute_query("SELECT * FROM patients LIMIT 3;", apply_masking=True)

            assert response.row_count > 0
            assert "email" in response.masked_columns

            executed_sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
            assert any(f"maskgate_policy_{policy.id}(email::text)" in sql for sql in executed_sqls)

            email_idx = response.columns.index("email")
            for row in response.rows:
                if row[email_idx]:
                    assert "***@" in row[email_idx]
        finally:
            masking_service.delete_policy(policy.id)

    def test_case_3_multiple_protected_columns(self, masking_service, query_service):
        """Case 3: Multiple protected columns in a single table."""
        p1 = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="email", strategy="EMAIL")
        )
        p2 = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="phone", strategy="PHONE_LAST4")
        )
        p3 = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="address", strategy="PARTIAL", parameters={"visible_chars": 2})
        )
        try:
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
                response = query_service.execute_query("SELECT email, phone, address FROM patients LIMIT 3;", apply_masking=True)

            assert response.row_count > 0
            assert "email" in response.masked_columns
            assert "phone" in response.masked_columns
            assert "address" in response.masked_columns

            executed_sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
            matching_query = next(
                (sql for sql in executed_sqls if "FROM patients" in sql and f"maskgate_policy_{p1.id}" in sql), None
            )
            assert matching_query is not None
            assert f"maskgate_policy_{p1.id}(email::text)" in matching_query
            assert f"maskgate_policy_{p2.id}(phone::text)" in matching_query
            assert f"maskgate_policy_{p3.id}(address::text)" in matching_query

            email_idx = response.columns.index("email")
            phone_idx = response.columns.index("phone")
            address_idx = response.columns.index("address")

            for row in response.rows:
                if row[email_idx]:
                    assert "***@" in row[email_idx]
                if row[phone_idx]:
                    assert row[phone_idx].startswith("*")
                if row[address_idx] and len(row[address_idx]) > 4:
                    assert "*" in row[address_idx]
        finally:
            masking_service.delete_policy(p1.id)
            masking_service.delete_policy(p2.id)
            masking_service.delete_policy(p3.id)

    def test_case_4_multiple_tables_with_join(self, masking_service, query_service):
        """
        Case 4: Multiple tables with JOIN:
        SELECT p.email, p.phone, a.doctor_name
        FROM patients p
        JOIN appointments a ON p.patient_id = a.patient_id;
        """
        p1 = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="email", strategy="EMAIL")
        )
        p2 = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="phone", strategy="PHONE_LAST4")
        )
        p3 = masking_service.create_policy(
            MaskingPolicy(table_name="appointments", column_name="doctor_name", strategy="REDACT")
        )
        try:
            query = """
            SELECT p.email, p.phone, a.doctor_name
            FROM patients p
            JOIN appointments a ON p.patient_id = a.patient_id
            LIMIT 3;
            """
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
                response = query_service.execute_query(query, apply_masking=True)

            assert response.row_count > 0
            assert "email" in response.masked_columns
            assert "phone" in response.masked_columns
            assert "doctor_name" in response.masked_columns

            executed_sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
            matching_query = next(
                (sql for sql in executed_sqls if "JOIN appointments" in sql and f"maskgate_policy_{p1.id}" in sql), None
            )
            assert matching_query is not None
            assert f"maskgate_policy_{p1.id}(p.email::text) AS email" in matching_query
            assert f"maskgate_policy_{p2.id}(p.phone::text) AS phone" in matching_query
            assert f"maskgate_policy_{p3.id}(a.doctor_name::text) AS doctor_name" in matching_query

            email_idx = response.columns.index("email")
            phone_idx = response.columns.index("phone")
            doc_idx = response.columns.index("doctor_name")

            for row in response.rows:
                if row[email_idx]:
                    assert "***@" in row[email_idx]
                if row[phone_idx]:
                    assert row[phone_idx].startswith("*")
                if row[doc_idx]:
                    assert set(row[doc_idx]) == {"*"}
        finally:
            masking_service.delete_policy(p1.id)
            masking_service.delete_policy(p2.id)
            masking_service.delete_policy(p3.id)

    def test_case_5_table_aliases(self, masking_service, query_service):
        """Case 5: Table aliases (SELECT p.email FROM patients AS p and SELECT p.email FROM patients p)."""
        p = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="email", strategy="EMAIL")
        )
        try:
            # Format A: patients AS p
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db1:
                resp1 = query_service.execute_query("SELECT p.email FROM patients AS p LIMIT 2;", apply_masking=True)
            assert resp1.row_count > 0
            assert "email" in resp1.masked_columns
            sqls1 = [c[0][0] for c in spy_db1.call_args_list if isinstance(c[0][0], str)]
            assert any(f"maskgate_policy_{p.id}(p.email::text) AS email" in sql for sql in sqls1)
            assert "***@" in resp1.rows[0][0]

            # Format B: patients p (without AS)
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db2:
                resp2 = query_service.execute_query("SELECT p.email FROM patients p LIMIT 2;", apply_masking=True)
            assert resp2.row_count > 0
            assert "email" in resp2.masked_columns
            sqls2 = [c[0][0] for c in spy_db2.call_args_list if isinstance(c[0][0], str)]
            assert any(f"maskgate_policy_{p.id}(p.email::text) AS email" in sql for sql in sqls2)
            assert "***@" in resp2.rows[0][0]
        finally:
            masking_service.delete_policy(p.id)

    def test_case_6_column_aliases(self, masking_service, query_service):
        """Case 6: Column aliases (SELECT email AS patient_email FROM patients;)."""
        p = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="email", strategy="EMAIL")
        )
        try:
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
                response = query_service.execute_query(
                    "SELECT email AS patient_email FROM patients LIMIT 2;", apply_masking=True
                )
            assert response.row_count > 0
            assert "patient_email" in response.columns
            assert "patient_email" in response.masked_columns

            sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
            assert any(f"maskgate_policy_{p.id}(email::text) AS patient_email" in sql for sql in sqls)
            assert "***@" in response.rows[0][0]
        finally:
            masking_service.delete_policy(p.id)

    def test_case_7_do_not_show(self, masking_service, query_service):
        """Case 7: DO_NOT_SHOW masking policy."""
        p = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="emergency_contact", strategy="DO_NOT_SHOW")
        )
        try:
            # 7A: SELECT * excludes the hidden column from the SQL projection entirely
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db_wildcard:
                resp_wildcard = query_service.execute_query("SELECT * FROM patients LIMIT 2;", apply_masking=True)
            assert "emergency_contact" not in resp_wildcard.columns
            sqls_wildcard = [c[0][0] for c in spy_db_wildcard.call_args_list if isinstance(c[0][0], str)]
            matching_wildcard = next((sql for sql in sqls_wildcard if "FROM patients" in sql and "SELECT" in sql), "")
            assert "emergency_contact" not in matching_wildcard

            # 7B: Explicit SELECT emergency_contact returns '[HIDDEN]' directly from PostgreSQL
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db_explicit:
                resp_explicit = query_service.execute_query("SELECT emergency_contact FROM patients LIMIT 2;", apply_masking=True)
            assert resp_explicit.row_count > 0
            sqls_explicit = [c[0][0] for c in spy_db_explicit.call_args_list if isinstance(c[0][0], str)]
            assert any("'[HIDDEN]'::text AS emergency_contact" in sql for sql in sqls_explicit)
            for row in resp_explicit.rows:
                assert row[0] == "[HIDDEN]"
        finally:
            masking_service.delete_policy(p.id)

    def test_case_8_no_masking_policy(self, masking_service, query_service):
        """Case 8: No masking policy exists for queried columns."""
        # Ensure no active policy on full_name or date_of_birth
        p_name = masking_service.policy_manager.find_active_policy("patients", "full_name")
        if p_name and p_name.id:
            masking_service.delete_policy(p_name.id)
        p_dob = masking_service.policy_manager.find_active_policy("patients", "date_of_birth")
        if p_dob and p_dob.id:
            masking_service.delete_policy(p_dob.id)

        with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
            response = query_service.execute_query("SELECT full_name, date_of_birth FROM patients LIMIT 2;", apply_masking=True)

        assert response.row_count > 0
        assert len(response.masked_columns) == 0
        sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
        matching_q = next((sql for sql in sqls if "FROM patients" in sql and "SELECT full_name" in sql), "")
        assert "maskgate_policy" not in matching_q
        # Raw data returned intact
        assert response.rows[0][0] is not None
        assert response.rows[0][1] is not None

    def test_case_9_policy_edited_email_to_redact(self, masking_service, query_service):
        """Case 9: Policy edited from EMAIL → REDACT."""
        policy = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="email", strategy="EMAIL")
        )
        try:
            # 1. Initially EMAIL
            resp1 = query_service.execute_query("SELECT email FROM patients LIMIT 1;", apply_masking=True)
            assert "***@" in resp1.rows[0][0]

            # 2. Update policy to REDACT
            updated = masking_service.update_policy(
                policy.id, MaskingPolicyUpdate(strategy="REDACT", description="Switched to full redaction")
            )
            assert updated.strategy == "REDACT"

            # 3. Subsequent query immediately returns REDACT from PostgreSQL
            resp2 = query_service.execute_query("SELECT email FROM patients LIMIT 1;", apply_masking=True)
            email_val = resp2.rows[0][0]
            assert set(email_val) == {"*"}
        finally:
            masking_service.delete_policy(policy.id)

    def test_case_10_policy_edited_partial_visible_chars(self, masking_service, query_service):
        """Case 10: Policy edited from PARTIAL visible_chars=2 → visible_chars=4."""
        policy = masking_service.create_policy(
            MaskingPolicy(
                table_name="patients",
                column_name="address",
                strategy="PARTIAL",
                parameters={"visible_chars": 2},
            )
        )
        try:
            # 1. Initially visible_chars=2
            raw_addr = db.execute_query("SELECT address FROM patients LIMIT 1;")[0]["address"]
            resp1 = query_service.execute_query("SELECT address FROM patients LIMIT 1;", apply_masking=True)
            masked_addr1 = resp1.rows[0][0]
            assert masked_addr1.startswith(raw_addr[:2])
            assert masked_addr1.endswith(raw_addr[-2:])

            # 2. Update policy to visible_chars=4
            updated = masking_service.update_policy(
                policy.id, MaskingPolicyUpdate(parameters={"visible_chars": 4})
            )
            assert updated.parameters.get("visible_chars") == 4

            # 3. Subsequent query immediately returns visible_chars=4 from PostgreSQL
            resp2 = query_service.execute_query("SELECT address FROM patients LIMIT 1;", apply_masking=True)
            masked_addr2 = resp2.rows[0][0]
            assert masked_addr2.startswith(raw_addr[:4])
            assert masked_addr2.endswith(raw_addr[-4:])
        finally:
            masking_service.delete_policy(policy.id)

    def test_case_11_policy_deactivated(self, masking_service, query_service):
        """Case 11: Policy deactivated (drops function, returns raw data)."""
        policy = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="phone", strategy="PHONE_LAST4")
        )
        raw_phone = db.execute_query("SELECT phone FROM patients LIMIT 1;")[0]["phone"]

        # Masked initially
        resp1 = query_service.execute_query("SELECT phone FROM patients LIMIT 1;", apply_masking=True)
        assert resp1.rows[0][0] != raw_phone
        assert resp1.rows[0][0].startswith("*")

        # Deactivate policy
        masking_service.delete_policy(policy.id)

        # Policy deactivated -> raw phone returned
        with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
            resp2 = query_service.execute_query("SELECT phone FROM patients LIMIT 1;", apply_masking=True)
        assert resp2.rows[0][0] == raw_phone
        sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
        matching_q = next((sql for sql in sqls if "FROM patients" in sql and "SELECT phone" in sql), "")
        assert "maskgate_policy" not in matching_q

    def test_case_12_policy_reactivated(self, masking_service, query_service):
        """Case 12: Policy reactivated (recreates DB function and reapplies masking)."""
        policy = masking_service.create_policy(
            MaskingPolicy(table_name="patients", column_name="phone", strategy="PHONE_LAST4")
        )
        policy_id = policy.id
        raw_phone = db.execute_query("SELECT phone FROM patients LIMIT 1;")[0]["phone"]

        # Deactivate
        masking_service.delete_policy(policy_id)
        resp_deact = query_service.execute_query("SELECT phone FROM patients LIMIT 1;", apply_masking=True)
        assert resp_deact.rows[0][0] == raw_phone

        # Reactivate
        reactivated = masking_service.reactivate_policy(policy_id)
        assert reactivated.is_active is True

        # Masking is active again inside PostgreSQL
        with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
            resp_react = query_service.execute_query("SELECT phone FROM patients LIMIT 1;", apply_masking=True)
        sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
        assert any(f"maskgate_policy_{policy_id}(phone::text)" in sql for sql in sqls)
        assert resp_react.rows[0][0] != raw_phone
        assert resp_react.rows[0][0].startswith("*")

        # Cleanup
        masking_service.delete_policy(policy_id)

    def test_case_13_ai_recommendation_approved(self, masking_service, query_service, rec_repo):
        """Case 13: AI recommendation approved creates DB function and applies DB masking."""
        # Clean up any existing active policy on appointments.doctor_name
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
        created_policy = None
        try:
            # Approve recommendation
            created_policy = masking_service.approve_recommendation(rec.id)
            assert created_policy.id is not None
            assert created_policy.status == "ACTIVE"

            # Check DB function exists in PostgreSQL
            fn_name = f"maskgate_policy_{created_policy.id}"
            res = db.execute_query(f"SELECT {fn_name}('Dr. Gregory House') AS val;")
            assert set(res[0]["val"]) == {"*"}

            # Query appointments.doctor_name applies DB masking
            with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
                resp = query_service.execute_query("SELECT doctor_name FROM appointments LIMIT 2;", apply_masking=True)
            sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
            assert any(f"maskgate_policy_{created_policy.id}(doctor_name::text)" in sql for sql in sqls)
            assert set(resp.rows[0][0]) == {"*"}
        finally:
            if created_policy and created_policy.id:
                masking_service.delete_policy(created_policy.id)

    def test_case_14_ai_recommendation_rejected(self, masking_service, query_service, rec_repo):
        """Case 14: AI recommendation rejected creates no DB function and applies no masking."""
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
                rationale="Appointment status is not sensitive",
                status="PENDING",
            )
        )
        rejected = masking_service.reject_recommendation(rec.id)
        assert rejected.status == "REJECTED"

        # Verify no active policy
        active_p = masking_service.policy_manager.find_active_policy("appointments", "status")
        assert active_p is None

        # Verify query on appointments.status returns raw unmasked data
        with patch.object(db, "execute_query", wraps=db.execute_query) as spy_db:
            resp = query_service.execute_query("SELECT status FROM appointments LIMIT 2;", apply_masking=True)
        sqls = [c[0][0] for c in spy_db.call_args_list if isinstance(c[0][0], str)]
        matching_q = next((sql for sql in sqls if "FROM appointments" in sql and "SELECT status" in sql), "")
        assert "maskgate_policy" not in matching_q
        assert "status" not in resp.masked_columns


# ===========================================================================
# 3. Critical Security Verification (Boundary, Zero Raw Data, Python Invariant)
# ===========================================================================

class TestCriticalSecurityDBBoundary:
    """
    CRITICAL SECURITY PROOFS:
    Proves that Python receives the DB-masked value rather than the original sensitive value.
    Proves that the SQL sent to PostgreSQL contains maskgate_policy_<id>(...).
    Proves raw original sensitive values are NOT passed into Python masking for DB-masked columns.
    Proves Stage 2 runtime detection remains available for unclassified suspicious data.
    """

    def test_critical_security_raw_value_never_crosses_db_boundary_into_python(
        self, masking_service, query_service
    ):
        """
        Proof:
        1. Instrument the database execution boundary (db.execute_query).
        2. Verify the query sent to PostgreSQL executes maskgate_policy_<id>(...).
        3. Verify that the raw database return values arriving at Python are already masked.
        4. Verify raw unmasked sensitive strings NEVER crossed into Python.
        """
        # Fetch raw unmasked email for comparison
        raw_db_res = db.execute_query("SELECT email FROM patients WHERE email IS NOT NULL LIMIT 1;")
        raw_sensitive_email = raw_db_res[0]["email"]
        assert "@" in raw_sensitive_email

        policy = masking_service.create_policy(
            MaskingPolicy(
                name="critical_sec_patients_email",
                schema_name="public",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
            )
        )
        try:
            captured_db_returns = []

            orig_execute_query = db.execute_query

            def instrumented_execute(query_sql, params=None):
                result = orig_execute_query(query_sql, params)
                captured_db_returns.append({"sql": query_sql, "result": result})
                return result

            with patch.object(db, "execute_query", side_effect=instrumented_execute):
                response = query_service.execute_query(
                    "SELECT email FROM patients WHERE email IS NOT NULL LIMIT 1;",
                    apply_masking=True,
                    mask_suspicious=False,
                )

            # Find the main data SELECT execution
            main_query_execution = next(
                (c for c in captured_db_returns if "FROM patients" in c["sql"] and "WHERE email IS NOT NULL" in c["sql"]),
                None
            )
            assert main_query_execution is not None

            # 1. Verify executed SQL contains the DB-level masking function call
            assert f"maskgate_policy_{policy.id}(email::text)" in main_query_execution["sql"]

            # 2. Verify PostgreSQL returned the masked value directly across the connection boundary
            db_row = main_query_execution["result"][0]
            masked_value_from_db = db_row["email"]

            assert masked_value_from_db != raw_sensitive_email
            assert "***@" in masked_value_from_db
            assert masked_value_from_db.startswith(raw_sensitive_email[0])

            # 3. Final QueryResponse matches what PostgreSQL generated
            assert response.rows[0][0] == masked_value_from_db
        finally:
            masking_service.delete_policy(policy.id)

    def test_critical_security_python_engine_does_not_remask_db_masked_columns(
        self, masking_service, query_service
    ):
        """
        Proof:
        Python's deterministic masking engine (MaskingEngine) receives already_masked_columns
        and skips in-memory masking for columns already transformed inside PostgreSQL.
        """
        policy = masking_service.create_policy(
            MaskingPolicy(
                name="patients_phone",
                schema_name="public",
                table_name="patients",
                column_name="phone",
                strategy="PHONE_LAST4",
            )
        )
        try:
            with patch("app.masking.strategies.PhoneMaskStrategy.mask") as mock_python_phone_mask:
                response = query_service.execute_query(
                    "SELECT phone FROM patients LIMIT 2;",
                    apply_masking=True,
                    mask_suspicious=False,
                )

                assert response.row_count > 0
                assert "phone" in response.masked_columns
                # Crucial proof: Python's in-memory mask function was NOT called because DB did it!
                assert mock_python_phone_mask.call_count == 0
                # But the phone is properly masked in the response
                assert response.rows[0][0].startswith("*")
        finally:
            masking_service.delete_policy(policy.id)

    def test_critical_security_stage2_runtime_detection_still_protects_unclassified_data(
        self, masking_service, query_service
    ):
        """
        Proof:
        Stage 1 DB-level masking protects known policy columns.
        Stage 2 runtime detection remains fully active and intercepts unclassified sensitive data
        in unstructured or unconfigured columns, while excluding already DB-masked columns.
        """
        policy = masking_service.create_policy(
            MaskingPolicy(
                name="patients_email",
                schema_name="public",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
            )
        )
        # Create a temporary medical record with unclassified PII (SSN) in notes
        patient_id = db.execute_query("SELECT patient_id FROM patients LIMIT 1;")[0]["patient_id"]
        ins_res = db.execute_query(
            """
            INSERT INTO medical_records (patient_id, diagnosis, medication, allergies, notes, visit_date)
            VALUES (%s, 'Routine Checkup', 'None', 'None', 'Patient SSN is 123-45-6789', '2025-01-01')
            RETURNING record_id;
            """,
            (patient_id,),
        )
        rec_id = ins_res[0]["record_id"]

        try:
            # Query combining DB-masked column (email) and unclassified column (notes)
            query = f"""
            SELECT p.email, m.notes
            FROM patients p
            JOIN medical_records m ON p.patient_id = m.patient_id
            WHERE m.record_id = {rec_id};
            """
            with patch("app.ai.llm.llm_client.is_available", return_value=False), \
                 patch("app.ai.sensitive_data_detector.llm_client.is_available", return_value=False):
                response = query_service.execute_query(
                    query, apply_masking=True, mask_suspicious=True
                )

            assert response.row_count == 1
            email_val = response.rows[0][0]
            notes_val = response.rows[0][1]

            # 1. DB-masked email
            assert "***@" in email_val

            # 2. Stage 2 runtime-detected unclassified SSN in notes was masked
            assert "123-45-6789" not in notes_val
            assert "*" in notes_val

            # 3. Masked columns tracks both DB-level and runtime-detected columns
            assert "email" in response.masked_columns
            assert "notes" in response.masked_columns
            assert "Pattern matching" in response.runtime_detection_summary
        finally:
            masking_service.delete_policy(policy.id)
            db.execute_update("DELETE FROM medical_records WHERE record_id = %s;", (rec_id,))


# ===========================================================================
# 4. API Endpoint Integration Tests (PUT /policies/{id}, etc.)
# ===========================================================================

class TestPolicyEditAPI:
    """Integration tests for PUT /api/v1/masking/policies/{id} endpoint."""

    def test_api_create_and_edit_policy(self, client):
        # 1. Create policy
        create_payload = {
            "name": "api_test_patient_phone",
            "schema_name": "public",
            "table_name": "patients",
            "column_name": "phone",
            "strategy": "PHONE_LAST4",
            "sensitivity": "HIGH",
        }
        res = client.post("/api/v1/masking/policies", json=create_payload)
        assert res.status_code == 201
        policy_id = res.json()["id"]

        # 2. Query editor test with PHONE_LAST4
        q_res = client.post(
            "/api/v1/query",
            json={"query": "SELECT phone FROM patients LIMIT 1;", "apply_masking": True},
        )
        assert q_res.status_code == 200
        phone_val = q_res.json()["rows"][0][0]
        if phone_val:
            assert phone_val.startswith("*")

        # 3. Edit policy via PUT endpoint to REDACT
        update_payload = {
            "strategy": "REDACT",
            "sensitivity": "HIGH",
            "description": "Updated via API to full redaction",
        }
        put_res = client.put(f"/api/v1/masking/policies/{policy_id}", json=update_payload)
        assert put_res.status_code == 200
        assert put_res.json()["strategy"] == "REDACT"

        # 4. Query editor test immediately reflects REDACT behavior
        q_res2 = client.post(
            "/api/v1/query",
            json={"query": "SELECT phone FROM patients LIMIT 1;", "apply_masking": True},
        )
        assert q_res2.status_code == 200
        phone_val2 = q_res2.json()["rows"][0][0]
        if phone_val2:
            assert set(phone_val2) == {"*"}

        # 5. Cleanup (Delete policy)
        del_res = client.delete(f"/api/v1/masking/policies/{policy_id}")
        assert del_res.status_code == 200

    def test_api_edit_policy_not_found(self, client):
        res = client.put("/api/v1/masking/policies/999999", json={"strategy": "REDACT"})
        assert res.status_code == 404

    def test_api_edit_policy_invalid_strategy(self, client):
        # Create a temp policy first
        create_res = client.post(
            "/api/v1/masking/policies",
            json={
                "table_name": "patients",
                "column_name": "phone",
                "strategy": "PHONE_LAST4",
            },
        )
        pid = create_res.json()["id"]

        # Attempt invalid strategy
        res = client.put(
            f"/api/v1/masking/policies/{pid}",
            json={"strategy": "MALICIOUS_DROP_TABLE"},
        )
        assert res.status_code == 400
        assert "Invalid masking strategy" in res.json()["detail"]

        # Cleanup
        client.delete(f"/api/v1/masking/policies/{pid}")


# ===========================================================================
# 5. Security & Injection Protection Tests
# ===========================================================================

class TestSecurityAndInjectionProtections:
    """Verify security controls against SQL injection in functions and identifiers."""

    def test_invalid_policy_id_raises_value_error(self, db_fn_manager):
        with pytest.raises(ValueError):
            db_fn_manager.get_function_name(-1)
        with pytest.raises(ValueError):
            db_fn_manager.get_function_name("not_an_int")

    def test_sql_injection_attempt_in_strategy_rejected(self, masking_service):
        with pytest.raises(ValueError) as exc:
            masking_service.create_policy(
                MaskingPolicy(
                    table_name="patients",
                    column_name="email",
                    strategy="EMAIL'; DROP TABLE users; --",
                )
            )
        assert "Invalid masking strategy" in str(exc.value)

    def test_sql_injection_attempt_in_parameters_sanitized(self, db_fn_manager):
        policy = MaskingPolicy(
            id=9999,
            table_name="patients",
            column_name="email",
            strategy="PARTIAL",
            parameters={"visible_chars": "2; DROP TABLE users; --"},
        )
        # Should sanitize string to default int 2 safely without executing injection
        fn_name = db_fn_manager.create_or_replace_policy_function(policy)
        assert fn_name == "maskgate_policy_9999"

        # Verify users table still exists
        assert db.table_exists("users") is True
        db_fn_manager.drop_policy_function(9999)
