"""The persistent index cache: a materialized DuckDB file beside the registry (ADR 0006).

Loading a bundle re-reads and re-parses every file, which costs 3.9 s on a 6000-concept bundle
and is paid *per invocation*. This module wraps :func:`readb.loader.load_bundle` — the seam the
design brief left for exactly this — and serves an unchanged bundle from a materialized DuckDB
file in about 4 ms, independent of bundle size.

Three rules from ADR 0006 shape everything here:

* **Consent.** A cache is written only under a ``.readb/`` directory the user created with
  ``readb init``. No registry means no cache and no writes anywhere.
* **Never stale, never fatal.** Change detection is a per-file stat manifest; a file whose stat
  moved is *hashed* before it is believed changed, so touching files rewrites nothing. Any
  failure to read or write a cache is a miss, never an error a query sees.
* **Incremental where it is provably safe.** A small, local change is applied to a copy of the
  cache; anything that could make the cached database differ from a fresh load falls back to a
  full rebuild. That list of conditions is the correctness argument, and it lives in
  :func:`_apply_incremental`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from readb import registry
from readb.loader import _suppress_pandas_probe, load_bundle
from readb.parser import Concept, parse_file
from readb.schema import (
    NULL,
    RESERVED_FIELDS,
    VIRTUAL_FIELDS,
    BundleSchema,
    LType,
    TableSchema,
    as_list_type,
    coerce,
    decode_ltype,
    evidence_key,
    normalize_type,
    quote_ident,
    render_ddl,
    unify,
)

logger = logging.getLogger(__name__)

CACHE_DIR_NAME = "cache"
META_TABLE = "__readb_meta"

# DuckDB's default block size leaves a 34-concept bundle occupying 4.9 MB; 16 KB blocks make the
# same cache 1.5 MB and cost nothing at scale (22.4 MB against 22.0 MB at 6000 concepts).
BLOCK_SIZE = 16384

# Applying thousands of row deltas is slower than a bulk load, so a large *confirmed* change set
# rebuilds instead. Files whose mtime merely moved are filtered out before this is counted.
INCREMENTAL_SHARE = 0.25
INCREMENTAL_FLOOR = 500

_CACHE_FORMAT = "1"

Evidence = dict[str, dict[str, "Counter[str]"]]


# --------------------------------------------------------------------------------------------
# The manifest: what the bundle looked like when the cache was written.
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FileStat:
    """One file's identity as the filesystem reports it — never a directory's."""

    size: int
    mtime_ns: int


def scan(root: Path) -> dict[str, FileStat]:
    """Walk ``root`` as the loader does, collecting each file's own size and mtime.

    ``os.scandir`` rather than ``rglob`` + ``stat``: measured at 1.7-2.1 us per file, linear to
    20000 files, and a strict subset of the open-and-read an uncached load performs anyway.
    """
    found: dict[str, FileStat] = {}
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:  # a directory that vanished or cannot be read is not fatal
            logger.debug("cache: cannot scan %s (%s)", directory, exc)
            continue
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                if entry.name != registry.MARKER_DIR:
                    stack.append(Path(entry.path))
            elif entry.name.endswith(".md"):
                try:
                    stat = entry.stat()
                except OSError:
                    continue
                relative = Path(entry.path).relative_to(root).as_posix()
                found[relative] = FileStat(size=stat.st_size, mtime_ns=stat.st_mtime_ns)
    return found


def manifest_key(entries: dict[str, FileStat], bundle_root: Path) -> str:
    """Identity of one bundle state: its files, this readb, this duckdb."""
    digest = hashlib.sha256()
    digest.update(f"{_CACHE_FORMAT}\0{_readb_version()}\0{duckdb.__version__}\0".encode())
    digest.update(f"{bundle_root.resolve().as_posix()}\0".encode())
    for path in sorted(entries):
        stat = entries[path]
        digest.update(f"{path}\0{stat.size}\0{stat.mtime_ns}\0".encode())
    return digest.hexdigest()[:32]


def _readb_version() -> str:
    from readb import __version__

    return __version__


def _slug(bundle_root: Path) -> str:
    """A stable, readable file-name stem for one bundle path."""
    resolved = bundle_root.resolve()
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in resolved.name) or "bundle"
    return f"{safe}-{hashlib.sha256(resolved.as_posix().encode()).hexdigest()[:8]}"


# --------------------------------------------------------------------------------------------
# Consent: where a cache may live, and whether it may exist at all.
# --------------------------------------------------------------------------------------------


def cache_dir_for(bundle_path: str | Path) -> Path | None:
    """The directory this bundle's cache belongs in, or None when caching is not consented to.

    Consent is the ``.readb/`` directory ``readb init`` writes (ADR 0004). Without one readb
    writes nothing, anywhere — the read-only promise, restated.
    """
    root = registry.find_registry(Path(bundle_path))
    if root is None:
        return None
    if _cache_disabled(root):
        return None
    return root / registry.MARKER_DIR / CACHE_DIR_NAME


def _cache_disabled(root: Path) -> bool:
    """``cache = false`` in the registry config turns the cache off for every bundle under it."""
    try:
        import tomllib

        with registry.config_path(root).open("rb") as handle:
            return tomllib.load(handle).get("cache") is False
    except (OSError, ValueError):
        return False


# --------------------------------------------------------------------------------------------
# Persisting what a cached database cannot rediscover.
# --------------------------------------------------------------------------------------------


def _schema_to_json(schema: BundleSchema) -> str:
    return json.dumps(
        {
            "tables": {
                name: {
                    "table_name": table.table_name,
                    "original_type": table.original_type,
                    "columns": dict(table.columns),
                }
                for name, table in schema.tables.items()
            },
            "type_mapping": dict(schema.type_mapping),
            "warnings": list(schema.warnings),
        }
    )


def _schema_from_json(payload: str) -> BundleSchema:
    data = json.loads(payload)
    schema = BundleSchema()
    for name, table in data["tables"].items():
        restored = TableSchema(table_name=table["table_name"], original_type=table["original_type"])
        restored.columns.update(table["columns"])
        schema.tables[name] = restored
    schema.type_mapping.update(data["type_mapping"])
    schema.warnings.extend(data["warnings"])
    return schema


def _evidence_to_json(evidence: Evidence) -> str:
    return json.dumps(
        {
            table: {column: dict(counts) for column, counts in columns.items()}
            for table, columns in evidence.items()
        }
    )


def _evidence_from_json(payload: str) -> Evidence:
    return {
        table: {column: Counter(counts) for column, counts in columns.items()}
        for table, columns in json.loads(payload).items()
    }


def _column_ltype(counts: Counter[str], column: str) -> LType:
    """A column's unified type, recomputed from evidence exactly as a fresh load infers it."""
    inferred = NULL
    for key, count in counts.items():
        if count > 0:
            inferred = unify(inferred, decode_ltype(json.loads(key)))
    if column == "tags":
        inferred = as_list_type(inferred)  # tags is semantically a list (singleton-promote)
    return inferred


