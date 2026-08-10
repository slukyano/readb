---
type: Sprint
title: Measure the efficiency claim
description: A single-task sprint — A/B-benchmark an agent over an OKF bundle with and without readb, and record the numbers whichever way they fall.
tags:
- research
- benchmarks
timestamp: '2026-08-10T00:00:00Z'
branch: sprint/004
created: '2026-08-10'
status: Implementing
tasks:
- 024-measure-agent-efficiency
---

Fourth sprint under the [session/sprint workflow](../workflow.md), and the first single-task
sprint.

## Scope rationale

readb's pitch to agents is efficiency: one SQL query instead of many file reads. The README and
the shipped skill both make that claim and no measurement backs it. `024` measures it.

The sprint deliberately carries one task. `028-evaluate-rust-rewrite` — the natural companion,
since it is sequenced behind these numbers — was proposed alongside it and held back, as was the
write-path pair (`016`, `029`); the maintainer trimmed the scope to the measurement alone at
scope approval (2026-08-10).

**A negative result is a result.** If readb does not beat unguided file access on this corpus and
this battery, the measured outcome is published as it stands.

## Process deviations (maintainer instruction, 2026-08-10)

Two gates of the standard lifecycle were explicitly waived for this sprint:

- The **scope-approval commit to `main`** is skipped; this file is committed on `sprint/004`.
- The **design merge to `main`** is skipped; the design phase runs on the branch and flows
  straight into implementation without a separate approval gate.

The close-out gates (validation, hands-on verification, independent review, publication hygiene)
and the final merge approval are unchanged.

The task's approach was set by the maintainer at the same time: design a set of experiments, have
an independent expert reviewer check the design, run them, measure tokens with and without
readb, have the reviewer check the results, and iterate until the reviewer is satisfied.

## Task checklist

- [ ] 024-measure-agent-efficiency — experiment design, corpus generator, harness, runs,
      analysis, and a dated `Research` concept under `docs/dev/research/`

## Implementation checklist

1. [ ] Experiment design written into the task body
2. [ ] Reviewer round 1 — expert review of the design; findings folded in
3. [ ] Corpus generator + ground truth
4. [ ] Harness (per-run token, cost, duration, accuracy capture)
5. [ ] Pilot run — calibrate cost and detect harness faults
6. [ ] Full run
7. [ ] Analysis + reviewer round 2 on the results; iterate until satisfied
8. [ ] `docs/dev/research/agent-efficiency.md` written
9. [ ] Gates

## Open questions

_(none yet)_

## Session log

- 2026-08-10 — sprint opened on the branch (scope merge waived), design phase started.
