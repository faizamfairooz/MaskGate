import datetime
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.masking.strategies import (
    MaskingStrategyFactory,
    NoneMaskStrategy,
    RedactionStrategy,
    PartialMaskStrategy,
    EmailMaskStrategy,
    PhoneMaskStrategy,
)
from app.masking.engine import MaskingEngine
from app.schemas.masking import MaskingPolicy
from app.services.query_service import QueryService
from app.database.postgresql import db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def strategy_factory():
    return MaskingStrategyFactory()


@pytest.fixture
def masking_engine():
    return MaskingEngine()


@pytest.fixture
def query_service():
    return QueryService()


# ---------------------------------------------------------------------------
# Unit Tests: Strategy Masking Behavior
# ---------------------------------------------------------------------------

class TestDeterministicStrategies:
    """Unit tests for the five standard deterministic masking strategies."""

    def test_none_strategy(self, strategy_factory):
        strategy = strategy_factory.get_strategy("NONE")
        assert isinstance(strategy, NoneMaskStrategy)
        assert strategy.mask("john.smith@gmail.com", {}) == "john.smith@gmail.com"
        assert strategy.mask(12345, {}) == 12345
        assert strategy.mask(None, {}) is None
        assert strategy.mask("", {}) == ""
        assert strategy.mask(True, {}) is True

    def test_redact_strategy(self, strategy_factory):
        strategy = strategy_factory.get_strategy("REDACT")
        assert isinstance(strategy, RedactionStrategy)
        assert strategy.mask("secret", {}) == "******"
        assert strategy.mask("12345", {}) == "*****"
        assert strategy.mask("", {}) == ""
        assert strategy.mask(None, {}) is None
        assert strategy.mask(123, {}) == "***"
        assert strategy.mask(True, {}) == "****"

    def test_partial_strategy(self, strategy_factory):
        strategy = strategy_factory.get_strategy("PARTIAL")
        assert isinstance(strategy, PartialMaskStrategy)
        # Default 2 visible characters on each side
        assert strategy.mask("sensitive_text", {}) == "se**********xt"
        # Custom visible_chars parameter
        assert strategy.mask("sensitive_text", {"visible_chars": 3}) == "sen********ext"
        # Short strings
        assert strategy.mask("ab", {}) == "**"
        assert strategy.mask("a", {}) == "**"
        assert strategy.mask("", {}) == ""
        assert strategy.mask(None, {}) is None

    def test_email_strategy(self, strategy_factory):
        strategy = strategy_factory.get_strategy("EMAIL")
        assert isinstance(strategy, EmailMaskStrategy)
        assert strategy.mask("john.smith@gmail.com", {}) == "j***@gmail.com"
        assert strategy.mask("alice@hospital.org", {}) == "a***@hospital.org"
        assert strategy.mask("a@b.com", {}) == "a***@b.com"
        assert strategy.mask("invalidemail", {}) == "***@***.***"
        assert strategy.mask("@domain.com", {}) == "@domain.com"
        assert strategy.mask("", {}) == ""
        assert strategy.mask(None, {}) is None

    def test_phone_last4_strategy(self, strategy_factory):
        strategy = strategy_factory.get_strategy("PHONE_LAST4")
        assert isinstance(strategy, PhoneMaskStrategy)
        assert strategy.mask("0771234567", {}) == "******4567"
        assert strategy.mask("+1 (555) 123-4567", {}) == "*******4567"
        assert strategy.mask("1234", {}) == "1234"
        assert strategy.mask("123", {}) == "****"
        assert strategy.mask("", {}) == ""
        assert strategy.mask(None, {}) is None

    def test_strategy_factory_case_and_aliases(self, strategy_factory):
        assert isinstance(strategy_factory.get_strategy("none"), NoneMaskStrategy)
        assert isinstance(strategy_factory.get_strategy("NONE"), NoneMaskStrategy)
        assert isinstance(strategy_factory.get_strategy("redact"), RedactionStrategy)
        assert isinstance(strategy_factory.get_strategy("REDACT"), RedactionStrategy)
        assert isinstance(strategy_factory.get_strategy("redaction"), RedactionStrategy)
        assert isinstance(strategy_factory.get_strategy("partial"), PartialMaskStrategy)
        assert isinstance(strategy_factory.get_strategy("PARTIAL"), PartialMaskStrategy)
        assert isinstance(strategy_factory.get_strategy("email"), EmailMaskStrategy)
        assert isinstance(strategy_factory.get_strategy("EMAIL"), EmailMaskStrategy)
        assert isinstance(strategy_factory.get_strategy("phone_last4"), PhoneMaskStrategy)
        assert isinstance(strategy_factory.get_strategy("PHONE_LAST4"), PhoneMaskStrategy)
        assert isinstance(strategy_factory.get_strategy("phone"), PhoneMaskStrategy)

    def test_invalid_strategy_raises_value_error(self, strategy_factory):
        with pytest.raises(ValueError, match="Unknown masking strategy"):
            strategy_factory.get_strategy("UNRECOGNIZED_STRATEGY")


