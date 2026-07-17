---
type: Task
title: Decide zero-row csv/tsv output (header or nothing?)
description: readb query --format csv/tsv prints nothing (no header) for an empty result; research what similar tools do and decide whether that is a bug.
status: Draft
priority: medium
tags:
- cli
- output
- research
created: 2026-07-17
timestamp: '2026-07-17T00:00:00Z'
---

`readb query --format csv|tsv` currently prints **nothing at all** — not even a header row —
when the result set is empty (see `_format_csv` in `src/readb/cli.py` and the
`## Sprint summary` in [sprint-001](sprint-001.md)). The reason is structural: `Database.sql`
returns a list of row dicts, so an empty result carries no column names to print a header from.
It was shipped as a documented limitation, but it may well be a **bug** — a shell caller
piping `readb query ... --format csv` into another tool likely expects a header line even on
zero rows.

Research what comparable tools do on an empty result, then decide readb's behavior:

- DuckDB CLI (`.mode csv`), `sqlite3 -csv`, `psql --csv` / `\copy ... to`;
- `csvkit`, `pandas.DataFrame.to_csv`, `duckdb` Python `.write_csv`;
- do they emit the header row (column names) on zero rows, or nothing?

If the consensus is "header always", the fix means carrying the column names independently of
the rows — e.g. having `Database.sql` (or a sibling) expose the result columns even when empty,
which is a small API question worth its own design note. Decide, and either fix `_format_csv`
or keep the current behavior with an explicit rationale.
