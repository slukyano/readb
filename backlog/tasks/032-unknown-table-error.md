---
type: Task
title: An unknown table should name the bundle's tables, not DuckDB's internals
description: readb passes DuckDB's catalog error through verbatim, so a mistyped table is answered with a suggestion like `duckdb_indexes` and no mention of `readb schema`.
status: Draft
priority: medium
tags:
- cli
- errors
- agents
created: 2026-08-22
---

Found by the v2 agent-efficiency benchmark (`031-benchmark-v2`, sprint-005). An agent guessed a
table name without running `readb schema` first and got DuckDB's error passed through unchanged:

```
$ readb query "select status, count(*) from concepts where type='Service' group by status" --bundle corpus
Error: Catalog Error: Table with name concepts does not exist!
Did you mean "duckdb_indexes"?
```

Two things are wrong with that reply. The suggestion points at a **DuckDB internal table**, which
exists in no bundle and answers no question. And nothing in the message names the bundle's own
tables, or `readb schema`, which is the one command that would resolve the mistake.

The cost is measurable rather than theoretical: v1 established that an agent's cost tracks turns
(`≈ $0.019/turn`), and every such miss spends one. Across the v2 matrix, readb-using arms recorded
54 failed readb invocations, a share of them this shape.

## Notes (to refine)

- The narrow fix is to catch DuckDB's `CatalogException` in the query path and re-raise with the
  bundle's own table list — the loader already knows it, since it created them.
- Worth deciding whether the suggestion should be nearest-match over the real tables, or simply
  the full list. The list is short for any plausible bundle, and a wrong suggestion is what makes
  the current message actively misleading.
- The same treatment may be worth extending to an unknown *column*, where DuckDB's candidate
  bindings are at least drawn from the right table.

## Design

The rewrite happens where the bundle's tables are known — in `Database.sql`/`sql_table`, not in
the CLI — so the Python API and the CLI get the same message. `Database` already holds the
`BundleSchema` the loader produced, which is the list of tables that actually exist.

### Behaviour

A `duckdb.CatalogException` raised by `execute` is caught and re-raised as a new
`readb.UnknownTableError` (a subclass of `duckdb.CatalogException`, so any caller catching the
DuckDB exception today keeps working) carrying a message built from the schema:

```
$ readb query "select status, count(*) from concepts where type='Service' group by status" --bundle corpus
Error: no table named 'concepts' in this bundle.
Tables: decision, incident, runbook, service, __DOCUMENTS, __INDEXES, __UNKNOWNTYPE, __TAGS.
Run 'readb schema --bundle corpus' for their columns.
```

Three decisions inside that message:

- **The bundle's own tables are listed; no nearest-match guess is made.** A wrong suggestion is
  precisely what makes DuckDB's current reply misleading — it points at `duckdb_indexes`, which
  exists in no bundle and answers no question. The list is short by construction (one table per
  distinct `type:`, plus the system tables), and it is the whole answer rather than a hint.
- **Concept tables come first, system tables after**, both alphabetically within their group: the
  user's mistyped name is nearly always a concept type.
- **Over 25 tables**, the first 25 are listed followed by `… and N more`, and the pointer to
  `readb schema` carries the rest. The message must stay readable in a terminal.

The `--bundle` value is echoed into the `readb schema` hint exactly as the user gave it, so the
suggested command is copy-pasteable. Where the bundle was resolved through the registry rather
than a flag, the hint omits `--bundle` for the same reason.

**Unknown column** gets a lighter touch: DuckDB's candidate bindings there are drawn from the right
table and are genuinely useful, so its message is kept verbatim and one line is appended —
`Run 'readb schema ...' for this bundle's columns.` The binder error is matched on its
`Binder Error: Referenced column ... not found` shape; anything unrecognized passes through
untouched.

### Public-surface delta

| Surface | Change |
| --- | --- |
| `readb query` / `readb schema` stderr | New message text for an unknown table; one appended line for an unknown column. Every other DuckDB error passes through unchanged. |
| Exit codes | Unchanged (1 for a query error). |
| `readb.UnknownTableError` | New exported exception, subclass of `duckdb.CatalogException`. |
| `Database.sql`, `Database.sql_table` | Same signatures; raise the new subclass instead of the bare DuckDB exception for this one case. |

### Tests

- A mistyped table name over a fixture bundle: the message names every table in the bundle, names
  no table that is not in it, and mentions `readb schema`. The string `duckdb_indexes` must not
  appear.
- The same through the CLI, asserting exit code 1 and stderr, and through `readb.open(...).sql(...)`.
- A bundle with more than 25 types truncates and says how many were elided.
- An unknown column keeps DuckDB's candidate bindings and gains the pointer line.
- A syntax error is passed through verbatim — the catch is narrow, and this test pins that.
- `except duckdb.CatalogException` still catches the new exception (the subclass promise).
