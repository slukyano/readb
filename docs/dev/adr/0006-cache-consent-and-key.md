---
type: ADR
title: 'The persistent cache writes only under an existing .readb/, is keyed on a path+size+mtime manifest, and is all-or-nothing'
status: Proposed
created: 2026-08-22
sprint: sprint-006
timestamp: '2026-08-22T00:00:00Z'
---

# Context

readb's hardest promise is that reading is inert: loading a bundle and running SQL never create or
modify any file. A persistent index cache — planned since the design brief, which left
`load_bundle` as the seam to wrap, and given a home by
[ADR 0004](0004-init-registry-discovery.md) — writes a file. That is a change to the promise, and
it needs stating as one rather than being folded in as an implementation detail.

Three things are being decided together, because each one's answer depends on the others: **when
readb may write a cache**, **what makes a cache valid**, and **how much of the bundle a stale
cache invalidates**.

The measurements that frame it (sprint-006 design branch, duckdb 1.5.4, CPython 3.14.6): reopening
a materialized DuckDB file and querying it costs 4.0 ms independent of bundle size, against a full
load of 384 ms at 600 concepts and 3873 ms at 6000 after the `036` fix. The staleness check — a
stat-only walk of the tree — costs 2.1 ms at 600 files and 20.3 ms at 6000. Materializing costs
42–163 ms and the file is 4.7–20.5 MB.

# Decision

**1. Consent. readb writes a cache only when a `.readb/` registry root already exists above the
bundle**, and never anywhere else. No registry means no cache and today's behaviour exactly. The
gesture that creates that directory is `readb init`, which ADR 0004 already established as the
user saying "this repository is readb's to work in". A registry-wide `cache = false` in
`config.toml`, a per-invocation `--no-cache`, and `readb.open(path, cache=False)` all switch it
off.

The read-only rule is restated, not weakened: **loading and querying never create or modify any
file in the bundle, and never any file at all outside a `.readb/` directory the user created.**

**2. Key. A cache is valid for exactly one manifest**: every file the loader's own walk sees,
recorded as bundle-relative path, size and `st_mtime_ns`, hashed together with the readb version,
the duckdb version, and the bundle's absolute path. The hash is carried in the cache filename, so
existence is validity and there is no second file to keep in sync. Writes land through `os.replace`
from a temp file in the same directory, which is atomic under concurrent readb processes.

**3. Granularity. A cache hit is all-or-nothing.** Any manifest difference rebuilds the whole
database. No incremental re-parse of changed files, no git-hash diffing.

**4. Failure is never fatal.** An unreadable, corrupt or version-mismatched cache is a miss. An
unwritable cache directory is a logged no-op. A query answers correctly in every case, which is the
same permissiveness the load path already promises for malformed markdown.

# Consequences

- A repeat query against an unchanged bundle costs about 80 ms end-to-end, essentially all of it
  process startup, at any bundle size. That is the result [ADR 0005](0005-stay-on-python.md) counts
  on when it declines a rewrite.
- **A bundle in a repository nobody ran `readb init` in gets no speed-up.** This is the price of
  the consent rule and it is paid knowingly: the fix is one command, and it should be said plainly
  in the README and the skill — `readb init` is what makes repeat queries fast on large bundles.
- `readb set` and `unset` invalidate for free, because they change the file's mtime. No write-path
  coupling to the cache exists, and the two paths stay independent.
- Cache size is bounded at one file per bundle; a rebuild deletes the previous revision's file.
  A 6000-concept bundle costs about 20 MB.
- mtime is trusted. A filesystem with coarse timestamps, or a tool that restores mtimes while
  changing content, could serve a stale answer. Nanosecond mtimes on the platforms readb targets
  make this remote, and the escape hatches (`--no-cache`, `readb cache clear`) exist for when it is
  not.
- Nothing about this decision assumes git, which keeps readb honest as a general-purpose tool over
  any OKF bundle.

# Alternatives considered

**Cache in a user-level directory (`~/.cache/readb`) for every bundle, no consent needed.** This is
what most CLI tools do, and it would make the speed-up universal instead of opt-in. Rejected
because it makes reading a bundle write to the user's disk without anyone asking, which is exactly
the property that makes readb safe to point at someone else's directory. The consent rule is worth
more than the convenience.

**Cache inside the bundle itself.** Rejected on ADR 0004's reasoning: the bundle is a publishable
OKF artifact and must not accumulate tool droppings.

**Key on content hashes instead of size+mtime.** Correct under every filesystem, and rejected on
cost: hashing 6000 files means reading all of them, which is most of the work the cache exists to
avoid. Size+mtime with nanosecond granularity is the standard build-system trade.

**Key on a git hash, diffing the working tree** (the design brief's sketch). Rejected: it assumes
git, and the incremental re-parse it enables is worth little — see below.

**Incremental re-parse of changed files only.** Rejected for this task: the column-type lattice
unifies across every concept of a type, so a single changed file can change a column's type and
force its table to be rebuilt regardless. The complexity buys speed only in the
one-file-changed-in-a-huge-bundle case, and an all-or-nothing miss there costs what today's every
load costs.
