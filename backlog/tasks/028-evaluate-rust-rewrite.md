---
type: Task
title: Evaluate rewriting readb in Rust
description: Decide, on measured evidence, whether readb's core should move from Python to Rust — and what that would cost in public surface, distribution, and YAML semantics.
status: Draft
priority: medium
tags:
- research
- architecture
- packaging
created: 2026-08-07
timestamp: '2026-08-07T00:00:00Z'
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
