# Development

Development basics for readb — environment, repository map, commands, checks, and
conventions. The user entry point is the [README](README.md); the coding-agent entry point is
[`AGENTS.md`](AGENTS.md); contributors start at [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Getting started

Python 3.14 is pinned in `.python-version` (the package itself supports >=3.11); uv manages
the environment and honors the pin.

```sh
uv sync              # install deps + dev tools
uv run readb --help  # exercise the CLI from the working copy
```

## Repository map

- `src/readb/` — the package (src layout; see `AGENTS.md` for the architecture seams).
- `tests/` — pytest suite; the design brief's 12 acceptance criteria are pinned here.
- `backlog/` — the project backlog, an OKF bundle: active tasks in `tasks/`, closed ones in
  `archive/`, sprint records in `sprints/`; the sprint process is `backlog/workflow.md`.
- `docs/dev/` — developer documentation, an OKF bundle: the binding design brief
  (`design.md`), ADRs (`adr/`), research artifacts (`research/`).
- `.readb/` — the committed readb bundle registry for this repo (`readb init`; ADR 0004).
- `skills/readb/` — the usage skill shipped to agents; `.claude-plugin/` makes this repository
  its own plugin marketplace. The skill's SQL examples are executed by the test suite.
- `scripts/` — small release-support scripts (tested like the package).

## Stack

Python >=3.11; uv for env/deps; hatchling build backend; pytest for tests; ruff for lint and
format. Key libraries: duckdb (engine), pyyaml (frontmatter), click (CLI).

## Commands

```sh
uv run pytest        # run tests
uv run ruff check    # lint
uv run ruff format   # format
```

## Checks

These must pass before any change is presented or merged:

```sh
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

New behavior carries tests.

## Conventions

Conventional Commits (`feat`, `fix`, `docs`, `design`, `refactor`, `test`, `chore`, `perf`,
`style`). `design` marks sprint design-phase commits (task `## Design` sections, `Proposed`
ADRs). Scopes match components (e.g. `loader`, `schema`, `cli`). If a coding agent helped
write a commit, add a `Co-Authored-By` trailer for the model that helped (e.g.
`Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`); otherwise no attribution.
Never add `Claude-Session:` or other private session-link trailers — the repo and its history
are public-bound (publication-hygiene gate, `backlog/workflow.md` §5).

## Docs upkeep

Which document takes which kind of change:

- **`docs/dev/design.md`** — scope changes and load-bearing boundaries. Binding: read it
  before designing a feature.
- **`docs/dev/adr/`** — one record per decision of architectural weight, added as part of the
  change that makes the decision (schema and lifecycle: `docs/dev/index.md`).
- **`README.md`** — how someone uses readb.
- **`DEVELOPMENT.md`** — commands, map, checks, conventions.
- **`backlog/`** — sprint and task state, per `backlog/workflow.md`.

## Releasing

The release procedure lives in [`CONTRIBUTING.md`](CONTRIBUTING.md#releasing). Pushing a `v*`
tag runs [`.github/workflows/release.yml`](.github/workflows/release.yml), which checks, builds,
publishes to PyPI via Trusted Publishing, and creates the GitHub release.
