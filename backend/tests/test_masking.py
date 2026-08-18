import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.masking.strategies import MaskingStrategyFactory
from app.masking.policies import PolicyManager
from app.schemas.masking import MaskingPolicy
from app.services.query_service import QueryService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def strategy_factory():
    return MaskingStrategyFactory()


@pytest.fixture
def policy_manager():
    mock_repo = MagicMock()
    manager = PolicyManager(repository=mock_repo)
    return manager, mock_repo


def test_redaction_strategy(strategy_factory):
    strategy = strategy_factory.get_strategy("redaction")
    masked = strategy.mask("hello world", {})
    assert masked == "***********"
    assert strategy.mask(None, {}) is None


def test_redaction_strategy_with_numbers(strategy_factory):
    strategy = strategy_factory.get_strategy("redaction")
    masked = strategy.mask("1234567890", {})
    assert masked == "**********"


def test_redaction_strategy_with_empty_string(strategy_factory):
    strategy = strategy_factory.get_strategy("redaction")
    masked = strategy.mask("", {})
    assert masked == ""


def test_partial_mask_strategy(strategy_factory):
    strategy = strategy_factory.get_strategy("partial_mask")
    masked = strategy.mask("hello world", {})
    assert masked.startswith("h")
    assert masked.endswith("d")
    assert "*" in masked


def test_partial_mask_strategy_with_parameters(strategy_factory):
    strategy = strategy_factory.get_strategy("partial_mask")
    masked = strategy.mask("hello world", {"visible_chars": 3})
    assert masked.startswith("hel")
    assert masked.endswith("rld")
    assert "*" in masked


def test_partial_mask_strategy_short_string(strategy_factory):
    strategy = strategy_factory.get_strategy("partial_mask")
    masked = strategy.mask("hi", {})
    assert masked == "**"


def test_hash_strategy(strategy_factory):
    strategy = strategy_factory.get_strategy("hash")
    original = "sensitive_data"
    masked = strategy.mask(original, {})
    assert masked != original
    assert len(masked) == 64


def test_email_mask_strategy(strategy_factory):
    strategy = strategy_factory.get_strategy("email_mask")
    masked = strategy.mask("john.smith@gmail.com", {})
    assert masked == "j***@gmail.com"


def test_email_mask_strategy_with_short_local(strategy_factory):
    strategy = strategy_factory.get_strategy("email_mask")
    masked = strategy.mask("a@example.com", {})
    assert masked == "a***@example.com"


def test_email_mask_strategy_without_at_symbol(strategy_factory):
    strategy = strategy_factory.get_strategy("email_mask")
    masked = strategy.mask("invalidemail", {})
    assert masked == "***@***.***"


def test_email_mask_strategy_with_empty_local(strategy_factory):
    strategy = strategy_factory.get_strategy("email_mask")
    masked = strategy.mask("@gmail.com", {})
    assert masked == "@gmail.com"


def test_phone_mask_strategy(strategy_factory):
    strategy = strategy_factory.get_strategy("phone_mask")
    masked = strategy.mask("0771234567", {})
    assert masked == "******4567"


def test_phone_mask_strategy_with_dashes(strategy_factory):
    strategy = strategy_factory.get_strategy("phone_mask")
    masked = strategy.mask("077-123-4567", {})
    assert masked == "******4567"


def test_phone_mask_strategy_short_number(strategy_factory):
    strategy = strategy_factory.get_strategy("phone_mask")
    masked = strategy.mask("123", {})
    assert masked == "****"


def test_phone_mask_strategy_exact_4_digits(strategy_factory):
    strategy = strategy_factory.get_strategy("phone_mask")
    masked = strategy.mask("1234", {})
    assert masked == "1234"


def test_null_handling_redaction(strategy_factory):
    strategy = strategy_factory.get_strategy("redaction")
    assert strategy.mask(None, {}) is None


def test_null_handling_partial_mask(strategy_factory):
    strategy = strategy_factory.get_strategy("partial_mask")
    assert strategy.mask(None, {}) is None


def test_null_handling_email_mask(strategy_factory):
    strategy = strategy_factory.get_strategy("email_mask")
    assert strategy.mask(None, {}) is None


def test_null_handling_phone_mask(strategy_factory):
    strategy = strategy_factory.get_strategy("phone_mask")
    assert strategy.mask(None, {}) is None


def test_null_handling_hash(strategy_factory):
    strategy = strategy_factory.get_strategy("hash")
    assert strategy.mask(None, {}) is None


def test_unknown_strategy(strategy_factory):
    with pytest.raises(ValueError, match="Unknown masking strategy"):
        strategy_factory.get_strategy("nonexistent_strategy")


def test_strategy_parameter_validation_redaction(strategy_factory):
    strategy = strategy_factory.get_strategy("redaction")
    assert strategy.validate_parameters({}) is True
    assert strategy.validate_parameters({"any": "param"}) is True


