# structmatch

[![PyPI version](https://badge.fury.io/py/structmatch.svg)](https://pypi.org/project/structmatch)
[![Python versions](https://img.shields.io/pypi/pyversions/structmatch.svg)](https://pypi.org/project/structmatch)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Deep structural matching, diffing, and pattern matching for Python. Zero dependencies.

## Install

```bash
pip install structmatch
```

## Quick Start

```python
from structmatch import eq, diff, match, ANY, GT, LT, BETWEEN

# Deep equality
eq({"a": [1, 2]}, {"a": [1, 2]})  # True

# Approximate matching
eq(3.14159, 3.14160, tolerance=0.001)  # True

# Order-independent lists
eq([1, 2, 3], [3, 2, 1], ignore_order=True)  # True

# Ignore specific keys
eq({"a": 1, "id": 999}, {"a": 1, "id": 1}, ignore_keys=["id"])  # True

# Case-insensitive strings
eq("Hello", "hello", case_sensitive=False)  # True

# Type coercion (int == float)
eq(1, 1.0, type_coerce=True)  # True

# Deep diff
result = diff({"a": 1, "b": 2}, {"a": 1, "b": 20, "c": 3})
print(result.added)    # {"c": 3}
print(result.changed)  # {"b": (2, 20)}

# Pattern matching
match({"status": 200, "count": 5}, {
    "status": GT(199),
    "count": BETWEEN(1, 10),
})  # True

match(42, ANY)  # True
match("hello@example.com", REGEX(r"@"))  # True
```

## Schema Validation

```python
from structmatch import Schema

UserSchema = Schema({
    "name": str,
    "age": int,
    "tags": [str],
    "metadata": {str: object},
})

UserSchema.validate({"name": "Alice", "age": 30, "tags": ["admin"], "metadata": {"key": "val"}})  # True
```

## Custom Comparators

```python
from structmatch import eq, Comparator

class DateTimeWithin(Comparator):
    def __init__(self, seconds):
        self.seconds = seconds
    def matches(self, a, b):
        return abs((a - b).total_seconds()) < self.seconds

eq({"created": now}, {"created": later}, comparators=[DateTimeWithin(5)])
```

## All Comparators

| Comparator | Matches |
|---|---|
| `ANY` | Anything |
| `TYPE(t)` | Any value of type `t` |
| `GT(n)` | `value > n` |
| `LT(n)` | `value < n` |
| `GE(n)` | `value >= n` |
| `LE(n)` | `value <= n` |
| `BETWEEN(a, b)` | `a <= value <= b` |
| `REGEX(pattern)` | String matches regex |
| `NOT(comp)` | Negates another comparator |

## License

MIT

---

Part of the [thecliffhanger](https://github.com/thecliffhanger) open source suite.
