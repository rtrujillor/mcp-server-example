"""Generate quote tool."""
from datetime import date, timedelta
import logging
from typing import Any, Dict, List, Literal, Optional

from product_assistant.models import GenerateQuoteResult
from product_assistant.resources import get_all_plans, get_pricing_current
from product_assistant.services import (
    apply_volume_discounts,
    build_base_and_user_items,
    get_plan_pricing,
    validate_minimum_users,
)

logger = logging.getLogger(__name__)


def generate_quote(
    plan_id: str,
    users: int,
    billing_cycle: Literal["monthly", "yearly"],
) -> GenerateQuoteResult:
    """
    Calculate and return a clear, traceable quote for a specific plan,
    number of users, and billing cycle.

    Validates plan limits using plans://all and applies pricing rules from
    pricing://current. Returns a structured quote with itemised costs,
    optional volume discounts, and full traceability of the keys read.
    
    Args:
        plan_id: Plan identifier (starter, professional, enterprise)
        users: Number of users for the quote
        billing_cycle: Billing frequency (monthly or yearly)
        
    Returns:
        GenerateQuoteResult with itemized costs, discounts, and validation
    """
    logger.info(
        "Generating quote plan=%s users=%d billing_cycle=%s",
        plan_id,
        users,
        billing_cycle,
    )
    valid_until = (date.today() + timedelta(days=14)).isoformat()
    trace: Dict[str, List[str]] = {"pricing://current": [], "plans://all": []}

    def _invalid(error: str, notes: List[str]) -> GenerateQuoteResult:
        logger.warning(
            "Quote rejected plan=%s users=%d billing_cycle=%s reason=%s",
            plan_id,
            users,
            billing_cycle,
            error,
        )
        return GenerateQuoteResult(
            valid=False,
            currency="EUR",
            cycle=billing_cycle,
            plan_id=plan_id,
            users=users,
            items=[],
            subtotal=0.0,
            tax=0.0,
            total=0.0,
            applied_discounts=[],
            notes=notes,
            valid_until=valid_until,
            trace=trace,
            error=error,
        )

    # ── 1. Basic input validation ───────────────────────────────────────────
    minimum_users_error = validate_minimum_users(users)
    if minimum_users_error is not None:
        return _invalid("users must be >= 1.", ["Number of users must be at least 1."])

    # ── 2. Load resources ───────────────────────────────────────────────────
    all_plans_data = get_all_plans()
    pricing_data = get_pricing_current()

    currency: str = pricing_data["currency"]
    trace["pricing://current"].append("currency")

    # ── 3. Locate plan in plans://all ───────────────────────────────────────
    plan_info = next((p for p in all_plans_data["plans"] if p["id"] == plan_id), None)
    if plan_info is None:
        return _invalid(
            f"Plan '{plan_id}' not found in plans://all.",
            [f"Plan '{plan_id}' does not exist. Available plans: starter, professional, enterprise."],
        )
    trace["plans://all"].append("limits.users")

    # ── 4. Locate plan in pricing://current ────────────────────────────────
    pricing_info = get_plan_pricing(pricing_data, plan_id)
    if pricing_info is None:
        return _invalid(
            f"Pricing for plan '{plan_id}' not found in pricing://current.",
            [f"No pricing found for plan '{plan_id}'."],
        )

    trace["pricing://current"].append(f"plans.{plan_id}.base_price.{billing_cycle}")
    trace["pricing://current"].append(f"plans.{plan_id}.per_user_price.{billing_cycle}")

    # ── 5. Handle custom / enterprise pricing ──────────────────────────────
    base_price_val: Optional[float] = pricing_info["base_price"].get(billing_cycle)
    per_user_price_val: Optional[float] = pricing_info["per_user_price"].get(billing_cycle)
    global_notes: List[str] = list(pricing_data.get("notes", []))
    trace["pricing://current"].append("notes")

    if base_price_val is None or per_user_price_val is None:
        return _invalid(
            f"Plan '{plan_id}' has custom pricing. Please contact sales for a tailored quote.",
            [
                "Enterprise pricing is custom and requires sales approval.",
                *global_notes,
            ],
        )

    # ── 6. Validate user limits ─────────────────────────────────────────────
    max_users: Optional[int] = pricing_info.get("maximum_users")
    validation_warnings: List[str] = []
    is_valid = True

    if max_users is not None and users > max_users:
        is_valid = False
        validation_warnings.append(
            f"The '{plan_id}' plan supports a maximum of {max_users} users "
            f"(requested: {users}). Consider upgrading to a higher-tier plan."
        )

    # ── 7. Build line items ─────────────────────────────────────────────────
    items = build_base_and_user_items(
        cycle=billing_cycle,
        base_price=base_price_val,
        per_user_price=per_user_price_val,
        users=users,
    )

    subtotal: float = round(sum(item.line_total for item in items), 2)

    # ── 8. Apply volume discounts (reduce total, not subtotal) ─────────────
    applied_discounts, total_discount = apply_volume_discounts(
        subtotal=subtotal,
        users=users,
        discounts=pricing_info.get("discounts", []),
    )

    # ── 9. Finalise totals ──────────────────────────────────────────────────
    # subtotal = raw sum of items (before discounts), per README formula
    # total   = subtotal - discounts + tax
    tax = 0.0
    total = round(subtotal - total_discount + tax, 2)

    result = GenerateQuoteResult(
        valid=is_valid,
        currency=currency,
        cycle=billing_cycle,
        plan_id=plan_id,
        users=users,
        items=items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        applied_discounts=applied_discounts,
        notes=[*validation_warnings, *global_notes],
        valid_until=valid_until,
        trace=trace,
    )
    logger.info(
        "Quote generated plan=%s valid=%s currency=%s total=%.2f",
        plan_id,
        result.valid,
        result.currency,
        result.total,
    )
    return result
