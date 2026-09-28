from product_assistant.resources import (
    get_all_plans,
    get_features_by_plan,
    get_pricing_current,
)


def test_get_all_plans_contains_expected_plan_ids() -> None:
    # Given
    expected_plan_ids = {"starter", "professional", "enterprise"}

    # When
    data = get_all_plans()
    observed_plan_ids = {plan["id"] for plan in data["plans"]}

    # Then
    assert expected_plan_ids.issubset(observed_plan_ids)


def test_get_features_by_plan_has_core_sections() -> None:
    # Given
    expected_sections = {
        "core_features",
        "analytics",
        "security",
        "support",
        "integrations",
    }

    # When
    data = get_features_by_plan()
    professional = data["plans"]["professional"]

    # Then
    assert expected_sections.issubset(set(professional.keys()))


def test_get_pricing_current_has_monthly_and_yearly_cycles() -> None:
    # Given
    expected_cycles = {"monthly", "yearly"}

    # When
    data = get_pricing_current()

    # Then
    assert expected_cycles.issubset(set(data["billing_cycles"]))
    assert data["currency"] == "EUR"
