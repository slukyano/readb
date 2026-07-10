"""The load path: bundle directory -> in-memory DuckDB + derived schema.

This is the single seam through which a bundle becomes a queryable database. Keeping the whole
load behind :func:`load_bundle` means a future persistent-index cache (a DuckDB file keyed to a
git hash, re-parsing only changed files) can wrap this function without touching callers.

The MVP load is a deliberate two-pass over the bundle:

  Pass 1 (infer): walk the tree, parse every file, route concepts to tables by normalized type,
                  and for each derived table infer the unified column types via the lattice in
                  :mod:`readb.schema`.
  Pass 2 (insert): create each table with explicit DDL, coerce each value to its column's
                   inferred type, and bind-insert the rows.

Derived tables / views:
  * ``__DOCUMENTS``   — one row per concept; the six reserved fields + virtual fields only.
  * one table per type — reserved fields + the union of producer keys for that type.
  * ``__INDEXES``     — one row per reserved ``index.md``; union of their frontmatter fields.
  * ``__LOG``         — one row per reserved ``log.md`` (only created if any exist).
  * ``__UNKNOWNTYPE`` — one row per non-conformant concept (no / non-string / empty-norm type).
  * ``__TAGS``        — a view exploding ``__DOCUMENTS.tags`` for join-style tag filtering.

NON-goals (seams only, not implemented): no on-disk index, no git awareness, no incremental
rebuild, no watcher, no write-back, no body-structure parsing, no schema enforcement.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

import duckdb

from readb.parser import Concept, parse_file
from readb.schema import (
    RESERVED_FIELDS,
    SYSTEM_TABLE_NAMES,
    VIRTUAL_FIELDS,
    VIRTUAL_PATH,
    BundleSchema,
    LType,
    TableSchema,
    as_list_type,
    coerce,
    infer_type,
    normalize_type,
    quote_ident,
    render_ddl,
)

logger = logging.getLogger(__name__)

_DOCUMENTS = "__DOCUMENTS"
_INDEXES = "__INDEXES"
_LOG = "__LOG"
_UNKNOWNTYPE = "__UNKNOWNTYPE"
_TAGS = "__TAGS"
_TAGS_FIELD = "tags"


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

    concepts, indexes, logs = _read_tree(root)
    schema = BundleSchema()
    connection = duckdb.connect(database=":memory:")

    # Route concepts to per-type tables / __UNKNOWNTYPE, resolving normalization collisions.
    by_table, name_to_original, unknown = _route_concepts(concepts, schema)

    # Build every table (pass 1 infer + pass 2 insert happen inside _build_table per table).
    _build_table(connection, _DOCUMENTS, concepts, list(RESERVED_FIELDS), None, schema)
    for table_name in sorted(by_table):
        rows = by_table[table_name]
        columns = list(RESERVED_FIELDS) + _producer_keys(rows)
        _build_table(connection, table_name, rows, columns, name_to_original[table_name], schema)

    unknown_columns = list(RESERVED_FIELDS) + _producer_keys(unknown)
    _build_table(connection, _UNKNOWNTYPE, unknown, unknown_columns, None, schema)

    _build_table(connection, _INDEXES, indexes, _frontmatter_union(indexes), None, schema)
    if logs:
        _build_table(connection, _LOG, logs, _frontmatter_union(logs), None, schema)

    _create_tags_view(connection)

    return connection, schema


# --------------------------------------------------------------------------------------------
# Pass 0: walk the tree and parse every file (permissively).
# --------------------------------------------------------------------------------------------


def _read_tree(root: Path) -> tuple[list[Concept], list[Concept], list[Concept]]:
    """Walk ``root`` and return ``(concepts, indexes, logs)`` as parsed, sorted Concepts.

    Reserved filenames (``index.md`` / ``log.md``) at any level are routed away from concepts.
    Malformed files are skipped (with a warning) by the parser and simply absent from the lists.
    """
    concepts: list[Concept] = []
    indexes: list[Concept] = []
    logs: list[Concept] = []

    for file_path in sorted(root.rglob("*.md"), key=lambda p: p.as_posix()):
        if not file_path.is_file():
            continue
        concept = parse_file(file_path, bundle_root=root)
        if concept is None:
            continue
        name = file_path.name
        if name == "index.md":
            indexes.append(concept)
        elif name == "log.md":
            logs.append(concept)
        else:
            concepts.append(concept)

    return concepts, indexes, logs


# --------------------------------------------------------------------------------------------
# Pass 1a: route concepts to tables, resolving type-name collisions.
# --------------------------------------------------------------------------------------------


def _route_concepts(
    concepts: list[Concept], schema: BundleSchema
) -> tuple[dict[str, list[Concept]], dict[str, str], list[Concept]]:
    """Group concepts by their resolved table name; collect non-conformant ones separately.

    Returns ``(by_table, name_to_original, unknown)`` where ``by_table`` maps a final table name
    to its concepts, ``name_to_original`` maps that name back to the original ``type`` string, and
    ``unknown`` holds concepts with no / non-string / empty-normalized type.
    """
    by_table: dict[str, list[Concept]] = defaultdict(list)
    original_to_name: dict[str, str] = {}
    name_to_original: dict[str, str] = {}
    used_names: set[str] = set(SYSTEM_TABLE_NAMES)
    unknown: list[Concept] = []

    for concept in concepts:  # concepts arrive sorted by path -> stable collision suffixes
        raw_type = concept.frontmatter.get("type")
        if not isinstance(raw_type, str) or normalize_type(raw_type) == "":
            unknown.append(concept)
            continue

        table_name = original_to_name.get(raw_type)
        if table_name is None:
            table_name = _assign_table_name(raw_type, used_names, schema)
            original_to_name[raw_type] = table_name
            name_to_original[table_name] = raw_type
        by_table[table_name].append(concept)

    schema.type_mapping = dict(name_to_original)
    return by_table, name_to_original, unknown


def _assign_table_name(raw_type: str, used_names: set[str], schema: BundleSchema) -> str:
    """Pick a unique table name for ``raw_type``, suffixing ``_2``, ``_3``, ... on collision."""
    base = normalize_type(raw_type)
    name = base
    if name in used_names:
        suffix = 2
        while f"{base}_{suffix}" in used_names:
            suffix += 1
        name = f"{base}_{suffix}"
        message = (
            f"type-name collision: {raw_type!r} normalizes to {base!r}, "
            f"already taken by a distinct type; using table name {name!r}"
        )
        logger.warning(message)
        schema.warnings.append(message)
    used_names.add(name)
    return name


# --------------------------------------------------------------------------------------------
# Pass 1b + 2: infer column types, then create the table and insert coerced rows.
# --------------------------------------------------------------------------------------------


def _build_table(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    rows: list[Concept],
    frontmatter_columns: list[str],
    original_type: str | None,
    schema: BundleSchema,
) -> None:
    """Infer types for ``frontmatter_columns``, create ``table_name``, and insert ``rows``.

    Virtual columns (``__path``, ``__name``, ``__body``, ``__raw``) are always appended as
    VARCHAR. The table
    is always created even when empty, so queries against it never fail.
    """
    column_types: dict[str, LType] = {}
    for column in frontmatter_columns:
        inferred = infer_type(concept.frontmatter.get(column) for concept in rows)
        if column == _TAGS_FIELD:
            inferred = as_list_type(inferred)  # tags is semantically a list (singleton-promote)
        column_types[column] = inferred

    column_ddl = [f"{quote_ident(c)} {render_ddl(column_types[c])}" for c in frontmatter_columns]
    column_ddl += [f"{quote_ident(v)} VARCHAR" for v in VIRTUAL_FIELDS]
    connection.execute(f"CREATE TABLE {quote_ident(table_name)} ({', '.join(column_ddl)})")

    if rows:
        bound_rows = [_bind_row(concept, frontmatter_columns, column_types) for concept in rows]
        placeholders = ", ".join("?" * (len(frontmatter_columns) + len(VIRTUAL_FIELDS)))
        connection.executemany(
            f"INSERT INTO {quote_ident(table_name)} VALUES ({placeholders})", bound_rows
        )

    table_schema = TableSchema(table_name=table_name, original_type=original_type)
    for column in frontmatter_columns:
        table_schema.columns[column] = render_ddl(column_types[column])
    for virtual in VIRTUAL_FIELDS:
        table_schema.columns[virtual] = "VARCHAR"
    schema.tables[table_name] = table_schema


def _bind_row(
    concept: Concept, frontmatter_columns: list[str], column_types: dict[str, LType]
) -> list[object]:
    """Build one positional row: coerced frontmatter values followed by the virtual fields."""
    row: list[object] = [
        coerce(concept.frontmatter.get(column), column_types[column])
        for column in frontmatter_columns
    ]
    row.append(concept.path)  # __path
    row.append(concept.name)  # __name
    row.append(concept.body)  # __body
    row.append(concept.raw)  # __raw
    return row


# --------------------------------------------------------------------------------------------
# Column-set helpers.
# --------------------------------------------------------------------------------------------

_NON_PRODUCER_KEYS: frozenset[str] = frozenset(RESERVED_FIELDS) | frozenset(VIRTUAL_FIELDS)


def _producer_keys(rows: list[Concept]) -> list[str]:
    """Sorted union of non-reserved, non-virtual frontmatter keys across ``rows``."""
    keys: set[str] = set()
    for concept in rows:
        for key in concept.frontmatter:
            if isinstance(key, str) and key not in _NON_PRODUCER_KEYS:
                keys.add(key)
    return sorted(keys)


def _frontmatter_union(rows: list[Concept]) -> list[str]:
    """Sorted union of *all* frontmatter keys across ``rows`` (for __INDEXES / __LOG).

    Virtual field names are excluded to avoid colliding with the injected virtual columns.
    """
    virtual = frozenset(VIRTUAL_FIELDS)
    keys: set[str] = set()
    for concept in rows:
        for key in concept.frontmatter:
            if isinstance(key, str) and key not in virtual:
                keys.add(key)
    return sorted(keys)


# --------------------------------------------------------------------------------------------
# The __TAGS view.
# --------------------------------------------------------------------------------------------


def _create_tags_view(connection: duckdb.DuckDBPyConnection) -> None:
    """Create ``__TAGS(concept_path, tag)`` by exploding ``__DOCUMENTS.tags``.

    ``tags`` is always a LIST column on ``__DOCUMENTS`` (see the lattice's tags rule), so the
    explode is well-defined. NULL and empty-list tag values simply contribute no rows.
    """
    path_col = quote_ident(VIRTUAL_PATH)
    tags_col = quote_ident(_TAGS_FIELD)
    connection.execute(
        f"""
        CREATE VIEW {quote_ident(_TAGS)} AS
        SELECT {path_col} AS concept_path, unnest({tags_col}) AS tag
        FROM {quote_ident(_DOCUMENTS)}
        WHERE {tags_col} IS NOT NULL
        """
    )
