"""Tests for the shipped usage skill and the plugin manifests that distribute it.

Documentation rots quietly. These tests make the skill's promises mechanical: every SQL example
in it is executed against a fixture bundle, so an example that stops working fails the checks
instead of misleading an agent, and the manifests are checked to actually point at the skill.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

import readb

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "readb" / "SKILL.md"
PLUGIN_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = ROOT / ".claude-plugin" / "marketplace.json"
LIBRARY = Path(__file__).parent / "fixtures" / "library"

# `readb query "SELECT ..."` as it appears in the skill's shell examples.
_QUERY_EXAMPLE = re.compile(r'readb query "((?:[^"\\]|\\.)+)"')
# The command table documents the shape as `readb query "<SQL>"`; that placeholder is not an
# example. Only whole-argument placeholders are dropped — `WHERE year < 1980` must survive.
_PLACEHOLDER = re.compile(r"<[A-Z]+>")


def _skill_queries() -> list[str]:
    found = _QUERY_EXAMPLE.findall(SKILL.read_text(encoding="utf-8"))
    return [sql for sql in found if not _PLACEHOLDER.fullmatch(sql)]


def test_skill_exists_with_portable_frontmatter() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    frontmatter = text.split("---\n")[1]
    # name + description are the portable core every runtime understands.
    assert re.search(r"^name: readb$", frontmatter, re.MULTILINE)
    assert re.search(r"^description: \S", frontmatter, re.MULTILINE)


def test_every_query_example_is_extracted() -> None:
    # Guards the guard. A loose lower bound would let examples silently stop being executed as
    # the skill grows, so this counts every invocation in the file and demands they all match.
    text = SKILL.read_text(encoding="utf-8")
    written = text.count('readb query "')
    assert written == len(_QUERY_EXAMPLE.findall(text)), (
        "an example is written in a form the extractor does not match"
    )
    assert len(_skill_queries()) == written - 1  # minus the `<SQL>` placeholder in the table


@pytest.mark.parametrize("sql", _skill_queries(), ids=lambda s: s[:48])
def test_skill_query_examples_run(sql: str) -> None:
    db = readb.open(str(LIBRARY))
    try:
        # Rows, not merely the absence of an exception: an example returning nothing teaches
        # nothing, and would go on passing after the fixture or the data model moved under it.
        assert db.sql(sql), "the example runs but returns no rows"
    finally:
        db.close()


def test_skill_python_example_runs() -> None:
    # Extracted, not transcribed: a hardcoded copy would keep passing after the skill changed.
    block = re.search(r"```python\n(.*?)```", SKILL.read_text(encoding="utf-8"), re.DOTALL)
    assert block, "the skill's Python example is missing"
    source = block.group(1).replace('readb.open("./library")', f"readb.open({str(LIBRARY)!r})")
    namespace: dict[str, object] = {}
    exec(compile(source, "SKILL.md", "exec"), namespace)  # noqa: S102 - our own documentation
    assert namespace["rows"]


def test_skill_carries_no_project_process_material() -> None:
    # readb is general-purpose: its public surfaces never present this project's own workflow.
    text = SKILL.read_text(encoding="utf-8").lower()
    for term in ("sprint", "backlog", "maintainer", "adr"):
        assert term not in text, f"the shipped skill must not mention {term!r}"


def test_plugin_manifests_parse_and_point_at_the_skill() -> None:
    plugin = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    marketplace = json.loads(MARKETPLACE_MANIFEST.read_text(encoding="utf-8"))
    assert plugin["name"] == "readb"
    assert plugin["description"]
    entries = marketplace["plugins"]
    assert [entry["name"] for entry in entries] == ["readb"]
    # The single entry sources the plugin from the repository root, where plugin.json lives.
    source = entries[0]["source"]
    assert (ROOT / source / ".claude-plugin" / "plugin.json").is_file()
    assert (ROOT / source / "skills" / "readb" / "SKILL.md").is_file()


def test_plugin_version_tracks_the_package_version() -> None:
    # A plugin pinned to a stale version never reaches users who already installed it.
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    plugin = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    assert plugin["version"] == pyproject["project"]["version"]
