"""The queryable database: a thin, read-only wrapper around an in-memory DuckDB connection.

A :class:`Database` is produced by loading a bundle (see :mod:`okdb.loader`) and registering
the derived tables/views (``__DOCUMENTS``, per-type tables, ``__INDEXES``, ``__UNKNOWNTYPE``,
``__LOG``, ``__TAGS``). Callers run SQL via :meth:`Database.sql`; DuckDB does all parsing and
planning. The wrapper is read-only with respect to the source bundle — it never writes files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import duckdb

    from okdb.schema import BundleSchema


class Database:
    """A read-only SQL handle over a loaded OKF bundle."""

    def __init__(self, connection: duckdb.DuckDBPyConnection, schema: BundleSchema) -> None:
        self._conn = connection
        self._schema = schema

    @classmethod
    def from_bundle(cls, bundle_path: str) -> Database:
        """Load ``bundle_path`` into a fresh in-memory DuckDB and return a Database.

        Implementation lives in :mod:`okdb.loader` (the load seam), so a persistent-index
        cache can later wrap loading without touching this class.
        """
        from okdb.loader import load_bundle

        connection, schema = load_bundle(bundle_path)
        return cls(connection, schema)

    def sql(self, query: str, parameters: list[Any] | None = None) -> list[dict[str, Any]]:
        """Execute ``query`` against the loaded bundle and return rows as dicts.

        DuckDB parses and plans the SQL; okdb never does. Optional positional ``parameters`` are
        bound through DuckDB's prepared-statement interface. A statement that returns no result
        set (rare for this read-only layer) yields an empty list.
        """
        cursor = self._conn.execute(query, parameters) if parameters else self._conn.execute(query)
        if cursor.description is None:
            return []
        columns = [descriptor[0] for descriptor in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def schema(self) -> BundleSchema:
        """Return the detected schema: types, normalized table names, columns + inferred types."""
        return self._schema

    def close(self) -> None:
        """Close the underlying DuckDB connection."""
        self._conn.close()

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
