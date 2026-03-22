"""Tests for MatchOptions."""

import pytest
from structmatch.options import MatchOptions
from structmatch import eq


class TestMatchOptions:
    def test_defaults(self):
        opts = MatchOptions()
        assert opts.tolerance == 0.0
        assert opts.ignore_order is False
        assert opts.ignore_keys == frozenset()
        assert opts.case_sensitive is True
        assert opts.type_coerce is False
        assert opts.comparators == []

    def test_custom_values(self):
        opts = MatchOptions(
            tolerance=0.01,
            ignore_order=True,
            ignore_keys=["id"],
            case_sensitive=False,
            type_coerce=True,
            comparators=[],
        )
        assert opts.tolerance == 0.01
        assert opts.ignore_order is True
        assert opts.ignore_keys == frozenset(["id"])
        assert opts.case_sensitive is False
        assert opts.type_coerce is True

    def test_update(self):
        opts = MatchOptions(tolerance=0.0)
        new_opts = opts.update(tolerance=0.01, ignore_order=True)
        assert opts.tolerance == 0.0
        assert new_opts.tolerance == 0.01
        assert new_opts.ignore_order is True

    def test_ignore_keys_immutable(self):
        opts = MatchOptions(ignore_keys=["a", "b"])
        assert "a" in opts.ignore_keys
        # frozenset
        with pytest.raises(AttributeError):
            opts.ignore_keys.add("c")

    def test_eq_with_options_obj(self):
        assert eq(1, 1, tolerance=0.0)
        assert not eq(1, 2, tolerance=0.0)
        assert eq(1.0, 1.001, tolerance=0.01)
