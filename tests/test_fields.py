"""Tests for the frontmatter field editor (readb.fields) and its CLI (readb get/set/unset).

The editor is the one write path in an otherwise read-only tool, so these tests pin down two
things: edits are surgical (only the targeted lines move; body and lists stay byte-for-byte),
and the CLI addresses a concept by ID within a bundle without letting the path escape it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
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


def _bundle(tmp_path: Path, name: str = "okf-demo", text: str = TASK) -> Path:
    path = tmp_path / f"{name}.md"
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
# Multi-line values.
#
# A key's value can span several lines — a block sequence, a block scalar, a nested mapping.
# Editing only the "key:" line orphans the rest into invalid YAML, and the permissive loader
# then skips the concept silently, so the damage is invisible. Every edit therefore addresses
# the key's whole span.
# --------------------------------------------------------------------------------------------

# Each multi-line form, plus a column-0 sequence (the shape that first exposed the bug) and a
# comment that documents the key after it.
MULTILINE = """\
---
type: Task
blocked_by:
- alpha
- beta
note: |
  line one
  line two
owner:
  name: someone
  team: infra
# introduces the next key
after: tail
---

body
"""


def _yaml_loads(path: Path) -> dict:
    """Parse a file's frontmatter the way the loader does, failing the test if it is broken."""
    block = path.read_text(encoding="utf-8").split("---\n")[1]
    return yaml.safe_load(block)


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("blocked_by", "- alpha\n- beta"),
        ("note", "|\n  line one\n  line two"),
        ("owner", "  name: someone\n  team: infra"),
    ],
)
def test_get_returns_multiline_value_verbatim(tmp_path: Path, key: str, expected: str) -> None:
    # Regression: these used to come back as "", indistinguishable from an empty scalar.
    _bundle(tmp_path, text=MULTILINE)
    assert fields.get_field(tmp_path / "okf-demo.md", key) == expected


@pytest.mark.parametrize("key", ["blocked_by", "note", "owner"])
def test_set_refuses_multiline_key(tmp_path: Path, key: str) -> None:
    _bundle(tmp_path, text=MULTILINE)
    path = tmp_path / "okf-demo.md"
    with pytest.raises(fields.MultilineValueError, match=key):
        fields.set_fields(path, [(key, "scalar")])
    assert path.read_text(encoding="utf-8") == MULTILINE  # untouched


def test_set_multiline_refusal_is_all_or_nothing(tmp_path: Path) -> None:
    _bundle(tmp_path, text=MULTILINE)
    path = tmp_path / "okf-demo.md"
    with pytest.raises(fields.MultilineValueError):
        fields.set_fields(path, [("status", "Draft"), ("note", "scalar")])
    # The valid pair in the same call must not have landed.
    assert path.read_text(encoding="utf-8") == MULTILINE
    assert fields.get_field(path, "status") is None


@pytest.mark.parametrize("key", ["blocked_by", "note", "owner"])
def test_unset_removes_the_whole_span(tmp_path: Path, key: str) -> None:
    _bundle(tmp_path, text=MULTILINE)
    path = tmp_path / "okf-demo.md"
    fields.unset_fields(path, [key])
    parsed = _yaml_loads(path)  # still valid YAML — the orphaned-continuation bug
    assert key not in parsed
    assert parsed["type"] == "Task"
    assert parsed["after"] == "tail"


def test_unset_preserves_a_comment_documenting_the_next_key(tmp_path: Path) -> None:
    _bundle(tmp_path, text=MULTILINE)
    path = tmp_path / "okf-demo.md"
    fields.unset_fields(path, ["owner"])
    assert "# introduces the next key\nafter: tail\n" in path.read_text(encoding="utf-8")


def test_unset_column_zero_sequence_regression(tmp_path: Path) -> None:
    """The exact shape that broke: `blocked_by:` with its items unindented at column 0."""
    text = (
        "---\ntype: Task\nblocked_by:\n- publish-readb-0-1-0\ntimestamp: '2026-07-20'\n---\n\nb\n"
    )
    _bundle(tmp_path, text=text)
    path = tmp_path / "okf-demo.md"
    fields.unset_fields(path, ["blocked_by"])
    assert path.read_text(encoding="utf-8") == (
        "---\ntype: Task\ntimestamp: '2026-07-20'\n---\n\nb\n"
    )
    assert _yaml_loads(path) == {"type": "Task", "timestamp": "2026-07-20"}


def test_single_line_edits_stay_byte_identical_around_multiline_neighbours(tmp_path: Path) -> None:
    _bundle(tmp_path, text=MULTILINE)
    path = tmp_path / "okf-demo.md"
    fields.set_fields(path, [("type", "Note")])
    assert path.read_text(encoding="utf-8") == MULTILINE.replace("type: Task", "type: Note")


# --------------------------------------------------------------------------------------------
# The write-path guard: a rewrite may never turn valid frontmatter into invalid frontmatter.
# --------------------------------------------------------------------------------------------


