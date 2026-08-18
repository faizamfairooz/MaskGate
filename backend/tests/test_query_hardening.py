import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.config.settings import settings
from app.database.postgresql import db
from app.database.repositories import PolicyRepository, RecommendationRepository
from app.masking.engine import MaskingEngine
from app.masking.strategies import MaskingStrategyFactory, DoNotShowStrategy
from app.schemas.masking import MaskingPolicy, MaskingRecommendation
from app.services.query_service import QueryService
from app.utils.query_parser import SQLQueryParser


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def parser():
    return SQLQueryParser()


@pytest.fixture
def query_service():
    return QueryService()


@pytest.fixture
def policy_repo():
    return PolicyRepository()


# ===========================================================================
# 1. SQL Parser & Default LIMIT Unit Tests
# ===========================================================================

class TestSQLQueryParserUnit:
    """Unit tests for SQL query parser: table extraction, outer limit detection, and default limit."""

    def test_has_outer_limit_true(self, parser):
        assert parser.has_outer_limit("SELECT * FROM patients LIMIT 10") is True
        assert parser.has_outer_limit("SELECT * FROM patients WHERE id = 1 ORDER BY id DESC LIMIT 5;") is True
        assert parser.has_outer_limit("SELECT * FROM patients LIMIT 100 OFFSET 20") is True

    def test_has_outer_limit_false(self, parser):
        assert parser.has_outer_limit("SELECT * FROM patients") is False
        assert parser.has_outer_limit("SELECT * FROM patients WHERE id = 1") is False
        assert parser.has_outer_limit("SELECT * FROM patients ORDER BY created_at DESC") is False
        assert parser.has_outer_limit("SELECT * FROM patients OFFSET 10") is False

    def test_has_outer_limit_ignores_subquery_limit(self, parser):
        # LIMIT inside subquery should NOT count as outer LIMIT
        query = "SELECT * FROM (SELECT * FROM patients LIMIT 5) sub"
        assert parser.has_outer_limit(query) is False

        query_with_where_subquery = "SELECT * FROM patients WHERE email IN (SELECT email FROM users LIMIT 3)"
        assert parser.has_outer_limit(query_with_where_subquery) is False

        # Outer limit present alongside inner limit
        query_both = "SELECT * FROM (SELECT * FROM patients LIMIT 5) sub LIMIT 10"
        assert parser.has_outer_limit(query_both) is True

    def test_apply_default_limit_without_limit(self, parser):
        assert parser.apply_default_limit("SELECT * FROM patients", 100) == "SELECT * FROM patients LIMIT 100"
        assert parser.apply_default_limit("SELECT * FROM patients;", 100) == "SELECT * FROM patients LIMIT 100;"
        assert parser.apply_default_limit("SELECT * FROM patients WHERE id > 5 ORDER BY id DESC", 50) == "SELECT * FROM patients WHERE id > 5 ORDER BY id DESC LIMIT 50"

    def test_apply_default_limit_preserves_existing_limit(self, parser):
        assert parser.apply_default_limit("SELECT * FROM patients LIMIT 10", 100) == "SELECT * FROM patients LIMIT 10"
        assert parser.apply_default_limit("SELECT * FROM patients LIMIT 500;", 100) == "SELECT * FROM patients LIMIT 500;"

    def test_apply_default_limit_preserves_offset(self, parser):
        query = "SELECT * FROM patients OFFSET 20"
        rewritten = parser.apply_default_limit(query, 100)
        assert "OFFSET 20" in rewritten
        assert "LIMIT 100" in rewritten

    def test_apply_default_limit_with_cte(self, parser):
        cte_query = "WITH recent_patients AS (SELECT * FROM patients WHERE created_at IS NOT NULL) SELECT * FROM recent_patients"
        rewritten = parser.apply_default_limit(cte_query, 100)
        assert rewritten.endswith("LIMIT 100")

    def test_extract_tables_single(self, parser):
        tables = parser.extract_tables("SELECT * FROM patients")
        assert len(tables) == 1
        assert tables[0].table_name == "patients"
        assert tables[0].schema_name == "public"

    def test_extract_tables_with_schema_and_alias(self, parser):
        tables = parser.extract_tables("SELECT p.email FROM public.patients AS p")
        assert len(tables) == 1
        assert tables[0].table_name == "patients"
        assert tables[0].schema_name == "public"
        assert tables[0].alias == "p"

    def test_extract_tables_multi_join(self, parser):
        query = """
        SELECT p.full_name, p.email, m.diagnosis
        FROM patients p
        JOIN medical_records m ON p.patient_id = m.patient_id
        LEFT JOIN appointments a ON p.patient_id = a.patient_id
        """
        tables = parser.extract_tables(query)
        table_names = {t.table_name for t in tables}
        assert "patients" in table_names
        assert "medical_records" in table_names
        assert "appointments" in table_names


