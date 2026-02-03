"""EvalGuard - Simple validation for AI agent outputs."""

from .core import Expectation, ValidationError, check, expect

__version__ = "0.1.0"
__all__ = ["Expectation", "ValidationError", "__version__", "check", "expect"]
