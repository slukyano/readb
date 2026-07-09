---
type: Task
title: Remove the __id virtual field
description: Drop __id; __path is already unique and can serve as the primary key.
status: Draft
priority: medium
tags:
- schema
- cleanup
created: 2026-06-29
blocked_by: []
timestamp: '2026-07-09T00:00:00Z'
---

We currently expose both `__path` (with `.md`) and `__id` (path minus `.md`) on every table.
`__path` is already unique per concept, so it can be the primary key on its own and `__id` is
redundant.

## Context

- The design brief said "expose both if cheap" — but in practice `__id` is trivially derivable
  from `__path` and adds a column to every table and to `okdb schema` output.

## Notes (to refine)

- Decide: drop `__id` entirely, or keep it derivable on demand (e.g. a function/expression).
- Update the lattice/loader, the `okdb schema` output, tests, and docs accordingly.
- Confirm nothing in `__TAGS`/joins depends on `__id`.
