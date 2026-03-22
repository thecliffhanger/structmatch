# PRD — structmatch v1.0

## What It Is
Deep structural matching, comparison, and diffing for Python objects. Goes beyond `==` — compares nested structures semantically, produces human-readable diffs, and supports pattern matching.

## Why It Matters
- `deepdiff` exists but is heavy, complex, and slow
- Python has no stdlib deep structural matching
- Testing, serialization validation, and API response comparison all need this
- **Novel**: supports structural pattern matching (PEP 634 style) with wildcards, type constraints, and approximate matching (fuzzy numbers)

## Core Features

### 1. Deep Equality
```python
from structmatch import eq, match

eq({"a": [1, 2]}, {"a": [1, 2]})  # True
eq({"a": [1.0]}, {"a": [1]})       # True (numeric tolerance)
eq([{"b": 2}], [{"b": 2}])         # True (order-independent for dicts in lists)
```

### 2. Deep Diff
```python
from structmatch import diff

result = diff(old_dict, new_dict)
print(result)
# {
#   "added": {"c": 3},
#   "removed": {"d": 4},
#   "changed": {"a": (1, 2)},
#   "type_changes": {"b": (int, str)}
# }
```

### 3. Pattern Matching
```python
from structmatch import match, ANY, TYPE, GT, LT, BETWEEN

match({"status": 200, "body": {"count": 5}}, {
    "status": GT(199),
    "body": {"count": BETWEEN(1, 10)}
})  # True
```

### 4. Approximate Matching
```python
eq(3.14159, 3.14160, tolerance=0.001)  # True
eq([1.0, 2.0], [1.001, 1.999], tolerance=0.01)  # True
```

### 5. Schema Validation
```python
from structmatch import Schema

UserSchema = Schema({
    "name": str,
    "age": int,
    "email": str,
    "tags": [str],
    "metadata": {str: object}
})

UserSchema.validate(data)  # raises SchemaError or returns True
```

### 6. Custom Comparators
```python
from structmatch import eq, Comparator

class DateTimeWithin(Comparator):
    def __init__(self, seconds):
        self.seconds = seconds
    def matches(self, a, b):
        return abs((a - b).total_seconds()) < self.seconds

eq({"created": now}, {"created": later}, comparators=[DateTimeWithin(5)])
```

## API Surface
- `eq(a, b, **opts)` — deep equality with options
- `diff(a, b, **opts)` — produce diff dict
- `match(obj, pattern, **opts)` — pattern matching
- `Schema(definition)` — schema validation
- `ANY`, `TYPE`, `GT`, `LT`, `GE`, `LE`, `BETWEEN`, `REGEX`, `NOT` — pattern primitives
- `Comparator` — base class for custom comparators

## Options
- `tolerance=0.001` — numeric tolerance
- `ignore_order=True` — for lists (expensive)
- `ignore_keys=["id", "timestamp"]` — exclude keys
- `case_sensitive=False` — for strings
- `type_coerce=True` — treat int 1 and float 1.0 as equal

## Dependencies
- Zero required (stdlib only)
- Optional: `numpy` for array comparison

## Testing
- 150+ tests covering all features
- Property-based tests with hypothesis
- Performance: compare nested dicts 100x faster than deepdiff

## Target
- Python 3.10+
- MIT license
