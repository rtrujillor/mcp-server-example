"""Sales pitch prompt generator."""
from typing import List

from product_assistant.resources import get_all_plans, get_features_by_plan


def sales_pitch(plan_id: str) -> str:
    """
    Generate a brief, honest sales pitch for a specific plan.

    Loads real data from plans://all and features://by_plan.
    Rules enforced in the prompt:
      - Do NOT invent prices or features.
      - Use exclusively plans://all and features://by_plan as data sources.
      - Do not mention prices; direct the prospect to use generate_quote for
        formal quotes.
        
    Args:
        plan_id: Plan identifier (starter, professional, enterprise)
        
    Returns:
        Formatted prompt string with plan data and instructions for LLM
    """
    all_plans_data = get_all_plans()
    features_data = get_features_by_plan()

    # Locate plan info
    plan_info = next((p for p in all_plans_data["plans"] if p["id"] == plan_id), None)
    if plan_info is None:
        available = ", ".join(p["id"] for p in all_plans_data["plans"])
        return (
            f"Error: plan '{plan_id}' not found. "
            f"Available plans: {available}."
        )

    plan_features = features_data["plans"].get(plan_id, {})

    # Serialise plan data for the LLM context
    limits = plan_info.get("limits", {})
    limits_lines = "\n".join(f"  - {k}: {v}" for k, v in limits.items())

    recommended_for = ", ".join(plan_info.get("recommended_for", []))

    def _section(title: str, items: List[str]) -> str:
        if not items:
            return ""
        lines = "\n".join(f"  - {item}" for item in items)
        return f"{title}:\n{lines}"

    features_block = "\n".join(
        _section(section.replace("_", " ").capitalize(), items)
        for section, items in plan_features.items()
        if items
    )

    return f"""You are an expert sales assistant for a SaaS product.
Your task is to write a SHORT, persuasive sales pitch (3–5 paragraphs) for the
**{plan_info["name"]}** plan targeted at a potential customer.

## Plan data (source: plans://all)

Name: {plan_info["name"]}
Description: {plan_info["description"]}
Recommended for: {recommended_for}

Limits:
{limits_lines}

## Feature details (source: features://by_plan)

{features_block}

## Rules — follow them strictly

1. Use ONLY the data provided above. Do NOT invent or assume any feature,
   limit, or capability not listed here.
2. Do NOT mention prices, costs, or billing amounts of any kind.
   If the prospect asks about pricing, instruct them to use the
   `generate_quote` tool for a formal, traceable quote.
3. Keep the tone professional, confident, and concise.
4. Highlight the top 3-4 features most relevant to the prospect context
   (or the plan's "recommended_for" audience if no context is given).
5. End with a clear call to action (e.g., request a demo, ask for a quote).

Write the sales pitch now."""
