"""An unknown table is answered from the bundle's tables, not DuckDB's catalog.

Backlog task ``032-unknown-table-error``: DuckDB suggested ``duckdb_indexes`` — a table that
exists in no bundle and answers no question — and never mentioned ``readb schema``.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from click.testing import CliRunner, Result

import readb
from readb.cli import main

MINI_BUNDLE = Path(__file__).parent / "fixtures" / "mini"


def _run(*args: str) -> Result:
    return CliRunner().invoke(main, args)


def test_message_lists_the_bundles_own_tables(mini_path: Path) -> None:
    with readb.open(str(mini_path)) as db:
        real_tables = set(db._table_names())
        with pytest.raises(readb.UnknownTableError) as caught:
            db.sql("SELECT * FROM concepts")
    message = str(caught.value)
    assert "no table named 'concepts'" in message
    for table in real_tables:
        assert table in message
    assert "duckdb_indexes" not in message
    assert "readb schema" in message


def test_the_error_is_still_a_duckdb_catalog_exception(mini_path: Path) -> None:
    """Anything catching DuckDB's exception today keeps working."""
    with readb.open(str(mini_path)) as db, pytest.raises(duckdb.CatalogException):
        db.sql("SELECT * FROM concepts")


def test_the_error_carries_the_table_list_for_a_caller_to_render(mini_path: Path) -> None:
    with readb.open(str(mini_path)) as db, pytest.raises(readb.UnknownTableError) as caught:
        db.sql_table("SELECT * FROM concepts")
    error = caught.value
    assert error.table == "concepts"
    assert "__DOCUMENTS" in error.tables
    assert "--bundle" not in error.render(show_bundle=False)
    assert "--bundle" in error.render()


def test_concept_tables_are_listed_before_system_tables(mini_path: Path) -> None:
    with readb.open(str(mini_path)) as db, pytest.raises(readb.UnknownTableError) as caught:
        db.sql("SELECT * FROM concepts")
    tables = caught.value.tables
    first_system = next(i for i, t in enumerate(tables) if t.startswith("__"))
    assert all(not t.startswith("__") for t in tables[:first_system])
    assert all(t.startswith("__") for t in tables[first_system:])


def test_a_long_table_list_is_truncated_and_says_how_many(tmp_path: Path) -> None:
    for index in range(40):
        (tmp_path / f"doc{index}.md").write_text(
            f"---\ntype: Type{index:02d}\n---\nbody\n", encoding="utf-8"
        )
    with readb.open(str(tmp_path)) as db, pytest.raises(readb.UnknownTableError) as caught:
        db.sql("SELECT * FROM nope")
    message = str(caught.value)
    assert "and 19 more" in message  # 40 concept tables + 4 system relations, 25 listed
    assert "readb schema" in message


def test_unknown_column_keeps_duckdbs_candidates_and_gains_a_pointer(mini_path: Path) -> None:
    with readb.open(str(mini_path)) as db, pytest.raises(duckdb.BinderException) as caught:
        db.sql("SELECT no_such_column FROM __DOCUMENTS")
    message = str(caught.value)
    assert "Candidate bindings" in message
    assert "readb schema" in message


def test_a_syntax_error_passes_through_untouched(mini_path: Path) -> None:
    with readb.open(str(mini_path)) as db, pytest.raises(duckdb.ParserException) as caught:
        db.sql("SELECT")
    assert "readb schema" not in str(caught.value)


def test_cli_reports_the_bundle_flag_it_was_given() -> None:
    result = _run("query", "SELECT * FROM concepts", "--bundle", str(MINI_BUNDLE))
    assert result.exit_code == 1
    assert f"readb schema --bundle {MINI_BUNDLE}" in result.output
    assert "duckdb_indexes" not in result.output


def test_cli_omits_the_flag_when_the_bundle_came_from_the_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registry-resolved bundle needs no --bundle in the suggested command (ADR 0004)."""
    bundle = tmp_path / "notes"
    bundle.mkdir()
    (bundle / "a.md").write_text("---\ntype: Note\n---\nbody\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "notes").exit_code == 0
    result = _run("query", "SELECT * FROM concepts")
    assert result.exit_code == 1, result.output
    assert "readb schema" in result.output
    assert "--bundle" not in result.output
