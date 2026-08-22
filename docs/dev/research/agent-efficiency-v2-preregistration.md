---
type: Research
title: Pre-registration — agent-efficiency benchmark v2
description: Arms, corpora, battery, strata, endpoints, statistics and exclusion rules for the v2 benchmark, fixed before the first measured run.
tags:
- benchmarks
- agents
- preregistration
registered: 2026-08-22
created: 2026-08-22
timestamp: '2026-08-22T00:00:00Z'
---

Produced by the backlog task `031-benchmark-v2` (sprint-005). This document is committed
**before the first measured run of v2**; its commit timestamp is what makes it a pre-registration
rather than a description. Nothing below may be edited once a measured run exists — a change after
that point retracts the runs it affects and says so in the write-up.

[v1](agent-efficiency.md) measured readb's efficiency claim once and published fifteen limitations
alongside the number. v2 addresses the six that can change a conclusion: an underpowered comparison
against the honest competitor, a corpus regular enough to flatter shell pipelines, arms with no
structured search tooling, a battery with no realistic workload and nothing needing a concept's
body, a single model at the accuracy ceiling, and a hazard never tested un-warned.

# What v2 does not re-litigate

Established by v1 and taken as given:

- Cost tracks turns (`cost ≈ $0.027 + $0.019/turn`, R² 0.879).
- readb ingests no less than a shell agent (0.97×).
- The advantage, where there is one, lives in join-shaped questions.

# Hypotheses

| # | Hypothesis | Endpoint |
| --- | --- | --- |
| H1 | On join-shaped questions, readb costs less than a coached shell pipeline. | E1 |
| H2 | On a small, cross-referencing bundle the effect compresses toward parity. | E2 |
| H3 | On a weaker model, readb's engine holds accuracy where shell pipelines slip. | E3 |

H2 is a **prediction of parity**. It is recorded here so that parity, if observed, is reported as
the predicted outcome rather than reframed after the fact.

# Arms — five

