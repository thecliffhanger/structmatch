"""Tests for core functions: eq(), diff(), match()."""

import pytest
from dataclasses import dataclass
from typing import NamedTuple
from structmatch import eq, diff, match, ANY, TYPE, GT, LT, BETWEEN, NOT, REGEX, GE, LE


# --- eq() tests ---

class TestEqBasics:
    def test_none(self):
        assert eq(None, None)

    def test_none_vs_value(self):
        assert not eq(None, 1)

    def test_bools(self):
        assert eq(True, True)
        assert eq(False, False)
        assert not eq(True, False)

    def test_bool_vs_int(self):
        assert not eq(True, 1)

    def test_ints(self):
        assert eq(1, 1)
        assert not eq(1, 2)

    def test_floats(self):
        assert eq(1.0, 1.0)
        assert not eq(1.0, 1.1)

    def test_strings(self):
        assert eq("hello", "hello")
        assert not eq("hello", "world")

    def test_empty_string(self):
        assert eq("", "")

    def test_lists(self):
        assert eq([1, 2, 3], [1, 2, 3])
        assert not eq([1, 2], [1, 2, 3])

    def test_tuples(self):
        assert eq((1, 2), (1, 2))
        assert not eq((1,), (1, 2))

    def test_list_vs_tuple(self):
        assert not eq([1, 2], (1, 2))

    def test_sets(self):
        assert eq({1, 2, 3}, {3, 2, 1})
        assert not eq({1, 2}, {1, 2, 3})

    def test_empty_containers(self):
        assert eq([], [])
        assert eq({}, {})
        assert eq(set(), set())
        assert eq((), ())


class TestEqNested:
    def test_nested_dicts(self):
        assert eq({"a": {"b": 1}}, {"a": {"b": 1}})
        assert not eq({"a": {"b": 1}}, {"a": {"b": 2}})

    def test_nested_lists(self):
        assert eq([[1, 2], [3]], [[1, 2], [3]])
        assert not eq([[1, 2], [3]], [[1], [3]])

    def test_deeply_nested(self):
        a = {"a": [{"b": {"c": [1, 2, {"d": 3}]}}, 4]}
        b = {"a": [{"b": {"c": [1, 2, {"d": 3}]}}, 4]}
        assert eq(a, b)

    def test_list_of_dicts(self):
        assert eq([{"a": 1}, {"b": 2}], [{"a": 1}, {"b": 2}])
        assert not eq([{"a": 1}], [{"a": 2}])


class TestEqTolerance:
    def test_exact(self):
        assert eq(1.0, 1.0, tolerance=0.0)

    def test_close_relative(self):
        assert eq(100.0, 100.5, tolerance=0.01)
        assert not eq(100.0, 101.0, tolerance=0.001)

    def test_close_absolute(self):
        assert eq(1.0, 2.5, tolerance=2.0)
        assert not eq(1.0, 5.0, tolerance=2.0)

    def test_tolerance_nested(self):
        assert eq([1.0, 2.0], [1.001, 1.999], tolerance=0.01)

    def test_tolerance_in_dict(self):
        assert eq({"x": 1.0}, {"x": 1.0001}, tolerance=0.001)

    def test_tolerance_zero(self):
        assert not eq(1.0, 1.0001, tolerance=0.0)

    def test_pi_approx(self):
        assert eq(3.14159, 3.14160, tolerance=0.001)


class TestEqIgnoreOrder:
    def test_ignore_order_list(self):
        assert eq([1, 2, 3], [3, 2, 1], ignore_order=True)

    def test_ignore_order_with_dupes(self):
        assert eq([1, 1, 2], [2, 1, 1], ignore_order=True)
        assert not eq([1, 1, 2], [1, 2, 2], ignore_order=True)

    def test_ignore_order_nested(self):
        a = [{"x": 1}, {"y": 2}]
        b = [{"y": 2}, {"x": 1}]
        assert eq(a, b, ignore_order=True)

    def test_ignore_order_false(self):
        assert not eq([1, 2], [2, 1], ignore_order=False)


class TestEqIgnoreKeys:
    def test_ignore_single_key(self):
        assert eq({"a": 1, "id": 999}, {"a": 1, "id": 1}, ignore_keys=["id"])

    def test_ignore_multiple_keys(self):
        assert eq(
            {"a": 1, "ts": "now", "id": 5},
            {"a": 1, "ts": "later", "id": 10},
            ignore_keys=["ts", "id"],
        )

    def test_ignore_keys_nested(self):
        assert eq(
            {"data": {"x": 1, "id": 5}},
            {"data": {"x": 1, "id": 10}},
            ignore_keys=["id"],
        )


class TestCaseSensitivity:
    def test_case_sensitive_default(self):
        assert eq("Hello", "Hello")
        assert not eq("Hello", "hello")

    def test_case_insensitive(self):
        assert eq("Hello", "hello", case_sensitive=False)
        assert eq("HELLO", "hello", case_sensitive=False)

    def test_case_insensitive_nested(self):
        assert eq(["Foo", "Bar"], ["foo", "bar"], case_sensitive=False)


class TestTypeCoerce:
    def test_int_float(self):
        assert eq(1, 1.0, type_coerce=True)
        assert not eq(1, 1.0, type_coerce=False)

    def test_int_float_nested(self):
        assert eq({"x": 1}, {"x": 1.0}, type_coerce=True)


