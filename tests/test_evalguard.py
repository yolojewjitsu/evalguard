"""Tests for evalguard."""

import pytest

from evalguard import check, expect, ValidationError


class TestExpect:
    def test_contains_passes(self):
        expect("SELECT * FROM users").contains("SELECT").contains("FROM")

    def test_contains_fails(self):
        with pytest.raises(ValidationError, match="contain"):
            expect("hello world").contains("missing")

    def test_not_contains_passes(self):
        expect("SELECT * FROM users").not_contains("DROP").not_contains("DELETE")

    def test_not_contains_fails(self):
        with pytest.raises(ValidationError, match="not contain"):
            expect("DROP TABLE users").not_contains("DROP")

    def test_matches_passes(self):
        expect("user_123").matches(r"user_\d+")

    def test_matches_fails(self):
        with pytest.raises(ValidationError, match="match pattern"):
            expect("invalid").matches(r"user_\d+")

    def test_not_matches_passes(self):
        expect("hello").not_matches(r"\d+")

    def test_not_matches_fails(self):
        with pytest.raises(ValidationError, match="not match"):
            expect("hello123").not_matches(r"\d+")

    def test_valid_json_passes(self):
        expect('{"key": "value"}').valid_json()

    def test_valid_json_fails(self):
        with pytest.raises(ValidationError, match="valid JSON"):
            expect("not json").valid_json()

    def test_max_length_passes(self):
        expect("short").max_length(10)

    def test_max_length_fails(self):
        with pytest.raises(ValidationError, match="length"):
            expect("this is too long").max_length(5)

    def test_min_length_passes(self):
        expect("hello").min_length(3)

    def test_min_length_fails(self):
        with pytest.raises(ValidationError, match="length"):
            expect("hi").min_length(5)

    def test_not_empty_passes(self):
        expect("content").not_empty()

    def test_not_empty_fails(self):
        with pytest.raises(ValidationError, match="non-empty"):
            expect("   ").not_empty()

    def test_equals_passes(self):
        expect(42).equals(42)

    def test_equals_fails(self):
        with pytest.raises(ValidationError, match="Expected"):
            expect(42).equals(43)

    def test_is_type_passes(self):
        expect("hello").is_type(str)
        expect(42).is_type(int)
        expect([1, 2]).is_type(list)

    def test_is_type_fails(self):
        with pytest.raises(ValidationError, match="type"):
            expect("hello").is_type(int)

    def test_satisfies_passes(self):
        expect(10).satisfies(lambda x: x > 5)

    def test_satisfies_fails(self):
        with pytest.raises(ValidationError, match="satisfy"):
            expect(3).satisfies(lambda x: x > 5, "x > 5")

    def test_chaining(self):
        result = expect("SELECT id FROM users WHERE active = true")
        result.contains("SELECT").contains("FROM").not_contains("DROP").max_length(100)

    def test_value_property(self):
        exp = expect("hello")
        assert exp.value == "hello"


class TestCheck:
    def test_check_contains_passes(self):
        @check(contains=["SELECT", "FROM"])
        def sql_query():
            return "SELECT * FROM users"

        assert sql_query() == "SELECT * FROM users"

    def test_check_contains_fails(self):
        @check(contains=["SELECT"])
        def sql_query():
            return "invalid query"

        with pytest.raises(ValidationError):
            sql_query()

    def test_check_not_contains_passes(self):
        @check(not_contains=["DROP", "DELETE"])
        def safe_query():
            return "SELECT * FROM users"

        assert safe_query() == "SELECT * FROM users"

    def test_check_not_contains_fails(self):
        @check(not_contains=["DROP"])
        def dangerous_query():
            return "DROP TABLE users"

        with pytest.raises(ValidationError):
            dangerous_query()

    def test_check_valid_json(self):
        @check(valid_json=True)
        def json_response():
            return '{"status": "ok"}'

        assert json_response() == '{"status": "ok"}'

    def test_check_valid_json_fails(self):
        @check(valid_json=True)
        def bad_json():
            return "not json"

        with pytest.raises(ValidationError):
            bad_json()

    def test_check_max_length(self):
        @check(max_length=20)
        def short_response():
            return "brief"

        assert short_response() == "brief"

    def test_check_max_length_fails(self):
        @check(max_length=5)
        def long_response():
            return "this is way too long"

        with pytest.raises(ValidationError):
            long_response()

    def test_check_not_empty(self):
        @check(not_empty=True)
        def content():
            return "hello"

        assert content() == "hello"

    def test_check_not_empty_fails(self):
        @check(not_empty=True)
        def empty():
            return ""

        with pytest.raises(ValidationError):
            empty()

    def test_check_matches(self):
        @check(matches=r"^\d{4}-\d{2}-\d{2}$")
        def date_string():
            return "2026-02-03"

        assert date_string() == "2026-02-03"

    def test_check_matches_list(self):
        @check(matches=[r"SELECT", r"FROM"])
        def query():
            return "SELECT * FROM users"

        assert query() == "SELECT * FROM users"

    def test_check_satisfies(self):
        @check(satisfies=lambda x: len(x) > 5)
        def long_enough():
            return "hello world"

        assert long_enough() == "hello world"

    def test_check_on_fail_handler(self):
        def handler(error):
            return "fallback"

        @check(contains=["required"], on_fail=handler)
        def failing_func():
            return "missing"

        assert failing_func() == "fallback"

    def test_check_combined(self):
        @check(
            contains=["SELECT"],
            not_contains=["DROP", "DELETE", "TRUNCATE"],
            max_length=1000,
            not_empty=True,
        )
        def sql_agent(query: str) -> str:
            return f"SELECT * FROM users WHERE name = '{query}'"

        result = sql_agent("john")
        assert "SELECT" in result
        assert "john" in result

    def test_check_preserves_function_metadata(self):
        @check(not_empty=True)
        def documented_func():
            """This is a docstring."""
            return "value"

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a docstring."


class TestValidationError:
    def test_error_attributes(self):
        err = ValidationError("test message", value="test value", rule="test_rule")
        assert err.message == "test message"
        assert err.value == "test value"
        assert err.rule == "test_rule"

    def test_error_str(self):
        err = ValidationError("failed validation")
        assert str(err) == "failed validation"

    def test_error_repr(self):
        err = ValidationError("test", rule="contains")
        assert "ValidationError" in repr(err)
        assert "contains" in repr(err)
