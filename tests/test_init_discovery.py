"""readb init + registry discovery (ADR 0004): the marker, the merge, and bundle resolution."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner, Result

import readb
from readb.cli import main
from readb.registry import RegistryError, config_path, init_registry, resolve_bundle


def _run(*args: str) -> Result:
    return CliRunner().invoke(main, args)


def _bundle(root: Path, rel: str, name: str = "doc") -> Path:
    directory = root / rel
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name}.md").write_text(f"---\ntype: T\n---\n{rel} body\n", encoding="utf-8")
    return directory


# --------------------------------------------------------------------------------------------
# readb init: creation, merge, no-op, errors.
# --------------------------------------------------------------------------------------------


def test_init_no_args_declares_dot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bundle(tmp_path, ".")
    monkeypatch.chdir(tmp_path)
    result = _run("init")
    assert result.exit_code == 0, result.output
    config = config_path(tmp_path).read_text(encoding="utf-8")
    assert "version = 1" in config
    assert 'bundles = ["."]' in config


def test_init_declares_given_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bundle(tmp_path, "tasks")
    _bundle(tmp_path, "docs/adr")
    monkeypatch.chdir(tmp_path)
    result = _run("init", "tasks", "docs/adr")
    assert result.exit_code == 0, result.output
    assert 'bundles = ["tasks", "docs/adr"]' in config_path(tmp_path).read_text(encoding="utf-8")


def test_init_missing_dir_is_clean_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = _run("init", "no-such-dir")
    assert result.exit_code == 1
    assert "does not exist" in result.output
    assert not (tmp_path / ".readb").exists()  # nothing half-written


def test_reinit_merges_and_preserves_hand_edits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bundle(tmp_path, "tasks")
    _bundle(tmp_path, "extra")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks").exit_code == 0
    # Hand-add a key; the surgical merge must preserve it.
    path = config_path(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8") + 'default_bundle = "tasks"\n', encoding="utf-8"
    )
    result = _run("init", "extra")
    assert result.exit_code == 0, result.output
    config = path.read_text(encoding="utf-8")
    assert 'bundles = ["tasks", "extra"]' in config
    assert 'default_bundle = "tasks"' in config


def test_reinit_already_declared_is_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bundle(tmp_path, "tasks")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks").exit_code == 0
    before = config_path(tmp_path).read_text(encoding="utf-8")
    result = _run("init", "tasks")
    assert result.exit_code == 0, result.output
    assert "nothing to do" in result.output
    assert config_path(tmp_path).read_text(encoding="utf-8") == before


def test_init_outside_root_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bundle(tmp_path, "elsewhere")
    inner = tmp_path / "project"
    inner.mkdir()
    monkeypatch.chdir(inner)
    with pytest.raises(RegistryError, match="outside the registry root"):
        init_registry(inner, ["../elsewhere"])


# --------------------------------------------------------------------------------------------
# Discovery: containment, sole bundle, default_bundle, ambiguity, errors.
# --------------------------------------------------------------------------------------------


def test_discovery_from_inside_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tasks = _bundle(tmp_path, "tasks")
    _bundle(tmp_path, "docs/adr")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks", "docs/adr").exit_code == 0
    monkeypatch.chdir(tasks)
    result = _run("query", "SELECT __name FROM t", "--format", "raw")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "doc"


def test_discovery_from_subdirectory_of_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tasks = _bundle(tmp_path, "tasks")
    sub = tasks / "deep" / "er"
    sub.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks").exit_code == 0
    monkeypatch.chdir(sub)
    result = _run("query", "SELECT count(*) AS n FROM t", "--format", "raw")
    assert result.exit_code == 0, result.output


def test_discovery_sole_bundle_from_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bundle(tmp_path, "tasks")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks").exit_code == 0
    result = _run("query", "SELECT __name FROM t", "--format", "raw")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "doc"


def test_discovery_multi_bundle_root_errs_listing_bundles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bundle(tmp_path, "tasks")
    _bundle(tmp_path, "docs/adr")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks", "docs/adr").exit_code == 0
    result = _run("query", "SELECT 1")
    assert result.exit_code == 1
    assert "tasks" in result.output and "docs/adr" in result.output
    assert "--bundle" in result.output


def test_discovery_default_bundle_breaks_ambiguity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bundle(tmp_path, "tasks")
    _bundle(tmp_path, "docs/adr")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks", "docs/adr").exit_code == 0
    path = config_path(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8") + 'default_bundle = "docs/adr"\n', encoding="utf-8"
    )
    result = _run("query", "SELECT __name FROM t", "--format", "raw")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "doc"  # resolved to docs/adr


def test_discovery_innermost_bundle_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bundle(tmp_path, "outer", name="outer-doc")
    inner = _bundle(tmp_path, "outer/inner", name="inner-doc")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "outer", "outer/inner").exit_code == 0
    monkeypatch.chdir(inner)
    result = _run("query", "SELECT __name FROM t", "--format", "raw")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "inner-doc"


def test_no_registry_is_clean_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = _run("query", "SELECT 1")
    assert result.exit_code == 1
    assert "readb init" in result.output
    assert "--bundle" in result.output


def test_explicit_bundle_bypasses_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # An uninitialized directory stays queryable by naming it; the registry is never consulted.
    other = _bundle(tmp_path, "standalone")
    registry_root = tmp_path / "project"
    _bundle(registry_root, "tasks")
    monkeypatch.chdir(registry_root)
    assert _run("init", "tasks").exit_code == 0
    result = _run("query", "SELECT __name FROM t", "--bundle", str(other), "--format", "raw")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "doc"


def test_dangling_declared_bundle_is_clean_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doomed = _bundle(tmp_path, "tasks")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks").exit_code == 0
    (doomed / "doc.md").unlink()
    doomed.rmdir()
    result = _run("query", "SELECT 1")
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_malformed_config_is_clean_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bundle(tmp_path, "tasks")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks").exit_code == 0
    config_path(tmp_path).write_text("version = [broken\n", encoding="utf-8")
    result = _run("query", "SELECT 1")
    assert result.exit_code == 1
    assert "malformed" in result.output


def test_unknown_config_version_is_clean_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bundle(tmp_path, "tasks")
    monkeypatch.chdir(tmp_path)
    config_path(tmp_path).parent.mkdir()
    config_path(tmp_path).write_text('version = 99\nbundles = ["tasks"]\n', encoding="utf-8")
    result = _run("query", "SELECT 1")
    assert result.exit_code == 1
    assert "version" in result.output


def test_nested_registries_nearest_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _bundle(tmp_path, "outer-bundle", name="outer-doc")
    inner_root = tmp_path / "nested"
    inner_bundle = _bundle(inner_root, "inner-bundle", name="inner-doc")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "outer-bundle").exit_code == 0
    monkeypatch.chdir(inner_root)
    assert _run("init", "inner-bundle").exit_code == 0
    monkeypatch.chdir(inner_bundle)
    result = _run("query", "SELECT __name FROM t", "--format", "raw")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "inner-doc"


# --------------------------------------------------------------------------------------------
# Containment: the resolve path refuses what init refuses (review finding, sprint-002).
# --------------------------------------------------------------------------------------------


def test_config_with_dotdot_bundle_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    victim = _bundle(tmp_path, "victim")
    root = tmp_path / "project"
    root.mkdir()
    (root / ".readb").mkdir()
    (root / ".readb" / "config.toml").write_text(
        'version = 1\nbundles = ["../victim"]\n', encoding="utf-8"
    )
    monkeypatch.chdir(root)
    for args in (
        ("query", "SELECT 1"),
        ("set", "doc", "status=pwned"),
    ):
        result = _run(*args)
        assert result.exit_code == 1, result.output
        assert "outside the registry root" in result.output
    assert "pwned" not in (victim / "doc.md").read_text(encoding="utf-8")


def test_config_with_absolute_bundle_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bundle(tmp_path, "elsewhere")
    root = tmp_path / "project"
    root.mkdir()
    (root / ".readb").mkdir()
    (root / ".readb" / "config.toml").write_text(
        f'version = 1\nbundles = ["{tmp_path / "elsewhere"}"]\n', encoding="utf-8"
    )
    monkeypatch.chdir(root)
    result = _run("query", "SELECT 1")
    assert result.exit_code == 1
    assert "outside the registry root" in result.output


def test_config_with_symlinked_escape_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bundle(tmp_path, "victim")
    root = tmp_path / "project"
    root.mkdir()
    (root / "link").symlink_to(tmp_path / "victim", target_is_directory=True)
    (root / ".readb").mkdir()
    (root / ".readb" / "config.toml").write_text(
        'version = 1\nbundles = ["link"]\n', encoding="utf-8"
    )
    monkeypatch.chdir(root)
    result = _run("query", "SELECT 1")
    assert result.exit_code == 1
    assert "outside the registry root" in result.output


def test_default_bundle_not_declared_is_clean_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bundle(tmp_path, "tasks")
    _bundle(tmp_path, "docs")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks", "docs").exit_code == 0
    path = config_path(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8") + 'default_bundle = "nope"\n', encoding="utf-8"
    )
    result = _run("query", "SELECT 1")
    assert result.exit_code == 1
    assert "not one of the declared bundles" in result.output


def test_non_string_default_bundle_is_clean_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bundle(tmp_path, "tasks")
    monkeypatch.chdir(tmp_path)
    assert _run("init", "tasks").exit_code == 0
    path = config_path(tmp_path)
    path.write_text(path.read_text(encoding="utf-8") + "default_bundle = 3\n", encoding="utf-8")
    result = _run("query", "SELECT 1")
    assert result.exit_code == 1
    assert "default_bundle" in result.output


def test_merge_into_multiline_array_is_clean_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bundle(tmp_path, "tasks")
    _bundle(tmp_path, "extra")
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".readb").mkdir()
    config_path(tmp_path).write_text('version = 1\nbundles = [\n  "tasks",\n]\n', encoding="utf-8")
    result = _run("init", "extra")
    assert result.exit_code == 1
    assert "edit the file by hand" in result.output
    # And the file was not touched.
    assert '"extra"' not in config_path(tmp_path).read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------------
# The loader never sees .readb/.
# --------------------------------------------------------------------------------------------


def test_loader_skips_readb_dir(tmp_path: Path) -> None:
    _bundle(tmp_path, ".")
    cache_dir = tmp_path / ".readb" / "cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "phantom.md").write_text("---\ntype: T\n---\nnot a concept\n", encoding="utf-8")
    (tmp_path / ".readb" / "config.toml").write_text(
        'version = 1\nbundles = ["."]\n', encoding="utf-8"
    )
    db = readb.open(str(tmp_path))
    try:
        rows = db.sql("SELECT __path FROM __DOCUMENTS")
        assert [r["__path"] for r in rows] == ["doc.md"]
    finally:
        db.close()


def test_resolve_bundle_direct_api(tmp_path: Path) -> None:
    tasks = _bundle(tmp_path, "tasks")
    init_registry(tmp_path, ["tasks"])
    assert resolve_bundle(tasks) == tasks.resolve()
    assert resolve_bundle(tmp_path) == tasks.resolve()
