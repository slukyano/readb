---
type: Sprint
title: Decide the language question, then make the load cheap
description: Answer the Rust question on the benchmark's evidence, build the persistent index cache behind the load seam, and fix the two agent-facing defects benchmark v2 surfaced.
tags:
- architecture
- performance
timestamp: '2026-08-23T18:00:00Z'
branch: sprint/006
created: '2026-08-22'
status: Done
tasks:
- 028-evaluate-rust-rewrite
- 036-load-pandas-import-probe
- 034-persistent-index-cache
- 033-skill-discovery-rate
- 032-unknown-table-error
- 040-hash-virtual-column
---

Sixth sprint under the [session/sprint workflow](../workflow.md), and the aftermath of the
benchmark line that ran through sprint-004 and sprint-005.

## Scope rationale

The scope is the entire medium-priority backlog, and it forms one arc: the benchmark produced the
evidence (`028-evaluate-rust-rewrite`), the defect list (`032-unknown-table-error`,
`033-skill-discovery-rate`), and the direction (`034-persistent-index-cache`).

`028-evaluate-rust-rewrite` has been deferred twice on purpose — sprint-003 raised it, sprint-004
was meant to feed it, and sprint-005 held it back so the argument would not ride on a benchmark. The
evidence now exists: cost tracks turns rather than language (readb at 0.72× Sonnet / 0.75× Haiku
against the uncoached baseline, and a coached shell pipeline at 0.75× / 0.69× — the two move
together under every subtraction rule), and repeat-invocation cost is dominated by re-loading the
bundle. That points at a cache rather than a rewrite, but the decision is recorded as an ADR either
way, so the question stops recurring.

`034-persistent-index-cache` is the consequence and the sprint's real build: the `.readb/` index
that [the design brief](../../docs/dev/design.md) left a seam for and [ADR
0004](../../docs/dev/adr/0004-init-registry-discovery.md) reserved a home for. It carries its own
ADR, because a cache writes and today's rule is absolute — loading and querying never create or
modify any file.

`032-unknown-table-error` and `033-skill-discovery-rate` are the two agent-facing defects benchmark
v2 measured, both small beside the decision.

## The dependency that sets the order

`028-evaluate-rust-rewrite`'s answer is `034-persistent-index-cache`'s premise. If the answer were
"rewrite in Rust", a Python cache is wasted work; if it is "stay on Python, the lever is the cache",
`034-persistent-index-cache` is the direct consequence and its ADR follows 028's.
`034-persistent-index-cache` is **designed** this sprint regardless, and **implemented** only if
`028-evaluate-rust-rewrite` keeps readb on Python — otherwise it stays `Designed` and the sprint
delivers the decision plus the two fixes.

## Task checklist

- [x] 028-evaluate-rust-rewrite — decide Python vs. Rust on the measured evidence; ADR either way;
      no product code
- [x] 036-load-pandas-import-probe — DuckDB probes for pandas twice per non-NULL bound value; the
      load runs ~2.9x slower than it should at every bundle size measured
- [x] 034-persistent-index-cache — the `.readb/` index behind `load_bundle`, plus the ADR on how a
      read-only tool may write a cache
- [x] 033-skill-discovery-rate — the shipped skill's `description` surface; the skill was loaded on
      37 of 78 runs and readb never invoked at all on 41
- [x] 032-unknown-table-error — a mistyped table names the bundle's tables and `readb schema`
      instead of DuckDB's `duckdb_indexes`
- [x] 040-hash-virtual-column — `__hash`, the hex SHA-256 of the file's bytes, in every table that
      carries `__raw`; the cache consumes the same value

Design order: `028-evaluate-rust-rewrite` → `036-load-pandas-import-probe` →
`034-persistent-index-cache` → `033-skill-discovery-rate` → `032-unknown-table-error`.
Implementation order: **`036-load-pandas-import-probe` first**, then `032-unknown-table-error`,
`033-skill-discovery-rate`, and `034-persistent-index-cache` as the long pole.
`036-load-pandas-import-probe` precedes `034-persistent-index-cache` because a cache benchmarked
against a load pass that is itself three times slower than it should be proves nothing.

## Scope decisions taken at approval

- **`029-field-editor-remaining-edges` stays out.** Its three items are decisions rather than
  patches, and design attention is this sprint's scarce resource.
- **`033-skill-discovery-rate` ships without a measured re-run inside this sprint.** The
  after-the-fact measurement it requires is a full re-measure of every arm once the cache lands,
  held by [`035-benchmark-v3-cached`](../tasks/035-benchmark-v3-cached.md). The revised description
  is frozen before that run; it is never tuned against the benchmark.

- **`036-load-pandas-import-probe` was added to scope mid-design**, found while measuring the load
  pass for `028-evaluate-rust-rewrite`. It is the only high-priority task in the backlog and it
  gates `034-persistent-index-cache`'s measurement.

## Design phase (approved 2026-08-23)

- [x] `028-evaluate-rust-rewrite` — decided on measurement; proposes [ADR
  0005](../../docs/dev/adr/0005-stay-on-python.md)
- [x] `036-load-pandas-import-probe` — the guard, its stated thread-safety limitation, and a
  counting regression test
