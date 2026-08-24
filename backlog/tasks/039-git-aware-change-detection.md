---
type: Task
title: Detect bundle changes without stat-ing every file, for filesystems where stat is expensive
description: The cache's change detection stats every file in the bundle. That is microseconds each on a local disk and unworkable on an S3-backed or network filesystem; git with an fsmonitor daemon can make detection O(changed files).
status: Draft
priority: medium
tags:
- performance
- loader
- cache
created: 2026-08-23
---

Split out of `034-persistent-index-cache` at design time, as the deliberate second step: ship the
cache with the simple detector, then optimize the detector behind the seam it already has.

## The limitation being addressed

`034-persistent-index-cache` detects change by walking the bundle and stat-ing every file. Measured
on a local APFS disk: 1.7–2.1 µs per file, linear from 600 to 20000 files (1.0 ms, 10.7 ms,
41.6 ms), which is 0.3% of the load it replaces and strictly less work than the open-and-read every
uncached load already performs.

That argument holds only where stat is cheap. **On an S3-backed filesystem, or NTFS or SMB across a
network, a per-file stat is a round trip**, and six thousand of them is not a cost anyone will
accept on every invocation. The cache would then be slower to validate than it is to use.

## Why `git status` is not the answer by itself

Measured on a 6000-file git repository, local disk: `git status --porcelain` is 11.9 ms against the
walk's 10.7 ms. Git is not faster because git does the same thing — **its index is a stat cache, and
it stats every file too**. Swapping one walk for another buys nothing, on any filesystem.

## What would actually help

- **`core.fsmonitor`.** Git can consult a filesystem-monitor daemon (watchman, or its built-in
  monitor) and skip the working-tree scan entirely, making change detection O(changed files) rather
  than O(files). That, not `git status` itself, is the win worth having — and it is exactly the
  case a huge bundle on a slow filesystem is in.
- **`git rev-parse HEAD` plus `git diff --name-only`** for the committed part of the tree, with a
  scan needed only for what git reports as dirty. Careful: this is only sound if the dirty set is
  itself obtained without a full scan, which brings it back to fsmonitor.
- A **readb-side watcher** was considered and declined in
  [ADR 0006](../../docs/dev/adr/0006-cache-consent-and-key.md) and
  [ADR 0005](../../docs/dev/adr/0005-stay-on-python.md); a daemon readb does not own and does not
  have to ship is a different proposition from one it does.

## Notes (to refine)

- Whatever lands must be a **strategy behind the existing seam**, chosen per bundle, with the stat
  walk as the always-available fallback. The cache's correctness argument must not fork.
- The blind spots recorded in ADR 0006 have to be handled explicitly, and every one of them fails
  toward a *stale answer*: gitignored files that are nonetheless part of the bundle, untracked
  files, submodules, several repositories under one bundle, a bundle outside any repository.
- Detection strategy is a **cache-validity input**, so switching strategies must invalidate the
  cache rather than silently reinterpret it.
- Measure on a filesystem that actually has the problem — a network mount or an S3-backed FUSE
  mount — not on the local disk where the current numbers were taken. Without that measurement this
  task cannot claim to have fixed anything.
