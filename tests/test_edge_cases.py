"""Edge case tests for evalguard."""

import pytest
from evalguard import check, expect, ValidationError


class TestEdgeCases:
    def test_empty_string(self):
        """Test validation on empty string."""
        expect("").max_length(0)
        
        with pytest.raises(ValidationError):
            expect("").not_empty()

    def test_none_value(self):
        """Test validation on None - converts to empty string."""
        # None becomes "" for string comparisons
        expect(None).max_length(0)

        with pytest.raises(ValidationError):
            expect(None).contains("anything")

        # None should fail not_empty
        with pytest.raises(ValidationError) as exc:
            expect(None).not_empty()
        assert "None" in exc.value.message

    def test_empty_list_not_empty(self):
        """Test not_empty with empty list."""
        with pytest.raises(ValidationError) as exc:
            expect([]).not_empty()
        assert "list" in exc.value.message.lower()

        # Non-empty list should pass
        expect([1, 2, 3]).not_empty()

    def test_empty_dict_not_empty(self):
        """Test not_empty with empty dict."""
        with pytest.raises(ValidationError) as exc:
            expect({}).not_empty()
        assert "dict" in exc.value.message.lower()

        # Non-empty dict should pass
        expect({"key": "value"}).not_empty()

    def test_empty_set_not_empty(self):
        """Test not_empty with empty set."""
        with pytest.raises(ValidationError):
            expect(set()).not_empty()

        # Non-empty set should pass
        expect({1, 2}).not_empty()

    def test_empty_tuple_not_empty(self):
        """Test not_empty with empty tuple."""
        with pytest.raises(ValidationError):
            expect(()).not_empty()

        # Non-empty tuple should pass
        expect((1, 2)).not_empty()

    def test_zero_not_empty(self):
        """Test not_empty with zero - should fail (falsy value)."""
        with pytest.raises(ValidationError):
            expect(0).not_empty()

        # Non-zero should pass
        expect(42).not_empty()

    def test_max_length_zero(self):
        """Test max_length=0 allows only empty."""
        expect("").max_length(0)
        
        with pytest.raises(ValidationError):
            expect("x").max_length(0)

    def test_min_length_zero(self):
        """Test min_length=0 allows empty."""
        expect("").min_length(0)
        expect("anything").min_length(0)

    def test_empty_contains_list(self):
        """Test with empty contains list - should pass."""
        @check(contains=[])
        def func():
            return "anything"
        
        assert func() == "anything"

    def test_empty_not_contains_list(self):
        """Test with empty not_contains list - should pass."""
        @check(not_contains=[])
        def func():
            return "anything"
        
        assert func() == "anything"

    def test_unicode(self):
        """Test with unicode strings."""
        expect("Привет мир 🌍").contains("Привет").contains("🌍")

    def test_very_long_string(self):
        """Test with very long string."""
        long_str = "x" * 1000000
        expect(long_str).max_length(1000001).min_length(999999)

    def test_json_with_unicode(self):
        """Test valid_json with unicode."""
        expect('{"key": "значение 🎉"}').valid_json()

    def test_on_fail_returns_none(self):
        """Test on_fail handler that returns None."""
        @check(contains=["missing"], on_fail=lambda e: None)
        def func():
            return "no match"

        # Should return None from handler
        assert func() is None

    def test_invalid_regex_matches(self):
        """Test that invalid regex raises ValidationError, not re.error."""
        with pytest.raises(ValidationError) as exc:
            expect("test").matches("[invalid")
        assert "Invalid regex" in exc.value.message
        assert exc.value.rule == "matches"

    def test_invalid_regex_not_matches(self):
        """Test that invalid regex raises ValidationError in not_matches."""
        with pytest.raises(ValidationError) as exc:
            expect("test").not_matches("(unclosed")
        assert "Invalid regex" in exc.value.message
        assert exc.value.rule == "not_matches"
