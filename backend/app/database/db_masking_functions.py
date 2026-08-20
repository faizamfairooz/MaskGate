"""
PostgreSQL Stored Masking Functions and Policy-Specific DB Function Lifecycle Manager.

Manages deterministic, read-only PostgreSQL functions that apply data masking directly
inside the database engine before query results are returned to the application.
"""

from typing import Any, Dict, List, Optional
import json
import re
import logging

from app.database.postgresql import db
from app.schemas.masking import MaskingPolicy

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base Reusable PostgreSQL Masking Functions
# ---------------------------------------------------------------------------

BASE_FUNCTIONS_SQL = """
-- 1. Base NONE Function
CREATE OR REPLACE FUNCTION maskgate_fn_none(val text)
RETURNS text AS $$
BEGIN
    RETURN val;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 2. Base REDACT Function
CREATE OR REPLACE FUNCTION maskgate_fn_redact(val text)
RETURNS text AS $$
BEGIN
    IF val IS NULL THEN
        RETURN NULL;
    END IF;
    IF LENGTH(val) = 0 THEN
        RETURN '';
    END IF;
    RETURN REPEAT('*', LENGTH(val));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 3. Base PARTIAL Function
CREATE OR REPLACE FUNCTION maskgate_fn_partial(val text, visible_chars int DEFAULT 2)
RETURNS text AS $$
DECLARE
    v_len int;
    v_vis int;
BEGIN
    IF val IS NULL THEN
        RETURN NULL;
    END IF;
    v_len := LENGTH(val);
    IF v_len = 0 THEN
        RETURN '';
    END IF;
    IF v_len <= 2 THEN
        RETURN '**';
    END IF;
    v_vis := COALESCE(visible_chars, 2);
    IF v_vis < 1 THEN
        v_vis := 2;
    END IF;
    IF v_len <= v_vis * 2 THEN
        RETURN REPEAT('*', v_len);
    END IF;
    RETURN SUBSTRING(val FROM 1 FOR v_vis)
           || REPEAT('*', v_len - (v_vis * 2))
           || SUBSTRING(val FROM (v_len - v_vis + 1) FOR v_vis);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 4. Base EMAIL Function
CREATE OR REPLACE FUNCTION maskgate_fn_email(val text)
RETURNS text AS $$
DECLARE
    at_pos int;
    local_part text;
    domain_part text;
BEGIN
    IF val IS NULL THEN
        RETURN NULL;
    END IF;
    IF LENGTH(val) = 0 THEN
        RETURN '';
    END IF;
    at_pos := POSITION('@' IN val);
    IF at_pos = 0 THEN
        RETURN '***@***.***';
    END IF;
    IF at_pos = 1 THEN
        RETURN val;
    END IF;
    local_part := SPLIT_PART(val, '@', 1);
    domain_part := SUBSTRING(val FROM at_pos + 1);
    RETURN SUBSTRING(local_part FROM 1 FOR 1) || '***@' || domain_part;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 5. Base PHONE_LAST4 Function
CREATE OR REPLACE FUNCTION maskgate_fn_phone_last4(val text)
RETURNS text AS $$
DECLARE
    digits text;
    d_len int;
BEGIN
    IF val IS NULL THEN
        RETURN NULL;
    END IF;
    IF LENGTH(val) = 0 THEN
        RETURN '';
    END IF;
    digits := REGEXP_REPLACE(val, '\\D', '', 'g');
    d_len := LENGTH(digits);
    IF d_len >= 4 THEN
        RETURN REPEAT('*', d_len - 4) || RIGHT(digits, 4);
    END IF;
    RETURN '****';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 6. Base HASH Function
DROP FUNCTION IF EXISTS maskgate_fn_hash(text);
CREATE OR REPLACE FUNCTION maskgate_fn_hash(val text, algorithm text DEFAULT 'sha256')
RETURNS text AS $$
DECLARE
    algo text;
BEGIN
    IF val IS NULL THEN
        RETURN NULL;
    END IF;
    algo := LOWER(COALESCE(algorithm, 'sha256'));
    IF algo = 'md5' THEN
        RETURN MD5(val);
    ELSIF algo = 'sha224' THEN
        RETURN ENCODE(SHA224(val::bytea), 'hex');
    ELSIF algo = 'sha384' THEN
        RETURN ENCODE(SHA384(val::bytea), 'hex');
    ELSIF algo = 'sha512' THEN
        RETURN ENCODE(SHA512(val::bytea), 'hex');
    ELSE
        -- Default to SHA256 to match Python HashStrategy default
        RETURN ENCODE(SHA256(val::bytea), 'hex');
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 7. Base SSN Function
CREATE OR REPLACE FUNCTION maskgate_fn_ssn(val text)
RETURNS text AS $$
DECLARE
    digits text;
BEGIN
    IF val IS NULL THEN
        RETURN NULL;
    END IF;
    IF LENGTH(val) = 0 THEN
        RETURN '';
    END IF;
    digits := REGEXP_REPLACE(val, '\\D', '', 'g');
    IF LENGTH(digits) = 9 THEN
        RETURN '***-**-' || RIGHT(digits, 4);
    END IF;
    RETURN '***-**-****';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 8. Base CREDIT_CARD Function
CREATE OR REPLACE FUNCTION maskgate_fn_credit_card(val text)
RETURNS text AS $$
DECLARE
    digits text;
    d_len int;
BEGIN
    IF val IS NULL THEN
        RETURN NULL;
    END IF;
    IF LENGTH(val) = 0 THEN
        RETURN '';
    END IF;
    digits := REGEXP_REPLACE(val, '\\D', '', 'g');
    d_len := LENGTH(digits);
    IF d_len >= 13 THEN
        RETURN REPEAT('*', d_len - 4) || RIGHT(digits, 4);
    END IF;
    RETURN '****-****-****-****';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 9. Base DATE Function
CREATE OR REPLACE FUNCTION maskgate_fn_date(val text)
RETURNS text AS $$
BEGIN
    IF val IS NULL THEN
        RETURN NULL;
    END IF;
    IF val ~ '^\d{4}-\d{2}-\d{2}' THEN
        RETURN SUBSTRING(val FROM 1 FOR 4) || '-01-01';
    END IF;
    RETURN val;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 10. Base DO_NOT_SHOW Function
CREATE OR REPLACE FUNCTION maskgate_fn_do_not_show(val text)
RETURNS text AS $$
BEGIN
    RETURN '[HIDDEN]';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 11. Base GENERALIZATION Function
CREATE OR REPLACE FUNCTION maskgate_fn_generalization(val text, bin_size numeric DEFAULT 1000)
RETURNS text AS $$
DECLARE
    b_size numeric;
    num_val numeric;
    lower_bin numeric;
    upper_bin numeric;
BEGIN
    IF val IS NULL THEN
        RETURN NULL;
    END IF;
    IF LENGTH(val) = 0 THEN
        RETURN '';
    END IF;
    b_size := COALESCE(bin_size, 1000);
    IF b_size <= 0 THEN
        b_size := 1000;
    END IF;
    BEGIN
        num_val := val::numeric;
        lower_bin := FLOOR(num_val / b_size) * b_size;
        upper_bin := lower_bin + b_size;
        IF b_size = FLOOR(b_size) THEN
            RETURN lower_bin::bigint::text || '-' || upper_bin::bigint::text;
        ELSE
            RETURN lower_bin::text || '-' || upper_bin::text;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        RETURN val;
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
"""


