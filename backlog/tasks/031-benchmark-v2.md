---
type: Task
title: Benchmark v2 — realistic workloads, a harder battery, and a second model
description: Extend the agent-efficiency benchmark to a task-tracker-shaped corpus, 26 questions across pre-registered strata, a routing-nudge arm, and Sonnet plus Haiku.
status: Designed
priority: medium
tags:
- research
- benchmarks
created: 2026-08-22
timestamp: '2026-08-22T00:00:00Z'
---

[`024-measure-agent-efficiency`](../archive/024-measure-agent-efficiency.md) (sprint-004) measured
the efficiency claim once and named fifteen limitations doing it. v2 addresses the ones that can
change a conclusion, and drops the parts of v1 that measured nothing.

What v1 established and v2 does not re-litigate: cost tracks turns (`cost ≈ $0.027 + $0.019/turn`,
R² 0.879), readb ingests no less than a shell agent (0.97×), and the advantage lives in
join-shaped questions. What v1 could not answer, and v2 targets:

1. **The comparison against a *coached* shell agent was underpowered** — 0.90× [0.79–1.05].
2. **The corpus was unrealistically regular**, which flattered the shell recipes and so biased
   *against* readb.
3. **No arm had ripgrep or a YAML processor**, for the same reason.
4. **The battery had no realistic-workload shape** — no chore an agent actually performs, and
   nothing requiring a concept's *body* alongside its frontmatter.
5. **One model only.** Every arm scored at ceiling, so accuracy had no variance to show.
6. **The malformed-file hazard was never tested un-warned** — v1's question, and the follow-up
   probe, both told the agent malformed files existed.

## Design

Produced by an independent design pass (2026-08-22) after that reviewer had audited v1, and
approved by the maintainer. Pre-registered: the battery text, the nudge sentence, the strata and
the endpoints are fixed **before the first measured run**, and the v1 discipline — no touching the
scorer after data exists — applies to all of it.

### Arms — five

| Arm | Preamble | PATH |
| --- | --- | --- |
| `baseline` | orientation only | shims, no readb |
| `shell-coached` | orientation + a worked recipe, one per corpus family | shims, no readb |
| `readb-bare` | orientation + readb syntax (v1 text) | + readb |
| `readb-skill` | orientation only; the shipped plugin loaded | + readb + uv |
| `readb-nudged` | `readb-bare` + one frozen routing sentence | + readb |

**The nudge is a separate arm on purpose.** Folding routing guidance into the base readb arm
would silently redefine what v1 measured, and editing prompt text until the tool choice improves
is tuning the benchmark until it flatters readb. The sentence is written once, frozen, and
carries a **retraction rule**: change it after any measured run and every `readb-nudged` run is
flagged `retracted`. The un-nudged arm always runs and is always reported; the nudge's worth is
the pre-registered contrast between them. If it proves valuable, that is a change to the shipped
skill, made afterwards and measured later — not a change to this experiment.

The skill arm is **interleaved into the main batch** this time (v1 ran it alone, and inherited an
ordering and cache-warmth confound).

### Corpora — four

| Corpus | What it is |
| --- | --- |
| `ops` | v1's 600-concept platform bundle, regenerated **messy** |
| `ops-malformed` | `ops` + 12 unparseable `type: Service` files, rigged so that including them **flips which team owns the most services** |
| `ops-tidy` | `ops` with messiness off — the sweep's control |
| `backlog` | new, ~192 concepts: a task-tracker-shaped bundle |

**Messiness** is semantics-preserving and seeded: quoted scalars, inline vs. block lists, shuffled
key order, occasional unknown extra keys, stray double spaces. Excluded deliberately: quoted
numbers and drifting key names, which change meaning and would make ground truth an
interpretation rather than a fact.

The **backlog** corpus is a generic engineering backlog for an **invented product** — a
self-hosted photo-library server. `Task` concepts (`status`, `priority`, `tags`, `blocked_by`) in
`tasks/` and `archive/`, `Sprint` concepts (`status`, `branch`, `tasks`) in `sprints/`, bodies
carrying `## Problem`, `## Design` and `## Outcome` sections. Task numbering has deliberate gaps,
so counting files gives a different answer from taking the maximum.

**Nothing in it is copied from this repository's own `backlog/`, and the write-up must not
present readb as a sprint tool** — the constraint in `AGENTS.md` binds here directly. It is "a
task-tracker-shaped bundle", one plausible OKF domain among others.

