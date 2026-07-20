---
type: Task
title: Explicit readb init + upward bundle discovery
description: An init command marks a directory as a bundle; commands without --bundle walk up to the marker (git-style). The marker doubles as the persistent-index home.
status: Draft
priority: medium
tags:
- cli
- dx
- index
created: 2026-07-11
timestamp: '2026-07-11T00:00:00Z'
---

Replace the reverted cwd-defaulting of `--bundle` ([default-bundle-cwd](default-bundle-cwd.md),
Dropped) with the git model: a directory is a bundle because the user said so once.

## Context

- `readb init` is an explicit, sanctioned write (the `set`/`unset` precedent: its own command,
  never a side effect of load/query). It drops a marker in the bundle root — e.g. a `.readb/`
  directory.
- Commands without `--bundle` walk **up** from the cwd to the nearest marker; no marker →
  a clear error suggesting `readb init` or `--bundle`. Works from subdirectories, which the
  plain cwd default never did; never silently treats a repo root or `$HOME` as a bundle.
- Explicit `--bundle <dir>` keeps working on any directory, uninitialized or not — naming the
  path is consent (must still be able to query a freshly cloned OKF bundle untouched).
- The marker directory is exactly where the future **persistent index/cache** lives
  (`load_bundle` is the seam to wrap, per the design brief) — the marker is the cache's home
  arriving early, not ceremony.

## Notes (to refine)

- Marker format and contents (empty dir? a small versioned config file?); keep it `.md`-free so
  the loader never sees it.
- Discovery stop conditions (filesystem root; home dir?); behavior when nested markers exist.
- Whether `init` gets any options (e.g. future: index settings) — default to none.
- ADR: this changes the CLI contract and creates a new sanctioned write; supersedes/extends
  the relevant part of the dropped task's design.

## Design (2026-07-20, sprint-002)

**Decision (human-approved in chat): the registry model.** One `readb init` at a root directory
(typically the repo root) creates a single `.readb/` marker whose config *declares the bundles*
by relative path. Not one marker per bundle (tool droppings inside a publishable artifact; no
help from the repo root), and never "whole repo as one bundle" (phantom concepts from README/
docs; per-bundle `index.md`/`log.md` semantics). The single-bundle case is the same model, not a
special case: `readb init` inside a bundle writes `bundles = ["."]`.
See [ADR 0004](../docs/adr/0004-init-registry-discovery.md).

### The command

`readb init [BUNDLE_DIR...]` — a new **sanctioned write** (its own command, like `set`/`unset`;
never a side effect of load/query). Run in the directory that should own the registry:

- Creates `.readb/config.toml` in the **current directory** declaring the given bundle dirs
  (paths relative to the registry root, POSIX separators). No args → `bundles = ["."]`.
- Explicit paths only — **no auto-detection** of what "looks like" a bundle.
- Named dirs must exist (clear error otherwise); no validation that they are "real" OKF bundles
  (permissive — an empty dir is a valid, empty bundle).
- **Re-init merges**: new paths are added to an existing config, existing entries are never
  removed or rewritten; re-running with already-declared paths is a friendly no-op. Removal =
  edit the config file by hand (it is a plain committed file). Prints what it did.

### The config

```toml
# .readb/config.toml
version = 1
bundles = ["tasks", "docs/adr"]
# default_bundle = "tasks"   # optional
```

- Read with stdlib `tomllib` (Python >=3.11; no new dependency). Unknown keys tolerated
  (permissive). A malformed config or a `version` we don't know → clear error at use.
- `.readb/config.toml` is meant to be **committed**; the rest of `.readb/` is reserved for the
  future persistent index/cache (`load_bundle` is the seam), which will be git-ignored when it
  arrives — out of scope here.

### Discovery (commands without `--bundle`)

`--bundle` becomes **optional** on all commands. When omitted:

1. Walk **up** from cwd to the filesystem root (git-style, no `$HOME` special case); the nearest
   directory containing `.readb/` is the registry root. Nested registries: nearest wins. None
   found → error: not inside a readb registry; run `readb init` or pass `--bundle <dir>`.
2. Resolve declared bundles relative to the registry root. Then:
   - cwd inside exactly one declared bundle → that bundle (nested declared bundles: the most
     specific/innermost wins);
   - cwd outside all declared bundles and exactly **one** bundle declared → that one;
   - else, if `default_bundle` is set (and is one of the declared paths) → it;
   - else → **hard error listing the declared bundles** ("which bundle?" from a multi-bundle
     root is genuinely ambiguous; explicit over magic). `init` does not prompt for or set
     `default_bundle`; it is opt-in by editing the config.
3. A declared bundle dir that no longer exists → clear error at use (no load-time registry
   validation).

Explicit `--bundle <dir>` is unchanged and never consults the registry — naming the path is
consent; a freshly cloned, uninitialized OKF bundle stays queryable.

### Loader

`load_bundle` explicitly skips any `.readb/` directory during the walk, so future cache files
can never be parsed as concepts. (No broader hidden-dir policy change — just `.readb/`.)

### Tests (implementation)

init creates/merges config; no-op re-init; discovery from inside a bundle, from a single-bundle
root, from a multi-bundle root (error lists bundles), with `default_bundle`, with nested
registries (nearest wins), uninitialized (clear error); `--bundle` bypasses the registry;
loader skips `.readb/`; malformed config and unknown `version` produce clean CLI errors.

### Dogfooding follow-through

After implementation: run `readb init tasks docs/adr` in this repo and commit
`.readb/config.toml`, then drop the now-redundant `--bundle ./tasks` from the documented
common commands (CLAUDE.md / workflow.md examples can use bare discovery from the repo root
only where unambiguous — with two bundles declared and no default, keep explicit `--bundle`
in examples, or set `default_bundle = "tasks"`; decide at implementation with the human if it
matters).

**Spun off:** cross-bundle querying (attach each declared bundle as a DuckDB schema; join
`tasks.task` × `adr.adr`) → draft [cross-bundle-querying](cross-bundle-querying.md).
