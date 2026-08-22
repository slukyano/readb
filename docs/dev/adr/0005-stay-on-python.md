---
type: ADR
title: 'readb stays a Python package; per-invocation cost is addressed by fixing the load pass and caching it, not by a rewrite'
status: Proposed
created: 2026-08-22
sprint: sprint-006
timestamp: '2026-08-22T00:00:00Z'
---

# Context

Whether readb's core should move from Python to Rust was raised while sprint-003 was designing
release automation, on the reasoning that automating a PyPI pipeline is the wrong investment if
the package is about to stop being a Python package. It was deferred twice on purpose — the
argument needed measurement rather than taste, and the measurements it needed did not exist.

Two candidate drivers were named at the time: **a single static binary** with no Python runtime
prerequisite, and **per-invocation latency**, since readb re-reads and re-parses the whole bundle
on every call.

Two bodies of evidence now exist.

**What an agent's cost actually tracks.** Benchmarks
[v1](../research/agent-efficiency.md) and [v2](../research/agent-efficiency-v2.md) measured one
agent answering pre-registered questions over OKF bundles, 783 runs in v2 across two models and
four corpora. Cost tracks **turns** — roughly $0.019 per turn — and readb's advantage over an
uncoached agent (0.72× on Sonnet, 0.75× on Haiku, 12–15 accuracy points) came from turns saved.
No arm's billed cost moved with wall clock, because an agent turn is measured in seconds and
billed in tokens.

**Where readb's own time goes.** Measured on the sprint-006 design branch (duckdb 1.5.4, CPython
3.14.6, macOS arm64, installed console script, median of 5–7 runs):

| Concepts | As shipped | With the `036` fix | On a cache hit |
| --- | --- | --- | --- |
| 34 | 150 ms | 114 ms | ~80 ms |
| 600 | 938 ms | 456 ms | ~80 ms |
| 2000 | 2903 ms | 1347 ms | ~80 ms |
| 6000 | 8751 ms | 3868 ms | ~90 ms |

Three facts sit behind that table:

1. **Two thirds of the load pass is a failed import.** DuckDB's Python client attempts
   `import pandas` twice per non-NULL bound value; Python never caches a failed import, so each
   attempt walks `sys.path` again. Removing it is a 2.9× speed-up at every bundle size measured,
   for a one-screen change. This is a defect, not a property of the language.
2. **What remains of the load is what a cache removes.** Reopening a materialized DuckDB file and
   querying it costs 4.0 ms independent of bundle size; the staleness check before it costs
   2.1–20.3 ms for 600–6000 files.
3. **The residue is process startup** — about 70 ms, of which the interpreter is 23 ms and
   `import duckdb` is the largest single component.

# Decision

**readb stays a Python package.** Neither a full Rust rewrite nor a PyO3 hybrid core is adopted.
Per-invocation cost is addressed by fixing the load pass and caching it — the two levers measured
above — and the roughly 70 ms process floor is accepted as it stands.

The performance case is settled by measurement: after those two changes a repeat invocation costs
about 80 ms, of which a rewrite could recover perhaps 60 ms, and 60 ms is worth nothing in the only
cost model that has been measured for readb's actual user.

The distribution case is real but not decisive. A single static binary is genuinely simpler to
install than a Python package — but `uvx readb` and `gh skill install` already deliver readb
without a manual install step, and `readb.open(path) -> Database` is a shipped public surface in
`0.1.0` on PyPI. A rewrite either drops that API or takes on PyO3 plus `maturin`/`cibuildwheel`
matrix builds, which is *more* release machinery than the Python package needs, not less.

A rewrite would also silently redefine which files load. readb's permissive-load contract is in
practice "what PyYAML accepts"; Rust's YAML ecosystem is thinner (`serde_yaml` unmaintained,
`saphyr`/`yaml-rust2` the live options, checked 2026-08-07), and losslessness under malformed
input is the behaviour this project has promised hardest.

**What would reopen this.** A measured use case where the process floor is paid often enough to
matter — an interactive or looping caller making thousands of invocations, where 60 ms each is a
real number — or a distribution requirement that `uvx` and `gh skill` cannot serve. Absent one of
those, the question is answered and does not need re-litigating.

# Consequences

- `034-persistent-index-cache` is licensed to be implemented rather than merely designed; it is now
  the project's performance lever, and this ADR is the reason it is the *only* one being funded.
- The PyPI release machinery built in sprint-003 keeps its investment; nothing is stranded.
- The ~70 ms floor is a stated, accepted characteristic of readb rather than an open defect. It
  should be quoted honestly in any performance claim.
- `import duckdb` dominates that floor and only the query path needs it. The field editor already
  avoids it (`readb get` costs 66 ms against `readb --help` at 70 ms), so no further work is
  implied here — but the floor is the thing to attack if it is ever attacked again, not the
  language.

# Alternatives considered

**Full Rust rewrite.** Rejected: 1,717 lines of production Python pinned by 190 tests would be
rebuilt to recover 60 ms per invocation that the cost model says is worth nothing, at the price of
the shipped Python API and the permissive-load contract.

**PyO3 hybrid — keep the package, move the load pass to Rust.** Rejected on the same evidence and
one extra count: it targets the load pass specifically, and after `036` and `034` the load pass is
either 4 ms (hit) or a cost paid once (miss). It would add a compiled-wheel matrix to a project
whose release story currently fits in one pure-Python artifact.

**Build a Rust prototype before deciding.** Rejected: a prototype prices the upside precisely, and
the upside is not what is in doubt. The measurements above locate it below the noise floor of the
only workload readb has been benchmarked against.
