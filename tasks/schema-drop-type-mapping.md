---
type: Task
title: Drop the type mapping from `okdb schema` output
description: Remove the separate type-mapping section; the original type is already shown per table.
status: Designed
priority: low
tags:
- cli
- schema
created: 2026-06-29
blocked_by: []
timestamp: '2026-07-10T00:00:00Z'
---

`okdb schema` prints a standalone "Type mapping (table name <- original type)" section. Each
table already shows its original type inline (e.g. `widget   (type: 'Widget')`), so the separate
section is redundant.

## Context

- The mapping is still available programmatically via `BundleSchema.type_mapping` and is
  recoverable from `type` values in the data.

## Notes (to refine)

- Remove the section from the CLI output only; keep `type_mapping` on the schema object (or
  decide whether to keep it at all).
- Update any tests that assert on the printed mapping section.

## Design

Designed 2026-07-10.

CLI output only: delete the "Type mapping (table name <- original type)" block from
`_format_schema` (`cli.py:194-203`); the per-table `(type: 'Widget')` suffix already carries
the information. `BundleSchema.type_mapping` **stays** — it is public API surface, costs
nothing, and programmatic consumers (and a future `index.md` generator) want it. Update the
tests that assert on the printed section.
