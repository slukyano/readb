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

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _installed_version

from readb.database import Database

try:
    # Derived, never written down twice: pyproject.toml is the single version source, and a
    # literal here would silently disagree with the distribution the moment one is bumped
    # without the other — which is invisible to tests and shows up only as `readb --version`
    # reporting the wrong number from an installed build.
    __version__ = _installed_version("readb")
except PackageNotFoundError:  # a source tree that was never installed
    __version__ = "0+unknown"

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
