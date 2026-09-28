from product_assistant.prompts import comparison_table


def test_comparison_table_prompt_contains_required_columns_and_rules() -> None:
    # Given
    expected_columns = (
        "Plan | Recommended for | Users limit | Projects limit | "
        "API requests/month | Base monthly | Per-user monthly | Key features"
    )

    # When
    prompt_text = comparison_table()

    # Then
    assert "STRICT Markdown comparison table" in prompt_text
    assert expected_columns in prompt_text
    assert "Use ONLY the provided data" in prompt_text
    assert "custom/contact sales" in prompt_text


def test_comparison_table_prompt_includes_all_plan_names_in_reference() -> None:
    # Given / When
    prompt_text = comparison_table()

    # Then
    assert "Starter" in prompt_text
    assert "Professional" in prompt_text
    assert "Enterprise" in prompt_text
