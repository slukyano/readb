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

Releases are cut by the maintainer. Pushing the tag is the release: everything after it runs in
[`.github/workflows/release.yml`](.github/workflows/release.yml).

1. **Bump the version** in `pyproject.toml` (the single version source) and in
   `.claude-plugin/plugin.json`, which a test keeps in step with it.
2. **Close the changelog section**: rename `Unreleased` to `[X.Y.Z] - YYYY-MM-DD`, add a fresh
   empty `Unreleased`, and update the comparison links at the bottom. This section becomes the
   GitHub release notes verbatim, so an empty one fails the release.
3. **Commit** as `chore(release): vX.Y.Z`, and let CI go green on `main`.
4. **Tag and push**: `git tag vX.Y.Z && git push origin main --tags`.
5. **Watch the workflow.** It refuses a tag that disagrees with `pyproject.toml`, re-runs the
   declared checks against the tagged commit, builds, runs `twine check`, publishes to PyPI, and
   creates the GitHub release with the changelog section as its notes and the artifacts attached.
6. **Verify** — `uv tool install readb` works from a clean environment and the README badges
   resolve.

Publishing uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/): the
workflow authenticates with a short-lived OIDC token, so the repository holds no PyPI
credentials. Only the publishing job is granted `id-token: write`, and it runs in a GitHub
environment (`pypi`, or `testpypi` for rehearsals) whose name must match the trusted publisher
configured on the registry. `pypa/gh-action-pypi-publish` also signs each distribution and
uploads PEP 740 attestations by default.

To rehearse the whole path without releasing, run the workflow manually
(**Actions → Release → Run workflow**). A manual run always targets TestPyPI and never creates a
GitHub release; real PyPI is reachable only by pushing a tag, so a rehearsal cannot skip the
tag/version guard.