# ---------------------------------------------------------------------------
# Unit Tests: Value Type Safety
# ---------------------------------------------------------------------------

class TestValueTypeSafety:
    """Ensure strategies handle unexpected data types without crashing."""

    def test_integer_values(self, strategy_factory):
        assert strategy_factory.get_strategy("NONE").mask(98765, {}) == 98765
        assert strategy_factory.get_strategy("REDACT").mask(98765, {}) == "*****"
        assert strategy_factory.get_strategy("PHONE_LAST4").mask(9876543210, {}) == "******3210"

    def test_float_values(self, strategy_factory):
        assert strategy_factory.get_strategy("NONE").mask(123.45, {}) == 123.45
        assert strategy_factory.get_strategy("REDACT").mask(123.45, {}) == "******"

    def test_boolean_values(self, strategy_factory):
        assert strategy_factory.get_strategy("NONE").mask(True, {}) is True
        assert strategy_factory.get_strategy("NONE").mask(False, {}) is False
        assert strategy_factory.get_strategy("REDACT").mask(True, {}) == "****"

    def test_date_values(self, strategy_factory):
        sample_date = datetime.date(2025, 8, 16)
        assert strategy_factory.get_strategy("NONE").mask(sample_date, {}) == sample_date
        assert strategy_factory.get_strategy("REDACT").mask(sample_date, {}) == "**********"


# ---------------------------------------------------------------------------
# Unit Tests: Masking Engine Rules & Immutability
# ---------------------------------------------------------------------------

class TestMaskingEngineRules:
    """Unit tests for engine execution, policy filtering, and immutability."""

    def test_inactive_and_disabled_policies_ignored(self, masking_engine):
        data = [[1, "alice@test.com", "0771112222", "patient-note"]]
        columns = ["id", "email", "phone", "notes"]

        policies = [
            MaskingPolicy(
                name="inactive_email_policy",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
                status="ACTIVE",
                is_active=False,  # Inactive
            ),
            MaskingPolicy(
                name="disabled_phone_policy",
                table_name="patients",
                column_name="phone",
                strategy="PHONE_LAST4",
                status="DISABLED",  # Disabled status
                is_active=True,
            ),
            MaskingPolicy(
                name="active_notes_policy",
                table_name="patients",
                column_name="notes",
                strategy="REDACT",
                status="ACTIVE",
                is_active=True,
            ),
        ]

        masked_data, masked_cols, _ = masking_engine.apply_masking(data, columns, policies)

        # Inactive & disabled policies should NOT mask
        assert masked_data[0][1] == "alice@test.com"
        assert masked_data[0][2] == "0771112222"
        # Only active policy masks
        assert masked_data[0][3] == "************"
        assert masked_cols == ["notes"]

    def test_unrelated_columns_not_masked(self, masking_engine):
        data = [[10, "John Doe", "Cardiology"]]
        columns = ["id", "full_name", "department"]

        policies = [
            MaskingPolicy(
                name="email_policy",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
                status="ACTIVE",
                is_active=True,
            )
        ]

        masked_data, masked_cols, _ = masking_engine.apply_masking(data, columns, policies)
        assert masked_data == [[10, "John Doe", "Cardiology"]]
        assert masked_cols == []

    def test_multiple_active_policies_applied_simultaneously(self, masking_engine):
        data = [
            [1, "john.smith@gmail.com", "0771234567", "Sensitive Diagnosis 1"],
            [2, "sarah.connor@sky.net", "0719876543", "Sensitive Diagnosis 2"],
        ]
        columns = ["id", "email", "phone", "diagnosis"]

        policies = [
            MaskingPolicy(
                name="email_pol",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
                status="ACTIVE",
                is_active=True,
            ),
            MaskingPolicy(
                name="phone_pol",
                table_name="patients",
                column_name="phone",
                strategy="PHONE_LAST4",
                status="ACTIVE",
                is_active=True,
            ),
            MaskingPolicy(
                name="diag_pol",
                table_name="patients",
                column_name="diagnosis",
                strategy="PARTIAL",
                status="ACTIVE",
                is_active=True,
            ),
        ]

        masked_data, masked_cols, _ = masking_engine.apply_masking(data, columns, policies)

        assert masked_data[0][0] == 1
        assert masked_data[0][1] == "j***@gmail.com"
        assert masked_data[0][2] == "******4567"
        assert masked_data[0][3] == "Se***************** 1"

        assert masked_data[1][0] == 2
        assert masked_data[1][1] == "s***@sky.net"
        assert masked_data[1][2] == "******6543"
        assert masked_data[1][3] == "Se***************** 2"

        assert set(masked_cols) == {"email", "phone", "diagnosis"}

    def test_input_dataset_immutability(self, masking_engine):
        original_row = [1, "john.smith@gmail.com", "0771234567"]
        data = [original_row]
        columns = ["id", "email", "phone"]

        policies = [
            MaskingPolicy(
                name="email_pol",
                table_name="patients",
                column_name="email",
                strategy="EMAIL",
                status="ACTIVE",
                is_active=True,
            )
        ]

        masked_data, _, _ = masking_engine.apply_masking(data, columns, policies)

        # Original data list and inner row must NOT be modified
        assert original_row[1] == "john.smith@gmail.com"
        assert data[0][1] == "john.smith@gmail.com"
        assert masked_data[0][1] == "j***@gmail.com"
        assert masked_data is not data
        assert masked_data[0] is not original_row


