"""Surgical, line-based editor for a file's leading YAML frontmatter block.

readb is a read-only SQL layer over a bundle: loading and querying a bundle never mutate it. This
module is the one deliberate, clearly-separated exception — an explicit frontmatter field editor
exposed via the ``readb get`` / ``readb set`` / ``readb unset`` commands, never through the
SQL/query path. Edits are line-based: only the targeted key's own lines change, so other fields,
the body, and unrelated formatting stay byte-for-byte intact, which keeps diffs small and
reviewable. It intentionally does NOT round-trip through a YAML parser (that would reflow,
reorder, and re-quote the whole block).

A key is addressed by its *span* — the ``key:`` line plus every continuation line of its value
(block sequences, block scalars, nested mappings) — so that removing or replacing a field cannot
orphan the rest of its value into invalid YAML. Writing is still scalar-only: ``set`` refuses a
key whose value spans multiple lines rather than silently discarding it.

PyYAML is used in exactly one place — verifying, never producing: a rewrite that would turn
valid frontmatter invalid is abandoned before the file is touched. Output always comes from the
line editor, so the no-round-trip guarantee holds. Nothing here loads the bundle to edit one file.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import yaml

_DELIM = "---"
_KEY_LINE = re.compile(r"^([A-Za-z0-9_-]+)\s*:")
# A YAML scalar that is safe to write unquoted (no special chars, not a reserved word).
_PLAIN = re.compile(r"[A-Za-z0-9_./@+-]+")
_RESERVED_WORDS = {"true", "false", "null", "yes", "no", "on", "off", "~"}


class FrontmatterError(Exception):
    """Raised when a frontmatter edit cannot be performed safely."""


class MultilineValueError(FrontmatterError):
    """Raised when ``set`` targets a key whose value spans more than one line."""


def get_field(path: Path, key: str) -> str | None:
    """Return the value of ``key`` in ``path``'s frontmatter, or None if absent.

    Single-line scalars come back unquoted. A value spanning several lines (a block sequence,
    block scalar, or nested mapping) comes back as the raw YAML fragment, exactly as written —
    a multi-line field is never reported as an empty string.

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

    Values are written as scalars. A key whose current value spans several lines raises
    :class:`MultilineValueError` — replacing a list or block scalar with a scalar would discard
    data the caller never named. Unset the key first if that is genuinely the intent.

    All-or-nothing: if any pair is refused, the file is left untouched.

    Raises :class:`FrontmatterError` if the file has no frontmatter block to write into.
    """
    _rewrite(path, lambda frontmatter: _set(frontmatter, pairs))


def unset_fields(path: Path, keys: list[str]) -> None:
    """Remove each key in ``keys`` from ``path``'s frontmatter in place (absent keys ignored).

    A key's whole value is removed, continuation lines included.

    Raises :class:`FrontmatterError` if the file has no frontmatter block.
    """
    _rewrite(path, lambda frontmatter: _unset(frontmatter, keys))


def _rewrite(path: Path, transform: Callable[[list[str]], list[str]]) -> None:
    """Read ``path``, apply ``transform`` to its frontmatter lines, and write it back in place.

    The write is abandoned if it would turn parseable frontmatter into unparseable frontmatter.
    A file whose frontmatter is *already* broken is still editable: the guard forbids introducing
    invalidity, it does not make readb the one tool that refuses to touch a damaged file.
    """
    parts = _split_frontmatter(path.read_text(encoding="utf-8"))
    if parts is None:
        raise FrontmatterError(f"{path}: no YAML frontmatter block found")
    opening, frontmatter, remainder = parts
    edited = transform(frontmatter)
    if _yaml_error(frontmatter) is None:
        broken = _yaml_error(edited)
        if broken is not None:
            raise FrontmatterError(
                f"{path}: edit would produce invalid YAML frontmatter, file left unchanged "
                f"({broken})"
            )
    path.write_text("".join(opening) + "".join(edited) + "".join(remainder), encoding="utf-8")


def _yaml_error(frontmatter: list[str]) -> str | None:
    """Return a one-line reason why ``frontmatter`` is not a usable YAML mapping, else None."""
    try:
        parsed = yaml.safe_load("".join(frontmatter))
    except yaml.YAMLError as exc:
        return " ".join(str(exc).split())
    if parsed is not None and not isinstance(parsed, dict):
        return "frontmatter is not a mapping"
    return None


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


def _span(frontmatter: list[str], key: str) -> tuple[int, int] | None:
    """Return the half-open line range ``key``'s whole entry occupies, or None if absent.

    The span starts at the ``key:`` line and runs to the next top-level key (or the end of the
    block). Trailing blank lines and column-0 comments are trimmed back out, so a comment
    introducing the *next* field survives the removal of this one.
    """
    key_line = re.compile(rf"^{re.escape(key)}\s*:")
    start = next((i for i, line in enumerate(frontmatter) if key_line.match(line)), None)
    if start is None:
        return None
    end = start + 1
    while end < len(frontmatter) and not _KEY_LINE.match(frontmatter[end]):
        end += 1
    while end - 1 > start and _is_trailing_filler(frontmatter[end - 1]):
        end -= 1
    return start, end


def _is_trailing_filler(line: str) -> bool:
    """True for a blank line or a column-0 comment — never part of the value above it."""
    return not line.strip() or line.startswith("#")


def _get(frontmatter: list[str], key: str) -> str | None:
    span = _span(frontmatter, key)
    if span is None:
        return None
    start, end = span
    inline = frontmatter[start].split(":", 1)[1]
    if end - start == 1:
        return _unquote(inline)
    # A multi-line value is returned verbatim: the indicator or fragment left on the key line
    # (often empty, or "|" for a block scalar) followed by its continuation lines.
    continuation = "".join(frontmatter[start + 1 : end]).rstrip("\n")
    inline = inline.strip()
    return f"{inline}\n{continuation}" if inline else continuation


def _set(frontmatter: list[str], pairs: list[tuple[str, str]]) -> list[str]:
    out = list(frontmatter)
    for key, value in pairs:
        new_line = f"{key}: {_format(value)}\n"
        span = _span(out, key)
        if span is None:
            if out and not out[-1].endswith("\n"):
                out[-1] += "\n"
            out.append(new_line)
            continue
        start, end = span
        if end - start > 1:
            raise MultilineValueError(
                f"{key}: multi-line value (list, block scalar, or nested mapping); "
                f"readb set writes scalar values only — unset the key first"
            )
        out[start] = new_line if out[start].endswith("\n") else new_line.rstrip("\n")
    return out


def _unset(frontmatter: list[str], keys: list[str]) -> list[str]:
    out = list(frontmatter)
    for key in keys:
        # Loop: a duplicated key is removed in full, as it was before spans existed.
        while (span := _span(out, key)) is not None:
            del out[span[0] : span[1]]
    return out
