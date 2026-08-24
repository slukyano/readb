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
    """Rung 2: the table is rebuilt with JSON columns, and the bundle stays queryable."""
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
    # A degraded table holds its values as JSON, which is what "widened to JSON" means.
    assert json.loads(rows[0]["title"]) == "kept"
    assert any("could not be built as inferred" in w for w in warnings)
    assert any("could not be built as inferred" in r.getMessage() for r in caplog.records)


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
