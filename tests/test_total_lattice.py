"""Every value shape has a type, and no single column can take a bundle down (ADR 0008).

Backlog task ``041``. Nine frontmatter shapes used to kill an entire load at the DDL step — an
error after parsing had already succeeded, so the promise that a bad file is logged and skipped
did not hold. These tests carry the shapes that used to be fatal, and the ladder that catches
whatever has not been thought of yet.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

import readb

# Each of these made `readb.open(...)` raise before this task, taking every query with it.
FATAL_SHAPES = {
    "empty_mapping": "flag: {}",
    "list_of_empty_mappings": "flag: [{}]",
    "nested_empty_mapping": "flag: {a: {}}",
    "tags_empty_mapping": "tags: {}",
    "colliding_keys": 'flag: {1: a, "1": b}',
    "empty_string_key": 'flag: {"": 1}',
    "huge_int": "flag: 99999999999999999999999999",
    "huge_int_in_list": "flag: [1, 99999999999999999999999999]",
    "negative_huge_int": "flag: -99999999999999999999999999",
}


@pytest.fixture
def shapes_bundle(tmp_path: Path) -> Path:
    for name, line in FATAL_SHAPES.items():
        (tmp_path / f"{name}.md").write_text(
            f"---\ntype: Shape\ntitle: {name}\n{line}\n---\nbody\n", encoding="utf-8"
        )
    (tmp_path / "healthy.md").write_text(
        "---\ntype: Shape\ntitle: healthy\n---\nbody\n", encoding="utf-8"
    )
    return tmp_path


def test_every_previously_fatal_shape_loads(shapes_bundle: Path) -> None:
    with readb.open(str(shapes_bundle), cache=False) as db:
        rows = db.sql("SELECT __name, title FROM shape ORDER BY __name")
    assert len(rows) == len(FATAL_SHAPES) + 1
    assert {r["title"] for r in rows} == set(FATAL_SHAPES) | {"healthy"}


def test_a_healthy_document_is_unaffected_by_a_bad_neighbour(shapes_bundle: Path) -> None:
    with readb.open(str(shapes_bundle), cache=False) as db:
        assert db.sql("SELECT title FROM shape WHERE __name = 'healthy'")[0]["title"] == "healthy"


def test_the_colliding_key_keeps_the_last_occurrence(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text(
        '---\ntype: T\nflag: {1: first, "1": second}\n---\nbody\n', encoding="utf-8"
    )
    with readb.open(str(tmp_path), cache=False) as db:
        assert db.sql("SELECT flag FROM t")[0]["flag"] == {"1": "second"}


def test_a_collision_is_logged(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    (tmp_path / "a.md").write_text(
        '---\ntype: T\nflag: {1: first, "1": second}\n---\nbody\n', encoding="utf-8"
    )
    with caplog.at_level(logging.WARNING, logger="readb"):
        readb.open(str(tmp_path), cache=False).close()
    assert any("keeping the last" in r.getMessage() for r in caplog.records)


def test_a_non_string_top_level_key_becomes_a_column(tmp_path: Path) -> None:
    """Union-of-keys is lossless: such a key used to be dropped, value and all."""
    (tmp_path / "a.md").write_text(
        "---\ntype: T\n1: one\n2026-01-01: dated\n---\nbody\n", encoding="utf-8"
    )
    with readb.open(str(tmp_path), cache=False) as db:
        row = db.sql('SELECT "1", "2026-01-01" FROM t')[0]
    assert row["1"] == "one"
    assert row["2026-01-01"] == "dated"


def test_an_all_empty_mapping_column_carries_the_placeholder(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntype: T\nflag: {}\n---\nbody\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("---\ntype: T\nflag: {}\n---\nbody\n", encoding="utf-8")
    with readb.open(str(tmp_path), cache=False) as db:
        assert db.schema().tables["t"].columns["flag"] == 'STRUCT("__DUMMY" VARCHAR)'
        assert db.sql("SELECT flag FROM t")[0]["flag"] == {"__DUMMY": None}


def test_one_real_key_retires_the_placeholder(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntype: T\nflag: {}\n---\nbody\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("---\ntype: T\nflag: {a: 1}\n---\nbody\n", encoding="utf-8")
    with readb.open(str(tmp_path), cache=False) as db:
        assert db.schema().tables["t"].columns["flag"] == 'STRUCT("a" BIGINT)'
        rows = {r["__name"]: r["flag"] for r in db.sql("SELECT __name, flag FROM t")}
    assert rows["a"] == {"a": None}  # the empty mapping contributes no field, so NULL
    assert rows["b"] == {"a": 1}


def test_an_oversized_integer_round_trips_as_text(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text(
        "---\ntype: T\nn: 99999999999999999999999999\n---\nbody\n", encoding="utf-8"
    )
    with readb.open(str(tmp_path), cache=False) as db:
        assert db.sql("SELECT n FROM t")[0]["n"] == "99999999999999999999999999"


# --------------------------------------------------------------------------------------------
# The ladder. With the lattice total nothing known reaches it, so it is forced.
# --------------------------------------------------------------------------------------------


def test_an_unrenderable_column_degrades_the_table_not_the_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Rung 2: only the column that failed is widened, and the warning names it.

    Widening the whole table would silently re-type healthy columns, so every predicate that
    used to work would match nothing — an error with no error message.
    """
    import readb.loader as loader_module
    from readb.schema import Kind

    real_render = loader_module.render_ddl

    def broken(t):  # type: ignore[no-untyped-def]
        if t.kind is Kind.BIGINT:
            return "NOT A TYPE"
        return real_render(t)

    monkeypatch.setattr(loader_module, "render_ddl", broken)
    (tmp_path / "a.md").write_text("---\ntype: T\nn: 1\ntitle: kept\n---\nbody\n", encoding="utf-8")
    with (
        caplog.at_level(logging.WARNING, logger="readb"),
        readb.open(str(tmp_path), cache=False) as db,
    ):
        rows = db.sql("SELECT __name, title, n FROM t")
        warnings = list(db.schema().warnings)
    # `title` is untouched: it did not fail, so it keeps its type and its plain value.
    assert rows[0]["title"] == "kept"
    # `n` is the column that could not be rendered, so it alone is JSON.
    assert json.loads(rows[0]["n"]) == 1
    assert any("'n' widened to JSON" in w for w in warnings), warnings
    assert any("'n' widened to JSON" in r.getMessage() for r in caplog.records)


