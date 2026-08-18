from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import re
import hashlib
import random
import string
from datetime import datetime


class MaskingStrategy(ABC):
    """Abstract base class for masking strategies."""

    @abstractmethod
    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        """Apply masking to a value."""
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate strategy parameters."""
        pass


class NoneMaskStrategy(MaskingStrategy):
    """No-op masking strategy - returns original value unchanged."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        return value

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return True


class RedactionStrategy(MaskingStrategy):
    """Simple redaction strategy - replaces with asterisks."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None
        value_str = str(value)
        if len(value_str) == 0:
            return ""
        return "*" * len(value_str)

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return True  # No parameters needed


class PartialMaskStrategy(MaskingStrategy):
    """Partial masking - shows first and last characters."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        value_str = str(value)
        if len(value_str) == 0:
            return ""
        if len(value_str) <= 2:
            return "**"

        visible_chars = parameters.get("visible_chars", 2)
        if not isinstance(visible_chars, int) or visible_chars < 1:
            visible_chars = 2

        if len(value_str) <= visible_chars * 2:
            return "*" * len(value_str)

        return (
            value_str[:visible_chars]
            + "*" * (len(value_str) - visible_chars * 2)
            + value_str[-visible_chars:]
        )

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        visible_chars = parameters.get("visible_chars", 2)
        return isinstance(visible_chars, int) and visible_chars >= 1


class HashStrategy(MaskingStrategy):
    """Hashing strategy - replaces with hash value."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        algorithm = parameters.get("algorithm", "sha256")
        hash_func = getattr(hashlib, algorithm, hashlib.sha256)
        return hash_func(str(value).encode()).hexdigest()

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        algorithm = parameters.get("algorithm", "sha256")
        return hasattr(hashlib, algorithm)


class EmailMaskStrategy(MaskingStrategy):
    """Email-specific masking strategy - shows first character of local part."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        email = str(value)
        if len(email) == 0:
            return ""
        if "@" not in email:
            return "***@***.***"

        local, domain = email.split("@", 1)
        if len(local) == 0:
            return f"@{domain}"
        masked_local = local[:1] + "***"
        return f"{masked_local}@{domain}"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return True


class PhoneMaskStrategy(MaskingStrategy):
    """Phone number masking strategy - shows last 4 digits only."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        phone = str(value)
        if len(phone) == 0:
            return ""
        digits = re.sub(r"[^\d]", "", phone)

        if len(digits) >= 4:
            return "*" * (len(digits) - 4) + digits[-4:]
        return "****"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return True


class SSNMaskStrategy(MaskingStrategy):
    """SSN masking strategy."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        ssn = str(value)
        digits = re.sub(r"[^\d]", "", ssn)

        if len(digits) == 9:
            return f"***-**-{digits[-4:]}"
        return "***-**-****"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return True


class CreditCardMaskStrategy(MaskingStrategy):
    """Credit card masking strategy."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        cc = str(value)
        digits = re.sub(r"[^\d]", "", cc)

        if len(digits) >= 13:
            return "*" * (len(digits) - 4) + digits[-4:]
        return "****-****-****-****"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return True


class TokenizationStrategy(MaskingStrategy):
    """Tokenization strategy - replaces with random token."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        token_length = parameters.get("token_length", 16)
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(token_length))

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        token_length = parameters.get("token_length", 16)
        return isinstance(token_length, int) and token_length >= 8


class NoiseAdditionStrategy(MaskingStrategy):
    """Noise addition strategy for numeric values."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        try:
            num_value = float(value)
            noise_level = parameters.get("noise_level", 0.1)
            noise = random.uniform(-noise_level, noise_level) * num_value
            return num_value + noise
        except (ValueError, TypeError):
            return value

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        noise_level = parameters.get("noise_level", 0.1)
        return isinstance(noise_level, (int, float)) and 0 <= noise_level <= 1


class DateMaskStrategy(MaskingStrategy):
    """Date masking strategy - preserves year but masks month/day."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        try:
            if isinstance(value, str):
                dt = datetime.strptime(value, "%Y-%m-%d")
            elif isinstance(value, datetime):
                dt = value
            else:
                return value

            return f"{dt.year}-01-01"  # Set to January 1st of the same year
        except (ValueError, TypeError):
            return value

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return True


