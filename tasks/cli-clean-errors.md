---
type: Task
title: Print clean CLI errors instead of Python tracebacks
description: A failed query (e.g. missing table) dumps a raw DuckDB traceback; print a one-line error and exit nonzero.
status: Draft
priority: high
tags:
- cli
- dx
- dogfooding
created: 2026-07-09
timestamp: '2026-07-09T00:00:00Z'
---

Any SQL error in `okdb query` surfaces as a full Python traceback ending in a
`_duckdb.CatalogException`/`ParserException`. The workflow's own session-start query
(`SELECT ... FROM sprint`) legitimately hits "Table with name sprint does not exist" when no
sprint has ever run — and gets a ~30-line traceback instead of a usable message.

Found while dogfooding: the traceback made the agent abandon okdb mid-session (2026-07-09).

## Context

- `src/okdb/cli.py` `query` calls `db.sql(sql)` with no exception handling; click prints the
  traceback and exits 1.
- The `get`/`set`/`unset` commands already translate their errors into `click.ClickException` —
  `query`/`schema` should behave the same.

## Notes (to refine)

- Catch DuckDB errors in `query` (and bundle-loading errors in `query`/`schema`) and re-raise
  as `click.ClickException` with the engine's message (it's good — keep it, drop the traceback).
- Keep exit code nonzero so scripts can branch on failure.
- Decide whether a missing table deserves special affordance (e.g. hint listing available
  tables) or just the clean DuckDB message.
