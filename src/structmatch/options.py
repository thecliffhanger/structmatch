from __future__ import annotations


class MatchOptions:
    """Options controlling comparison behavior."""

    __slots__ = (
        "tolerance",
        "ignore_order",
        "ignore_keys",
        "case_sensitive",
        "type_coerce",
        "comparators",
    )

    def __init__(
        self,
        tolerance: float = 0.0,
        ignore_order: bool = False,
        ignore_keys: set[str] | None = None,
        case_sensitive: bool = True,
        type_coerce: bool = False,
        comparators: list | None = None,
    ):
        self.tolerance = tolerance
        self.ignore_order = ignore_order
        self.ignore_keys = frozenset(ignore_keys) if ignore_keys else frozenset()
        self.case_sensitive = case_sensitive
        self.type_coerce = type_coerce
        self.comparators = comparators or []

    def update(self, **kwargs) -> MatchOptions:
        """Return a new MatchOptions with updated fields."""
        d = {
            "tolerance": self.tolerance,
            "ignore_order": self.ignore_order,
            "ignore_keys": set(self.ignore_keys) if self.ignore_keys else None,
            "case_sensitive": self.case_sensitive,
            "type_coerce": self.type_coerce,
            "comparators": list(self.comparators),
        }
        d.update(kwargs)
        return MatchOptions(**d)
