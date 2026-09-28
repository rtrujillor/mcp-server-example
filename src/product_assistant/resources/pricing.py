"""Pricing resource handler."""
from typing import Any, Dict

from product_assistant.resources._data_loader import load_data


def get_pricing_current() -> Dict[str, Any]:
    """
    Return current pricing information for all plans.
    
    Returns:
        Dictionary containing pricing models, base prices,
        per-user prices, and discount rules for all plans.
    """
    return load_data("pricing.json")
