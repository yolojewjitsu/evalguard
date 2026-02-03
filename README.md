# EvalGuard

Simple, zero-dependency validation for AI agent outputs.

## The Problem

AI agents produce unpredictable outputs. You need to validate them before using them, but existing tools are heavy:
- LangSmith: Requires cloud, vendor lock-in
- DeepEval: 50+ dependencies, expensive LLM-as-judge
- RAGAS: RAG-only, not general purpose

## The Solution

```python
from evalguard import check, expect

@check(contains=["SELECT"], not_contains=["DROP", "DELETE"])
def sql_agent(query: str) -> str:
    return llm.complete(f"Write SQL for: {query}")

# Or inline validation
result = agent.run("Get all users")
expect(result).contains("SELECT").not_contains("DROP").valid_json()
```

## Installation

```bash
pip install evalguard
```

## Features

- **Zero dependencies** - Only Python stdlib
- **Simple decorators** - `@check()` for validation rules
- **Fluent API** - `expect(value).contains().matches().valid_json()`
- **Deterministic checks** - No LLM needed for basic validation
- **pytest compatible** - Works with existing test infrastructure
- **Type hints** - Full typing support

## Usage

### Fluent Validation with `expect()`

```python
from evalguard import expect, ValidationError

result = agent.run("Generate SQL query")

# Chain multiple validations
expect(result).contains("SELECT").not_contains("DROP").max_length(1000)

# JSON validation
expect(response).valid_json()

# Regex matching
expect(date_str).matches(r"^\d{4}-\d{2}-\d{2}$")

# Custom predicates
expect(value).satisfies(lambda x: x > 0, "must be positive")
```

### Decorator Validation with `@check()`

```python
from evalguard import check

@check(
    contains=["SELECT", "FROM"],
    not_contains=["DROP", "DELETE", "TRUNCATE"],
    max_length=1000,
    not_empty=True,
)
def sql_agent(query: str) -> str:
    return llm.complete(query)

# Raises ValidationError if any check fails
result = sql_agent("Get all active users")
```

### Custom Failure Handler

```python
@check(contains=["required"], on_fail=lambda e: "fallback value")
def risky_agent(query: str) -> str:
    return llm.complete(query)

# Returns "fallback value" instead of raising on failure
```

### Available Validations

| Method | Description |
|--------|-------------|
| `.contains(s)` | Value must contain substring |
| `.not_contains(s)` | Value must not contain substring |
| `.matches(pattern)` | Value must match regex |
| `.not_matches(pattern)` | Value must not match regex |
| `.valid_json()` | Value must be valid JSON |
| `.max_length(n)` | Value length must be <= n |
| `.min_length(n)` | Value length must be >= n |
| `.not_empty()` | Value must not be empty/whitespace |
| `.equals(v)` | Value must equal v |
| `.is_type(t)` | Value must be instance of type |
| `.satisfies(fn)` | Custom predicate must return True |

## API

### `expect(value)`

Create a fluent expectation for chaining validations.

```python
exp = expect(value)
exp.contains("x").not_contains("y")
exp.value  # Access the original value
```

### `@check(**rules)`

Decorator to validate function return values.

```python
@check(
    contains=["a", "b"],           # List of required substrings
    not_contains=["x", "y"],       # List of forbidden substrings
    matches=r"pattern",            # Regex that must match (or list)
    not_matches=r"pattern",        # Regex that must not match (or list)
    valid_json=True,               # Must be valid JSON
    max_length=100,                # Max string length
    min_length=10,                 # Min string length
    not_empty=True,                # Must not be empty
    satisfies=lambda x: x > 0,     # Custom predicate
    on_fail=handler,               # Optional failure handler
)
def my_function():
    ...
```

### `ValidationError`

Raised when validation fails.

```python
try:
    expect(value).contains("required")
except ValidationError as e:
    print(e.message)  # "Expected value to contain 'required'"
    print(e.value)    # The actual value
    print(e.rule)     # "contains"
```

## Part of the Guard Suite

EvalGuard is part of a reliability suite for AI agents:

- **[LoopGuard](https://pypi.org/project/loopguard/)** - Prevent infinite loops
- **EvalGuard** - Validate outputs (this package)
- **FailGuard** - Detect drift and silent failures (coming soon)

## License

MIT