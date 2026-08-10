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

1. [x] Experiment design written into the task body
2. [x] Reviewer round 1 — verdict *not fit to run as written*; five blockers and eleven majors
       folded in as "Design revision 1" (arms, controls, metrics, battery, analysis all changed)
3. [x] Corpus generator + ground truth — 600 concepts, cross-checked by an independent PyYAML
       pass; a second corpus carries 12 files whose frontmatter declares its type but does not
       parse
4. [x] Harness — stream-json transcripts, per-run integrity assertions, cache-invariant cost
5. [x] Pilot runs — three harness faults found and fixed before any measured run
6. [x] Full run — 144 runs (4 arms × 12 questions × 3 repeats); 36 later retracted, see step 9
7. [x] Size sweep at 150 and 2000 concepts (32 runs) — the finding that matters most
8. [x] Reviewer round 2 on the results — every primary table reproduced exactly, but three
       blockers: the skill arm measured a broken environment, the manifest recorded the wrong
       batch, and the published cost basis was the flattering one
9. [x] Corrective runs — skill arm re-measured with `uv` present (36 runs), harness floor
       measured (4 runs)
10. [ ] Reviewer round 3 — verification of the corrections
11. [x] `docs/dev/research/agent-efficiency.md` written and corrected
12. [x] Gates — ruff clean, 188 package tests, 21 harness tests

## Faults the pilots caught (before any measured run)

- **A rigged question.** The baseline counted all four concept types *and* `index.md`'s own
  `type: Index`, and binary scoring called that wrong — the question was silently testing
  knowledge of OKF's reserved-filename rule, which readb encodes and a grep does not. The index
  now carries no `type` key and every arm is told it is a listing, not a concept.
- **A working directory named after the tool.** The new baseline-leak assertion fired on its
  first use: the scratch root sat under a path containing `readb`, which the runtime echoes into
  the agent's system prompt.
- **`--safe-mode` suppresses `--plugin-dir`.** Arm C would have run as arm A under arm C's label.

## Open questions

_(none — every deferral has a named home: `030-skill-uvx-assumption` holds the skill's `uv`
assumption; the unrun conditions are stated as limitations 1, 8 and 9 in the research concept.)_

## Session log

- 2026-08-10 — sprint opened on the branch (scope merge waived), design phase started.
- 2026-08-10 — design reviewed (verdict: not fit to run), rebuilt; corpus, harness and battery
  built; 144-run matrix and 32-run size sweep executed; results audited; skill arm re-measured
  after the audit found its environment broken; write-up corrected. Spend across all batches $25.05.
