---
type: ADR
title: 'The persistent cache writes only under an existing .readb/, detects change by a per-file stat manifest, and applies changes incrementally'
status: Proposed
created: 2026-08-22
sprint: sprint-006
timestamp: '2026-08-23T00:00:00Z'
---

# Context

readb's hardest promise is that reading is inert: loading a bundle and running SQL never create or
modify any file. A persistent index cache — planned since the design brief, which left
`load_bundle` as the seam to wrap, and given a home by [ADR 0004](0004-init-registry-discovery.md) —
writes a file. That is a change to the promise and it needs stating as one.

Three questions have to be answered together, and they are **independent axes** that are easy to
conflate:

1. **Consent** — when may readb write a cache at all?
2. **Detection** — how does a load discover that the bundle changed?
3. **Granularity** — how much is rebuilt when it did?

Git appears as a candidate answer to (2), and a git-diff-driven rebuild as an answer to (3); the
two are separable, and the evidence below treats them separately.

Measured on the sprint-006 design branch (duckdb 1.5.4, CPython 3.14.6, macOS arm64, medians),
against a 6000-concept bundle unless stated:

| Detecting change | 600 | 2000 | 6000 | 20000 |
| --- | --- | --- | --- | --- |
| `os.scandir` walk collecting size + mtime | 1.0 ms | 3.3 ms | 10.7 ms | 41.6 ms |
| `pathlib.rglob` + `stat()` (the naive version) | 1.7 ms | 5.2 ms | 17.7 ms | — |
| `git status --porcelain` (clean tree) | — | — | 11.9 ms | — |
| `git status --porcelain --ignored` | — | — | 12.3 ms | — |
| `git rev-parse HEAD` | — | — | 4.0 ms | — |
| `git ls-files` | — | — | 6.1 ms | — |
| Read (not parse) every file | 8.2 ms | — | ~100 ms | — |
| Confirm a suspect file by content hash | — | — | 0.014 ms each | — |
| Re-parse a file instead of confirming it | — | — | 0.161 ms each | — |

| Rebuilding | 6000 concepts |
| --- | --- |
| Full load from source, after the `036-load-pandas-import-probe` fix | 3873 ms |
| Open the cache and query it (no change) | 4.0 ms |
| Apply a one-file edit: open, delete that file's rows, re-parse, insert | 6.9 ms |
| Copy the cache file (what makes an update atomic) | 4.7 ms |

# Decision

**1. Consent. readb writes a cache only when a `.readb/` registry root already exists above the
bundle**, and never anywhere else. No registry means no cache and today's behaviour exactly. The
gesture that creates that directory is `readb init`, which ADR 0004 already established as the user
saying "this repository is readb's to work in". A registry-wide `cache = false` in `config.toml`, a
per-invocation `--no-cache`, and `readb.open(path, cache=False)` all switch it off.

The read-only rule is restated, not weakened: **loading and querying never create or modify any file
in the bundle, and never any file at all outside a `.readb/` directory the user created.**

**readb never edits `.gitignore`,** or any other file belonging to the user's tooling. What to ignore
is the user's business; the documentation says `.readb/cache/` is disposable and the rest is theirs.

**2. Detection: a per-file stat manifest, with every suspect confirmed by content hash.**

The manifest is built by an `os.scandir` walk that mirrors the loader's own walk, recording for each
file its bundle-relative POSIX path, **that file's own `st_size`**, and its `st_mtime_ns`. No
directory is ever sized — a directory's size is not defined cheaply on any filesystem, and nothing
here needs it.

A file whose size and mtime match its manifest entry is unchanged. A file whose stat moved is a
**suspect**, and every suspect is read and hashed before anything is rebuilt. The order matters
because confirming is **twelve times cheaper than re-parsing** — 0.014 ms against 0.161 ms per file —
so the check never costs more than the work it might save:

- hash matches → the file was touched, not changed. Its manifest entry is refreshed and nothing else
  happens.
- hash differs → the file is genuinely changed and joins the change set.

**A mass mtime change therefore cannot cause a mass rewrite.** Six thousand touched-but-identical
files confirm in 95 ms and the cached database stands, against 3873 ms to rebuild it. That case is
routine — a formatter rewriting every file with identical bytes, a `cp -R` or `rsync` without `-t`,
an unzip, a restore from backup, a sync client, a `git checkout` away and back — and it is the case
this check exists for.

Hashes cost 16 bytes per file: 256 KB for a 6000-file bundle, about 1% of its cache. They are stored
independently of which columns the cache holds, so
`038-derive-text-columns` can change what is stored without touching change detection.