def test_a_table_that_cannot_hold_its_columns_at_all_keeps_its_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rung 3: frontmatter columns are dropped; the documents stay addressable."""
    import readb.loader as loader_module
    from readb.schema import VIRTUAL_FIELDS

    def always_broken(t):  # type: ignore[no-untyped-def]
        return "NOT A TYPE"

    monkeypatch.setattr(loader_module, "render_ddl", always_broken)
    (tmp_path / "a.md").write_text("---\ntype: T\nn: 1\n---\nbody\n", encoding="utf-8")
    with readb.open(str(tmp_path), cache=False) as db:
        columns = set(db.schema().tables["t"].columns)
        rows = db.sql("SELECT __name, __body FROM t")
        # __DOCUMENTS degrades too, so __TAGS has no `tags` column to explode: it must still
        # answer rather than fail on a missing relation.
        assert db.sql("SELECT * FROM __TAGS") == []
    assert columns == set(VIRTUAL_FIELDS)
    assert rows[0]["__name"] == "a"
    assert rows[0]["__body"].strip() == "body"


# --------------------------------------------------------------------------------------------
# Findings from the sprint's two independent reviews. Each of these took a whole bundle down.
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "frontmatter",
    [
        pytest.param("d: 2026-02-30", id="impossible-date"),
        pytest.param("d: 2026-13-01", id="month-13"),
        pytest.param("d: 2026-01-01 25:00:00", id="hour-25"),
        pytest.param("d: 0000-01-01", id="year-zero"),
        pytest.param("f: &x\n  b: *x", id="recursive-anchor"),
        pytest.param("f: &x\n  - *x", id="recursive-list-anchor"),
        pytest.param("deep: " + "{a: " * 450 + "1" + "}" * 450, id="450-deep"),
        pytest.param('k: "\\uD800"', id="lone-surrogate"),
        pytest.param('tags: {"": 1}', id="mapping-in-tags"),
        pytest.param('description: {"": 1}', id="mapping-in-a-reserved-field"),
        pytest.param('title: {"a\\0b": 1}', id="nul-in-a-field-name"),
    ],
)
def test_a_bad_document_never_costs_the_bundle(tmp_path: Path, frontmatter: str) -> None:
    """Every one of these made `readb.open` raise, so no query against the bundle answered."""
    (tmp_path / "bad.md").write_text(
        f"---\ntype: T\ntitle: bad\n{frontmatter}\n---\nbody\n", encoding="utf-8"
    )
    (tmp_path / "good.md").write_text(
        "---\ntype: T\ntitle: healthy\nkeep: 7\n---\nbody\n", encoding="utf-8"
    )
    with readb.open(str(tmp_path), cache=False) as db:
        healthy = db.sql("SELECT keep FROM t WHERE __name = 'good'")
        db.sql("SELECT * FROM __TAGS")  # the view is built after the tables, outside the ladder
    assert healthy == [{"keep": 7}], "the healthy document must keep its columns and values"


def test_keys_that_python_considers_equal_stay_distinct(tmp_path: Path) -> None:
    """`hash(True) == hash(1)`, so PyYAML would merge these before readb ever saw them."""
    (tmp_path / "a.md").write_text("---\ntype: T\n1: one\ntrue: T\n---\nbody\n", encoding="utf-8")
    with readb.open(str(tmp_path), cache=False) as db:
        row = db.sql('SELECT "1", "true" FROM t')[0]
    assert row["1"] == "one"
    assert row["true"] == "T"


def test_names_that_differ_only_by_case_are_one_column_and_warned(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """DuckDB compares identifiers case-insensitively, so these cannot be two columns."""
    (tmp_path / "a.md").write_text(
        "---\ntype: T\nStatus: open\nstatus: closed\n---\nbody\n", encoding="utf-8"
    )
    with (
        caplog.at_level(logging.WARNING, logger="readb"),
        readb.open(str(tmp_path), cache=False) as db,
    ):
        assert db.sql("SELECT status FROM t")[0]["status"] == "closed"
    assert any("keeping the last" in r.getMessage() for r in caplog.records)


def test_an_empty_key_name_does_not_cost_the_table_its_columns(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text('---\ntype: T\n"": 1\nkeep: 5\n---\nbody\n', encoding="utf-8")
    with readb.open(str(tmp_path), cache=False) as db:
        row = db.sql('SELECT keep, "__EMPTY" FROM t')[0]
    assert row["keep"] == 5
    assert row["__EMPTY"] == 1


def test_a_set_value_is_stored_deterministically(tmp_path: Path) -> None:
    """`str(a_set)` is hash-randomized, so the same bundle stored different bytes per process."""
    (tmp_path / "a.md").write_text(
        "---\ntype: T\nk: !!set {alpha, beta, gamma, delta}\n---\nbody\n", encoding="utf-8"
    )
    with readb.open(str(tmp_path), cache=False) as db:
        stored = db.sql("SELECT k FROM t")[0]["k"]
    assert json.loads(stored) == ["alpha", "beta", "delta", "gamma"]
