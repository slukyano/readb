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
timestamp: '2026-07-10T00:00:00Z'
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

Designed 2026-07-10. The contract change is [ADR 0003](../docs/adr/0003-virtual-columns.md)
(also adds `__raw` from [read-full-concept](read-full-concept.md)).

**Drop `__id` entirely** — no macro, no generated column, no derivation. `__path` (with `.md`)
is the primary key and *is* the ID; joins against ID-valued frontmatter references append the
suffix instead (`WHERE d.__path = b.dep || '.md'`), and the CLI resolver accepts both
spellings.

Changes:

- `schema.py`: remove `VIRTUAL_ID`; `loader.py`: remove the `concept_id` row value
  (`loader.py:243`); `parser.Concept.concept_id` stays (the CLI resolver and `fields` editor
  address by ID — only the SQL surface loses the column).
- Verified: `__TAGS(concept_path, tag)` joins on the path — unaffected.
- **Docs ripple (breaking):** every `__id` query in `tasks/workflow.md`, `CLAUDE.md`, and
  `docs/adr/index.md` example blocks rewrites to `__path` (e.g.
  `WHERE __path = 'sprint-001.md'`, `SELECT __path, status ...`). The sprint's own session-start
  query changes shape — update the workflow doc in the same commit.
- Known asymmetry (accepted in ADR 0003): CLI addresses by ID, SQL shows `__path`; the
  resolver accepts both spellings.
- Tests: `__id` absent from tables and `okdb schema`; `__path` uniqueness still asserted.
