---
type: Sprint
title: Benchmark v2 — realistic workloads and a second model
description: Build and run the v2 agent-efficiency benchmark — a task-tracker-shaped corpus, 26 pre-registered questions, five arms, Sonnet and Haiku — and fix the shipped skill's uv assumption.
tags:
- research
- benchmarks
timestamp: '2026-08-22T08:00:00Z'
branch: sprint/005
created: '2026-08-22'
status: Done
tasks:
- 031-benchmark-v2
- 030-skill-uvx-assumption
---

Fifth sprint under the [session/sprint workflow](../workflow.md), and the direct follow-on from
sprint-004.

## Scope rationale

Sprint-004 measured readb's efficiency claim for the first time and published fifteen limitations
alongside the number. `031` addresses the ones that can change a conclusion — an underpowered
comparison against the honest competitor, a corpus regular enough to flatter shell pipelines, a
battery with no realistic workload and nothing needing a concept's body, a single model at the
accuracy ceiling, and a hazard never tested un-warned. Its design is already written and
approved; the sprint is a build-and-run.

`030` rides along because it is a defect in a shipped public surface that this line of work found:
`skills/readb/SKILL.md` leads with `uvx readb`, which fails on any machine where readb is
installed but `uv` is not. It invalidated 36 benchmark runs before it was understood. Small, and
it belongs with the work that surfaced it.

Deliberately out of scope: `028-evaluate-rust-rewrite`, which sprint-004 was supposed to feed.
The data already points at its answer — cost is turn-driven, not language-driven, and 13–32% of
readb's wall clock is repeated bundle loading, so the lever is a cache rather than a rewrite — but
that argument deserves its own sprint and an ADR, not a rider on a benchmark.

## What v2 must not become

Two design commitments carried into this sprint, both from the review rounds that shaped v1:

- **The nudge is an arm, not an edit.** Prompt text is never adjusted because the agent chose the
  "wrong" tool. Routing guidance is a fifth arm with a frozen sentence and a retraction rule; the
  un-nudged arm is always run and always reported. Tuning a prompt until the numbers improve
  measures the tuning, not the tool.
- **A negative result is still a result.** v2 is more likely than v1 to produce parity — the shell
  arms now have ripgrep and a YAML processor, and the backlog bundle is small enough to sit near
  the harness floor. That outcome gets published as it stands.

## Task checklist

- [x] 030-skill-uvx-assumption — the skill's leading example must work where readb is installed
      and `uv` is not
- [x] 031-benchmark-v2 — corpora, battery, harness changes, 783 runs, stratified analysis, and a
      second `Research` concept

`030` is ordered first: it lands before the first measured v2 run, so v2 measures the corrected
skill rather than the artifact whose `uv` assumption retracted an arm of v1.

## Implementation checklist

1. [x] `030` — the skill's leading example, plus the two regression tests that keep it bare
2. [x] `generate_corpus.py` — messy/tidy styling, the new plants and assertions, the
       malformed-team flip
3. [x] The backlog corpus generator — invented product, tasks/archive/sprints, mechanical ground
       truth for the body questions
4. [x] `battery.py` — `record` and `mapping_str` kinds, the `none` convention, `expert_tool`,
       q6 reworded, q14–q18 and b1–b8
5. [x] `run_benchmark.py` — the `readb-nudged` arm, per-corpus recipes, a corpus registry,
       per-model price tables, recipe preflight, tool-choice and failure recording
6. [x] `analyze.py` — strata, the three endpoints with exact tests, tool-match matrices, the
       nudge contrast, per-model sections
7. [x] Tests for all of it, and **pre-registration committed before the first measured run**
8. [x] Runs — Sonnet and Haiku blocks, floors, messiness sweep
9. [x] Analysis, independent review, and `docs/dev/research/agent-efficiency-v2.md`
10. [x] Gates

## Open questions

