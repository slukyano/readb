---
type: Task
title: Create a distributable package
description: Publish okdb (under its new name) as an installable distribution.
status: Done
priority: medium
tags:
- packaging
- release
created: 2026-06-29
blocked_by:
- choose-package-name
timestamp: '2026-07-20T00:00:00Z'
---

Make okdb installable for end users (not just `uv sync` from a clone) — e.g. `pipx install`,
`uv tool install`, or `pip install` from a package index.

Blocked by [Choose a package name](/choose-package-name.md): we cannot publish until the
distribution name is settled.

## Context

- Build backend and `[project.scripts]` entry point are already in `pyproject.toml`.
- Need to decide the target index (PyPI vs. a private/test index first) and a release flow.

## Notes (to refine)

- Verify the wheel/sdist build, smoke-test an install in a clean environment.
- Consider a tagged release + changelog.

## Design (2026-07-20, sprint-002; human-approved)

Metadata in `pyproject.toml` is already complete (name/description/readme/Apache-2.0/authors/
keywords/classifiers/URLs/`[project.scripts]`). Decisions:

- **Version**: bump `0.0.1 → 0.1.0` for the first public release (stays 0.x / Alpha classifier).
- **Publishing mechanics**: **manual `uv publish` with a PyPI token** held by the human — no CI.
  GitHub Actions + Trusted Publishing recorded as draft
  [release-automation](release-automation.md) for when releases become routine.
- **Split with the publish step** (human call at approval): the actual publishing is **not part
  of this sprint** — it is the special standalone task
  [publish-readb-0-1-0](publish-readb-0-1-0.md), run after sprint-002's final merge, from
  tagged `main`. Everything upload-shaped (TestPyPI rehearsal included — it needs external
  accounts/tokens) lives there.

**In-sprint scope (this task):**

1. Bump version to `0.1.0`.
2. `uv build` → wheel + sdist; `twine check` both (via `uvx`, ephemeral, no global install).
3. Install the built **wheel into a clean scratch venv** and smoke-test: `readb --help`,
   `readb query` + `schema` against a scratch bundle, `readb set`/`get` round-trip.
4. Repeat the smoke on **Python 3.11** (our floor; we develop on 3.14) via a uv-managed 3.11.
5. No uploads, no tags, no CHANGELOG file (GitHub release notes at publish time suffice).
