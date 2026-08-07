---
type: Task
title: Automate releases (GitHub Actions + PyPI Trusted Publishing)
description: Replace manual uv publish with a tag-triggered workflow using OIDC trusted publishing; consider a CHANGELOG.
status: Designed
priority: low
tags:
- packaging
- release
- ci
created: 2026-07-20
timestamp: '2026-08-07T00:00:00Z'
---

Deferred from the [distributable-package](../archive/003-distributable-package.md) design (sprint-002): 0.1.0
ships via manual `uv publish` with a maintainer-held token. When releases become routine, automate:

- GitHub Actions workflow triggered on `v*` tag push: build, `twine check`, run the test suite,
  publish to PyPI via **Trusted Publishing** (OIDC — no long-lived token secrets).
- Configure the trusted publisher on the PyPI project (exists after
  [publish-readb-0-1-0](../archive/022-publish-readb-0-1-0.md)).
- Decide whether a `CHANGELOG.md` earns its keep at that point, or GitHub release notes remain
  enough.
- First CI in the repo — consider whether tests-on-push comes along for the ride or stays out.

## Status of the open points

Two of the four were settled outside a sprint, before this task was designed: `CHANGELOG.md`
exists (Keep a Changelog + SemVer) and CI exists (`.github/workflows/ci.yml`, running the
declared checks on push to `main`, on pull requests, and on dispatch). What remains is the
release workflow itself and the PyPI-side configuration.

## Design

Approved in chat 2026-08-06 (sprint-003).

### Publishing mechanism

**`pypa/gh-action-pypi-publish@release/v1`**, not `uv publish`. The deciding fact, checked
2026-08-06: `uv publish` *uploads* PEP 740 attestations but
[does not generate them](https://docs.astral.sh/uv/guides/package/) ("attestations must be
created separately before publishing"), while the PyPA action
[generates and uploads them by default](https://docs.pypi.org/attestations/producing-attestations/)
since v1.11.0, signed via Sigstore with the workflow's OIDC identity. Attestations for free is
worth the one non-uv step; `uv` still drives everything else (sync, checks, build).

### `.github/workflows/release.yml`

Triggered by `v*` tag pushes, plus `workflow_dispatch` with a target input for TestPyPI
rehearsals. Default permissions are `contents: read`; `id-token: write` is granted **only** to
the publishing job, per the action's own guidance.

1. **build** — checkout, `astral-sh/setup-uv`, then:
   - **tag/version guard**: the tag must equal `v` + `pyproject.toml`'s `version` (read with
     `tomllib`), or the run fails. `pyproject.toml` stays the single version source.
   - the full declared checks (`ruff format --check`, `ruff check`, `pytest`) — re-run even
     though CI covered `main`, because a tag can point at any commit.
   - `uv build`, `uvx twine check dist/*`, upload `dist/` as an artifact.
2. **publish** — `needs: build`, `environment: pypi` (or `testpypi` on dispatch),
   `permissions: id-token: write`; download the artifact and hand it to the PyPA action. No
   secrets anywhere in the repository.
3. **github-release** — `needs: publish`, `permissions: contents: write`; extract the
   `## [X.Y.Z]` section from `CHANGELOG.md` and create the GitHub release with it as the body
   (`gh release create`, using the runner's `GITHUB_TOKEN` — no third-party action). A missing
   changelog section fails the job rather than publishing an empty release.

### Maintainer hand-off

Configuring the trusted publisher is a PyPI-side action the agent cannot perform: owner
`slukyano`, repository `readb`, workflow `release.yml`, environment `pypi` — and the same on
TestPyPI (environment `testpypi`) for the rehearsal. Agreed at scoping; the workflow lands
first and is verified against TestPyPI once the setting exists.

### Documentation ripple

`CONTRIBUTING.md` § Releasing becomes the automated procedure — bump the version, close the
changelog section, commit, tag, push; the workflow does build/publish/release — keeping the
manual route only as the fallback. The `023-release-automation` pointer in that section goes
away.
