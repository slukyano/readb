"""Shared pytest fixtures.

The offline ``mini`` bundle is hand-authored and always present. The upstream Google bundles
(``ga4`` etc.) are cloned on demand and gitignored, so tests that need them skip gracefully when
the clone is absent (see ``tests/fixtures/README.md``).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

import readb
from readb.database import Database

FIXTURES = Path(__file__).parent / "fixtures"
MINI_BUNDLE = FIXTURES / "mini"
GA4_BUNDLE = FIXTURES / "upstream" / "okf" / "bundles" / "ga4"
CRYPTO_BUNDLE = FIXTURES / "upstream" / "okf" / "bundles" / "crypto_bitcoin"


@pytest.fixture(autouse=True)
def _cache_off_unless_asked(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep the repository's own ``.readb/`` registry out of the tests that are not about it.

    The fixtures live inside this repository, which *is* a readb registry, so an unguarded test
    would both write cache files into the working tree and exercise a code path it never meant
    to. Tests that are about the cache carry ``@pytest.mark.uses_cache`` and see it for real.
    """
    if request.node.get_closest_marker("uses_cache"):
        return
    monkeypatch.setattr("readb.cache.cache_dir_for", lambda *_args, **_kwargs: None)


@pytest.fixture
def mini_path() -> Path:
    return MINI_BUNDLE


@pytest.fixture
def mini_db() -> Iterator[Database]:
    db = readb.open(str(MINI_BUNDLE))
    yield db
    db.close()


@pytest.fixture
def ga4_path() -> Path:
    if not GA4_BUNDLE.is_dir():
        pytest.skip("ga4 upstream fixture not cloned (see tests/fixtures/README.md)")
    return GA4_BUNDLE


@pytest.fixture
def ga4_db(ga4_path: Path) -> Iterator[Database]:
    db = readb.open(str(ga4_path))
    yield db
    db.close()


@pytest.fixture
def crypto_path() -> Path:
    if not CRYPTO_BUNDLE.is_dir():
        pytest.skip("crypto_bitcoin upstream fixture not cloned (see tests/fixtures/README.md)")
    return CRYPTO_BUNDLE