def test_strategy_parameter_validation_partial_mask(strategy_factory):
    strategy = strategy_factory.get_strategy("partial_mask")
    assert strategy.validate_parameters({}) is True
    assert strategy.validate_parameters({"visible_chars": 3}) is True
    assert strategy.validate_parameters({"visible_chars": 0}) is False
    assert strategy.validate_parameters({"visible_chars": -1}) is False


def test_strategy_parameter_validation_email_mask(strategy_factory):
    strategy = strategy_factory.get_strategy("email_mask")
    assert strategy.validate_parameters({}) is True
    assert strategy.validate_parameters({"any": "param"}) is True


def test_strategy_parameter_validation_phone_mask(strategy_factory):
    strategy = strategy_factory.get_strategy("phone_mask")
    assert strategy.validate_parameters({}) is True
    assert strategy.validate_parameters({"any": "param"}) is True


def test_policy_creation(policy_manager):
    manager, mock_repo = policy_manager
    expected = MaskingPolicy(
        id=1,
        name="Test Policy",
        description="A test policy",
        table_name="users",
        column_name="email",
        strategy="email_mask",
    )
    mock_repo.create_policy.return_value = expected

    policy = MaskingPolicy(
        name="Test Policy",
        description="A test policy",
        table_name="users",
        column_name="email",
        strategy="email_mask",
    )
    result = manager.create_policy(policy)
    assert result.name == "Test Policy"
    mock_repo.create_policy.assert_called_once()


def test_get_available_strategies(strategy_factory):
    strategies = strategy_factory.get_available_strategies()
    assert "redaction" in strategies
    assert "email_mask" in strategies
    assert "phone_mask" in strategies
    assert "partial_mask" in strategies


def test_validate_query_select_only():
    svc = QueryService()
    assert svc.validate_query("SELECT 1")[0] is True
    assert svc.validate_query("INSERT INTO x VALUES (1)")[0] is False
    assert svc.validate_query("DROP TABLE x")[0] is False


def test_validate_query_with_cte():
    svc = QueryService()
    ok, _ = svc.validate_query("WITH cte AS (SELECT 1) SELECT * FROM cte")
    assert ok is True


def test_masking_engine_apply_policies_to_query_results():
    from app.masking.engine import MaskingEngine
    engine = MaskingEngine()
    data = [
        [1, "john.smith@gmail.com", "0771234567", "secret123"],
        [2, "alice.wonder@corp.org", "0719876543", "password456"],
    ]
    columns = ["id", "email", "phone", "notes"]
    policies = [
        MaskingPolicy(
            name="users.email",
            description="Mask email",
            table_name="users",
            column_name="email",
            strategy="email_mask",
        ),
        MaskingPolicy(
            name="users.phone",
            description="Mask phone",
            table_name="users",
            column_name="phone",
            strategy="phone_mask",
        ),
        MaskingPolicy(
            name="users.notes",
            description="Redact notes",
            table_name="users",
            column_name="notes",
            strategy="redaction",
        ),
    ]

    masked_data, masked_cols, _ = engine.apply_masking(data, columns, policies)

    assert masked_data[0][0] == 1
    assert masked_data[0][1] == "j***@gmail.com"
    assert masked_data[0][2] == "******4567"
    assert masked_data[0][3] == "*********"

    assert masked_data[1][0] == 2
    assert masked_data[1][1] == "a***@corp.org"
    assert masked_data[1][2] == "******6543"
    assert masked_data[1][3] == "***********"

    assert set(masked_cols) == {"email", "phone", "notes"}


def test_masking_engine_does_not_modify_original_records():
    from app.masking.engine import MaskingEngine
    engine = MaskingEngine()
    original_row = [1, "john.smith@gmail.com", "0771234567"]
    data = [original_row]
    columns = ["id", "email", "phone"]
    policies = [
        MaskingPolicy(
            name="users.email",
            description="Mask email",
            table_name="users",
            column_name="email",
            strategy="email_mask",
        )
    ]

    masked_data, _, _ = engine.apply_masking(data, columns, policies)

    # Verify original input list and inner elements were not mutated
    assert original_row[1] == "john.smith@gmail.com"
    assert masked_data[0][1] == "j***@gmail.com"


def test_masking_engine_missing_or_unknown_policy_columns():
    from app.masking.engine import MaskingEngine
    engine = MaskingEngine()
    data = [[1, "active_user"]]
    columns = ["id", "username"]
    policies = [
        MaskingPolicy(
            name="users.nonexistent",
            description="Policy on non-existent column",
            table_name="users",
            column_name="nonexistent_column",
            strategy="redaction",
        )
    ]

    masked_data, masked_cols, _ = engine.apply_masking(data, columns, policies)

    # Should safely ignore policies for columns not present in the dataset
    assert masked_data == [[1, "active_user"]]
    assert masked_cols == []


