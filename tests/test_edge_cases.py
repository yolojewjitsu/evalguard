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
