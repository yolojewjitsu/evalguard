"""EvalGuard - Simple validation for AI agent outputs."""

from .core import check, expect, ValidationError, Expectation

__version__ = "0.1.0"
__all__ = ["check", "expect", "ValidationError", "Expectation", "__version__"]
