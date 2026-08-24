"""The persistent index cache (ADR 0006, task 034-persistent-index-cache).

Hits and misses are asserted by *observation* — a spy on the parser counts how many files were
read — never by timing. The property test at the end is the correctness argument for the
incremental path: after any edit sequence, the cached database must equal a fresh load.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest

import readb
from readb import cache
from readb.cli import main

pytestmark = pytest.mark.uses_cache


# --------------------------------------------------------------------------------------------
# Helpers.
# --------------------------------------------------------------------------------------------


def _bundle(root: Path, *, concepts: int = 6) -> Path:
    """A registry root with one bundle under it, as ``readb init`` would leave it."""
    bundle = root / "notes"
    bundle.mkdir(parents=True, exist_ok=True)
    for index in range(concepts):
        (bundle / f"note{index}.md").write_text(
            f"---\ntype: Note\ntitle: Note {index}\nrank: {index}\n---\nbody {index}\n",
            encoding="utf-8",
        )
    marker = root / ".readb"
    marker.mkdir(exist_ok=True)
    (marker / "config.toml").write_text('version = 1\nbundles = ["notes"]\n', encoding="utf-8")
    return bundle


class _ParseSpy:
    """Counts the files a load actually parses."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.parsed: list[str] = []
        import readb.cache as cache_module
        import readb.loader as loader_module

        original = loader_module.parse_file

        def counting(file_path: Path, *, bundle_root: Path):  # type: ignore[no-untyped-def]
            self.parsed.append(file_path.name)
            return original(file_path, bundle_root=bundle_root)

        # Both the loader and the cache's incremental path bound the name at import time.
        monkeypatch.setattr(loader_module, "parse_file", counting)
        monkeypatch.setattr(cache_module, "parse_file", counting)

    def reset(self) -> None:
        self.parsed.clear()


@pytest.fixture
def spy(monkeypatch: pytest.MonkeyPatch) -> Iterator[_ParseSpy]:
    yield _ParseSpy(monkeypatch)


def _rows(bundle: Path) -> list[dict]:
    with readb.open(str(bundle)) as db:
        return db.sql("SELECT __name, title, rank, __hash FROM note ORDER BY __name")


def _fresh_rows(bundle: Path) -> list[dict]:
    with readb.open(str(bundle), cache=False) as db:
        return db.sql("SELECT __name, title, rank, __hash FROM note ORDER BY __name")


# --------------------------------------------------------------------------------------------
# Consent: no registry, no writes. This is the read-only promise.
# --------------------------------------------------------------------------------------------


def test_without_a_registry_nothing_is_written_anywhere(tmp_path: Path) -> None:
    bundle = tmp_path / "loose"
    bundle.mkdir()
    (bundle / "a.md").write_text("---\ntype: Note\n---\nbody\n", encoding="utf-8")
    before = {p for p in tmp_path.rglob("*")}
    with readb.open(str(bundle)) as db:
        assert db.sql("SELECT count(*) AS n FROM note")[0]["n"] == 1
    assert {p for p in tmp_path.rglob("*")} == before
    assert cache.cache_dir_for(bundle) is None


