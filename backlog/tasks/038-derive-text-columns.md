---
type: Task
title: Stop storing every file's text twice — derive the text columns instead
description: __raw and __body hold the file's text and the file's text-minus-frontmatter for every concept, in __DOCUMENTS and again in each type table. Deriving them would cut the biggest thing readb keeps.
status: Draft
priority: medium
tags:
- loader
- performance
- query
created: 2026-08-23
---

Raised while designing `034-persistent-index-cache`: if the cache is going to hold a database on
disk, what is *in* that database starts to matter, and most of it is copies of the source files.

## What is stored today

Measured on a 6000-concept bundle (~12 MB of markdown):

| Column | Bytes held |
| --- | --- |
| `__DOCUMENTS.__raw` — the file's full text | 11.9 MB |
| `__DOCUMENTS.__body` — the same text minus frontmatter | 10.7 MB |
| `service.__raw` + `service.__body` — again, per type table | 7.5 MB for one type |

So the whole corpus is held at least twice, and every concept's text is held once in
`__DOCUMENTS` and once more in its type table. The materialized cache file for that bundle is
20.5 MB; the in-memory load pays the same duplication in RAM on every invocation, cache or no cache.

## The idea, and what a feasibility check found

**`__body` can be derived from `__raw` in native SQL, with no file access and no Python.** A
`regexp_replace` over `__raw` reproduced the parser's body for all 6000 rows to within a single
leading newline the parser strips:

```sql
regexp_replace(__raw, '^---\n.*?\n---\n', '', 'ns')
```

Closing that one-character gap and pinning the result against the parser is the work; the prize is
roughly half the stored text.

**Reading `__raw` from the file on demand is harder than it looks.** DuckDB's `read_text` is a
*table* function, not a scalar one, so a lazy `__raw` would be a view joined against
`read_text('<bundle>/**/*.md')` — and the filename predicate does **not** push down: fetching one
file's text out of a 600-file glob costs 14.4 ms against 0.14 ms for reading that file directly. A
full scan of 6000 files is 119.9 ms, so bulk access is fine and point access is not. readb cannot
fix that by rewriting the query — it never parses or plans SQL.

The scalar-UDF route (`con.create_function`) is closed for a different reason: DuckDB's Python UDFs
require numpy, and adding numpy to readb's dependencies to save disk space would be a poor trade —
the same class of mistake as `036-load-pandas-import-probe`.

## Notes (to refine)

- The cheap, certain half is **deriving `__body`**; the speculative half is **not storing `__raw`**.
  They can ship separately, and the first does not depend on the second.
- Also worth weighing: does the per-type table need `__raw`/`__body` at all, given `__DOCUMENTS`
  has them and `__path` joins the two? That is a change to a documented virtual-column contract
  (ADR 0003), so it needs its own decision — a view could preserve the surface exactly.
- Any change here alters what a `SELECT __raw` costs, which is a public-surface performance
  characteristic even when the values are identical.
- Measure the result three ways: cache file size, resident memory during a load, and load time.
