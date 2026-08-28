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

# Results

**732 runs on 2026-08-24** — 390 Sonnet, 312 Haiku, 30 floors. **$48.18 billed** by the committed
price tables, which is the basis of every figure below. **One run was excluded**, a `baseline` run
that hit an API 529. No PATH leak, no context compaction, no permission denial, and all 701 battery
runs produced an `ANSWER` line that parsed.

## The three endpoints

| id | Contrast | Effect | p | Holm p |
| --- | --- | --- | --- | --- |
| **E1** | billed cost, `readb-cached` vs `readb-bare`, backlog, Sonnet | 1.00x [0.98–1.07] | 0.5469 | 1.0000 |
| **E2** | skill invocation rate vs v2's 37/78 | 44/78 = 56% against 47% | 0.3363 | 1.0000 |
| **E3** | billed cost, `readb-cached` vs `shell-coached`, join, Sonnet | 1.04x [0.71–1.34] | 0.9453 | 1.0000 |

**None reaches significance, and E1's null was predicted in advance.** A cache changes seconds and
an agent is billed for tokens, so 1.00x is the result the pre-registration said to expect. Recording
that prediction beforehand is what makes it a result rather than an excuse.

## What the numbers say

**1. The cache costs an agent nothing, and saves it nothing.** E1 is 1.00x on a tight interval —
the tightest of the three, because the two arms differ in nothing an agent can see. Turn counts are
identical at a median of 4. Whatever the cache is worth, it is not worth money here.

Medians throughout; the distributions are long-tailed.

| Sonnet 5 | exact | billed (median) | ingested (median) | turns |
| --- | --- | --- | --- | --- |
| `baseline` | 88% | $0.0969 | 12,277 | 6.0 |
| `shell-coached` | 96% | $0.0667 | 9,819 | 3.0 |
| `readb-bare` | 100% | $0.0688 | 10,285 | 4.0 |
| `readb-cached` | 99% | $0.0688 | 10,314 | 4.0 |
| `readb-skill` | 95% | $0.0800 | 12,377 | 5.0 |

| Haiku 4.5 | exact | billed (median) | ingested (median) | turns |
| --- | --- | --- | --- | --- |
| `baseline` | 77% | $0.0520 | 11,702 | 9.0 |
| `shell-coached` | 92% | $0.0307 | 8,372 | 4.0 |
| `readb-bare` | 94% | $0.0318 | 8,628 | 4.0 |
| `readb-cached` | 92% | $0.0307 | 8,558 | 4.0 |

**2. Against an uncoached agent, structure still wins — by the same margin it did in v2.** Paired by
question against `baseline`: on Sonnet `readb-cached` is 0.68x [0.55–0.90] and `shell-coached`
0.67x [0.60–0.79]; on Haiku 0.69x [0.53–0.83] and 0.71x [0.50–0.84]. Accuracy rises 11 points on
Sonnet and 15 on Haiku. This replicates v2 on a battery whose readb arms now run different code.

**3. readb still does not beat a competently coached shell.** E3 is 1.04x. Two batteries have now
asked that question and neither answers yes.

**4. This benchmark cannot resolve the cache's wall-clock effect.** The measured contrast is 0.89x
on E1's stratum — but arms run in a fixed order and `readb-cached` always runs immediately after
`readb-bare`, and v2's uncached `readb-bare`/`readb-nudged` pair, adjacent in exactly the same way,
shows **0.94x favouring the later arm with no treatment at all**. Roughly half the observed effect
is explained by running second, and the design cannot separate the halves.

What the cache is actually worth was measured directly on the same corpora, without an agent:

| corpus | files | `--no-cache` | cache hit | saved per invocation |
| --- | --- | --- | --- | --- |
| `backlog` | 193 | 0.528 s | 0.119 s | **0.410 s** |
| `ops` | 601 | 0.842 s | 0.118 s | **0.724 s** |

An agent made a mean of 2.88 readb invocations per backlog run, so the cache's ceiling is
2.88 x 0.41 s = **1.18 s of a 9.98 s run, about 12%** — real, and smaller than the noise this
instrument can see. A wall-clock claim for the cache should cite the table above, not this battery.

**5. Skill discovery moved, and the move is not significant.** 44 of 78 runs invoked the skill
against v2's 37 of 78 (56% against 47%, Fisher p = 0.34), and readb went unused in 34 runs against
v2's 41. The direction is the one the rewrite intended and the evidence does not establish it.

**E2 cannot attribute even that much to the description.** Three things besides the wording differ
between the batteries: v3's skill arm also runs against a primed cache, the skill's *body* changed
in sprint-006, and the agent runtime moved. E2 is reported as declared and read as an observation.

# What this supports, and what it does not

**Supported.** On these corpora and this battery, at two models: an agent given readb answers for
**0.68x the money on Sonnet and 0.69x on Haiku** against an uncoached agent, with 11 to 15 points
more accuracy. The cache changes an agent's cost by nothing measurable.

**Not supported.** That the cache makes an agent faster in any way this experiment can see. Its
per-invocation saving is real and directly measured; its effect on a run is inside the ordering
artefact.

**Not supported.** That readb beats a competently coached shell pipeline. Third battery, same
answer.

**Not supported.** That the rewritten skill description improved discovery. The rate moved the right
way, the test does not resolve it, and three uncontrolled differences sit between the batteries.

# Deviations from the pre-registration

- **`readb-nudged` was dropped**, as declared in the pre-registration itself.
- **The wall-clock secondary was computed over every question and both models** in a first draft of
  the analysis, where the design scopes it to E1's stratum and model. Corrected before any number
  was published; an independent review of the instrument found it.
- **E2 was Holm-corrected as a family of one and tested by normal approximation** in that same
  draft. It is now in the declared family of three and tested exactly. Both defects would have made
  a null look stronger than it is.

# Limitations

1. **Arm order is fixed**, so any wall-clock contrast between adjacent arms carries a ~6% artefact.
   Rotating arm order is the fix and belongs to the next battery.
2. **E1 cannot distinguish parity from a +-20% effect** at eight questions; "parity" here means "no
   effect this design could see".
3. **E2 compares across batteries** with three uncontrolled differences, listed above.
4. Synthetic corpora, one agent runtime, one machine, three repeats. Nothing here generalizes past
   that.
5. The cache was primed before every cached run and verified per run; a bundle nobody has queried
   before pays the cold path, which this battery does not measure.
