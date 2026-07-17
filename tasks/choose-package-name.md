---
type: Task
title: Choose a package name (okdb is taken)
description: Pick and verify an available distribution name; okdb is already taken on PyPI.
status: Done
priority: high
tags:
- packaging
- naming
created: 2026-06-29
blocked_by: []
timestamp: '2026-07-17T00:00:00Z'
---

`okdb` is taken on PyPI, so we need a different distribution name before we can publish.

This task **blocks** [Create a distributable package](/distributable-package.md).

## Context

- The import package and the CLI binary can keep `okdb` locally, but the *distribution* name
  must be unique on the index we publish to.
- Want a short, memorable name that still signals "OKF + SQL".

## Notes / candidates (to refine)

- Confirm availability on PyPI before committing.
- Decide whether the CLI command and the import name change too, or only the dist name.

## Design

Decided 2026-07-10 — see [ADR 0002](../docs/adr/0002-package-name-readb.md) for the full
research (PyPI/npm/crates/GitHub/web) and rationale.

**The name is `readb`** ("readable / reads your files + db"), aligned across dist, import, and
CLI: `pip install readb`, `import readb`, `readb query ...`. Not pitched as "read-only" — the
name means the database *stays human-readable* (files are the storage), which survives the
existing frontmatter editor and future inserts.

Implementation (do this task **first** in the sprint, so every other task lands on the new
name):

1. `pyproject.toml`: `name = "readb"`, `[project.scripts] readb = "readb.cli:main"`.
2. `src/okdb/` → `src/readb/`; update all imports, docstrings, and CLI prog name.
3. Tests: imports + any `okdb`-literal assertions (CLI invocation, version string).
4. Docs: README, CLAUDE.md, `docs/design-brief.md` headline references, `tasks/workflow.md`
   command examples, `tasks/index.md` prose.
5. `uv sync` (regenerate the entry point), then full gates.

Out of scope: renaming the GitHub repo / local directory (human's call; nothing in the code
depends on it), and staking the PyPI name (first step of `distributable-package`).
