---
type: Research
title: Does readb make an agent cheaper or faster than plain file access?
description: A four-arm benchmark of one agent answering twelve questions over a 600-concept OKF bundle, with and without readb. Measured, not asserted.
tags:
- benchmarks
- agents
measured: 2026-08-10
created: 2026-08-10
timestamp: '2026-08-10T00:00:00Z'
---

Produced by the backlog task `024-measure-agent-efficiency` (sprint-004). readb's pitch to agents
is efficiency — one SQL query instead of many file reads — and until this experiment that claim
had no measurement behind it. The design was reviewed adversarially before any measured run and
substantially rebuilt as a result; the corrections are recorded in the task.

**The numbers below describe one model, one agent runtime, one synthetic corpus and one battery,
at three repeats per cell.** Nothing here supports a claim beyond that.

# Method

## Arms

Four arms. Every arm receives the same question text; only the preamble and the environment
differ.

| Arm | Preamble | readb |
| --- | --- | --- |
| `baseline` | Orientation only: a knowledge base of markdown files, shell tools available | Absent from `PATH` |
| `shell-coached` | Orientation plus a worked `grep`/`awk` recipe over the same corpus | Absent from `PATH` |
| `readb-bare` | Orientation plus `readb query` and `readb schema` syntax | On `PATH` |
| `readb-skill` | Orientation only — identical to `baseline` | On `PATH`, the shipped plugin loaded so the skill is discoverable |

`shell-coached` exists because readb's honest competitor is a shell pipeline, not an uncoached
agent. Without it, `readb-bare` minus `baseline` measures *given a worked recipe* against *given
none*, and would be misread as *readb* against *file tools*.

`readb-skill` carries no inline instruction: what it measures is whether the shipped skill is
found and used from a cold prompt.

## Corpus

A deterministic synthetic OKF bundle (seed 24): 600 concepts across four types — 180 `Service`,
198 `Runbook`, 162 `Incident`, 60 `Decision` — with 6–9 frontmatter keys per type including
list-valued ones, and 15–60 line bodies. 2.3 MB, roughly 3.9 KB per file. A second corpus adds 12
files whose frontmatter declares `type: Service` but does not parse as YAML.

Ground truth is computed twice by independent paths — from the generation parameters, and by
reading the written files back with PyYAML — and generation fails if they disagree. It is written
outside the bundle, where the agent under test cannot reach it.

## Battery

Twelve questions. Seven are frontmatter aggregation, where a SQL layer is expected to win. Five
were added specifically because a battery with no losing shape is not a measurement.

| # | Shape | Favours |
| --- | --- | --- |
| Q1 | Type rollup | sql |
| Q2 | Group-by on one field | sql |
| Q3 | Filtered listing | sql |
| Q4 | Cross-reference between two types | sql |
| Q5 | List-field membership | sql |
| Q6 | Extremum over a group-by | sql |
| Q7 | Exact-phrase needle in a body | files |
| Q8 | Three-predicate multi-hop | sql |
| Q9 | Single-file field lookup | files |
| Q10 | Count including files whose YAML does not parse | files |
| Q11 | Fuzzy retrieval among four near-identical candidates | files |
| Q12 | Five related questions in one session | neutral |

Q10 is the sharpest of these: readb's permissive load **skips a malformed file silently**, so a
count taken through readb alone omits the 12 broken records — readb reports 180 services where
`grep` finds 192. The question asks for the count including them, in every arm's prompt.

## Controls

- Model `claude-sonnet-5` at medium effort, pinned; the dated model id is recorded per run.
- Every arm runs with `--setting-sources ""`: no personal configuration, skill, hook or MCP
  server reaches any of them. `--plugin-dir` then adds exactly one skill to `readb-skill`. A
  preflight refuses to start unless the baseline lacks that skill and `readb-skill` has it.
  (`--safe-mode` cannot be used: it suppresses `--plugin-dir`, and the arm would silently
  collapse onto the baseline.)
