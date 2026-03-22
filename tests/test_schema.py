"""Tests for Schema validation."""

import pytest
from structmatch import Schema, SchemaError, BETWEEN, TYPE


class TestSchemaBasic:
    def test_simple_dict(self):
        s = Schema({"name": str, "age": int})
        assert s.validate({"name": "Alice", "age": 30})

    def test_missing_key(self):
        s = Schema({"name": str, "age": int})
        with pytest.raises(SchemaError) as exc_info:
            s.validate({"name": "Alice"})
        assert any("missing" in e["message"] for e in exc_info.value.errors)

    def test_wrong_type(self):
        s = Schema({"age": int})
        with pytest.raises(SchemaError) as exc_info:
            s.validate({"age": "30"})
        assert any("int" in e["message"] for e in exc_info.value.errors)

    def test_extra_keys_ok(self):
        s = Schema({"name": str})
        assert s.validate({"name": "Alice", "extra": 42})

    def test_none_type(self):
        s = Schema({"x": type(None)})
        assert s.validate({"x": None})
        with pytest.raises(SchemaError):
            s.validate({"x": 1})


class TestSchemaNested:
    def test_nested_dict(self):
        s = Schema({"user": {"name": str, "age": int}})
        assert s.validate({"user": {"name": "Alice", "age": 30}})

    def test_nested_wrong_type(self):
        s = Schema({"user": {"name": str}})
        with pytest.raises(SchemaError):
            s.validate({"user": {"name": 42}})

    def test_list_of_type(self):
        s = Schema({"tags": [str]})
        assert s.validate({"tags": ["a", "b", "c"]})

    def test_list_of_dicts(self):
        s = Schema({"items": [{"name": str, "price": float}]})
        assert s.validate({"items": [{"name": "Widget", "price": 9.99}]})

    def test_list_wrong_item_type(self):
        s = Schema({"items": [int]})
        with pytest.raises(SchemaError):
            s.validate({"items": [1, "two", 3]})


class TestSchemaTuple:
    def test_tuple_schema(self):
        s = Schema({"coords": (int, int)})
        assert s.validate({"coords": [1, 2]})

    def test_tuple_wrong_length(self):
        s = Schema({"coords": (int, int)})
        with pytest.raises(SchemaError):
            s.validate({"coords": [1, 2, 3]})

    def test_tuple_wrong_type(self):
        s = Schema({"coords": (int, int)})
        with pytest.raises(SchemaError):
            s.validate({"coords": ["x", "y"]})


class TestSchemaSet:
    def test_set_schema(self):
        s = Schema({"status": {1, 2, 3}})
        assert s.validate({"status": {1, 2, 3}})

    def test_set_wrong_value(self):
        s = Schema({"status": {1, 2, 3}})
        with pytest.raises(SchemaError):
            s.validate({"status": {4}})


class TestSchemaComparators:
    def test_comparator_in_schema(self):
        s = Schema({"score": BETWEEN(0, 100)})
        assert s.validate({"score": 50})
        with pytest.raises(SchemaError):
            s.validate({"score": 150})

    def test_type_in_schema(self):
        s = Schema({"value": TYPE((int, float))})
        assert s.validate({"value": 42})
        assert s.validate({"value": 3.14})
        with pytest.raises(SchemaError):
            s.validate({"value": "x"})


class TestSchemaIsInvalid:
    def test_is_valid_true(self):
        s = Schema({"x": int})
        assert s.is_valid({"x": 1})

    def test_is_valid_false(self):
        s = Schema({"x": int})
        assert not s.is_valid({"x": "bad"})


class TestSchemaError:
    def test_error_message(self):
        s = Schema({"name": str, "age": int})
        with pytest.raises(SchemaError) as exc_info:
            s.validate({"name": 42})
        msg = str(exc_info.value)
        assert "root" in msg


class TestSchemaIntFloatCoercion:
    def test_int_accepted_for_float(self):
        s = Schema({"price": float})
        assert s.validate({"price": 10})

    def test_float_accepted_for_int(self):
        s = Schema({"count": int})
        assert s.validate({"count": 10.0})

    def test_bool_rejected_for_int(self):
        s = Schema({"flag": int})
        with pytest.raises(SchemaError):
            s.validate({"flag": True})
