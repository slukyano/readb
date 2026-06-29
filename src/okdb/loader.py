"""The load path: bundle directory -> in-memory DuckDB + derived schema.

This is the single seam through which a bundle becomes a queryable database. Keeping the whole
load behind :func:`load_bundle` means a future persistent-index cache (a DuckDB file keyed to a
git hash, re-parsing only changed files) can wrap this function without touching callers.

The MVP load is a deliberate two-pass over the bundle:

  Pass 1 (infer): walk the tree, parse every concept, and for each derived table infer the
                  unified column types via the lattice in :mod:`okdb.schema`.
  Pass 2 (insert): coerce each value to its column's inferred type and insert into DuckDB.

NON-goals (seams only, not implemented): no on-disk index, no git awareness, no incremental
rebuild, no watcher, no write-back, no body-structure parsing, no schema enforcement.
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from okdb.schema import BundleSchema

logger = logging.getLogger(__name__)


def load_bundle(bundle_path: str) -> tuple[duckdb.DuckDBPyConnection, BundleSchema]:
    """Read and parse the whole bundle, returning a populated DuckDB connection and its schema.

    Strictly read-only with respect to the bundle: no files are created or modified. The current
    implementation re-reads and re-parses every file on each call (milliseconds at hundreds of
    files); a cache may later wrap this seam.

    Raises:
        FileNotFoundError: if ``bundle_path`` does not exist or is not a directory.
    """
    root = Path(bundle_path)
    if not root.is_dir():
        raise FileNotFoundError(f"bundle path is not a directory: {bundle_path}")
    raise NotImplementedError
