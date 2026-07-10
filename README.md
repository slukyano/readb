# readb

A transparent, read-only SQL query layer over an **Open Knowledge Format (OKF)** bundle — a
directory of markdown files with YAML frontmatter — so an agent or a human can run real SQL
against the wiki with no explicit database-creation step.

readb loads a bundle into an embedded [DuckDB](https://duckdb.org/) engine and lets DuckDB
execute the SQL. There is no custom SQL parser or query planner, and the source files are never
modified.

> Status: MVP implemented. Bundle loading, type inference, the library API, and the CLI all
> work; the 12 acceptance criteria in [`docs/design-brief.md`](docs/design-brief.md) are covered
> by tests. Not yet built (left as clean seams): persistent on-disk index, git-aware incremental
> rebuild, and write-back — all explicit non-goals for this MVP.

## Install

```sh
uv sync
```

## Usage

Library:

```python
import readb

db = readb.open("./path/to/bundle")          # builds an in-memory DuckDB; no files written
rows = db.sql("SELECT * FROM __DOCUMENTS WHERE type = 'Metric'")
```

CLI:

```sh
readb query "SELECT * FROM __DOCUMENTS" --bundle ./path       # results as a table
readb query "SELECT * FROM __DOCUMENTS" --bundle ./path --json
readb schema --bundle ./path                                  # detected types, tables, columns
```

## Tables and views

| Name | Rows |
| --- | --- |
| `__DOCUMENTS` | one per concept (the six reserved OKF fields + the virtual fields below) |
| *per-type tables* | one per detected `type`; columns are reserved fields + the union of producer keys across docs of that type |
| `__INDEXES` | one per reserved `index.md` file; columns are the union of their frontmatter fields |
| `__LOG` | one per reserved `log.md` file (created only if any exist) |
| `__UNKNOWNTYPE` | one per non-conformant concept (no / non-string / empty-normalized `type`) |
| `__TAGS` | normalized `(concept_path, tag)` view for join-style tag filtering |

Every table also carries three virtual columns: `__path` (bundle-relative path, with `.md`),
`__id` (the Concept ID, i.e. `__path` minus `.md`), and `__body` (the markdown body).

## Type inference

Each column's type is inferred once at load time as the narrowest DuckDB type that losslessly
holds every observed value (`int`+`float` → `DOUBLE`; a scalar alongside a list → a `LIST`;
maps with a consistent key set → a `STRUCT`). Anything that doesn't reduce to a single engine
type is stored as a `JSON` column — nothing is dropped, and producer intent is never guessed
(strings are never split or parsed). The reserved `tags` field is always a `LIST`. Run
`readb schema` to see the inferred type of every column.

## Development

```sh
uv sync              # install deps + dev tools
uv run pytest        # run tests
uv run ruff check    # lint
uv run ruff format   # format
```

## License

[Apache 2.0](LICENSE) © 2026 Stanislav Lukyanov
