---
type: Task
title: Persistent index cache behind the load seam
description: Stop re-parsing the whole bundle on every invocation — cache the loaded index under `.readb/` and reuse it when the working tree has not changed.
status: Draft
priority: medium
tags:
- performance
- loader
- architecture
created: 2026-08-22
---

The load path re-reads and re-parses every file on every invocation, by design: the MVP's
[design brief](../../docs/dev/design.md) declared a persistent index an explicit non-goal and
asked only that the seam be left in place ("Build the seam, not the cache"). The seam exists —
`load_bundle` in `src/readb/loader.py` — and [ADR 0004](../../docs/dev/adr/0004-init-registry-discovery.md)
put `.readb/` in the repository as its future home. This task is the cache itself.

## The evidence

Measured per-invocation load-plus-query time on the v1 corpora, paid **per query, not per
session**:

| Concepts | Load + query |
| --- | --- |
| 150 | 0.28–0.35 s |
| 600 | 0.80–0.89 s |
| 2000 | 2.52–2.79 s |

[v1](../../docs/dev/research/agent-efficiency.md) calls this "the strongest argument in the data
for the persistent index cache the loader was designed to accommodate": at 2000 concepts, the
one battery question that asks five questions in a session is the single place readb *loses* wall
clock, because five queries mean five full bundle loads. A multi-query agent session is the normal
case, not the edge case.

It is also the lever [028](028-evaluate-rust-rewrite.md) weighs a rewrite against: repeat-invocation
cost is dominated by re-loading, which is a caching problem rather than a language problem.

## The intended design, as recorded

From the design brief: the index is a DuckDB file keyed to a git hash; on load, the working tree is
diffed against that hash and only changed files are re-parsed (so a dirty tree stays correct). No
daemon and no watcher — with a DuckDB-file index, page cache and mmap make repeat opens near-free,
and the only residual win would be amortizing process startup.

## Notes (to refine)

- **The read-only constraint has to be re-stated, not quietly bent.** Today the rule is absolute:
  loading and querying never create or modify any file. A cache writes. Whether that write is
  opt-in, implied by `readb init`, or automatic — and what happens for a bundle with no `.readb/`
  and no registry — is the ADR-shaped decision at the centre of this task.
- **Staleness is the failure mode that matters.** A slow correct answer is cheap; a fast wrong one
  from a stale index is not. Whatever key is chosen (git hash + dirty-file diff, or mtime/size for
  non-git bundles) has to be conservative: unsure means re-parse.
- **Non-git bundles are not the exception.** readb is a general-purpose tool over any OKF bundle;
  the key cannot assume a repository.
- Concurrency: two readb processes over one bundle, one of them building the index.
- Invalidation from the write path: `readb set`/`unset` edits a file the cache has already indexed.
- Where the file lives when the bundle is outside any registry root, and what `.gitignore`
  handling ships with it (`load_bundle` already skips `.readb/` during the walk).
- Whether any command surface is needed at all (`readb index`/`--no-cache`/`--rebuild`), or whether
  the cache should be entirely invisible except in timings.
- Interaction with [021](021-cross-bundle-querying.md): one cache per bundle, attached per schema.
- The acceptance measure is the v1 table above re-measured, plus the multi-query session case.

## Design

The cache is **all-or-nothing and consent-gated**: a bundle whose files have not changed since the
last load is served from a materialized DuckDB file in about 4 ms; any change at all rebuilds the
whole thing; and nothing is ever written unless the user has already created a `.readb/` registry
with `readb init`. The read-only promise is restated rather than bent, in
[ADR 0006](../../docs/dev/adr/0006-cache-consent-and-key.md).

### Measured basis

Taken on the design branch, same conditions as [028](028-evaluate-rust-rewrite.md)'s table:

| | 600 concepts | 2000 | 6000 |
| --- | --- | --- | --- |
| Materialize the loaded database to a file | 42 ms | 68 ms | 163 ms |
| Cache file size | 4.7 MB | 10.0 MB | 20.5 MB |
| **Reopen + query (the hit path)** | **4.2 ms** | **4.0 ms** | **4.0 ms** |
| Stat-only walk (the staleness check) | 2.1 ms | 6.4 ms | 20.3 ms |
| Full load, after `036` | 384 ms | 1266 ms | 3873 ms |

A hit is flat in bundle size; a miss costs the full load plus the materialize column. Both are
measured, not projected.

### Behaviour

