---
type: Task
title: Evaluate rewriting readb in Rust
description: Decide, on measured evidence, whether readb's core should move from Python to Rust — and what that would cost in public surface, distribution, and YAML semantics.
status: Done
priority: medium
tags:
- research
- architecture
- packaging
created: 2026-08-07
timestamp: '2026-08-23T18:00:00Z'
---

Raised by the maintainer 2026-08-07, while sprint-003 was designing release automation: if readb
is going to leave Python, automating a PyPI release pipeline is the wrong investment order. The
question deserves an answer on evidence rather than taste, and it is ADR-shaped either way.

## What a rewrite would buy

- **A single static binary** — no Python runtime, no `uv`/`pip` prerequisite; install by
  downloading a file, or via Homebrew/cargo.
- **Startup cost close to zero.** Measured 2026-08-07 on the project's own 34-file backlog
  bundle: `import duckdb` alone is ~120 ms, and an end-to-end `readb query` is ~120–250 ms. A
  Rust binary would plausibly land in the 5–20 ms range.
- **A faster load pass** on large bundles, where parsing and inserting thousands of concepts —
  not engine time — dominates.

## What it would cost

- **The Python API is a shipped public surface.** `readb.open(path) -> Database` is in 0.1.0 on
  PyPI. A rewrite either drops it or takes on PyO3 plus `maturin`/`cibuildwheel` matrix builds —
  *more* release machinery than the Python package needs, not less.
- **YAML semantics are defined by the parser.** readb's permissive-load contract is, in practice,
  "what PyYAML accepts". Rust's YAML ecosystem is thinner (`serde_yaml` is unmaintained;
  `saphyr`/`yaml-rust2` are the live options), so a rewrite silently redefines which files load —
  the one behavior the project has promised to keep lossless and forgiving.
- **Rebuild cost against a small but real codebase**: 1,572 lines of production Python across 9
  modules, pinned by 129 tests (1,501 lines) including the design brief's 12 acceptance criteria.
  Feasible — weeks, not months — but it freezes feature work right after the tool went public.
- DuckDB itself is not a blocker: `duckdb-rs` is actively maintained (948★, last push
  2026-08-04, checked 2026-08-07).

## Notes (to refine)

- **The driver has to be named before the decision.** Binary distribution and per-invocation
  latency are the only two candidates, and the latency case is weak on current evidence: ~0.1–0.2 s
  per call sits inside the noise of an agent turn measured in seconds.
- **Sequence behind [measure-agent-efficiency](024-measure-agent-efficiency.md)**: that task
  produces the load-pass numbers on large bundles that would make or break the performance
  argument. Deciding before it exists is deciding without data.
- **The persistent index cache is the cheaper lever** for repeat-invocation cost, and it is
  already the planned direction (the loader is the seam it wraps). Compare the two options on the
  same measurements.
- Consider the middle path explicitly: keep the Python package and add a Rust core behind PyO3
  only if the load pass proves to be the bottleneck.
- Outcome is an ADR — rewrite, hybrid, or explicitly stay on Python with the reasons recorded so
  the question stops recurring.

## Design

The evaluation is decided on measurement and existing evidence; no Rust prototype is built. A
prototype would price the rewrite's *upside* precisely, and the upside is not what is in doubt —
what the measurements below establish is that the upside lands somewhere the benchmark has already
shown does not matter. The deliverable is
[ADR 0005](../../docs/dev/adr/0005-stay-on-python.md), proposed in the design phase rather than
during implementation, because `034-persistent-index-cache`'s implementation is conditional on its
answer.

**Public-surface delta: none.** No CLI command, flag, output format, Python API name, on-disk path,
config key or packaged artifact changes. The task produces one ADR and this section.

### The measurements taken

All on the design branch, duckdb 1.5.4 / CPython 3.14.6 / macOS arm64, median of 5–7 runs of the
installed console script (not `uv run`, which adds its own wrapper cost).

Per-invocation floor, independent of bundle size:

| | ms |
| --- | --- |
| interpreter alone (`python -c pass`) | 23 |
| `readb --help` (click, no duckdb import) | 70 |
| `readb get` — the field editor, which never imports duckdb | 66 |
| `import duckdb` alone | 60 |

End-to-end `readb query`, by bundle size, before and after the fix in
[036-load-pandas-import-probe](036-load-pandas-import-probe.md):

| Concepts | As shipped | With `036-load-pandas-import-probe` | Cache hit (measured, `034-persistent-index-cache` prototype) |
| --- | --- | --- | --- |
| 34 (`backlog/`) | 150 ms | 114 ms | ~80 ms |
| 600 | 938 ms | 456 ms | ~80 ms |
| 2000 | 2903 ms | 1347 ms | ~80 ms |
| 6000 | 8751 ms | 3868 ms | ~90 ms |

The cache column is not a projection: reopening a materialized DuckDB file and querying it costs
**4.0 ms at every size measured**, and the staleness check that must precede it (a stat-only walk
of the tree) costs 2.1 ms at 600 files, 6.4 ms at 2000 and 20.3 ms at 6000. The rest is the
process floor.

### What the numbers decide

The two candidate drivers named when the task was raised were **binary distribution** and
**per-invocation latency**. Only the second is a performance argument, and it dissolves:

1. **The load pass is not slow because Python is slow.** Two thirds of it is a failed import
   (`036-load-pandas-import-probe`) — a defect, not a language property. Removing it is a 2.9×
   speed-up at every size measured, for a one-screen change.
2. **What remains of the load pass is what a cache removes**, and the cache is measured at 4 ms
   regardless of bundle size. After `036-load-pandas-import-probe` and `034-persistent-index-cache`,
   a repeat invocation costs about 80 ms.
3. **Of that 80 ms, roughly 70 ms is process startup** — the interpreter plus click plus
   `import duckdb`. That is the only part a Rust rewrite would still attack, and it would win
   perhaps 60 ms per invocation.
4. **Benchmark v2 measured what 60 ms is worth**: nothing. Agent cost tracks turns
   (`≈ $0.019/turn`), a turn is measured in seconds, and readb's cost advantage over an uncoached
   agent (0.72× Sonnet, 0.75× Haiku) came from turns saved, not milliseconds. No arm's cost moved
   with wall clock.

Binary distribution remains a real benefit, and it is the one the ADR does not dismiss — it is
weighed against a Python API that is already shipped in `0.1.0` on PyPI, and against the fact that
`uvx readb` and `gh skill install` already deliver readb without a manual install step. The
rewrite's cost side is unchanged from the task's original framing except that it grew: 1,717 lines
of production Python across 9 modules, pinned by 190 tests.

### Consequence for the rest of the sprint

`028-evaluate-rust-rewrite` answering "stay on Python" is what licenses `034-persistent-index-cache`
to be implemented in this sprint rather than merely designed. If the ADR were rejected,
`034-persistent-index-cache` would stay `Designed` and the sprint would deliver the decision,
`036-load-pandas-import-probe`, `033-skill-discovery-rate` and `032-unknown-table-error`.
