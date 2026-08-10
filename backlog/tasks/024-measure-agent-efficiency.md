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

## Design

Written on `sprint/004`, 2026-08-10. The experiment is a three-arm A/B/C benchmark of one agent
runtime answering a fixed question battery over one synthetic OKF bundle. **A negative or null
result is published as it stands** — the point is a number, not a favourable number.

### Arms

Every arm receives a byte-identical question prompt. The arms differ only in what the runtime
makes available.

| Arm | Label | What differs |
| --- | --- | --- |
| A | `baseline` | No mention of readb. Standard file tools (`Read`, `Grep`, `Glob`, `Bash`). All customizations off. |
| B | `readb-bare` | Identical, plus a two-sentence preamble stating that `readb` is installed and showing `readb query "<sql>" --bundle <dir>` and `readb schema --bundle <dir>`. |
| C | `readb-skill` | Identical to **A's prompt** — no preamble — with the repository's shipped plugin loaded, so `skills/readb/SKILL.md` is discoverable. |

Arm C deliberately carries no inline instruction: what it measures is whether the shipped skill
gets *found and used* from a cold prompt. If it never triggers, C collapses onto A, and that is a
finding about the skill's description, not a failed run.

### Corpus

Deterministic, seeded generator (`benchmarks/generate_corpus.py`), producing a neutral
platform-engineering knowledge base — not this project's own process material.

| Property | Value |
| --- | --- |
| Primary size | 600 concepts |
| Concept types | `Service`, `Runbook`, `Incident`, `Decision` |
| Frontmatter | 6–9 keys per type, incl. scalars, enums, dates, and list-valued keys (`services`, `tags`, `dependencies`) |
| Body | 15–60 lines of markdown with conventional headings, so a file read costs realistic tokens |
| Layout | One directory per type, plus `index.md` (reserved, non-concept) |

The generator writes a `ground_truth.json` beside the corpus, computed **from the generation
parameters in plain Python** — never by querying readb, which would bias correctness toward
readb's own semantics.

A supplementary **size sweep** (120 / 600 / 2000 concepts) runs a three-question subset, to locate
the crossover below which unguided reading is competitive — the task's own caveat that small
bundles may be answerable in a couple of reads either way.

### Question battery

Eight questions, each with a mechanically checkable answer. The set spans shapes that favour SQL
and shapes that do not.

| # | Shape | Question |
| --- | --- | --- |
| Q1 | Type rollup | Count of concepts of each type |
| Q2 | Group-by | `Service` count by `status` |
| Q3 | Filtered listing | Tier-1 services owned by one team whose status is not `ga` |
| Q4 | Cross-reference | Runbooks whose service is tier-1 and deprecated |
| Q5 | List membership | Incidents whose `services` list contains a given service |
| Q6 | Extremum | The team owning the most services |
| Q7 | Body needle | The concept whose body contains an exact phrase — **grep-favouring**, included on purpose |
| Q8 | Multi-hop | Runbooks covering the services of every sev-1 incident |

Each prompt ends with the answer protocol: a final line `ANSWER: <value>`, scored as
set-equality (order- and case-insensitive) or numeric equality. Scoring is **binary**; the raw
answer text is retained for every run so a wrong answer can be inspected rather than guessed at.

### Controls

- **Model and effort pinned**: `--model claude-sonnet-5 --effort medium`. One model, one runtime;
  generalization beyond that is not claimed.
- **Customizations off**: `--safe-mode` (arms A, B) so no user CLAUDE.md, skill, plugin, hook or
  MCP server leaks in. Arm C is the same environment plus `--plugin-dir` for this repository's
  plugin; the harness asserts that arms A and B loaded no skill.
- **No network**: `WebSearch`/`WebFetch` disallowed in every arm.
- **readb as shipped**: version 0.2.0 installed into a dedicated venv and put on `PATH`, not
  `uvx` (whose resolution latency is not part of the tool) and not the working copy.
- **Read-only corpus**: mode `555`/`444`, so the read-only contract is enforced rather than
  trusted; a writable scratch dir sits beside it.
- **Cache and drift spread across arms**: runs are interleaved round-robin by arm and the
  question order rotates per repeat, so no arm systematically inherits a warm prompt cache. Two
  discarded warmup runs precede the measured set.
- **Per-run budget guard**: `--max-budget-usd`; a run that trips it is recorded as truncated, not
  silently dropped.
- **Repeats**: 3 per (arm × question) — 72 measured runs — raised to 5 if the pilot's cost allows.

### Metrics

Captured per run from the runtime's JSON result, then aggregated as **median and IQR** (the
distributions are long-tailed; means would be led by one runaway run):

| Metric | Source |
| --- | --- |
| Wall clock | harness-measured, cross-checked against `duration_ms` |
| Context volume | `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` |
| Output tokens | `output_tokens` |
| Cost | `total_cost_usd`, and main-model-only cost from `modelUsage` |
| Turns | `num_turns` |
| Accuracy | binary, against `ground_truth.json` |
| Faults | `is_error`, `permission_denials`, truncation |

Both raw tokens **and** cost are reported: cache reads are billed at a fraction of fresh input,
so a token ratio and a cost ratio can disagree, and quoting only the flattering one would be
dishonest. Three repeats support medians and ratios, not significance claims; the write-up says
so and publishes every raw data point.

### Threats to validity (stated before the runs, revisited after)

1. **Battery selection bias** — the questions are written by readb's author. Mitigated by Q7 (a
   grep-favouring needle) and by reporting per-question results, never a single blended figure.
2. **Prompt caching** — controlled by interleaving; residual effect visible in the cache columns.
3. **Synthetic corpus** — generator parameters are published with the results.
4. **Single model / single runtime** — claimed as such.
5. **Agent nondeterminism** — three repeats; spread reported, not hidden.
6. **readb's own startup cost** (~0.1–0.25 s per invocation) is inside the measurement, as it
   should be.

### Deliverables and public-surface delta

- `docs/dev/research/agent-efficiency.md` — the dated `Research` concept: setup, numbers, raw
  data pointer, and the honest reading.
- `benchmarks/` — generator, harness, battery, scorer, and raw per-run JSON, committed for
  reproducibility and **excluded from the sdist** (the precedent set for process material).
- **readb's public surface is unchanged**: no CLI command, flag, or output format; no Python API
  name; no config key or on-disk path read by the tool; no change to the packaged wheel. The only
  packaging change is the sdist exclusion above.
- README figures are **not** part of this task. If the numbers support a claim, a follow-up task
  carries it into the README; if they do not, nothing moves.
