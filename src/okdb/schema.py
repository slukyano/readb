"""Schema derivation: type-name normalization and the column-type unification lattice.

Two responsibilities:

1. ``normalize_type`` maps a frontmatter ``type`` string to a SQL table name, tracking the
   reverse mapping and collision-driven suffixes.
2. The column-type lattice infers ONE losslessly-holding DuckDB type per column from all
   observed values, with JSON as the universal fallback at the top of the lattice.

These are pure, side-effect-free building blocks consumed by :mod:`okdb.loader`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Reserved OKF frontmatter fields, guaranteed (as columns) on every table.
RESERVED_FIELDS: tuple[str, ...] = (
    "type",
    "title",
    "description",
    "resource",
    "tags",
    "timestamp",
)

# Virtual fields injected on every table.
VIRTUAL_PATH = "__path"
VIRTUAL_BODY = "__body"

# Reserved filenames that are NOT concept docs.
RESERVED_FILENAMES: frozenset[str] = frozenset({"index.md", "log.md"})


@dataclass
class TableSchema:
    """Inferred schema for one detected type (or system table)."""

    table_name: str
    original_type: str | None
    columns: dict[str, str] = field(default_factory=dict)  # column name -> DuckDB type


@dataclass
class BundleSchema:
    """The full set of tables derived from a bundle, plus the type-name mapping."""

    tables: dict[str, TableSchema] = field(default_factory=dict)
    # normalized table name -> original frontmatter `type` string
    type_mapping: dict[str, str] = field(default_factory=dict)


def normalize_type(raw_type: str) -> str:
    """Normalize a frontmatter ``type`` string to a candidate SQL table name.

    Rules:
        - Lowercase, then delete every character outside ``[a-z0-9_]``.
        - If the result starts with a digit, prefix ``_``.
        - If the result is empty, return ``""`` (caller routes the doc to ``__UNKNOWNTYPE``).

    Collision resolution (``_2``, ``_3``, ... on distinct original types) is the caller's job,
    since it requires cross-document state.
    """
    raise NotImplementedError
