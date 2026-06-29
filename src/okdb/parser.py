"""Parse a single OKF concept file into (frontmatter, body).

An OKF file is a YAML frontmatter block delimited by ``---`` lines, followed by a free-form
markdown body. Consumers MUST be permissive: a malformed file (e.g. broken YAML) is logged and
skipped, never fatal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Concept:
    """One parsed OKF concept.

    Attributes:
        path: Bundle-root-relative path, WITH the ``.md`` suffix (the ``__path`` virtual field).
        frontmatter: Parsed YAML mapping (may contain arbitrary producer keys).
        body: Markdown body with the frontmatter block stripped (the ``__body`` virtual field).
    """

    path: str
    frontmatter: dict[str, Any]
    body: str

    @property
    def concept_id(self) -> str:
        """The Concept ID: ``path`` with the trailing ``.md`` removed."""
        return self.path[:-3] if self.path.endswith(".md") else self.path


def parse_file(file_path: Path, *, bundle_root: Path) -> Concept | None:
    """Parse one markdown file into a :class:`Concept`, or return None if it must be skipped.

    Never raises on malformed input: logs a warning and returns None so the load can continue.
    """
    raise NotImplementedError