- Per-arm `PATH`: the readb-free arms cannot reach the globally installed binary, and any run
  whose transcript mentions readb in a readb-free arm is discarded.
- readb 0.2.0 from a pinned venv — the released artifact, not the working copy.
- Each run gets a fresh working directory containing nothing but its own copy of the corpus,
  under a path that does not contain the string `readb` (the agent's cwd reaches its system
  prompt).
- Runs are interleaved by arm and the question order rotates per repeat.
- Full stream transcripts are kept, which is what makes the integrity checks above possible at
  all.

## Metrics

| Metric | Definition |
| --- | --- |
| **New tokens ingested** | `input + cache_creation` — content the agent actually had to pull in. The headline. |
| Cumulative prompt tokens | All four token counts summed. Billing-facing, and largely driven by turn count. |
| Cost, cache-neutral | Recomputed from token counts with every input token priced as fresh, against a price table committed with the results. |
| Cost, as billed | The same recomputation at cache prices. Reproduces the runtime's own figure to the cent. |
| Wall clock | Harness-measured, cross-checked against the runtime's own duration. |
| Turns, readb invocations | From the transcript. |
| Exactness / partial credit | Binary set-equality, plus F1, against a normalizer fixed before the first run. |

Comparisons are **paired by question**: per-question median per arm, then the ratio, then the
median ratio across the twelve questions, with a percentile bootstrap interval resampled over
questions. Between-question variance dominates between-repeat variance here, so a figure pooled
across shapes would mostly report the battery's composition.

# Results

144 runs (4 arms × 12 questions × 3 repeats), 2026-08-10. **None was excluded**: no leak, no
permission denial, no unsupported answer, no context compaction, no harness fault. Total spend
$16.51.

## Headline

| Arm | Exact | New tokens ingested | Cost, cache-neutral | Wall clock | Output tokens | Turns |
| --- | --- | --- | --- | --- | --- | --- |
| `baseline` | 97% | 9,739 | $0.370 | 11.4 s | 453 | 4.0 |
| `shell-coached` | 100% | 9,051 | $0.368 | 11.8 s | 512 | 4.0 |
| `readb-bare` | 94% | 9,542 | $0.278 | 10.6 s | 338 | 3.0 |
| `readb-skill` | 100% | 12,260 | $0.493 | 14.4 s | 604 | 6.0 |

Medians across all runs in the arm. Ratios below are the defensible form — paired by question,
with a percentile bootstrap interval over questions:

| Arm vs `baseline` | New tokens ingested | Cost | Wall clock | Output tokens | Turns |
| --- | --- | --- | --- | --- | --- |
| `shell-coached` | 0.95× [0.91–0.97] | 0.99× [0.79–1.02] | 0.95× [0.79–1.16] | 0.98× [0.70–1.04] | 1.00× [0.79–1.00] |
| `readb-bare` | 0.97× [0.85–1.02] | **0.76×** [0.62–1.00] | 1.03× [0.70–1.20] | **0.65×** [0.43–0.96] | **0.75×** [0.62–1.00] |
| `readb-skill` | 1.21× [1.00–1.35] | 1.21× [0.90–1.55] | 1.28× [0.89–1.38] | 0.99× [0.79–1.16] | 1.33× [1.00–1.75] |

Against `shell-coached` — the fairer comparison, since both arms are coached — `readb-bare`'s
median cost ratio is **0.76×**, the same figure. The saving is not an artefact of being told
what to do.

## What the numbers say

**1. There is no accuracy effect.** Every arm answered every question shape correctly, including
the two the tool was expected to fail. The three misses in the whole matrix are all Q6 and all a
defect in that question's answer template (below), not a difference in capability. On this corpus
and battery, readb does not make an agent more right — the file-reading arms were not struggling.

**2. The cost saving is real but modest and unevenly distributed.** `readb-bare` costs about a
quarter less overall, and the interval's upper bound touches 1.00, so a null effect is not
excluded at this n. The saving comes almost entirely from **fewer turns and less output**, not
from ingesting less: new tokens ingested is 0.97× — statistically nothing. readb does not save
an agent from reading the bundle; it saves the agent from *writing* shell pipelines.

