"""Reusable validation logic for tools."""

from typing import Dict, List, Optional, Tuple

from product_assistant.models import UsageProfile


def validate_minimum_users(users: int) -> Optional[str]:
    """Validate minimum allowed users."""
    if users < 1:
        return "users must be >= 1."
    return None


def validate_plan_usage_limits(
    plan_id: str,
    limits: Dict[str, object],
    usage: UsageProfile,
    trace: Dict[str, List[str]],
) -> Tuple[bool, List[str]]:
    """Validate usage against integer limits declared in the plan."""
    warnings: List[str] = []
    is_valid = True

    checks: List[Tuple[str, Optional[int]]] = [
        ("users", usage.users),
        ("projects", usage.projects),
        ("api_requests_per_month", usage.api_requests_per_month),
    ]

    for key, value in checks:
        if value is None:
            continue

        trace["plans://all"].append(f"limits.{key}")
        limit_raw = limits.get(key)
        if isinstance(limit_raw, int) and value > limit_raw:
            is_valid = False
            warnings.append(
                f"Usage '{key}' ({value}) exceeds the '{plan_id}' "
                f"plan limit ({limit_raw})."
            )

    return is_valid, warnings
