"""Command-line interface for readb.

readb query "<SQL>" --bundle ./path         # results as a table
readb query "<SQL>" --bundle ./path --json  # results as JSON
readb schema --bundle ./path                # detected types, table names, columns, mapping

Read-only query commands (query, schema) never touch the bundle. The get/set/unset commands are
the one, deliberately separate, write path: a surgical frontmatter field editor (see
``readb.fields``). ``get`` is read-only; ``set``/``unset`` edit a single concept file in place.

readb get   --bundle ./path <concept-id> <key>              # print one frontmatter field
readb set   --bundle ./path <concept-id> key=value ...      # set fields in place
readb unset --bundle ./path <concept-id> <key> ...          # remove fields in place
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

import readb
from readb import fields

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
@click.option("--json", "as_json", is_flag=True, help="Emit results as JSON instead of a table.")
def query(sql: str, bundle: str, as_json: bool) -> None:
    """Execute SQL against the bundle and print the result rows."""
    with readb.open(bundle) as db:
        rows = db.sql(sql)
    if as_json:
        click.echo(json.dumps(rows, indent=2, default=_json_default, ensure_ascii=False))
    else:
        click.echo(_format_table(rows))


@main.command()
@_BUNDLE_OPTION
def schema(bundle: str) -> None:
    """Print detected types, their normalized table names, columns + types, and the mapping."""
    with readb.open(bundle) as db:
        bundle_schema = db.schema()
    click.echo(_format_schema(bundle_schema))


# --------------------------------------------------------------------------------------------
# Frontmatter field editing (get / set / unset).
#
# The one write path, kept separate from the read-only query layer. Each command addresses a
# single concept by its ID within the bundle (``<bundle>/<concept-id>.md``); the edit is
# surgical and line-based (see readb.fields), so only the touched fields change.
# --------------------------------------------------------------------------------------------


@main.command()
@_BUNDLE_OPTION
@click.argument("concept_id")
@click.argument("key")
def get(bundle: str, concept_id: str, key: str) -> None:
    """Print one frontmatter field of a concept (nothing if the field is absent)."""
    value = fields.get_field(_concept_path(bundle, concept_id), key)
    if value is not None:
        click.echo(value)


@main.command(name="set")
@_BUNDLE_OPTION
@click.argument("concept_id")
@click.argument("assignments", nargs=-1, required=True)
def set_(bundle: str, concept_id: str, assignments: tuple[str, ...]) -> None:
    """Set one or more frontmatter fields (KEY=VALUE ...) on a concept, in place."""
    pairs: list[tuple[str, str]] = []
    for item in assignments:
        if "=" not in item:
            raise click.BadParameter(f"expected KEY=VALUE, got {item!r}", param_hint="ASSIGNMENTS")
        key, _, value = item.partition("=")
        if not key:
            raise click.BadParameter(f"empty key in {item!r}", param_hint="ASSIGNMENTS")
        pairs.append((key, value))
    _edit(lambda path: fields.set_fields(path, pairs), bundle, concept_id)


@main.command()
@_BUNDLE_OPTION
@click.argument("concept_id")
@click.argument("keys", nargs=-1, required=True)
def unset(bundle: str, concept_id: str, keys: tuple[str, ...]) -> None:
    """Remove one or more frontmatter fields (KEY ...) from a concept, in place."""
    _edit(lambda path: fields.unset_fields(path, list(keys)), bundle, concept_id)


def _concept_path(bundle: str, concept_id: str) -> Path:
    """Resolve a concept ID to its file (``<bundle>/<id>.md``), guarding against escapes.

    Accepts an ID with or without a trailing ``.md``. Raises a click error if the path escapes
    the bundle directory or the file does not exist.
    """
    bundle_root = Path(bundle).resolve()
    relative = concept_id[:-3] if concept_id.endswith(".md") else concept_id
    target = (bundle_root / f"{relative}.md").resolve()
    try:
        target.relative_to(bundle_root)
    except ValueError:
        raise click.BadParameter(
            f"concept id escapes the bundle: {concept_id!r}", param_hint="CONCEPT_ID"
        ) from None
    if not target.is_file():
        raise click.ClickException(f"no such concept in bundle: {concept_id!r} ({target})")
    return target


def _edit(action: Any, bundle: str, concept_id: str) -> None:
    """Run a frontmatter mutation, translating a missing frontmatter block into a click error."""
    try:
        action(_concept_path(bundle, concept_id))
    except fields.FrontmatterError as exc:
        raise click.ClickException(str(exc)) from exc


# --------------------------------------------------------------------------------------------
# Output formatting.
# --------------------------------------------------------------------------------------------


def _json_default(obj: Any) -> str:
    """Serialize non-JSON-native values (e.g. datetimes) as strings for ``--json`` output."""
    return str(obj)


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
    if value is None:
        return "NULL"
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=_json_default, ensure_ascii=False)
    return str(value)


def _format_schema(bundle_schema: Any) -> str:
    """Render the detected schema: tables (with columns + types) and the type-name mapping."""
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

    lines.append("\nType mapping (table name <- original type)")
    lines.append("==========================================")
    if bundle_schema.type_mapping:
        map_width = max(len(n) for n in bundle_schema.type_mapping)
        for table_name in sorted(bundle_schema.type_mapping):
            lines.append(
                f"    {table_name.ljust(map_width)}  <-  {bundle_schema.type_mapping[table_name]}"
            )
    else:
        lines.append("    (no concept types detected)")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
