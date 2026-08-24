"""The queryable database: a thin, read-only wrapper around an in-memory DuckDB connection.

A :class:`Database` is produced by loading a bundle (see :mod:`readb.loader`) and registering
the derived tables/views (``__DOCUMENTS``, per-type tables, ``__INDEXES``, ``__UNKNOWNTYPE``,
``__LOG``, ``__TAGS``). Callers run SQL via :meth:`Database.sql`; DuckDB does all parsing and
planning. The wrapper is read-only with respect to the source bundle — it never writes files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from readb.errors import translate

if TYPE_CHECKING:
    import duckdb

    from readb.schema import BundleSchema


class Database:
    """A read-only SQL handle over a loaded OKF bundle."""

    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        schema: BundleSchema,
        bundle_path: str = "",
    ) -> None:
        self._conn = connection
        self._schema = schema
        self._bundle_path = bundle_path

    @classmethod
    def from_bundle(cls, bundle_path: str, *, cache: bool = True) -> Database:
        """Load ``bundle_path`` and return a Database.

        Loading goes through :mod:`readb.cache`, which serves an unchanged bundle from a
        materialized DuckDB file when the user consented to one with ``readb init`` (ADR 0006),
        and otherwise calls the load seam in :mod:`readb.loader` directly. ``cache=False``
        always loads from source.
        """
        from readb.cache import load

        connection, schema = load(bundle_path, enabled=cache)
        return cls(connection, schema, bundle_path)

    def sql(self, query: str, parameters: list[Any] | None = None) -> list[dict[str, Any]]:
        """Execute ``query`` against the loaded bundle and return rows as dicts.

        DuckDB parses and plans the SQL; readb never does. Optional positional ``parameters`` are
        bound through DuckDB's prepared-statement interface. A statement that returns no result
        set (rare for this read-only layer) yields an empty list.
        """
        columns, rows = self.sql_table(query, parameters)
        return [dict(zip(columns, row, strict=True)) for row in rows]

    def sql_table(
        self, query: str, parameters: list[Any] | None = None
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        """Execute ``query`` and return ``(column_names, rows)`` — columns survive empty results.

        The tabular sibling of :meth:`sql`: a zero-row result still carries its column names
        (so e.g. csv output can print a header), which the dict-shaped ``sql`` cannot convey.
        A statement that returns no result set yields ``([], [])``.
        """
        import duckdb

        try:
            cursor = (
                self._conn.execute(query, parameters) if parameters else self._conn.execute(query)
            )
        except duckdb.Error as exc:
            # readb knows the bundle's tables; DuckDB answers from its own catalog (032).
            raise translate(
                exc, tables=self._table_names(), bundle_path=self._bundle_path
            ) from None
        if cursor.description is None:
            return [], []
        columns = [descriptor[0] for descriptor in cursor.description]
        return columns, cursor.fetchall()

    def _table_names(self) -> list[str]:
        """Every relation a query could name, views included — asked of DuckDB, not inferred.

        ``BundleSchema`` covers the tables the loader built but not ``__TAGS``, which is a view;
        the catalog knows both. Falls back to the schema if the catalog query itself fails,
        since this runs while another error is already being reported.
        """
        try:
            rows = self._conn.execute(
                "SELECT table_name FROM duckdb_tables() "
                "UNION ALL SELECT view_name FROM duckdb_views() WHERE NOT internal"
            ).fetchall()
        except Exception:  # noqa: BLE001 - never let error reporting raise its own error
            return list(self._schema.tables)
        # The cache's own bookkeeping lives in the same database on a hit; it is readb's, not
        # the bundle's, and naming it here would be as unhelpful as DuckDB's `duckdb_indexes`.
        return [row[0] for row in rows if not row[0].startswith("__readb_")]

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
