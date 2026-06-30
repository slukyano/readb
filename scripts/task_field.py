#!/usr/bin/env python3
"""Minimal, low-churn frontmatter field editor for OKF task files.

Used by ``scripts/agent-loop.sh`` to read and update single-line scalar fields (``status``,
``claimed_by``, ``claimed_at``, ``timestamp``) inside a task's leading ``--- ... ---`` YAML
frontmatter block. Edits are surgical and line-based: only the targeted lines change, so lists,
the body, and unrelated formatting are left untouched (small, reviewable diffs).

Usage:
    task_field.py get   <file> <key>
    task_field.py set   <file> key=value [key=value ...]
    task_field.py unset <file> <key> [<key> ...]

Stdlib only — no third-party dependencies.
"""

from __future__ import annotations

import re
import sys

_DELIM = "---"
_KEY_LINE = re.compile(r"^([A-Za-z0-9_-]+)\s*:")
# A YAML scalar that is safe to write unquoted (no special chars, not a reserved word).
_PLAIN = re.compile(r"[A-Za-z0-9_./@+-]+")
_RESERVED_WORDS = {"true", "false", "null", "yes", "no", "on", "off", "~"}


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


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write(__doc__ or "")
        return 2
    command, path = argv[0], argv[1]
    rest = argv[2:]

    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    parts = _split_frontmatter(text)
    if parts is None:
        sys.stderr.write(f"{path}: no YAML frontmatter block found\n")
        return 1
    opening, frontmatter, remainder = parts

    if command == "get":
        if not rest:
            sys.stderr.write("get requires a key\n")
            return 2
        value = _get(frontmatter, rest[0])
        if value is not None:
            print(value)
        return 0

    if command == "set":
        pairs = [(item.split("=", 1)[0], item.partition("=")[2]) for item in rest]
        frontmatter = _set(frontmatter, pairs)
    elif command == "unset":
        frontmatter = _unset(frontmatter, rest)
    else:
        sys.stderr.write(f"unknown command: {command}\n")
        return 2

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(opening) + "".join(frontmatter) + "".join(remainder))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
