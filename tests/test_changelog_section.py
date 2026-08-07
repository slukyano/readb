"""Tests for the release-notes extractor (scripts/changelog_section.py).

The release workflow turns its output into the GitHub release body, so a silent
mis-extraction would ship wrong or empty notes. Failure has to be loud.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from changelog_section import extract, main  # noqa: E402

CHANGELOG = """\
# Changelog

Preamble that belongs to no version.

## [Unreleased]

## [0.2.0] - 2026-08-07

### Fixed

- A thing that was broken.

## [0.1.0] - 2026-07-21

Initial release.

[Unreleased]: https://example.invalid/compare/v0.2.0...HEAD
[0.2.0]: https://example.invalid/releases/tag/v0.2.0
"""


def test_extracts_only_the_named_section() -> None:
    assert extract(CHANGELOG, "0.2.0") == "### Fixed\n\n- A thing that was broken."


def test_last_section_stops_before_link_definitions() -> None:
    assert extract(CHANGELOG, "0.1.0") == "Initial release."


def test_missing_section_raises() -> None:
    with pytest.raises(LookupError, match="9.9.9"):
        extract(CHANGELOG, "9.9.9")


def test_empty_section_is_not_notes() -> None:
    assert extract(CHANGELOG, "Unreleased") == ""


def test_cli_fails_loudly_on_an_empty_section(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    path = tmp_path / "CHANGELOG.md"
    path.write_text(CHANGELOG, encoding="utf-8")
    assert main(["Unreleased", str(path)]) == 1
    assert "empty" in capsys.readouterr().err


def test_cli_prints_the_section(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    path = tmp_path / "CHANGELOG.md"
    path.write_text(CHANGELOG, encoding="utf-8")
    assert main(["0.2.0", str(path)]) == 0
    assert capsys.readouterr().out.strip() == "### Fixed\n\n- A thing that was broken."


def test_the_projects_own_changelog_has_extractable_release_notes() -> None:
    # Pins the real file's shape: the released section must survive extraction.
    assert extract((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), "0.1.0")
