---
type: Task
title: Research querying the body as structured data
description: Investigate exposing the body as JSON/YAML/DOM (headings as structure).
status: Draft
priority: low
tags:
- research
- body
created: 2026-06-29
blocked_by: []
timestamp: '2026-07-09T00:00:00Z'
---

Right now `__body` is plain text. Investigate exposing it as a queryable structure — e.g. a tree
addressable by heading (`# Schema`, `# Examples`, `# Citations`), or extracting fenced code
blocks, tables, and links.

## Context

- The design brief left this as a future, type-specific feature with a hook.
- OKF gives conventional meaning to some headings (`# Schema`, `# Examples`, `# Citations`),
  which makes a heading-addressed DOM attractive.

## Notes (to refine)

- Survey prior "structured markdown" / "markdown as data" query attempts (Dataview, MDAST/remark,
  CommonMark AST tooling, "queryable markdown" experiments).
- Decide on a representation (JSON DOM vs. flattened sections) and how it surfaces in SQL
  (a view, a column, or table-valued function over `__body`).
