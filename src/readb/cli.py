"""Command-line interface for readb.

readb query "<SQL>" --bundle ./path                 # results as a table
readb query "<SQL>" --bundle ./path --format csv    # or json | tsv | raw (--json = json alias)
readb schema --bundle ./path                        # detected types, table names, columns
readb show   --bundle ./path <name-or-path> ...     # a concept's body (SELECT __body alias)

Read-only query commands (query, schema) never touch the bundle. The get/set/unset commands are
the one, deliberately separate, write path: a surgical frontmatter field editor (see
``readb.fields``). ``get`` is read-only; ``set``/``unset`` edit a single concept file in place.

readb get   --bundle ./path <name-or-path> <key>              # print one frontmatter field
readb set   --bundle ./path <name-or-path> key=value ...      # set fields in place
readb unset --bundle ./path <name-or-path> <key> ...          # remove fields in place
"""

from __future__ import annotations

import csv
import glob
import io
import json
from pathlib import Path
from typing import Any

import click
import duckdb

import readb
from readb import fields, parser

# --bundle is deliberately required: defaulting to the cwd silently treats any directory
# (a repo root, $HOME) as a bundle — wrong-scope reads and misdirected name-resolved writes.
# The ergonomic replacement is explicit init + upward discovery (task: bundle-init-discovery).
_BUNDLE_OPTION = click.option(
    "--bundle",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the OKF bundle directory.",
)


@click.group()
@click.version_option(version=readb.__version__, prog_name="readb")
def main() -> None:
    """readb: run real SQL against an OKF bundle (read-only)."""


@main.command()
@click.argument("sql")
@_BUNDLE_OPTION
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv", "tsv", "raw"]),
    default=None,
    help="Output format (default: table). raw prints values verbatim, one per line.",
)
@click.option("--json", "as_json", is_flag=True, help="Alias for --format json.")
def query(sql: str, bundle: str, output_format: str | None, as_json: bool) -> None:
    """Execute SQL against the bundle and print the result rows."""
    if as_json and output_format not in (None, "json"):
        raise click.UsageError(f"--json conflicts with --format {output_format}")
    output_format = "json" if as_json else (output_format or "table")
    try:
        with readb.open(bundle) as db:
            rows = db.sql(sql)
    except duckdb.Error as exc:
        raise click.ClickException(str(exc)) from exc
    if output_format == "json":
        click.echo(json.dumps(rows, indent=2, default=_json_default, ensure_ascii=False))
    elif output_format in ("csv", "tsv"):
        click.echo(_format_csv(rows, delimiter="," if output_format == "csv" else "\t"), nl=False)
    elif output_format == "raw":
        _echo_raw(rows)
    else:
        click.echo(_format_table(rows))


@main.command()
@_BUNDLE_OPTION
def schema(bundle: str) -> None:
    """Print detected types, their normalized table names, and columns + types."""
    try:
        with readb.open(bundle) as db:
            bundle_schema = db.schema()
    except duckdb.Error as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(_format_schema(bundle_schema))


@main.command()
@_BUNDLE_OPTION
@click.argument("names", nargs=-1, required=True)
def show(bundle: str, names: tuple[str, ...]) -> None:
    """Print the body of one or more concepts (frontmatter stripped).

    The CLI alias for ``SELECT __body``: same parser, same semantics. Accepts a simple name or
    a full ``.md`` path per concept; also works for the reserved index/log files. Does not load
    the bundle — only the addressed files are parsed.
    """
    bundle_root = Path(bundle).resolve()
    resolved = [_concept_path(bundle, name) for name in names]
    for name, file_path in zip(names, resolved, strict=True):
        concept = parser.parse_file(file_path, bundle_root=bundle_root)
        if concept is None:
            raise click.ClickException(f"cannot parse {name!r} ({file_path})")
        if len(resolved) > 1:
            click.echo(f"==> {concept.path} <==")
        # The body is printed verbatim; add a newline only when the file lacks a trailing one.
        click.echo(concept.body, nl=not concept.body.endswith("\n"))