class DBMaskingFunctionManager:
    """Manages PostgreSQL stored masking functions for active masking policies."""

    _initialized = False

    @classmethod
    def init_base_functions(cls) -> bool:
        """Create or replace all core MaskGate base masking functions in PostgreSQL."""
        try:
            db.execute_query(BASE_FUNCTIONS_SQL)
            cls._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize base database masking functions: {e}")
            return False

    @staticmethod
    def get_function_name(policy_id: int) -> str:
        """Generate safe, deterministic function name for a policy ID."""
        if not isinstance(policy_id, int) or isinstance(policy_id, bool) or policy_id <= 0:
            raise ValueError(f"Invalid policy ID for database function: {policy_id}")
        return f"maskgate_policy_{policy_id}"

    @classmethod
    def function_exists(cls, policy_id: int) -> bool:
        """Check if the PostgreSQL stored function for a policy ID exists."""
        if not isinstance(policy_id, int) or isinstance(policy_id, bool) or policy_id <= 0:
            return False
        try:
            func_name = cls.get_function_name(policy_id)
            rows = db.execute_query(
                "SELECT 1 AS exists FROM pg_proc WHERE proname = %s LIMIT 1;",
                (func_name,),
            )
            return bool(rows and len(rows) > 0)
        except Exception:
            return False

    @classmethod
    def create_or_replace_policy_function(cls, policy: MaskingPolicy) -> str:
        """
        Generate and execute CREATE OR REPLACE FUNCTION in PostgreSQL for an ACTIVE policy.
        Returns the created function name.
        """
        if not cls._initialized:
            cls.init_base_functions()

        if not policy.id or not isinstance(policy.id, int) or isinstance(policy.id, bool) or policy.id <= 0:
            raise ValueError(f"Cannot create DB function for policy without valid integer id: {policy.id}")

        func_name = cls.get_function_name(policy.id)
        strategy = (policy.strategy or "").strip().lower().replace("-", "_")
        params = policy.parameters or {}
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except Exception:
                params = {}

        fn_body = cls._generate_function_body(strategy, params)

        sql = f"""
        CREATE OR REPLACE FUNCTION {func_name}(val text)
        RETURNS text AS $$
        BEGIN
            {fn_body}
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """

        try:
            db.execute_query(sql)
            return func_name
        except Exception as e:
            logger.error(f"Failed to create database function {func_name} for policy {policy.id}: {e}")
            raise RuntimeError(f"Database masking function creation failed for policy {policy.id}: {e}")

    @classmethod
    def drop_policy_function(cls, policy_id: int) -> bool:
        """
        Drop the PostgreSQL function for a policy when deactivated or deleted.
        """
        if not isinstance(policy_id, int) or isinstance(policy_id, bool) or policy_id <= 0:
            return False

        func_name = cls.get_function_name(policy_id)
        sql = f"DROP FUNCTION IF EXISTS {func_name}(text);"
        try:
            db.execute_query(sql)
            return True
        except Exception as e:
            logger.warning(f"Failed to drop database function {func_name}: {e}")
            return False

    @classmethod
    def sync_all_active_policies(cls, policies: List[MaskingPolicy]) -> int:
        """Ensure all currently active policies have valid PostgreSQL functions."""
        cls.init_base_functions()
        synced_count = 0
        for policy in policies:
            if policy.is_active and (policy.status or "ACTIVE").upper() == "ACTIVE":
                try:
                    cls.create_or_replace_policy_function(policy)
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Error syncing policy {policy.id} function: {e}")
        return synced_count

    @classmethod
    def _generate_function_body(cls, strategy: str, params: Dict[str, Any]) -> str:
        """Generate PL/pgSQL function body for a strategy and parameters."""
        if strategy in ("email", "email_mask"):
            return "RETURN maskgate_fn_email(val);"

        elif strategy in ("phone", "phone_mask", "phone_last4", "last4"):
            return "RETURN maskgate_fn_phone_last4(val);"

        elif strategy in ("partial", "partial_mask"):
            vis = params.get("visible_chars", 2)
            try:
                vis_int = int(vis)
                if vis_int < 1:
                    vis_int = 2
            except (ValueError, TypeError):
                vis_int = 2
            return f"RETURN maskgate_fn_partial(val, {vis_int});"

        elif strategy in ("redact", "redaction"):
            return "RETURN maskgate_fn_redact(val);"

        elif strategy in ("none", "no_mask"):
            return "RETURN maskgate_fn_none(val);"

        elif strategy == "hash":
            algo = params.get("algorithm", "sha256")
            safe_algo = re.sub(r"[^a-zA-Z0-9]", "", str(algo)).lower() or "sha256"
            return f"RETURN maskgate_fn_hash(val, '{safe_algo}');"

        elif strategy in ("ssn_mask", "ssn"):
            return "RETURN maskgate_fn_ssn(val);"

        elif strategy in ("credit_card_mask", "credit_card", "creditcard"):
            return "RETURN maskgate_fn_credit_card(val);"

        elif strategy in ("date_mask", "date"):
            return "RETURN maskgate_fn_date(val);"

        elif strategy in ("do_not_show", "donotshow", "hide", "hidden"):
            return "RETURN maskgate_fn_do_not_show(val);"

        elif strategy in ("generalization", "generalize"):
            bin_size = params.get("bin_size", 1000)
            try:
                bin_num = float(bin_size)
                if bin_num <= 0:
                    bin_num = 1000.0
            except (ValueError, TypeError):
                bin_num = 1000.0
            return f"RETURN maskgate_fn_generalization(val, {bin_num});"

        else:
            # Safe fallback to redaction
            return "RETURN maskgate_fn_redact(val);"
