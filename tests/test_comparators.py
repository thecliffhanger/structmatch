"""Tests for comparators."""

import pytest
from structmatch.comparators import (
    Comparator, ANY, TYPE, GT, LT, GE, LE, BETWEEN, REGEX, NOT,
)


class TestComparatorBase:
    def test_abstract(self):
        with pytest.raises(TypeError):
            Comparator()

    def test_custom_comparator(self):
        class Even(Comparator):
            def matches(self, a, b):
                return b % 2 == 0

        e = Even()
        assert e.matches(None, 4)
        assert not e.matches(None, 3)
        assert e(None, 4)  # callable


class TestANY:
    def test_matches_anything(self):
        a = ANY()
        assert a.matches(1, None)
        assert a.matches("x", 42)
        assert a.matches({}, [])


class TestTYPE:
    def test_type_int(self):
        t = TYPE(int)
        assert t.matches(None, 42)
        assert not t.matches(None, "hello")

    def test_type_str(self):
        t = TYPE(str)
        assert t.matches(None, "hello")
        assert not t.matches(None, 42)

    def test_type_multiple(self):
        t = TYPE((int, float))
        assert t.matches(None, 42)
        assert t.matches(None, 3.14)
        assert not t.matches(None, "x")


class TestGT:
    def test_gt(self):
        g = GT(5)
        assert g.matches(None, 6)
        assert not g.matches(None, 5)
        assert not g.matches(None, 4)

    def test_gt_string(self):
        g = GT("b")
        assert g.matches(None, "c")


class TestLT:
    def test_lt(self):
        l = LT(5)
        assert l.matches(None, 4)
        assert not l.matches(None, 5)
        assert not l.matches(None, 6)


class TestGE:
    def test_ge(self):
        g = GE(5)
        assert g.matches(None, 5)
        assert g.matches(None, 6)
        assert not g.matches(None, 4)


class TestLE:
    def test_le(self):
        l = LE(5)
        assert l.matches(None, 5)
        assert l.matches(None, 4)
        assert not l.matches(None, 6)


class TestBETWEEN:
    def test_between(self):
        b = BETWEEN(1, 10)
        assert b.matches(None, 1)
        assert b.matches(None, 5)
        assert b.matches(None, 10)
        assert not b.matches(None, 0)
        assert not b.matches(None, 11)

    def test_between_reversed(self):
        b = BETWEEN(10, 1)
        assert b.matches(None, 5)

    def test_between_float(self):
        b = BETWEEN(0.0, 1.0)
        assert b.matches(None, 0.5)


class TestREGEX:
    def test_regex_search(self):
        r = REGEX(r"\d{3}")
        assert r.matches(None, "abc123def")

    def test_regex_full_match(self):
        r = REGEX(r"^\d{3}$")
        assert r.matches(None, "123")
        assert not r.matches(None, "abc123def")

    def test_regex_non_string(self):
        r = REGEX(r"\d+")
        assert not r.matches(None, 42)


class TestNOT:
    def test_not(self):
        n = NOT(GT(5))
        assert n.matches(None, 3)
        assert not n.matches(None, 10)

    def test_not_any(self):
        n = NOT(ANY())
        assert not n.matches(None, "anything")