def test_cache_false_in_the_config_disables_it(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    (tmp_path / ".readb" / "config.toml").write_text(
        'version = 1\nbundles = ["notes"]\ncache = false\n', encoding="utf-8"
    )
    with readb.open(str(bundle)) as db:
        db.sql("SELECT 1")
    assert cache.cache_dir_for(bundle) is None
    assert not (tmp_path / ".readb" / "cache").exists()


def test_no_cache_argument_neither_reads_nor_writes(tmp_path: Path, spy: _ParseSpy) -> None:
    bundle = _bundle(tmp_path)
    with readb.open(str(bundle), cache=False) as db:
        db.sql("SELECT 1")
    assert not (tmp_path / ".readb" / "cache").exists()
    spy.reset()
    with readb.open(str(bundle), cache=False) as db:
        db.sql("SELECT 1")
    assert len(spy.parsed) == 6  # every file, every time


# --------------------------------------------------------------------------------------------
# Hits and misses, observed through the parser.
# --------------------------------------------------------------------------------------------


def test_an_unchanged_bundle_parses_nothing_the_second_time(tmp_path: Path, spy: _ParseSpy) -> None:
    bundle = _bundle(tmp_path)
    with readb.open(str(bundle)) as db:
        first = db.sql("SELECT __name FROM note ORDER BY __name")
    spy.reset()
    with readb.open(str(bundle)) as db:
        second = db.sql("SELECT __name FROM note ORDER BY __name")
    assert spy.parsed == []
    assert first == second


def test_touching_every_file_reparses_nothing(tmp_path: Path, spy: _ParseSpy) -> None:
    """The mass-mtime case: a formatter, a copy or a checkout must not rewrite the cache."""
    bundle = _bundle(tmp_path)
    with readb.open(str(bundle)) as db:
        before = db.sql("SELECT __name, rank FROM note ORDER BY __name")
    for path in bundle.glob("*.md"):
        os_stat = path.stat()
        path.touch()
        assert path.stat().st_mtime_ns != os_stat.st_mtime_ns
    spy.reset()
    with readb.open(str(bundle)) as db:
        after = db.sql("SELECT __name, rank FROM note ORDER BY __name")
    assert spy.parsed == []
    assert before == after


def test_editing_one_file_reparses_only_that_file(tmp_path: Path, spy: _ParseSpy) -> None:
    bundle = _bundle(tmp_path)
    _rows(bundle)
    (bundle / "note2.md").write_text(
        "---\ntype: Note\ntitle: Edited\nrank: 2\n---\nnew body\n", encoding="utf-8"
    )
    spy.reset()
    rows = _rows(bundle)
    assert spy.parsed == ["note2.md"]
    assert [r["title"] for r in rows if r["__name"] == "note2"] == ["Edited"]
    assert rows == _fresh_rows(bundle)


def test_a_frontmatter_edit_through_readb_set_is_seen(tmp_path: Path) -> None:
    from click.testing import CliRunner

    bundle = _bundle(tmp_path)
    assert _rows(bundle)[0]["title"] == "Note 0"
    result = CliRunner().invoke(main, ["set", "--bundle", str(bundle), "note0", "title=Renamed"])
    assert result.exit_code == 0, result.output
    assert _rows(bundle)[0]["title"] == "Renamed"


def test_adding_and_deleting_files_is_applied(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    _rows(bundle)
    (bundle / "note9.md").write_text(
        "---\ntype: Note\ntitle: Nine\nrank: 9\n---\nbody\n", encoding="utf-8"
    )
    assert _rows(bundle) == _fresh_rows(bundle)
    (bundle / "note0.md").unlink()
    rows = _rows(bundle)
    assert "note0" not in [r["__name"] for r in rows]
    assert rows == _fresh_rows(bundle)


def test_a_new_key_falls_back_to_a_full_rebuild(tmp_path: Path, spy: _ParseSpy) -> None:
    """A producer key nothing carried before is a new column: not a local change."""
    bundle = _bundle(tmp_path)
    _rows(bundle)
    (bundle / "note1.md").write_text(
        "---\ntype: Note\ntitle: One\nrank: 1\nowner: ada\n---\nbody\n", encoding="utf-8"
    )
    spy.reset()
    with readb.open(str(bundle)) as db:
        rows = db.sql("SELECT __name, owner FROM note ORDER BY __name")
    # The changed file is parsed once while the incremental path decides, then the rebuild
    # parses everything: a full rebuild is what "every file was read" means here.
    assert {f"note{index}.md" for index in range(6)} <= set(spy.parsed)
    assert [r["owner"] for r in rows if r["__name"] == "note1"] == ["ada"]


def test_a_widening_type_falls_back_to_a_full_rebuild(tmp_path: Path, spy: _ParseSpy) -> None:
    """`rank` is BIGINT until a document makes it text; JSON is the lattice's meeting point."""
    bundle = _bundle(tmp_path)
    with readb.open(str(bundle)) as db:
        assert db.schema().tables["note"].columns["rank"] == "BIGINT"
    (bundle / "note3.md").write_text(
        "---\ntype: Note\ntitle: Three\nrank: high\n---\nbody\n", encoding="utf-8"
    )
    spy.reset()
    with readb.open(str(bundle)) as db:
        assert db.schema().tables["note"].columns["rank"] == "JSON"
    assert {f"note{index}.md" for index in range(6)} <= set(spy.parsed)


# --------------------------------------------------------------------------------------------
# Never fatal.
# --------------------------------------------------------------------------------------------


def test_a_corrupt_cache_answers_correctly_and_is_rebuilt(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    expected = _rows(bundle)
    cached = next((tmp_path / ".readb" / "cache").glob("*.duckdb"))
    cached.write_bytes(b"not a duckdb file at all")
    assert _rows(bundle) == expected
    assert _rows(bundle) == expected  # and the replacement is usable


def test_an_unwritable_cache_directory_is_not_an_error(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    directory = tmp_path / ".readb" / "cache"
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o500)
    try:
        assert _rows(bundle) == _fresh_rows(bundle)
    finally:
        directory.chmod(0o700)


def test_a_cache_hit_repeats_the_warnings_the_load_emitted(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Serving from a cache must not silently stop telling the user a file was skipped."""
    bundle = _bundle(tmp_path)
    (bundle / "broken.md").write_text("---\n: : :\nnot: [yaml\n---\nbody\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="readb"):
        readb.open(str(bundle)).close()
    assert any("broken.md" in record.getMessage() for record in caplog.records)
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="readb"):
        readb.open(str(bundle)).close()
    assert any("broken.md" in record.getMessage() for record in caplog.records)


def test_cache_bookkeeping_never_shows_up_in_a_user_facing_list(tmp_path: Path) -> None:
    """The cache's own tables are readb's, not the bundle's."""
    bundle = _bundle(tmp_path)
    _rows(bundle)
    with readb.open(str(bundle)) as db:
        assert all(not name.startswith("__readb_") for name in db.schema().tables)
        with pytest.raises(readb.UnknownTableError) as caught:
            db.sql("SELECT * FROM nope")
    assert "__readb_" not in str(caught.value)


def test_a_cache_hit_opens_read_only(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    _rows(bundle)
    with readb.open(str(bundle)) as db, pytest.raises(duckdb.Error):
        db.sql("CREATE TABLE persisted AS SELECT 1 AS a")


def test_only_one_cache_file_survives_per_bundle(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    for index in range(3):
        (bundle / "note0.md").write_text(
            f"---\ntype: Note\ntitle: v{index}\nrank: 0\n---\nbody\n", encoding="utf-8"
        )
        _rows(bundle)
    assert len(list((tmp_path / ".readb" / "cache").glob("*.duckdb"))) == 1


# --------------------------------------------------------------------------------------------
# status / clear.
# --------------------------------------------------------------------------------------------


def test_status_reports_absence_then_presence(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    assert cache.status(str(bundle))["path"] is None
    _rows(bundle)
    reported = cache.status(str(bundle))
    assert reported["enabled"] is True
    assert reported["current"] is True
    assert reported["bytes"] > 0


def test_status_explains_why_caching_is_off(tmp_path: Path) -> None:
    bundle = tmp_path / "loose"
    bundle.mkdir()
    (bundle / "a.md").write_text("---\ntype: Note\n---\nbody\n", encoding="utf-8")
    reported = cache.status(str(bundle))
    assert reported["enabled"] is False
    assert "readb init" in reported["reason"]


def test_clear_removes_the_cache_and_the_next_load_rebuilds(tmp_path: Path, spy: _ParseSpy) -> None:
    bundle = _bundle(tmp_path)
    _rows(bundle)
    assert cache.clear(str(bundle))
    assert cache.status(str(bundle))["path"] is None
    spy.reset()
    _rows(bundle)
    assert len(spy.parsed) == 6


# --------------------------------------------------------------------------------------------
# The property test: a cached database must equal a fresh one, after any edit sequence.
# --------------------------------------------------------------------------------------------


def _snapshot(bundle: Path, *, cached: bool) -> tuple:
    with readb.open(str(bundle), cache=cached) as db:
        schema = db.schema()
        shape = tuple(
            (name, tuple(table.columns.items())) for name, table in sorted(schema.tables.items())
        )
        contents = tuple(
            tuple(sorted(row.items(), key=lambda item: item[0]))
            for row in db.sql("SELECT * FROM __DOCUMENTS ORDER BY __path")
        )
    return shape, contents


@pytest.mark.parametrize("seed", range(8))
def test_incremental_result_equals_a_fresh_load(tmp_path: Path, seed: int) -> None:
    """Random edits, applied through the cache, must land where a full load would."""
    bundle = _bundle(tmp_path, concepts=8)
    _snapshot(bundle, cached=True)  # prime
    rng = random.Random(seed)
    for step in range(12):
        choice = rng.choice(["edit", "add", "delete", "touch", "newkey", "retype", "widen"])
        existing = sorted(bundle.glob("*.md"))
        if choice == "edit" and existing:
            target = rng.choice(existing)
            target.write_text(
                f"---\ntype: Note\ntitle: edited {step}\nrank: {step}\n---\nbody {step}\n",
                encoding="utf-8",
            )
        elif choice == "add":
            (bundle / f"added{step}.md").write_text(
                f"---\ntype: Note\ntitle: added {step}\nrank: {step}\n---\nbody\n",
                encoding="utf-8",
            )
        elif choice == "delete" and len(existing) > 1:
            rng.choice(existing).unlink()
        elif choice == "touch":
            for path in existing:
                path.touch()
        elif choice == "newkey" and existing:
            rng.choice(existing).write_text(
                f"---\ntype: Note\ntitle: keyed\nrank: 1\nextra{step}: yes\n---\nbody\n",
                encoding="utf-8",
            )
        elif choice == "retype" and existing:
            rng.choice(existing).write_text(
                f"---\ntype: Memo\ntitle: retyped {step}\n---\nbody\n", encoding="utf-8"
            )
        elif choice == "widen" and existing:
            rng.choice(existing).write_text(
                f"---\ntype: Note\ntitle: widened\nrank: [1, 2, {step}]\n---\nbody\n",
                encoding="utf-8",
            )
        assert _snapshot(bundle, cached=True) == _snapshot(bundle, cached=False), (
            f"seed {seed}, step {step}, action {choice}"
        )


# --------------------------------------------------------------------------------------------
# The CLI surface.
# --------------------------------------------------------------------------------------------


def test_cli_no_cache_flag_neither_reads_nor_writes(tmp_path: Path) -> None:
    from click.testing import CliRunner

    bundle = _bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        main, ["query", "SELECT count(*) AS n FROM note", "--bundle", str(bundle), "--no-cache"]
    )
    assert result.exit_code == 0, result.output
    assert not (tmp_path / ".readb" / "cache").exists()
    schema_result = runner.invoke(main, ["schema", "--bundle", str(bundle), "--no-cache"])
    assert schema_result.exit_code == 0
    assert not (tmp_path / ".readb" / "cache").exists()


def test_cli_cache_status_and_clear(tmp_path: Path) -> None:
    from click.testing import CliRunner

    bundle = _bundle(tmp_path)
    runner = CliRunner()
    before = runner.invoke(main, ["cache", "status", "--bundle", str(bundle)])
    assert "no cache written yet" in before.output
    _rows(bundle)
    after = runner.invoke(main, ["cache", "status", "--bundle", str(bundle)])
    assert "current" in after.output
    assert "files indexed" in after.output
    cleared = runner.invoke(main, ["cache", "clear", "--bundle", str(bundle)])
    assert "removed" in cleared.output
    assert runner.invoke(main, ["cache", "clear", "--bundle", str(bundle)]).output.strip() == (
        "nothing to clear"
    )


def test_cli_cache_status_says_why_it_is_off(tmp_path: Path) -> None:
    from click.testing import CliRunner

    bundle = tmp_path / "loose"
    bundle.mkdir()
    (bundle / "a.md").write_text("---\ntype: Note\n---\nbody\n", encoding="utf-8")
    result = CliRunner().invoke(main, ["cache", "status", "--bundle", str(bundle)])
    assert "caching off" in result.output
    assert "readb init" in result.output


def test_warnings_follow_the_files_that_produced_them(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A warning is repeated once per load, and disappears when its file is fixed."""
    bundle = _bundle(tmp_path)
    broken = bundle / "broken.md"
    broken.write_text("---\nnot: [yaml\n: :\n---\nbody\n", encoding="utf-8")
    readb.open(str(bundle)).close()

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="readb"):
        readb.open(str(bundle)).close()
    complaints = [r for r in caplog.records if "broken.md" in r.getMessage()]
    assert len(complaints) == 1, "the warning must be repeated exactly once, not duplicated"

    broken.write_text("---\ntype: Note\ntitle: Fixed\nrank: 1\n---\nbody\n", encoding="utf-8")
    readb.open(str(bundle)).close()
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="readb"):
        readb.open(str(bundle)).close()
    assert not [r for r in caplog.records if "broken.md" in r.getMessage()]