class GeneralizationStrategy(MaskingStrategy):
    """Generalization strategy for numeric ranges."""

    def mask(self, value: Any, parameters: Dict[str, Any]) -> Any:
        if value is None:
            return None

        try:
            num_value = float(value)
            bin_size = parameters.get("bin_size", 1000)

            lower_bin = int(num_value // bin_size) * bin_size
            upper_bin = lower_bin + bin_size

            return f"{lower_bin}-{upper_bin}"
        except (ValueError, TypeError):
            return value

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        bin_size = parameters.get("bin_size", 1000)
        return isinstance(bin_size, (int, float)) and bin_size > 0


class MaskingStrategyFactory:
    """Factory for creating masking strategy instances."""

    _none_strategy = NoneMaskStrategy()
    _redact_strategy = RedactionStrategy()
    _partial_strategy = PartialMaskStrategy()
    _email_strategy = EmailMaskStrategy()
    _phone_strategy = PhoneMaskStrategy()
    _hash_strategy = HashStrategy()
    _ssn_strategy = SSNMaskStrategy()
    _credit_card_strategy = CreditCardMaskStrategy()
    _tokenization_strategy = TokenizationStrategy()
    _noise_strategy = NoiseAdditionStrategy()
    _date_strategy = DateMaskStrategy()
    _generalization_strategy = GeneralizationStrategy()

    _strategies = {
        # Standard Core Strategies
        "none": _none_strategy,
        "no_mask": _none_strategy,
        "redact": _redact_strategy,
        "redaction": _redact_strategy,
        "partial": _partial_strategy,
        "partial_mask": _partial_strategy,
        "email": _email_strategy,
        "email_mask": _email_strategy,
        "phone": _phone_strategy,
        "phone_mask": _phone_strategy,
        "phone_last4": _phone_strategy,
        "last4": _phone_strategy,
        # Extended strategies for backwards compatibility
        "hash": _hash_strategy,
        "ssn_mask": _ssn_strategy,
        "credit_card_mask": _credit_card_strategy,
        "tokenization": _tokenization_strategy,
        "noise_addition": _noise_strategy,
        "date_mask": _date_strategy,
        "generalization": _generalization_strategy,
    }

    def get_strategy(self, strategy_name: str) -> MaskingStrategy:
        """Get a strategy instance by name (case-insensitive)."""
        if not strategy_name:
            raise ValueError("Strategy name cannot be empty")
        normalized = strategy_name.strip().lower().replace("-", "_")
        strategy = self._strategies.get(normalized)
        if strategy is None:
            raise ValueError(f"Unknown masking strategy: {strategy_name}")
        return strategy

    def get_available_strategies(self) -> Dict[str, str]:
        """Get available core and extended strategies with descriptions."""
        return {
            "NONE": "Return original value without masking",
            "REDACT": "Replace entire value with asterisks",
            "PARTIAL": "Preserve edge characters and mask middle characters",
            "EMAIL": "Mask local part of email address (e.g. j***@domain.com)",
            "PHONE_LAST4": "Mask phone number preserving last 4 digits",
            "redaction": "Replace with asterisks",
            "partial_mask": "Show first and last characters",
            "hash": "Replace with hash value",
            "email_mask": "Email-specific masking",
            "phone_mask": "Phone number masking",
            "ssn_mask": "SSN masking",
            "credit_card_mask": "Credit card masking",
            "tokenization": "Replace with random token",
            "noise_addition": "Add noise to numeric values",
            "date_mask": "Preserve year, mask month/day",
            "generalization": "Convert to ranges",
        }
