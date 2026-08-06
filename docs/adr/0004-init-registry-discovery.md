---
type: ADR
title: 'Explicit readb init writes a bundle registry; discovery walks up to it; --bundle stays explicit consent'
status: Accepted
created: 2026-07-20
sprint: sprint-002
timestamp: '2026-07-20T00:00:00Z'
---

# Context

Sprint-001 implemented, then reverted, defaulting `--bundle` to the cwd
([default-bundle-cwd](../../backlog/archive/002-default-bundle-cwd.md), Dropped): a cwd default silently
treats *any* directory as a bundle — wrong-scope reads and misdirected name-resolved writes.
The successor idea ([bundle-init-discovery](../../backlog/archive/013-bundle-init-discovery.md)) is the git
model: a directory is a bundle because the user said so once, via an explicit `init`, and
commands without `--bundle` walk up to that marker.

Designing it against our most common case — **one git repo containing several bundles**
(this repo: `tasks/` and `docs/adr/`) — showed that one marker *inside each bundle* serves it
poorly: from the repo root (where the user stands) upward discovery finds nothing, the marker
is tool droppings inside a publishable OKF artifact, and N bundles mean N markers, N gitignore
entries, N future cache homes. Treating the whole repo as one bundle is worse: every stray
`README.md` becomes a phantom concept and per-bundle `index.md`/`log.md` semantics break.

Prior art: Backlog.md's explicit `init` (choose folder, config preserved on re-init, scriptable
flags); the `.obsidian/`/`.backlog/` dotdir-marker norm
([research-similar-tools](../../backlog/archive/006-research-similar-tools.md)).

# Decision

**`readb init [BUNDLE_DIR...]` creates a single `.readb/` registry in the current directory**,
whose `config.toml` declares the bundle directories by relative path (no args → `["."]` — the
single-bundle case is the same model, not a special case). It is a **sanctioned write** in the
`set`/`unset` tradition: its own explicit command, never a side effect of load or query.
Explicit paths only; no auto-detection. Re-init merges and never removes.

```toml
# .readb/config.toml  (committed; read with stdlib tomllib)
version = 1
bundles = ["tasks", "docs/adr"]
# default_bundle = "tasks"   # optional, opt-in by editing the file
```

**`--bundle` becomes optional.** When omitted, discovery walks **up** from cwd to the nearest
`.readb/` (filesystem root is the only stop; nested registries — nearest wins), then picks:
the declared bundle containing cwd (innermost wins); else the sole declared bundle; else
`default_bundle`; else a **hard error listing the declared bundles**. No marker → a clear
error suggesting `readb init` or `--bundle`. Ambiguity always errs, never guesses.

**Explicit `--bundle <dir>` never consults the registry** and works on any directory,
initialized or not — naming the path is consent, and a freshly cloned OKF bundle must stay
queryable untouched.

The loader skips `.readb/` during the bundle walk. Beyond `config.toml`, `.readb/` is reserved
as the future home of the persistent index/cache (wrap `load_bundle`, per the design brief) —
the marker is the cache's home arriving early.

# Consequences

- Running readb from anywhere inside an initialized repo works without `--bundle`, including
  subdirectories — which the reverted cwd default never did — while `$HOME` or a repo root can
  never silently become a bundle.
- One committed config per repo; bundles themselves stay pristine (no tool files inside the
  OKF artifact); the future cache gets a single predictable location.
- A multi-bundle root without `default_bundle` requires either `--bundle` or an explicit
  config choice — deliberate friction where the intent is genuinely ambiguous.
- New failure modes are loud: malformed/unknown-`version` config, dangling declared bundle,
  ambiguous multi-bundle root — all clear errors at use, none load-time-fatal for `--bundle`
  users.
- Registry names open a path to cross-bundle querying (attach each bundle as a DuckDB schema)
  — deferred to [cross-bundle-querying](../../backlog/tasks/021-cross-bundle-querying.md).

# Alternatives considered

- **Marker inside each bundle** (`.obsidian/` style): rejected — no repo-root ergonomics,
  pollutes the publishable artifact, N markers/caches.
- **Whole repo as one bundle**: rejected — phantom concepts, broken per-bundle reserved-file
  semantics, likelier name clashes.
- **cwd default** (sprint-001): already rejected in practice — silent wrong-scope operations.
