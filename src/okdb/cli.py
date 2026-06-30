"""Command-line interface for okdb.

okdb query "<SQL>" --bundle ./path        # results as a table
okdb query "<SQL>" --bundle ./path --json # results as JSON
okdb schema --bundle ./path               # detected types, table names, columns, mapping
"""

from __future__ import annotations

import json
from typing import Any

import click

import okdb

_BUNDLE_OPTION = click.option(
    "--bundle",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the OKF bundle directory.",
)


@click.group()
@click.version_option(version=okdb.__version__, prog_name="okdb")
def main() -> None:
    """okdb: run real SQL against an OKF bundle (read-only)."""


@main.command()
@click.argument("sql")
@_BUNDLE_OPTION
@click.option("--json", "as_json", is_flag=True, help="Emit results as JSON instead of a table.")
def query(sql: str, bundle: str, as_json: bool) -> None:
    """Execute SQL against the bundle and print the result rows."""
    with okdb.open(bundle) as db:
        rows = db.sql(sql)
    if as_json:
        click.echo(json.dumps(rows, indent=2, default=_json_default, ensure_ascii=False))
    else:
        click.echo(_format_table(rows))


@main.command()
@_BUNDLE_OPTION
def schema(bundle: str) -> None:
    """Print detected types, their normalized table names, columns + types, and the mapping."""
    with okdb.open(bundle) as db:
        bundle_schema = db.schema()
    click.echo(_format_schema(bundle_schema))


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