# ===========================================================================
# 2. DO_NOT_SHOW Strategy & Engine Tests
# ===========================================================================

class TestDoNotShowStrategyAndEngine:
    """Unit tests for DO_NOT_SHOW strategy and in-memory engine column removal."""

    def test_strategy_factory_resolves_donotshow(self):
        factory = MaskingStrategyFactory()
        strat1 = factory.get_strategy("DO_NOT_SHOW")
        strat2 = factory.get_strategy("do_not_show")
        strat3 = factory.get_strategy("HIDE")
        strat4 = factory.get_strategy("HIDDEN")
        assert isinstance(strat1, DoNotShowStrategy)
        assert isinstance(strat2, DoNotShowStrategy)
        assert isinstance(strat3, DoNotShowStrategy)
        assert isinstance(strat4, DoNotShowStrategy)

    def test_available_strategies_includes_donotshow(self):
        factory = MaskingStrategyFactory()
        strategies = factory.get_available_strategies()
        assert "DO_NOT_SHOW" in strategies
        assert "Exclude column" in strategies["DO_NOT_SHOW"]

    def test_engine_in_memory_donotshow_column_removal(self):
        engine = MaskingEngine()
        columns = ["id", "username", "ssn", "email"]
        data = [
            [1, "alice", "123-45-6789", "alice@example.com"],
            [2, "bob", "987-65-4321", "bob@example.com"],
        ]
        policies = [
            MaskingPolicy(
                name="hide_ssn",
                table_name="users",
                column_name="ssn",
                strategy="DO_NOT_SHOW",
                status="ACTIVE",
                is_active=True,
            ),
            MaskingPolicy(
                name="mask_email",
                table_name="users",
                column_name="email",
                strategy="EMAIL",
                status="ACTIVE",
                is_active=True,
            )
        ]

        masked_data, masked_cols, _ = engine.apply_masking(data, columns, policies)

        # SSN column and cells must be completely removed from columns and rows!
        assert columns == ["id", "username", "email"]
        assert len(masked_data[0]) == 3
        assert masked_data[0] == [1, "alice", "a***@example.com"]
        assert masked_data[1] == [2, "bob", "b***@example.com"]
        assert "ssn" in masked_cols
        assert "email" in masked_cols

    def test_query_parser_rewrites_select_star_for_hidden_columns(self, parser):
        hidden_cols = {"users": {"ssn", "password_hash"}}
        def fake_get_columns(tbl, schema):
            if tbl == "users":
                return ["id", "username", "email", "ssn", "password_hash", "full_name"]
            return []

        rewritten, was_rewritten = parser.rewrite_for_hidden_columns(
            "SELECT * FROM users",
            hidden_cols,
            fake_get_columns
        )
        assert was_rewritten is True
        assert "ssn" not in rewritten
        assert "password_hash" not in rewritten
        assert "id" in rewritten
        assert "username" in rewritten
        assert "email" in rewritten
        assert "full_name" in rewritten


# ===========================================================================
# 3. Query Service & Integration Tests
# ===========================================================================

