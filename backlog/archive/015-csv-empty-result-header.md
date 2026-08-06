---
type: Task
title: Decide zero-row csv/tsv output (header or nothing?)
description: readb query --format csv/tsv prints nothing (no header) for an empty result; research what similar tools do and decide whether that is a bug.
status: Done
priority: medium
tags:
- cli
- output
- research
created: 2026-07-17
timestamp: '2026-07-20T00:00:00Z'
---

`readb query --format csv|tsv` currently prints **nothing at all** — not even a header row —
when the result set is empty (see `_format_csv` in `src/readb/cli.py` and the
`## Sprint summary` in [sprint-001](../sprints/sprint-001.md)). The reason is structural: `Database.sql`
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

## Design (2026-07-20, sprint-002)

**Decision: it is a bug — emit the header row on zero-row csv/tsv output.**

Evidence (peers checked 2026-07-20; DuckDB and sqlite3 verified live, the rest from docs and
the sprint-002 survey):

- **DuckDB itself** — our engine — emits the header on zero rows from both
  `COPY (SELECT ...) TO ... (FORMAT csv, HEADER)` and `.write_csv(header=True)` (verified,
  duckdb 1.5.4: output is exactly `'a,b\n'`).
- **psql `--csv`** prints the header row regardless of row count (unless `tuples_only`).
- **pandas** `DataFrame.to_csv` on an empty frame with columns writes the header.
- **Backlog.md's machine-output contract** (sprint-002 survey): structure is preserved when
  empty — an empty collection is `[]`, never *nothing*.
- The one dissenter: **sqlite3 CLI** (`.mode csv`, `.headers on`) prints 0 bytes on zero rows
  (verified, 3.51.0) — readb's current behavior has exactly one peer, and it is not our engine.

A shell caller piping `readb query ... --format csv` downstream gets schema-carrying, valid CSV
either way; zero rows stop being a special case.

### API change (the "small API question")

`Database.sql` keeps returning `list[dict]` (unchanged, convenient). Add a sibling:

```python
def sql_table(self, query, parameters=None) -> tuple[list[str], list[tuple]]:
    """Columns and raw rows — column names survive an empty result."""
```

Implementation is a refactor of `sql()`'s existing body (it already extracts
`cursor.description` at `database.py:48` and throws the names away into dicts); `sql()` becomes
a thin wrapper over `sql_table()`. `description is None` (no result set) → `([], [])`.

### CLI

- `_format_csv` takes `(columns, rows)` and always writes the header when there are columns;
  the csv/tsv path calls `sql_table()`. Zero rows → exactly the header line.
- `--format json` (`[]`), `table` (`"(0 rows)"`), and `raw` (empty — values-only format by
  design) are **unchanged**.
- The `_format_csv` docstring's "zero-row prints nothing" rationale (cli.py:255) is replaced by
  the new contract; same for the note in `tests/test_cli.py:103`.

### Tests

Zero-row csv prints exactly `header + "\n"`; tsv same; non-empty output unchanged; json/raw/
table zero-row behavior pinned unchanged; `sql_table` returns column names on an empty result
and `([], [])` for statements with no result set.

No ADR: reverses a sprint-001 *documented limitation*, not an accepted decision.
