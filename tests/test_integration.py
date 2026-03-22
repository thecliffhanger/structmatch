"""Integration tests for structmatch — real-world scenarios."""

import pytest
from structmatch import (
    eq, diff, match, Schema, SchemaError,
    GT, LT, GE, LE, BETWEEN, REGEX, TYPE, ANY, MatchOptions,
)


# --- API response comparison ---

def test_api_response_eq():
    resp1 = {
        "status": 200,
        "data": {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ],
            "total": 2,
        },
        "pagination": {"page": 1, "per_page": 10},
    }
    resp2 = {
        "status": 200,
        "data": {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ],
            "total": 2,
        },
        "pagination": {"page": 1, "per_page": 10},
    }
    assert eq(resp1, resp2)


def test_api_response_diff():
    old = {"status": 200, "data": {"count": 5}, "timestamp": "2024-01-01"}
    new = {"status": 200, "data": {"count": 8}, "timestamp": "2024-01-02"}
    d = diff(old, new)
    assert d.changed
    assert d.changed.get("timestamp") == ("2024-01-01", "2024-01-02")


def test_api_response_ignore_keys():
    resp1 = {"id": "uuid-1", "data": "hello", "timestamp": 1000}
    resp2 = {"id": "uuid-2", "data": "hello", "timestamp": 2000}
    assert eq(resp1, resp2, ignore_keys=["id", "timestamp"])


# --- Database row comparison ---

def test_db_rows_eq():
    row1 = {"id": 1, "name": "Alice", "score": 95.0, "active": True}
    row2 = {"id": 1, "name": "Alice", "score": 95.0, "active": True}
    assert eq(row1, row2)


def test_db_rows_tolerance():
    row1 = {"id": 1, "price": 10.001}
    row2 = {"id": 1, "price": 10.002}
    assert not eq(row1, row2)
    assert eq(row1, row2, tolerance=0.01)


def test_db_rows_diff():
    old = {"id": 1, "name": "Alice", "score": 90}
    new = {"id": 1, "name": "Alice", "score": 95}
    d = diff(old, new)
    assert d.changed


# --- Schema validation: complex nested config ---

def test_config_schema():
    schema = Schema({
        "app_name": str,
        "version": str,
        "database": {
            "host": str,
            "port": int,
            "credentials": {"username": str, "password": str},
        },
        "features": [str],
        "logging": {
            "level": str,
            "enabled": bool,
        },
    })

    valid = {
        "app_name": "MyApp",
        "version": "1.0.0",
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {"username": "admin", "password": "secret"},
        },
        "features": ["auth", "api", "dashboard"],
        "logging": {"level": "INFO", "enabled": True},
    }
    assert schema.validate(valid)

    invalid = {
        "app_name": "MyApp",
        "version": "1.0.0",
        "database": {
            "host": "localhost",
            "port": "5432",  # wrong type
            "credentials": {"username": "admin"},  # missing password
        },
        "features": "auth",  # should be list
    }
    with pytest.raises(SchemaError):
        schema.validate(invalid)


def test_schema_with_comparators():
    schema = Schema({
        "name": str,
        "age": GT(0),
        "score": BETWEEN(0, 100),
        "email": REGEX(r"[^@]+@[^@]+\.[^@]+"),
    })
    assert schema.validate({"name": "Alice", "age": 30, "score": 85, "email": "a@b.com"})
    assert not schema.is_valid({"name": "Alice", "age": -1, "score": 85, "email": "a@b.com"})
    assert not schema.is_valid({"name": "Alice", "age": 30, "score": 150, "email": "a@b.com"})
    assert not schema.is_valid({"name": "Alice", "age": 30, "score": 85, "email": "not-an-email"})


# --- Pattern matching for HTTP response validation ---

def test_http_response_match():
    response = {
        "status_code": 200,
        "body": {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "user"},
            ],
        },
        "headers": {"content-type": "application/json"},
    }

    pattern = {
        "status_code": GE(200),
        "body": {
            "users": [
                {"id": int, "name": str, "role": str},
                {"id": int, "name": str, "role": str},
            ],
        },
        "headers": ANY,
    }
    assert match(response, pattern)


def test_http_response_match_fail():
    response = {"status_code": 404, "error": "Not found"}
    assert not match(response, {"status_code": GE(200), "body": dict})


# --- Diff for tracking changes between versions ---

def test_version_diff():
    v1 = {
        "name": "MyApp",
        "version": "1.0",
        "config": {"debug": False, "port": 8080},
        "dependencies": ["requests", "flask"],
    }
    v2 = {
        "name": "MyApp",
        "version": "2.0",
        "config": {"debug": True, "port": 8080, "workers": 4},
        "dependencies": ["requests", "flask", "redis"],
    }
    d = diff(v1, v2)
    assert d.has_changes()
    assert d.changed.get("version") == ("1.0", "2.0")
    # config is flattened: debug and workers appear at root level
    assert d.changed.get("debug") or d.added.get("workers") or d.path_changes
    assert d.path_changes or d.added  # redis added


def test_version_diff_with_ignore():
    v1 = {"version": "1.0", "hash": "abc123", "data": [1, 2, 3]}
    v2 = {"version": "2.0", "hash": "def456", "data": [1, 2, 3]}
    d = diff(v1, v2, ignore_keys=["version", "hash"])
    assert not d.has_changes()


# --- MatchOptions ---

def test_match_options_reuse():
    opts = MatchOptions(tolerance=0.1, ignore_keys={"ts"}, case_sensitive=False)
    assert eq({"a": 1.01}, {"a": 1.02}, tolerance=opts.tolerance)
    assert eq("Hello", "hello", case_sensitive=opts.case_sensitive)


# --- Mixed real-world: comparing paginated results ---

def test_paginated_results():
    page1 = {"items": [{"id": i} for i in range(10)], "next_cursor": "abc"}
    page2 = {"items": [{"id": i} for i in range(10)], "next_cursor": "def"}
    assert eq(page1, page2, ignore_keys=["next_cursor"])


def test_order_independent_user_list():
    users1 = [{"id": 3, "name": "C"}, {"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    users2 = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "C"}]
    assert eq(users1, users2, ignore_order=True)
    assert not eq(users1, users2, ignore_order=False)
