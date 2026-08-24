---
type: Sprint
title: Decide the language question, then make the load cheap
description: Answer the Rust question on the benchmark's evidence, build the persistent index cache behind the load seam, and fix the two agent-facing defects benchmark v2 surfaced.
tags:
- architecture
- performance
timestamp: '2026-08-23T12:00:00Z'
branch: sprint/006
created: '2026-08-22'
status: Implementing
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

- [ ] 028-evaluate-rust-rewrite — decide Python vs. Rust on the measured evidence; ADR either way;
      no product code
- [ ] 036-load-pandas-import-probe — DuckDB probes for pandas twice per non-NULL bound value; the
      load runs ~2.9x slower than it should at every bundle size measured
- [ ] 034-persistent-index-cache — the `.readb/` index behind `load_bundle`, plus the ADR on how a
      read-only tool may write a cache
- [ ] 033-skill-discovery-rate — the shipped skill's `description` surface; the skill was loaded on
      37 of 78 runs and readb never invoked at all on 41
- [ ] 032-unknown-table-error — a mistyped table names the bundle's tables and `readb schema`
      instead of DuckDB's `duckdb_indexes`
- [ ] 040-hash-virtual-column — `__hash`, the hex SHA-256 of the file's bytes, in every table that
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

_(none yet)_

## Session log

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
