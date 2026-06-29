"""Smoke tests for the package skeleton.

These assert the public surface exists and is wired up; behavioral tests covering the
acceptance criteria in docs/design-brief.md arrive with the implementation.
"""

from __future__ import annotations

import okdb


def test_version_is_exposed() -> None:
    assert isinstance(okdb.__version__, str)
    assert okdb.__version__


def test_open_is_callable() -> None:
    assert callable(okdb.open)


def test_database_is_exported() -> None:
    assert hasattr(okdb, "Database")
