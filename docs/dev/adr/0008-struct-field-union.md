---
type: ADR
title: 'The lattice promotes to the narrowest type that holds every value: field union for mappings, VARCHAR for mixed scalars'
status: Accepted
created: 2026-08-23
sprint: sprint-007
timestamp: '2026-08-23T22:00:00Z'
---

# Context

The binding spec fixed the rule as "maps with a consistent key set → STRUCT; inconsistent keys →
JSON" (`docs/dev/design.md`). One level up, the same problem is solved the opposite way: a type's
table takes the **union** of every producer key any document of that type carries, and fills the
gaps with NULL. Two documents that differ by a key do not fall back to a single opaque column;
they widen the table.

Mappings did not get that treatment, and the inconsistency has three costs.

**It loses queryability for no reason.** `{a: 1}` beside `{b: "x"}` becomes `JSON`, so a reader who
could have written `flag.a` writes JSON extraction instead — over data whose shape readb already
knows.

**It makes a column's type depend on which awkward case was hit**, rather than on what the values
are. That is the property the adversarial review of `034-persistent-index-cache` turned into a
correctness bug: a type that varies with circumstance is a type nothing can recompute.

**It was not total.** Four value shapes had no representable type at all and killed the whole load
rather than one file (`041-empty-struct-crashes-the-load`): an empty mapping renders `STRUCT()`,
two YAML keys can collide once stringified, an empty-string key is not an identifier, and an
integer outside ±2^63 is not a `BIGINT`. A rule that answers "JSON" for each awkward case would
have made the lattice total while entrenching the first two costs.

# Decision

**A column takes the narrowest type that holds every value it has, and falls to JSON only when no
such type exists.** Today the lattice reaches for JSON as soon as two values disagree at all, which
throws away a type that would have held both.

**Scalars promote to `VARCHAR` rather than to JSON.** Text holds any scalar losslessly, stays
readable in query output, and remains usable with `LIKE` and ordering, where JSON is opaque. Of the
fifteen scalar pairs, thirteen change:

| | Today | After |
| --- | --- | --- |
| `BIGINT` + `DOUBLE` | `DOUBLE` | `DOUBLE` — unchanged, and the one deliberate exception to the rule above |
| `DATE` + `TIMESTAMP` | `JSON` | `TIMESTAMP` — a date is midnight, the widening SQL itself performs |
| every other scalar pair | `JSON` | `VARCHAR` |

**`BIGINT` + `DOUBLE` → `DOUBLE` is not lossless, and is kept anyway.** A double cannot hold an
integer above 2^53: a column with `9007199254740993` beside `1.5` returns `9007199254740992`. That
contradicts the rule this ADR states, so it is recorded as an exception rather than left to be
discovered. It is kept because it is what SQL itself does — verified against DuckDB, which resolves
`BIGINT` with `DOUBLE` to `DOUBLE` in a `UNION`, in arithmetic, in `COALESCE` and in a list, and
loses exactly the same precision silently; the SQL standard's numeric rule (exact + approximate →
approximate) says the same. Making readb's most ordinary numeric shape — an integer beside a
decimal — into text to avoid a precision loss above 2^53 would cost every numeric comparison in the
column and surprise every user who knows SQL. Values above 2^53 remain exact in `__raw`, and an
integer too large for `BIGINT` at all is still `VARCHAR`.

The scalar order is `NULL` < {`BOOLEAN`, `BIGINT` < `DOUBLE`, `DATE` < `TIMESTAMP`} < `VARCHAR` <
`JSON`. A value promoted into a `VARCHAR` column is rendered canonically from the *parsed* value —
`true`/`false`, decimal integers, shortest round-tripping floats, ISO-8601 dates — which matches the
file for ordinary spellings and normalizes the alternates YAML allows (`yes` becomes `true`, `0x10`
becomes `16`, `00123` becomes `83`). The file's own bytes remain in `__raw`.

JSON remains the top of the lattice and the universal fallback, but it is now reached only when the
values disagree *structurally* — a scalar against a mapping, a list against a mapping — where no
narrower type can hold both.

**Two mappings unify to a `STRUCT` whose fields are the union of theirs, recursively**, with each
shared field's type unified in turn and each missing field NULL for the documents that lack it.
Field order is by name, so the type does not depend on document order.

