"""CLI behavior for the read-only commands (query, schema): output modes and clean errors."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner, Result

from readb.cli import main

MINI_BUNDLE = Path(__file__).parent / "fixtures" / "mini"


def _run(*args: str) -> Result:
    return CliRunner().invoke(main, args)


# --------------------------------------------------------------------------------------------
# Clean errors: engine failures surface as one-line click errors, never tracebacks.
# --------------------------------------------------------------------------------------------


def test_query_missing_table_is_clean_error() -> None:
    result = _run("query", "SELECT * FROM no_such_table", "--bundle", str(MINI_BUNDLE))
    assert result.exit_code == 1
    assert "no_such_table" in result.output
    assert "Catalog Error" in result.output
    assert "Traceback" not in result.output


def test_query_bad_sql_is_clean_error() -> None:
    result = _run("query", "SELEC oops", "--bundle", str(MINI_BUNDLE))
    assert result.exit_code == 1
    assert "Error" in result.output
    assert "Traceback" not in result.output


def test_query_success_still_works() -> None:
    result = _run("query", "SELECT count(*) AS n FROM __DOCUMENTS", "--bundle", str(MINI_BUNDLE))
    assert result.exit_code == 0, result.output
    assert "n" in result.output
