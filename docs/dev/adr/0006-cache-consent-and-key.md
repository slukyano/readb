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

| Detecting change | 600 | 2000 | 6000 |
| --- | --- | --- | --- |
| `os.scandir` walk collecting size + mtime | 1.1 ms | 3.1 ms | 11.1 ms |
| `pathlib.rglob` + `stat()` (the naive version) | 1.7 ms | 5.2 ms | 17.7 ms |
| `git status --porcelain` (clean tree) | — | — | 11.9 ms |
| `git status --porcelain --ignored` | — | — | 12.3 ms |
| `git rev-parse HEAD` | — | — | 4.0 ms |
| `git ls-files` | — | — | 6.1 ms |
| Read + content-hash **every** file | 8.2 ms | — | 106.5 ms |
| Compare **one** suspect file against the `__raw` already in the cache | — | — | 0.79 ms |
| Compare **twenty** suspects the same way | — | — | 3.4 ms |

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

**2. Detection: a per-file stat manifest, confirmed against the text the cache already holds. No
git, and no stored hashes.**

The manifest is built by an `os.scandir` walk that mirrors the loader's own walk, recording for each
file its bundle-relative POSIX path, **that file's own `st_size`**, and its `st_mtime_ns`. No
directory is ever sized — a directory's size is not defined cheaply on any filesystem, and nothing
here needs it.

A file whose size and mtime match its manifest entry is unchanged. A file whose stat differs is
**compared before being believed** — and the comparison needs no stored digest, because the cache
already contains every concept's complete file text in the `__raw` virtual column. Reading the
suspect and comparing it to its `__raw` costs 0.79 ms for one file and 3.4 ms for twenty, and it is
*exact* rather than probabilistic. A suspect with no `__raw` in the cache — a file that failed to
parse and was skipped — is simply re-read. Files present in one set and not the other are additions
and deletions.

Storing a hash per file would have been affordable rather than wrong (16 bytes each, 256 KB per 6000
files, about 1% of the cache), but it is unnecessary weight next to a copy of the text itself.

The manifest is hashed together with the readb version and the duckdb version to form the cache
identity, which is carried in the cache's filename so a hit can be recognized without opening
anything.

**3. Granularity: incremental.** A change set of added, deleted and modified files is applied to the
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

**4. The cache file is immutable; updates are copy-apply-rename.** An update copies the current cache
(4.7 ms at 20 MB), applies the delta to the copy, and lands it with `os.replace`, which is atomic.
Readers never see a half-written database, concurrent readb processes never contend on a write lock,
and a crash mid-update leaves the previous cache intact. A cache hit opens the file **read-only**,
which also means a caller cannot accidentally persist a `CREATE TABLE` into it; temp tables still
work, and DuckDB permits many simultaneous readers.

**5. Failure is never fatal.** An unreadable, corrupt or version-mismatched cache is a miss. An
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
- **Cache files are created with `BLOCK_SIZE 16384` rather than DuckDB's default.** DuckDB's file
  format has a large fixed overhead — a 9-concept bundle materializes to 3.6 MB and the project's
  own 34-concept backlog to 4.9 MB at the default block size, because every column claims at least
  one block. At 16 KB blocks the backlog's cache is 1.5 MB, and nothing regresses at scale: a
  6000-concept cache is 22.4 MB against 22.0 MB, and its hit path is 3.96 ms against 4.89 ms. Small
  bundles are the common case, so the small-bundle cost is the one worth cutting.
- Cache size is one file per bundle: about 1.5 MB for a few dozen concepts, 22 MB at 6000.

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
Rejected as the default at 106 ms per invocation on a large bundle — an eightfold increase in the
hit path's cost to close a gap git does not close either. It remains the natural implementation of a
future `--verify` flag.

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