A mapping unified with a non-mapping is still `JSON`: JSON remains the top of the lattice and the
universal fallback, and this decision does not move it.

Three rules make the mapping case total:

1. **A column whose mappings contribute no fields at all is `STRUCT("__DUMMY" VARCHAR)`** — one
   placeholder field, always NULL, because `STRUCT()` is not valid DDL. The placeholder disappears
   as soon as any value contributes a real field.
2. **Keys are normalized at the parse boundary, before any type is chosen**: stringified
   recursively, and when two collide the last occurrence in document order wins — the rule PyYAML
   already applies to genuinely duplicate YAML keys, so `readb get` and `SELECT` agree with the
   file. A collision is logged. Choosing JSON instead would not have helped: `json.dumps` renders
   `{1: "a", "1": "b"}` as `{"1": "a", "1": "b"}`, a duplicate key in the text. JSON absorbs
   incompatible *values*; it cannot absorb a duplicate *key*.
3. **An integer outside ±2^63 is `VARCHAR`**, carrying its decimal text. `type_of_value` claimed
   `BIGINT` for every Python integer, which is a promise the engine cannot keep. With scalar
   promotion above, a column mixing in-range and out-of-range integers is `VARCHAR` throughout
   rather than JSON — the whole column takes the type that holds all of it.

# Consequences

- **Breaking, and wider than the mapping rule alone.** Thirteen of the fifteen scalar pairs move
  from `JSON` to `VARCHAR` (or `TIMESTAMP`), so a column mixing, say, `rank: 1` with `rank: high` is
  now text. JSON extraction on such a column breaks; ordinary string predicates start working.
- **Breaking.** A column of mappings with differing key sets is now `STRUCT` where it was `JSON`:
  JSON access (`flag ->> 'a'`) on such a column breaks, and struct access (`flag.a`) starts
  working. Columns whose key sets already matched are unaffected, as is every non-mapping column.
  Persistent caches are invalidated automatically, since the cache key carries the readb version.
- Four value shapes that made an entire bundle unqueryable now load.
- A frontmatter key that is not a string becomes a column under its stringified name. Today the
  loader skips it and the value is reachable only through `__raw` — a silent breach of the
  union-of-keys promise, fixed by the same normalization.
- Struct unification becomes **associative and commutative**, since set union is, and scalar
  promotion removes the counterexample that forced `readb.cache` to refuse mixed-type columns
  (`DOUBLE`, `VARCHAR`, `LIST<BIGINT>` folded in two orders now agree). Whether the lattice is
  associative *everywhere* is a separate claim needing its own proof or fuzzing, so the cache's
  guard stays until someone establishes it.
- A promoted column normalizes alternate YAML spellings, so a bundle written with `yes` and `0x10`
  reads back `true` and `16`. That is a consequence of typing the parsed value rather than the text,
  which readb has always done; promotion just makes it visible in a column a reader will look at.
- A pathological bundle can now produce a very wide struct — one field per distinct key across
  every document of that type. That is the same exposure the union-of-keys rule already accepts for
  table columns, and it is bounded by the same thing: what the producer actually wrote.
- `__DUMMY` is visible in `readb schema` output and in query results for the all-empty case. A
  mapping column carrying no keys is degenerate, and showing that plainly beats reclassifying the
  column as something else.

# Alternatives considered

**Answer `JSON` for each awkward shape** — an empty mapping, colliding keys, an oversized integer.
Makes the lattice total in the fewest lines, and was the first design. Rejected: it decides a
column's type by which edge case it met rather than by its values, which is precisely the
variability that made the cache's incremental path unsound, and it leaves the union inconsistency
in place.

**Keep matching-key-sets and add the union only for the empty case.** Rejected as the worst of
both: two rules for mappings, and the queryability loss stays.

**Represent an all-empty mapping column as `VARCHAR` or `JSON` instead of a placeholder struct.**
Rejected: the column *is* a mapping column, and the type should say so. A placeholder field is
honest about the degeneracy; a different type hides it and changes again the moment a key appears.

**Keep JSON for mixed scalars, promoting only oversized integers to text.** The narrower change,
and the one first proposed. Rejected: it decides a column's type by which case it met rather than by
what would hold its values, which is the same inconsistency the mapping rule removes. A rule applied
in one place and not the other is the thing worth avoiding here.
