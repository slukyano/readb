---
type: Research
title: Does a warm cache change what an agent costs, and did a rewritten skill description get found?
description: A five-arm, two-model benchmark isolating readb's persistent index cache in an arm of its own, and measuring a revised skill description against the rate v2 recorded.
tags:
- benchmarks
- agents
created: 2026-08-23
timestamp: '2026-08-23T00:00:00Z'
---

Produced by the backlog task `035-benchmark-v3-cached` (sprint-007), and the direct follow-on from
[v2](agent-efficiency-v2.md). Everything below was fixed before the first measured run and is
recorded in [the pre-registration](agent-efficiency-v3-preregistration.md).

**The numbers describe two models, one agent runtime, four synthetic corpora and one battery, at
three repeats per cell.** Nothing here supports a claim beyond that.

# Why there is a v3

Two shipped surfaces changed in sprint-006 on reasoning rather than evidence, and v2's numbers
describe a load path that no longer exists:

- **The persistent index cache.** Its claim is a wall-clock claim, and wall clock is precisely what
  v2 demoted to a footnote for being machine-dependent.
- **The skill's `description`.** v2 measured the old wording, on which the skill was loaded in 37 of
  78 runs and readb was never invoked at all in 41.

# Method

Corpora, battery and strata are v2's — four corpora (`ops` 600 concepts messy, `ops-malformed` 612,
`ops-tidy` 600 as the sweep control, `backlog` 192) and the same 26 questions across five strata —
so the two batteries stay comparable on those axes. What differs is listed in full below, including
the differences that were not intended as treatments, because E2 compares a rate across batteries
and every uncontrolled difference is a rival explanation for a move in it.

## One arm added, to price the cache

| Arm | Preamble | `PATH` | Bundle state |
| --- | --- | --- | --- |
| `baseline` | orientation only | shims, no readb | no registry |
| `shell-coached` | orientation + a worked recipe per corpus family | shims, no readb | no registry |
| `readb-bare` | orientation + readb syntax | + readb | no registry: no cache |
| `readb-cached` | **identical to `readb-bare`, word for word** | + readb | `readb init` run, cache primed |
| `readb-skill` | orientation only; the shipped plugin loaded | + readb + uv | `readb init` run, cache primed |

`readb-cached` differs from `readb-bare` by one thing that is **not prompt text**: whether the
corpus is a readb registry with a warm cache. A harness test asserts every other field of the two
arms is equal, so the contrast cannot quietly become something else. The priming query runs after
the corpus is copied and before the agent starts, and is **not charged** to the arm — a second test
asserts that ordering from the source.

That is deliberate about what is being measured. The claim under test is repeat invocation — an
agent working in a repository someone already uses readb in. The cold path was measured directly
while building the cache and is reported from those measurements rather than re-derived from agent
runs.

## One arm dropped

`readb-nudged` is gone. v2 ran it, found it moved readb usage without moving any cost ratio and
roughly doubled failed readb calls, and published that. Re-running it would have spent a fifth of
this battery re-confirming a negative. **This is a deviation from v2's arm set**, and the rule the
arm existed to enforce still governs the harness: prompt text is never adjusted because an agent
chose the "wrong" tool.

## Endpoints — three, declared in advance

| id | Contrast | Statistic |
| --- | --- | --- |
| **E1** | billed cost, `readb-cached` vs `readb-bare`, backlog stratum, Sonnet | paired signed-rank by question |
| **E2** | skill invocation rate against v2's 37/78 | two-proportion test |
| **E3** | billed cost, `readb-cached` vs `shell-coached`, join stratum, Sonnet | paired signed-rank by question |

**E1's null result was predicted in the pre-registration**: agent cost tracks turns, and a cache
changes seconds rather than turns. Wall clock returns as a **declared secondary** for E1's contrast
alone — the one place two arms share a machine, a repeat and a corpus, which is what made wall clock
untrustworthy in v2 and trustworthy here.

## What differs between v2 and v3, in full

Two intended changes, and four that came along with them:

| Difference | Intended? | Bears on |
| --- | --- | --- |
| `readb-cached` added | yes | E1, E3 |
| `readb-nudged` dropped | yes | comparability of the arm set |
| `readb-skill`'s corpus is now a primed registry too | **no** — a consequence of the arm design | **E2** |
| The skill's *body* changed in sprint-006: a `__hash` row and a paragraph about `readb init` | **no** | **E2** |
| The agent runtime moved between batteries | **no** | everything, weakly |
| Arms run in a fixed order, so `readb-cached` always follows `readb-bare` | pre-existing | the wall-clock secondary |

The last one is why the wall-clock secondary cannot be read as the cache's effect: v2's uncached
`readb-bare`/`readb-nudged` pair, adjacent in exactly the same way, shows the later arm ~6% faster
on Sonnet with no treatment at all.

<!-- RESULTS PENDING: this document is not complete until the sections below are written from the
     measured runs. Do not publish or cite it in this state. -->

# Results

_To be written from the measured matrix._