# --------------------------------------------------------------------------------------------
# Reading a cache.
# --------------------------------------------------------------------------------------------


def _open_cache(
    path: Path, *, replay: bool = True
) -> tuple[duckdb.DuckDBPyConnection, BundleSchema] | None:
    """Open a cache file read-only and restore its schema, or None if it cannot be trusted.

    Read-only matters twice: a caller's stray ``CREATE TABLE`` cannot be persisted into the
    cache, and many readers can hold the same file at once.
    """
    try:
        connection = duckdb.connect(str(path), read_only=True)
        meta = dict(connection.execute(f"SELECT key, value FROM {META_TABLE}").fetchall())
        if meta.get("format") != _CACHE_FORMAT:
            connection.close()
            return None
        schema = _schema_from_json(meta["schema"])
        if replay:
            _replay_warnings(meta.get("warnings", "[]"))
    except Exception as exc:  # noqa: BLE001 - a cache that will not open is a miss, never an error
        logger.debug("cache: %s unusable (%s)", path, exc)
        return None
    return connection, schema


def _replay_warnings(payload: str) -> None:
    """Re-emit the load warnings the cached build produced.

    A skipped malformed file is something the user is told about once per load. Serving from a
    cache must not silently stop telling them, so the warnings are stored with the cache and
    logged again on every hit, through the same logger that first raised them.
    """
    try:
        stored = json.loads(payload)
    except ValueError:
        return
    for entry in stored:
        name, message = entry[0], entry[1]
        logging.getLogger(name).warning("%s", message)


