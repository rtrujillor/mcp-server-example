"""Plans resource handler."""
from typing import Any, Dict

from product_assistant.resources._data_loader import load_data


def get_all_plans() -> Dict[str, Any]:
    """
    Return all available subscription plans with their details.
    
    Returns:
        Dictionary containing all plans with their configuration,
        limits, features, and recommended use cases.
    """
    return load_data("plans.json")
