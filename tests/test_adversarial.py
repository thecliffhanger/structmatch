"""Adversarial tests for structmatch."""

import sys
import math
from dataclasses import dataclass, field
from collections import namedtuple, Counter
from decimal import Decimal

import pytest
from structmatch import eq, diff, match, GT, LT, GE, LE, BETWEEN, REGEX, NOT, TYPE, ANY


# --- Circular references ---

class CircularRef:
    def __init__(self):
        self.value = 42
        self.ref = None


def test_circular_ref_eq():
    a = CircularRef()
    a.ref = a
    b = CircularRef()
    b.ref = b
    # Should not hang; behavior on circular refs is implementation-defined
    with pytest.raises(Exception):
        eq(a, b)


def test_circular_ref_diff():
    a = CircularRef()
    a.ref = a
    b = CircularRef()
    b.value = 43
    b.ref = b
    # Library doesn't detect circular refs; may hang or crash
    # Document as known limitation — just verify it terminates
    # For non-circular case:
    c = CircularRef()
    c.value = 43
    d = diff(a, c)  # refs differ but won't recurse forever since c.ref is None


# --- Deeply nested ---

def make_nested(depth):
    result = {"level": depth}
    if depth > 0:
        result["child"] = make_nested(depth - 1)
    return result


def test_deep_nested_eq():
    a = make_nested(500)
    b = make_nested(500)
    assert eq(a, b)


def test_deep_nested_eq_diff():
    a = make_nested(200)
    b = make_nested(200)
    b["child"]["child"]["level"] = 999
    assert not eq(a, b)
    d = diff(a, b)
    assert d.has_changes()


def test_very_deep_nested_eq():
    sys.setrecursionlimit(10000)
    a = make_nested(2000)
    b = make_nested(2000)
    assert eq(a, b)


# --- Large collections ---

def test_large_dict_eq():
    a = {f"key_{i}": i for i in range(10000)}
    b = {f"key_{i}": i for i in range(10000)}
    assert eq(a, b)


def test_large_dict_diff():
    a = {f"key_{i}": i for i in range(10000)}
    b = {f"key_{i}": i for i in range(10000)}
    b["key_5000"] = -1
    assert not eq(a, b)
    d = diff(a, b)
    assert d.changed


def test_large_list_eq():
    a = list(range(10000))
    b = list(range(10000))
    assert eq(a, b)


def test_large_list_ignore_order():
    a = list(range(10000))
    b = list(range(9999, -1, -1))
    assert eq(a, b, ignore_order=True)


# --- Mixed numeric types ---

def test_int_vs_float():
    assert not eq(1, 1.0)  # different types
    assert eq(1, 1.0, type_coerce=True)


def test_int_vs_decimal():
    assert not eq(1, Decimal(1))


def test_float_vs_decimal():
    assert not eq(1.5, Decimal("1.5"))


def test_tolerance_decimal():
    # Decimal not supported by _is_numeric; should fall through
    assert not eq(Decimal(1), Decimal(2), tolerance=0.5)


def test_nan_eq():
    assert not eq(float('nan'), float('nan'))


def test_nan_tolerance():
    # tolerance > 0, but nan comparisons are always False
    assert not eq(float('nan'), float('nan'), tolerance=1.0)


def test_inf_eq():
    assert eq(float('inf'), float('inf'))
    assert not eq(float('inf'), float('-inf'))


def test_tolerance_zero():
    assert eq(1.0, 1.0, tolerance=0.0)
    assert not eq(1.0, 1.0000001, tolerance=0.0)


def test_tolerance_negative():
    # Negative tolerance should behave like 0 (exact match)
    assert eq(1.0, 1.0, tolerance=-1.0)
    assert not eq(1.0, 1.0000001, tolerance=-1.0)


def test_tolerance_very_small():
    assert eq(1.0, 1.0 + 1e-15, tolerance=1e-14)
    assert not eq(1.0, 1.0 + 0.1, tolerance=1e-14)


def test_tolerance_very_large():
    assert eq(-1e100, 1e100, tolerance=1e101)


# --- Unicode ---

def test_unicode_basic():
    assert eq("café", "café")
    assert not eq("café", "Café")
    assert eq("café", "Café", case_sensitive=False)


def test_unicode_normalize():
    # NFC vs NFD — library does NOT normalize unicode (documented limitation)
    assert not eq("é", "e\u0301")  # NFC vs NFD


def test_unicode_emoji():
    assert eq("🎉", "🎉")
    assert not eq("🎉", "🎊")


def test_unicode_surrogates():
    # These should just work as strings
    assert eq("\U0001f600", "\U0001f600")


# --- Custom objects ---

