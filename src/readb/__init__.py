"""readb: a transparent, read-only SQL query layer over Open Knowledge Format (OKF) bundles.

Public API
----------
    import readb

    db = readb.open("./path/to/bundle")   # builds an in-memory DuckDB, no files written
    rows = db.sql("SELECT * FROM __DOCUMENTS WHERE type = 'Metric'")

The bundle is loaded into an embedded DuckDB engine which executes the SQL directly;
readb never parses or plans SQL itself. All operations are strictly read-only with respect
to the source bundle.
"""

from __future__ import annotations

from readb.database import Database

__version__ = "0.0.1"

__all__ = ["Database", "open", "__version__"]


def open(bundle_path: str) -> Database:  # noqa: A001 - mirrors the sqlite3/duckdb `open` idiom
    """Open an OKF bundle and return a queryable, read-only :class:`Database`.

    Builds an in-memory DuckDB from the markdown-with-frontmatter files under
    ``bundle_path``. No files are created or modified anywhere in the bundle.

    Args:
        bundle_path: Path to the root directory of an OKF bundle.

    Returns:
        A :class:`Database` ready to accept ``.sql(...)`` queries.
    """
    return Database.from_bundle(bundle_path)