**The known limitation: this assumes stat is cheap.** It is, on a local disk — 1.7–2.1 µs per file,
linear from 600 to 20000 files, 0.3% of the load it replaces, and a strict subset of the
open-and-read that every uncached load already performs on the same files. On an S3-backed
filesystem, or NTFS or SMB over a network, per-file stat is not cheap, and neither is `git status`,
which stats every file for the same reason. The escape for those filesystems is a change detector
that does not walk at all — git backed by an fsmonitor daemon, where detection becomes O(changed
files) rather than O(files) — and that is deliberately **not** built here. It is
`039-git-aware-change-detection`, an optimization to be added behind the same seam once the cache
exists.

**3. A large *confirmed* change set falls back to a full rebuild.** Applying thousands of individual
deletes and inserts is slower than loading the bundle from scratch, so above a threshold (a quarter
of the bundle, floor 500 files) the incremental path is abandoned before it starts. The threshold
counts files whose **content** changed, never files whose mtime merely moved — those have already
been filtered out by the confirmation step above.

**4. Granularity: incremental.** A change set of added, deleted and modified files is applied to the
cached database — delete the affected concepts' rows by `__path`, re-parse only the files that
actually changed, insert their rows — rather than rebuilding from source. A one-file edit in a
6000-concept bundle costs 6.9 ms against 3873 ms, and the write-then-query loop
(`readb set` followed by `readb query`) is the workflow readb is used in.

**The incremental path is guarded by a conservative fallback.** It applies only when the change is
provably local; anything that could make the cached database differ from a fresh load falls back to
a full rebuild. That covers: a column whose unified type would change under the lattice, a producer
key appearing or disappearing for a type, a type appearing or disappearing, any change in the
normalized-table-name collision map, a change to the `index.md`/`log.md` set, and a readb or duckdb
version change. To decide the first two exactly rather than guess, the cache stores per-(table,
column) **type evidence** — how many concepts contribute each lattice type — which is decremented
and incremented as files leave and enter, and the unified type recomputed from it.

The invariant, stated so it can be tested rather than asserted: **a cache-hit database answers every
query, and prints every `readb schema`, exactly as a freshly loaded one does.** It is not required to
be byte-identical, because the cache carries its own metadata tables that a cacheless load has no
reason to build.

**5. The cache file is immutable; updates are copy-apply-rename.** An update copies the current cache
(4.7 ms at 20 MB), applies the delta to the copy, and lands it with `os.replace`, which is atomic.
Readers never see a half-written database, concurrent readb processes never contend on a write lock,
and a crash mid-update leaves the previous cache intact. A cache hit opens the file **read-only**,
which also means a caller cannot accidentally persist a `CREATE TABLE` into it; temp tables still
work, and DuckDB permits many simultaneous readers.

**6. Failure is never fatal.** An unreadable, corrupt or version-mismatched cache is a miss. An
unwritable cache directory is a logged no-op. A query answers correctly in every case — the same
permissiveness the load path already promises for malformed markdown.

# Consequences

- A repeat query against an unchanged bundle costs about 80 ms end-to-end at any bundle size,
  essentially all of it process startup; a query after editing one file costs about 90 ms. That is
  the result [ADR 0005](0005-stay-on-python.md) counts on when it declines a rewrite.
- **A bundle in a repository nobody ran `readb init` in gets no speed-up.** This is the price of the
  consent rule, paid knowingly: the fix is one command, and the README and the skill should say so.
- readb gains no dependency on git, and behaves identically inside a repository, across several
  repositories, in a worktree, and in a directory that has never seen version control.
- The incremental path is the largest piece of machinery in the codebase, and its correctness rests
  on the fallback list above being complete. It is pinned by a property test that applies random
  edit sequences and compares the incremental database against a fresh load; a mismatch is a bug in
  the fallback list, and the test is written to find one.
- mtime is trusted for the *unchanged* verdict. A filesystem with coarse timestamps, or a tool that
  restores mtimes while changing content, could serve a stale answer. Git has the same blind spot
  for the same reason. `--no-cache` and `readb cache clear` are the escape hatches.
- mtime is *not* trusted for the changed verdict: a stat mismatch only nominates a file for a
  content check, so touching files never rewrites anything.
- **Cache files are created with `BLOCK_SIZE 16384` rather than DuckDB's default.** DuckDB's file
  format has a large fixed overhead — a 9-concept bundle materializes to 3.6 MB and the project's
  own 34-concept backlog to 4.9 MB at the default block size, because every column claims at least
  one block. At 16 KB blocks the backlog's cache is 1.5 MB, and nothing regresses at scale: a
  6000-concept cache is 22.4 MB against 22.0 MB, and its hit path is 3.96 ms against 4.89 ms. Small
  bundles are the common case, so the small-bundle cost is the one worth cutting.