- [x] `034-persistent-index-cache` — all-or-nothing consent-gated cache; proposes [ADR
  0006](../../docs/dev/adr/0006-cache-consent-and-key.md)
- [x] `033-skill-discovery-rate` — the frozen description text and the rule it is held to
- [x] `032-unknown-table-error` — the message, raised where the schema is known
- [x] `040-hash-virtual-column` — added to scope during design; proposes
      [ADR 0007](../../docs/dev/adr/0007-hash-virtual-column.md)

## Open questions

_(none — every deferral has a named home: `041-empty-struct-crashes-the-load` holds the
permissive-load defect the adversarial review found in code that predates this sprint,
`037-field-editor-list-values` holds the field editor's
inability to change a list, `038-derive-text-columns` holds the duplicated text storage the cache
exposed, `039-git-aware-change-detection` holds change detection for filesystems where stat is
expensive, and `035-benchmark-v3-cached` holds the re-measure the cache and the new skill
description now owe.)_

## Sprint summary

Six tasks, all delivered, and the sprint's own measurements changed two of its designs while it ran.

`028-evaluate-rust-rewrite` was answered by measuring rather than prototyping, and the measuring
found `036-load-pandas-import-probe` immediately: two thirds of every load was DuckDB re-attempting
an import of pandas, once per non-NULL bound value, with Python never caching the failure. That is
a defect rather than a property of the language, and removing it made the load ~2.9x faster at every
bundle size. What remained was what a cache removes, and what remains after *that* is process
startup — which benchmark v2 already priced at nothing. ADR 0005 records the decision with the
whole trade, and names the two things that would reopen it: a native install story `uvx` cannot
serve, or a caller that pays the ~70 ms floor often enough for it to add up.

`034-persistent-index-cache` is the sprint's build. It began as an all-or-nothing cache and became
an incremental one during design review, because a full rebuild on every single-file edit would
have made the common workflow the slow one. Two more decisions came out of measuring: git is not
used for change detection (`git status` is no faster than the walk and has blind spots that fail
toward a stale answer), and a file whose timestamp moved is confirmed by content hash before it is
believed changed, which is 12x cheaper than re-parsing and keeps a mass mtime change from rewriting
anything.

`040-hash-virtual-column` joined scope during design: the cache needed a per-file digest, and
exposing it as `__hash` turned duplicate detection and change tracking into queries.

Fourteen defects were found and fixed before the merge, and only three of them by the tests written
alongside the code. Two came from driving the built artifact and re-reading the diff. The other nine
came from two independent reviews with no implementation context — one over the whole diff, one an
adversarial differential fuzzer aimed at the cache's equivalence claim.

The most serious was the fuzzer's: `unify` is commutative but **not** associative, so a column
carrying more than one lattice type has a type that depends on the order its values were folded in.
A fresh load folds in path order; evidence counts cannot reproduce that order, and the cache was
comparing its own recomputation against itself. Such a column now forces a full rebuild. The second
was routing: two raw types normalizing to one table name are told apart by a suffix, and which of
them owns the un-suffixed name depends on which document comes first — so a delete or a rename could
silently make a legitimate query return the other type's rows. A bundle with a collision is now
never updated incrementally.

The review also found that the incremental update built its result at its final, key-named path with
no atomic rename, so a crash or a concurrent reader could see the previous contents under the new
key — permanently. It now stages and renames like the full write does.

One finding is **not** this sprint's and is not fixed: four frontmatter shapes, `flag: {}` among
them, make a whole bundle unqueryable rather than skipping one file, which breaks the permissive-load
promise outright. It reproduces identically on pre-sprint `main`, and is held by
[`041-empty-struct-crashes-the-load`](../tasks/041-empty-struct-crashes-the-load.md) (high).

## Session log

* **2026-08-23** — Two independent reviews ran against the finished branch and returned twelve
  findings between them; eleven were fixed and pinned by regression tests, and the twelfth predates
  the sprint and is now `041-empty-struct-crashes-the-load`.
* **2026-08-23** — Implemented all six tasks, ran the gates, and closed the sprint out on the
  branch. `040-hash-virtual-column` was added to scope during design; `038-derive-text-columns` and
  `039-git-aware-change-detection` were drafted out of it.
* **2026-08-23** — Design approved. ADRs 0005, 0006 and 0007 `Accepted`; six tasks `Designed`;
  sprint `Implementing`; design merge to `main`. `040-hash-virtual-column` joined scope during the
  phase; `038-derive-text-columns` and `039-git-aware-change-detection` were drafted out of it and
  stay in the backlog.
* **2026-08-22** — Design phase: all five designs written, ADRs 0005 and 0006 proposed. Load-pass
  and cache-prototype measurements taken on the branch (a cache hit is 4 ms at every bundle size).
* **2026-08-22** — `036-load-pandas-import-probe` added to scope during 028's design measurements
  (approved in session); `037-field-editor-list-values` drafted for the dogfooding gap that
  hand-editing this file exposed.
* **2026-08-22** — Scope approved: four tasks, branch `sprint/006`. `034-persistent-index-cache`
  drafted during the scoping session (no task held the caching work before);
  `035-benchmark-v3-cached` drafted to hold the post-cache re-measure.
  `029-field-editor-remaining-edges` considered and left out.