| Arm | Preamble | `PATH` |
| --- | --- | --- |
| `baseline` | orientation only | shims, no readb |
| `shell-coached` | orientation + a worked recipe, one per corpus family | shims, no readb |
| `readb-bare` | orientation + readb syntax (v1's text, unchanged) | + readb |
| `readb-nudged` | `readb-bare` + one frozen routing sentence | + readb |
| `readb-skill` | orientation only; the shipped plugin loaded | + readb + uv |

Every arm is told, in identical words, about the tools every arm has (`rg`, `jq`, `yq`, `python3`,
`perl`, `sqlite3`). `readb-skill` is interleaved into the main batch; v1 ran it alone and inherited
an ordering and cache-warmth confound.

`uv` reaches `readb-skill` alone, now as insurance rather than as a requirement: the shipped
skill's leading example was `uvx readb …` until task `030` landed, and it now invokes the bare
binary. v2 therefore measures the **corrected** skill, and its skill numbers are not comparable to
v1's retracted ones.

## The nudge, frozen

> When a question is about many documents at once — counting them, filtering them, grouping them,
> or relating one kind of document to another — a single `readb query` is usually cheaper than
> reading or searching the files.

Routing guidance is an **arm, not an edit**. Folding it into `readb-bare` would silently redefine
what v1 measured, and adjusting prompt text until an agent picks the tool the experimenter prefers
is tuning the benchmark until it flatters the tool. The un-nudged arm is always run and always
reported.

**Retraction rule:** if that sentence changes after any measured run, every `readb-nudged` record
produced before the change is flagged `retracted` and re-measured. If the nudge proves valuable,
that is an argument for changing the shipped skill — a separate task, measured separately, never a
change to this experiment.

# Corpora — four

| Corpus | What it is | Concepts |
| --- | --- | --- |
| `ops` | v1's platform bundle, regenerated **messy** | 600 |
| `ops-malformed` | `ops` + 12 unparseable `type: Service` files | 612 |
| `ops-tidy` | `ops` rendered in one uniform style — the sweep's control | 600 |
| `backlog` | a task-tracker-shaped bundle, new | 192 |

**Messiness** is semantics-preserving and seeded per file: quoted scalars, inline flow sequences
beside block ones, shuffled key order, an occasional unknown extra key, a stray double space after
a colon. Deliberately excluded: quoting numbers and dates, and drifting key names — those change
what a document *means*, and ground truth would become an interpretation rather than a fact. The
`type:` line keeps its canonical rendering, because Q10 is carried from v1 verbatim and asks for
every file containing one; padding or quoting that line would quietly change what a pre-registered
question means.

`ops-malformed`'s twelve files are **rigged so that counting them changes which team owns the most
services**. Without that, a tool which silently skips them still lands on the right team and the
un-warned trap catches nobody. Generation asserts the flip.

The `backlog` corpus is a generic engineering backlog for an **invented** self-hosted photo-library
server. Nothing in it is drawn from any real project's backlog; it is one plausible OKF domain
among many, chosen because a task tracker is the commonest place a directory of frontmatter
documents actually arises. Task numbers have deliberate gaps, so counting the files gives a
different answer from asking for the next free number.

Ground truth for both families is computed from the generation records in plain Python and then
re-derived from the written bytes by an independent PyYAML read-back that must agree. **Free-prose
summarisation is out of scope**: it cannot be scored without an LLM judge, which would add a second
model as a noise source and a standing temptation to tune. The two body questions therefore ask for
a **checkable extraction** — which approach a task's design names, why a task was dropped — so what
is measured is the cost of producing a grounded digest, not prose quality.

# Battery — 26 questions

Eighteen on the ops corpora, eight on the backlog corpus. Thirteen ops questions carry v1's wording
unchanged, including `q2` (the group-by readb *lost*) and `q10b` (promoted from v1's post-hoc
probes). Only `q6`'s **answer template** changed: v1 asked for `ANSWER: team-name=<count>` and three
runs answered the literal string `team-name`. The fix is a template whose field names are obviously
field names, not a looser scorer.

Five ops questions are new: a body-and-frontmatter hybrid neither half answers, an output-heavy
enumeration where a turn advantage should be diluted by the cost of writing the answer out, a
filter with no matches, a question resting on a field that does not exist, and **the malformed trap
with no warning in its prompt**.

Eight backlog questions are new, each modelled on a chore performed against a real tracker:
ready-to-schedule work, the active sprint's scope and the approach each design names, what a
finished sprint delivered, open work touching one feature, one task's status and priority, a
dropped-task digest with reasons, the next free task number, and a tag rollup over mixed inline and
block lists.

Scoring gains a `none` convention for empty answers, a `record` kind with literal field names, and
a `mapping_str` kind scored by token containment. The normalizer, the question text, the declared
strata and the declared expert tool are all fixed here.

## Strata — they partition the battery

| Stratum | What it is | n |
| --- | --- | --- |
| `join` | the answer relates more than one record, or more than one source of fact | 8 |
| `scan` | one type, one pass — a rollup, a group-by, a plain filter | 4 |
| `retrieval` | finding one document among many by what it says | 3 |
| `hazard` | counting things a permissive loader skips | 3 |
| `backlog` | every question on the task-tracker bundle | 8 |

# Endpoints — three, Holm-corrected

Pooling across all 26 questions produces a number set by the battery's composition, so v2 does not
chase one. A power computation on v1's raw data settles why: separating 0.90× from 1.00× on the
pooled coached contrast has **22% power at 12 questions, 51% at 36, 63% at 48**; 80% would need
80–100, and v2's better shell tooling should shrink the pooled effect further.

| id | Contrast | Model | Scope | Statistic |
| --- | --- | --- | --- | --- |
| **E1** | billed cost, `readb-bare` vs `shell-coached` | Sonnet 5 | `join` stratum | Wilcoxon signed-rank on per-question log-ratios |
| **E2** | billed cost, `readb-bare` vs `shell-coached` | Sonnet 5 | `backlog` stratum | Wilcoxon signed-rank on per-question log-ratios |
| **E3** | exactness, `readb-bare` vs `shell-coached` | Haiku 4.5 | every question | Wilcoxon signed-rank on per-question exactness differences |

The test is two-sided, by **exact sign-flip enumeration** of the signed-rank statistic (average
ranks for ties, zero differences dropped); above eighteen non-zero pairs it becomes a seeded Monte
Carlo over the same null and the output says so. The three p-values are corrected together by
Holm-Bonferroni. **Significance is declared at Holm-adjusted p < 0.05, and at no other threshold.**

Every other figure this benchmark publishes is **descriptive**, the pooled coached ratio explicitly
so. The comparator for all three endpoints is `shell-coached`, never `baseline`, and never the
nudged arm — that contrast is its own, reported separately and not part of the correction.

# Matrix

| Block | Runs |
| --- | --- |
| Sonnet 5 — 5 arms × 26 questions × 3 | 390 |
| Haiku 4.5 — 4 arms × 26 questions × 3 | 312 |
| Floors — 9 arm×model combinations × 3 | 27 |
| Messy-vs-tidy sweep — 3 arms × 3 questions × 2 corpora × 3 | 54 |
| **Total** | **783** |

The Haiku block omits `readb-skill`: the skill arm exists to measure a shipped artifact on the
model that artifact is written for, and adding it would buy a fourth cell of an arm no endpoint
uses. Repeats stay at 3 — v1's within-cell variation is 8.6% against 33% between questions, so
repeats buy nothing and questions are the axis that pays.

The floor block replaces every question with a trivial prompt through the identical harness, to
measure the fixed overhead both arms pay before any work happens.

The sweep runs `baseline`, `shell-coached` and `readb-bare` on **`q2`, `q3` and `q15`** against both
`ops` and `ops-tidy`. `q2` and `q3` filter on string values, which messiness may quote; `q15`
filters on `tier`, a number, which messiness never quotes — so the third question is a control
inside the sweep, and a sweep effect that shows up on it too is not an effect of quoting.

Arms round-robin inside each repeat and the question order rotates per repeat, so no arm
systematically inherits a warm cache or a quiet machine.

# Prices

USD per million tokens, at the rates published on the day of registration. Sonnet 5's introductory
$2/$10 has become its standard price, so **v2's absolute dollar figures are not comparable to
v1's**, which used $3/$15. Every published ratio is a contrast between two arms on the same model,
where a uniform scale cancels, so no ratio is affected.

| Model | Input | 5m cache write | 1h cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| `claude-sonnet-5` | $2.00 | $2.50 | $4.00 | $0.20 | $10.00 |
| `claude-haiku-4-5` | $1.00 | $1.25 | $2.00 | $0.10 | $5.00 |

# What is recorded, beyond v1

- **Tool choice.** Each question declares the tool an expert would reach for; the harness
  classifies what the agent actually used (`readb` outright if it ran readb at all, otherwise
  searching or reading by which it did more of, ties to searching). Reported as a matrix per arm
  and model. **It is a result, never a reason to edit a prompt.**
- **Failure counts** — failed tool results, and failed readb calls specifically, read from tool
  results rather than from the call list.
- **Trap diagnostics** — whether readb's skip warning reached the transcript, so an un-warned wrong
  answer can be told apart from a warning that went unread.
- **Format compliance** — whether an `ANSWER` line parsed at all, reported apart from accuracy so a
  weaker model's formatting does not silently deflate its score.

# Dropped from v1 because it measured nothing

The `supported` check (at least one tool call — zero failures were structurally guaranteed); wall
clock and output tokens leave the headline tables; cache-neutral cost is demoted to an appendix,
having never disagreed with billed cost in direction; and the n=1 floor becomes three repeats per
arm and model.

# Exclusion rules

A run's numbers are not used when, and only when, it is flagged `retracted`, the harness errored or
timed out, the runtime reported an error, readb leaked into a readb-free arm, or a permission was
denied mid-run. Every exclusion is listed by arm, question and repeat in the analysis output. No
run is excluded for being an outlier.

# Deviations

Any departure from this document is listed in the write-up under its own heading, with what changed
and why. An empty list is itself a claim, and is stated as one.
