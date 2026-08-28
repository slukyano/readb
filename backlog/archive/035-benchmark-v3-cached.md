---
type: Task
title: Benchmark v3 — re-measure every arm with the cache enabled
description: Re-run the full agent-efficiency matrix once the persistent index cache ships, and use it to measure the revised skill description after the fact.
status: Done
priority: medium
tags:
- research
- benchmarks
- skill
created: 2026-08-22
timestamp: '2026-08-24T04:00:00Z'
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

## Design

v3 answers two questions v2 could not, and re-establishes the rest as a comparison basis:

1. **Does the cache change what an agent costs?** v2 measured a load path that no longer exists,
   and the cache's whole claim is a wall-clock claim — the one endpoint v2 demoted to a footnote.
2. **Did the skill's new `description` move discovery?** v2 measured the old wording: the skill was
   loaded on 37 of 78 runs, and readb was never invoked at all on 41.

### Arms — five, one of them new

| Arm | Preamble | `PATH` | Bundle state |
| --- | --- | --- | --- |
| `baseline` | orientation only | shims, no readb | no registry |
| `shell-coached` | orientation + a worked recipe | shims, no readb | no registry |
| `readb-bare` | orientation + readb syntax (v1's text, unchanged) | + readb | **no registry: no cache** |
| `readb-cached` | identical to `readb-bare`, word for word | + readb | **`readb init` run, cache primed** |
| `readb-skill` | orientation only; the shipped plugin loaded | + readb + uv | `readb init` run, cache primed |

`readb-cached` differs from `readb-bare` by **one thing that is not prompt text**: whether the
bundle has a `.readb/` registry. That isolates the cache exactly, and it is the only honest way to
price a change that never touches what the agent is told.

`readb-nudged` is **dropped**. v2 ran it, found it moved readb usage without moving any cost ratio
and roughly doubled failed readb calls, and that result stands; re-running it would spend a fifth of
the budget re-confirming a published negative. Its absence is a deviation from v2's arm set and is
reported as one.

### The cache warmth question, decided in advance

A cache is primed by one `readb query` before the agent starts, and the priming call is **not**
counted in the arm's cost. The claim being tested is about repeat invocation — an agent working in a
repository someone already uses readb in — not about first contact. The cold path is a known
quantity already: it is `readb-bare` plus the one-time write, both measured directly in sprint-006
and reported in the write-up rather than re-derived from agent runs.

Corpora are still regenerated per repeat, so no arm inherits another's filesystem state; priming
happens after generation, per cell.

### Endpoints — three, declared before the first measured run

| id | Contrast | Statistic |
| --- | --- | --- |
| **E1** | billed cost, `readb-cached` vs `readb-bare`, backlog stratum, Sonnet | paired signed-rank by question |
| **E2** | skill invocation rate, `readb-skill`, against v2's recorded 37/78 | two-proportion test |
| **E3** | billed cost, `readb-cached` vs `shell-coached`, join stratum, Sonnet | paired signed-rank by question |

Holm-corrected across the three. Everything else — accuracy, turns, wall clock, tool-choice
matrices, per-model tables — is descriptive and said to be descriptive.

**E1 is expected to come back at parity or near it**, and that is a real result rather than a
disappointment: agent cost tracks turns, and the cache changes seconds rather than turns. Publishing
that is the point of measuring instead of asserting. Wall clock, demoted in v2, returns as a
declared secondary for `readb-cached` vs `readb-bare` only, where the machine is the same and the
contrast is within a repeat.

### Budget and matrix

v2 was 783 runs for $50.92. v3 drops one arm and adds one, so the shape is unchanged: **Sonnet five
arms, Haiku four (no skill arm), three repeats, four corpora, 26 questions**, plus floors. Expect
the same order of magnitude — **roughly $50–60**, priced from the tables committed with the
pre-registration on the day it lands.

### What this must not become

The rule v1 and v2 were held to holds here: **a change to a shipped surface is measured after the
fact, never tuned until the benchmark improves.** The skill `description` shipped in sprint-006 is
frozen and is measured as it stands. If E2 says discovery did not move, the hypothesis behind that
wording was wrong and the write-up says so.

### Implementation notes

The harness changes landed before the pre-registration was committed, and the pre-registration
before the first measured run — the order the rule requires. `readb-cached` is asserted equal to
`readb-bare` field by field except for the corpus state, and the priming call's position before the
measured invocation is asserted from the source, so neither can drift into something else quietly.

The analysis gained E2 as a two-proportion test against v2's recorded 37/78, and lost v2's nudge
contrast along with the arm. Wall clock returns for the `readb-cached` vs `readb-bare` contrast
only.

### Deliverables

- A pre-registration concept in `docs/dev/research/`, committed **before the first measured run**,
  carrying arms, corpora, battery, strata, endpoints, exclusion rules and price tables.
- Harness changes: the `readb-cached` arm, registry setup and priming per cell, wall clock restored
  as a declared secondary, and the `readb-nudged` arm removed.
- A `Research` concept reporting the result, whatever it is.

### Public-surface delta

**None.** Everything here is development material under `benchmarks/` and `docs/dev/research/`;
no CLI command, flag, output format, Python API name, on-disk path or packaged artifact changes.
