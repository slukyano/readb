---
type: Research
title: Pre-registration — agent-efficiency benchmark v3
description: Arms, corpora, battery, endpoints, exclusion rules and prices for the v3 benchmark, fixed before the first measured run.
tags:
- benchmarks
- agents
created: 2026-08-23
timestamp: '2026-08-23T00:00:00Z'
---

Committed **before any measured v3 run**, as v1 and v2 were. Produced by the backlog task
`035-benchmark-v3-cached` (sprint-007).

v3 exists because two shipped surfaces changed on reasoning rather than evidence, and
[v2](agent-efficiency-v2.md) measured a load path that no longer exists.

# What v3 asks

1. **Does the persistent index cache change what an agent costs?** Its claim is a wall-clock
   claim, and wall clock is the one thing v2 demoted to a footnote.
2. **Did the skill's new `description` move discovery?** v2 measured the old wording: the skill
   was loaded on 37 of 78 runs, and readb was never invoked at all on 41.

# Arms — five

| Arm | Preamble | `PATH` | Bundle state |
| --- | --- | --- | --- |
| `baseline` | orientation only | shims, no readb | no registry |
| `shell-coached` | orientation + a worked recipe per corpus family | shims, no readb | no registry |
| `readb-bare` | orientation + readb syntax (v1's text, unchanged) | + readb | **no registry: no cache** |
| `readb-cached` | **identical to `readb-bare`, word for word** | + readb | **`readb init` run, cache primed** |
| `readb-skill` | orientation only; the shipped plugin loaded | + readb + uv | `readb init` run, cache primed |

`readb-cached` differs from `readb-bare` by one thing that is **not prompt text**: whether the
corpus is a readb registry with a warm cache. A test in `benchmarks/test_harness.py` asserts every
other field of the two arms is equal, so the contrast cannot silently become something else.

**`readb-nudged` is dropped.** v2 ran it, found it moved readb usage without moving any cost ratio
and roughly doubled failed readb calls, and published that. Re-running it would spend a fifth of the
battery re-confirming a negative. This is a deviation from v2's arm set and is reported as one.

## Cache warmth, decided in advance

The cache is primed by one `readb query` after the corpus is copied and before the agent starts.
**The priming call is not charged to the arm** — it runs outside the runtime invocation whose tokens
and wall clock are recorded, and a test pins that ordering. The claim under test is about repeat
invocation, not first contact; the cold path was measured directly in sprint-007 and is reported
from those numbers rather than re-derived from agent runs.

Corpora are regenerated per repeat, so no arm inherits another's filesystem state.

# Corpora, battery and strata — unchanged from v2

Four corpora (`ops` 600 concepts messy, `ops-malformed` 612, `ops-tidy` 600 as the sweep control,
`backlog` 192), and the same 26 questions across five strata: scan 4, join 8, retrieval 3, hazard 3,
backlog 8. Keeping them fixed is what makes v3 comparable to v2 line for line.

# Endpoints — three, Holm-corrected

| id | Contrast | Statistic |
| --- | --- | --- |
| **E1** | billed cost, `readb-cached` vs `readb-bare`, backlog stratum, Sonnet | paired signed-rank by question |
| **E2** | skill invocation rate, `readb-skill`, against v2's recorded 37/78 | two-proportion test |
| **E3** | billed cost, `readb-cached` vs `shell-coached`, join stratum, Sonnet | paired signed-rank by question |

**E1 is predicted to return parity or near it.** Agent cost tracks turns; the cache changes seconds,
not turns. Recording that prediction here is the point of pre-registering: a null result is the
expected result, and publishing it is not a disappointment.

Wall clock returns as a **declared secondary** for E1's contrast only — same machine, same repeat,
the one place it is a fair comparison. Everything else — accuracy, turns, tool-choice matrices,
per-model tables — is descriptive and is reported as descriptive.

# The frozen skill description

E2 measures this text, which shipped in sprint-006 and is not edited before or after the run:

> Answer questions about a directory of markdown files by running SQL over their YAML frontmatter, and change one frontmatter field without rewriting the file. Use when a question spans many .md files in one tree — a docs directory, a notes vault, a knowledge base, an OKF bundle — and answering it would otherwise mean grepping, cat-ing or yq-ing file after file: counts and rollups, "which files have X", filtering or grouping by a frontmatter key, or cross-referencing one document type against another. Also use when a single frontmatter field in one file needs setting or removing.

If E2 says discovery did not move, the hypothesis behind that wording was wrong and the write-up
says so. Tuning the text until the benchmark improves would measure the tuning.

# Exclusion rules

A run is excluded, and the exclusion reported with its count, when: the runtime errors or is
rate-limited; the transcript shows a readb-free arm invoking readb (a PATH leak); context
compaction fires; or no `ANSWER` line is produced *and* the transcript shows the agent never
attempted the question. A wrong answer is never excluded — it is the measurement.

If the instrument is found defective after runs have happened, those runs are **deleted**, not
adjusted, and the deletion is reported. v2 deleted 77 runs on that rule.

# Prices

Recomputed from token counts against this table, committed here and used for every figure:

| Model | Input | Output | Cache read | Cache write 5m | Cache write 1h |
| --- | --- | --- | --- | --- | --- |
| Sonnet 5 | $2.00 | $10.00 | $0.20 | $2.50 | $4.00 |
| Haiku 4.5 | $1.00 | $5.00 | $0.10 | $1.25 | $2.00 |

Ratios are always contrasts between two arms on the same model, where a uniform scale cancels.

# Matrix

Sonnet across five arms, Haiku across four (no skill arm), three repeats, plus floors — the same
shape as v2's 783 runs, which billed $50.92. Expect the same order of magnitude.