def _merge_warnings(
    stored: str, captured: list[tuple[str, str, str | None]], touched: set[str]
) -> str:
    """Carry forward the warnings for files this update did not read, and replace the rest."""
    try:
        previous = json.loads(stored)
    except ValueError:
        previous = []
    kept = [entry for entry in previous if len(entry) < 3 or entry[2] not in touched]
    return json.dumps(kept + [list(entry) for entry in captured])


class _WarningCollector(logging.Handler):
    """Captures the warnings a load emits, so a cache hit can repeat them verbatim."""

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.records: list[tuple[str, str, str | None]] = []

    def emit(self, record: logging.LogRecord) -> None:
        # The bundle-relative path is the parser's first argument, which is what lets an
        # incremental update replace exactly the warnings belonging to the files it re-read.
        subject = record.args[0] if isinstance(record.args, tuple) and record.args else None
        self.records.append(
            (record.name, record.getMessage(), subject if isinstance(subject, str) else None)
        )


def _manifest_to_json(entries: dict[str, FileStat], hashes: dict[str, str]) -> str:
    """The manifest is one JSON value, not a table.

    It is only ever read and written whole, and ``executemany`` costs about 0.1 ms per row —
    600 ms for a 6000-file bundle, which would dominate every cache write. One string costs
    nothing and removes the row-by-row update path entirely.
    """
    return json.dumps(
        {path: [stat.size, stat.mtime_ns, hashes.get(path, "")] for path, stat in entries.items()}
    )


def _manifest_from_json(payload: str) -> dict[str, tuple[FileStat, str]]:
    return {
        path: (FileStat(size=size, mtime_ns=mtime), digest)
        for path, (size, mtime, digest) in json.loads(payload).items()
    }


# --------------------------------------------------------------------------------------------
# Writing a cache.
# --------------------------------------------------------------------------------------------


