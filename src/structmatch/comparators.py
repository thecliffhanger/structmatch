"""Pattern-matching comparators."""

from __future__ import annotations
import re
from abc import ABC, abstractmethod


class Comparator(ABC):
    """Base class for custom comparators."""

    @abstractmethod
    def matches(self, a, b) -> bool:
        ...

    def __call__(self, a, b) -> bool:
        return self.matches(a, b)


class ANY(Comparator):
    """Matches anything."""

    def matches(self, a, b) -> bool:
        return True


class TYPE(Comparator):
    """Matches any value of a given type."""

    def __init__(self, expected_type):
        self.expected_type = expected_type

    def matches(self, a, b) -> bool:
        return isinstance(b, self.expected_type)


class GT(Comparator):
    """Matches if b > value."""

    def __init__(self, value):
        self.value = value

    def matches(self, a, b) -> bool:
        return b > self.value


class LT(Comparator):
    """Matches if b < value."""

    def __init__(self, value):
        self.value = value

    def matches(self, a, b) -> bool:
        return b < self.value


class GE(Comparator):
    """Matches if b >= value."""

    def __init__(self, value):
        self.value = value

    def matches(self, a, b) -> bool:
        return b >= self.value


class LE(Comparator):
    """Matches if b <= value."""

    def __init__(self, value):
        self.value = value

    def matches(self, a, b) -> bool:
        return b <= self.value


class BETWEEN(Comparator):
    """Matches if low <= b <= high."""

    def __init__(self, low, high):
        self.low = min(low, high)
        self.high = max(low, high)

    def matches(self, a, b) -> bool:
        return self.low <= b <= self.high


class REGEX(Comparator):
    """Matches if b (string) matches the regex pattern."""

    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern)

    def matches(self, a, b) -> bool:
        if not isinstance(b, str):
            return False
        return bool(self.pattern.search(b))


class NOT(Comparator):
    """Negates another comparator."""

    def __init__(self, comparator: Comparator):
        self.comparator = comparator

    def matches(self, a, b) -> bool:
        return not self.comparator.matches(a, b)
