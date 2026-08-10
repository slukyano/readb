---
type: Task
title: Measure readb's efficiency gains for agents over unguided bundle access
description: A/B-benchmark an agent on OKF-style bundles — no guidance vs. using readb — measuring wall-clock speedup and token-usage reduction on large enough repos.
status: Designed
priority: medium
tags:
- research
- benchmarks
created: 2026-07-21
timestamp: '2026-08-10T00:00:00Z'
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

## Design revision 1 — after independent expert review, 2026-08-10

The design above was reviewed adversarially before any measured run by an agent-benchmark
specialist with no stake in the outcome. Verdict: **not fit to run as written** — two of three
arms had defects that would have made their numbers uninterpretable, and the chosen output format
made those defects undetectable after the fact. The changes below all landed before the first
measured run.

### Corrections to controls

| Finding | What was wrong | What changed |
| --- | --- | --- |
| Arm C measured nothing | `--safe-mode` **suppresses `--plugin-dir`** — verified: a probe under both flags lists only Claude Code's built-in skills, no `readb`. Arm C would have silently run as arm A while the write-up read the null as "the skill's description doesn't trigger". | All arms now run under `--setting-sources ""` (identical built-in-only environment, verified); `--plugin-dir` then adds exactly one skill. A **preflight** asserts the skill is absent in the baseline and present in arm C, and refuses to start otherwise. |
| Baseline could reach readb | A globally installed `readb` sits on this machine's `PATH`. | Per-arm `PATH` construction; the baseline gets `/usr/bin:/bin:/usr/sbin:/sbin` and the runtime binary is invoked by absolute path. A post-hoc assertion fails any baseline run whose transcript contains the string `readb`. |
| No transcripts | `--output-format json` records no tool calls, so *none* of the integrity checks the design promised could actually be made. | `--output-format stream-json`, full transcript persisted per run. Every run now carries its tool calls, its readb invocation count, whether the skill fired, and whether any tool call was made at all. |
| The cwd leaked the tool's name | Caught by the new assertion on its first use: the working root sat under a path containing `readb`, which is echoed into the agent's system prompt. | Working directories are created under a neutral root and named `kb-<uuid>`. |
| Permissions came from dotfiles | A denied `Bash` would cripple the readb arms (which need it) and barely touch the baseline, reading as "readb didn't help". | Permissions pinned explicitly; any run with a permission denial is excluded from the metrics rather than counted. |
| Answers could be unsupported | Binary scoring rewards a lucky guess as much as a derivation. | A run with zero tool calls is scored 0 whatever it answered. |

### Corrections to arms

A fourth arm, **`shell-coached`**, was added. Arm B's preamble does three things at once — names a
tool, supplies working syntax, and orients the agent to the data model — so `B − A` was measuring
*coached versus uncoached*, not *readb versus file tools*. `shell-coached` receives a
length-matched preamble with a worked `grep`/`awk` recipe over the same corpus. readb's honest
competitor is a shell pipeline, and this is the arm that supplies one.

| Arm | Preamble | readb |
| --- | --- | --- |
| `baseline` | orientation only | absent from `PATH` |
| `shell-coached` | orientation + a worked grep/awk recipe | absent from `PATH` |
| `readb-bare` | orientation + `readb query` / `readb schema` | on `PATH` |
| `readb-skill` | orientation only (identical to `baseline`) | on `PATH`, shipped skill loaded |

### Corrections to metrics

- The headline is **new tokens ingested** (`input + cache_creation`) — content the agent actually
  had to pull in. The design's "context volume" summed cached reads too, which grows with turn
  count and largely re-measures `num_turns`; it is still reported, renamed **cumulative prompt
  tokens** and labelled billing-facing.
- Cost is **recomputed** from token counts against a price table committed with the results, main
  model only, in two forms: as-billed and **cache-neutral** (every input token priced as fresh).
  The recomputation reproduces the runtime's own `total_cost_usd` to the cent, which is the check
  that the price table is right. `total_cost_usd` is recorded but is not a metric: it depends on
  the machine's cache state and on prices that will move.
- **readb invocations per run** is now recorded, because the bundle is reloaded on every one.

### Correction to a stated fact

The design claimed readb's startup cost is ~0.1–0.25 s. Measured on this machine against this
benchmark's own corpus: **0.93 s at 600 concepts** (0.14 s at 5). The reviewer independently
measured 2.8 s at 2000. The load is repaid on **every invocation**, so a multi-query session pays
it repeatedly against a grep's ~10 ms. Wall clock and tokens are therefore reported separately and
never blended into one "efficiency" figure — readb may lose the former while winning the latter.

### Corrections to the battery

The original eight questions were seven-to-one in favour of SQL, and the one counterweight (an
**exact-phrase** needle) is a recipe the shipped skill teaches, so it favoured readb too. There
was no shape in which readb could lose. Four were added:

| # | Shape | Why it can go against readb |
| --- | --- | --- |
| Q9 | Single-file lookup | Loading a 600-concept bundle to read one field is pure overhead against one `Read`. |
| Q10 | Malformed-file honesty | 12 files declare `type: Service` in frontmatter that does not parse. readb's permissive load **skips them silently** — verified: readb reports 180, `grep` finds 192. The question asks for the count *including* them, in both arms' prompts. |
| Q11 | Fuzzy retrieval | Four runbooks describe a failover; all four mention a standby and a datastore, so neither `grep` nor SQL `LIKE` separates them. The candidates must be read. |
| Q12 | Five-part session | Five related questions in one run — the realistic shape. The file-reading arms pay their reads once and keep them in context; the readb arms pay a full bundle load per query. |

A write chore (`readb set` over many files) is **out of scope**: this task measures the read path,
and the write-up states that limitation rather than implying coverage.

### Corrections to analysis, and what may not be claimed

- Comparisons are **paired by question** — per-question median per arm, then the ratio, then the
  median ratio across questions, with a percentile bootstrap interval resampled over *questions*.
  Between-question variance dominates between-repeat variance here, so an arm-level number pooled
  across shapes would be an artefact of the battery's composition.
- Set answers are scored by exact set-equality **and** F1, with a normalizer **pre-registered**
  before the first run (strip directories and `.md`, casefold, split on commas/newlines) — arms
  name things differently by construction, and a normalizer tuned after seeing results is a
  garden of forking paths.
- Ground truth is computed **twice by independent paths** — from the generation parameters, and by
  reading the written files back with PyYAML — and the generator fails if they disagree.
- **Forbidden in the write-up at n=3**: any p-value or the word "significant"; any point ratio
  without its interval; a bare "N× faster/cheaper" headline; generalization to another model,
  runtime, or a non-synthetic bundle; and any README figure before a follow-up task re-runs the
  pre-registered analysis.

### Accepted but not implemented

Named here so the write-up can state them as limitations rather than pass over them: a second
arm pairing the readb preamble *with* the skill (isolating the skill's content from its
discovery); a corrected size sweep across 25/100/300/600/2000 concepts; a cross-check against
`claude plugin eval --ablation`; and a second measurement block on another day to establish the
wall-clock noise floor. Each is additive; none blocks a first honest number.