Ground truth stays mechanical: the generator records each task's approach and reason tokens, and
an independent PyYAML-plus-regex read-back of the written files must agree. **Free-prose
summarisation is out of scope** — it cannot be scored without an LLM judge, which would add a
second model as a noise source and a standing temptation to tune. Body questions therefore ask
for a *checkable extraction* (which approach a task's design names, why a task was dropped), so
what is measured is the cost of producing a grounded digest, not prose quality.

### Battery — 26 pre-registered questions

Eighteen on the ops corpora: thirteen kept from v1 verbatim (including `q2`, the group-by readb
*loses*, and `q10b`, promoted from a post-hoc probe), plus five new — a body+frontmatter hybrid,
an output-heavy enumeration where readb's turn advantage should compress, a zero-result question,
a false-presupposition question, and **the un-warned malformed trap**, whose prompt never mentions
malformed files and whose corpus is rigged so a naive `GROUP BY` names the wrong team.

Eight on the backlog corpus, all modelled on real chores: which Draft tasks are unblocked and
ready to schedule; what is in the active sprint's scope and what approach each task's design
names; which of a finished sprint's tasks were delivered; which tasks mentioning a feature are
still open; one task's status and priority; a dropped-task digest with reasons; the next free task
number; a tag rollup over mixed inline and block lists.

Scoring gains a `none` convention for empty answers, a `record` kind with literal keys the model
cannot mistake for content (fixing v1's Q6 defect), and a `mapping_str` kind scored by token
containment.

### Strata and endpoints — declared before running

Pooling across all questions produces a number set by the battery's composition, so v2 does not
chase it. A power computation on v1's raw data settles why: separating 0.90× from 1.00× on the
pooled coached contrast has **22% power at 12 questions, 51% at 36, 63% at 48**; 80% would need
80–100 questions, and v2's better shell tooling should shrink the pooled effect further.

Three endpoints instead, Holm-corrected:

- **E1** — billed cost, `readb-bare` vs `shell-coached`, Sonnet, **join stratum** (8 questions
  where v1's effect is 0.46–0.76×). Wilcoxon signed-rank on per-question log-ratios.
- **E2** — the same contrast on the **backlog stratum**. Recorded in advance: that bundle is
  small, so runs sit near the harness floor and compressed ratios are the expected honest
  outcome. Parity here is a finding, not a failure.
- **E3** — **exactness**, `readb-bare` vs `shell-coached`, **Haiku**, all questions. The
  hypothesis worth the money: Haiku's shell pipelines fail on join shapes while Haiku with readb
  holds, because the engine executes logic the model would botch in a pipeline. This is where the
  accuracy dimension finally has variance.

Everything else is descriptive, the pooled coached ratio explicitly so.

### Matrix

| Block | Runs |
| --- | --- |
| Sonnet — 5 arms × 26 questions × 3 | 390 |
| Haiku — 4 arms × 26 questions × 3 | 312 |
| Floors — 9 arm×model combinations × 3 | 27 |
| Messy-vs-tidy sweep — 3 arms × 3 questions × 2 corpora × 3 | 54 |
| **Total** | **783** |

Repeats stay at 3: v1's within-cell variation is 8.6% against 33% between questions, so repeats
buy nothing and questions are the axis that pays. Roughly 2.5–3 hours serial.

### New measurements

- **Tool-choice validation.** Each question declares the tool an expert would use; the harness
  classifies what the agent actually reached for and records whether they matched. Reported as a
  matrix per arm and model — it is a result, never a reason to edit a prompt.
- **Failure counts** — failed commands and failed readb invocations, from tool results. This is
  the retry-rate metric the model comparison needs.
- **Trap diagnostics** — whether a run saw readb's skip warnings, so an un-warned wrong answer
  can be told apart from a warning that did its job.
- **Format compliance** — whether an `ANSWER` line parsed at all, reported separately so Haiku's
  formatting does not silently deflate its accuracy.

### Dropped from v1 because it measured nothing

The `supported` check (at least one tool call — zero failures were structurally guaranteed);
wall clock and output tokens leave the headline tables, kept only where they carry a finding;
cache-neutral cost demoted to an appendix column, since it never disagreed in direction and two
headline bases doubled every sentence; and the n=1 floor, now three repeats per arm and model.

### Public-surface delta

**None.** No CLI command, flag or output format; no Python API name; no config key or on-disk path
read by the tool; no change to the packaged wheel. `benchmarks/` is development material and is
already excluded from the sdist. The one product change this work may *propose* — better routing
guidance in `skills/readb/SKILL.md` — is explicitly out of scope here and would be its own task.
No README figure follows from v2 either, on the same terms as v1.
