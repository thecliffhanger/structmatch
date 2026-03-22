"""structmatch — Deep structural matching, diffing, and pattern matching for Python."""

from .core import eq, diff, match
from .comparators import (
    Comparator,
    ANY,
    TYPE,
    GT,
    LT,
    GE,
    LE,
    BETWEEN,
    REGEX,
    NOT,
)
from .diff import DiffResult
from .schema import Schema, SchemaError
from .options import MatchOptions

__version__ = "0.1.0"

__all__ = [
    "eq",
    "diff",
    "match",
    "ANY",
    "TYPE",
    "GT",
    "LT",
    "GE",
    "LE",
    "BETWEEN",
    "REGEX",
    "NOT",
    "Comparator",
    "DiffResult",
    "Schema",
    "SchemaError",
    "MatchOptions",
]
