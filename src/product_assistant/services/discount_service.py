"""Business rules for pricing discounts."""

from typing import Any, Dict, List, Tuple


def apply_volume_discounts(
    subtotal: float,
    users: int,
    discounts: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], float]:
    """Apply supported volume discounts and return details plus total amount."""
    applied_discounts: List[Dict[str, Any]] = []
    total_discount = 0.0

    for discount in discounts:
        if discount.get("type") != "volume":
            continue

        condition = str(discount.get("condition", ""))
        percentage = float(discount.get("percentage", 0))

        try:
            operator_map = {
                ">=": lambda a, b: a >= b,
                ">": lambda a, b: a > b,
                "<=": lambda a, b: a <= b,
                "<": lambda a, b: a < b,
                "==": lambda a, b: a == b,
            }
            for operator, predicate in operator_map.items():
                if operator in condition:
                    _, threshold_text = condition.split(operator)
                    threshold = int(threshold_text.strip())
                    if predicate(users, threshold):
                        discount_amount = round(subtotal * (percentage / 100), 2)
                        total_discount = round(total_discount + discount_amount, 2)
                        applied_discounts.append(
                            {
                                "type": "volume",
                                "condition": condition.strip(),
                                "percentage": percentage,
                                "amount": discount_amount,
                            }
                        )
                    break
        except (ValueError, KeyError):
            continue

    return applied_discounts, total_discount
