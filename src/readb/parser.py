"""Parse a single OKF file into (frontmatter, body).

An OKF file is an optional YAML frontmatter block delimited by ``---`` lines, followed by a
free-form markdown body. Consumers MUST be permissive: a malformed file (e.g. broken YAML, a
frontmatter block that is not a mapping, or invalid UTF-8) is logged and skipped, never fatal.

The same parser serves concept documents *and* the reserved ``index.md`` / ``log.md`` files.
A file with no leading ``---`` is treated as all-body with empty frontmatter (the common case
for index/log files); only a file that *opens* a frontmatter block it cannot parse is skipped.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_DELIMITER = "---"


@dataclass(frozen=True)
class Concept:
    """One parsed OKF file (concept document, index, or log).

    Attributes:
        path: Bundle-root-relative path, WITH the ``.md`` suffix (the ``__path`` virtual field),
            using forward slashes regardless of platform.
        frontmatter: Parsed YAML mapping (may contain arbitrary producer keys; may be empty).
        body: Markdown body with the frontmatter block stripped (the ``__body`` virtual field).
        raw: The byte-exact file text as on disk, frontmatter included, no normalization
            (the ``__raw`` virtual field).
    """

    path: str
    frontmatter: dict[str, Any]
    body: str
    raw: str

    @property
    def content_hash(self) -> str:
        """Lowercase hex SHA-256 of the file's bytes — what ``sha256sum`` prints for it.

        The ``__hash`` virtual field (ADR 0007). Derived from ``raw``, which is byte-exact by
        contract, so re-encoding it as UTF-8 reproduces the file: no line-ending, encoding or
        whitespace normalization, and none of the framing ``git hash-object`` applies.
        """
        return hashlib.sha256(self.raw.encode("utf-8")).hexdigest()

    @property
    def name(self) -> str:
        """The concept name (wiki-style): the simple file name, no directories, no ``.md``.

        Assumed unique within a bundle, NOT guaranteed (the ``__name`` virtual field);
        ``path`` is the unambiguous key.
        """
        filename = self.path.rsplit("/", 1)[-1]
        return filename[:-3] if filename.endswith(".md") else filename


# A frontmatter key becomes a column name and a mapping key becomes a STRUCT field name, so a
# key has to survive as a DuckDB identifier: an empty name cannot be addressed at all.
_EMPTY_KEY_NAME = "__EMPTY"


class _CanonicalKeyLoader(yaml.SafeLoader):
    """Builds mappings with canonical string keys, resolving collisions as they are read.

    PyYAML's own mapping construction would merge ``1:`` and ``true:`` into one entry before
    readb ever sees them, because ``hash(True) == hash(1)`` in Python, and the first value would
    vanish with no warning. Keying on the canonical *text* of each key keeps them distinct, and
    makes every collision resolve by one rule: the last occurrence wins, and it is logged.

    Collisions are judged case-insensitively, because that is how DuckDB compares the identifiers
    these names become.
    """

    rel_path: str = "<unknown>"

    def construct_mapping(self, node, deep=False):  # type: ignore[no-untyped-def]
        mapping: dict[str, Any] = {}
        claimed: dict[str, str] = {}  # identifier form -> the name currently holding it
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            name = _key_name(key)
            identifier = name.casefold()
            if identifier in claimed:
                previous = claimed[identifier]
                logger.warning(
                    "%s: frontmatter keys %r and %r are one column %r; keeping the last",
                    self.rel_path,
                    previous,
                    name,
                    name,
                )
                del mapping[previous]
            claimed[identifier] = name
            mapping[name] = self.construct_object(value_node, deep=deep)
        return mapping


def _key_name(key: Any) -> str:
    """The column or field name a YAML key takes.

    The canonical text of the parsed key, with one identifier rule on top: an empty name becomes
    ``__EMPTY``, since a zero-length identifier cannot be addressed in SQL.
    """
    from readb.schema import canonical_text

    text = key if isinstance(key, str) else canonical_text(key)
    return text or _EMPTY_KEY_NAME


def parse_file(file_path: Path, *, bundle_root: Path) -> Concept | None:
    """Parse one markdown file into a :class:`Concept`, or return None if it must be skipped.

    Never raises on malformed input: logs a warning and returns None so the load can continue.
    """
    rel_path = file_path.relative_to(bundle_root).as_posix()
    try:
        # read_bytes + decode, NOT read_text: universal-newline mode would rewrite CRLF to LF
        # and ``raw`` must stay byte-exact (ADR 0003).
        text = file_path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("skipping %s: cannot read as UTF-8 (%s)", rel_path, exc)
        return None

    frontmatter_text, body = _split_frontmatter(text)

    if frontmatter_text is None:
        # No frontmatter block: all body, empty frontmatter (normal for index.md / log.md).
        return Concept(path=rel_path, frontmatter={}, body=body, raw=text)

    loader = _CanonicalKeyLoader(frontmatter_text)
    loader.rel_path = rel_path
    try:
        parsed = loader.get_single_data()
    except yaml.YAMLError as exc:
        logger.warning("skipping %s: malformed YAML frontmatter (%s)", rel_path, _terse(exc))
        return None
    except ValueError as exc:
        # PyYAML constructs timestamps by calling `datetime` directly, so an impossible date
        # (`2026-02-30`, `25:00:00`, year 0) raises ValueError rather than a YAMLError. One
        # mistyped date in one document must not make a bundle unqueryable.
        logger.warning("skipping %s: frontmatter has an invalid value (%s)", rel_path, _terse(exc))
        return None
    except RecursionError:
        logger.warning("skipping %s: frontmatter is too deeply nested", rel_path)
        return None
    finally:
        loader.dispose()

    if parsed is None:
        parsed = {}  # an empty frontmatter block (`---\n---`) is valid: a doc with no fields.
    if not isinstance(parsed, dict):
        logger.warning(
            "skipping %s: frontmatter is not a mapping (got %s)", rel_path, type(parsed).__name__
        )
        return None

    depth = _depth(parsed)
    if depth > _MAX_DEPTH:
        # Type inference walks this structure recursively, and Python's stack runs out around
        # 500 levels — after parsing succeeded, where the skip contract no longer applies.
        logger.warning(
            "skipping %s: frontmatter nests %d levels deep (limit %d)", rel_path, depth, _MAX_DEPTH
        )
        return None

    unpaired = _unpaired_surrogate(parsed)
    if unpaired is not None:
        # A YAML escape can name half a surrogate pair (`"\uD800"`). Python holds it, but it is
        # not encodable text, and binding it raises out of the database driver — where the skip
        # contract no longer applies and one value would cost the whole table its columns.
        logger.warning(
            "skipping %s: frontmatter key or value %r is not encodable", rel_path, unpaired
        )
        return None

    if _is_cyclic(parsed):
        # A self-referential anchor (`f: &x {b: *x}`) parses fine — PyYAML builds the loop in two
        # phases — and then has no bottom for anything that walks it. Skipping the file here is
        # the load's promise; letting it through would recurse to death in type inference.
        logger.warning("skipping %s: frontmatter refers to itself", rel_path)
        return None

    return Concept(path=rel_path, frontmatter=parsed, body=body, raw=text)


# Deep enough for any real document, shallow enough that recursive walks over it cannot exhaust
# the stack. Measured: type inference survives 400 levels and dies somewhere before 500.
_MAX_DEPTH = 200


def _depth(value: Any) -> int:
    """How deeply this structure nests, walked iteratively so measuring costs no stack."""
    deepest = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, level = stack.pop()
        deepest = max(deepest, level)
        if level > _MAX_DEPTH:
            return level  # no point walking further; the answer is already "too deep"
        if isinstance(current, dict):
            stack.extend((child, level + 1) for child in current.values())
        elif isinstance(current, list):
            stack.extend((child, level + 1) for child in current)
    return deepest


def _unpaired_surrogate(value: Any) -> str | None:
    """The first string here that cannot be encoded as UTF-8, or None if every one can."""
    stack: list[Any] = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, str):
            try:
                current.encode("utf-8")
            except UnicodeEncodeError:
                return current
        elif isinstance(current, dict):
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return None


def _is_cyclic(value: Any) -> bool:
    """Does this structure contain itself? Walked iteratively, tracking the path by identity."""
    stack: list[tuple[Any, set[int]]] = [(value, set())]
    while stack:
        current, seen = stack.pop()
        if isinstance(current, (dict, list)):
            if id(current) in seen:
                return True
            path = seen | {id(current)}
            children = current.values() if isinstance(current, dict) else current
            stack.extend((child, path) for child in children)
    return False


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """Split raw file text into ``(frontmatter_text, body)``.

    Returns ``(None, text)`` when the file does not open with a frontmatter delimiter or never
    closes one (treated permissively as all-body, not malformed). Otherwise returns the raw YAML
    text and the body that follows the closing delimiter.
    """
    # Normalize newlines so CRLF files parse identically.
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    if not lines or lines[0].strip() != _DELIMITER:
        return None, _strip_leading_blanks(normalized)

    for idx in range(1, len(lines)):
        if lines[idx].strip() == _DELIMITER:
            frontmatter_text = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1 :])
            return frontmatter_text, _strip_leading_blanks(body)

    # Opened a frontmatter block that never closes: treat as all-body (permissive).
    return None, _strip_leading_blanks(normalized)


def _strip_leading_blanks(body: str) -> str:
    """Drop blank lines immediately following the frontmatter so the body starts at content."""
    return body.lstrip("\n")


def _terse(exc: Exception) -> str:
    """Collapse a multi-line exception message to a single line for log readability."""
    return " ".join(str(exc).split())
