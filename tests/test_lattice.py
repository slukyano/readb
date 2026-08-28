"""Unit tests for the type lattice and type-name normalization in readb.schema."""

from __future__ import annotations

import datetime as dt

import pytest

from readb import schema as s


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


def test_mixed_scalars_promote_to_text() -> None:
    """ADR 0008: two scalars meet at the narrowest type holding both, never at JSON."""
    assert _ddl(["x", 1]) == "VARCHAR"
    assert _ddl([True, 1]) == "VARCHAR"  # bool and int are distinct kinds; text holds each
    assert _ddl([dt.date(2026, 1, 1), "later"]) == "VARCHAR"
    assert _ddl([1, 2.5]) == "DOUBLE"  # the narrower widening still wins
    assert _ddl([dt.date(2026, 1, 1), dt.datetime(2026, 1, 1, 12, 0)]) == "TIMESTAMP"


def test_an_integer_outside_bigint_is_text() -> None:
    assert _ddl([2**62]) == "BIGINT"
    assert _ddl([2**63]) == "VARCHAR"
    assert _ddl([-(2**63) - 1]) == "VARCHAR"
    assert _ddl([1, 2**70]) == "VARCHAR"  # the whole column takes the type that holds it all


def test_a_promoted_value_is_rendered_canonically() -> None:
    """The parsed value's canonical form, not the file's bytes — `__raw` keeps those."""
    from readb.schema import VARCHAR, coerce

    assert coerce(True, VARCHAR) == "true"
    assert coerce(16, VARCHAR) == "16"
    assert coerce(1.5, VARCHAR) == "1.5"
    assert coerce(dt.date(2026, 1, 1), VARCHAR) == "2026-01-01"
    assert coerce(2**70, VARCHAR) == "1180591620717411303424"


def test_scalar_and_list_promote_to_list() -> None:
    assert _ddl([5, [5, 6]]) == "BIGINT[]"
    assert _ddl([[1, 2], 3]) == "BIGINT[]"


def test_list_of_mixed_elements_is_a_list_of_text() -> None:
    # The brief's worked example: "1, 2, 3" (str) vs [1, 2, 3] (ints). The comma-string is never
    # split — readb does not guess producer intent — it simply becomes a one-element list.
    assert _ddl(["1, 2, 3", [1, 2, 3]]) == "VARCHAR[]"


def test_consistent_maps_become_struct() -> None:
    ddl = _ddl([{"rows": 10, "cols": 5}, {"rows": 20, "cols": 8}])
    assert ddl == 'STRUCT("cols" BIGINT, "rows" BIGINT)'  # fields are sorted by name


def test_maps_unify_by_field_union() -> None:
    """ADR 0008: differing key sets widen the struct instead of collapsing it to JSON."""
    assert _ddl([{"a": 1}, {"b": 2}]) == 'STRUCT("a" BIGINT, "b" BIGINT)'
    assert _ddl([{"a": {"x": 1}}, {"a": {"y": 2}}]) == 'STRUCT("a" STRUCT("x" BIGINT, "y" BIGINT))'
    assert _ddl([{"a": 1}, {"a": "text"}]) == 'STRUCT("a" VARCHAR)'  # fields unify in turn


def test_a_map_column_with_no_keys_keeps_a_placeholder_field() -> None:
    assert _ddl([{}]) == 'STRUCT("__DUMMY" VARCHAR)'
    assert _ddl([{}, {"a": 1}]) == 'STRUCT("a" BIGINT)'  # one real key retires the placeholder


def test_a_map_beside_a_non_map_is_still_json() -> None:
    """JSON stays the top of the lattice, for values no narrower type can hold together."""
    assert _ddl([{"a": 1}, "plain"]) == "JSON"
    assert _ddl([{"a": 1}, [1, 2]]) == "JSON"


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


def test_pytz_canary_timestamptz_fetch_still_requires_pytz() -> None:
    """Revisit signal for the tz-aware -> JSON routing (see the schema module docstring).

    duckdb's Python client requires pytz to fetch ANY TIMESTAMPTZ value (verified 1.5.4).
    If this canary fails, a future duckdb has lifted the requirement: reconsider giving the
    lattice a native TIMESTAMPTZ node (tasks/tz-aware-datetime-handling.md). Skipped when
    pytz happens to be importable, since then the premise cannot be observed.
    """
    try:
        import pytz  # noqa: F401
    except ImportError:
        pass
    else:
        pytest.skip("pytz is importable here; the fetch failure cannot be observed")

    import duckdb

    con = duckdb.connect()
    try:
        with pytest.raises(duckdb.Error, match="pytz"):
            con.execute("SELECT TIMESTAMPTZ '2026-01-01 00:00:00+00'").fetchall()
    finally:
        con.close()


def test_int_and_float_meet_at_double_which_is_the_one_lossy_widening() -> None:
    """ADR 0008 keeps SQL's own numeric rule, so the rounding above 2^53 is documented, not a bug.

    DuckDB resolves BIGINT with DOUBLE to DOUBLE in a UNION, in arithmetic and in COALESCE, and
    rounds the same way. Making the commonest numeric shape into text to avoid it would cost
    every numeric comparison in the column.
    """
    from readb.schema import BIGINT, DOUBLE, coerce, unify

    assert _ddl([1, 2.5]) == "DOUBLE"
    assert unify(BIGINT, DOUBLE) == DOUBLE
    assert coerce(9007199254740993, DOUBLE) == 9007199254740992.0
