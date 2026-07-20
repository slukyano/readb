"""The bundle registry: ``readb init`` and upward discovery (ADR 0004).

A directory becomes a *registry root* when the user runs ``readb init`` in it, which writes
``.readb/config.toml`` declaring one or more bundle directories by relative path. Commands
invoked without ``--bundle`` walk up from the cwd to the nearest registry and resolve the
bundle from it; explicit ``--bundle`` never consults the registry.

``init`` is a sanctioned write in the ``set``/``unset`` tradition: its own explicit command,
never a side effect of load or query. Re-init merges new paths and never removes; the merge is
a surgical line edit (only the ``bundles = [...]`` line changes), so hand-added keys like
``default_bundle`` survive. Stdlib only: ``tomllib`` to read, a constrained writer for the one
line we own.

Beyond ``config.toml``, ``.readb/`` is reserved for the future persistent index/cache; the
loader skips the directory entirely.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

MARKER_DIR = ".readb"
CONFIG_NAME = "config.toml"
CONFIG_VERSION = 1


class RegistryError(Exception):
    """A registry problem the user must resolve; the message is CLI-ready."""


@dataclass(frozen=True)
class RegistryConfig:
    root: Path  # the directory containing .readb/
    bundles: tuple[str, ...]  # declared bundle dirs, POSIX-relative to root
    default_bundle: str | None


def config_path(root: Path) -> Path:
    return root / MARKER_DIR / CONFIG_NAME


def find_registry(start: Path) -> Path | None:
    """Walk up from ``start`` to the filesystem root; return the nearest registry root."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / MARKER_DIR).is_dir():
            return candidate
    return None


def load_config(root: Path) -> RegistryConfig:
    """Read and validate ``.readb/config.toml`` under ``root``. Unknown keys are tolerated."""
    path = config_path(root)
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError:
        raise RegistryError(
            f"registry marker {root / MARKER_DIR} exists but has no {CONFIG_NAME}; "
            f"re-run 'readb init' there or pass --bundle <dir>"
        ) from None
    except tomllib.TOMLDecodeError as exc:
        raise RegistryError(f"malformed registry config {path}: {exc}") from exc

    version = data.get("version")
    if version != CONFIG_VERSION:
        raise RegistryError(
            f"unsupported registry config version {version!r} in {path} "
            f"(this readb understands version {CONFIG_VERSION})"
        )
    bundles = data.get("bundles")
    if not isinstance(bundles, list) or not all(isinstance(b, str) for b in bundles) or not bundles:
        raise RegistryError(f"registry config {path} must declare 'bundles' as a list of paths")
    default = data.get("default_bundle")
    if default is not None and not isinstance(default, str):
        raise RegistryError(f"registry config {path}: 'default_bundle' must be a string")
    # Containment: the resolve path must refuse what init refuses — a checked-in config the
    # invoking user did not author must never point reads (or set/unset writes) outside the
    # registry root, via '..', absolute paths, or symlinked bundle dirs.
    root_resolved = root.resolve()
    for entry in bundles:
        target = (root_resolved / entry).resolve()
        if not target.is_relative_to(root_resolved):
            raise RegistryError(
                f"registry config {path}: bundle {entry!r} resolves outside the registry "
                f"root ({target}); declared bundles must live within it"
            )
    return RegistryConfig(root=root, bundles=tuple(bundles), default_bundle=default)


def resolve_bundle(cwd: Path) -> Path:
    """Resolve the bundle for a command invoked without ``--bundle`` (ADR 0004).

    Nearest registry wins; within it: the declared bundle containing ``cwd`` (innermost wins),
    else the sole declared bundle, else ``default_bundle``, else a hard error listing the
    declared bundles. Ambiguity always errs, never guesses.
    """
    root = find_registry(cwd)
    if root is None:
        raise RegistryError(
            f"no bundle specified and no {MARKER_DIR}/ registry found from {cwd} upward; "
            f"run 'readb init' in your project root or pass --bundle <dir>"
        )
    config = load_config(root)

    def declared_path(entry: str) -> Path:
        return (root / entry).resolve()

    cwd_resolved = cwd.resolve()
    containing = [b for b in config.bundles if cwd_resolved.is_relative_to(declared_path(b))]
    if containing:
        chosen = max(containing, key=lambda b: len(declared_path(b).parts))  # innermost wins
    elif len(config.bundles) == 1:
        chosen = config.bundles[0]
    elif config.default_bundle is not None:
        if config.default_bundle not in config.bundles:
            raise RegistryError(
                f"default_bundle {config.default_bundle!r} in {config_path(root)} is not one of "
                f"the declared bundles: {', '.join(config.bundles)}"
            )
        chosen = config.default_bundle
    else:
        raise RegistryError(
            f"multiple bundles declared in {config_path(root)}: {', '.join(config.bundles)}; "
            f"pass --bundle <dir> or set default_bundle in the config"
        )

    bundle_dir = declared_path(chosen)
    if not bundle_dir.is_dir():
        raise RegistryError(
            f"bundle {chosen!r} declared in {config_path(root)} does not exist: {bundle_dir}"
        )
    return bundle_dir


def _bundles_line(bundles: list[str]) -> str:
    quoted = ", ".join(f'"{b}"' for b in bundles)
    return f"bundles = [{quoted}]"


def init_registry(root: Path, bundle_dirs: list[str]) -> str:
    """Create or extend the registry at ``root`` (the ``readb init`` write). Returns a summary.

    New config: version + the given bundles. Existing config: merge new entries into the
    ``bundles = [...]`` line only (a surgical line edit — every other line, including
    hand-added keys, is preserved verbatim); already-declared entries are a no-op.
    """
    entries: list[str] = []
    for raw in bundle_dirs:
        target = (root / raw).resolve()
        if not target.is_dir():
            raise RegistryError(f"bundle directory does not exist: {raw!r} ({target})")
        if not target.is_relative_to(root.resolve()):
            raise RegistryError(f"bundle {raw!r} lies outside the registry root {root}")
        relative = target.relative_to(root.resolve()).as_posix()
        entries.append(relative if relative != "." else ".")

    path = config_path(root)
    if not path.exists():
        path.parent.mkdir(exist_ok=True)
        content = (
            f"# readb bundle registry (readb init; see ADR 0004)\n"
            f"version = {CONFIG_VERSION}\n"
            f"{_bundles_line(entries)}\n"
        )
        path.write_text(content, encoding="utf-8")
        return f"initialized {path} with bundles: {', '.join(entries)}"

    existing = load_config(root)  # validates before we touch anything
    new_entries = [e for e in entries if e not in existing.bundles]
    if not new_entries:
        return f"{path} already declares: {', '.join(entries)} (nothing to do)"

    merged = [*existing.bundles, *new_entries]
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for index, line in enumerate(lines):
        key, equals, value = line.partition("=")
        # Only a complete single-line array is safely replaceable; the opening line of a
        # multi-line array also starts with 'bundles =' and must NOT match (silent corruption).
        if key.strip() == "bundles" and equals and value.strip().endswith("]"):
            newline = "\n" if line.endswith("\n") else ""
            lines[index] = _bundles_line(merged) + newline
            break
    else:
        raise RegistryError(
            f"cannot merge into {path}: no single-line 'bundles = [...]' found "
            f"(multi-line arrays are not supported by the surgical merge; edit the file by hand)"
        )
    path.write_text("".join(lines), encoding="utf-8")
    return f"added {', '.join(new_entries)} to {path} (now: {', '.join(merged)})"
