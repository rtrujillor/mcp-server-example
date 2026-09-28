"""Resource handlers for the Product Assistant MCP Server."""
from product_assistant.resources.features import get_features_by_plan
from product_assistant.resources.plans import get_all_plans
from product_assistant.resources.pricing import get_pricing_current

__all__ = [
    "get_all_plans",
    "get_features_by_plan",
    "get_pricing_current",
]
