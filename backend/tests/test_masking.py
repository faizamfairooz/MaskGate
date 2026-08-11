import pytest
from unittest.mock import MagicMock, patch

from app.masking.strategies import MaskingStrategyFactory
from app.masking.policies import PolicyManager
from app.schemas.masking import MaskingPolicy
from app.services.query_service import QueryService


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
