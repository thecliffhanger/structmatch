"""Schema validation."""

from __future__ import annotations
from .utils import _is_comparator


class SchemaError(Exception):
    """Raised when schema validation fails."""

    def __init__(self, errors: list[dict]):
        self.errors = errors
        parts = []
        for e in errors:
            path = e.get("path", "root")
            msg = e.get("message", "validation error")
            parts.append(f"  {path}: {msg}")
        super().__init__("Schema validation failed:\n" + "\n".join(parts))


def _validate_type(value, expected, path: str, errors: list):
    """Validate a value against an expected type/schema."""
    if expected is None or expected is type(None):
        if value is not None:
            errors.append({"path": path, "message": f"expected None, got {type(value).__name__}: {value!r}"})
        return

    if isinstance(expected, type):
        if isinstance(value, bool) and expected in (int, float):
            errors.append({"path": path, "message": f"expected {expected.__name__}, got bool"})
            return
        if not isinstance(value, expected):
            # Allow int/float coercion
            if expected in (int, float) and isinstance(value, (int, float)) and not isinstance(value, bool):
                return
            if expected is float and isinstance(value, int) and not isinstance(value, bool):
                return
            errors.append({"path": path, "message": f"expected {expected.__name__}, got {type(value).__name__}: {value!r}"})
        return

    if isinstance(expected, dict):
        if not isinstance(value, dict):
            errors.append({"path": path, "message": f"expected dict, got {type(value).__name__}"})
            return
        for key, sub_schema in expected.items():
            if key not in value:
                errors.append({"path": f"{path}.{key}", "message": "missing required key"})
            else:
                _validate_type(value[key], sub_schema, f"{path}.{key}", errors)
        return

    if isinstance(expected, list):
        schema = expected[0] if expected else None
        if not isinstance(value, (list, tuple)):
            errors.append({"path": path, "message": f"expected list, got {type(value).__name__}"})
            return
        for i, item in enumerate(value):
            if schema is not None:
                _validate_type(item, schema, f"{path}[{i}]", errors)
        return

    if isinstance(expected, tuple):
        if not isinstance(value, (list, tuple)):
            errors.append({"path": path, "message": f"expected tuple/list, got {type(value).__name__}"})
            return
        if len(value) != len(expected):
            errors.append({"path": path, "message": f"expected {len(expected)} elements, got {len(value)}"})
            return
        for i, (item, sub_schema) in enumerate(zip(value, expected)):
            _validate_type(item, sub_schema, f"{path}[{i}]", errors)
        return

    if isinstance(expected, set):
        if not isinstance(expected, frozenset):
            expected = frozenset(expected)
        if not isinstance(value, (list, tuple, set, frozenset)):
            errors.append({"path": path, "message": f"expected set/list, got {type(value).__name__}"})
            return
        if set(value) != set(expected):
            errors.append({"path": path, "message": f"expected one of {expected}, got {set(value)}"})
        return

    if _is_comparator(expected):
        if not expected.matches(None, value):
            errors.append({"path": path, "message": f"failed comparator {type(expected).__name__}"})
        return

    # Literal value
    if value != expected:
        errors.append({"path": path, "message": f"expected {expected!r}, got {value!r}"})


class Schema:
    """Schema validator for Python structures."""

    def __init__(self, definition):
        self.definition = definition

    def validate(self, data) -> bool:
        errors = []
        _validate_type(data, self.definition, "root", errors)
        if errors:
            raise SchemaError(errors)
        return True

    def is_valid(self, data) -> bool:
        try:
            self.validate(data)
            return True
        except SchemaError:
            return False
