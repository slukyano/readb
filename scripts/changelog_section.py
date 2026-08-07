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

_FENCE = re.compile(r"^\s*(```+|~~~+)")
_LINK_DEF = re.compile(r"^\[[^\]]+\]:")


def extract(changelog: str, version: str) -> str:
    """Return the body of the ``## [<version>]`` section, without its heading.

    The section runs to the next top-level heading *outside a fenced code block*, so a shell
    comment like ``## usage`` inside an example cannot truncate it. Trailing link-reference
    definitions — the block at the foot of a Keep a Changelog file — belong to no section and
    are dropped; definitions used mid-body are left alone, since removing them would silently
    break the links that reference them.
    """
    heading = re.compile(rf"^## \[{re.escape(version)}\][^\n]*$", re.MULTILINE)
    match = heading.search(changelog)
    if match is None:
        raise LookupError(f"no '## [{version}]' section in the changelog")

    lines = changelog[match.end() :].splitlines()
    fence: str | None = None
    body: list[str] = []
    for line in lines:
        fence_match = _FENCE.match(line)
        if fence_match:
            marker = fence_match.group(1)[0] * 3
            fence = None if fence and marker in fence else marker
        elif fence is None and line.startswith("## "):
            break
        body.append(line)

    while body and (not body[-1].strip() or _LINK_DEF.match(body[-1])):
        body.pop()
    return "\n".join(body).strip()


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
