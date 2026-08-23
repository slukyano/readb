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

It is also the lever [028-evaluate-rust-rewrite](028-evaluate-rust-rewrite.md) weighs a rewrite
against: repeat-invocation cost is dominated by re-loading, which is a caching problem rather than a
language problem.

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
- Interaction with [021-cross-bundle-querying](021-cross-bundle-querying.md): one cache per bundle,
  attached per schema.
- The acceptance measure is the v1 table above re-measured, plus the multi-query session case.

## Design

The cache is **consent-gated, incrementally updated, and immutable on disk**: nothing is written
unless a `.readb/` registry already exists; a bundle whose files have not changed is served in about
4 ms; a bundle where one file changed is brought up to date in about 7 ms rather than rebuilt; and
every update lands atomically by rename. The read-only promise is restated rather than bent, in
[ADR 0006](../../docs/dev/adr/0006-cache-consent-and-key.md), which also records why git is not used
to detect change.

### Measured basis

Design-branch measurements, duckdb 1.5.4 / CPython 3.14.6 / macOS arm64, medians:

| | 600 concepts | 2000 | 6000 |
| --- | --- | --- | --- |
| Full load from source, after `036-load-pandas-import-probe` | 384 ms | 1266 ms | 3873 ms |
| **Open the cache and query it** | **4.2 ms** | **4.0 ms** | **4.0 ms** |
| **Apply a one-file edit** (open, delete rows, re-parse, insert) | — | — | **6.9 ms** |
| Detect change (`os.scandir` walk) | 1.1 ms | 3.1 ms | 11.1 ms |
| Copy the cache file, which is what makes an update atomic | — | — | 4.7 ms |
| Materialize a fresh cache | 42 ms | 68 ms | 163 ms |
| Cache file size | 4.7 MB | 10.0 MB | 20.5 MB |

Both hit paths are flat in bundle size. A cold miss costs a full load plus the materialize row.

### The three paths

**Hit.** Walk the bundle with `os.scandir`, collecting each file's bundle-relative path, its own
`st_size` and its `st_mtime_ns` — no directory is ever sized. Hash that manifest with the readb and
duckdb versions; the result is carried in the cache's filename, so recognizing a hit opens nothing.
Open the file read-only and return. No markdown file is read at all.

**Incremental.** When the manifest differs, open the cached database and read the per-file metadata
it carries. Files whose stat changed are **hashed before being believed** (0.0016 ms each), so a
touched-but-unmodified file is not re-parsed. What remains is a change set: for each deleted or
modified concept, `DELETE ... WHERE __path = ?` from its type table and from `__DOCUMENTS`; for each
added or modified one, parse the file and insert. Per-(table, column) **type evidence** — a count of
concepts contributing each lattice type — is decremented and incremented alongside, so the unified
column type is recomputed exactly rather than guessed.

The update is applied to a **copy** of the cache file and landed with `os.replace`. Readers in other
processes keep reading the old inode until the rename; a crash mid-update leaves the previous cache
intact; there is no write lock to contend on.

**Full rebuild.** The incremental path is attempted only when the change is provably local. Any of
these falls back to loading from source:

- a column's unified type would change under the lattice;
- a producer key appears for a type, or disappears from it entirely;
- a type appears or disappears;
- the normalized-table-name collision map changes (`_route_concepts` resolves collisions, and a new
  type can change what an existing table is called);
- the `index.md` / `log.md` set changes;
- the readb or duckdb version changes;
- the cache will not open, fails its integrity check, or carries metadata this version does not
  understand.

The list is the correctness argument, so it is written down here and pinned by the property test
below rather than left implicit.

### The invariant

**A cache-hit database answers every query, and prints every `readb schema`, exactly as a freshly
loaded one does.** Not byte-identical: the cache carries `__readb_*` metadata tables that a cacheless
load has no reason to build, and they are excluded from `readb schema` output, which keeps that
public surface unchanged.

A cache hit opens the file read-only. Temp tables still work (verified); persistent DDL fails, which
readb's read-only contract forbids anyway, and it is what stops a caller's stray `CREATE TABLE` from
being persisted into the cache.

### Implementation order

1. Detection, metadata and the **hit path**, with every miss falling back to a full rebuild. This is
   small, and on its own it delivers the whole win for a bundle that is only being read.
2. The **incremental path** on top, guarded by the fallback list, gated by the property test.

If stage 2 could not be made sound, stage 1 would still ship — but the maintainer's case
(edit-then-query on a large bundle) is stage 2's, so shipping only stage 1 is a failure to be
reported, not a quiet outcome.

### Public-surface delta

| Surface | Change |
| --- | --- |
| `readb query`, `readb schema` | New `--no-cache` flag: load from source, neither read nor write the cache. |
| `readb cache status [--bundle B]` | New. Whether a cache exists for the bundle, its path, size and age — or why caching is off. |
| `readb cache clear [--bundle B]` | New. Deletes the bundle's cache file (every bundle in the registry when `--bundle` is omitted). |
| `.readb/config.toml` | New optional key `cache = false`, disabling the cache registry-wide. Absent means enabled. |
| On disk | New `<registry root>/.readb/cache/`, holding one `*.duckdb` file per cached bundle. |
| Python API | `readb.open(path, cache=False)` opts out; otherwise unchanged. |
| `readb init` | **Unchanged.** readb does not write or edit `.gitignore`; the README says `.readb/cache/` is disposable. |
| Output formats, exit codes, `readb get`/`set`/`unset` | Unchanged. |

### Tests

- **The property test**: apply a random sequence of edits to a fixture bundle — add, delete, modify,
  rename, change a value's type, introduce a new key, remove the last user of a key, add a new type —
  and after each step assert that the cached database's schema and full contents equal a fresh
  load's. This is what makes the fallback list falsifiable.
- Hit and miss are asserted **by observation, not timing**: a spy on the parser shows zero files
  parsed on a hit, and exactly the changed files parsed on an incremental update.
- A `readb set` between two queries is observed by the second (mtime invalidation, no cache hook).
- Touching a file without changing its bytes does not re-parse it (the hash-on-suspicion path).
- No registry root → no file is created anywhere, and the query still answers. This pins the consent
  rule.
- `cache = false`, `--no-cache` and `cache=False` each suppress both read and write.
- A corrupt cache file yields a correct answer and a rebuilt cache; an unwritable `.readb/cache/`
  yields a correct answer, no traceback, and no crash.
- A rename that keeps content identical is handled as a delete plus an add, not a stale row.
- Concurrency: a second process reading while an update lands gets one coherent database, never a
  half-written one.

### Deliberately not in this task

- **No git integration.** ADR 0006 records the measurements: `git status` is no faster than the
  `scandir` walk, and it introduces blind spots (ignored files, untracked files, multiple
  repositories, no repository at all) whose failure mode is a stale answer.
- **No daemon, no watcher.** At 4 ms per open the only residual win is amortizing process startup,
  which [ADR 0005](../../docs/dev/adr/0005-stay-on-python.md) prices at nothing.
- **No cross-bundle sharing.** One cache per bundle; `021-cross-bundle-querying` would attach
  per-bundle caches per schema if it is ever built.
- **No `--verify` mode** that content-hashes every file (106 ms at 6000 files). Worth having the day
  someone reports a stale answer; not worth paying for by default.
