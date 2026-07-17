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


def test_json_flag_with_format_json_is_allowed() -> None:
    result = _run(
        "query", "SELECT 1 AS n", "--bundle", str(MINI_BUNDLE), "--json", "--format", "json"
    )
    assert result.exit_code == 0, result.output


def test_format_csv_zero_rows_prints_nothing() -> None:
    # Documented: column names travel with rows, so an empty result has no header to print.
    result = _run(
        "query", "SELECT 1 AS n WHERE false", "--bundle", str(MINI_BUNDLE), "--format", "csv"
    )
    assert result.exit_code == 0, result.output
    assert result.output == ""


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
    # The separate mapping section is gone; the original type still shows inline per table.
    assert "Type mapping" not in result.output
    assert "(type: 'Widget')" in result.output


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
    body = row["__body"]
    assert shown.output == (body if body.endswith("\n") else body + "\n")


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


# --------------------------------------------------------------------------------------------
# Wiki-style name resolution: a clashing simple name errors with the clashing paths listed.
# --------------------------------------------------------------------------------------------


def _clashing_bundle(tmp_path: Path, copies: int) -> Path:
    for i in range(copies):
        sub = tmp_path / f"dir{i}"
        sub.mkdir()
        (sub / "dup.md").write_text(f"---\ntype: T\n---\nbody {i}\n", encoding="utf-8")
    return tmp_path


def test_show_name_clash_lists_paths(tmp_path: Path) -> None:
    bundle = _clashing_bundle(tmp_path, 2)
    result = _run("show", "--bundle", str(bundle), "dup")
    assert result.exit_code == 1
    assert "ambiguous" in result.output
    assert "dir0/dup.md" in result.output
    assert "dir1/dup.md" in result.output
    assert "full path" in result.output


def test_name_clash_list_is_capped_at_five(tmp_path: Path) -> None:
    bundle = _clashing_bundle(tmp_path, 7)
    result = _run("show", "--bundle", str(bundle), "dup")
    assert result.exit_code == 1
    assert "dir4/dup.md" in result.output
    assert "dir5/dup.md" not in result.output
    assert "and 2 more" in result.output


def test_full_path_resolves_during_clash(tmp_path: Path) -> None:
    bundle = _clashing_bundle(tmp_path, 2)
    result = _run("show", "--bundle", str(bundle), "dir1/dup.md")
    assert result.exit_code == 0, result.output
    assert result.output == "body 1\n"


def test_name_resolution_refuses_symlink_escape(tmp_path: Path) -> None:
    # A symlink inside the bundle pointing outside must be unreachable by name AND by path.
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("---\ntype: T\n---\nsecret\n", encoding="utf-8")
    (bundle / "evil.md").symlink_to(outside)
    # Both spellings are refused, and the error explicitly names the symlink-escape cause.
    by_name = _run("show", "--bundle", str(bundle), "evil")
    assert by_name.exit_code == 1
    assert "outside the bundle" in by_name.output
    assert "symlink" in by_name.output
    assert "secret" not in by_name.output
    by_path = _run("show", "--bundle", str(bundle), "evil.md")
    assert by_path.exit_code != 0
    assert "secret" not in by_path.output
    assert "outside the bundle" in by_path.output


def test_name_is_literal_not_a_glob_pattern(tmp_path: Path) -> None:
    (tmp_path / "task.md").write_text("---\ntype: T\n---\na\n", encoding="utf-8")
    (tmp_path / "tusk.md").write_text("---\ntype: T\n---\nb\n", encoding="utf-8")
    result = _run("show", "--bundle", str(tmp_path), "t?sk")
    assert result.exit_code == 1
    assert "no such concept" in result.output
    result = _run("show", "--bundle", str(tmp_path), "*")
    assert result.exit_code == 1


def test_directory_named_md_is_not_a_concept(tmp_path: Path) -> None:
    (tmp_path / "weird.md").mkdir()
    (tmp_path / "real.md").write_text("---\ntype: T\n---\nok\n", encoding="utf-8")
    by_name = _run("show", "--bundle", str(tmp_path), "weird")
    assert by_name.exit_code == 1
    assert "no such concept" in by_name.output
    by_path = _run("get", "--bundle", str(tmp_path), "weird.md", "type")
    assert by_path.exit_code == 1
    assert "Traceback" not in by_path.output


def test_name_column_present_and_id_gone() -> None:
    result = _run("schema", "--bundle", str(MINI_BUNDLE))
    assert result.exit_code == 0
    assert "__name" in result.output
    assert "__id" not in result.output


# --------------------------------------------------------------------------------------------
# --bundle is required (the cwd default was reverted: silent wrong-scope operations).
# --------------------------------------------------------------------------------------------


def test_bundle_is_required() -> None:
    result = _run("query", "SELECT 1")
    assert result.exit_code == 2
    assert "--bundle" in result.output
