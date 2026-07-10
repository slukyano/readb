"""Schema derivation: type-name normalization and the column-type unification lattice.

Two responsibilities:

1. ``normalize_type`` maps a frontmatter ``type`` string to a SQL table name, tracking the
   reverse mapping and collision-driven suffixes (collisions are resolved in :mod:`readb.loader`,
   which holds the cross-document state).
2. The column-type lattice infers ONE losslessly-holding DuckDB type per column from all
   observed values, with JSON as the universal fallback at the top of the lattice.

These are pure, side-effect-free building blocks consumed by :mod:`readb.loader`.

The lattice
-----------
An internal :class:`LType` describes a column's unified shape. Values are classified into a
*narrowest* LType (:func:`type_of_value`); LTypes are combined pairwise (:func:`unify`) so the
result losslessly holds both operands, following the brief's narrowest-fit-wins rules:

* ``NULL`` is the bottom (absent / unconstrained); it never constrains the other operand.
* ``int`` mixed with ``float`` widens to ``DOUBLE``.
* A scalar mixed with a LIST promotes the scalar to a singleton list; element types unify.
* Maps with a *consistent* key set become a STRUCT; an inconsistent key set falls to JSON.
* ``JSON`` is the top and universal fallback: any combination that does not reduce to a single
  engine type stores the raw parsed value as a JSON document. Nothing is dropped.

Temporal handling: YAML may parse unquoted ISO values into ``date``/``datetime`` objects.
``date`` -> DATE and naive ``datetime`` -> TIMESTAMP (both bind to DuckDB without extra deps).
A timezone-aware ``datetime`` would require ``pytz`` to bind, so it routes to the JSON fallback
(serialized via ISO-8601, which is lossless) to keep the dependency surface minimal.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any

# Reserved OKF frontmatter fields, guaranteed (as columns) on every concept table.
RESERVED_FIELDS: tuple[str, ...] = (
    "type",
    "title",
    "description",
    "resource",
    "tags",
    "timestamp",
)

# Virtual fields injected on every table.
VIRTUAL_PATH = "__path"  # concept path relative to bundle root, WITH the .md suffix
VIRTUAL_ID = "__id"  # Concept ID: __path minus the .md suffix
VIRTUAL_BODY = "__body"  # the markdown body, frontmatter stripped
VIRTUAL_FIELDS: tuple[str, ...] = (VIRTUAL_PATH, VIRTUAL_ID, VIRTUAL_BODY)

# Reserved filenames that are NOT concept docs.
RESERVED_FILENAMES: frozenset[str] = frozenset({"index.md", "log.md"})

# System table / view names (lower-cased; DuckDB identifiers are case-insensitive).
SYSTEM_TABLE_NAMES: frozenset[str] = frozenset(
    {"__documents", "__indexes", "__log", "__unknowntype", "__tags"}
)


# --------------------------------------------------------------------------------------------
# Type-name normalization
# --------------------------------------------------------------------------------------------

_INVALID_IDENT_CHARS = re.compile(r"[^a-z0-9_]")


def normalize_type(raw_type: str) -> str:
    """Normalize a frontmatter ``type`` string to a candidate SQL table name.

    Rules:
        - Lowercase, then delete every character outside ``[a-z0-9_]``.
        - If the result starts with a digit, prefix ``_``.
        - If the result is empty, return ``""`` (caller routes the doc to ``__UNKNOWNTYPE``).

    Collision resolution (``_2``, ``_3``, ... on distinct original types) is the caller's job,
    since it requires cross-document state. See :mod:`readb.loader`.

    Examples:
        >>> normalize_type("Big %// Table")
        'bigtable'
        >>> normalize_type("3D Model")
        '_3dmodel'
        >>> normalize_type("%%%")
        ''
    """
    collapsed = _INVALID_IDENT_CHARS.sub("", raw_type.lower())
    if not collapsed:
        return ""
    if collapsed[0].isdigit():
        return "_" + collapsed
    return collapsed


# --------------------------------------------------------------------------------------------
# The column-type lattice
# --------------------------------------------------------------------------------------------


class Kind(StrEnum):
    """The kinds of node in the type lattice."""

    NULL = "null"  # bottom: absent / unconstrained
    BOOLEAN = "boolean"
    BIGINT = "bigint"
    DOUBLE = "double"
    VARCHAR = "varchar"
    DATE = "date"
    TIMESTAMP = "timestamp"
    JSON = "json"  # top: universal fallback
    LIST = "list"
    STRUCT = "struct"


_SCALAR_KINDS: frozenset[Kind] = frozenset(
    {Kind.BOOLEAN, Kind.BIGINT, Kind.DOUBLE, Kind.VARCHAR, Kind.DATE, Kind.TIMESTAMP}
)


@dataclass(frozen=True)
class LType:
    """A node in the column-type lattice.

    ``element`` is set only for LIST; ``fields`` (an ordered tuple of ``(name, LType)``) only for
    STRUCT. All other kinds are leaf scalars (or NULL/JSON sentinels).
    """

    kind: Kind
    element: LType | None = None
    fields: tuple[tuple[str, LType], ...] | None = None


# Scalar / sentinel singletons.
NULL = LType(Kind.NULL)
BOOLEAN = LType(Kind.BOOLEAN)
BIGINT = LType(Kind.BIGINT)
DOUBLE = LType(Kind.DOUBLE)
VARCHAR = LType(Kind.VARCHAR)
DATE = LType(Kind.DATE)
TIMESTAMP = LType(Kind.TIMESTAMP)
JSON = LType(Kind.JSON)

# Rendering for leaf kinds. NULL (an all-null column) defaults to VARCHAR.
_LEAF_DDL: dict[Kind, str] = {
    Kind.NULL: "VARCHAR",
    Kind.BOOLEAN: "BOOLEAN",
    Kind.BIGINT: "BIGINT",
    Kind.DOUBLE: "DOUBLE",
    Kind.VARCHAR: "VARCHAR",
    Kind.DATE: "DATE",
    Kind.TIMESTAMP: "TIMESTAMP",
    Kind.JSON: "JSON",
}


def type_of_value(value: Any) -> LType:
    """Classify a single Python value (as parsed from YAML) into its narrowest LType."""
    if value is None:
        return NULL
    if isinstance(value, bool):  # bool is a subclass of int; must precede the int check
        return BOOLEAN
    if isinstance(value, int):
        return BIGINT
    if isinstance(value, float):
        return DOUBLE
    if isinstance(value, str):
        return VARCHAR
    if isinstance(value, datetime):  # datetime is a subclass of date; must precede date
        return TIMESTAMP if value.tzinfo is None else JSON
    if isinstance(value, date):
        return DATE
    if isinstance(value, list):
        return LType(Kind.LIST, element=infer_type(value))
    if isinstance(value, dict):
        sorted_fields = tuple(
            sorted(((str(k), type_of_value(v)) for k, v in value.items()), key=lambda kv: kv[0])
        )
        return LType(Kind.STRUCT, fields=sorted_fields)
    return JSON


def unify(a: LType, b: LType) -> LType:
    """Combine two LTypes into the narrowest LType that losslessly holds both."""
    if a.kind is Kind.NULL:
        return b
    if b.kind is Kind.NULL:
        return a
    if a == b:
        return a
    # int mixed with float -> double.
    if {a.kind, b.kind} <= {Kind.BIGINT, Kind.DOUBLE}:
        return DOUBLE
    # list + list -> list of unified elements.
    if a.kind is Kind.LIST and b.kind is Kind.LIST:
        return LType(Kind.LIST, element=unify(a.element or NULL, b.element or NULL))
    # scalar + list -> promote the scalar to a singleton list, then unify elements.
    if a.kind is Kind.LIST and b.kind in _SCALAR_KINDS:
        return LType(Kind.LIST, element=unify(a.element or NULL, b))
    if b.kind is Kind.LIST and a.kind in _SCALAR_KINDS:
        return LType(Kind.LIST, element=unify(b.element or NULL, a))
    # struct + struct -> struct iff the key sets match exactly; otherwise JSON.
    if a.kind is Kind.STRUCT and b.kind is Kind.STRUCT:
        a_fields = a.fields or ()
        b_fields = b.fields or ()
        if tuple(n for n, _ in a_fields) == tuple(n for n, _ in b_fields):
            merged = tuple(
                (n, unify(ta, tb)) for (n, ta), (_, tb) in zip(a_fields, b_fields, strict=True)
            )
            return LType(Kind.STRUCT, fields=merged)
        return JSON
    # Anything else (incompatible scalars, scalar+struct, list+struct, anything+JSON) -> JSON.
    return JSON


def infer_type(values: Any) -> LType:
    """Infer the unified LType across an iterable of Python values (Nones do not constrain)."""
    result = NULL
    for value in values:
        result = unify(result, type_of_value(value))
    return result


def as_list_type(t: LType) -> LType:
    """Force ``t`` to be a LIST (wrapping a scalar/struct/json element type in a singleton list).

    Used for the OKF-reserved ``tags`` field, which is semantically a list: bare scalars are
    promoted to singletons. A column that is already a LIST is returned unchanged.
    """
    if t.kind is Kind.LIST:
        return t
    return LType(Kind.LIST, element=t)


def render_ddl(t: LType) -> str:
    """Render an LType as a DuckDB column type expression."""
    if t.kind is Kind.LIST:
        return render_ddl(t.element or NULL) + "[]"
    if t.kind is Kind.STRUCT:
        inner = ", ".join(f"{quote_ident(name)} {render_ddl(ft)}" for name, ft in (t.fields or ()))
        return f"STRUCT({inner})"
    return _LEAF_DDL[t.kind]


def coerce(value: Any, t: LType) -> Any:
    """Coerce a raw Python value to a representation DuckDB will bind for column type ``t``.

    Lossless by construction: incompatible shapes were unified to JSON upstream, so this never
    discards data. JSON columns receive a JSON *string*; LIST columns a Python ``list``; STRUCT
    columns a Python ``dict``.
    """
    if value is None:
        return None
    kind = t.kind
    if kind is Kind.JSON:
        return json.dumps(value, default=_json_default, ensure_ascii=False)
    if kind is Kind.LIST:
        element = t.element or NULL
        items = value if isinstance(value, list) else [value]  # promote scalar -> singleton
        return [coerce(item, element) for item in items]
    if kind is Kind.STRUCT:
        if not isinstance(value, dict):
            return {name: None for name, _ in (t.fields or ())}
        by_str_key = {str(k): v for k, v in value.items()}
        return {name: coerce(by_str_key.get(name), ft) for name, ft in (t.fields or ())}
    if kind is Kind.DOUBLE:
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    # BOOLEAN, BIGINT, VARCHAR, DATE, TIMESTAMP, and NULL(->VARCHAR): bind as-is.
    return value


def _json_default(obj: Any) -> Any:
    """Fallback serializer for the JSON column: ISO-8601 for temporals, str() otherwise."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return str(obj)


def quote_ident(name: str) -> str:
    """Quote a SQL identifier for safe interpolation into DDL."""
    return '"' + name.replace('"', '""') + '"'


# --------------------------------------------------------------------------------------------
# Public schema description (consumed by `readb schema`)
# --------------------------------------------------------------------------------------------


@dataclass
class TableSchema:
    """Inferred schema for one detected type (or system table)."""

    table_name: str
    original_type: str | None  # original frontmatter `type` string, or None for system tables
    columns: dict[str, str] = field(default_factory=dict)  # column name -> rendered DuckDB type


@dataclass
class BundleSchema:
    """The full set of tables derived from a bundle, plus the type-name mapping and warnings."""

    tables: dict[str, TableSchema] = field(default_factory=dict)
    # normalized table name -> original frontmatter `type` string
    type_mapping: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
