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
