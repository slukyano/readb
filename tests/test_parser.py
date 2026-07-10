"""Unit tests for the permissive OKF file parser (readb.parser)."""

from __future__ import annotations

import logging
from pathlib import Path

from readb.parser import parse_file


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_parses_frontmatter_and_body(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.md", "---\ntype: Thing\ntitle: T\n---\n\nBody here.\n")
    c = parse_file(f, bundle_root=tmp_path)
    assert c is not None
    assert c.frontmatter == {"type": "Thing", "title": "T"}
    assert c.body == "Body here.\n"
    assert c.path == "a.md"
    assert c.name == "a"


def test_no_frontmatter_is_all_body(tmp_path: Path) -> None:
    # The common shape for index.md / log.md: no frontmatter block.
    f = _write(tmp_path, "index.md", "# Listing\n\n* item\n")
    c = parse_file(f, bundle_root=tmp_path)
    assert c is not None
    assert c.frontmatter == {}
    assert c.body == "# Listing\n\n* item\n"


def test_empty_frontmatter_block_is_empty_mapping(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.md", "---\n---\nbody\n")
    c = parse_file(f, bundle_root=tmp_path)
    assert c is not None
    assert c.frontmatter == {}
    assert c.body == "body\n"


def test_malformed_yaml_is_skipped(tmp_path: Path, caplog) -> None:
    f = _write(tmp_path, "bad.md", "---\nitems: [1, 2, 3\noops: : :\n---\nbody\n")
    with caplog.at_level(logging.WARNING, logger="readb.parser"):
        c = parse_file(f, bundle_root=tmp_path)
    assert c is None
    assert any("bad.md" in rec.getMessage() for rec in caplog.records)


def test_non_mapping_frontmatter_is_skipped(tmp_path: Path) -> None:
    # A frontmatter block that parses to a list, not a mapping.
    f = _write(tmp_path, "list.md", "---\n- a\n- b\n---\nbody\n")
    assert parse_file(f, bundle_root=tmp_path) is None


def test_unclosed_frontmatter_treated_as_body(tmp_path: Path) -> None:
    # Opens a delimiter but never closes it: permissively treated as all-body.
    f = _write(tmp_path, "a.md", "---\nnot really frontmatter\nstill going\n")
    c = parse_file(f, bundle_root=tmp_path)
    assert c is not None
    assert c.frontmatter == {}


def test_crlf_newlines(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.md", "---\r\ntype: Thing\r\n---\r\nBody\r\n")
    c = parse_file(f, bundle_root=tmp_path)
    assert c is not None
    assert c.frontmatter == {"type": "Thing"}
    assert c.body == "Body\n"


def test_nested_path_is_posix_relative(tmp_path: Path) -> None:
    f = _write(tmp_path, "sub/dir/x.md", "---\ntype: T\n---\nbody\n")
    c = parse_file(f, bundle_root=tmp_path)
    assert c is not None
    assert c.path == "sub/dir/x.md"
    assert c.name == "x"  # wiki-style: the simple file name, directories dropped
