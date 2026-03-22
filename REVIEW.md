# structmatch Code Review

## Summary

Solid, well-structured library. Code is clean, focused, and the API design is sensible. Found **1 bug** (fixed) and several documented limitations. All 256 tests pass.

## Bug Fixed

**Negative tolerance in `_within_tolerance`** (`utils.py:67`): When `tolerance < 0`, the code fell into the `tolerance <= 1` branch and computed `abs(a-b) <= negative_number * max(...)`, which is always False — making equal values compare as unequal. Fixed by treating `tolerance <= 0` as exact match (same as `0`).

## Known Limitations

| Issue | Impact | Severity |
|-------|--------|----------|
| **No circular reference detection** | `eq()`/`diff()` can infinite-loop on self-referencing objects | Medium |
| **No Unicode normalization** | NFC vs NFD strings (e.g. `"é"` vs `"e\u0301"`) compare as different | Low |
| **Comparators don't catch TypeError** | `GT(0).matches(None, "hello")` raises `TypeError` instead of returning `False` | Low |
| **`diff()` RecursionError on deep structures** | Works fine at ~200 levels but `eq()` handles 2000+ while `diff()` doesn't (due to extra call depth per frame) | Low |
| **`match()` ignores `type_coerce`** | `match(1.0, int)` returns `False` despite `type_coerce=True` — the option isn't passed through | Low |

## Code Quality

- **Clean architecture**: Clear separation between `core.py`, `diff.py`, `comparators.py`, `schema.py`, `options.py`, `utils.py`
- **Immutable options**: `MatchOptions` uses `frozenset` for `ignore_keys` and `__slots__` — good
- **No shared mutable state**: All functions are pure — thread-safe by design
- **Performance**: No obvious inefficiencies. `_filter_keys` creates a new dict each call, but that's the cost of immutability. `_as_multiset` is used correctly for order-independent comparison.

## Testing

- **Before**: 187 tests
- **After**: 256 tests (+69 new: 55 adversarial + 14 integration)
- Coverage areas added: circular refs, deep nesting, large collections, numeric edge cases, unicode, custom objects, dataclasses, real-world scenarios (API responses, DB rows, config validation, HTTP response matching, version diffing)

## Recommendations (non-blocking)

1. Add circular reference detection via a `seen` set of `id()`s — would prevent infinite recursion
2. Consider making comparators catch `TypeError` and return `False` for type-incompatible comparisons
3. Pass `type_coerce` through to `match()` for consistency with `eq()`
4. Add unicode normalization option (e.g. `normalize_unicode=True`)
5. Consider iterative (stack-based) diff implementation to avoid RecursionError on very deep structures
