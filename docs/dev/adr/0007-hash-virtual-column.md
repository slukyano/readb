---
type: ADR
title: '__hash joins the virtual columns: the lowercase hex SHA-256 of the file bytes'
status: Proposed
created: 2026-08-23
sprint: sprint-006
timestamp: '2026-08-23T00:00:00Z'
---

# Context

[ADR 0003](0003-virtual-columns.md) defined readb's virtual columns — `__path`, `__name`, `__body`,
`__raw` — as the file-level facts a query may need that are not frontmatter keys.

`034-persistent-index-cache` adds a per-file content digest to the load, because telling a *touched*
file from a *changed* one is what keeps a mass mtime change from causing a mass rebuild. That value
exists on every load; the question is whether it is internal machinery or part of the queryable
surface.

Measured on a 6000-concept bundle (11.9 MB, mean file 1984 B), hashing bytes the loader already
holds: SHA-256 costs 4.8 ms, blake2b-128 9.6 ms, md5 14.4 ms. Stored as a 64-character hex
`VARCHAR` a column of 6000 hashes occupies 524 KB — the same as a 16-byte `BLOB`, because DuckDB's
block granularity dominates at that size.

# Decision

**`__hash` becomes a virtual column, carrying the lowercase hexadecimal SHA-256 of the file's
bytes** — the value `sha256sum` prints for the same file. It appears in every table that carries
`__raw` (`__DOCUMENTS`, each type table, `__INDEXES`, `__LOG`, `__UNKNOWNTYPE`), is listed by
`readb schema` like the other virtual columns, and is computed on every load whether or not the
cache is enabled.

**The algorithm is part of the contract.** `__hash` is SHA-256 over the raw file bytes, with no
normalization of line endings, encoding or trailing whitespace, and no framing of the kind
`git hash-object` applies. Changing the algorithm would change what every stored value means, so it
requires an ADR superseding this one.

`034-persistent-index-cache` consumes this same value for change detection instead of keeping a
private digest, so there is one hash in the system with one definition.

# Consequences

- Duplicate detection (`GROUP BY __hash HAVING count(*) > 1`), change tracking against an external
  snapshot, and cross-bundle content comparison become queries rather than features.
- Every load costs 0.80 µs per file more — 4.8 ms on a 3873 ms load of 6000 concepts, 0.12%.
- A cached 6000-concept bundle grows by roughly 1 MB against 22 MB, since the column is carried in
  `__DOCUMENTS` and again in each type table, as every virtual column is.
- The value is reproducible outside readb with standard tools, which is what makes it useful in a
  pipeline and what makes the contract testable.
- SHA-256 was chosen over faster-in-principle alternatives because it measured fastest here anyway;
  if that ever inverts, the cost of switching is a superseding ADR and a cache invalidation, not a
  silent change.

# Alternatives considered

**Name it `__sha256`.** Pins the algorithm in the column name, so a future change could not silently
redefine it. Rejected for consistency with the plain naming of `__path` and `__raw`; the guarantee is
carried by this ADR instead, which is where the other columns' contracts live too.

**Keep the digest internal to the cache.** No measurable saving, and it would leave duplicate-finding
as a feature request instead of a one-line query.

**Hash the parsed content rather than the bytes** (frontmatter plus body, normalized). More stable
across formatting changes, and much less useful: it would match nothing any other tool computes, and
readb's own change detection needs byte identity, not semantic identity.
