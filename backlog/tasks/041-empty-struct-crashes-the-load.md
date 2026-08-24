---
type: Task
title: Four frontmatter shapes crash the whole load instead of skipping one file
description: An empty mapping value anywhere in a bundle makes every query against it fail with a DuckDB parser error, which breaks the permissive-load promise outright.
status: Draft
priority: high
tags:
- loader
- parser
- bug
created: 2026-08-23
---

Found by the adversarial review of `034-persistent-index-cache` in sprint-006, while fuzzing the
cache. **Not introduced by that sprint** — every case below reproduces identically on the
pre-sprint `main`, with and without the cache.

readb's load is supposed to be permissive: "a bad file is logged and skipped, never crashes the
load". These four shapes break that promise at the DDL step, after parsing succeeded, so the
failure is not a skipped file but a dead bundle — *every* query against it raises.

| Frontmatter | Failure |
| --- | --- |
| `flag: {}` (also `[{}]`, `{a: {}}`, `tags: {}`, and the same in `index.md`) | `ParserException: syntax error at or near ")"` — `render_ddl` emits `STRUCT()` with no fields |
| `flag: {1: a, "1": b}` | `BinderException: Duplicate STRUCT type argument name "1"` — distinct YAML keys collide once stringified |
| `flag: {"": 1}` | `ParserException: zero-length delimited identifier` |
| `flag: 99999999999999999999999999` | `ConversionException: INT128 out of range` — `type_of_value` calls it BIGINT |

## Notes (to refine)

- Each is a **type-inference** decision, not a parser bug: what type is an empty mapping, a
  mapping whose keys are not distinct as identifiers, or an integer outside INT128? JSON is the
  lattice's declared universal fallback and the obvious answer for all four, but that is a
  deliberate call about `type_of_value`/`render_ddl` rather than a patch.
- The deeper defect is that **no DDL failure is contained**: a single unrenderable column takes
  the whole bundle down. Whatever the type answers are, `_build_table` should fail one table (or
  one column) rather than the load, so the promise holds for shapes nobody has thought of yet.
- The acceptance test is a bundle containing every shape above plus healthy documents: the
  healthy ones must be queryable and the bad ones logged.
- Repro scripts from the review are worth re-deriving as fixtures; each is three lines.

## Design

Two changes, and the second is the one that matters. The first makes the four known shapes load;
the second makes an unknown fifth shape cost one column instead of the whole bundle.

### 1. The lattice becomes total

Each failing shape is a value `type_of_value` classifies as something DuckDB then cannot express.
JSON is the lattice's declared universal fallback and the answer in every case:

| Value | Today | After |
| --- | --- | --- |
| `{}` — a mapping with no entries | `STRUCT()`, which is not valid DDL | `JSON` |
| A mapping whose stringified keys are not distinct (`{1: a, "1": b}`) | `STRUCT` with a duplicate field name | `JSON` |
| A mapping with an empty-string key (`{"": 1}`) | `STRUCT` with a zero-length identifier | `JSON` |
| An integer outside BIGINT — measured boundary is exactly ±2^63 | `BIGINT`, which the value does not fit | `JSON` |

The rule for mappings is stated once, positively: **a mapping is a `STRUCT` only when its keys
stringify to a set of distinct, non-empty names; otherwise it is JSON.** The rule for integers is
the same shape: **an integer is `BIGINT` only when it fits in one.** Nothing is dropped and nothing
is guessed, which is the existing contract; these are the cases where the contract was not applied.

Sub-values are classified by the same function, so `[{}]` becomes `JSON[]` and `{a: {}}` becomes
JSON by way of its field — no special-casing per nesting depth.

### 2. A table build cannot take the load down

The load's promise is that a bad file is logged and skipped, never fatal, and today a single
unrenderable column breaks every query against the bundle. Type rules fix the shapes that are
known; the promise has to hold for the ones that are not. `_build_table` gains a bounded ladder,
each rung logged:

1. Create and insert with the inferred DDL — today's path, unchanged for every bundle that works.
2. On failure, rebuild that table with every non-virtual column as `JSON`. This is the widest
   type in the lattice and the one thing that can hold any value the parser produced.
3. On failure again, create the table with its virtual columns only (`__path`, `__name`, `__body`,
   `__raw`, `__hash`) and no frontmatter columns, so the documents remain addressable and the rest
   of the bundle remains queryable.

Only the affected table degrades; the others are untouched. Each fallback appends to
`schema.warnings`, so `readb schema` shows it and a caller can see that a table is degraded rather
than wondering why a column is missing.

### Public-surface delta

| Surface | Change |
| --- | --- |
| Inferred column types | Four value shapes that previously killed the load now yield `JSON`. No bundle that loads today changes type: every affected shape is one that currently raises. |
| `readb schema` | May now print a warning line for a degraded table. The table and column output is unchanged otherwise. |
| Exit codes, CLI commands, flags, Python API names, on-disk paths | Unchanged. |

### Consequence for the cache, stated rather than discovered

`schema.warnings` being non-empty makes the persistent cache refuse the incremental path (ADR 0006,
because a whole-bundle warning cannot be attributed to a file). A bundle that degrades a table
therefore rebuilds its cache on every change instead of updating it. That is correct and cheap for
the rare bundle it applies to; if it ever stops being rare, the answer is attributable warnings,
not a weaker rule.

### Tests

- One fixture bundle carrying **all nine measured shapes** — `{}`, `[{}]`, `{a: {}}`, `tags: {}`,
  duplicate stringified keys, an empty-string key, and integers at `2^63`, `2^64` and `-2^63` —
  alongside healthy documents. Every healthy document stays queryable and every bad value round
  trips as JSON.
- The boundary is pinned on both sides: `2^62` is still `BIGINT`, `2^63` is `JSON`.
- A test that forces rung 2 and a test that forces rung 3 by monkeypatching the DDL renderer to
  emit something invalid — the ladder must be exercised by something other than the shapes rung 1
  already handles, since those are exactly the ones this task removes.
- A degraded table's warning appears in `schema.warnings` and in `readb schema` output.
- The 12 acceptance criteria and the existing lattice suite keep passing unchanged: this task adds
  total cases, it does not renegotiate any type that already worked.
