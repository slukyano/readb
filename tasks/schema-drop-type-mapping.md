---
type: Task
title: Drop the type mapping from `okdb schema` output
description: Remove the separate type-mapping section; the original type is already shown per table.
status: Draft
priority: low
tags:
- cli
- schema
created: 2026-06-29
blocked_by: []
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
