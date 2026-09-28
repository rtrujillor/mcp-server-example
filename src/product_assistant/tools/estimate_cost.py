"""Estimate cost tool."""
from typing import Dict, List, Optional

from product_assistant.models import EstimateCostResult, UsageProfile
from product_assistant.resources import get_all_plans, get_pricing_current
from product_assistant.services import (
    build_base_and_user_items,
    build_optional_api_item,
    get_plan_pricing,
    validate_plan_usage_limits,
)


def estimate_cost(
    plan: str,
    usage: UsageProfile,
) -> EstimateCostResult:
    """
    Quickly estimate the monthly operational cost for a given plan and usage
    profile. Unlike generate_quote, this does not produce a formal proposal
    or validity period — it is designed for fast what-if analysis.

    Validates plan limits using plans://all and calculates cost from
    pricing://current (base + per-user + per-API-request when available).
    Returns a cost breakdown with full traceability of the keys read.
    
    Args:
        plan: Plan identifier (starter, professional, enterprise)
        usage: Usage profile with users, projects, and API requests
        
    Returns:
        EstimateCostResult with itemized costs and validation
    """
    trace: Dict[str, List[str]] = {"pricing://current": [], "plans://all": []}
    # Always use monthly cycle for quick estimates
    cycle = "monthly"

    def _invalid(error: str, notes: List[str]) -> EstimateCostResult:
        return EstimateCostResult(
            valid=False,
            currency="EUR",
            plan=plan,
            usage=usage,
            items=[],
            total_estimated_cost=0.0,
            notes=notes,
            trace=trace,
            error=error,
        )

    # ── 1. Load resources ───────────────────────────────────────────────────
    all_plans_data = get_all_plans()
    pricing_data = get_pricing_current()

    currency: str = pricing_data["currency"]
    trace["pricing://current"].append("currency")

    # ── 2. Locate plan in plans://all ───────────────────────────────────────
    plan_info = next((p for p in all_plans_data["plans"] if p["id"] == plan), None)
    if plan_info is None:
        return _invalid(
            f"Plan '{plan}' not found in plans://all.",
            [f"Plan '{plan}' does not exist. Available plans: starter, professional, enterprise."],
        )

    # ── 3. Validate limits from plans://all ────────────────────────────────
    limits = plan_info.get("limits", {})
    is_valid, limit_warnings = validate_plan_usage_limits(
        plan_id=plan,
        limits=limits,
        usage=usage,
        trace=trace,
    )

    # ── 4. Locate plan in pricing://current ────────────────────────────────
    pricing_info = get_plan_pricing(pricing_data, plan)
    if pricing_info is None:
        return _invalid(
            f"Pricing for plan '{plan}' not found in pricing://current.",
            [f"No pricing found for plan '{plan}'."],
        )

    # ── 5. Handle custom / enterprise pricing ──────────────────────────────
    base_price_val: Optional[float] = pricing_info["base_price"].get(cycle)
    per_user_price_val: Optional[float] = pricing_info["per_user_price"].get(cycle)

    trace["pricing://current"].append(f"plans.{plan}.base_price.{cycle}")
    trace["pricing://current"].append(f"plans.{plan}.per_user_price.{cycle}")
    trace["pricing://current"].append("notes")

    global_notes: List[str] = list(pricing_data.get("notes", []))

    if base_price_val is None or per_user_price_val is None:
        return _invalid(
            f"Plan '{plan}' has custom pricing. Please contact sales for a tailored estimate.",
            [
                "Enterprise pricing is custom and requires sales approval.",
                *global_notes,
            ],
        )

    # ── 6. Build line items ─────────────────────────────────────────────────
    items = build_base_and_user_items(
        cycle=cycle,
        base_price=base_price_val,
        per_user_price=per_user_price_val,
        users=usage.users,
        per_user_round_decimals=4,
    )

    # ── 7. Optional: per-API-request cost ──────────────────────────────────
    if usage.api_requests_per_month is not None:
        per_api_price_val: Optional[float] = (
            pricing_info.get("per_api_request_price", {}) or {}
        ).get(cycle)
        trace["pricing://current"].append(f"plans.{plan}.per_api_request_price.{cycle}")
        api_item = build_optional_api_item(
            api_requests=usage.api_requests_per_month,
            per_api_price=per_api_price_val,
            round_decimals=4,
        )
        if api_item is not None:
            items.append(api_item)

    # ── 8. Total ────────────────────────────────────────────────────────────
    total_estimated_cost = round(sum(item.line_total for item in items), 2)

    notes: List[str] = [
        *limit_warnings,
        f"Quick estimate based on {cycle} prices.",
        "Does not include volume discounts or promotions.",
        "For a formal quote, use the generate_quote tool.",
        *global_notes,
    ]

    return EstimateCostResult(
        valid=is_valid,
        currency=currency,
        plan=plan,
        usage=usage,
        items=items,
        total_estimated_cost=total_estimated_cost,
        notes=notes,
        trace=trace,
    )
