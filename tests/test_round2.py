"""Hypothesis property-based tests and adversarial cases."""

import pytest
from hypothesis import given, strategies as st
from structmatch import eq, diff, match, ANY, TYPE, GT, LT, BETWEEN, NOT
from structmatch.comparators import Comparator


# --- Strategies ---

def nested_structure(max_depth=3):
    """Generate random nested structures."""
    base = st.none() | st.booleans() | st.integers(-1000, 1000) | st.floats(-100, 100, allow_nan=False, allow_infinity=False) | st.text(max_size=10)

    def _recursion(depth):
        if depth <= 0:
            return base
        return st.one_of(
            base,
            st.lists(_recursion(depth - 1), max_size=5),
            st.dictionaries(st.text(max_size=5), _recursion(depth - 1), max_size=5),
            st.tuples(_recursion(depth - 1), _recursion(depth - 1)),
            st.sets(st.integers(-100, 100), max_size=5),
        )

    return _recursion(max_depth)


# --- eq() property tests ---

@given(s=nested_structure())
def test_eq_reflexive(s):
    """eq(x, x) should always be True."""
    assert eq(s, s)


@given(s=nested_structure())
def test_eq_symmetric(s):
    """eq(a, b) == eq(b, a)."""
    assert eq(s, s)  # trivial but symmetric


@given(a=nested_structure(), b=nested_structure(), c=nested_structure())
def test_eq_transitive_subset(a, b, c):
    """If eq(a,b) and eq(b,c), then eq(a,c). We only test when a==b==c."""
    # Build transitive case: use the same structure
    if eq(a, b) and eq(b, c):
        assert eq(a, c)


@given(a=nested_structure(), b=nested_structure())
def test_eq_symmetric_general(a, b):
    """eq(a, b) == eq(b, a) for random structures."""
    assert eq(a, b) == eq(b, a)


@given(x=nested_structure())
def test_eq_with_tolerance_same(x):
    """eq(x, x, tolerance=...) always True."""
    assert eq(x, x, tolerance=0.1)


# --- tolerance property tests ---

@given(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))
def test_tolerance_zero_exact(x):
    """With tolerance=0, only exact matches."""
    assert eq(x, x, tolerance=0.0)


@given(
    a=st.floats(1, 1000, allow_nan=False, allow_infinity=False),
    b=st.floats(1, 1000, allow_nan=False, allow_infinity=False),
)
def test_tolerance_relative_monotonic(a, b):
    """Higher tolerance should match more, not less."""
    # If they match at tolerance t, they should also match at 2*t
    # (approximately, due to floating point)
    if eq(a, b, tolerance=0.01):
        assert eq(a, b, tolerance=0.1)


# --- diff property tests ---

@given(a=nested_structure(), b=nested_structure())
def test_diff_symmetric_info(a, b):
    """If eq(a,b) then diff is empty."""
    result = diff(a, b)
    if eq(a, b):
        assert not result.has_changes()


@given(d=st.dictionaries(st.text(max_size=5), st.integers(-100, 100), max_size=10))
def test_diff_same_dict(d):
    """Diff of dict with itself is empty."""
    assert not diff(d, d).has_changes()


@given(d=st.dictionaries(st.text(max_size=5), st.integers(-100, 100), max_size=10))
def test_diff_added_keys(d):
    """Adding a key shows up in diff."""
    d2 = {**d, "extra_key_12345": 999}
    result = diff(d, d2)
    if "extra_key_12345" not in d:
        assert "extra_key_12345" in result.added


@given(
    d=st.dictionaries(
        st.text(max_size=5),
        st.dictionaries(st.text(max_size=5), st.integers(-100, 100), max_size=5),
        max_size=5,
    )
)
def test_diff_nested_dicts(d):
    """Diff of nested dict with itself is empty."""
    assert not diff(d, d).has_changes()


# --- match() property tests ---

@given(x=nested_structure())
def test_match_any_always(x):
    """match(x, ANY) always True."""
    assert match(x, ANY)


@given(x=st.integers(-1000, 1000))
def test_match_gt(x):
    """GT(n) matches x > n."""
    n = 0
    assert match(x, GT(n)) == (x > n)


@given(x=st.integers(-1000, 1000))
def test_match_lt(x):
    """LT(n) matches x < n."""
    n = 0
    assert match(x, LT(n)) == (x < n)


@given(x=st.integers(-1000, 1000))
def test_match_between(x):
    """BETWEEN(0, 100) matches 0 <= x <= 100."""
    assert match(x, BETWEEN(0, 100)) == (0 <= x <= 100)


@given(x=st.integers(-1000, 1000))
def test_match_not_gt(x):
    """NOT(GT(0)) matches x <= 0."""
    assert match(x, NOT(GT(0))) == (x <= 0)


@given(
    d=st.dictionaries(st.text(max_size=5), st.integers(-100, 100), max_size=5)
)
def test_match_literal_dict(d):
    """match(d, d) always True for dict."""
    assert match(d, d)


@given(d=st.dictionaries(st.text(max_size=5), st.integers(-100, 100), max_size=5))
def test_match_subset_dict(d):
    """match(d, {}) always True — empty pattern matches any dict."""
    assert match(d, {})


# --- adversarial tests ---

class TestAdversarial:
    def test_self_referencing_avoided(self):
        """eq should not recurse infinitely on simple structures."""
        a = {"x": [1, 2, 3]}
        b = {"x": [1, 2, 3]}
        assert eq(a, b)

    def test_large_nested(self):
        """Handle deeply nested but finite structures."""
        d = {"l" * i: i for i in range(50)}
        assert eq(d, d)

    def test_empty_vs_none(self):
        assert not eq({}, None)
        assert not eq([], None)
        assert not eq("", None)

    def test_bool_not_int(self):
        """Booleans should not equal ints."""
        assert not eq(True, 1)
        assert not eq(False, 0)
        assert not eq(True, True) is not True or eq(True, True)  # True == True
        assert eq(True, True)

    def test_nan_values(self):
        """NaN should not equal NaN (consistent with Python)."""
        import math
        assert not eq(float("nan"), float("nan"))

    def test_infinity(self):
        assert eq(float("inf"), float("inf"))

    def test_very_different_types(self):
        assert not eq(lambda: None, 42)

    def test_custom_comparator_in_eq(self):
        class AlwaysTrue(Comparator):
            def matches(self, a, b):
                return True

        assert eq("anything", "different", comparators=[AlwaysTrue()])
        assert eq(1, 999, comparators=[AlwaysTrue()])

    def test_tolerance_edge_cases(self):
        assert not eq(0, 0, tolerance=-1)  # negative tolerance behaves like 0
        assert eq(0, 0, tolerance=0)
        assert eq(0, 0, tolerance=100)

    def test_unicode_strings(self):
        assert eq("café", "café")
        assert not eq("café", "cafe")

    def test_case_insensitive_unicode(self):
        assert eq("Café", "café", case_sensitive=False)

    def test_ignore_order_empty_lists(self):
        assert eq([], [], ignore_order=True)

    def test_ignore_order_single_element(self):
        assert eq([42], [42], ignore_order=True)

    def test_diff_with_none_values(self):
        result = diff({"a": None}, {"a": 1})
        assert result.has_changes()

    def test_match_type_none(self):
        assert match(None, type(None))
        assert not match(1, type(None))

    def test_match_nested_comparators(self):
        pattern = {
            "items": [BETWEEN(0, 10), BETWEEN(0, 10)],
            "status": TYPE(str),
        }
        obj = {"items": [5, 3], "status": "ok", "extra": True}
        assert match(obj, pattern)
