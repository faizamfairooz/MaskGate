"""
PostgreSQL Masking Strategy Compatibility Audit Test Suite.

Audits behavioral equivalence between Python strategy implementations
(MaskingStrategyFactory / strategies.py) and PostgreSQL DB-level masking functions:
    Python strategy(value, parameters) == PostgreSQL function(value, parameters)

Audited deterministic strategies:
1. NONE
2. REDACT
3. PARTIAL
4. EMAIL
5. PHONE_LAST4
6. HASH
7. SSN_MASK
8. CREDIT_CARD_MASK
9. DATE_MASK
10. GENERALIZATION
11. DO_NOT_SHOW
"""

import pytest
from datetime import date, datetime
from app.database.postgresql import db
from app.database.db_masking_functions import DBMaskingFunctionManager
from app.masking.strategies import (
    MaskingStrategyFactory,
    NoneMaskStrategy,
    RedactionStrategy,
    PartialMaskStrategy,
    EmailMaskStrategy,
    PhoneMaskStrategy,
    HashStrategy,
    SSNMaskStrategy,
    CreditCardMaskStrategy,
    DateMaskStrategy,
    GeneralizationStrategy,
    DoNotShowStrategy,
)
from app.schemas.masking import MaskingPolicy
from app.services.masking_service import MaskingService
from app.services.query_service import QueryService


@pytest.fixture(autouse=True)
def init_db_functions():
    """Ensure all base stored functions are registered in PostgreSQL."""
    DBMaskingFunctionManager.init_base_functions()


@pytest.fixture
def factory():
    return MaskingStrategyFactory()


@pytest.fixture
def masking_service():
    return MaskingService()


@pytest.fixture
def query_service():
    return QueryService()


def _assert_equivalence(strat_instance, db_sql_fn, val, params=None):
    """Helper to verify exact equality between Python strategy and PostgreSQL function."""
    params = params or {}
    py_result = strat_instance.mask(val, params)

    sql = db_sql_fn(val, params)
    db_rows = db.execute_query(sql)
    assert len(db_rows) == 1
    db_result = db_rows[0]["res"]

    assert py_result == db_result, (
        f"Mismatch on input {repr(val)} with params {params}: "
        f"Python={repr(py_result)} vs DB={repr(db_result)}"
    )
    return py_result


