"""Core validation logic for AI agent outputs."""

from __future__ import annotations

import json
import re
from functools import wraps
from re import Pattern
from typing import Any, Callable, TypeVar

__all__ = ["Expectation", "ValidationError", "check", "expect"]

T = TypeVar("T")


class ValidationError(Exception):
    """Raised when validation fails.

    Attributes:
        message: Description of the validation failure.
        value: The value that failed validation.
        rule: The rule that was violated.

    """

    __slots__ = ("message", "rule", "value")

    def __init__(
        self,
        message: str,
        value: Any = None,
        rule: str | None = None,
    ) -> None:
        self.message = message
        self.value = value
        self.rule = rule
        super().__init__(message)

    def __repr__(self) -> str:
        return f"ValidationError({self.message!r}, rule={self.rule!r})"


class Expectation:
    """Fluent interface for validating values.

    Example:
        expect(result).contains("SELECT").not_contains("DROP").valid_json()

    """

    __slots__ = ("_str_value", "_value")

    def __init__(self, value: Any) -> None:
        """Initialize with a value to validate.

        Note: For bytes values, str(bytes) gives "b'...'" representation,
        not the decoded content. Decode bytes before passing if needed.
        """
        self._value = value
        self._str_value = str(value) if value is not None else ""

    def contains(self, substring: str) -> Expectation:
        """Assert that the value contains the given substring."""
        if substring not in self._str_value:
            raise ValidationError(
                f"Expected value to contain {substring!r}",
                value=self._value,
                rule="contains",
            )
        return self

    def not_contains(self, substring: str) -> Expectation:
        """Assert that the value does not contain the given substring."""
        if substring in self._str_value:
            raise ValidationError(
                f"Expected value to not contain {substring!r}",
                value=self._value,
                rule="not_contains",
            )
        return self

    def matches(self, pattern: str | Pattern[str]) -> Expectation:
        """Assert that the value matches the given regex pattern."""
        if isinstance(pattern, str):
            try:
                pattern = re.compile(pattern)
            except re.error as e:
                raise ValidationError(
                    f"Invalid regex pattern: {e}",
                    value=self._value,
                    rule="matches",
                ) from e
        if not pattern.search(self._str_value):
            raise ValidationError(
                f"Expected value to match pattern {pattern.pattern!r}",
                value=self._value,
                rule="matches",
            )
        return self

    def not_matches(self, pattern: str | Pattern[str]) -> Expectation:
        """Assert that the value does not match the given regex pattern."""
        if isinstance(pattern, str):
            try:
                pattern = re.compile(pattern)
            except re.error as e:
                raise ValidationError(
                    f"Invalid regex pattern: {e}",
                    value=self._value,
                    rule="not_matches",
                ) from e
        if pattern.search(self._str_value):
            raise ValidationError(
                f"Expected value to not match pattern {pattern.pattern!r}",
                value=self._value,
                rule="not_matches",
            )
        return self

    def valid_json(self) -> Expectation:
        """Assert that the value is valid JSON."""
        try:
            json.loads(self._str_value)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValidationError(
                f"Expected valid JSON: {e}",
                value=self._value,
                rule="valid_json",
            ) from e
        return self

    def max_length(self, length: int) -> Expectation:
        """Assert that the string representation length is at most the given length.

        Note: For non-string values, this checks len(str(value)), not len(value).
        """
        if len(self._str_value) > length:
            raise ValidationError(
                f"Expected length <= {length}, got {len(self._str_value)}",
                value=self._value,
                rule="max_length",
            )
        return self

    def min_length(self, length: int) -> Expectation:
        """Assert that the string representation length is at least the given length.

        Note: For non-string values, this checks len(str(value)), not len(value).
        """
        if len(self._str_value) < length:
            raise ValidationError(
                f"Expected length >= {length}, got {len(self._str_value)}",
                value=self._value,
                rule="min_length",
            )
        return self

    def not_empty(self) -> Expectation:
        """Assert that the value is not empty.

        For strings: checks that the stripped value is non-empty.
        For collections (list, dict, set, tuple): checks length > 0.
        For other types: checks truthiness.
        """
        # Handle None explicitly
        if self._value is None:
            raise ValidationError(
                "Expected non-empty value, got None",
                value=self._value,
                rule="not_empty",
            )
        # Handle strings: check stripped content
        if isinstance(self._value, str):
            if not self._value.strip():
                raise ValidationError(
                    "Expected non-empty value",
                    value=self._value,
                    rule="not_empty",
                )
        # Handle collections: check length
        elif isinstance(self._value, (list, dict, set, frozenset, tuple)):
            if len(self._value) == 0:
                raise ValidationError(
                    f"Expected non-empty {type(self._value).__name__}",
                    value=self._value,
                    rule="not_empty",
                )
        # Handle other types: check truthiness
        elif not self._value:
            raise ValidationError(
                "Expected non-empty value",
                value=self._value,
                rule="not_empty",
            )
        return self

    def equals(self, expected: Any) -> Expectation:
        """Assert that the value equals the expected value."""
        if self._value != expected:
            raise ValidationError(
                f"Expected {expected!r}, got {self._value!r}",
                value=self._value,
                rule="equals",
            )
        return self

    def is_type(self, expected_type: type) -> Expectation:
        """Assert that the value is of the expected type."""
        if not isinstance(self._value, expected_type):
            raise ValidationError(
                f"Expected type {expected_type.__name__}, "
                f"got {type(self._value).__name__}",
                value=self._value,
                rule="is_type",
            )
        return self

    def satisfies(
        self,
        predicate: Callable[[Any], bool],
        description: str = "custom predicate",
    ) -> Expectation:
        """Assert that the value satisfies the given predicate.

        If the predicate raises an exception, it is wrapped in ValidationError.
        """
        try:
            result = predicate(self._value)
        except Exception as e:
            raise ValidationError(
                f"Predicate '{description}' raised an exception: {e}",
                value=self._value,
                rule="satisfies",
            ) from e
        if not result:
            raise ValidationError(
                f"Value did not satisfy {description}",
                value=self._value,
                rule="satisfies",
            )
        return self

    @property
    def value(self) -> Any:
        """Return the wrapped value."""
        return self._value


