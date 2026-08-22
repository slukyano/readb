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
