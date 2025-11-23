# ANCHOR: tests.unit.actions-validation
# TITLE: Unit tests for server actions Pydantic validation
# ROLE: testing/unit layer
# COVERS: server.actions.models
# SCENARIOS: Valid/invalid payloads, field validation, type checking

"""
Unit tests for server actions Pydantic models.

Phase 5: Data Loading & Server Actions
Tests validation logic for request payloads:
- CreateTodoPayload: text field validation
- UpdateTodoPayload: done field validation
- Error messages for invalid inputs
"""

import pytest
from pydantic import ValidationError
from server.actions import CreateTodoPayload, UpdateTodoPayload


class TestCreateTodoPayload:
    """Test CreateTodoPayload validation."""

    def test_valid_payload(self):
        """Valid payload with non-empty text."""
        payload = CreateTodoPayload(text="New todo")
        assert payload.text == "New todo"

    def test_empty_string_rejected(self):
        """Empty string should be rejected (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTodoPayload(text="")

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("at least 1 character" in str(e).lower() or "min_length" in str(e).lower() for e in errors)

    def test_missing_text_field(self):
        """Missing text field should raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTodoPayload()

        errors = exc_info.value.errors()
        assert len(errors) > 0
        # Check that 'text' field is mentioned in error
        assert any("text" in str(e).lower() for e in errors)

    def test_wrong_type(self):
        """Non-string text should raise validation error."""
        with pytest.raises(ValidationError):
            CreateTodoPayload(text=123)

    def test_whitespace_only_string(self):
        """Whitespace-only string is technically valid (server trims).

        NOTE: Server logic should handle trimming, not validation.
        Pydantic only checks min_length on raw string.
        """
        # This passes validation (has 3 chars), server should trim and check
        payload = CreateTodoPayload(text="   ")
        assert payload.text == "   "


class TestUpdateTodoPayload:
    """Test UpdateTodoPayload validation."""

    def test_valid_true(self):
        """Valid payload with done=True."""
        payload = UpdateTodoPayload(done=True)
        assert payload.done is True

    def test_valid_false(self):
        """Valid payload with done=False."""
        payload = UpdateTodoPayload(done=False)
        assert payload.done is False

    def test_missing_done_field(self):
        """Missing done field should raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateTodoPayload()

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("done" in str(e).lower() for e in errors)

    def test_wrong_type_string_coerced(self):
        """String value is coerced to bool by Pydantic.

        NOTE: Pydantic v2 coerces "true" → True, "false" → False
        This is acceptable for our use case.
        """
        payload = UpdateTodoPayload(done="true")
        assert payload.done is True  # Coerced

        payload2 = UpdateTodoPayload(done="false")
        assert payload2.done is False  # Coerced

    def test_wrong_type_number_coerced(self):
        """Number value is coerced to bool by Pydantic.

        NOTE: Pydantic v2 coerces 1 → True, 0 → False
        This is acceptable for our use case.
        """
        payload = UpdateTodoPayload(done=1)
        assert payload.done is True  # Coerced

        payload2 = UpdateTodoPayload(done=0)
        assert payload2.done is False  # Coerced

    def test_none_value(self):
        """None value should raise validation error."""
        with pytest.raises(ValidationError):
            UpdateTodoPayload(done=None)