def test_guard_abandons_a_write_that_would_break_the_frontmatter(tmp_path: Path) -> None:
    _bundle(tmp_path)
    path = tmp_path / "okf-demo.md"
    with pytest.raises(fields.FrontmatterError, match="left unchanged"):
        fields._rewrite(path, lambda lines: [*lines, "  oops: orphaned\n"])
    assert path.read_text(encoding="utf-8") == TASK


BROKEN = "---\ntype: Task\nstatus: Draft\n- orphan\n---\n\nbody\n"


def test_guard_still_allows_editing_an_already_broken_file(tmp_path: Path) -> None:
    # readb must not be the one tool that refuses to touch a damaged file: the guard forbids
    # *introducing* invalidity, not living with it. Keys away from the damage edit normally.
    _bundle(tmp_path, text=BROKEN)
    path = tmp_path / "okf-demo.md"
    fields.set_fields(path, [("type", "Note")])
    assert path.read_text(encoding="utf-8") == BROKEN.replace("type: Task", "type: Note")


def test_unset_repairs_a_file_broken_by_an_orphaned_continuation(tmp_path: Path) -> None:
    # `- orphan` reads as part of `status`'s value, so the whole span goes — which is exactly
    # the repair. (`set status=...` is refused on this file for the same reason: the key looks
    # multi-line. Unset first, then set, as the error says.)
    _bundle(tmp_path, text=BROKEN)
    path = tmp_path / "okf-demo.md"
    with pytest.raises(fields.MultilineValueError):
        fields.set_fields(path, [("status", "Done")])
    fields.unset_fields(path, ["status"])
    assert path.read_text(encoding="utf-8") == "---\ntype: Task\n---\n\nbody\n"
    assert _yaml_loads(path) == {"type": "Task"}


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
    result = _run(["set", "--bundle", str(bundle), "../secret.md", "status=Hacked"])
    assert result.exit_code != 0
    assert "escapes the bundle" in result.output
    # The bare spelling is rejected earlier: a name has no separators, a path needs .md.
    result = _run(["set", "--bundle", str(bundle), "../secret", "status=Hacked"])
    assert result.exit_code != 0
    assert "status: Hacked" not in secret.read_text()
    assert "Hacked" not in secret.read_text()  # the outside file is untouched


def test_cli_nested_concept_by_path_and_by_name(tmp_path: Path) -> None:
    # A nested concept is reachable by its full .md path or (when unique) by its simple name.
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "x.md").write_text("---\nstatus: Draft\n---\nbody\n", encoding="utf-8")
    result = _run(["set", "--bundle", str(tmp_path), "sub/x.md", "status=Refined"])
    assert result.exit_code == 0
    assert "status: Refined" in (sub / "x.md").read_text()
    result = _run(["set", "--bundle", str(tmp_path), "x", "status=Done"])
    assert result.exit_code == 0
    assert "status: Done" in (sub / "x.md").read_text()


def test_cli_name_with_separator_is_rejected(tmp_path: Path) -> None:
    # A bare name has no path separators; a path must carry its .md suffix.
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "x.md").write_text("---\nstatus: Draft\n---\nbody\n", encoding="utf-8")
    result = _run(["set", "--bundle", str(tmp_path), "sub/x", "status=Refined"])
    assert result.exit_code == 2
    assert ".md" in result.output


def test_cli_set_multiline_key_prints_a_clean_error(tmp_path: Path) -> None:
    # The refusal reaches the user as a one-line message, not a traceback, and names the way out.
    _bundle(tmp_path, text=MULTILINE)
    result = _run(["set", "--bundle", str(tmp_path), "okf-demo", "blocked_by=x"])
    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "blocked_by" in result.output and "unset the key first" in result.output
    assert (tmp_path / "okf-demo.md").read_text(encoding="utf-8") == MULTILINE


def test_cli_get_and_unset_handle_a_multiline_key(tmp_path: Path) -> None:
    _bundle(tmp_path, text=MULTILINE)
    result = _run(["get", "--bundle", str(tmp_path), "okf-demo", "blocked_by"])
    assert result.exit_code == 0
    assert result.output.strip() == "- alpha\n- beta"
    result = _run(["unset", "--bundle", str(tmp_path), "okf-demo", "blocked_by"])
    assert result.exit_code == 0
    assert _yaml_loads(tmp_path / "okf-demo.md")["after"] == "tail"


# --------------------------------------------------------------------------------------------
# Span boundaries: what ends a key's value.
#
# The boundary test asks whether a line *continues* the value above it, never whether it looks
# like a key readb recognizes. Keys outside a conservative identifier charset — dotted, spaced,
# quoted, non-ASCII — are ordinary YAML, and readb writes dotted ones itself.
# --------------------------------------------------------------------------------------------

NEIGHBOURS = """\
---
type: Book
status: read
tags:
- a
- b
og.title: 'Dune (1965)'
"my key": v1
full name: Frank
título: T
---

body
"""


