# okdb

Read-only SQL query layer over an OKF (Open Knowledge Format) bundle — a directory of markdown
files with YAML frontmatter. The bundle is loaded into an in-memory DuckDB; DuckDB executes the
SQL. Full design and acceptance criteria: `docs/design-brief.md`. OKF spec:
https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

## Commands

```sh
uv sync              # install deps + dev tools
uv run pytest        # run tests
uv run ruff check    # lint
uv run ruff format   # format
uv run okdb --help   # exercise the CLI
```

## Repo structure

- `src/okdb/__init__.py` — public API: `okdb.open(path)` -> `Database`.
- `src/okdb/database.py` — `Database`: thin read-only wrapper over a DuckDB connection; `.sql()`.
- `src/okdb/loader.py` — THE load seam (`load_bundle`): bundle dir -> populated DuckDB + schema.
  Wrap this, not callers, to add the future persistent-index cache.
- `src/okdb/parser.py` — parse one file -> `Concept(path, frontmatter, body)`. Permissive.
- `src/okdb/schema.py` — type-name normalization + the column-type unification lattice.
- `src/okdb/cli.py` — click CLI: `okdb query` and `okdb schema`.

## Hard constraints

- NEVER write a SQL parser or query planner. DuckDB executes all SQL.
- READ-ONLY: never create or modify any file inside a bundle, during any operation.
- Be permissive when loading: tolerate unknown keys, broken cross-links, missing `index.md`,
  malformed files. A bad file is logged and skipped — never crashes the load.
- Union-of-keys per type must be lossless (missing key -> NULL, never an error).
- JSON is the top of the type lattice and the universal fallback; nothing is dropped. Never
  guess producer intent (don't split comma-strings into lists, don't parse strings to numbers).
- `index.md` / `log.md` are reserved filenames, NOT concept docs.

## Implementation order

Two-pass load: pass 1 parses every concept and infers unified column types via the lattice;
pass 2 coerces values and inserts into DuckDB. The brief's acceptance criteria (1-12) should be
written as tests.

## Task backlog (dogfooding)

The project backlog lives in `tasks/`, which is itself an OKF bundle (one `Task` concept per
file). Query it with okdb: `okdb query "SELECT status, title FROM task" --bundle ./tasks`.

Tasks move along a single linear chain — `Draft → Refining → Refined → Implementing → Done` —
where `Refining`/`Implementing` are in-progress locks and human approval is the PR merge (no
separate `approved` status). The agent loop `scripts/agent-loop.sh` advances one ready task by
one step per run: it claims the task on `main` (the lock), branches, invokes an agent, runs the
validation gate, and opens a PR for human review + subagent review. The full lifecycle,
frontmatter schema, claim/lease lock, and gates are documented in `tasks/workflow.md`.

## Stack

- Python >=3.11 (developed on 3.14, pinned in `.python-version`).
- uv for env/deps; hatchling build backend; src layout.
- pytest for tests, ruff for lint/format.
- Key libraries: duckdb (engine), pyyaml (frontmatter), click (CLI).

## Commit convention

Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`).
Scopes match components (e.g. `loader`, `schema`, `cli`). If Claude helped write code in a
commit, add `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`; otherwise no attribution.
