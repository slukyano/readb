"""Command-line interface for okdb.

okdb query "<SQL>" --bundle ./path        # results as a table
okdb query "<SQL>" --bundle ./path --json # results as JSON
okdb schema --bundle ./path               # detected types, table names, columns, mapping
"""

from __future__ import annotations

import click

import okdb


@click.group()
@click.version_option(version=okdb.__version__, prog_name="okdb")
def main() -> None:
    """okdb: run real SQL against an OKF bundle (read-only)."""


@main.command()
@click.argument("sql")
@click.option(
    "--bundle",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the OKF bundle directory.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit results as JSON instead of a table.")
def query(sql: str, bundle: str, as_json: bool) -> None:
    """Execute SQL against the bundle and print the result rows."""
    raise NotImplementedError


@main.command()
@click.option(
    "--bundle",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the OKF bundle directory.",
)
def schema(bundle: str) -> None:
    """Print detected types, their normalized table names, columns + types, and the mapping."""
    raise NotImplementedError


if __name__ == "__main__":
    main()
