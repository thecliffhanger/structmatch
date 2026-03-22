"""Tests for diff engine."""

import pytest
from dataclasses import dataclass
from structmatch import diff, DiffResult


class TestDiffResult:
    def test_empty(self):
        d = DiffResult()
        assert not d.has_changes()
        assert not d

    def test_with_added(self):
        d = DiffResult(added={"x": 1})
        assert d.has_changes()
        assert d

    def test_equality(self):
        d1 = DiffResult(added={"x": 1}, changed={"y": (1, 2)})
        d2 = DiffResult(added={"x": 1}, changed={"y": (1, 2)})
        assert d1 == d2

    def test_repr(self):
        d = DiffResult(added={"x": 1})
        assert "added" in repr(d)
        assert "DiffResult" in repr(d)

    def test_inequality(self):
        d1 = DiffResult(added={"x": 1})
        d2 = DiffResult(added={"y": 1})
        assert d1 != d2


class TestDiffDicts:
    def test_empty_dicts(self):
        assert not diff({}, {})

    def test_identical(self):
        assert not diff({"a": 1, "b": "x"}, {"a": 1, "b": "x"})

    def test_added(self):
        result = diff({"a": 1}, {"a": 1, "b": 2})
        assert result.added == {"b": 2}

    def test_removed(self):
        result = diff({"a": 1, "b": 2}, {"a": 1})
        assert result.removed == {"b": 2}

    def test_changed(self):
        result = diff({"a": 1}, {"a": 2})
        assert result.changed == {"a": (1, 2)}

    def test_type_change(self):
        result = diff({"a": 42}, {"a": "42"})
        assert "a" in result.type_changes

    def test_nested_change(self):
        result = diff({"x": {"y": 1}}, {"x": {"y": 2}})
        assert any("y" in k for k in result.changed)

    def test_nested_added(self):
        result = diff({"x": {}}, {"x": {"y": 1}})
        assert any("y" in k for k in result.added)

    def test_deeply_nested(self):
        a = {"a": {"b": {"c": {"d": 1}}}}
        b = {"a": {"b": {"c": {"d": 2}}}}
        result = diff(a, b)
        assert any("d" in k for k in result.changed)


class TestDiffLists:
    def test_identical_lists(self):
        assert not diff([1, 2, 3], [1, 2, 3])

    def test_list_item_changed(self):
        result = diff([1, 2, 3], [1, 5, 3])
        changes = [pc for pc in result.path_changes if pc["change"] == "changed"]
        assert len(changes) == 1
        assert changes[0]["from"] == 2
        assert changes[0]["to"] == 5

    def test_list_added(self):
        result = diff([1], [1, 2])
        added = [pc for pc in result.path_changes if pc["change"] == "added"]
        assert len(added) == 1

    def test_list_removed(self):
        result = diff([1, 2], [1])
        removed = [pc for pc in result.path_changes if pc["change"] == "removed"]
        assert len(removed) == 1

    def test_empty_lists(self):
        assert not diff([], [])

    def test_list_of_dicts(self):
        a = [{"x": 1}]
        b = [{"x": 2}]
        result = diff(a, b)
        # Both have 1 element but they differ
        assert result.has_changes()

    def test_ignore_order(self):
        result = diff([1, 2, 3], [3, 2, 1], ignore_order=True)
        assert not result.has_changes()

    def test_ignore_order_different_length(self):
        result = diff([1, 2], [1, 2, 3], ignore_order=True)
        assert result.has_changes()


class TestDiffTolerance:
    def test_within_tolerance(self):
        result = diff(1.0, 1.0001, tolerance=0.001)
        assert not result.has_changes()

    def test_outside_tolerance(self):
        result = diff(1.0, 1.1, tolerance=0.001)
        assert result.has_changes()

    def test_nested_tolerance(self):
        result = diff({"x": 1.0}, {"x": 1.01}, tolerance=0.1)
        assert not result.has_changes()


class TestDiffWithIgnoreKeys:
    def test_ignore_keys_flat(self):
        result = diff({"a": 1, "id": 5}, {"a": 1, "id": 99}, ignore_keys=["id"])
        assert not result.has_changes()

    def test_ignore_keys_nested(self):
        result = diff(
            {"data": {"x": 1, "ts": "a"}},
            {"data": {"x": 1, "ts": "b"}},
            ignore_keys=["ts"],
        )
        assert not result.has_changes()


class TestDiffSets:
    def test_identical_sets(self):
        assert not diff({1, 2, 3}, {3, 2, 1})

    def test_different_sets(self):
        result = diff({1, 2}, {2, 3})
        assert result.has_changes()

    def test_empty_sets(self):
        assert not diff(set(), set())


class TestDiffSpecial:
    def test_none_values(self):
        result = diff(None, None)
        assert not result.has_changes()

    def test_none_vs_value(self):
        result = diff(None, 42)
        assert result.has_changes()

    def test_dataclass(self):
        @dataclass
        class Point:
            x: int
            y: int

        result = diff(Point(1, 2), Point(1, 3))
        assert result.has_changes()

    def test_mixed_types_root(self):
        result = diff(42, "42")
        assert result.has_changes()