**3. Wall clock does not improve at all** (1.03×). readb loads and discards the whole bundle on
every invocation — measured at **0.93 s for 600 concepts** on this machine, against roughly 10 ms
for a grep — and that overhead cancels the turns it saves.

**4. The effect is concentrated in join-shaped questions.** Per-question cost ratio,
`readb-bare` against `baseline`:

| Question | Shape | Ratio | |
| --- | --- | --- | --- |
| Q8 | Three-predicate multi-hop | **0.32×** | readb wins decisively |
| Q4 | Cross-reference between types | **0.38×** | |
| Q3 | Filtered listing | 0.49× | |
| Q6, Q11, Q12 | Extremum, fuzzy, session | 0.74–0.75× | |
| Q1 | Type rollup | 0.77× | |
| Q5, Q7, Q9 | Membership, needle, single file | 0.98–1.00× | parity |
| Q10 | Malformed-file count | 1.24× | readb loses |
| Q2 | Group-by on one field | 1.34× | readb loses |

Q2 is the instructive loss: `grep -h '^status:' … | sort | uniq -c` is a one-liner an agent
writes without hesitation, and paying a bundle load to run `GROUP BY` costs more than it saves.
readb earns its keep where a shell pipeline needs a *join* — Q4 and Q8, where the baseline spent
nine and ten turns debugging nested `awk` loops against readb's three.

**5. The shipped skill is a net cost.** `readb-skill` is worse than doing nothing on every
metric: 1.21× the cost, 1.33× the turns. The skill did fire — 28 of 36 runs, and sensibly (never
on the exact-phrase needle, once on the single-file lookup) — but loading and following it costs
more than the queries it produces save. Its one clear win is Q4 (0.41× baseline). This is a
finding about the skill as shipped, not about whether a skill can pay for itself.

**6. Coaching alone changes nothing.** `shell-coached` sits at 0.99× the baseline's cost. Giving
an agent a worked `grep`/`awk` recipe does not measurably help; it already knows how.

**7. An agent given readb often declines to use it — correctly.** In 12 of 36 `readb-bare` runs
no readb command was issued, and those 12 are exactly the four file-favouring questions (Q7, Q9,
Q10, Q11, 3/3 each). The tool choice was right every time: on those shapes readb offers nothing.

**8. The malformed-file trap never sprang.** Q10 asks for a count that includes 12 files whose
frontmatter does not parse — where readb reports 180 services and `grep` finds 192. Every arm
answered 192, because the readb arms reached for `grep` instead. The documented silent-skip
behaviour is a real hazard, but on this question an agent did not walk into it. It cost the readb
arm money anyway: Q10 is `readb-bare`'s worst question against `shell-coached` at 2.70×.

## Size sweep — the finding that matters most

The main matrix runs at one size. A separate sweep repeats the four query-shaped questions
(Q3, Q4, Q8, Q12) at 150, 600 and 2000 concepts, `baseline` against `readb-bare`, two repeats —
32 additional runs. Every answer in the sweep was correct in both arms at every size.

| Concepts | `baseline` cost | `readb-bare` cost | Ratio | `baseline` wall | `readb-bare` wall |
| --- | --- | --- | --- | --- | --- |
| 150 | $0.46–0.86 | $0.28–0.32 | **0.51×** | 12–26 s | 8–10 s |
| 600 | $0.37–0.98 | $0.28–0.37 | **0.44×** | 14–27 s | 10–14 s |
| 2000 | $0.51–1.32 | $0.28–0.29 | **0.29×** | 15–49 s | 15–24 s |

Ratios are the median across the four questions at that size.

