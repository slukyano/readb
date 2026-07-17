"""Surgical, line-based editor for a file's leading YAML frontmatter block.

readb is a read-only SQL layer over a bundle: loading and querying a bundle never mutate it. This
module is the one deliberate, clearly-separated exception — an explicit frontmatter field editor
exposed via the ``readb get`` / ``readb set`` / ``readb unset`` commands, never through the
SQL/query path. Edits are line-based: only the targeted ``key: value`` lines change, so lists,
the body, and unrelated formatting stay byte-for-byte intact, which keeps diffs small and
reviewable. It intentionally does NOT round-trip through a YAML parser (that would reflow,
reorder, and re-quote the whole block). Scope is single-line scalar fields (e.g. ``status``,
``claimed_by``, ``claimed_at``, ``timestamp``).

Stdlib only — deliberately independent of the parser/loader, so it never loads the bundle to
edit one file.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

_DELIM = "---"
_KEY_LINE = re.compile(r"^([A-Za-z0-9_-]+)\s*:")
# A YAML scalar that is safe to write unquoted (no special chars, not a reserved word).
_PLAIN = re.compile(r"[A-Za-z0-9_./@+-]+")
_RESERVED_WORDS = {"true", "false", "null", "yes", "no", "on", "off", "~"}


class FrontmatterError(Exception):
    """Raised when a file to be edited has no YAML frontmatter block to write into."""


def get_field(path: Path, key: str) -> str | None:
    """Return the scalar value of ``key`` in ``path``'s frontmatter, or None if absent.

    Reads are forgiving: a file with no frontmatter block is treated as having no fields
    (returns None), never an error.
    """
    parts = _split_frontmatter(path.read_text(encoding="utf-8"))
    if parts is None:
        return None
    _, frontmatter, _ = parts
    return _get(frontmatter, key)


def set_fields(path: Path, pairs: list[tuple[str, str]]) -> None:
    """Set each ``key=value`` in ``path``'s frontmatter in place, appending keys that are absent.

    Raises :class:`FrontmatterError` if the file has no frontmatter block to write into.
    """
    _rewrite(path, lambda frontmatter: _set(frontmatter, pairs))


def unset_fields(path: Path, keys: list[str]) -> None:
    """Remove each key in ``keys`` from ``path``'s frontmatter in place (absent keys ignored).

    Raises :class:`FrontmatterError` if the file has no frontmatter block.
    """
    _rewrite(path, lambda frontmatter: _unset(frontmatter, keys))


def _rewrite(path: Path, transform: Callable[[list[str]], list[str]]) -> None:
    """Read ``path``, apply ``transform`` to its frontmatter lines, and write it back in place."""
    parts = _split_frontmatter(path.read_text(encoding="utf-8"))
    if parts is None:
        raise FrontmatterError(f"{path}: no YAML frontmatter block found")
    opening, frontmatter, remainder = parts
    frontmatter = transform(frontmatter)
    path.write_text("".join(opening) + "".join(frontmatter) + "".join(remainder), encoding="utf-8")


def _split_frontmatter(text: str) -> tuple[list[str], list[str], list[str]] | None:
    """Return (opening-delimiter lines, frontmatter lines, remainder lines), or None.

    Remainder includes the closing delimiter and the body. None if there is no frontmatter.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != _DELIM:
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == _DELIM:
            return lines[:1], lines[1:i], lines[i:]
    return None


def _needs_quote(value: str) -> bool:
    if value == "":
        return True
    if value.lower() in _RESERVED_WORDS:
        return True
    return not _PLAIN.fullmatch(value)


def _format(value: str) -> str:
    if _needs_quote(value):
        return "'" + value.replace("'", "''") + "'"
    return value


def _unquote(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        inner = raw[1:-1]
        return inner.replace("''", "'") if raw[0] == "'" else inner
    return raw


def _get(frontmatter: list[str], key: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(key)}\s*:\s*(.*?)\s*$")
    for line in frontmatter:
        match = pattern.match(line)
        if match:
            return _unquote(match.group(1))
    return None


def _set(frontmatter: list[str], pairs: list[tuple[str, str]]) -> list[str]:
    out = list(frontmatter)
    for key, value in pairs:
        key_pattern = re.compile(rf"^{re.escape(key)}\s*:.*$")
        new_line = f"{key}: {_format(value)}\n"
        for idx, line in enumerate(out):
            if key_pattern.match(line):
                out[idx] = new_line if line.endswith("\n") else new_line.rstrip("\n")
                break
        else:
            if out and not out[-1].endswith("\n"):
                out[-1] += "\n"
            out.append(new_line)
    return out


def _unset(frontmatter: list[str], keys: list[str]) -> list[str]:
    drop = set(keys)
    return [line for line in frontmatter if not _is_key(line, drop)]


def _is_key(line: str, keys: set[str]) -> bool:
    match = _KEY_LINE.match(line)
    return bool(match and match.group(1) in keys)
