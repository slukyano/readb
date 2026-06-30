---
type: Task
title: Default --bundle to the current directory
description: When no --bundle is passed, default to the current directory.
status: Draft
priority: medium
tags:
- cli
- dx
created: 2026-06-29
blocked_by: []
---

Make `--bundle` optional and default it to `.` so you can run okdb from inside a bundle without
repeating the path.

## Context

- Today `--bundle` is required on both `query` and `schema`.
- Common case is "I'm standing in the bundle" — `okdb query "..."` should just work.

## Notes (to refine)

- Apply to both `query` and `schema`.
- Keep the existing not-a-directory error behavior; give a clear message if `.` isn't a bundle.
