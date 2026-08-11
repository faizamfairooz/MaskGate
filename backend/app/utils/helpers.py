from typing import Any, List, Dict
import json


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string with fallback."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def truncate_string(s: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate a string to max length with suffix."""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def batch_list(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Split a list into batches."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def remove_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from a dictionary."""
    return {k: v for k, v in d.items() if v is not None}
