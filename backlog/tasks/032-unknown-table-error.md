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

Found by the v2 agent-efficiency benchmark (`031`, sprint-005). An agent guessed a table name
without running `readb schema` first and got DuckDB's error passed through unchanged:

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
