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


# --------------------------------------------------------------------------------------------
# Output formats: --format table|json|csv|tsv|raw (+ the --json alias).
# --------------------------------------------------------------------------------------------

_TWO_ROWS = "SELECT * FROM (VALUES ('a,b', 1), ('c' || chr(10) || 'd', NULL)) t(x, y) ORDER BY y"


def test_format_csv_quotes_commas_and_newlines() -> None:
    result = _run("query", _TWO_ROWS, "--bundle", str(MINI_BUNDLE), "--format", "csv")
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == "x,y"
    assert '"a,b",1' in result.output  # comma quoted
    assert '"c\nd",' in result.output  # newline quoted, NULL as empty field


def test_format_tsv() -> None:
    result = _run(
        "query", "SELECT 'a,b' AS x, 2 AS y", "--bundle", str(MINI_BUNDLE), "--format", "tsv"
    )
    assert result.exit_code == 0, result.output
    assert "x\ty" in result.output
    assert "a,b\t2" in result.output  # comma needs no quoting in tsv


def test_format_raw_is_verbatim_and_null_is_empty() -> None:
    result = _run(
        "query",
        "SELECT * FROM (VALUES ('a \"quoted\", value'), (NULL)) t(x)",
        "--bundle",
        str(MINI_BUNDLE),
        "--format",
        "raw",
    )
    assert result.exit_code == 0, result.output
    assert result.output == 'a "quoted", value\n\n'  # verbatim, then NULL as an empty line


def test_json_flag_is_alias_for_format_json() -> None:
    by_flag = _run("query", "SELECT 1 AS n", "--bundle", str(MINI_BUNDLE), "--json")
    by_format = _run("query", "SELECT 1 AS n", "--bundle", str(MINI_BUNDLE), "--format", "json")
    assert by_flag.exit_code == by_format.exit_code == 0
    assert by_flag.output == by_format.output


def test_json_flag_conflicts_with_other_format() -> None:
    result = _run("query", "SELECT 1", "--bundle", str(MINI_BUNDLE), "--json", "--format", "csv")
    assert result.exit_code == 2
    assert "conflicts" in result.output


# --------------------------------------------------------------------------------------------
# __raw virtual column and the show command.
# --------------------------------------------------------------------------------------------


def test_raw_column_is_byte_exact() -> None:
    result = _run(
        "query",
        "SELECT __raw FROM __DOCUMENTS WHERE __path LIKE '%.md' ORDER BY __path LIMIT 1",
        "--bundle",
        str(MINI_BUNDLE),
        "--format",
        "raw",
    )
    assert result.exit_code == 0, result.output
    row = _run(
        "query",
        "SELECT __path FROM __DOCUMENTS ORDER BY __path LIMIT 1",
        "--bundle",
        str(MINI_BUNDLE),
        "--format",
        "raw",
    )
    on_disk = (MINI_BUNDLE / row.output.strip()).read_text(encoding="utf-8")
    assert result.output == on_disk + "\n"  # echo adds the trailing newline


def test_raw_column_in_schema_output() -> None:
    result = _run("schema", "--bundle", str(MINI_BUNDLE))
    assert result.exit_code == 0
    assert "__raw" in result.output


def test_show_prints_body_matching_body_column() -> None:
    path_result = _run(
        "query",
        "SELECT __path, __body FROM __DOCUMENTS WHERE length(__body) > 0 ORDER BY __path LIMIT 1",
        "--bundle",
        str(MINI_BUNDLE),
        "--json",
    )
    import json

    row = json.loads(path_result.output)[0]
    shown = _run("show", "--bundle", str(MINI_BUNDLE), row["__path"])
    assert shown.exit_code == 0, shown.output
    assert shown.output == row["__body"] + "\n"


def test_show_multiple_uses_path_headers() -> None:
    result = _run("show", "--bundle", str(MINI_BUNDLE), "index", "log")
    assert result.exit_code == 0, result.output
    assert "==> index.md <==" in result.output
    assert "==> log.md <==" in result.output


def test_show_missing_concept_is_clean_error() -> None:
    result = _run("show", "--bundle", str(MINI_BUNDLE), "does-not-exist")
    assert result.exit_code == 1
    assert "does-not-exist" in result.output
    assert "Traceback" not in result.output
