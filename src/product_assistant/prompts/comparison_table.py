"""Comparison table prompt generator."""
from typing import List

from product_assistant.resources import (
    get_all_plans,
    get_features_by_plan,
    get_pricing_current,
)


def comparison_table() -> str:
    """
    Generate a strict Markdown comparison table for all plans.

    Uses only real data from plans://all, features://by_plan and pricing://current.
    
    Returns:
        Formatted prompt string with all plan data and table generation instructions
    """
    all_plans_data = get_all_plans()
    features_data = get_features_by_plan()
    pricing_data = get_pricing_current()

    plans = all_plans_data.get("plans", [])
    pricing_by_plan = {
        plan_pricing.get("plan_id"): plan_pricing
        for plan_pricing in pricing_data.get("plans", [])
    }

    def _fmt_feature_list(plan_id: str, max_items: int = 4) -> str:
        plan_features = features_data.get("plans", {}).get(plan_id, {})
        flat_items: List[str] = []
        for section_items in plan_features.values():
            if isinstance(section_items, list):
                flat_items.extend(section_items)
        if not flat_items:
            return "N/A"
        return ", ".join(flat_items[:max_items])

    rows: List[str] = []
    for plan in plans:
        plan_id = plan.get("id", "")
        limits = plan.get("limits", {})
        recommended_for = ", ".join(plan.get("recommended_for", [])) or "N/A"

        plan_pricing = pricing_by_plan.get(plan_id, {})
        base_monthly = (plan_pricing.get("base_price", {}) or {}).get("monthly")
        per_user_monthly = (plan_pricing.get("per_user_price", {}) or {}).get("monthly")

        base_monthly_text = str(base_monthly) if base_monthly is not None else "custom/contact sales"
        per_user_monthly_text = str(per_user_monthly) if per_user_monthly is not None else "custom/contact sales"

        rows.append(
            "| {name} | {recommended_for} | {users} | {projects} | {api} | {base_monthly} | {per_user_monthly} | {features} |".format(
                name=plan.get("name", plan_id),
                recommended_for=recommended_for,
                users=limits.get("users", "N/A"),
                projects=limits.get("projects", "N/A"),
                api=limits.get("api_requests_per_month", "N/A"),
                base_monthly=base_monthly_text,
                per_user_monthly=per_user_monthly_text,
                features=_fmt_feature_list(plan_id),
            )
        )

    table_header = "\n".join(
        [
            "| Plan | Recommended for | Users limit | Projects limit | API requests/month | Base monthly | Per-user monthly | Key features |",
            "|---|---|---:|---:|---:|---:|---:|---|",
            *rows,
        ]
    )

    return f"""You are an expert SaaS sales assistant.
Create a STRICT Markdown comparison table for all available plans.

## Data source (plans://all)
{plans}

## Data source (features://by_plan)
{features_data.get("plans", {})}

## Data source (pricing://current)
{pricing_data.get("plans", [])}

## Required output format
1. First output ONLY one Markdown table using exactly these columns:
   Plan | Recommended for | Users limit | Projects limit | API requests/month | Base monthly | Per-user monthly | Key features
2. Then output a short conclusion (2-3 lines) with plain recommendations.

## Rules
1. Use ONLY the provided data. Do not invent any feature, limit, or price.
2. If any value is missing/null, write "N/A" or "custom/contact sales" when pricing is custom.
3. Keep it concise and business-friendly.
4. Do not add extra sections, JSON, or explanations outside the requested table + short conclusion.

Reference table skeleton:
{table_header}
"""
