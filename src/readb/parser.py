"""Parse a single OKF file into (frontmatter, body).

An OKF file is an optional YAML frontmatter block delimited by ``---`` lines, followed by a
free-form markdown body. Consumers MUST be permissive: a malformed file (e.g. broken YAML, a
frontmatter block that is not a mapping, or invalid UTF-8) is logged and skipped, never fatal.

The same parser serves concept documents *and* the reserved ``index.md`` / ``log.md`` files.
A file with no leading ``---`` is treated as all-body with empty frontmatter (the common case
for index/log files); only a file that *opens* a frontmatter block it cannot parse is skipped.
"""

from __future__ import annotations

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
    def name(self) -> str:
        """The concept name (wiki-style): the simple file name, no directories, no ``.md``.

        Assumed unique within a bundle, NOT guaranteed (the ``__name`` virtual field);
        ``path`` is the unambiguous key.
        """
        filename = self.path.rsplit("/", 1)[-1]
        return filename[:-3] if filename.endswith(".md") else filename


def parse_file(file_path: Path, *, bundle_root: Path) -> Concept | None:
    """Parse one markdown file into a :class:`Concept`, or return None if it must be skipped.

    Never raises on malformed input: logs a warning and returns None so the load can continue.
    """
    rel_path = file_path.relative_to(bundle_root).as_posix()
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("skipping %s: cannot read as UTF-8 (%s)", rel_path, exc)
        return None

    frontmatter_text, body = _split_frontmatter(text)

    if frontmatter_text is None:
        # No frontmatter block: all body, empty frontmatter (normal for index.md / log.md).
        return Concept(path=rel_path, frontmatter={}, body=body, raw=text)

    try:
        parsed = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        logger.warning("skipping %s: malformed YAML frontmatter (%s)", rel_path, _terse(exc))
        return None

    if parsed is None:
        parsed = {}  # an empty frontmatter block (`---\n---`) is valid: a doc with no fields.
    if not isinstance(parsed, dict):
        logger.warning(
            "skipping %s: frontmatter is not a mapping (got %s)", rel_path, type(parsed).__name__
        )
        return None

    return Concept(path=rel_path, frontmatter=parsed, body=body, raw=text)


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
