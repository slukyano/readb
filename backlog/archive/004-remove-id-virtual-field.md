---
type: Task
title: Remove the __id virtual field
description: Drop __id; __path is already unique and can serve as the primary key.
status: Done
priority: medium
tags:
- schema
- cleanup
created: 2026-06-29
blocked_by: []
timestamp: '2026-07-17T00:00:00Z'
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

## Design

Designed 2026-07-10 (revised same day: wiki-style naming). The contract change is
[ADR 0003](../../docs/dev/adr/0003-virtual-columns.md) (which also adds `__raw` from
[read-full-concept](012-read-full-concept.md)).

**`__id` is dropped and replaced by `__name`** — the simple file name (no directories, no
`.md`), wiki-style: *assumed* unique, not guaranteed. `__path` (full relative path with `.md`)
is the guaranteed-unambiguous primary key. "ID" terminology is retired throughout.

Changes:

- `schema.py`: `VIRTUAL_ID` → `VIRTUAL_NAME` (`__name`); `loader.py:243`: row value becomes
  the basename; `parser.Concept.concept_id` → `Concept.name` (basename semantics).
- **CLI resolver rewrite** (`_concept_path`, shared by `show`/`get`/`set`/`unset`): argument
  ending in `.md` = exact path (escape-guarded, as today); otherwise = name (no `/` allowed),
  resolved via `**/<name>.md` search — one match resolves, zero errors, **two+ raise the clash
  exception listing at most 5 clashing paths** and prompting to re-run with the full path.
- Frontmatter references (`blocked_by`, sprint `tasks:`) hold names; the eligibility join
  becomes `WHERE d.__name = b.dep`.
- Verified: `__TAGS(concept_path, tag)` joins on the path — unaffected; the bundle walk is
  already recursive (`rglob`), so clashes are real, not theoretical.
- **Docs ripple (breaking):** `tasks/workflow.md` and `CLAUDE.md` example queries move from
  `__id` to `__name` (unchanged shape for flat bundles); prose "Concept ID" → "concept name".
- Tests: `__id` absent, `__name` present (basename for a nested fixture file); clash exception
  message (5-path cap) for a name duplicated across subdirectories; exact-path addressing
  still works during a clash.
