# server.py
"""Main MCP server entry point."""
from typing import Any, Dict, Literal

from mcp.server.fastmcp import FastMCP

from product_assistant.models import (
    EstimateCostResult,
    GenerateQuoteResult,
    UsageProfile,
)
from product_assistant.prompts import (
    comparison_table as _comparison_table,
    sales_pitch as _sales_pitch,
)
from product_assistant.resources import (
    get_all_plans as _get_all_plans,
    get_features_by_plan as _get_features_by_plan,
    get_pricing_current as _get_pricing_current,
)
from product_assistant.tools import (
    estimate_cost as _estimate_cost,
    generate_quote as _generate_quote,
)

# Initialize FastMCP instance
mcp = FastMCP("Product Assistant")

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("plans://all")
def get_all_plans() -> Dict[str, Any]:
    """Return all available subscription plans."""
    return _get_all_plans()

@mcp.resource("features://by_plan")
def get_features_by_plan() -> Dict[str, Any]:
    """Return detailed feature breakdown for each plan."""
    return _get_features_by_plan()

@mcp.resource("pricing://current")
def get_pricing_current() -> Dict[str, Any]:
    """Return current pricing information for all plans."""
    return _get_pricing_current()

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
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
    """
    return _generate_quote(plan_id, users, billing_cycle)


@mcp.tool()
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
    """
    return _estimate_cost(plan, usage)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@mcp.prompt()
def sales_pitch(plan_id: str) -> str:
    """
    Generate a brief, honest sales pitch for a specific plan.

    Loads real data from plans://all and features://by_plan.
    Rules enforced in the prompt:
      - Do NOT invent prices or features.
      - Use exclusively plans://all and features://by_plan as data sources.
      - Do not mention prices; direct the prospect to use generate_quote for
        formal quotes.
    """
    return _sales_pitch(plan_id)


@mcp.prompt()
def comparison_table() -> str:
    """
    Generate a strict Markdown comparison table for all plans.

    Uses only real data from plans://all, features://by_plan and pricing://current.
    """
    return _comparison_table()


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