class TestStrategyCompatibilityAudit:
    """Rigorous audit across all 11 supported deterministic masking strategies."""

    # -----------------------------------------------------------------------
    # 1. NONE Strategy Audit
    # -----------------------------------------------------------------------
    def test_none_strategy_compatibility(self, factory):
        strat = factory.get_strategy("NONE")
        assert isinstance(strat, NoneMaskStrategy)

        def db_fn(v, p):
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_none({arg}) AS res;"

        # Representative values, NULL, empty string, short strings, malformed
        for val in [None, "", "a", "short", "john.smith@hospital.org", "12345", "Special & <chars>"]:
            _assert_equivalence(strat, db_fn, val)

    # -----------------------------------------------------------------------
    # 2. REDACT Strategy Audit
    # -----------------------------------------------------------------------
    def test_redact_strategy_compatibility(self, factory):
        strat = factory.get_strategy("REDACT")
        assert isinstance(strat, RedactionStrategy)

        def db_fn(v, p):
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_redact({arg}) AS res;"

        # NULL, empty string, 1-char, 2-char, regular words, long strings
        test_inputs = [None, "", "a", "ab", "abc", "Confidential_Record", "1234567890", "Dr. House MD"]
        for val in test_inputs:
            res = _assert_equivalence(strat, db_fn, val)
            if val is not None and len(val) > 0:
                assert res == "*" * len(val)

    # -----------------------------------------------------------------------
    # 3. PARTIAL Strategy Audit
    # -----------------------------------------------------------------------
    def test_partial_strategy_compatibility(self, factory):
        strat = factory.get_strategy("PARTIAL")
        assert isinstance(strat, PartialMaskStrategy)

        def db_fn(v, p):
            vis = p.get("visible_chars", 2)
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_partial({arg}, {vis}) AS res;"

        # NULL, empty string, short strings (<=2 chars), edge lengths
        for val in [None, "", "a", "ab", "abc", "abcd", "abcde", "sensitive_text_payload"]:
            _assert_equivalence(strat, db_fn, val, {"visible_chars": 2})

        # Custom visible_chars parameters
        for vis in [1, 2, 3, 4]:
            _assert_equivalence(strat, db_fn, "sensitive_text_payload", {"visible_chars": vis})

    # -----------------------------------------------------------------------
    # 4. EMAIL Strategy Audit
    # -----------------------------------------------------------------------
    def test_email_strategy_compatibility(self, factory):
        strat = factory.get_strategy("EMAIL")
        assert isinstance(strat, EmailMaskStrategy)

        def db_fn(v, p):
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_email({arg}) AS res;"

        test_emails = [
            None,
            "",
            "invalid_no_at",
            "a",
            "@domain.com",
            "a@b.com",
            "john.smith@gmail.com",
            "patient.record+alias@hospital.region.org",
            "123@numbers.com",
        ]
        for val in test_emails:
            res = _assert_equivalence(strat, db_fn, val)
            if val == "john.smith@gmail.com":
                assert res == "j***@gmail.com"

    # -----------------------------------------------------------------------
    # 5. PHONE_LAST4 Strategy Audit
    # -----------------------------------------------------------------------
    def test_phone_last4_strategy_compatibility(self, factory):
        strat = factory.get_strategy("PHONE_LAST4")
        assert isinstance(strat, PhoneMaskStrategy)

        def db_fn(v, p):
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_phone_last4({arg}) AS res;"

        test_phones = [
            None,
            "",
            "1",
            "12",
            "123",
            "1234",
            "12345",
            "0771234567",
            "+1 (555) 123-4567",
            "phone-with-no-digits",
            "+44 20 7946 0958",
        ]
        for val in test_phones:
            res = _assert_equivalence(strat, db_fn, val)
            if val == "0771234567":
                assert res == "******4567"

    # -----------------------------------------------------------------------
    # 6. HASH Strategy Audit
    # -----------------------------------------------------------------------
    def test_hash_strategy_compatibility(self, factory):
        strat = factory.get_strategy("HASH")
        assert isinstance(strat, HashStrategy)

        def db_fn(v, p):
            algo = p.get("algorithm", "sha256")
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_hash({arg}, '{algo}') AS res;"

        # Default sha256 (64 hex characters)
        for val in [None, "", "secret_api_key", "password123", "token_98765"]:
            res = _assert_equivalence(strat, db_fn, val, {"algorithm": "sha256"})
            if val and val != "":
                assert len(res) == 64

        # Supported algorithms: md5, sha224, sha384, sha512
        for algo, expected_len in [("md5", 32), ("sha224", 56), ("sha384", 96), ("sha512", 128)]:
            res = _assert_equivalence(strat, db_fn, "secret_api_key", {"algorithm": algo})
            assert len(res) == expected_len

    # -----------------------------------------------------------------------
    # 7. SSN_MASK Strategy Audit
    # -----------------------------------------------------------------------
    def test_ssn_mask_strategy_compatibility(self, factory):
        strat = factory.get_strategy("SSN_MASK")
        assert isinstance(strat, SSNMaskStrategy)

        def db_fn(v, p):
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_ssn({arg}) AS res;"

        test_ssns = [
            None,
            "",
            "123",
            "12345678",
            "123-45-6789",
            "123456789",
            "1234567890",
            "not_an_ssn_value",
        ]
        for val in test_ssns:
            res = _assert_equivalence(strat, db_fn, val)
            if val == "123-45-6789":
                assert res == "***-**-6789"
            elif val == "123":
                assert res == "***-**-****"

    # -----------------------------------------------------------------------
    # 8. CREDIT_CARD_MASK Strategy Audit
    # -----------------------------------------------------------------------
    def test_credit_card_mask_strategy_compatibility(self, factory):
        strat = factory.get_strategy("CREDIT_CARD_MASK")
        assert isinstance(strat, CreditCardMaskStrategy)

        def db_fn(v, p):
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_credit_card({arg}) AS res;"

        test_cards = [
            None,
            "",
            "123",
            "1234-5678",
            "1234-5678-9012-3",
            "1234-5678-9012-3456",
            "1234567890123456",
            "1234-5678-9012-3456-789",
            "invalid_card",
        ]
        for val in test_cards:
            res = _assert_equivalence(strat, db_fn, val)
            if val == "1234-5678-9012-3456":
                assert res == "************3456"
            elif val == "123":
                assert res == "****-****-****-****"

    # -----------------------------------------------------------------------
    # 9. DATE_MASK Strategy Audit
    # -----------------------------------------------------------------------
    def test_date_mask_strategy_compatibility(self, factory):
        strat = factory.get_strategy("DATE_MASK")
        assert isinstance(strat, DateMaskStrategy)

        def db_fn(v, p):
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_date({arg}) AS res;"

        test_dates = [
            None,
            "",
            "2025-08-16",
            "1990-01-31",
            "2023",
            "invalid_date_format",
            "123",
        ]
        for val in test_dates:
            res = _assert_equivalence(strat, db_fn, val)
            if val == "2025-08-16":
                assert res == "2025-01-01"

        # Python object handling
        assert strat.mask(date(2025, 8, 16), {}) == "2025-01-01"
        assert strat.mask(datetime(2025, 8, 16, 12, 0), {}) == "2025-01-01"

    # -----------------------------------------------------------------------
    # 10. GENERALIZATION Strategy Audit
    # -----------------------------------------------------------------------
    def test_generalization_strategy_compatibility(self, factory):
        strat = factory.get_strategy("GENERALIZATION")
        assert isinstance(strat, GeneralizationStrategy)

        def db_fn(v, p):
            bin_size = p.get("bin_size", 1000)
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_generalization({arg}, {bin_size}) AS res;"

        test_values = [
            (None, 1000),
            ("", 1000),
            ("2500", 1000),
            ("0", 1000),
            ("500", 1000),
            ("75", 50),
            ("1250", 500),
            ("not_numeric", 1000),
        ]
        for val, bin_sz in test_values:
            res = _assert_equivalence(strat, db_fn, val, {"bin_size": bin_sz})
            if val == "2500":
                assert res == "2000-3000"
            elif val == "75":
                assert res == "50-100"

    # -----------------------------------------------------------------------
    # 11. DO_NOT_SHOW Strategy Audit
    # -----------------------------------------------------------------------
    def test_do_not_show_strategy_compatibility(self, factory):
        strat = factory.get_strategy("DO_NOT_SHOW")
        assert isinstance(strat, DoNotShowStrategy)

        def db_fn(v, p):
            arg = "NULL" if v is None else f"'{v}'"
            return f"SELECT maskgate_fn_do_not_show({arg}) AS res;"

        for val in [None, "", "a", "confidential_record", "12345"]:
            res = _assert_equivalence(strat, db_fn, val)
            assert res == "[HIDDEN]"