def test_masking_engine_null_values_in_dataset():
    from app.masking.engine import MaskingEngine
    engine = MaskingEngine()
    data = [
        [1, None, None],
        [2, "test@example.com", "0771234567"],
    ]
    columns = ["id", "email", "phone"]
    policies = [
        MaskingPolicy(
            name="users.email",
            description="Mask email",
            table_name="users",
            column_name="email",
            strategy="email_mask",
        ),
        MaskingPolicy(
            name="users.phone",
            description="Mask phone",
            table_name="users",
            column_name="phone",
            strategy="phone_mask",
        ),
    ]

    masked_data, masked_cols, _ = engine.apply_masking(data, columns, policies)

    # Null values should remain None without raising errors
    assert masked_data[0][1] is None
    assert masked_data[0][2] is None
    assert masked_data[1][1] == "t***@example.com"
    assert masked_data[1][2] == "******4567"


def test_policy_repository_create_and_recreate_sql():
    from app.database.repositories import PolicyRepository
    repo = PolicyRepository()
    policy = MaskingPolicy(
        name="Doctor Name Masking",
        description="Masks doctor names",
        table_name="appointments",
        column_name="doctor_name",
        strategy="partial_mask",
    )

    with patch("app.database.repositories.db.execute_query") as mock_query:
        mock_query.return_value = [{"id": 10, "created_at": None, "updated_at": None}]
        created = repo.create_policy(policy)
        assert created.id == 10
        assert mock_query.called
        sql_called = mock_query.call_args[0][0]
        assert "ON CONFLICT (table_name, column_name) DO UPDATE" in sql_called
        assert "is_active = TRUE" in sql_called


def test_masking_service_create_policy_valid():
    from app.services.masking_service import MaskingService
    svc = MaskingService()
    policy = MaskingPolicy(
        table_name="patients",
        column_name="email",
        strategy="EMAIL",
        schema_name="public",
    )
    with patch.object(svc, "validate_table_and_column") as mock_val, \
         patch.object(svc.policy_manager, "create_policy") as mock_create:
        mock_create.return_value = MaskingPolicy(
            id=15,
            name="patients.email",
            table_name="patients",
            column_name="email",
            strategy="EMAIL",
            schema_name="public",
            status="ACTIVE",
            is_active=True,
        )
        created = svc.create_policy(policy)
        assert created.id == 15
        assert created.table_name == "patients"
        assert created.column_name == "email"
        mock_val.assert_called_once_with("patients", "email", schema_name="public")
        mock_create.assert_called_once()


def test_masking_service_create_policy_invalid_table():
    from app.services.masking_service import MaskingService
    svc = MaskingService()
    policy = MaskingPolicy(
        table_name="nonexistent_tbl",
        column_name="some_col",
        strategy="REDACT",
    )
    with patch("app.services.masking_service.db.table_exists", return_value=False):
        with pytest.raises(ValueError, match="does not exist in schema"):
            svc.create_policy(policy)


def test_masking_service_create_policy_invalid_column():
    from app.services.masking_service import MaskingService
    svc = MaskingService()
    policy = MaskingPolicy(
        table_name="patients",
        column_name="nonexistent_col",
        strategy="REDACT",
    )
    with patch("app.services.masking_service.db.table_exists", return_value=True), \
         patch("app.services.masking_service.db.get_table_schema", return_value=[{"column_name": "email"}, {"column_name": "phone"}]):
        with pytest.raises(ValueError, match="Column 'nonexistent_col' does not exist"):
            svc.create_policy(policy)


def test_masking_service_create_policy_invalid_strategy():
    from app.services.masking_service import MaskingService
    svc = MaskingService()
    policy = MaskingPolicy(
        table_name="patients",
        column_name="email",
        strategy="INVALID_MAGIC_STRATEGY",
    )
    with pytest.raises(ValueError, match="Invalid masking strategy"):
        svc.create_policy(policy)


def test_api_create_policy_endpoint(client):
    policy_data = {
        "table_name": "patients",
        "column_name": "phone",
        "strategy": "PHONE_LAST4",
        "schema_name": "public",
    }
    with patch("app.api.routes.masking.masking_service.create_policy") as mock_create:
        mock_create.return_value = MaskingPolicy(
            id=20,
            name="patients.phone",
            table_name="patients",
            column_name="phone",
            strategy="PHONE_LAST4",
            schema_name="public",
            status="ACTIVE",
            is_active=True,
        )
        res = client.post("/api/v1/masking/policies", json=policy_data)
        assert res.status_code == 201
        data = res.json()
        assert data["id"] == 20
        assert data["table_name"] == "patients"
        assert data["column_name"] == "phone"
        assert data["strategy"] == "PHONE_LAST4"


def test_api_create_policy_endpoint_invalid_table_rejected(client):
    policy_data = {
        "table_name": "ghost_table",
        "column_name": "id",
        "strategy": "REDACT",
    }
    with patch("app.api.routes.masking.masking_service.create_policy", side_effect=ValueError("Table 'ghost_table' does not exist in schema 'public'")):
        res = client.post("/api/v1/masking/policies", json=policy_data)
        assert res.status_code == 400
        assert "ghost_table" in res.json()["detail"]