**readb's cost is close to flat in corpus size; unguided file access is not.** Across a 13×
growth in the bundle, `readb-bare` moved from $0.28 to $0.28 on Q8 while `baseline` went from
$0.86 to $1.32, and the baseline's turn count climbed from 8 to 11.5 as its shell pipelines
needed more debugging. That is the mechanism behind the whole result: a SQL query's cost is set
by the answer, a grep pipeline's by the corpus.

Wall clock crosses over too, in the other direction from the aggregate figure: at 2000 concepts
`readb-bare` finished Q8 in 19 s against the baseline's 49 s. The exception is Q12, the five-part
session, where readb *loses* wall clock at 2000 (24 s against 15 s) — five queries mean five full
bundle loads. Measured load time for a single `readb query` on this machine:

| Concepts | Load + query |
| --- | --- |
| 150 | 0.28–0.35 s |
| 600 | 0.80–0.89 s |
| 2000 | 2.52–2.79 s |

The bundle is re-read on every invocation, so that figure is paid per query, not per session.
This is the strongest argument in the data for the persistent index cache the loader was designed
to accommodate.

## The Q6 defect

Q6's answer template read `ANSWER: team-name=<count>`, and three runs copied the placeholder
literally — `team-name=31`, `team-name=platform=31`, `team-name=platform, count=31`. All three
carry the right team and the right count; the pre-registered scorer marked them wrong, and they
are left marked wrong rather than re-scored after the fact. Read the accuracy column as **100%
on substance across all four arms**, with Q6's format compliance varying by chance. The
placeholder should have been a shape the model could not mistake for an answer.

# What this supports, and what it does not

**Supported by the measurement:**

- On a bundle of a few hundred concepts and up, an agent told that readb exists spends about a
  quarter less per question than one working from files, and the gap widens with bundle size —
  to roughly a third of the cost at 2000 concepts.
- The saving comes from fewer turns and less generated output, not from reading less. The agent
  stops writing and debugging shell pipelines.
- readb's cost is close to independent of bundle size. File-based access is not.
- The advantage is concentrated in questions needing a **join or several predicates**. On
  single-field group-bys, single-file lookups and exact-phrase searches, readb is at parity or
  worse.
- An agent given readb picks correctly when to use it, and skips it on shapes where files win.
- The shipped skill, as it stands, costs more than it saves.

**Not supported, and not claimed:**

- No accuracy benefit was observed. Every arm answered every shape correctly.
- No general wall-clock benefit at 600 concepts; the advantage appears only at 2000, and reverses
  for repeated queries in one session.
- Nothing about other models, other agent runtimes, or real (non-synthetic) bundles.
- No statistical significance claim. Three repeats support medians and intervals; the cost
  interval's upper bound touches 1.00.
- No README figure follows from this document. Publishing a headline number needs a follow-up
  that re-runs the pre-registered analysis, ideally on a second day and a real bundle.

# Limitations

1. **One model, one runtime, one machine, one day.** The wall-clock noise floor was not
   established by a second measurement block.
2. **Synthetic corpus.** Generator and seed are committed, but a generated bundle's frontmatter
   is more regular than a real one's, which flatters both arms' pipelines.
3. **The battery is author-written.** Twelve questions, five of them chosen specifically to be
   hard for readb, but the selection is still not neutral. Per-question results are published so
   the composition can be judged.
4. **Read path only.** `readb set` is not exercised; nothing here speaks to the write path.
5. **n = 3** in the main matrix, **n = 2** in the sweep.
6. **Q6's answer template was defective**, as described above.
7. **The cost model is a recomputation**, not an invoice: token counts times a committed price
   table. It reproduces the runtime's own figure to the cent, which is the check that the table
   is right.
8. Arms measuring the skill's *content* separately from its *discovery*, and a cross-check
   against the runtime's own plugin-evaluation harness, were designed but not run.

# Reproducing

Harness, corpus generator, battery, scorer, raw per-run records and full transcripts are in
[`benchmarks/`](../../../benchmarks/README.md), with a `manifest.json` per batch recording the
runtime version, readb version, model, price table, corpus checksums and machine.
