---
type: Task
title: Create a distributable package
description: Publish okdb (under its new name) as an installable distribution.
status: Draft
priority: medium
tags:
- packaging
- release
created: 2026-06-29
blocked_by:
- choose-package-name
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
