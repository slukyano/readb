"""Print one version's section of a Keep a Changelog file, for use as release notes.

Used by the release workflow: the GitHub release body is the changelog section for the tag
being released, so the notes and the changelog can never disagree. Exits non-zero when the
section is missing or empty, which fails the release rather than publishing empty notes.

Usage: python3 scripts/changelog_section.py <version> [path]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def extract(changelog: str, version: str) -> str:
    """Return the body of the ``## [<version>]`` section, without its heading.

    The section runs to the next top-level heading. Link-reference definitions at the foot of
    the file are not part of any section.
    """
    heading = re.compile(rf"^## \[{re.escape(version)}\][^\n]*$", re.MULTILINE)
    match = heading.search(changelog)
    if match is None:
        raise LookupError(f"no '## [{version}]' section in the changelog")
    rest = changelog[match.end() :]
    end = re.search(r"^## ", rest, re.MULTILINE)
    body = rest[: end.start()] if end else rest
    body = re.sub(r"^\[[^\]]+\]:.*$", "", body, flags=re.MULTILINE)
    return body.strip()


def main(argv: list[str]) -> int:
    if not 1 <= len(argv) <= 2:
        print(__doc__, file=sys.stderr)
        return 2
    version = argv[0]
    path = Path(argv[1]) if len(argv) == 2 else Path("CHANGELOG.md")
    try:
        body = extract(path.read_text(encoding="utf-8"), version)
    except LookupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not body:
        print(f"error: the '{version}' changelog section is empty", file=sys.stderr)
        return 1
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