# --------------------------------------------------------------------------------------------
# Frontmatter field editing (get / set / unset).
#
# The one write path, kept separate from the read-only query layer. Each command addresses a
# single concept by wiki-style name or full ``.md`` path (see ``_concept_path``); the edit is
# surgical and line-based (see readb.fields), so only the touched fields change.
# --------------------------------------------------------------------------------------------


@main.command()
@_BUNDLE_OPTION
@click.argument("name_or_path")
@click.argument("key")
def get(bundle: str, name_or_path: str, key: str) -> None:
    """Print one frontmatter field of a concept (nothing if the field is absent)."""
    value = fields.get_field(_concept_path(bundle, name_or_path), key)
    if value is not None:
        click.echo(value)


@main.command(name="set")
@_BUNDLE_OPTION
@click.argument("name_or_path")
@click.argument("assignments", nargs=-1, required=True)
def set_(bundle: str, name_or_path: str, assignments: tuple[str, ...]) -> None:
    """Set one or more frontmatter fields (KEY=VALUE ...) on a concept, in place."""
    pairs: list[tuple[str, str]] = []
    for item in assignments:
        if "=" not in item:
            raise click.BadParameter(f"expected KEY=VALUE, got {item!r}", param_hint="ASSIGNMENTS")
        key, _, value = item.partition("=")
        if not key:
            raise click.BadParameter(f"empty key in {item!r}", param_hint="ASSIGNMENTS")
        pairs.append((key, value))
    _edit(lambda path: fields.set_fields(path, pairs), bundle, name_or_path)


@main.command()
@_BUNDLE_OPTION
@click.argument("name_or_path")
@click.argument("keys", nargs=-1, required=True)
def unset(bundle: str, name_or_path: str, keys: tuple[str, ...]) -> None:
    """Remove one or more frontmatter fields (KEY ...) from a concept, in place."""
    _edit(lambda path: fields.unset_fields(path, list(keys)), bundle, name_or_path)


_CLASH_LIST_CAP = 5


def _is_inside(path: Path, root: Path) -> bool:
    """True when ``path`` (already resolved) is ``root`` or lives under it."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _concept_path(bundle: str, name_or_path: str) -> Path:
    """Resolve a concept reference to its file: a full ``.md`` path or a wiki-style name.

    A reference ending in ``.md`` is a bundle-relative path, resolved exactly (guarded against
    escaping the bundle). Anything else is a simple name — no path separators — resolved by
    searching the bundle for ``**/<name>.md``: exactly one match resolves; several raise an
    error listing the clashing paths (at most 5) so the caller can re-run with the full path.

    Symlinks (or ``../`` segments) that resolve to a file *outside* the bundle are not
    supported: they are refused with an explicit error, by name and by path alike. readb only
    ever addresses files that live within the bundle root.
    """
    bundle_root = Path(bundle).resolve()

    if name_or_path.endswith(".md"):
        target = (bundle_root / name_or_path).resolve()
        try:
            target.relative_to(bundle_root)
        except ValueError:
            raise click.BadParameter(
                f"path escapes the bundle (a '../' segment or a symlink resolving outside the "
                f"bundle is not supported): {name_or_path!r}",
                param_hint="NAME_OR_PATH",
            ) from None
        if not target.is_file():
            raise click.ClickException(f"no such concept in bundle: {name_or_path!r} ({target})")
        return target

    if "/" in name_or_path or "\\" in name_or_path:
        raise click.BadParameter(
            f"a concept name has no path separators; use the full path ending in .md "
            f"instead: {name_or_path!r}",
            param_hint="NAME_OR_PATH",
        )
    # glob.escape: a name is a literal file name, never a pattern. Candidates must be regular
    # files; a symlink whose target resolves outside the bundle is refused (unreachable by name
    # just as by path) with an explicit error, not silently reported as "not found".
    name_matches = [p for p in bundle_root.rglob(f"{glob.escape(name_or_path)}.md") if p.is_file()]
    matches = sorted(
        (p for p in name_matches if _is_inside(p.resolve(), bundle_root)),
        key=lambda p: p.as_posix(),
    )
    if not matches:
        escaped = [p for p in name_matches if not _is_inside(p.resolve(), bundle_root)]
        if escaped:
            culprit = escaped[0]
            raise click.ClickException(
                f"concept {name_or_path!r} resolves outside the bundle via a symlink and is "
                f"not supported: {culprit.relative_to(bundle_root)} -> {culprit.resolve()}"
            )
        raise click.ClickException(f"no such concept in bundle: {name_or_path!r}")
    if len(matches) > 1:
        shown = ", ".join(str(p.relative_to(bundle_root)) for p in matches[:_CLASH_LIST_CAP])
        more = len(matches) - _CLASH_LIST_CAP
        tail = f", and {more} more" if more > 0 else ""
        raise click.ClickException(
            f"name {name_or_path!r} is ambiguous in this bundle: {shown}{tail}; "
            f"re-run with the full path instead of the simple name"
        )
    return matches[0]


def _edit(action: Any, bundle: str, name_or_path: str) -> None:
    """Run a frontmatter mutation, translating a missing frontmatter block into a click error."""
    try:
        action(_concept_path(bundle, name_or_path))
    except fields.FrontmatterError as exc:
        raise click.ClickException(str(exc)) from exc


# --------------------------------------------------------------------------------------------
# Output formatting.
# --------------------------------------------------------------------------------------------


def _json_default(obj: Any) -> str:
    """Serialize non-JSON-native values (e.g. datetimes) as strings for ``--json`` output."""
    return str(obj)


def _format_csv(rows: list[dict[str, Any]], *, delimiter: str) -> str:
    """Render rows as CSV/TSV: header row, stdlib-csv quoting, NULL as an empty field.

    A zero-row result prints nothing, header included — column names travel with the rows
    (``Database.sql`` returns dicts), so there is nothing to name an empty result with.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    if rows:
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow("" if v is None else _text_value(v) for v in row.values())
    return buffer.getvalue()


