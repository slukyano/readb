"""Tests for the frontmatter field editor (readb.fields) and its CLI (readb get/set/unset).

The editor is the one write path in an otherwise read-only tool, so these tests pin down two
things: edits are surgical (only the targeted lines move; body and lists stay byte-for-byte),
and the CLI addresses a concept by ID within a bundle without letting the path escape it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from readb import fields
from readb.cli import main

# A representative task file: scalar fields to edit, a list and a body that must stay untouched.
TASK = """\
---
type: Task
status: Draft
priority: high
claimed_by: alice@box
blocked_by:
  - okf-foo
  - okf-bar
---

## Plan

Do the thing.
"""


def _bundle(tmp_path: Path, concept_id: str = "okf-demo", text: str = TASK) -> Path:
    path = tmp_path / f"{concept_id}.md"
    path.write_text(text, encoding="utf-8")
    return tmp_path


# --------------------------------------------------------------------------------------------
# Editor module
# --------------------------------------------------------------------------------------------


def test_get_returns_scalar(tmp_path: Path) -> None:
    _bundle(tmp_path)
    assert fields.get_field(tmp_path / "okf-demo.md", "status") == "Draft"


def test_get_absent_key_is_none(tmp_path: Path) -> None:
    _bundle(tmp_path)
    assert fields.get_field(tmp_path / "okf-demo.md", "nonexistent") is None


def test_get_unquotes_value(tmp_path: Path) -> None:
    _bundle(tmp_path, text="---\ntitle: 'a: b'\n---\nbody\n")
    assert fields.get_field(tmp_path / "okf-demo.md", "title") == "a: b"


def test_get_no_frontmatter_is_none(tmp_path: Path) -> None:
    _bundle(tmp_path, text="# just a body\n")
    assert fields.get_field(tmp_path / "okf-demo.md", "status") is None


def test_set_is_surgical(tmp_path: Path) -> None:
    _bundle(tmp_path)
    path = tmp_path / "okf-demo.md"
    fields.set_fields(path, [("status", "Refined")])
    out = path.read_text(encoding="utf-8")
    # The one field changed; everything else — the list and the body — is byte-for-byte intact.
    assert "status: Refined\n" in out
    assert "status: Draft" not in out
    assert out == TASK.replace("status: Draft", "status: Refined")


def test_set_appends_absent_key(tmp_path: Path) -> None:
    _bundle(tmp_path)
    path = tmp_path / "okf-demo.md"
    fields.set_fields(path, [("timestamp", "2026-07-02T00:00:00Z")])
    assert fields.get_field(path, "timestamp") == "2026-07-02T00:00:00Z"
    # Appended inside the frontmatter block, before the body.
    assert "timestamp:" in path.read_text().split("---")[1]


def test_set_quotes_when_needed(tmp_path: Path) -> None:
    _bundle(tmp_path)
    path = tmp_path / "okf-demo.md"
    fields.set_fields(path, [("note", "has spaces: and colons")])
    assert "note: 'has spaces: and colons'\n" in path.read_text(encoding="utf-8")
    assert fields.get_field(path, "note") == "has spaces: and colons"


def test_unset_removes_only_named_keys(tmp_path: Path) -> None:
    _bundle(tmp_path)
    path = tmp_path / "okf-demo.md"
    fields.unset_fields(path, ["claimed_by"])
    assert fields.get_field(path, "claimed_by") is None
    assert fields.get_field(path, "status") == "Draft"  # untouched
    assert "- okf-foo" in path.read_text()  # the list survives


def test_set_without_frontmatter_raises(tmp_path: Path) -> None:
    _bundle(tmp_path, text="# body only\n")
    with pytest.raises(fields.FrontmatterError):
        fields.set_fields(tmp_path / "okf-demo.md", [("status", "Refined")])


# --------------------------------------------------------------------------------------------
# CLI: readb get / set / unset
# --------------------------------------------------------------------------------------------


def _run(args: list[str]) -> Result:
    return CliRunner().invoke(main, args)


def test_cli_get(tmp_path: Path) -> None:
    _bundle(tmp_path)
    result = _run(["get", "--bundle", str(tmp_path), "okf-demo", "status"])
    assert result.exit_code == 0
    assert result.output.strip() == "Draft"


def test_cli_set_then_get_roundtrip(tmp_path: Path) -> None:
    _bundle(tmp_path)
    assert _run(["set", "--bundle", str(tmp_path), "okf-demo", "status=Refined"]).exit_code == 0
    result = _run(["get", "--bundle", str(tmp_path), "okf-demo", "status"])
    assert result.output.strip() == "Refined"


def test_cli_set_multiple_assignments(tmp_path: Path) -> None:
    _bundle(tmp_path)
    result = _run(
        ["set", "--bundle", str(tmp_path), "okf-demo", "status=Refined", "claimed_by=bob"]
    )
    assert result.exit_code == 0
    text = (tmp_path / "okf-demo.md").read_text()
    assert "status: Refined" in text and "claimed_by: bob" in text


def test_cli_unset(tmp_path: Path) -> None:
    _bundle(tmp_path)
    result = _run(["unset", "--bundle", str(tmp_path), "okf-demo", "claimed_by"])
    assert result.exit_code == 0
    assert "claimed_by" not in (tmp_path / "okf-demo.md").read_text()


def test_cli_accepts_id_with_md_suffix(tmp_path: Path) -> None:
    _bundle(tmp_path)
    result = _run(["get", "--bundle", str(tmp_path), "okf-demo.md", "status"])
    assert result.exit_code == 0
    assert result.output.strip() == "Draft"


def test_cli_missing_concept_errors(tmp_path: Path) -> None:
    _bundle(tmp_path)
    result = _run(["get", "--bundle", str(tmp_path), "nope", "status"])
    assert result.exit_code != 0
    assert "no such concept" in result.output


def test_cli_set_bad_assignment_errors(tmp_path: Path) -> None:
    _bundle(tmp_path)
    result = _run(["set", "--bundle", str(tmp_path), "okf-demo", "statusRefined"])
    assert result.exit_code != 0
    assert "KEY=VALUE" in result.output


def test_cli_rejects_path_escape(tmp_path: Path) -> None:
    # A concept id that would resolve outside the bundle must be refused, not written.
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    _bundle(bundle)
    secret = tmp_path / "secret.md"
    secret.write_text("---\nstatus: Draft\n---\nbody\n", encoding="utf-8")
    result = _run(["set", "--bundle", str(bundle), "../secret", "status=Hacked"])
    assert result.exit_code != 0
    assert "escapes the bundle" in result.output
    assert "Hacked" not in secret.read_text()  # the outside file is untouched


def test_cli_nested_concept_id(tmp_path: Path) -> None:
    # Concept IDs can include a subdirectory (path relative to the bundle root).
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "x.md").write_text("---\nstatus: Draft\n---\nbody\n", encoding="utf-8")
    result = _run(["set", "--bundle", str(tmp_path), "sub/x", "status=Refined"])
    assert result.exit_code == 0
    assert "status: Refined" in (sub / "x.md").read_text()
