# Contributing to readb

Bug reports, fixes, and focused improvements are welcome — GitHub
[issues](https://github.com/slukyano/readb/issues) and pull requests are the way in.

## Getting started

Everything needed to work in the repository — environment setup, the repository map, commands,
and conventions — is in [`DEVELOPMENT.md`](DEVELOPMENT.md).

## Before submitting

The [declared checks](DEVELOPMENT.md#checks) are the project's bar; CI runs exactly them.
New behavior carries tests.

## Commits

Follow the commit convention in [`DEVELOPMENT.md` § Conventions](DEVELOPMENT.md#conventions).

## Changelog

User-visible changes get an entry under `Unreleased` in [`CHANGELOG.md`](CHANGELOG.md) as part
of the change; internal work (refactors, tests, CI, backlog bookkeeping) does not. Write
entries for someone who uses readb and has not read the code.

## Documentation

Which document takes which kind of change is mapped in
[`DEVELOPMENT.md` § Docs upkeep](DEVELOPMENT.md#docs-upkeep).

## Pull requests

Fork, branch, and open a PR against `main`. Keep each PR focused on one change.

## How this project is developed

The maintainer develops readb in agent-driven, maintainer-approved sprints; the backlog
(`backlog/`) and the developer documentation (`docs/dev/`) are OKF bundles, and the process is
described in [`backlog/workflow.md`](backlog/workflow.md). **That workflow is the maintainer's
process, not a contribution requirement**: contributors do not follow it or edit the backlog —
the contributor path is standard issues and pull requests, as above.

## Releasing

Releases are cut by the maintainer. The procedure (manual until
automation lands — backlog task `023-release-automation`):

1. **Checks are green** on the commit being released — the declared checks and CI on `main`.
2. **Bump the version** in `pyproject.toml` (the single version source).
3. **Close the changelog section**: rename `Unreleased` to `[X.Y.Z] - YYYY-MM-DD`, add a fresh
   empty `Unreleased`, and update the comparison links at the bottom.
4. **Commit** as `chore(release): vX.Y.Z`.
5. **Tag and push**: `git tag vX.Y.Z && git push origin main --tags`.
6. **Build and publish**: `uv build`, then publish to PyPI (`uv publish`; rehearse against
   TestPyPI when in doubt), and create the GitHub release with the changelog section as notes.
7. **Verify** — the release exists with the expected artifacts and notes, `uv tool install
   readb` works from a clean environment, and the README badges resolve.
