---
type: Task
title: Add plain-text row output to okdb query
description: A --csv/--tsv output mode so shell callers can read rows without python-parsing --json.
status: Done
priority: low
tags:
- cli
- dx
created: 2026-07-02
timestamp: '2026-07-17T00:00:00Z'
---

`okdb query` emits a pretty table or `--json`. Shell consumers currently need a python
one-liner just to pull two fields out of the JSON. A machine-readable plain-text mode
(`--csv` or `--tsv`) would let them use `read -r`/`cut` directly.

## Context

- DuckDB can already produce CSV natively — prefer delegating to the engine over hand-rolling
  escaping.

## Notes (to refine)

- Decide the flag surface: `--csv`, `--tsv`, or `--format table|json|csv` (one enum flag may age
  better than accumulating booleans; keep `--json` as an alias either way).
- Define NULL and list/JSON-value representation in text output; document it.

## Design

Designed 2026-07-10 (maintainer decision: one `--format` enum; also serves
[read-full-concept](012-read-full-concept.md)).

`okdb query` grows `--format table|json|csv|tsv|raw` (default `table`). `--json` stays as a
compatibility alias for `--format json`; combining `--json` with a conflicting `--format` is a
usage error.

Per-format semantics:

- **`csv` / `tsv`** — header row, then data rows, quoting/escaping via Python's **stdlib
  `csv` module** (csv dialect / excel-tab). NULL → empty field; lists/dicts → their JSON text
  (same coercion as the table's `_cell`). *Decision note:* the seed suggested delegating to
  DuckDB's native CSV writer, but that means textually wrapping the user's SQL in
  `COPY (...) TO`, which is exactly the kind of SQL string manipulation we forbid; stdlib
  `csv` is not hand-rolled escaping.
- **`raw`** — every selected value printed verbatim, each followed by a newline; no quoting,
  no escaping. NULL → empty line. Intended for single-column reads
  (`SELECT __body ... --format raw`); with multiline values, row boundaries are ambiguous by
  construction — documented, not "fixed" (that is what csv is for).
- **`json`, `table`** — unchanged.

Tests: csv quoting (comma, quote, newline inside a value), tsv, raw verbatim + NULL-as-empty,
`--json` alias unchanged, conflict error.
