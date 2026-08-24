"""Errors readb raises in place of DuckDB's, where readb knows more than the engine does.

DuckDB answers a mistyped table name from its own catalog, which is why a bundle query can be
told "Did you mean \"duckdb_indexes\"?" — a table that exists in no bundle and answers no
question (backlog task ``032-unknown-table-error``). readb holds the list of tables it built,
so it can answer with the truth instead.

Every error here subclasses the DuckDB exception it replaces, so code that already catches
``duckdb.CatalogException`` keeps working unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

import duckdb

# DuckDB's own phrasing, matched narrowly: anything else is passed through untouched.
_UNKNOWN_TABLE = re.compile(r"Table with name ([^\s]+) does not exist")
_UNKNOWN_COLUMN = re.compile(r"Referenced column .* not found")

_MAX_LISTED_TABLES = 25


def _order_tables(tables: Sequence[str]) -> list[str]:
    """Concept tables first, then the system ones — a mistyped name is almost always a type."""
    concept = sorted(t for t in tables if not t.startswith("__"))
    system = sorted(t for t in tables if t.startswith("__"))
    return concept + system


class UnknownTableError(duckdb.CatalogException):
    """A query named a table this bundle does not have.

    Carries the bundle's real table list so a caller can render its own message; the default
    rendering names every table and points at ``readb schema``.
    """

    def __init__(self, table: str, tables: Sequence[str], bundle_path: str) -> None:
        self.table = table
        self.tables = _order_tables(tables)
        self.bundle_path = bundle_path
        super().__init__(self.render())

    def render(self, *, show_bundle: bool = True) -> str:
        listed = self.tables[:_MAX_LISTED_TABLES]
        elided = len(self.tables) - len(listed)
        names = ", ".join(listed) if listed else "(none — the bundle has no documents)"
        if elided:
            names += f", … and {elided} more"
        command = "readb schema"
        if show_bundle and self.bundle_path:
            command += f" --bundle {self.bundle_path}"
        return (
            f"no table named {self.table!r} in this bundle.\n"
            f"Tables: {names}.\n"
            f"Run '{command}' for their columns."
        )


def translate(exc: duckdb.Error, *, tables: Sequence[str], bundle_path: str) -> duckdb.Error:
    """Return the error readb wants to raise for ``exc`` — often ``exc`` itself.

    Only two shapes are rewritten. An unknown *table* is replaced outright, because DuckDB's
    suggestion is drawn from its own catalog and points outside the bundle. An unknown *column*
    keeps DuckDB's message, whose candidate bindings come from the right table and are worth
    reading, and gains one line pointing at ``readb schema``.
    """
    message = str(exc)
    if isinstance(exc, duckdb.CatalogException):
        match = _UNKNOWN_TABLE.search(message)
        if match:
            return UnknownTableError(match.group(1), tables, bundle_path)
    if isinstance(exc, duckdb.BinderException) and _UNKNOWN_COLUMN.search(message):
        command = "readb schema" + (f" --bundle {bundle_path}" if bundle_path else "")
        return duckdb.BinderException(f"{message}\nRun '{command}' for this bundle's columns.")
    return exc