**The key.** A manifest is built by walking the bundle exactly as the loader walks it (the same
skip rules, `.readb/` included), recording for every file its bundle-relative POSIX path, size and
`st_mtime_ns`. The manifest is hashed together with the readb version, the duckdb version and the
bundle's resolved absolute path. That hash is the cache identity — no git, no content hashing: the
walk must stay cheap, and mtime granularity on any filesystem readb runs on is nanoseconds.

**The file.** `<registry root>/.readb/cache/<bundle-slug>-<manifest-hash>.duckdb`. The hash is *in
the filename*, so the existence of the file is the hit and there is no sidecar to keep in sync. A
write goes to a temp file in the same directory and lands with `os.replace`, which is atomic; two
readb processes racing on the same bundle both end up correct, and the loser's work is discarded.
After a successful write, other files with the same `<bundle-slug>-` prefix are removed, so a
bundle costs one cache file rather than one per revision.

**The hit path.** Build the manifest, compute the hash, and if the file exists, open it and return.
Nothing else is read; no markdown file is opened at all.

**The miss path.** Load as today, materialize with `COPY FROM DATABASE`, rename into place, return
the in-memory connection. The caller never waits on a second load.

**Never stale, never fatal.** Any failure on the hit path — the file will not open, its stored
readb version does not match, DuckDB reports corruption — is treated as a miss and rebuilt, logged
at debug level. Any failure on the write path (read-only filesystem, no space, a permissions
problem) is logged and swallowed: a cache that cannot be written must never fail a query. The
permissive-load contract extends to the cache.

**Invalidation is free.** `readb set`/`unset` rewrite a file, which changes its `st_mtime_ns`,
which changes the manifest hash. No explicit invalidation hook is needed, and a test pins that a
`set` between two queries is observed by the second.

**Schema restoration.** DuckDB's catalog gives back the tables and column types on reopen, but not
the normalized-table-name to original-`type:`-string mapping that `readb schema` prints. That
mapping is stored as JSON in a `__readb_meta` table created on **both** paths, so a cached load and
a fresh load are byte-for-byte the same database. It is excluded from `readb schema` output, which
keeps that public surface unchanged.

### Public-surface delta

| Surface | Change |
| --- | --- |
| `readb query`, `readb schema` | New `--no-cache` flag: load from source, neither read nor write the cache. |
| `readb cache status [--bundle B]` | New. Prints whether a cache exists for the bundle, its path, size and age, or why caching is off. |
| `readb cache clear [--bundle B]` | New. Deletes the bundle's cache files (all bundles in the registry when `--bundle` is omitted). |
| `.readb/config.toml` | New optional key `cache = false` disables caching for the whole registry. Absent means enabled. |
| On disk | New directory `<registry root>/.readb/cache/`, holding one `*.duckdb` file per cached bundle. |
| `readb init` | Adds `cache/` to the `.gitignore` it maintains under `.readb/`. |
| Python API | Unchanged. `readb.open(path)` uses the cache under the same rules; `readb.open(path, cache=False)` opts out. |
| Output formats, exit codes, `readb get`/`set`/`unset` | Unchanged. |

### Tests

- Hit and miss are asserted **by observation, not by timing**: a fixture bundle is loaded twice
  with a spy on the parser — the second load parses zero files.
- A `set` between two loads is observed by the second (mtime invalidation).
- Adding, deleting and renaming a file each force a miss; touching nothing forces a hit.
- No registry root → no cache file is created anywhere, and the query still answers. This is the
  test that pins the consent rule.
- `cache = false`, `--no-cache` and `cache=False` each suppress both read and write.
- A corrupt cache file (truncated bytes) yields a correct answer and a rebuilt cache.
- An unwritable `.readb/cache/` yields a correct answer, no traceback, and no crash.
- A cached load and a fresh load produce identical `readb schema` output and identical query
  results over the same bundle.
- Cache files for older revisions of the same bundle are removed on write.

### Deliberately not in this task

- **No incremental re-parse.** The design brief imagined diffing against a git hash and re-parsing
  only changed files. It is not built: the column-type lattice unifies across every concept of a
  type, so one changed file can change a column's type and force the table to be rebuilt anyway.
  All-or-nothing captures the measured case — repeated queries against an unchanged bundle — and
  keeps the correctness argument short.
- **No daemon, no watcher.** The design brief's reasoning holds: at 4 ms per open, the only
  residual win is amortizing process startup, and [ADR 0005](../../docs/dev/adr/0005-stay-on-python.md)
  prices that at nothing.
- **No cross-bundle sharing.** One cache per bundle; [021](021-cross-bundle-querying.md) attaches
  per-bundle caches per schema if it is ever built.