# ---------------------------------------------------------------------------
# Unit Tests: SQL Validation & Table Extraction
# ---------------------------------------------------------------------------

class TestQueryValidationAndExtraction:
    """Unit tests for SELECT-only security validation and table extraction."""

    def test_validate_query_allows_select_and_cte(self, query_service):
        assert query_service.validate_query("SELECT * FROM patients")[0] is True
        assert query_service.validate_query("SELECT email, phone FROM public.patients WHERE id = 1")[0] is True
        assert query_service.validate_query("WITH cte AS (SELECT 1 AS id) SELECT * FROM cte")[0] is True

    def test_validate_query_rejects_mutations_and_ddl(self, query_service):
        assert query_service.validate_query("INSERT INTO patients (email) VALUES ('x')")[0] is False
        assert query_service.validate_query("UPDATE patients SET email = 'x'")[0] is False
        assert query_service.validate_query("DELETE FROM patients WHERE id = 1")[0] is False
        assert query_service.validate_query("DROP TABLE patients")[0] is False
        assert query_service.validate_query("TRUNCATE TABLE patients")[0] is False
        assert query_service.validate_query("ALTER TABLE patients ADD COLUMN x text")[0] is False
        assert query_service.validate_query("CREATE TABLE test (id int)")[0] is False

    def test_validate_query_rejects_multiple_statements(self, query_service):
        assert query_service.validate_query("SELECT 1; DROP TABLE patients;")[0] is False

    def test_table_and_schema_extraction(self, query_service):
        assert query_service._extract_table_and_schema("SELECT * FROM patients") == ("public", "patients")
        assert query_service._extract_table_and_schema("SELECT email FROM public.patients") == ("public", "patients")
        assert query_service._extract_table_and_schema('SELECT * FROM "public"."patients"') == ("public", "patients")
        assert query_service._extract_table_and_schema("SELECT * FROM clinical.records") == ("clinical", "records")


# ---------------------------------------------------------------------------
# Integration Tests: PostgreSQL Query Execution & Zero Database Mutation
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeterministicMaskingPostgreSQLIntegration:
    """Integration tests verifying query masking against PostgreSQL and zero database mutation."""

    def test_e2e_query_masking_preserves_postgresql_records(self, client):
        # 1. Verify direct PostgreSQL records exist
        raw_rows = db.execute_query("SELECT patient_id, email, phone FROM patients ORDER BY patient_id LIMIT 1")
        assert len(raw_rows) > 0
        patient_id = raw_rows[0]["patient_id"]
        original_email = raw_rows[0]["email"]
        original_phone = raw_rows[0]["phone"]

        # Ensure we have test email and phone
        assert "@" in str(original_email)
        assert original_phone is not None

        # 2. Ensure ACTIVE policies exist for patients.email (EMAIL) and patients.phone (PHONE_LAST4)
        from app.database.repositories import PolicyRepository
        repo = PolicyRepository()

        email_policy = MaskingPolicy(
            name="patients.email",
            description="Mask patient email",
            schema_name="public",
            table_name="patients",
            column_name="email",
            strategy="EMAIL",
            status="ACTIVE",
            is_active=True,
        )
        phone_policy = MaskingPolicy(
            name="patients.phone",
            description="Mask patient phone",
            schema_name="public",
            table_name="patients",
            column_name="phone",
            strategy="PHONE_LAST4",
            status="ACTIVE",
            is_active=True,
        )
        repo.create_policy(email_policy)
        repo.create_policy(phone_policy)

        # 3. Execute query via API
        response = client.post(
            "/api/v1/query",
            json={
                "query": f"SELECT patient_id, email, phone FROM patients WHERE patient_id = {patient_id}",
                "apply_masking": True,
                "mask_suspicious": False,
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert "rows" in data
        assert len(data["rows"]) == 1
        masked_row = data["rows"][0]
        col_indices = {col: i for i, col in enumerate(data["columns"])}

        masked_email = masked_row[col_indices["email"]]
        masked_phone = masked_row[col_indices["phone"]]

        # 4. Verify returned results ARE masked
        assert masked_email != original_email
        assert "@" in masked_email
        assert masked_email.startswith(original_email[0])
        assert "***" in masked_email

        assert masked_phone != original_phone
        assert masked_phone.endswith(str(original_phone)[-4:])
        assert "****" in masked_phone

        # 5. ZERO DATABASE MUTATION VERIFICATION:
        # Query PostgreSQL directly and verify the original records in the database are UNCHANGED!
        db_rows_after = db.execute_query(
            f"SELECT patient_id, email, phone FROM patients WHERE patient_id = {patient_id}"
        )
        assert len(db_rows_after) == 1
        assert db_rows_after[0]["email"] == original_email
        assert db_rows_after[0]["phone"] == original_phone
