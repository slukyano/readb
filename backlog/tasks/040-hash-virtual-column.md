---
type: Task
title: Expose the file's content hash as a __hash virtual column
description: The cache computes a per-file digest for change detection; exposing it as a queryable virtual column makes duplicate-finding, change tracking and cross-bundle comparison one-liners.
status: Designed
priority: medium
tags:
- query
- schema
- cache
created: 2026-08-23
timestamp: '2026-08-23T12:00:00Z'
---

Raised while designing `034-persistent-index-cache`, which computes a content digest per file to
tell a touched file from a changed one. The value is already there; today it would be internal
metadata. Making it a virtual column alongside `__path`, `__name`, `__body` and `__raw`
([ADR 0003](../../docs/dev/adr/0003-virtual-columns.md)) turns it into something a query can use.

## What it buys

```sql
-- byte-identical documents
SELECT __hash, count(*), list(__name) FROM __DOCUMENTS GROUP BY __hash HAVING count(*) > 1;

-- what changed since a recorded snapshot
SELECT __name FROM __DOCUMENTS WHERE __hash NOT IN (SELECT h FROM read_csv('snapshot.csv'));
```

Duplicate detection, change tracking against an external record, cross-bundle comparison (the join
`021-cross-bundle-querying` would enable), and content-addressed export all become expressible
without readb growing a feature for each.

## Design

**`__hash` is the lowercase hex SHA-256 of the file's bytes** — exactly what `sha256sum` prints for
the same file, so it is reproducible outside readb and means something to a reader.

Measured on a 6000-concept bundle (11.9 MB, mean file 1984 B), hashing bytes already in hand:

| Digest | 6000 files | Per file |
| --- | --- | --- |
| **sha256** | **4.8 ms** | **0.80 µs** |
| blake2b-128 | 9.6 ms | 1.60 µs |
| md5 | 14.4 ms | 2.39 µs |

SHA-256 is both the recognizable choice and the fastest measured one (hardware acceleration), so
there is no trade to make. Column storage is 524 KB per 6000 rows, identical for a 64-character hex
`VARCHAR` and a 16-byte `BLOB` — DuckDB's block granularity dominates, so the readable form is free.

- Populated on **every** load, cached or not: 4.8 ms on a 3873 ms load is 0.12%, and a virtual
  column cannot exist only when caching happens to be on.
- Present wherever `__raw` is: `__DOCUMENTS`, each type table, `__INDEXES`, `__LOG`,
  `__UNKNOWNTYPE`. Roughly 1 MB on a 22 MB cache for a 6000-concept bundle.
- Listed by `readb schema` exactly as the other virtual columns are.
- `034-persistent-index-cache` uses this same value for change detection rather than keeping a
  second digest of its own.

**Public-surface delta**: one new virtual column, `__hash`, in every table that has `__raw`; one new
line in `readb schema` output per table; [ADR 0007](../../docs/dev/adr/0007-hash-virtual-column.md)
extending the virtual-column set defined by ADR 0003. No CLI flag, no config key, no new path.

### Tests

- `__hash` equals `sha256sum` of the file, for a fixture with unicode, CRLF and a trailing-newline-
  free file.
- Two byte-identical files in different directories share a hash; changing one byte changes it.
- The column is present in every table that carries `__raw`, and in `readb schema` output.
- A file that fails to parse still gets a hash in `__UNKNOWNTYPE` where it lands.
- The cache's detection and the exposed column never disagree (one value, one code path).

### Alternatives considered

- **`__sha256` as the name**, pinning the algorithm in the column itself, so a future change of
  digest could not silently change what the column means. Rejected in favour of matching the plain
  style of `__path`/`__raw`, with the algorithm pinned by ADR 0007 instead: changing it requires a
  superseding ADR, which is the same guarantee with less noise.
- **Keep the digest internal to the cache.** Cheaper by nothing measurable, and it would make
  duplicate-finding a feature request rather than a query.
