from product_assistant.prompts import sales_pitch


def test_sales_pitch_contains_guardrails_and_plan_data() -> None:
    # Given
    plan_id = "professional"

    # When
    prompt_text = sales_pitch(plan_id)

    # Then
    assert "Do NOT mention prices" in prompt_text
    assert "generate_quote" in prompt_text
    assert "Name: Professional" in prompt_text
    assert "Feature details" in prompt_text


def test_sales_pitch_returns_error_for_unknown_plan() -> None:
    # Given
    plan_id = "premium"

    # When
    prompt_text = sales_pitch(plan_id)

    # Then
    assert prompt_text.startswith("Error:")
    assert "Available plans" in prompt_text
