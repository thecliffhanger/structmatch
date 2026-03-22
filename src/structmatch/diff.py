"""Deep diff engine."""

from __future__ import annotations
from .options import MatchOptions
from .utils import (
    _is_numeric,
    _within_tolerance,
    _compare_strings,
    _filter_keys,
    _is_dataclass_like,
    _get_fields,
)


class DiffResult:
    """Result of a deep diff between two structures."""

    __slots__ = ("added", "removed", "changed", "type_changes", "path_changes")

    def __init__(
        self,
        added: dict | None = None,
        removed: dict | None = None,
        changed: dict | None = None,
        type_changes: dict | None = None,
        path_changes: list | None = None,
    ):
        self.added = added if added is not None else {}
        self.removed = removed if removed is not None else {}
        self.changed = changed if changed is not None else {}
        self.type_changes = type_changes if type_changes is not None else {}
        self.path_changes = path_changes if path_changes is not None else []

    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed or self.type_changes or self.path_changes)

    def __bool__(self) -> bool:
        return self.has_changes()

    def __repr__(self) -> str:
        parts = []
        if self.added:
            parts.append(f"added={self.added}")
        if self.removed:
            parts.append(f"removed={self.removed}")
        if self.changed:
            parts.append(f"changed={self.changed}")
        if self.type_changes:
            parts.append(f"type_changes={self.type_changes}")
        if self.path_changes:
            parts.append(f"path_changes={self.path_changes}")
        return f"DiffResult({', '.join(parts)})"

    def __eq__(self, other):
        if not isinstance(other, DiffResult):
            return NotImplemented
        return (
            self.added == other.added
            and self.removed == other.removed
            and self.changed == other.changed
            and self.type_changes == other.type_changes
        )


def _diff_dicts(a: dict, b: dict, opts: MatchOptions, path: str = "") -> DiffResult:
    added = {}
    removed = {}
    changed = {}
    type_changes = {}
    path_changes = []

    a_filtered = _filter_keys(a, opts.ignore_keys)
    b_filtered = _filter_keys(b, opts.ignore_keys)

    all_keys = set(a_filtered) | set(b_filtered)
    for key in all_keys:
        key_path = f"{path}.{key}" if path else key
        if key not in a_filtered:
            added[key] = b_filtered[key]
        elif key not in b_filtered:
            removed[key] = a_filtered[key]
        else:
            va = a_filtered[key]
            vb = b_filtered[key]
            child = _diff_values(va, vb, opts, key_path)
            if child is None:
                continue
            if isinstance(child, dict):
                if "sub_diff" in child:
                    sub = child["sub_diff"]
                    # Merge sub_diff into current
                    added.update({f"{key}.{k}" if k in added else k: v for k, v in sub.added.items()})
                    removed.update({f"{key}.{k}" if k in removed else k: v for k, v in sub.removed.items()})
                    changed.update({f"{key}.{k}" if k in changed else k: v for k, v in sub.changed.items()})
                    type_changes.update({f"{key}.{k}" if k in type_changes else k: v for k, v in sub.type_changes.items()})
                    path_changes.extend(sub.path_changes)
                elif "type_change" in child:
                    type_changes[key] = child["type_change"]
                elif "set_diff" in child:
                    changed[key] = (va, vb)
            elif isinstance(child, tuple):
                changed[key] = child

    return DiffResult(added=added, removed=removed, changed=changed, type_changes=type_changes, path_changes=path_changes)


def _diff_sequences(a, b, opts: MatchOptions, path: str = "") -> DiffResult:
    if opts.ignore_order:
        # If same elements (multiset), no changes
        from .utils import _as_multiset
        if _as_multiset(a) == _as_multiset(b):
            return DiffResult()

    path_changes = []
    max_len = max(len(a), len(b))
    for i in range(max_len):
        idx_path = f"{path}[{i}]"
        if i >= len(a):
            path_changes.append({"path": idx_path, "change": "added", "value": b[i]})
        elif i >= len(b):
            path_changes.append({"path": idx_path, "change": "removed", "value": a[i]})
        else:
            child = _diff_values(a[i], b[i], opts, idx_path)
            if child is not None:
                if isinstance(child, dict) and "type_change" in child:
                    path_changes.append({"path": idx_path, "change": "type_change", "from": child["type_change"][0], "to": child["type_change"][1]})
                elif isinstance(child, tuple):
                    path_changes.append({"path": idx_path, "change": "changed", "from": child[0], "to": child[1]})
                elif isinstance(child, dict) and "sub_diff" in child:
                    path_changes.append({"path": idx_path, "change": "sub_diff", "details": child["sub_diff"]})
                else:
                    path_changes.append({"path": idx_path, "change": "changed", "from": a[i], "to": b[i]})

    return DiffResult(path_changes=path_changes)


def _diff_values(va, vb, opts: MatchOptions, path: str = ""):
    """Returns None if equal, a tuple (old, new) if changed, or dict with type_change."""
    type_a = type(va)
    type_b = type(vb)

    if type_a != type_b:
        if opts.type_coerce and _is_numeric(va, vb) and _within_tolerance(va, vb, opts.tolerance):
            return None
        return {"type_change": (type_a, type_b)}

    if isinstance(va, dict):
        sub = _diff_dicts(va, vb, opts, path)
        if sub.has_changes():
            return {"sub_diff": sub}
        return None

    if isinstance(va, str):
        if not _compare_strings(va, vb, opts.case_sensitive):
            return (va, vb)
        return None

    if _is_numeric(va, vb):
        if _within_tolerance(va, vb, opts.tolerance):
            return None
        return (va, vb)

    if isinstance(va, (list, tuple)):
        sub = _diff_sequences(va, vb, opts, path)
        if sub.has_changes():
            return {"sub_diff": sub}
        return None

    if isinstance(va, set):
        extra_a = va - vb
        extra_b = vb - va
        if extra_a or extra_b:
            return {"set_diff": {"removed": extra_a, "added": extra_b}}
        return None

    if _is_dataclass_like(va):
        fa = _get_fields(va)
        fb = _get_fields(vb)
        return _diff_dicts(fa, fb, opts, path)

    if va == vb:
        return None
    return (va, vb)


def diff(a, b, **opts) -> DiffResult:
    """Compute a deep diff between two structures."""
    options = MatchOptions(**opts)
    result = _diff_values(a, b, options)
    if result is None:
        return DiffResult()
    if isinstance(result, dict):
        if "sub_diff" in result:
            return result["sub_diff"]
        if "type_change" in result:
            return DiffResult(type_changes={"root": result["type_change"]})
        if "set_diff" in result:
            return DiffResult(
                added={"root_set_added": result["set_diff"]["added"]},
                removed={"root_set_removed": result["set_diff"]["removed"]},
            )
        return DiffResult(changed={"root": (a, b)})
    return DiffResult(changed={"root": result})
