from product_assistant.tools import generate_quote


def test_generate_quote_happy_path_professional_monthly() -> None:
    # Given
    plan_id = "professional"
    users = 22
    billing_cycle = "monthly"

    # When
    result = generate_quote(plan_id=plan_id, users=users, billing_cycle=billing_cycle)

    # Then
    assert result.valid is True
    assert result.plan_id == plan_id
    assert result.cycle == billing_cycle
    assert result.subtotal == 167.0
    assert result.total == 150.3
    assert len(result.items) == 2
    assert result.error is None


def test_generate_quote_invalid_when_users_less_than_one() -> None:
    # Given
    users = 0

    # When
    result = generate_quote(plan_id="starter", users=users, billing_cycle="monthly")

    # Then
    assert result.valid is False
    assert result.error == "users must be >= 1."


def test_generate_quote_invalid_when_plan_not_found() -> None:
    # Given
    unknown_plan = "premium"

    # When
    result = generate_quote(plan_id=unknown_plan, users=10, billing_cycle="monthly")

    # Then
    assert result.valid is False
    assert "not found" in (result.error or "")


def test_generate_quote_custom_pricing_for_enterprise() -> None:
    # Given
    plan_id = "enterprise"

    # When
    result = generate_quote(plan_id=plan_id, users=100, billing_cycle="monthly")

    # Then
    assert result.valid is False
    assert "custom pricing" in (result.error or "")


def test_generate_quote_limit_exceeded_marks_invalid_but_keeps_quote() -> None:
    # Given
    plan_id = "professional"
    users = 50

    # When
    result = generate_quote(plan_id=plan_id, users=users, billing_cycle="yearly")

    # Then
    assert result.valid is False
    assert result.subtotal > 0
    assert result.total > 0
    assert any("maximum" in note for note in result.notes)