def expect(value: Any) -> Expectation:
    """Create an expectation for fluent validation.

    Example:
        expect(result).contains("SELECT").not_contains("DROP").valid_json()

    Args:
        value: The value to validate.

    Returns:
        An Expectation object for chaining validations.

    """
    return Expectation(value)


def check(
    *,
    contains: list[str] | None = None,
    not_contains: list[str] | None = None,
    matches: str | Pattern[str] | list[str | Pattern[str]] | None = None,
    not_matches: str | Pattern[str] | list[str | Pattern[str]] | None = None,
    valid_json: bool = False,
    max_length: int | None = None,
    min_length: int | None = None,
    not_empty: bool = False,
    satisfies: Callable[[Any], bool] | None = None,
    on_fail: Callable[[ValidationError], Any] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Validate function return values with a decorator.

    Example:
        @check(contains=["SELECT"], not_contains=["DROP", "DELETE"])
        def sql_agent(query):
            return llm.complete(query)

    Args:
        contains: List of substrings that must be present.
        not_contains: List of substrings that must not be present.
        matches: Regex pattern(s) that must match.
        not_matches: Regex pattern(s) that must not match.
        valid_json: If True, validate that output is valid JSON.
        max_length: Maximum allowed length.
        min_length: Minimum required length.
        not_empty: If True, validate that output is not empty.
        satisfies: Custom predicate function.
        on_fail: Optional callback on validation failure. If provided and returns
                 a non-None value, that value is returned instead of raising.
                 If it returns None, None is returned (not the original result).

    Raises:
        ValidationError: If any validation fails (unless on_fail handles it).

    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            result = fn(*args, **kwargs)

            try:
                exp = expect(result)

                if not_empty:
                    exp.not_empty()

                if contains:
                    for s in contains:
                        exp.contains(s)

                if not_contains:
                    for s in not_contains:
                        exp.not_contains(s)

                if matches:
                    if isinstance(matches, (str, Pattern)):
                        patterns = [matches]
                    else:
                        patterns = matches
                    for p in patterns:
                        exp.matches(p)

                if not_matches:
                    if isinstance(not_matches, (str, Pattern)):
                        patterns = [not_matches]
                    else:
                        patterns = not_matches
                    for p in patterns:
                        exp.not_matches(p)

                if valid_json:
                    exp.valid_json()

                if max_length is not None:
                    exp.max_length(max_length)

                if min_length is not None:
                    exp.min_length(min_length)

                if satisfies is not None:
                    exp.satisfies(satisfies, "custom check")

            except ValidationError as e:
                if on_fail is not None:
                    return on_fail(e)
                raise

            return result

        return wrapper

    return decorator
