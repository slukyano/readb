---
type: Sprint
title: Benchmark v2 — realistic workloads and a second model
description: Build and run the v2 agent-efficiency benchmark — a task-tracker-shaped corpus, 26 pre-registered questions, five arms, Sonnet and Haiku — and fix the shipped skill's uv assumption.
tags:
- research
- benchmarks
timestamp: '2026-08-22T12:30:00Z'
branch: sprint/005
created: '2026-08-22'
status: Implementing
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

- [ ] 030-skill-uvx-assumption — the skill's leading example must work where readb is installed
      and `uv` is not
- [ ] 031-benchmark-v2 — corpora, battery, harness changes, 783 runs, stratified analysis, and a
      second `Research` concept

`030` is ordered first: it lands before the first measured v2 run, so v2 measures the corrected
skill rather than the artifact whose `uv` assumption retracted an arm of v1.

## Implementation checklist

1. [ ] `030` — the skill's leading example, plus the two regression tests that keep it bare
2. [ ] `generate_corpus.py` — messy/tidy styling, the new plants and assertions, the
       malformed-team flip
3. [ ] The backlog corpus generator — invented product, tasks/archive/sprints, mechanical ground
       truth for the body questions
4. [ ] `battery.py` — `record` and `mapping_str` kinds, the `none` convention, `expert_tool`,
       q6 reworded, q14–q18 and b1–b8
5. [ ] `run_benchmark.py` — the `readb-nudged` arm, per-corpus recipes, a corpus registry,
       per-model price tables, recipe preflight, tool-choice and failure recording
6. [ ] `analyze.py` — strata, the three endpoints with exact tests, tool-match matrices, the
       nudge contrast, per-model sections
7. [ ] Tests for all of it, and **pre-registration committed before the first measured run**
8. [ ] Runs — Sonnet and Haiku blocks, floors, messiness sweep
9. [ ] Analysis, independent review, and `docs/dev/research/agent-efficiency-v2.md`
10. [ ] Gates

## Open questions

_(none yet)_

## Session log

- 2026-08-22 — sprint scoped and opened after sprint-004 merged; design for `031` carried in from
  the independent design pass and recorded in the task body.
- 2026-08-22 — `030` designed on the branch: a three-surface audit found the defect in the skill
  alone, the fix inverts the leading example and states the recovery in prose, two mechanical
  tests keep the executable surface bare, and the task is ordered ahead of `031`. Design batch
  approved; both tasks `Designed`, sprint `Implementing`, design merge to `main`.
