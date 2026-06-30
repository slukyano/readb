"""Unit tests for the type lattice and type-name normalization in okdb.schema."""

from __future__ import annotations

import datetime as dt

import pytest

from okdb import schema as s


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Big %// Table", "bigtable"),
        ("BigQuery Table", "bigquerytable"),
        ("3D Model", "_3dmodel"),
        ("%%%", ""),
        ("   ", ""),
        ("already_ok", "already_ok"),
        ("Mixed-CASE 99", "mixedcase99"),
        ("99bottles", "_99bottles"),
    ],
)
def test_normalize_type(raw: str, expected: str) -> None:
    assert s.normalize_type(raw) == expected


def _ddl(values: list[object]) -> str:
    return s.render_ddl(s.infer_type(values))


def test_all_null_defaults_to_varchar() -> None:
    assert _ddl([None, None]) == "VARCHAR"


def test_homogeneous_scalars() -> None:
    assert _ddl(["a", "b", None]) == "VARCHAR"
    assert _ddl([1, 2, 3]) == "BIGINT"
    assert _ddl([1.0, 2.5]) == "DOUBLE"
    assert _ddl([True, False]) == "BOOLEAN"


def test_int_float_widens_to_double() -> None:
    assert _ddl([1, 2.5]) == "DOUBLE"
    assert _ddl([2.5, 1]) == "DOUBLE"


def test_incompatible_scalars_fall_to_json() -> None:
    assert _ddl(["x", 1]) == "JSON"
    assert _ddl([True, 1]) == "JSON"  # bool and int are distinct kinds


def test_scalar_and_list_promote_to_list() -> None:
    assert _ddl([5, [5, 6]]) == "BIGINT[]"
    assert _ddl([[1, 2], 3]) == "BIGINT[]"


def test_list_of_incompatible_elements_is_list_of_json() -> None:
    # The brief's worked example: "1, 2, 3" (str) vs [1, 2, 3] (ints).
    assert _ddl(["1, 2, 3", [1, 2, 3]]) == "JSON[]"


def test_consistent_maps_become_struct() -> None:
    ddl = _ddl([{"rows": 10, "cols": 5}, {"rows": 20, "cols": 8}])
    assert ddl == 'STRUCT("cols" BIGINT, "rows" BIGINT)'  # fields are sorted by name


def test_inconsistent_maps_fall_to_json() -> None:
    assert _ddl([{"a": 1}, {"b": 2}]) == "JSON"


def test_nested_list_of_structs() -> None:
    ddl = _ddl([[{"x": 1}], [{"x": 2}]])
    assert ddl == 'STRUCT("x" BIGINT)[]'


def test_naive_datetime_is_timestamp_aware_is_json() -> None:
    assert _ddl([dt.datetime(2026, 6, 29, 12, 0, 0)]) == "TIMESTAMP"
    assert _ddl([dt.date(2026, 6, 29)]) == "DATE"
    aware = dt.datetime(2026, 6, 29, 12, 0, 0, tzinfo=dt.UTC)
    assert _ddl([aware]) == "JSON"  # tz-aware routes to the JSON fallback (no pytz dep)


def test_tags_forcing_wraps_scalar_in_list() -> None:
    # as_list_type is what the loader applies to the reserved `tags` column.
    assert s.render_ddl(s.as_list_type(s.infer_type(["solo", "x"]))) == "VARCHAR[]"
    assert s.render_ddl(s.as_list_type(s.infer_type([None]))) == "VARCHAR[]"


def test_coerce_json_serializes_value() -> None:
    assert s.coerce("hello", s.JSON) == '"hello"'
    assert s.coerce({"a": 1}, s.JSON) == '{"a": 1}'
    assert s.coerce(None, s.JSON) is None


def test_coerce_list_promotes_scalar() -> None:
    list_of_bigint = s.LType(s.Kind.LIST, element=s.BIGINT)
    assert s.coerce(5, list_of_bigint) == [5]
    assert s.coerce([5, 6], list_of_bigint) == [5, 6]


def test_coerce_double_casts_int() -> None:
    assert s.coerce(1, s.DOUBLE) == 1.0
    assert isinstance(s.coerce(1, s.DOUBLE), float)
