---
type: Task
title: Default --bundle to the current directory
description: When no --bundle is passed, default to the current directory.
status: Dropped
priority: medium
tags:
- cli
- dx
created: 2026-06-29
blocked_by: []
timestamp: '2026-07-11T00:00:00Z'
---

Make `--bundle` optional and default it to `.` so you can run okdb from inside a bundle without
repeating the path.

## Context

- Today `--bundle` is required on both `query` and `schema`.
- Common case is "I'm standing in the bundle" — `okdb query "..."` should just work.

## Notes (to refine)

- Apply to both `query` and `schema`.
- Keep the existing not-a-directory error behavior; give a clear message if `.` isn't a bundle.

## Design

Designed 2026-07-10.

`--bundle` becomes optional with `default="."` (`show_default=True`) on **all five commands** —
`query`, `schema`, `show`, and the editor commands `get`/`set`/`unset`. The seed named only
`query`/`schema`, but a flag that defaults differently per command is worse than the
consistency; flagged for the design review.

- `click.Path(exists=True, file_okay=False)` stays — a nonexistent or non-directory `--bundle`
  keeps its current clear usage error.
- **No "is this really a bundle?" heuristic.** An empty/markdown-free directory loads as zero
  tables (the permissive-load constraint says that's a valid bundle); a query against it then
  fails with the clean missing-table catalog error from
  [cli-clean-errors](011-cli-clean-errors.md), which names what exists. `okdb schema` on it shows
  no tables — that *is* the clear message.
- Tests: CliRunner with `chdir` into a fixture bundle, no `--bundle` flag, for a query and an
  editor command; default shown in `--help` output.

## Dropped (2026-07-11)

Implemented in sprint 001, then reverted at implementation review, by maintainer decision. A cwd
default turns scoping mistakes into silent wrong-scope operations: any directory (a repo root,
`$HOME`) quietly loads as a bundle, queries return wrong-scope data, and — sharpest — a
name-resolved `set` can write into a bundle the caller never named. Verified live from the
repo root: the whole repository loaded and a `task` table materialized.

The ergonomic goal returns as [bundle-init-discovery](013-bundle-init-discovery.md): explicit
`readb init` + git-style upward discovery, with the marker doubling as the future
persistent-index home.
