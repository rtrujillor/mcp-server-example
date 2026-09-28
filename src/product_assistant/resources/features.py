"""Features resource handler."""
from typing import Any, Dict

from product_assistant.resources._data_loader import load_data


def get_features_by_plan() -> Dict[str, Any]:
    """
    Return detailed feature breakdown for each plan.
    
    Returns:
        Dictionary containing feature details organized by plan,
        including core features, analytics, security, support, and integrations.
    """
    return load_data("features.json")