def _write_cache(
    connection: duckdb.DuckDBPyConnection,
    schema: BundleSchema,
    evidence: Evidence,
    entries: dict[str, FileStat],
    hashes: dict[str, str],
    destination: Path,
    warnings: str = "[]",
) -> None:
    """Materialize an in-memory database to ``destination``, atomically.

    The write lands through ``os.replace`` from a temporary file in the same directory, so a
    reader either sees the previous cache or this one, never a half-written database.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / f".{destination.name}.{os.getpid()}.tmp"
    temporary.unlink(missing_ok=True)
    # The metadata is built in memory and carried across by COPY FROM DATABASE, then dropped:
    # a bulk copy costs a fraction of inserting thousands of rows into a file-backed database,
    # and the caller is left with exactly the database a cacheless load would have produced.
    _build_metadata(connection, schema, evidence, entries, hashes, warnings)
    connection.execute(f"ATTACH '{temporary}' AS __readb_cache (BLOCK_SIZE {BLOCK_SIZE})")
    try:
        connection.execute("COPY FROM DATABASE memory TO __readb_cache")
    finally:
        connection.execute("DETACH __readb_cache")
        connection.execute(f"DROP TABLE IF EXISTS {META_TABLE}")
    os.replace(temporary, destination)


def _build_metadata(
    connection: duckdb.DuckDBPyConnection,
    schema: BundleSchema,
    evidence: Evidence,
    entries: dict[str, FileStat],
    hashes: dict[str, str],
    warnings: str,
) -> None:
    """Create the meta table in the connection that is about to be copied out."""
    connection.execute(f"CREATE TABLE {META_TABLE} (key VARCHAR, value VARCHAR)")
    with _suppress_pandas_probe():
        connection.executemany(
            f"INSERT INTO {META_TABLE} VALUES (?, ?)",
            [
                ("format", _CACHE_FORMAT),
                ("readb_version", _readb_version()),
                ("duckdb_version", duckdb.__version__),
                ("schema", _schema_to_json(schema)),
                ("evidence", _evidence_to_json(evidence)),
                ("manifest", _manifest_to_json(entries, hashes)),
                ("warnings", warnings),
            ],
        )


def _discard_siblings(directory: Path, slug: str, keep: Path) -> None:
    """One cache file per bundle: older revisions are removed once the new one has landed."""
    for candidate in directory.glob(f"{slug}-*.duckdb"):
        if candidate != keep:
            candidate.unlink(missing_ok=True)


# --------------------------------------------------------------------------------------------
# The entry point.
# --------------------------------------------------------------------------------------------


def load(
    bundle_path: str, *, enabled: bool = True
) -> tuple[duckdb.DuckDBPyConnection, BundleSchema]:
    """Load a bundle, using or refreshing the persistent cache where one is allowed.

    Falls back to :func:`readb.loader.load_bundle` whenever the cache cannot help: caching is
    off, no registry consented to it, the bundle changed structurally, or anything at all went
    wrong with the cache itself.
    """
    root = Path(bundle_path)
    if not enabled:
        return load_bundle(bundle_path)
    directory = cache_dir_for(root)
    if directory is None:
        return load_bundle(bundle_path)

    try:
        entries = scan(root)
        key = manifest_key(entries, root)
        slug = _slug(root)
        target = directory / f"{slug}-{key}.duckdb"

        if target.exists():
            opened = _open_cache(target)
            if opened is not None:
                logger.debug("cache: hit %s", target)
                return opened

        previous = _previous_cache(directory, slug, target)
        if previous is not None:
            refreshed = _apply_incremental(previous, root, entries, target)
            if refreshed is not None:
                _discard_siblings(directory, slug, target)
                return refreshed

        connection, schema, evidence, hashes, warnings = _load_with_evidence(bundle_path, entries)
        try:
            _write_cache(connection, schema, evidence, entries, hashes, target, warnings)
            _discard_siblings(directory, slug, target)
        except (OSError, duckdb.Error) as exc:
            # A cache that cannot be written must never fail a query.
            logger.debug("cache: cannot write %s (%s)", target, exc)
        return connection, schema
    except Exception as exc:  # noqa: BLE001 - the cache is an optimization, never a failure mode
        logger.debug("cache: falling back to a full load (%s)", exc)
        return load_bundle(bundle_path)


def _previous_cache(directory: Path, slug: str, target: Path) -> Path | None:
    for candidate in sorted(directory.glob(f"{slug}-*.duckdb")):
        if candidate != target:
            return candidate
    return None


def _load_with_evidence(
    bundle_path: str, entries: dict[str, FileStat]
) -> tuple[duckdb.DuckDBPyConnection, BundleSchema, Evidence, dict[str, str], str]:
    evidence: Evidence = {}
    collector = _WarningCollector()
    readb_logger = logging.getLogger("readb")
    readb_logger.addHandler(collector)
    try:
        connection, schema = load_bundle(bundle_path, evidence=evidence)
    finally:
        readb_logger.removeHandler(collector)
    hashes = _hashes_from_load(connection, Path(bundle_path), entries)
    return connection, schema, evidence, hashes, json.dumps(collector.records)


def _hashes_from_load(
    connection: duckdb.DuckDBPyConnection, root: Path, entries: dict[str, FileStat]
) -> dict[str, str]:
    """Take the manifest's hashes from the load that just happened, not from the disk again.

    Every concept already carries ``__hash`` — the same SHA-256 of the same bytes (ADR 0007) —
    so re-reading 6000 files to compute it a second time would be pure waste. Only files with
    no row at all (skipped as malformed, or a reserved index/log file) are hashed here.
    """
    hashes: dict[str, str] = {}
    for table in ("__DOCUMENTS", "__INDEXES", "__LOG"):
        try:
            rows = connection.execute(f"SELECT __path, __hash FROM {table}").fetchall()
        except duckdb.Error:
            continue  # __LOG only exists when the bundle has one
        hashes.update({row[0]: row[1] for row in rows})
    for path in entries:
        if path not in hashes:
            hashes[path] = _hash_file(root / path)
    return hashes


def _hash_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


# --------------------------------------------------------------------------------------------
# The incremental path.
# --------------------------------------------------------------------------------------------


def _apply_incremental(
    previous: Path,
    root: Path,
    entries: dict[str, FileStat],
    target: Path,
) -> tuple[duckdb.DuckDBPyConnection, BundleSchema] | None:
    """Bring ``previous`` up to date in a copy, or return None to ask for a full rebuild.

    Returning None is always safe and is the answer whenever the change is not *provably* local:
    a column's inferred type would move, a producer key appears or vanishes, a concept changes
    type or table, a reserved file appears, or the change set is large enough that a bulk load
    would be quicker. Those conditions are the correctness argument for this whole module.
    """
    opened = _open_cache(previous, replay=False)
    if opened is None:
        return None
    reader, schema = opened
    try:
        meta = dict(reader.execute(f"SELECT key, value FROM {META_TABLE}").fetchall())
        stored = _manifest_from_json(meta["manifest"])
        evidence = _evidence_from_json(meta["evidence"])
        old_rows = {
            row[0]: row[1]
            for row in reader.execute("SELECT __path, __raw FROM __DOCUMENTS").fetchall()
        }
        # How many concepts each type table holds: a table whose last one leaves must not
        # survive as an empty table, which a fresh load would never produce.
        populations = {
            table: reader.execute(f"SELECT count(*) FROM {quote_ident(table)}").fetchone()[0]
            for table in schema.tables
            if not table.startswith("__")
        }
    except (KeyError, duckdb.Error):
        reader.close()
        return None
    reader.close()

    changed, added, removed = _change_set(root, entries, stored)
    touched = len(changed) + len(added) + len(removed)
    limit = max(INCREMENTAL_FLOOR, int(len(entries) * INCREMENTAL_SHARE))
    if touched > limit:
        logger.debug("cache: %d changed files exceeds the incremental limit %d", touched, limit)
        return None

    if touched == 0:
        # Files were touched but not changed. Nothing to apply — the manifest just has to learn
        # the new mtimes, so the next load recognizes the bundle without hashing anything.
        deletes: list[str] = []
        inserts: list[tuple[str, list[str], list[Any]]] = []
        warnings = meta.get("warnings", "[]")
    else:
        # Warnings belong to the files that produced them: the ones this update re-read are
        # replaced by whatever re-reading them says now, and the rest carry over untouched.
        collector = _WarningCollector()
        readb_logger = logging.getLogger("readb")
        readb_logger.addHandler(collector)
        try:
            plan = _plan_delta(
                root, schema, evidence, old_rows, populations, changed, added, removed
            )
        finally:
            readb_logger.removeHandler(collector)
        if plan is None:
            return None
        deletes, inserts, evidence = plan
        warnings = _merge_warnings(
            meta.get("warnings", "[]"), collector.records, set(changed) | set(added) | set(removed)
        )

    shutil.copy2(previous, target)
    try:
        writer = duckdb.connect(str(target))
        for path in deletes:
            for table in _tables_holding(schema, table_names=None):
                writer.execute(f"DELETE FROM {quote_ident(table)} WHERE __path = ?", [path])
        with _suppress_pandas_probe():
            for table, columns, row in inserts:
                placeholders = ", ".join("?" * len(row))
                names = ", ".join(quote_ident(c) for c in columns)
                writer.execute(
                    f"INSERT INTO {quote_ident(table)} ({names}) VALUES ({placeholders})", row
                )
        # A file whose bytes changed needs a fresh hash; one that was merely touched keeps the
        # hash already recorded for it, so a wide touch reads nothing.
        hashes = {
            path: (
                _hash_file(root / path)
                if path in changed or path not in stored
                else stored[path][1]
            )
            for path in entries
        }
        writer.execute(
            f"DELETE FROM {META_TABLE} WHERE key IN ('evidence', 'manifest', 'warnings')"
        )
        with _suppress_pandas_probe():
            writer.executemany(
                f"INSERT INTO {META_TABLE} VALUES (?, ?)",
                [
                    ("evidence", _evidence_to_json(evidence)),
                    ("manifest", _manifest_to_json(entries, hashes)),
                    ("warnings", warnings),
                ],
            )
        writer.close()
    except (OSError, duckdb.Error) as exc:
        logger.debug("cache: incremental update failed (%s)", exc)
        target.unlink(missing_ok=True)
        return None

    logger.debug("cache: applied %d changed files incrementally", touched)
    return _open_cache(target)


def _change_set(
    root: Path, entries: dict[str, FileStat], stored: dict[str, tuple[FileStat, str]]
) -> tuple[list[str], list[str], list[str]]:
    """Split the bundle into genuinely changed, added and removed files.

    A file whose stat moved is a *suspect*: it is read and hashed before it is believed changed,
    which is 12x cheaper than re-parsing it and is what stops a mass mtime change — a formatter,
    a copy, an unzip, a checkout — from rewriting anything.
    """
    changed: list[str] = []
    added: list[str] = []
    for path, stat in entries.items():
        if path not in stored:
            added.append(path)
            continue
        previous_stat, previous_hash = stored[path]
        if previous_stat == stat:
            continue
        if _hash_file(root / path) == previous_hash:
            continue  # touched, not changed
        changed.append(path)
    removed = [path for path in stored if path not in entries]
    return changed, added, removed


def _tables_holding(schema: BundleSchema, table_names: list[str] | None) -> list[str]:
    return list(schema.tables) if table_names is None else table_names


def _plan_delta(
    root: Path,
    schema: BundleSchema,
    evidence: Evidence,
    old_rows: dict[str, str],
    populations: dict[str, int],
    changed: list[str],
    added: list[str],
    removed: list[str],
) -> tuple[list[str], list[tuple[str, list[str], list[Any]]], Evidence] | None:
    """Work out the row deltas, or return None when a full rebuild is the honest answer."""
    from readb.schema import RESERVED_FILENAMES

    working = {
        table: {c: Counter(counts) for c, counts in cols.items()}
        for table, cols in evidence.items()
    }

    for path in changed + added + removed:
        if Path(path).name in RESERVED_FILENAMES:
            return None  # index.md / log.md change the reserved tables' unions

    # Withdraw what leaves.
    for path in changed + removed:
        raw = old_rows.get(path)
        if raw is None:
            return None  # a file the cache has no row for: let a full load decide
        old_concept = _concept_from_raw(path, raw)
        if old_concept is None:
            return None
        table = _table_of(schema, old_concept)
        if table is None:
            return None
        _withdraw(working, table, old_concept)
        if table in populations:
            populations[table] -= 1

    # Admit what arrives.
    inserts: list[tuple[str, list[str], list[Any]]] = []
    arriving: list[tuple[str, Concept]] = []
    for path in changed + added:
        concept = parse_file(root / path, bundle_root=root)
        if concept is None:
            continue  # a file that no longer parses is simply gone from the tables
        table = _table_of(schema, concept)
        if table is None:
            return None  # a new type means a new table: rebuild
        arriving.append((table, concept))
        _admit(working, table, concept)
        if table in populations:
            populations[table] += 1

    if any(count <= 0 for count in populations.values()):
        return None  # a type table would be left empty; a fresh load would not create it at all

    # Every affected table must still infer exactly the schema the cache already has.
    affected = {table for table, _ in arriving} | {"__DOCUMENTS"}
    for path in changed + removed:
        raw = old_rows.get(path)
        old_concept = _concept_from_raw(path, raw) if raw is not None else None
        if old_concept is not None:
            table = _table_of(schema, old_concept)
            if table is not None:
                affected.add(table)
    for table in affected:
        if not _schema_unchanged(schema, working, table):
            return None

    for table, concept in arriving:
        for name in (table, "__DOCUMENTS"):
            columns, values = _bind(schema, working, name, concept)
            inserts.append((name, columns, values))

    return changed + removed, inserts, working


def _concept_from_raw(path: str, raw: str) -> Concept | None:
    """Re-parse a concept from the text the cache holds, without touching the filesystem."""
    import yaml

    from readb.parser import _split_frontmatter

    frontmatter_text, body = _split_frontmatter(raw)
    if frontmatter_text is None:
        return Concept(path=path, frontmatter={}, body=body, raw=raw)
    try:
        parsed = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return None
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        return None
    return Concept(path=path, frontmatter=parsed, body=body, raw=raw)


def _table_of(schema: BundleSchema, concept: Concept) -> str | None:
    """The table a concept belongs in, or None when it would need one that does not exist."""
    raw_type = concept.frontmatter.get("type")
    if not isinstance(raw_type, str) or not normalize_type(raw_type):
        return "__UNKNOWNTYPE" if "__UNKNOWNTYPE" in schema.tables else None
    name = normalize_type(raw_type)
    table = schema.tables.get(name)
    if table is None or table.original_type != raw_type:
        return None  # a new type, or a normalization collision resolved differently
    return name


def _tracked_keys(table: str, concept: Concept) -> list[str]:
    """The frontmatter keys that are columns of ``table``.

    ``__DOCUMENTS`` holds the reserved fields and nothing else, so a producer key contributes to
    its own type's table only. Getting this wrong makes every edit look like a new column.
    """
    if table == "__DOCUMENTS":
        return [key for key in concept.frontmatter if key in RESERVED_FIELDS]
    return list(concept.frontmatter)


def _withdraw(evidence: Evidence, table: str, concept: Concept) -> None:
    for name in (table, "__DOCUMENTS"):
        columns = evidence.setdefault(name, {})
        for key in _tracked_keys(name, concept):
            if key in columns:
                columns[key][evidence_key(concept.frontmatter[key])] -= 1


def _admit(evidence: Evidence, table: str, concept: Concept) -> None:
    for name in (table, "__DOCUMENTS"):
        columns = evidence.setdefault(name, {})
        for key in _tracked_keys(name, concept):
            columns.setdefault(key, Counter())[evidence_key(concept.frontmatter[key])] += 1


def _schema_unchanged(schema: BundleSchema, evidence: Evidence, table: str) -> bool:
    """Would a fresh load still produce this table's exact columns and types?"""
    stored = schema.tables.get(table)
    if stored is None:
        return False
    counts = evidence.get(table, {})
    reserved = set(RESERVED_FIELDS)
    for column, ddl in stored.columns.items():
        if column in VIRTUAL_FIELDS:
            continue
        column_counts = counts.get(column, Counter())
        total = sum(c for c in column_counts.values() if c > 0)
        if total == 0 and column not in reserved:
            return False  # the last document carrying this key is gone: the column would vanish
        if render_ddl(_column_ltype(column_counts, column)) != ddl:
            return False
    for column, column_counts in counts.items():
        if column in stored.columns or column in VIRTUAL_FIELDS:
            continue
        if any(c > 0 for c in column_counts.values()):
            return False  # a key no document of this type carried before: a new column
    return True


