from product_assistant.models import UsageProfile
from product_assistant.tools import estimate_cost


def test_estimate_cost_happy_path_professional_with_api_requests() -> None:
    # Given
    plan = "professional"
    usage = UsageProfile(users=22, projects=5, api_requests_per_month=100000)

    # When
    result = estimate_cost(plan=plan, usage=usage)

    # Then
    assert result.valid is True
    assert result.plan == plan
    assert result.total_estimated_cost == 177.0
    assert any(item.name == "Per API request" for item in result.items)
    assert result.error is None


def test_estimate_cost_invalid_when_plan_not_found() -> None:
    # Given
    plan = "premium"
    usage = UsageProfile(users=10)

    # When
    result = estimate_cost(plan=plan, usage=usage)

    # Then
    assert result.valid is False
    assert "not found" in (result.error or "")


def test_estimate_cost_custom_pricing_enterprise() -> None:
    # Given
    plan = "enterprise"
    usage = UsageProfile(users=100)

    # When
    result = estimate_cost(plan=plan, usage=usage)

    # Then
    assert result.valid is False
    assert "custom pricing" in (result.error or "")


def test_estimate_cost_limit_exceeded_marks_invalid() -> None:
    # Given
    plan = "starter"
    usage = UsageProfile(users=10, projects=5, api_requests_per_month=20000)

    # When
    result = estimate_cost(plan=plan, usage=usage)

    # Then
    assert result.valid is False
    assert any("exceeds" in note for note in result.notes)


def test_estimate_cost_without_api_usage_has_no_api_item() -> None:
    # Given
    plan = "starter"
    usage = UsageProfile(users=3, projects=1)

    # When
    result = estimate_cost(plan=plan, usage=usage)

    # Then
    assert result.valid is True
    assert all(item.name != "Per API request" for item in result.items)
    assert result.total_estimated_cost == 44.0
