# readb

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
uv run readb --help   # exercise the CLI
```

## Repo structure

- `src/readb/__init__.py` — public API: `readb.open(path)` -> `Database`.
- `src/readb/database.py` — `Database`: thin read-only wrapper over a DuckDB connection; `.sql()`.
- `src/readb/loader.py` — THE load seam (`load_bundle`): bundle dir -> populated DuckDB + schema.
  Wrap this, not callers, to add the future persistent-index cache.
- `src/readb/parser.py` — parse one file -> `Concept(path, frontmatter, body)`. Permissive.
- `src/readb/schema.py` — type-name normalization + the column-type unification lattice.
- `src/readb/fields.py` — the ONE write path: a surgical, line-based frontmatter field editor
  (`get_field`/`set_fields`/`unset_fields`). Stdlib only; does NOT load the bundle or round-trip
  YAML — only the targeted `key: value` lines change.
- `src/readb/cli.py` — click CLI: `readb query`/`readb schema` (read-only) and `readb get`/`set`/
  `unset` (the frontmatter editor, addressed by `--bundle <dir> <concept-id>`).
- `src/readb/registry.py` — `readb init` + upward bundle discovery (ADR 0004): `.readb/config.toml`
  at the repo root declares the bundles; commands without `--bundle` resolve through it. From the
  multi-bundle repo root, keep passing `--bundle` explicitly (no `default_bundle` is set —
  deliberate).

## Hard constraints

- NEVER write a SQL parser or query planner. DuckDB executes all SQL.
- READ-ONLY query/load path: loading a bundle and running SQL (`query`/`schema`, `readb.open`)
  never create or modify any file. The ONLY write path is the explicit frontmatter editor
  (`readb set`/`unset`, `readb.fields`) — kept out of the load/query path and its own CLI commands.
  Never write back from SQL, and never mutate a file as a side effect of loading or querying.
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

## Development workflow (sessions + sprints, dogfooding)

The project backlog lives in `tasks/`, which is itself an OKF bundle (one `Task` concept per
file, plus one `Sprint` concept per sprint). Query it with readb:
`readb query "SELECT status, title FROM task" --bundle ./tasks`. All frontmatter edits go
through readb's own field editor — `readb set`/`unset --bundle ./tasks <id> ...`.

**Dogfooding rule:** always prefer readb itself for reading and querying the local OKF bundles
(`tasks/`, `docs/adr/`, `docs/research/`) — do not fall back to `cat`/grep/manual file reads for what readb should
answer. When readb fails or can't express what you need: stop, immediately record a new `Draft`
task for the gap, and only then work around it. Tasks that block dogfooding readb take priority
over the rest of the backlog.

Development runs in **sprints** (no PRs). At session start, check for an unfinished sprint
(`SELECT __name, status, branch FROM sprint WHERE status NOT IN ('Done','Aborted')`; a missing
`sprint` table means no sprint ever ran) and resume it from its branch; otherwise propose a
scope from the `Draft` backlog. Scope approval =
committing `tasks/sprint-NNN.md` to `main` and cutting branch `sprint/NNN`. Then: an
interactive design phase (per-task `## Design` sections + `Proposed` ADRs; human approval →
design merge to `main`), an autonomous implementation phase (commit throughout; **stop and
ask** on any decision that belongs to the human — never guess), gates (`pytest` + `ruff` +
an independent subagent review of the diff + a publication-hygiene check: third-person
project voice, factual/dated/sourced claims about other projects, no personal or environment
leakage — see `tasks/workflow.md` §5), a sprint summary, and on human approval the final
merge. Task lifecycle: `Draft → Designed → Done` (+ `Dropped`). ADRs live in `docs/adr/` (an
OKF bundle); **only the human approves ADRs**. All approvals happen in chat: present a
separator, a short summary, the complete self-contained decision context (quote what matters;
don't require reading files; batch approvals list every task with at least a one-line
description), key-file references for double-clicking, then the explicit question(s). Full
workflow: `tasks/workflow.md`.

## Stack

- Python >=3.11 (developed on 3.14, pinned in `.python-version`).
- uv for env/deps; hatchling build backend; src layout.
- pytest for tests, ruff for lint/format.
- Key libraries: duckdb (engine), pyyaml (frontmatter), click (CLI).

## Commit convention

Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`).
Scopes match components (e.g. `loader`, `schema`, `cli`). If Claude helped write code in a
commit, add a `Co-Authored-By` trailer for the model that helped (e.g.
`Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`); otherwise no attribution.
