"""Reusable pricing-related business logic."""

from typing import Any, Dict, List, Optional

from product_assistant.models import QuoteLineItem


def get_plan_pricing(
    pricing_data: Dict[str, Any],
    plan_id: str,
) -> Optional[Dict[str, Any]]:
    """Return pricing configuration for a plan identifier."""
    return next(
        (plan for plan in pricing_data.get("plans", []) if plan.get("plan_id") == plan_id),
        None,
    )


def build_base_and_user_items(
    cycle: str,
    base_price: float,
    per_user_price: float,
    users: int,
    per_user_round_decimals: Optional[int] = None,
) -> List[QuoteLineItem]:
    """Build base and per-user line items for a quote or estimate."""
    per_user_total = per_user_price * users
    if per_user_round_decimals is not None:
        per_user_total = round(per_user_total, per_user_round_decimals)

    return [
        QuoteLineItem(
            name=f"Base fee ({cycle})",
            unit_price=base_price,
            quantity=1,
            line_total=base_price,
        ),
        QuoteLineItem(
            name=f"Per-user ({cycle})",
            unit_price=per_user_price,
            quantity=users,
            line_total=per_user_total,
        ),
    ]


def build_optional_api_item(
    api_requests: Optional[int],
    per_api_price: Optional[float],
    round_decimals: int = 4,
) -> Optional[QuoteLineItem]:
    """Build optional API-request line item when usage and pricing are present."""
    if api_requests is None or per_api_price is None:
        return None

    return QuoteLineItem(
        name="Per API request",
        unit_price=per_api_price,
        quantity=api_requests,
        line_total=round(per_api_price * api_requests, round_decimals),
    )