class TestDBPolicyLifecycleAndQueryIntegration:
    """Verify policy lifecycle and query execution across all strategies."""

    def test_dynamic_policy_function_generation_all_strategies(self, masking_service, query_service):
        """Create active policies for all strategies and verify execution in DB."""
        strategies = [
            ("NONE", {}),
            ("REDACT", {}),
            ("PARTIAL", {"visible_chars": 3}),
            ("EMAIL", {}),
            ("PHONE_LAST4", {}),
            ("HASH", {"algorithm": "sha256"}),
            ("SSN_MASK", {}),
            ("CREDIT_CARD_MASK", {}),
            ("DATE_MASK", {}),
            ("GENERALIZATION", {"bin_size": 100}),
            ("DO_NOT_SHOW", {}),
        ]

        created_policies = []
        try:
            for idx, (strat, params) in enumerate(strategies, start=800):
                policy = MaskingPolicy(
                    id=idx,
                    name=f"audit_policy_{idx}",
                    table_name="patients",
                    column_name="email",
                    strategy=strat,
                    parameters=params,
                )
                func_name = DBMaskingFunctionManager.create_or_replace_policy_function(policy)
                assert func_name == f"maskgate_policy_{idx}"
                assert DBMaskingFunctionManager.function_exists(idx) is True
                created_policies.append(policy)

            # Test execution of each policy function
            assert db.execute_query("SELECT maskgate_policy_800('test') AS v")[0]["v"] == "test"
            assert db.execute_query("SELECT maskgate_policy_801('test') AS v")[0]["v"] == "****"
            assert db.execute_query("SELECT maskgate_policy_802('testing_partial') AS v")[0]["v"] == "tes*********ial"
            assert db.execute_query("SELECT maskgate_policy_803('admin@test.com') AS v")[0]["v"] == "a***@test.com"
            assert db.execute_query("SELECT maskgate_policy_804('0771234567') AS v")[0]["v"] == "******4567"
            assert len(db.execute_query("SELECT maskgate_policy_805('secret') AS v")[0]["v"]) == 64
            assert db.execute_query("SELECT maskgate_policy_806('123-45-6789') AS v")[0]["v"] == "***-**-6789"
            assert db.execute_query("SELECT maskgate_policy_807('1234-5678-9012-3456') AS v")[0]["v"] == "************3456"
            assert db.execute_query("SELECT maskgate_policy_808('2026-08-20') AS v")[0]["v"] == "2026-01-01"
            assert db.execute_query("SELECT maskgate_policy_809('250') AS v")[0]["v"] == "200-300"
            assert db.execute_query("SELECT maskgate_policy_810('anything') AS v")[0]["v"] == "[HIDDEN]"

        finally:
            for p in created_policies:
                DBMaskingFunctionManager.drop_policy_function(p.id)
                assert DBMaskingFunctionManager.function_exists(p.id) is False