class TestEqDataclass:
    def test_dataclass(self):
        @dataclass
        class Point:
            x: int
            y: int

        assert eq(Point(1, 2), Point(1, 2))
        assert not eq(Point(1, 2), Point(1, 3))

    def test_nested_dataclass(self):
        @dataclass
        class Inner:
            val: int

        @dataclass
        class Outer:
            inner: Inner

        assert eq(Outer(Inner(1)), Outer(Inner(1)))
        assert not eq(Outer(Inner(1)), Outer(Inner(2)))


class TestEqNamedTuple:
    def test_named_tuple(self):
        class Point(NamedTuple):
            x: int
            y: int

        assert eq(Point(1, 2), Point(1, 2))
        assert not eq(Point(1, 2), Point(2, 2))


class TestEqCustomObject:
    def test_custom_object(self):
        class Obj:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        assert eq(Obj(1, 2), Obj(1, 2))
        assert not eq(Obj(1, 2), Obj(1, 3))


# --- match() tests ---

class TestMatchBasic:
    def test_any(self):
        assert match(42, ANY)
        assert match(None, ANY)
        assert match("hello", ANY)

    def test_type(self):
        assert match(42, int)
        assert match("hello", str)
        assert match([1], list)
        assert not match(42, str)

    def test_gt(self):
        assert match(5, GT(3))
        assert not match(2, GT(3))

    def test_lt(self):
        assert match(2, LT(5))
        assert not match(5, LT(2))

    def test_ge(self):
        assert match(3, GE(3))
        assert match(5, GE(3))
        assert not match(2, GE(3))

    def test_le(self):
        assert match(3, LE(3))
        assert match(2, LE(5))
        assert not match(5, LE(2))

    def test_between(self):
        assert match(5, BETWEEN(1, 10))
        assert match(1, BETWEEN(1, 10))
        assert match(10, BETWEEN(1, 10))
        assert not match(0, BETWEEN(1, 10))
        assert not match(11, BETWEEN(1, 10))

    def test_regex(self):
        assert match("hello123", REGEX(r"\d+"))
        assert match("test@email.com", REGEX(r"@"))
        assert not match("hello", REGEX(r"\d+"))

    def test_not(self):
        assert match(5, NOT(GT(10)))
        assert not match(15, NOT(GT(10)))

    def test_literal_pattern(self):
        assert match(42, 42)
        assert not match(42, 43)

    def test_dict_pattern(self):
        assert match({"x": 5}, {"x": 5})
        assert not match({"x": 5}, {"x": 6})

    def test_dict_pattern_with_comparator(self):
        assert match({"status": 200}, {"status": GT(199)})
        assert not match({"status": 100}, {"status": GT(199)})

    def test_nested_pattern(self):
        assert match(
            {"body": {"count": 5}},
            {"body": {"count": BETWEEN(1, 10)}},
        )

    def test_list_pattern(self):
        assert match([1, 2, 3], [1, 2, 3])
        assert not match([1, 2], [1, 2, 3])

    def test_match_extra_keys_ok(self):
        """match only checks pattern keys, extra keys in obj are ok."""
        assert match({"x": 1, "y": 2}, {"x": 1})

    def test_match_missing_key_fails(self):
        assert not match({"x": 1}, {"x": 1, "y": 2})


# --- diff() tests ---

class TestDiffBasics:
    def test_identical(self):
        result = diff({"a": 1}, {"a": 1})
        assert not result.has_changes()

    def test_scalar_root(self):
        result = diff(1, 2)
        assert result.has_changes()

    def test_added_key(self):
        result = diff({"a": 1}, {"a": 1, "b": 2})
        assert result.added == {"b": 2}
        assert not result.removed

    def test_removed_key(self):
        result = diff({"a": 1, "b": 2}, {"a": 1})
        assert result.removed == {"b": 2}
        assert not result.added

    def test_changed_value(self):
        result = diff({"a": 1}, {"a": 2})
        assert result.changed == {"a": (1, 2)}

    def test_type_change(self):
        result = diff({"a": 1}, {"a": "hello"})
        assert "a" in result.type_changes

    def test_multiple_changes(self):
        result = diff({"a": 1, "b": 2, "c": 3}, {"a": 1, "b": 20, "d": 4})
        assert result.changed == {"b": (2, 20)}
        assert result.removed == {"c": 3}
        assert result.added == {"d": 4}

    def test_nested_diff(self):
        result = diff({"a": {"b": 1}}, {"a": {"b": 2}})
        assert any("b" in k for k in result.changed)

    def test_list_diff(self):
        result = diff([1, 2, 3], [1, 5, 3])
        assert any(pc["change"] == "changed" for pc in result.path_changes)

    def test_list_added_item(self):
        result = diff([1, 2], [1, 2, 3])
        assert any(pc["change"] == "added" for pc in result.path_changes)

    def test_list_removed_item(self):
        result = diff([1, 2, 3], [1, 2])
        assert any(pc["change"] == "removed" for pc in result.path_changes)

    def test_set_diff(self):
        result = diff({1, 2}, {2, 3})
        assert result.has_changes()

    def test_diff_repr(self):
        result = diff({"a": 1}, {"a": 2})
        assert "DiffResult" in repr(result)

    def test_diff_bool(self):
        assert not diff(1, 1)
        assert diff(1, 2)

    def test_ignore_keys_in_diff(self):
        result = diff({"a": 1, "id": 5}, {"a": 1, "id": 10}, ignore_keys=["id"])
        assert not result.has_changes()

    def test_tolerance_in_diff(self):
        result = diff({"x": 1.0}, {"x": 1.001}, tolerance=0.01)
        assert not result.has_changes()
