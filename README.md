# okdb

A transparent, read-only SQL query layer over an **Open Knowledge Format (OKF)** bundle — a
directory of markdown files with YAML frontmatter — so an agent or a human can run real SQL
against the wiki with no explicit database-creation step.

okdb loads a bundle into an embedded [DuckDB](https://duckdb.org/) engine and lets DuckDB
execute the SQL. There is no custom SQL parser or query planner, and the source files are never
modified.

> Status: early scaffold. The module layout and public API are in place; the loader, type
> inference, and CLI commands are stubbed. See [`docs/design-brief.md`](docs/design-brief.md)
> for the full design and acceptance criteria.

## Install

```sh
uv sync
```

## Usage

Library:

```python
import okdb

db = okdb.open("./path/to/bundle")          # builds an in-memory DuckDB; no files written
rows = db.sql("SELECT * FROM __DOCUMENTS WHERE type = 'Metric'")
```

CLI:

```sh
okdb query "SELECT * FROM __DOCUMENTS" --bundle ./path       # results as a table
okdb query "SELECT * FROM __DOCUMENTS" --bundle ./path --json
okdb schema --bundle ./path                                  # detected types, tables, columns
```

## Tables and views

| Name | Rows |
| --- | --- |
| `__DOCUMENTS` | one per concept (the six reserved OKF fields + `__path`, `__body`) |
| *per-type tables* | one per detected `type`; columns are the union of keys across docs of that type |
| `__INDEXES` | one per reserved `index.md` file |
| `__UNKNOWNTYPE` | one per non-conformant concept (no/non-string/empty-normalized `type`) |
| `__TAGS` | normalized `(concept_path, tag)` view for join-style tag filtering |

## Development

```sh
uv sync              # install deps + dev tools
uv run pytest        # run tests
uv run ruff check    # lint
uv run ruff format   # format
```

## License

[MIT](LICENSE) © Stanislav Lukyanov
