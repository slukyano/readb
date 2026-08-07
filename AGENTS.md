# readb

Read-only SQL query layer over an OKF (Open Knowledge Format) bundle — a directory of markdown
files with YAML frontmatter. The bundle is loaded into an in-memory DuckDB; DuckDB executes the
SQL. OKF spec:
https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

- **What it is, usage, install:** [`README.md`](README.md).
- **Development basics — commands, repository map, checks, conventions:**
  [`DEVELOPMENT.md`](DEVELOPMENT.md).
- **Binding spec (goals, non-goals, acceptance criteria):**
  [`docs/dev/design.md`](docs/dev/design.md).

This file holds the rules an agent must follow that are not already in those documents.

## Architecture

The load is a deliberate two-pass: pass 1 parses every concept and infers unified column types
via the lattice; pass 2 coerces values and inserts into DuckDB.

- `src/readb/__init__.py` — public API: `readb.open(path)` -> `Database`.
- `src/readb/database.py` — `Database`: thin read-only wrapper over a DuckDB connection; `.sql()`.
- `src/readb/loader.py` — THE load seam (`load_bundle`): bundle dir -> populated DuckDB + schema.
  Wrap this, not callers, to add the future persistent-index cache.
- `src/readb/parser.py` — parse one file -> `Concept(path, frontmatter, body)`. Permissive.
- `src/readb/schema.py` — type-name normalization + the column-type unification lattice.
- `src/readb/fields.py` — the ONE write path: a surgical, line-based frontmatter field editor
  (`get_field`/`set_fields`/`unset_fields`). Does NOT load the bundle or round-trip YAML — only
  the targeted key's own lines change. A key is addressed by its *span* (the `key:` line plus
  its continuation lines), so an edit can never orphan half a value into invalid YAML; `set`
  refuses a multi-line key rather than discarding it. PyYAML appears here for exactly one
  purpose: verifying that a rewrite does not break frontmatter that parsed before.
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
- readb is a general-purpose tool over any OKF bundle. Its public surfaces — README, CLI help,
  shipped skills/docs, package metadata, examples — must never present this project's own
  development process (sprints, the `backlog/` bundle, the task lifecycle) as part of readb.
  Examples there use neutral domains; process material stays in `AGENTS.md`, `backlog/`, and
  `docs/dev/`.

## Verification

The declared checks ([`DEVELOPMENT.md` § Checks](DEVELOPMENT.md#checks)) must pass before work
is presented. New behavior carries tests; the design brief's 12 acceptance criteria stay pinned
by tests.

## Development workflow (sessions + sprints, dogfooding)

**Follow this workflow only when asked to develop the project as the maintainer** — otherwise
it is context, not a requirement, and external contributions go through standard GitHub issues
and PRs.

The project backlog lives in `backlog/`, an OKF bundle: one `Task` concept per file, named
`NNN-slug.md` — active in `tasks/`, closed in `archive/` — plus one `Sprint` concept per sprint
in `sprints/`. Developer docs and ADRs live in `docs/dev/`. Frontmatter is state: edits are
surgical — change only the keys being updated, never reformat or round-trip a file. Full
workflow (sprint lifecycle, gates, chat approval protocol): `backlog/workflow.md`.

**Dogfooding rule:** always prefer readb itself for reading and querying the local OKF bundles
(`backlog/`, `docs/dev/`) — do not fall back to `cat`/grep/manual file reads for what readb
should answer (e.g. `readb query "SELECT status, title FROM task" --bundle ./backlog`;
frontmatter edits via `readb set`/`unset --bundle ./backlog <id> ...`). When readb fails or
can't express what you need: stop, immediately record a new `Draft` task for the gap, and only
then work around it. Tasks that block dogfooding readb take priority over the rest of the
backlog.

**Use the global readb on the project's own state:** manipulating this repo's bundles
(`backlog/`, `docs/dev/`) is done with the globally run readb — `uvx readb` — never
`uv run readb` from the working copy: code mid-change must not operate on the repo's own
backlog. `uv run readb` is for exercising the code under development.

At session start, check for an unfinished sprint
(`SELECT __name, status, branch FROM sprint WHERE status NOT IN ('Done','Aborted')`; a missing
`sprint` table means no sprint ever ran) and resume it from its branch; otherwise propose a
scope from the `Draft` backlog. **Stop and ask** on any decision that belongs to the
maintainer — never guess. **Only the maintainer approves ADRs.** All approvals happen in chat
and must be self-contained.
