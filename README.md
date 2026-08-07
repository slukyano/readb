# readb

[![CI](https://github.com/slukyano/readb/actions/workflows/ci.yml/badge.svg)](https://github.com/slukyano/readb/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/readb)](https://pypi.org/project/readb/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

A transparent, read-only SQL query layer over an **Open Knowledge Format (OKF)** bundle — a
directory of markdown files with YAML frontmatter — so an agent or a human can run real SQL
against the wiki with no explicit database-creation step.

readb loads a bundle into an embedded [DuckDB](https://duckdb.org/) engine and lets DuckDB
execute the SQL. There is no custom SQL parser or query planner, and the source files are never
modified.

- **Zero setup** — point readb at a bundle directory and query; no database to create,
  migrate, or clean up.
- **Real SQL** — DuckDB executes every query: joins, aggregates, window functions, the works.
- **Read-only by construction** — loading and querying never write a file; the one write path
  is the explicit, surgical frontmatter editor (`readb get`/`set`/`unset`).
- **Lossless and permissive** — every frontmatter key of every concept stays queryable
  (union-of-keys, `JSON` fallback); malformed files are skipped, never fatal.
- **Library and CLI** — `readb.open()` in Python, or `readb query`/`schema`/`show` in the
  shell.

> Status: MVP implemented. Bundle loading, type inference, the library API, and the CLI all
> work; the 12 acceptance criteria in [`docs/dev/design.md`](docs/dev/design.md) are covered
> by tests. Not yet built (left as clean seams): persistent on-disk index, git-aware incremental
> rebuild, and write-back — all explicit non-goals for this MVP.

## Install

From [PyPI](https://pypi.org/project/readb/) (Python >= 3.11):

```sh
uv tool install readb    # the CLI as a standalone tool
# or
pip install readb        # the library + CLI into an environment
```

For development from a clone, see [Development](#development).

## Usage

The examples below query `./library`, a bundle of book notes: markdown files whose frontmatter
carries `type: Book` or `type: Author`.

Python API:

```python
import readb

db = readb.open("./library")                 # builds an in-memory DuckDB; no files written
rows = db.sql("SELECT title, year FROM book WHERE year < 1980")
```

CLI:

```sh
readb query "SELECT * FROM __DOCUMENTS" --bundle ./library     # results as a table
readb query "SELECT * FROM book" --bundle ./library --format json   # or csv | tsv | raw
readb schema --bundle ./library                                # detected types, tables, columns
readb show --bundle ./library dune                             # a concept's body, by name
```

Concepts are addressed wiki-style: a simple file name (`some-concept`) when it is unique in
the bundle, or the full path (`sub/some-concept.md`) — always unambiguous — when it is not.
An ambiguous bare name is always a hard error listing the clashing paths — never a silent
first match. Names are filenames: `__name` is immutable and filename-derived, and a producer
`name:` frontmatter key is just an ordinary data column — it affects neither `__name` nor
addressing.

## readb init: skip --bundle

`--bundle` may be omitted once you register your bundles (the git model — a directory is a
bundle because you said so once):

```sh
readb init library notes    # in the project root: writes .readb/config.toml (commit it)
cd library && readb query "SELECT count(*) FROM book"   # bundle resolved by walking up
```

Commands without `--bundle` walk up from the cwd to the nearest `.readb/` registry, then pick
the declared bundle containing the cwd (innermost wins), else the sole declared bundle, else
the config's optional `default_bundle`. Genuine ambiguity — e.g. the root of a repo declaring
several bundles, no default — is a hard error listing the choices, never a guess; a directory
never silently becomes a bundle. Explicit `--bundle <dir>` always works on any directory,
initialized or not, and never consults the registry. Re-running `init` merges new dirs and
never removes. Besides the config, `.readb/` is reserved for readb's future persistent index —
it is never read as bundle content.
readb only addresses files inside the bundle root: a `../` path or a symlink that resolves
outside the bundle is not supported and is refused with an explicit error (by name and by
path alike). `--format raw` prints values verbatim, so
`readb query "SELECT __raw FROM book WHERE __name = 'dune'" --format raw` is exactly `cat`.

## Tables and views

| Name | Rows |
| --- | --- |
| `__DOCUMENTS` | one per concept (the six reserved OKF fields + the virtual fields below) |
| *per-type tables* | one per detected `type`; columns are reserved fields + the union of producer keys across docs of that type |
| `__INDEXES` | one per reserved `index.md` file; columns are the union of their frontmatter fields |
| `__LOG` | one per reserved `log.md` file (created only if any exist) |
| `__UNKNOWNTYPE` | one per non-conformant concept (no / non-string / empty-normalized `type`) |
| `__TAGS` | normalized `(concept_path, tag)` view for join-style tag filtering |

Every table also carries four virtual columns: `__path` (bundle-relative path, with `.md` —
the guaranteed-unique key), `__name` (the simple file name, no directories or `.md`; wiki-style,
assumed unique but not guaranteed), `__body` (the markdown body, frontmatter stripped), and
`__raw` (the byte-exact file text as on disk, frontmatter included).

## Type inference

Each column's type is inferred once at load time as the narrowest DuckDB type that losslessly
holds every observed value (`int`+`float` → `DOUBLE`; a scalar alongside a list → a `LIST`;
maps with a consistent key set → a `STRUCT`). Anything that doesn't reduce to a single engine
type is stored as a `JSON` column — nothing is dropped, and producer intent is never guessed
(strings are never split or parsed). The reserved `tags` field is always a `LIST`. Run
`readb schema` to see the inferred type of every column.

## Using readb with an agent

This repository doubles as a plugin marketplace, so an agent installs readb's usage guidance the
same way it installs anything else:

```sh
/plugin marketplace add slukyano/readb
/plugin install readb@readb
```

The skill covers the data model, the command surface, and worked SQL. Its examples are executed
by readb's own test suite, so they cannot quietly drift from the tool. For runtimes that read
skill folders directly, [`skills/readb/SKILL.md`](skills/readb/SKILL.md) is a portable folder to
symlink or copy — nothing in it is specific to one agent.

## Prior art

readb's architecture is not novel: load markdown frontmatter into a SQL engine, then query it
with SQL. What differs is that **the index is transparent and disposable** — point readb at a
directory and query it. There is no database to create, migrate, regenerate, or keep in sync;
the markdown files are the only state.

Neighbours worth knowing (checked 2026-08-07):

- **[frontmatter-mcp](https://github.com/kzmshx/frontmatter-mcp)** — queries markdown frontmatter
  with DuckDB SQL, packaged as an MCP server. The closest architectural twin (1★, last commit
  2025-12).
- **[MarkdownDB](https://github.com/flowershow/markdowndb)** — a JS/TS library that indexes
  markdown into SQLite, MySQL, or Postgres and runs SQL over that index, which you build and
  refresh as a managed artifact (499★, last commit 2026-05).
- **[Obsidian Dataview](https://github.com/blacksmithgu/obsidian-dataview)** — the widely used
  non-SQL alternative, with its own DQL query language, inside Obsidian (9.3k★).

readb differs in packaging and constraints rather than in engine: an OKF bundle in, an in-memory
DuckDB out, a load and query path that never writes, and exactly one narrow write path — the
frontmatter field editor, which is deliberately string-literal (`readb set n=42` writes the
string `42`; producer intent is never guessed).

The full survey, including the tools not listed here, is in
[`docs/dev/research/similar-tools.md`](docs/dev/research/similar-tools.md).

## Development

Contributions are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md); release history is in
[`CHANGELOG.md`](CHANGELOG.md). See [`DEVELOPMENT.md`](DEVELOPMENT.md) for the repository map,
commands, and checks. Development runs in maintainer-approved sprints; the backlog and the
developer documentation (including Architecture Decision Records) are
[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) bundles in
[`backlog/`](backlog/index.md) and [`docs/dev/`](docs/dev/index.md). Process:
[`backlog/workflow.md`](backlog/workflow.md).

## License

[Apache 2.0](LICENSE) © 2026 Stanislav Lukyanov