@pytest.mark.integration
class TestQueryHardeningIntegration:
    """Integration tests verifying default LIMIT, multi-table JOIN policies, DO_NOT_SHOW, and security."""

    def test_query_without_limit_applies_default_limit(self, client):
        response = client.post(
            "/api/v1/query",
            json={"query": "SELECT patient_id, full_name FROM patients", "apply_masking": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert "rows" in data
        assert data["row_count"] <= 100

    def test_query_with_existing_limit_preserved(self, client):
        response = client.post(
            "/api/v1/query",
            json={"query": "SELECT patient_id, full_name FROM patients LIMIT 2", "apply_masking": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["rows"]) <= 2

    def test_query_with_offset_preserved(self, client):
        response = client.post(
            "/api/v1/query",
            json={"query": "SELECT patient_id FROM patients OFFSET 1", "apply_masking": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert "rows" in data

    def test_multi_table_join_policies_applied(self, client, policy_repo):
        # 1. Create active policy on patients.email and medical_records.diagnosis
        p1 = MaskingPolicy(
            name="patients.email",
            table_name="patients",
            column_name="email",
            strategy="EMAIL",
            status="ACTIVE",
            is_active=True
        )
        p2 = MaskingPolicy(
            name="medical_records.diagnosis",
            table_name="medical_records",
            column_name="diagnosis",
            strategy="PARTIAL",
            status="ACTIVE",
            is_active=True
        )
        policy_repo.create_policy(p1)
        policy_repo.create_policy(p2)

        # 2. Execute JOIN query
        join_query = """
        SELECT p.patient_id, p.email, m.diagnosis
        FROM patients p
        JOIN medical_records m ON p.patient_id = m.patient_id
        LIMIT 5
        """
        response = client.post(
            "/api/v1/query",
            json={"query": join_query, "apply_masking": True}
        )
        assert response.status_code == 200
        data = response.json()

        if data["rows"]:
            email_idx = data["columns"].index("email")
            diag_idx = data["columns"].index("diagnosis")
            first_row = data["rows"][0]
            masked_email = first_row[email_idx]
            masked_diag = first_row[diag_idx]

            assert "@" in masked_email
            assert "***" in masked_email
            assert "*" in masked_diag
            assert "email" in data["masked_columns"]
            assert "diagnosis" in data["masked_columns"]

    def test_do_not_show_policy_excludes_column(self, client, policy_repo):
        # Create DO_NOT_SHOW policy on patients.address
        p = MaskingPolicy(
            name="patients.address",
            table_name="patients",
            column_name="address",
            strategy="DO_NOT_SHOW",
            status="ACTIVE",
            is_active=True
        )
        policy_repo.create_policy(p)

        response = client.post(
            "/api/v1/query",
            json={"query": "SELECT * FROM patients LIMIT 5", "apply_masking": True}
        )
        assert response.status_code == 200
        data = response.json()
        # 'address' must not appear in the returned columns
        assert "address" not in data["columns"]

    def test_security_select_only_blocks_mutations(self, client):
        mutations = [
            "INSERT INTO patients (full_name) VALUES ('Hacker')",
            "UPDATE patients SET full_name = 'Hacker'",
            "DELETE FROM patients WHERE patient_id = 1",
            "DROP TABLE patients",
            "TRUNCATE TABLE patients",
            "ALTER TABLE patients ADD COLUMN test text",
        ]
        for sql in mutations:
            response = client.post("/api/v1/query", json={"query": sql})
            assert response.status_code == 400
            assert "disallowed" in response.json()["detail"].lower() or "only select" in response.json()["detail"].lower()

    def test_security_multiple_statements_blocked(self, client):
        response = client.post("/api/v1/query", json={"query": "SELECT 1; SELECT 2;"})
        assert response.status_code == 400
        assert "Multiple statements" in response.json()["detail"]

        response_drop = client.post("/api/v1/query", json={"query": "SELECT 1; DROP TABLE patients;"})
        assert response_drop.status_code == 400


# ===========================================================================
# 4. Schema and Masking Policy API Endpoints Tests
# ===========================================================================

class TestSchemaAndPolicyAPIEndpoints:
    """API endpoint tests for schema/table/column/strategy discovery and policy management."""

    def test_get_schemas_endpoint(self, client):
        response = client.get("/api/v1/schema/schemas")
        assert response.status_code == 200
        schemas = response.json()
        assert isinstance(schemas, list)
        assert "public" in schemas

    def test_get_tables_endpoint(self, client):
        response = client.get("/api/v1/schema/tables?schema=public")
        assert response.status_code == 200
        tables = response.json()
        assert isinstance(tables, list)
        assert "patients" in tables

    def test_get_table_schema_columns_endpoint(self, client):
        response = client.get("/api/v1/schema/tables/patients?schema=public")
        assert response.status_code == 200
        data = response.json()
        assert data["table_name"] == "patients"
        column_names = [c["column_name"] for c in data["columns"]]
        assert "email" in column_names
        assert "phone" in column_names

    def test_get_strategies_endpoint(self, client):
        response = client.get("/api/v1/masking/strategies")
        assert response.status_code == 200
        strategies = response.json()
        assert "EMAIL" in strategies
        assert "PHONE_LAST4" in strategies
        assert "PARTIAL" in strategies
        assert "REDACT" in strategies
        assert "DO_NOT_SHOW" in strategies

    def test_manual_policy_creation_and_retrieval(self, client):
        payload = {
            "name": "patients.blood_group",
            "description": "Redact blood group",
            "schema_name": "public",
            "table_name": "patients",
            "column_name": "blood_group",
            "strategy": "REDACT",
            "status": "ACTIVE",
            "source": "admin_manual",
            "is_active": True
        }
        create_res = client.post("/api/v1/masking/policies", json=payload)
        assert create_res.status_code == 201
        created = create_res.json()
        assert created["table_name"] == "patients"
        assert created["column_name"] == "blood_group"
        assert created["strategy"] == "REDACT"

        # Verify in list
        list_res = client.get("/api/v1/masking/policies")
        assert list_res.status_code == 200
        policies = list_res.json()
        matching = [p for p in policies if p["table_name"] == "patients" and p["column_name"] == "blood_group"]
        assert len(matching) > 0
