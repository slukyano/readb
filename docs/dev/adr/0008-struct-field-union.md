---
type: ADR
title: 'Mappings unify by recursive field union, not by matching key sets'
status: Proposed
created: 2026-08-23
sprint: sprint-007
timestamp: '2026-08-23T00:00:00Z'
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

**Two mappings unify to a `STRUCT` whose fields are the union of theirs, recursively**, with each
shared field's type unified in turn and each missing field NULL for the documents that lack it.
Field order is by name, so the type does not depend on document order.

A mapping unified with a non-mapping is still `JSON`: JSON remains the top of the lattice and the
universal fallback, and this decision does not move it.

Three rules make the mapping case total:

1. **A column whose mappings contribute no fields at all is `STRUCT("__DUMMY" VARCHAR)`** — one
   placeholder field, always NULL, because `STRUCT()` is not valid DDL. The placeholder disappears
   as soon as any value contributes a real field.
2. **Keys are stringified, and when two collide the last occurrence in document order wins** — the
   rule PyYAML already applies to genuinely duplicate YAML keys, so `readb get` and `SELECT` agree
   with the file. A collision is logged.
3. **An integer outside ±2^63 is `VARCHAR`**, carrying its decimal text. `type_of_value` claimed
   `BIGINT` for every Python integer, which is a promise the engine cannot keep.

# Consequences

- **Breaking.** A column of mappings with differing key sets is now `STRUCT` where it was `JSON`:
  JSON access (`flag ->> 'a'`) on such a column breaks, and struct access (`flag.a`) starts
  working. Columns whose key sets already matched are unaffected, as is every non-mapping column.
  Persistent caches are invalidated automatically, since the cache key carries the readb version.
- Four value shapes that made an entire bundle unqueryable now load.
- Struct unification becomes **associative and commutative**, since set union is. That removes one
  source of the order-dependence that forced `readb.cache` to refuse mixed-type columns; the
  scalar-and-list rules are still order-dependent, so the guard stays.
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

**Make `BIGINT` unify with `VARCHAR` as `VARCHAR`** so a column mixing in-range and out-of-range
integers stays text rather than becoming `JSON`. Not decided here — it is a change to scalar
unification affecting every mixed scalar column, not just oversized integers, and it is raised as
an open question with `041-empty-struct-crashes-the-load`.
