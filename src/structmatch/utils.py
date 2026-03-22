"""Helper utilities."""

from __future__ import annotations
from collections import Counter
from dataclasses import is_dataclass, fields
from typing import Any


def _is_dataclass_like(obj: Any) -> bool:
    return is_dataclass(obj) and not isinstance(obj, type)


def _get_fields(obj: Any) -> dict:
    """Get comparable fields from an object."""
    if _is_dataclass_like(obj):
        return {f.name: getattr(obj, f.name) for f in fields(obj)}
    try:
        return dict(vars(obj))
    except TypeError:
        return None


def _as_multiset(lst):
    """Convert a list to a Counter for order-independent comparison."""
    return Counter(_hashable(x) for x in lst)


def _hashable(x):
    """Make a value hashable for multiset comparison."""
    if isinstance(x, dict):
        return tuple(sorted((k, _hashable(v)) for k, v in x.items()))
    if isinstance(x, (list, tuple)):
        return tuple(_hashable(i) for i in x)
    if isinstance(x, set):
        return frozenset(_hashable(i) for i in x)
    return x


def _is_numeric(a, b) -> bool:
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool)


def _within_tolerance(a, b, tolerance: float) -> bool:
    if not _is_numeric(a, b):
        return a == b
    if tolerance <= 0.0:
        return a == b
    if tolerance > 1:
        return abs(a - b) <= tolerance
    return abs(a - b) <= tolerance * max(abs(a), abs(b), 1)


def _compare_strings(a: str, b: str, case_sensitive: bool) -> bool:
    if case_sensitive:
        return a == b
    return a.lower() == b.lower()


def _is_comparator(val) -> bool:
    from .comparators import Comparator
    return isinstance(val, Comparator) or (isinstance(val, type) and issubclass(val, Comparator) and val is not Comparator)


def _filter_keys(d: dict, ignore_keys) -> dict:
    if not ignore_keys:
        return d
    return {k: v for k, v in d.items() if k not in ignore_keys}
