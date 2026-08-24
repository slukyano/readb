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

The failing shapes are symptoms: the lattice is not total, so some values have no representable
type. The fix is to make it total **without introducing a second way to represent a mapping** —
a column is a `STRUCT` or it is `JSON`, decided by what the values are, never by which awkward
case was hit. That revises a rule in the binding spec, so it carries
[ADR 0008](../../docs/dev/adr/0008-struct-field-union.md).

### 1. Structs unify by recursive field union

Today two mappings unify to a `STRUCT` only when their key sets match **exactly**, and to `JSON`
otherwise (`docs/dev/design.md` line 82). That is the same problem the union-of-keys rule already
solved one level up, solved differently: a type's table takes the union of every producer key and
fills the gaps with NULL. Mappings now do the same.

| Values in a column | Today | After |
| --- | --- | --- |
| `{a: 1}`, `{a: 2}` | `STRUCT(a BIGINT)` | `STRUCT(a BIGINT)` — unchanged |
| `{a: 1}`, `{b: "x"}` | `JSON` | `STRUCT(a BIGINT, b VARCHAR)`, each missing field NULL |
| `{a: {x: 1}}`, `{a: {y: 2}}` | `JSON` | `STRUCT(a STRUCT(x BIGINT, y BIGINT))` — recursive |
| `{a: 1}`, `"text"` | `JSON` | `JSON` — a mapping and a non-mapping still meet at the top |

Fields stay sorted by name, so the type is deterministic regardless of document order.

### 2. An all-empty mapping gets a placeholder field

`{}` contributes no fields, so a column whose values are *all* empty mappings would render as
`STRUCT()`, which is not valid DDL. Such a column is rendered `STRUCT("__DUMMY" VARCHAR)` — one
placeholder field, always NULL. As soon as any value contributes a real field the placeholder is
gone, because the union is non-empty; `{}` beside `{a: 1}` is simply `STRUCT(a BIGINT)` with a NULL
row.

The placeholder is visible: `readb schema` prints it and `SELECT flag FROM t` returns
`{'__DUMMY': NULL}`. That is the price of a mapping column that carries no keys at all, and it is
preferable to the column silently becoming something else.

### 3. Keys are normalized once, at the parse boundary — before any type is chosen

YAML keys may be any scalar; a `STRUCT` field name is a string. **JSON does not rescue this**, which
is worth stating because it was the obvious escape: `json.dumps({1: "a", "1": "b"})` emits
`{"1": "a", "1": "b"}` — a duplicate key in the text, malformed as data even though a reader happens
to keep the last one. A mapping that cannot be a `STRUCT` cannot be honest JSON either, so the
collision has to be resolved *before* a type is chosen, not by choosing a different type.

So `parse_file` normalizes every mapping it returns, recursively: **each key is stringified, and
when two collide the last occurrence in document order wins.** That is the rule PyYAML already
applies to genuinely duplicate YAML keys, so one convention covers both, and `readb get` agrees with
`SELECT`. Each collision is logged once per document, because a dropped value deserves a line.

Everything downstream — `STRUCT` field names, JSON encoding, column naming, `readb set` — then sees
one normalized mapping and cannot disagree about it.

**This also fixes a losslessness bug found while designing the rule.** A non-string key at the *top*
level is not just untyped, it is silently discarded: `_producer_keys` skips any key that is not a
`str` (`loader.py:326`), so

```yaml
---
type: T
1: one
true: yes
2026-01-01: dated
---
```

produces a `t` table with **no column for any of the three**, no warning, and the values reachable
only through `__raw`. Union-of-keys is supposed to be lossless. With normalization at the parse
boundary the keys arrive as `"1"`, `"True"` and `"2026-01-01"`, and become ordinary columns.

### 4. An integer that does not fit BIGINT is text

`type_of_value` calls every Python integer a `BIGINT`; the measured boundary is exactly ±2^63, and a
value outside it kills the load at insert time. Such a value is classified `VARCHAR` — its decimal
text, lossless and comparable — and the normal lattice rules take it from there.

**The consequence, stated because it is a decision and not an accident:** a column mixing in-range
and out-of-range integers unifies `BIGINT` with `VARCHAR`, which the existing lattice sends to
`JSON`. That is lossless — verified rather than assumed: DuckDB's JSON type stores
`1180591620717411303424` and returns it intact, and each value keeps its own JSON encoding, so `42`
and `"high"` remain a number and a string rather than being flattened into one type. JSON's weakness
is duplicate *keys*, which rule 3 removes before typing begins; incompatible *values* are exactly
what it is for.

### 5. A table build still cannot take the load down

With the lattice total, the nine measured shapes load. The promise — a bad file is logged and
skipped, never fatal — has to hold for shapes nobody has enumerated yet, so `_build_table` gains a
bounded ladder, each rung logged and recorded in `schema.warnings`:

1. Create and insert with the inferred DDL — today's path, unchanged for every bundle that works.
2. On failure, rebuild that table with every non-virtual column as `JSON`.
3. On failure again, create it with virtual columns only, so its documents stay addressable.

Only the affected table degrades. This is defence in depth rather than a fix for anything known to
be broken, and it can be dropped without affecting the four rules above.

### Public-surface delta — including a breaking change

| Surface | Change |
| --- | --- |
| Inferred column types | **Breaking:** a column of mappings with differing key sets is `STRUCT` where it was `JSON`. A query using JSON access (`flag ->> 'a'`) on such a column breaks; struct access (`flag.a`) starts working. Columns whose key sets already matched are unaffected. |
| Inferred column types | Four shapes that previously *killed the load* now have types: empty mappings (`STRUCT("__DUMMY" VARCHAR)` when nothing else contributes), colliding stringified keys (last wins), an out-of-range integer (`VARCHAR`). |
| Columns | A frontmatter key that is not a string now becomes a column under its stringified name. Today it is silently dropped, so nothing that works loses a column — bundles gain the ones they were missing. |
| `readb schema` | Prints `STRUCT(...)` where it printed `JSON` for those columns, plus a warning line for a degraded table. |
| Exit codes, CLI commands, flags, Python API names, on-disk paths | Unchanged. |

Caches built by an earlier readb are invalidated automatically: the cache key carries the readb
version (ADR 0006), so no bundle is served types from the old rule.

### Tests

- A fixture bundle carrying **all nine measured shapes** alongside healthy documents: every healthy
  document stays queryable, and every previously fatal value round trips.
- The union rule at each shape: disjoint key sets, overlapping key sets, nested mappings unified
  recursively, a mapping beside a non-mapping still meeting at `JSON`.
- The placeholder: a column of only `{}` is `STRUCT("__DUMMY" VARCHAR)`; adding one real key removes
  the placeholder entirely.
- Key collision at both levels: `{1: a, "1": b}` keeps `b` and logs, nested and at the top level.
- Non-string top-level keys (`1:`, `true:`, a date) become columns carrying their values, which is
  the losslessness regression this rule closes.
- The integer boundary on both sides: `2^62` is `BIGINT`, `2^63` and `-2^63 - 1` are `VARCHAR`.
- Rungs 2 and 3 of the ladder, forced by monkeypatching the renderer to emit invalid DDL — the
  shapes that used to reach them are exactly the ones this task removes.
- The 12 acceptance criteria keep passing; the lattice suite gains cases and loses none.
