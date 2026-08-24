"""The load path must not re-attempt a failed import for every value it binds.

Backlog task ``036-load-pandas-import-probe``: DuckDB's Python client probes each non-NULL bound
value for pandas types, and Python never caches a failed import, so with pandas absent every probe
walks ``sys.path`` again. These are *counting* tests rather than timing tests — deterministic, and
they fail loudly if a future duckdb release moves the probe somewhere the guard does not cover.
"""

from __future__ import annotations

import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

from readb.loader import _suppress_pandas_probe, load_bundle


class _ImportSpy:
    """A ``sys.meta_path`` finder that counts lookups without resolving any of them."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()

    def find_spec(self, name: str, path: object = None, target: object = None) -> None:
        self.counts[name] += 1
        return None


@pytest.fixture
def import_spy() -> Iterator[_ImportSpy]:
    spy = _ImportSpy()
    sys.meta_path.insert(0, spy)
    try:
        yield spy
    finally:
        sys.meta_path.remove(spy)


def test_load_never_probes_for_pandas(mini_path: Path, import_spy: _ImportSpy) -> None:
    if "pandas" in sys.modules:
        pytest.skip("pandas is importable here; the probe resolves once and is cached")
    import_spy.counts.clear()
    connection, _ = load_bundle(str(mini_path))
    connection.close()
    assert import_spy.counts["pandas"] == 0


def test_guard_leaves_sys_modules_as_it_found_it(mini_path: Path) -> None:
    if "pandas" in sys.modules:
        pytest.skip("pandas is importable here")
    connection, _ = load_bundle(str(mini_path))
    connection.close()
    assert "pandas" not in sys.modules


def test_guard_is_inert_when_pandas_is_already_imported() -> None:
    """A caller who uses pandas keeps it: the sentinel is never installed over a real module."""
    stub = ModuleType("pandas")
    sys.modules["pandas"] = stub
    try:
        with _suppress_pandas_probe():
            assert sys.modules["pandas"] is stub
        assert sys.modules["pandas"] is stub
    finally:
        del sys.modules["pandas"]


def test_guard_restores_after_an_exception() -> None:
    if "pandas" in sys.modules:
        pytest.skip("pandas is importable here")
    with pytest.raises(RuntimeError), _suppress_pandas_probe():
        raise RuntimeError("boom")
    assert "pandas" not in sys.modules


def test_sentinel_is_not_left_behind() -> None:
    """Inside the guard an import fails on the sentinel; outside it fails normally, if at all."""
    if "pandas" in sys.modules:
        pytest.skip("pandas is importable here")
    with _suppress_pandas_probe(), pytest.raises(ImportError):
        import pandas  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        import pandas  # noqa: F401,F811
