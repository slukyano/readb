"""Smoke tests for the package skeleton.

These assert the public surface exists and is wired up; behavioral tests covering the
acceptance criteria in docs/design-brief.md arrive with the implementation.
"""

from __future__ import annotations

import readb


def test_version_is_exposed() -> None:
    assert isinstance(readb.__version__, str)
    assert readb.__version__


def test_open_is_callable() -> None:
    assert callable(readb.open)


def test_database_is_exported() -> None:
    assert hasattr(readb, "Database")


def test_version_matches_the_distribution_metadata() -> None:
    """`readb --version` must report the version that was actually packaged.

    A literal in `__init__.py` drifts the moment `pyproject.toml` is bumped without it, and
    nothing in the suite notices: the wrong number only appears when an installed build is run.
    """
    import tomllib
    from pathlib import Path

    import readb

    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
    assert readb.__version__ == declared


def test_cli_version_flag_reports_the_same_version() -> None:
    from click.testing import CliRunner

    import readb
    from readb.cli import main

    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert readb.__version__ in result.output
