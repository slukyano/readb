---
type: Research
title: Does readb still make an agent cheaper when the shell arm is armed and the corpus is messy?
description: A five-arm, two-model benchmark of one agent answering 26 pre-registered questions over four OKF bundles, with three declared endpoints and no pooled headline.
tags:
- benchmarks
- agents
measured: 2026-08-22
created: 2026-08-22
timestamp: '2026-08-22T00:00:00Z'
---

Produced by the backlog task `031-benchmark-v2` (sprint-005), and the direct follow-on from
[v1](agent-efficiency.md). Everything below was fixed before the first measured run and is
recorded in [the pre-registration](agent-efficiency-v2-preregistration.md).

**The numbers describe two models, one agent runtime, four synthetic corpora and one battery, at
three repeats per cell.** Nothing here supports a claim beyond that.

# Method

Identical in structure to v1, and different in six ways — each one addressing a v1 limitation that
could change a conclusion.

## Arms — five

| Arm | Preamble | `PATH` |
| --- | --- | --- |
| `baseline` | orientation only | shims, no readb |
| `shell-coached` | orientation + a worked recipe, one per corpus family | shims, no readb |
| `readb-bare` | orientation + readb syntax (v1's text, unchanged) | + readb |
| `readb-nudged` | `readb-bare` + one frozen routing sentence | + readb |
| `readb-skill` | orientation only; the shipped plugin loaded | + readb + uv |

Every arm is told about `rg`, `jq`, `yq`, `python3`, `perl` and `sqlite3` in identical words, and
every arm has them. v1's first battery ran with `/usr/bin` alone, which handicapped the
file-reading arms specifically.

The coached recipe is **executable data**, not prose: the exact commands an arm is shown are run
against the real corpus before any measured run, and — where the answer is known — checked against
ground truth. A recipe that runs and under-counts would make the competitor a straw man, which is
worth more to readb's ratio than any real effect. v2's corpora are written in mixed styles, so the
coached patterns tolerate quoting and spacing; the preflight confirms they find every file the
ground truth says is there.

`readb-nudged` carries routing guidance as an **arm rather than an edit**, with a retraction rule.
Folding it into `readb-bare` would have silently redefined what v1 measured, and adjusting prompt
text until an agent picks the preferred tool measures the adjusting.

`readb-skill` is interleaved into the main batch; v1 ran it alone and inherited an ordering and
cache-warmth confound. It measures the **corrected** skill — task `030` replaced its `uvx readb`
leading example with the bare binary during this sprint — so its numbers are not comparable to
v1's retracted ones.

## Corpora — four

| Corpus | What it is | Concepts |
| --- | --- | --- |
| `ops` | v1's platform bundle, regenerated **messy** | 600 |
| `ops-malformed` | `ops` + 12 unparseable `type: Service` files | 612 |
| `ops-tidy` | `ops` in one uniform style — the sweep's control | 600 |
| `backlog` | a task-tracker-shaped bundle, new | 192 |

**Messiness** varies how each file is written without changing what it means: quoted scalars,
inline flow sequences beside block ones, shuffled key order, an occasional unknown extra key, a
stray double space after a colon — all seeded per file. Quoting numbers and dates, and drifting key
names, are excluded: those change what a document *means*, and ground truth would become an
interpretation rather than a fact. The `type:` line keeps its canonical rendering, because Q10 is
carried from v1 verbatim and asks for every file containing one.

`ops-malformed`'s twelve files are **rigged so that counting them changes which team owns the most
services**. Without that, a tool which silently skips them still lands on the right team and the
un-warned trap catches nobody.

The `backlog` corpus is a generic engineering backlog for an **invented** self-hosted photo-library
server: tasks and sprints that point at each other, bodies carrying the approach and drop-reason
tokens the body questions extract, and deliberately gapped task numbers so that counting files
answers a different question from asking for the next free number. Nothing in it is drawn from any
real project's backlog. Ground truth for both families is computed from the generation records in
plain Python and then re-derived from the written bytes by an independent PyYAML read-back that
must agree.

## Battery — 26 questions across five strata

| Stratum | What it is | n |
| --- | --- | --- |
| `join` | the answer relates more than one record, or more than one source of fact | 8 |
| `scan` | one type, one pass — a rollup, a group-by, a plain filter | 4 |
| `retrieval` | finding one document among many by what it says | 3 |
| `hazard` | counting things a permissive loader skips | 3 |
| `backlog` | every question on the task-tracker bundle | 8 |

Thirteen ops questions carry v1's wording unchanged, including `q2` (the group-by readb *lost*) and
`q10b` (promoted from v1's post-hoc probes). Only `q6`'s answer template changed: v1 asked for
`ANSWER: team-name=<count>` and three runs answered the literal string `team-name`.

Five ops questions are new — a body-and-frontmatter hybrid, an output-heavy enumeration, a
zero-result filter, a question resting on a field that does not exist, and the malformed trap **with
no warning in its prompt**. Eight backlog questions are new, each modelled on a chore performed
against a real tracker. Two of them need a concept's body, and both ask for a **checkable
extraction** rather than a summary: free prose cannot be scored without an LLM judge, which would
add a second model as a noise source and a standing temptation to tune.

## Endpoints — three, declared in advance

Pooling across 26 questions produces a number set by the battery's composition, so v2 does not
chase one. A power computation on v1's raw data settles why: separating 0.90× from 1.00× on the
pooled coached contrast has 22% power at 12 questions, 51% at 36 and 63% at 48.

| id | Contrast | Model | Scope |
| --- | --- | --- | --- |
| **E1** | billed cost, `readb-bare` vs `shell-coached` | Sonnet 5 | `join` stratum |
| **E2** | billed cost, `readb-bare` vs `shell-coached` | Sonnet 5 | `backlog` stratum |
| **E3** | exactness, `readb-bare` vs `shell-coached` | Haiku 4.5 | every question |

Two-sided Wilcoxon signed-rank by exact sign-flip enumeration, Holm-corrected across the three.
Significance at Holm-adjusted p < 0.05 and no other threshold. **E2 predicted parity** — the
backlog bundle is small enough that runs sit near the harness floor — and that prediction is
recorded in the pre-registration, not fitted afterwards.

Every other figure in this document is descriptive, the pooled coached ratio explicitly so.

## Matrix and prices

783 runs: 390 Sonnet (5 arms), 312 Haiku (4 arms, no skill arm), 27 floors, 54 sweep. Repeats stay
at 3 — v1's within-cell variation is 8.6% against 33% between questions, so repeats buy nothing and
questions are the axis that pays. Arms round-robin inside each repeat and question order rotates
per repeat, so no arm systematically inherits a warm cache.

Prices are each model's published rates on the day of registration. Sonnet 5's introductory $2/$10
has become its standard price, so **v2's absolute dollars are not comparable to v1's**, which used
$3/$15. Every published ratio is a contrast between two arms on the same model, where a uniform
scale cancels.

## What is recorded, beyond v1

Tool choice against each question's declared expert tool (a result, never a reason to edit a
prompt); failed tool results and failed readb calls, read from tool results rather than the call
list; whether readb's skip warning reached the transcript, so an un-warned wrong answer can be told
from a warning that went unread; and whether an `ANSWER` line parsed at all, reported apart from
accuracy.

Dropped from v1 because it measured nothing: the `supported` check, wall clock and output tokens in
the headline, cache-neutral cost as a second headline basis, and the n=1 floor.
