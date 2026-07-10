---
type: ADR
title: Name the package readb (dist, import, and CLI aligned)
status: Accepted
created: 2026-07-10
sprint: sprint-001
timestamp: '2026-07-10T00:00:00Z'
---

# Context

`okdb` is taken on PyPI, so the project needs a different distribution name before it can
publish ([choose-package-name](../../tasks/choose-package-name.md), blocking
[distributable-package](../../tasks/distributable-package.md)). The human set the naming
direction — "DB to read my markdown/OKF bundles"; keywords *markdown, knowledge, read, plain,
human-readable, simple*; explicitly no `-ql` names (we are not building a query language — DuckDB
executes all SQL).

Candidates were checked against PyPI, npm, crates.io, GitHub repo names, and the web
(2026-07-09/10). Finalists:

- **readb** — PyPI/npm free. Neighbors: `Basis-Health/readb`, a dormant Rust key-value crate
  (10★, last push 2024-07, crates.io only); a bookshelf app dead since 2017.
- **readbl** — free everywhere incl. crates.io, but carries only "readable" and loses the
  `db`/database signal; casual search collides with "read BL novels" apps.
- **plaindex** — free everywhere, zero conflicts, but leans "index" and hides that it's a
  queryable database.
- **knowdb** — registries free, but two active claimants in exactly our space (an agent-native
  knowledge-database prototype, 26★, active; an MCP/DuckDB semantic layer already listed in MCP
  directories), and search drowns in generic "knowledge database" content.
- **okfdb** and friends — free, but OKF-literal; direction rejected by the human.

# Decision

The package is **`readb`**, read as "**readable / reads your files + db**": a database that
stays human-readable — the markdown files are the storage, and everything round-trips through
plain files. It is *not* pitched as "read-only database": the frontmatter editor already writes,
and inserts through the same interface may come later without betraying the name.

The distribution name, the import package, and the CLI command are **all `readb`**
(`pip install readb`, `import readb`, `readb query ...`). A dist/import mismatch is a permanent
papercut, and pre-publish with zero users is the cheapest moment to rename.

# Consequences

- `pyproject.toml` name + `[project.scripts]`, `src/okdb/` → `src/readb/`, tests, README,
  CLAUDE.md, and workflow/task docs all rename (this sprint, task `choose-package-name`).
- The GitHub repo / local directory rename is the human's call and out of code scope; nothing
  in the code depends on it.
- The dormant `readb` Rust crate is an accepted, low-risk neighbor; crates.io would need
  another name if a Rust port ever exists.
- Residual risk: PyPI can reject names too similar to existing projects at first upload
  (`okdb` exists); certainty lands with `distributable-package`. Staking the PyPI name early
  is that task's first step.

# Alternatives considered

`readbl`, `plaindex` (clean but weaker semantics — see Context), `knowdb` (active collisions),
`markdb` (concept already in third-party use), `readbase` (multiple small commercial products),
`fmdb`/`matterdb`/`mddb`/`okread` (taken or famous), `okfdb`/`okfsql` (OKF-literal direction
rejected).
