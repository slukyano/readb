---
type: Task
title: Benchmark v3 — re-measure every arm with the cache enabled
description: Re-run the full agent-efficiency matrix once the persistent index cache ships, and use it to measure the revised skill description after the fact.
status: Draft
priority: medium
tags:
- research
- benchmarks
- skill
created: 2026-08-22
---

Planned in the sprint-006 scope session. Two things this sprint changes invalidate the v2
numbers rather than extend them, so the honest answer is one full re-measure afterwards rather
than a targeted contrast during:

- **The cache.** [034-persistent-index-cache](034-persistent-index-cache.md) changes what a readb
  invocation costs in wall clock, and v2's per-invocation load time is paid per query. Every readb
  arm's timing — and the multi-query session question specifically, the one place readb *lost* wall
  clock at 2000 concepts — is measured against a load path that no longer exists.
- **The skill's `description`.** [033-skill-discovery-rate](033-skill-discovery-rate.md) changes the
  surface a runtime matches a task against before loading the skill body. v2 measured the old one:
  the skill was loaded on 37 of 78 runs, and readb was never invoked at all on 41.

## What this must not become

The rule carried from v1 and v2 holds: **a change to a shipped surface is measured after the
fact, never tuned until the benchmark improves.** 033's new description is frozen before the
first measured v3 run, exactly as `readb-nudged`'s sentence was in v2. If v3 says the change did
not move discovery, that is the result.

## Notes (to refine)

- Scope is the **full matrix**, not the skill arm alone: five arms, both models, all four corpora,
  the same 26-question battery, so v3 is comparable to v2 line for line.
- A cache-enabled run needs a decision about **cache warmth as a variable** — cold on first
  invocation, warm after — and the pre-registration has to fix whether the cache is primed before
  a run or left to warm inside it. v2 already sets a precedent: corpora were regenerated per
  repeat so no arm inherited a warm cache.
- Wall clock stops being a footnote if the cache lands: v2 demoted it because it varies with the
  machine, but the cache's whole claim is a wall-clock claim.
- Pre-registration first, as in v2 — arms, strata, endpoints and exclusion rules committed before
  the first measured run.
- Budget: v2's 783 runs billed $50.92 on the committed price tables.
