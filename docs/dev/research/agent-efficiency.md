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
