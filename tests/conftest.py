"""Shared pytest fixtures.

The offline ``mini`` bundle is hand-authored and always present. The upstream Google bundles
(``ga4`` etc.) are cloned on demand and gitignored, so tests that need them skip gracefully when
the clone is absent (see ``tests/fixtures/README.md``).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

import okdb
from okdb.database import Database

FIXTURES = Path(__file__).parent / "fixtures"
MINI_BUNDLE = FIXTURES / "mini"
GA4_BUNDLE = FIXTURES / "upstream" / "okf" / "bundles" / "ga4"
CRYPTO_BUNDLE = FIXTURES / "upstream" / "okf" / "bundles" / "crypto_bitcoin"


@pytest.fixture
def mini_path() -> Path:
    return MINI_BUNDLE


@pytest.fixture
def mini_db() -> Iterator[Database]:
    db = okdb.open(str(MINI_BUNDLE))
    yield db
    db.close()


@pytest.fixture
def ga4_path() -> Path:
    if not GA4_BUNDLE.is_dir():
        pytest.skip("ga4 upstream fixture not cloned (see tests/fixtures/README.md)")
    return GA4_BUNDLE


@pytest.fixture
def ga4_db(ga4_path: Path) -> Iterator[Database]:
    db = okdb.open(str(ga4_path))
    yield db
    db.close()


@pytest.fixture
def crypto_path() -> Path:
    if not CRYPTO_BUNDLE.is_dir():
        pytest.skip("crypto_bitcoin upstream fixture not cloned (see tests/fixtures/README.md)")
    return CRYPTO_BUNDLE
