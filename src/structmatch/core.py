"""Core functions: eq(), diff(), match()."""

from __future__ import annotations
from .options import MatchOptions
from .diff import DiffResult, diff as _diff
from .utils import (
    _is_numeric,
    _within_tolerance,
    _compare_strings,
    _filter_keys,
    _is_dataclass_like,
    _get_fields,
    _is_comparator,
    _as_multiset,
    _hashable,
)
from .comparators import Comparator


def _deep_eq(va, vb, opts: MatchOptions) -> bool:
    """Recursive deep equality."""
    # Check custom comparators first
    for comp in opts.comparators:
        if comp.matches(va, vb):
            return True

    # Handle type coercion: int/float interop
    if opts.type_coerce and _is_numeric(va, vb) and _within_tolerance(va, vb, opts.tolerance):
        return True

    # Type mismatch (but handle dataclass/NamedTuple equality)
    type_a = type(va)
    type_b = type(vb)
    if type_a != type_b:
        if opts.type_coerce and _is_numeric(va, vb) and _within_tolerance(va, vb, opts.tolerance):
            return True
        return False

    # None
    if va is None:
        return vb is None

    # Booleans
    if isinstance(va, bool):
        return va == vb

    # Strings
    if isinstance(va, str):
        return _compare_strings(va, vb, opts.case_sensitive)

    # Numbers
    if _is_numeric(va, vb):
        return _within_tolerance(va, vb, opts.tolerance)

    # Dicts
    if isinstance(va, dict):
        if len(va) != len(vb):
            return False
        va_f = _filter_keys(va, opts.ignore_keys)
        vb_f = _filter_keys(vb, opts.ignore_keys)
        if len(va_f) != len(vb_f):
            return False
        if set(va_f) != set(vb_f):
            return False
        for k in va_f:
            if not _deep_eq(va_f[k], vb_f[k], opts):
                return False
        return True

    # Lists / tuples
    if isinstance(va, (list, tuple)):
        if type(va) != type(vb):
            return False
        if len(va) != len(vb):
            return False
        if opts.ignore_order and isinstance(va, list):
            return _as_multiset(va) == _as_multiset(vb)
        return all(_deep_eq(a, b, opts) for a, b in zip(va, vb))

    # Sets
    if isinstance(va, set):
        return va == vb

    # Dataclasses / NamedTuples / objects with __dict__
    if _is_dataclass_like(va):
        fa = _get_fields(va)
        fb = _get_fields(vb)
        if fa is not None and fb is not None:
            return _deep_eq(fa, fb, opts)

    # Objects with __dict__ (but not dataclasses)
    if not isinstance(va, (type, bool, int, float, str, list, tuple, set, dict)):
        fa = _get_fields(va)
        fb = _get_fields(vb)
        if fa is not None and fb is not None and type(va) == type(vb):
            return _deep_eq(fa, fb, opts)

    # Fallback to ==
    return va == vb


def eq(a, b, *, tolerance: float = 0.0, ignore_order: bool = False,
       ignore_keys: list[str] | None = None, case_sensitive: bool = True,
       type_coerce: bool = False, comparators: list[Comparator] | None = None) -> bool:
    """Deep structural equality comparison."""
    opts = MatchOptions(
        tolerance=tolerance,
        ignore_order=ignore_order,
        ignore_keys=ignore_keys,
        case_sensitive=case_sensitive,
        type_coerce=type_coerce,
        comparators=comparators,
    )
    return _deep_eq(a, b, opts)


def diff(a, b, **opts) -> DiffResult:
    """Compute a deep diff between two structures."""
    return _diff(a, b, **opts)


def _deep_match(value, pattern, opts: MatchOptions) -> bool:
    """Check if value matches a pattern (which may contain comparators)."""
    # Pattern is a comparator (check FIRST, before any type checks)
    if _is_comparator(pattern):
        if isinstance(pattern, type):
            pattern = pattern()
        return pattern.matches(value, value)

    # None value
    if value is None:
        if pattern is None or pattern is type(None):
            return True
        if isinstance(pattern, type):
            return False
        return False

    # Pattern is a type
    if isinstance(pattern, type):
        if pattern is type(None):
            return value is None
        if pattern in (int, float):
            return _is_numeric(value, value) and isinstance(value, pattern)
        return isinstance(value, pattern)

    # Both dicts
    if isinstance(pattern, dict) and isinstance(value, dict):
        value_f = _filter_keys(value, opts.ignore_keys)
        for key, sub_pattern in pattern.items():
            if key not in value_f:
                return False
            if not _deep_match(value_f[key], sub_pattern, opts):
                return False
        return True

    # Both lists/tuples
    if isinstance(pattern, (list, tuple)) and isinstance(value, (list, tuple)):
        if len(pattern) != len(value):
            return False
        return all(_deep_match(v, p, opts) for v, p in zip(value, pattern))

    # String pattern with case sensitivity
    if isinstance(pattern, str) and isinstance(value, str):
        return _compare_strings(pattern, value, opts.case_sensitive)

    # Numeric with tolerance
    if _is_numeric(pattern, value) or _is_numeric(value, pattern):
        return _within_tolerance(pattern, value, opts.tolerance)

    # Literal match
    return pattern == value


def match(obj, pattern, **opts) -> bool:
    """Pattern matching: check if obj matches the given pattern."""
    options = MatchOptions(**opts)
    return _deep_match(obj, pattern, options)