- Cache size is one file per bundle: about 1.5 MB for a few dozen concepts, 22 MB at 6000.
- **The stat walk is the hit path's floor, and it is not the binding constraint.** At 6000 concepts a
  cache hit costs about 80 ms end-to-end, of which roughly 70 ms is Python process startup and 11 ms
  is the walk. Even at 20000 files the walk is 42 ms against a full load of some 13 seconds. Two
  caveats belong on the record: the rate assumes a warm inode cache, and a network filesystem makes
  per-file stat expensive — though there the cache wins by more, since a load opens and reads every
  file the walk merely stats. If a bundle ever grows large enough for the walk to dominate, the
  answer is a watcher, which this ADR and [ADR 0005](0005-stay-on-python.md) both decline today.

# Alternatives considered

**Key on the git commit hash, and apply what git reports as dirty.** The idea is sound — it is what
build tools do — and it was measured rather than dismissed. It is not adopted, for four reasons in
descending order of weight:

1. **It is not faster.** `git status --porcelain` costs 11.9 ms on a 6000-file repository against
   11.1 ms for readb's own `scandir` walk, and it spawns a process to do it. Git is fast because its
   index *is* a stat cache — it does exactly the work the manifest does.
2. **It has blind spots the manifest does not.** Git does not report ignored files unless asked, and
   a bundle may perfectly well contain a file someone gitignored; untracked files, submodules,
   several repositories under one bundle, and bundles outside any repository each need their own
   code path. Every one of those paths fails toward a **stale answer**, which is the failure mode
   this design most needs to avoid.
3. **It offers no correctness advantage.** Where git is content-exact — a file touched but not
   modified — hashing the suspect file gives the same answer for 0.0016 ms. Where git trusts stat,
   so does the manifest.
4. **It answers the wrong question.** Detection was never the expensive part; granularity was. Git
   would not have made the rebuild incremental on its own.

The one case git genuinely wins: a branch switch or `git stash` that rewrites many files' mtimes
while restoring identical content. The manifest then hashes every suspect — 106 ms at 6000 files —
where a HEAD hash would answer instantly. A bounded, rare cost, paid only in a git repository, and
not worth the four items above.

**All-or-nothing rebuild on any change.** The simpler design, and the one this ADR started as.
Rejected: editing one file in a 6000-concept bundle would cost 3873 ms, and edit-then-query is
readb's own daily workflow. Simplicity is not worth making the common case the slow one.

**Content-hash every file on every load.** Correct under every filesystem and needs no mtime trust.
Rejected as the default at 106 ms per invocation on a large bundle — an eightfold increase in the hit
path's cost to close a gap git does not close either. It remains the natural implementation of a
future `--verify` flag.

**Re-parse every suspect without confirming it first.** Simpler, and briefly adopted during design on
the reasoning that re-parsing one file is cheap anyway. Rejected once measured: confirmation is 12×
cheaper than re-parsing rather than comparable, so it pays for itself even on a single file, and
without it a mass mtime change turns into a full rebuild — the outcome this design most wants to
avoid.

**Confirm by comparing against the `__raw` text the cache already holds**, instead of storing a
digest. Exact, and needs no extra bytes, but it costs 0.79 ms per point lookup and ties change
detection to `__raw` being *stored* — which
`038-derive-text-columns` may stop doing. A 16-byte digest per file is 1% of the cache and depends
on nothing.

**Mutate the cache file in place instead of copy-apply-rename.** Saves a 4.7 ms copy and costs
single-writer locking, contention between concurrent readb processes, and a corrupt cache if a write
is interrupted. Not worth it at that price.

**Cache in a user-level directory (`~/.cache/readb`) for every bundle, no consent needed.** What most
CLI tools do, and it would make the speed-up universal instead of opt-in. Rejected because it makes
*reading* a directory write to the user's disk without anyone asking, which is exactly the property
that makes readb safe to point at someone else's files.

**Cache inside the bundle itself.** Rejected on ADR 0004's reasoning: the bundle is a publishable OKF
artifact and must not accumulate tool droppings.

**Have `readb init` add `.readb/cache/` to `.gitignore`.** Rejected: a tool that edits a user's
`.gitignore` is a tool that edits files it was not asked to edit, which is the habit this project is
built against. Documentation carries it instead.
