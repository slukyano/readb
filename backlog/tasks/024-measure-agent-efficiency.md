---
type: Task
title: Measure readb's efficiency gains for agents over unguided bundle access
description: A/B-benchmark an agent on OKF-style bundles — no guidance vs. using readb — measuring wall-clock speedup and token-usage reduction on large enough repos.
status: Draft
priority: medium
tags:
- research
- benchmarks
created: 2026-07-21
---

readb's pitch to agents is efficiency: one SQL query instead of many file reads. That claim
is currently unmeasured. This task designs and runs the experiment: have an agent (Claude in
the initial setup) perform the same tasks over OKF-style bundles twice —

1. **Baseline**: no guidance at all; the agent figures out whatever it wants to access
   (grep, file reads, manual scanning).
2. **With readb**: the agent is instructed to use readb for bundle access.

Compare the two arms on **wall-clock time** and **token usage** (both should drop with
readb). The bundles must be large enough for the difference to be measurable — small
backlogs like this repo's `tasks/` may be answerable in a couple of reads either way.

## Notes (to refine)

- Corpus: find or synthesize large OKF-style bundles (hundreds to thousands of concepts);
  a generator would also give control over concept size and schema spread.
- Task battery: representative agent chores — status/priority rollups, filtered listings,
  cross-file lookups, "find the concept where X" — each with a verifiable correct answer,
  so accuracy can be checked alongside cost.
- Harness: scripted runs per arm with captured token counts and timings; repeat runs to
  average out variance; keep prompts identical except for the readb instruction.
- Possible third arm: readb plus the shipped usage skill
  ([ship-usage-skill](../archive/025-ship-usage-skill.md)), to measure what the skill adds over bare
  tool availability.
- Output: a durable `Research` concept in `docs/dev/research/` with the numbers, setup, and
  date; headline figures could feed the README.