# As parsed: the quoted key `"my key"` is the key `my key`.
@pytest.mark.parametrize("key", ["og.title", "my key", "full name", "título"])
def test_an_unusual_key_is_not_swallowed_into_its_neighbours_value(
    tmp_path: Path, key: str
) -> None:
    _bundle(tmp_path, text=NEIGHBOURS)
    path = tmp_path / "okf-demo.md"
    fields.unset_fields(path, ["tags"])
    assert key in _yaml_loads(path), f"unsetting a neighbour deleted {key!r}"


def test_a_scalar_next_to_an_unusual_key_stays_settable(tmp_path: Path) -> None:
    # Regression: the scalar `status` was refused as "multi-line" purely because the *next* line
    # held a dotted key the boundary test did not recognize.
    _bundle(tmp_path, text=NEIGHBOURS)
    path = tmp_path / "okf-demo.md"
    fields.set_fields(path, [("status", "unread")])
    assert _yaml_loads(path)["status"] == "unread"


@pytest.mark.parametrize(
    "opened",
    ["tags: {x: 1,\ny: 2}\n", "tags: [a,\nb]\n"],
    ids=["flow-mapping", "flow-sequence"],
)
def test_a_flow_collection_left_open_is_one_span(tmp_path: Path, opened: str) -> None:
    # These continue on lines that look like new entries, so bracket depth decides the boundary.
    # Removing only the first line left `y: 2}` behind — which still parses, inventing a column.
    _bundle(tmp_path, text=f"---\n{opened}status: open\n---\n\nbody\n")
    path = tmp_path / "okf-demo.md"
    fields.unset_fields(path, ["tags"])
    assert _yaml_loads(path) == {"status": "open"}


def test_a_brace_inside_a_block_scalar_does_not_extend_the_span(tmp_path: Path) -> None:
    # Depth tracking must engage only when the *key line* opens a collection.
    _bundle(tmp_path, text="---\nnote: |\n  a { b\nnext: x\n---\n\nbody\n")
    path = tmp_path / "okf-demo.md"
    fields.unset_fields(path, ["note"])
    assert _yaml_loads(path) == {"next": "x"}


def test_a_quoted_brace_is_not_an_open_collection(tmp_path: Path) -> None:
    _bundle(tmp_path, text="---\ntitle: 'a { b'\nstatus: open\n---\n\nbody\n")
    path = tmp_path / "okf-demo.md"
    fields.set_fields(path, [("status", "closed")])
    assert _yaml_loads(path) == {"title": "a { b", "status": "closed"}


# --------------------------------------------------------------------------------------------
# Byte-exactness of the write path.
# --------------------------------------------------------------------------------------------

CRLF = "---\r\ntype: Book\r\nstatus: open\r\n---\r\n\r\nbody\r\n"


def test_crlf_line_endings_survive_an_edit(tmp_path: Path) -> None:
    # "byte-for-byte intact" has to hold for the bytes nobody looked at, the body included.
    _bundle(tmp_path, text=CRLF)
    path = tmp_path / "okf-demo.md"
    fields.set_fields(path, [("status", "closed")])
    assert path.read_bytes() == CRLF.replace("status: open", "status: closed").encode()


def test_a_key_appended_to_a_crlf_file_gets_crlf(tmp_path: Path) -> None:
    _bundle(tmp_path, text=CRLF)
    path = tmp_path / "okf-demo.md"
    fields.set_fields(path, [("rating", "5")])
    assert path.read_bytes().endswith(b"---\r\n\r\nbody\r\n")
    assert b"rating: 5\r\n" in path.read_bytes()


def test_an_edit_that_changes_nothing_writes_nothing(tmp_path: Path) -> None:
    _bundle(tmp_path, text=CRLF)
    path = tmp_path / "okf-demo.md"
    before = path.stat().st_mtime_ns
    fields.unset_fields(path, ["totally-absent"])
    assert path.stat().st_mtime_ns == before
    assert path.read_bytes() == CRLF.encode()


def test_a_value_containing_a_line_break_is_refused(tmp_path: Path) -> None:
    # Written out it would become several lines, which YAML folds into different data entirely.
    _bundle(tmp_path)
    path = tmp_path / "okf-demo.md"
    with pytest.raises(fields.FrontmatterError, match="line break"):
        fields.set_fields(path, [("note", "a\nb")])
    assert path.read_text(encoding="utf-8") == TASK


def test_the_guard_covers_frontmatter_that_is_not_a_mapping(tmp_path: Path) -> None:
    # Parseable-but-not-a-mapping must not read as "already broken", which would switch the
    # guard off for precisely the edit that breaks it.
    text = "---\n- a\n- b\n---\n\nbody\n"
    _bundle(tmp_path, text=text)
    path = tmp_path / "okf-demo.md"
    with pytest.raises(fields.FrontmatterError, match="left unchanged"):
        fields.set_fields(path, [("status", "open")])
    assert path.read_text(encoding="utf-8") == text