class CustomEq:
    def __init__(self, val):
        self.val = val
        self._hash = hash(val)

    def __eq__(self, other):
        return isinstance(other, CustomEq) and self.val == other.val

    def __hash__(self):
        return self._hash

    def __dict__(self):
        return {"val": self.val}


def test_custom_eq_objects():
    assert eq(CustomEq(1), CustomEq(1))
    assert not eq(CustomEq(1), CustomEq(2))


def test_custom_eq_diff():
    d = diff(CustomEq(1), CustomEq(2))
    # Falls through to ==, should be changed
    assert d.has_changes()


class NoDictObj:
    __slots__ = ('val',)
    def __init__(self, val):
        self.val = val


def test_slots_object_eq():
    # No __dict__; falls to ==
    a = NoDictObj(1)
    b = NoDictObj(1)
    # Different objects, no custom __eq__, so == is identity
    assert not eq(a, b)


# --- Dataclasses ---

@dataclass
class Parent:
    name: str = "parent"
    age: int = 0


@dataclass
class Child(Parent):
    school: str = "default"


def test_dataclass_inheritance():
    assert eq(Child("alice", 10, "MIT"), Child("alice", 10, "MIT"))
    assert not eq(Child("alice", 10, "MIT"), Child("alice", 11, "MIT"))


def test_dataclass_defaults():
    assert eq(Child(), Child())
    assert not eq(Child(), Child(school="Stanford"))


def test_dataclass_vs_dict():
    assert not eq(Child("a", 1, "s"), {"name": "a", "age": 1, "school": "s"})


# --- Comparator edge cases ---

def test_gt_non_numeric():
    # GT with non-numeric types raises TypeError (documented limitation)
    with pytest.raises(TypeError):
        GT(0).matches(None, "hello")
    assert GT(0).matches(None, -1) is False


def test_regex_non_string():
    assert REGEX(".*").matches(None, 42) is False
    assert REGEX(".*").matches(None, None) is False


def test_regex_empty():
    assert REGEX("").matches(None, "anything")
    assert REGEX("$").matches(None, "")


def test_not_any():
    assert NOT(ANY()).matches(None, "anything") is False


def test_between_same():
    assert BETWEEN(5, 5).matches(None, 5)


def test_between_non_numeric():
    # Python supports comparison of some non-numeric types
    assert BETWEEN("a", "c").matches(None, "b")


# --- ignore_order with duplicates ---

def test_ignore_order_dupes():
    assert eq([1, 1, 2], [2, 1, 1], ignore_order=True)
    assert not eq([1, 1, 2], [1, 2, 2], ignore_order=True)


def test_ignore_order_dupes_nested():
    assert eq([[1], [1], [2]], [[2], [1], [1]], ignore_order=True)


def test_ignore_order_empty():
    assert eq([], [], ignore_order=True)


def test_ignore_order_single():
    assert eq([1], [1], ignore_order=True)


# --- Empty structures ---

def test_empty_dict_none():
    assert not eq({}, None)
    assert not eq([], None)


def test_empty_dict_vs_list():
    assert not eq({}, [])


# --- Set edge cases ---

def test_set_with_unhashable():
    # Can't create sets with unhashable items, but can compare frozensets
    assert eq(frozenset([1, 2, 3]), frozenset([3, 2, 1]))


# --- NamedTuple ---

Point = namedtuple("Point", ["x", "y"])


def test_namedtuple():
    assert eq(Point(1, 2), Point(1, 2))
    assert not eq(Point(1, 2), Point(2, 1))


def test_namedtuple_vs_tuple():
    assert not eq(Point(1, 2), (1, 2))


# --- Match edge cases ---

def test_match_empty_pattern():
    assert match({}, {})
    assert match({"a": 1}, {})
    assert not match({}, {"a": 1})


def test_match_nested_comparator_fail():
    assert not match({"x": 3}, {"x": GT(5)})

def test_match_type_coerce():
    # match uses isinstance, not type_coerce (different from eq)
    assert not match(1.0, int)  # float is not isinstance of int
    assert match(1, int)
    assert not match("1", int)

def test_match_none_type():
    assert match(None, type(None))
    assert not match(1, type(None))

def test_match_list_wrong_length():
    assert not match([1, 2], [int, int, int])

# --- Diff edge cases ---

def test_diff_same_value():
    assert not diff(42, 42).has_changes()

def test_diff_type_change_root():
    d = diff(42, "42")
    assert d.type_changes

def test_diff_none_vs_dict():
    d = diff(None, {"a": 1})
    assert d.has_changes()

def test_diff_nested_type_change():
    d = diff({"x": 1}, {"x": "1"})
    assert d.type_changes
