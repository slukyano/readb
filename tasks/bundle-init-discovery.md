---
type: Task
title: Explicit readb init + upward bundle discovery
description: An init command marks a directory as a bundle; commands without --bundle walk up to the marker (git-style). The marker doubles as the persistent-index home.
status: Draft
priority: medium
tags:
- cli
- dx
- index
created: 2026-07-11
timestamp: '2026-07-11T00:00:00Z'
---

Replace the reverted cwd-defaulting of `--bundle` ([default-bundle-cwd](default-bundle-cwd.md),
Dropped) with the git model: a directory is a bundle because the user said so once.

## Context

- `readb init` is an explicit, sanctioned write (the `set`/`unset` precedent: its own command,
  never a side effect of load/query). It drops a marker in the bundle root — e.g. a `.readb/`
  directory.
- Commands without `--bundle` walk **up** from the cwd to the nearest marker; no marker →
  a clear error suggesting `readb init` or `--bundle`. Works from subdirectories, which the
  plain cwd default never did; never silently treats a repo root or `$HOME` as a bundle.
- Explicit `--bundle <dir>` keeps working on any directory, uninitialized or not — naming the
  path is consent (must still be able to query a freshly cloned OKF bundle untouched).
- The marker directory is exactly where the future **persistent index/cache** lives
  (`load_bundle` is the seam to wrap, per the design brief) — the marker is the cache's home
  arriving early, not ceremony.

## Notes (to refine)

- Marker format and contents (empty dir? a small versioned config file?); keep it `.md`-free so
  the loader never sees it.
- Discovery stop conditions (filesystem root; home dir?); behavior when nested markers exist.
- Whether `init` gets any options (e.g. future: index settings) — default to none.
- ADR: this changes the CLI contract and creates a new sanctioned write; supersedes/extends
  the relevant part of the dropped task's design.