def _bind(
    schema: BundleSchema, evidence: Evidence, table: str, concept: Concept
) -> tuple[list[str], list[Any]]:
    stored = schema.tables[table]
    counts = evidence.get(table, {})
    columns: list[str] = []
    values: list[Any] = []
    for column, _ddl in stored.columns.items():
        if column in VIRTUAL_FIELDS:
            continue
        columns.append(column)
        values.append(
            coerce(
                concept.frontmatter.get(column),
                _column_ltype(counts.get(column, Counter()), column),
            )
        )
    columns.extend(VIRTUAL_FIELDS)
    values.extend([concept.path, concept.name, concept.body, concept.raw, concept.content_hash])
    return columns, values


# --------------------------------------------------------------------------------------------
# The `readb cache` commands.
# --------------------------------------------------------------------------------------------


def status(bundle_path: str) -> dict[str, Any]:
    """Describe this bundle's cache: where it is, how big, how old — or why there is none."""
    root = Path(bundle_path)
    directory = cache_dir_for(root)
    if directory is None:
        marker = registry.find_registry(root)
        reason = (
            "caching is off for this registry (cache = false in .readb/config.toml)"
            if marker is not None
            else "no .readb/ registry above this bundle — run 'readb init' to enable caching"
        )
        return {"enabled": False, "reason": reason, "path": None}
    slug = _slug(root)
    files = sorted(directory.glob(f"{slug}-*.duckdb"))
    if not files:
        return {"enabled": True, "reason": "no cache written yet", "path": None}
    newest = files[-1]
    stat = newest.stat()
    entries = scan(root)
    fresh = newest.name == f"{slug}-{manifest_key(entries, root)}.duckdb"
    return {
        "enabled": True,
        "path": str(newest),
        "bytes": stat.st_size,
        "mtime": stat.st_mtime,
        "current": fresh,
        "files": len(entries),
    }


def clear(bundle_path: str) -> list[str]:
    """Delete this bundle's cache files, returning what was removed."""
    directory = cache_dir_for(bundle_path)
    if directory is None or not directory.is_dir():
        return []
    removed = []
    for candidate in sorted(directory.glob(f"{_slug(Path(bundle_path))}-*.duckdb")):
        candidate.unlink(missing_ok=True)
        removed.append(str(candidate))
    return removed