def _echo_raw(rows: list[dict[str, Any]]) -> None:
    """Print every value verbatim, one per line: no quoting, no escaping, NULL as empty.

    Intended for single-column reads (``SELECT __body ... --format raw``); with multiline
    values, row boundaries are ambiguous by construction — that is what csv is for.
    """
    for row in rows:
        for value in row.values():
            click.echo("" if value is None else _text_value(value))


def _text_value(value: Any) -> str:
    """Stringify one value for text output; lists/dicts keep their JSON text form."""
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=_json_default, ensure_ascii=False)
    return str(value)


def _format_table(rows: list[dict[str, Any]]) -> str:
    """Render result rows as a simple aligned text table."""
    if not rows:
        return "(0 rows)"
    columns = list(rows[0].keys())
    cells = [[_cell(row.get(col)) for col in columns] for row in rows]
    widths = [
        max(len(columns[i]), *(len(cells[r][i]) for r in range(len(cells))))
        for i in range(len(columns))
    ]
    header = "  ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
    separator = "  ".join("-" * widths[i] for i in range(len(columns)))
    body = "\n".join(
        "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row_cells)) for row_cells in cells
    )
    plural = "s" if len(rows) != 1 else ""
    return f"{header}\n{separator}\n{body}\n({len(rows)} row{plural})"


def _cell(value: Any) -> str:
    """Stringify a single result value for table display."""
    return "NULL" if value is None else _text_value(value)


def _format_schema(bundle_schema: Any) -> str:
    """Render the detected schema: tables with columns + types (original type inline)."""
    lines: list[str] = []
    for warning in bundle_schema.warnings:
        lines.append(f"! warning: {warning}")
    if bundle_schema.warnings:
        lines.append("")

    lines.append("Tables")
    lines.append("======")
    for table_name in sorted(bundle_schema.tables):
        table = bundle_schema.tables[table_name]
        suffix = f"   (type: {table.original_type!r})" if table.original_type else ""
        lines.append(f"\n{table_name}{suffix}")
        name_width = max((len(c) for c in table.columns), default=0)
        for column, ddl in table.columns.items():
            lines.append(f"    {column.ljust(name_width)}  {ddl}")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