_(none — every deferral has a named home: `032-unknown-table-error` holds readb's unhelpful
catalog error, `033-skill-discovery-rate` holds the skill's sub-50% discovery rate, and
`028-evaluate-rust-rewrite` remains deliberately out of scope with its answer now better
evidenced.)_

## Sprint summary

Two tasks, both delivered.

`030` inverted the shipped skill's leading example: it opened with `uvx readb …`, so the first
runnable line an agent read failed with `command not found` wherever readb had been installed
without `uv`. A three-surface audit found the defect in the skill alone — the README already
installed first, and the plugin manifests carry no commands — and two mechanical tests now keep
the file's executable surface uniformly bare.

`031` built and ran benchmark v2: four corpora (a messy platform bundle, its tidy control, a
malformed variant rigged so that counting the unparseable files changes which team owns the most
services, and a new task-tracker bundle for an invented product), a 26-question battery across
five pre-registered strata, five arms including a routing-nudge arm kept separate from the base
readb arm, and 783 runs across Sonnet 5 and Haiku 4.5 for $50.92 billed. Nothing was excluded.

**The result is a negative on what was tested and a positive on something adjacent.** None of the
three pre-registered endpoints reached significance: the join-stratum cost advantage is 0.74× but
eight paired questions cannot separate that from parity, the small-bundle stratum is parity exactly
as predicted in advance, and the accuracy endpoint had too few discriminating questions to test at
all. Against an *uncoached* agent, though, readb costs 0.72×/0.75× with intervals excluding parity
and lifts exactness from 85%→97% and 77%→92% — and a coached shell recipe does the same, by the
same margin. The gain is structure, not SQL.

Two review rounds shaped the outcome. The first, on the harness, found twelve defects including a
coached preamble that quoted one of its own answers — a defect v1 shares, now recorded as its
limitation 15 — and 77 runs were deleted so the pre-registration would still precede the first
surviving run. The second, on the write-up, found a hazard table cell that was factually wrong and
contradicted by the analysis file committed beside it; correcting it inverted the finding from "the
warning is a real mitigation" to "the hazard separates models, not tools".

## Session log

- 2026-08-22 — sprint scoped and opened after sprint-004 merged; design for `031` carried in from
  the independent design pass and recorded in the task body.
- 2026-08-22 — `030` designed on the branch: a three-surface audit found the defect in the skill
  alone, the fix inverts the leading example and states the recovery in prose, two mechanical
  tests keep the executable surface bare, and the task is ordered ahead of `031`. Design batch
  approved; both tasks `Designed`, sprint `Implementing`, design merge to `main`.
- 2026-08-22 — `030` implemented and verified hands-on against a readb-without-`uv` PATH: the old
  leading line exits 127 there, the new one returns rows. Implementation of `031` begins.
- 2026-08-22 — `031` built: messy/tidy ops corpora with the rigged malformed flip, the new
  task-tracker corpus on an invented product, the 26-question battery across five strata, the
  five-arm harness with a corpus registry and per-model prices, the analyzer's three
  Holm-corrected endpoints on a pure-stdlib exact test, and 71 harness tests. Pre-registration
  committed before the first measured run. The 783-run matrix is under way.
- 2026-08-22 — independent review of the harness found twelve defects, two of which would have
  corrupted a published number: the coached preamble quoted one of its own answers (v1 has the
  same defect, now recorded as its limitation 15), and an empty `ANSWER:` line scored exactly
  right on the two empty-truth questions. All 77 runs made until then were deleted rather than
  retracted, so the pre-registration still precedes the first measured run; its Revisions section
  lists every correction. The matrix restarted on the corrected harness.
- 2026-08-22 — 783 runs completed, none excluded, $50.92 billed. Write-up drafted, then corrected
  against an independent accuracy check that recomputed every figure from the raw records. Both
  tasks `Designed -> Done`; sprint `Implementing -> Done`; `032` and `033` filed as `Draft` for
  the two product findings the benchmark surfaced. Presented for implementation approval.
