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

# Results

**783 runs on 2026-08-22** — 390 Sonnet, 312 Haiku, 27 floors, 54 sweep — for $51.91. **None was
excluded.** No leak into a readb-free arm, no permission denial, no context compaction, no harness
fault, no API error, and every one of the 702 battery runs produced an `ANSWER` line that parsed.

An earlier 77-run batch was **deleted** before any of this, when an independent review found
defects in the instrument. Those corrections are listed in the pre-registration; no data from
before them survives, and none reached a table here.

## The three endpoints

| id | Contrast | Effect | p | Holm p |
| --- | --- | --- | --- | --- |
| **E1** | billed cost, join stratum, Sonnet | 0.74× [0.66–1.41] | 0.4609 | 1.0000 |
| **E2** | billed cost, backlog stratum, Sonnet | 1.02× [0.88–1.30] | 0.4609 | 1.0000 |
| **E3** | exactness, every question, Haiku | 92% vs 92% | — | — |

**No endpoint reaches significance, and none of the three hypotheses is supported.** E1's median
favours readb by a quarter, but eight paired questions cannot separate 0.74× from parity: the
per-question ratios are 0.66, 0.66, 0.67, 0.56 and 0.81 against 1.76, 1.41 and 1.34, and a
signed-rank test on five-against-three does not resolve. E2 is parity, which is what the
pre-registration predicted. E3 has **no test at all**: `readb-bare` and `shell-coached` differ on
fewer than five of the 26 questions, so there is nothing for a paired test to see.

(E1 and E2 share a p-value because their signed-rank statistics happen to have the same magnitude,
|T| = 12, on the same number of pairs. Different data, same cell of a discrete distribution.)

## What the numbers say

**1. readb makes an agent cheaper and more accurate than plain file access — and so does a good
shell recipe, by the same margin.** This is the finding that matters, and it is not the one v1
would have predicted.

| Sonnet 5 | exact | billed | ingested | turns |
| --- | --- | --- | --- | --- |
| `baseline` | 85% | $0.0914 | 11,778 | 6.0 |
| `shell-coached` | 97% | $0.0702 | 10,288 | 3.0 |
| `readb-bare` | 97% | $0.0679 | 10,175 | 4.0 |
| `readb-nudged` | 100% | $0.0668 | 10,152 | 4.0 |
| `readb-skill` | 96% | $0.0792 | 12,384 | 5.0 |

| Haiku 4.5 | exact | billed | ingested | turns |
| --- | --- | --- | --- | --- |
| `baseline` | 77% | $0.0492 | 10,883 | 8.0 |
| `shell-coached` | 92% | $0.0291 | 8,298 | 4.0 |
| `readb-bare` | 92% | $0.0322 | 8,527 | 4.0 |
| `readb-nudged` | 94% | $0.0281 | 8,366 | 3.0 |

Against the uncoached baseline, paired by question, both structured approaches win and their
intervals exclude 1.00:

| vs `baseline` | Sonnet | Haiku |
| --- | --- | --- |
| `readb-bare` | **0.72×** [0.62–0.95] | **0.75×** [0.57–0.89] |
| `shell-coached` | **0.75×** [0.71–0.85] | **0.69×** [0.55–0.78] |

readb against a *coached* shell agent is the contrast the endpoints test, and there it is a wash.
**The gain is structure, not SQL.** An agent told how to attack a directory of frontmatter — by any
means — costs about 30% less and answers 12 to 15 points more accurately than one left to read
files.

**2. There is an accuracy effect this time, and v1 missed it because nothing could fail.** v1
reported no accuracy difference: every arm sat at ceiling on a regular corpus and an easy battery.
v2's baseline drops to 85% on Sonnet and 77% on Haiku, and both structured arms recover it. The
variance came from the harder battery, not from the messier corpus — see finding 6.

**3. The advantage is concentrated in join-shaped work, and it is larger on the weaker model.**
Billed cost against baseline, by stratum:

| stratum | Sonnet `readb-bare` | Sonnet `shell-coached` | Haiku `readb-bare` | Haiku `shell-coached` |
| --- | --- | --- | --- | --- |
| `join` (8) | **0.60×** | 0.71× | **0.38×** | 0.50× |
| `scan` (4) | 0.72× | 0.59× | 0.68× | 0.74× |
| `backlog` (8) | 0.90× | 0.83× | 0.89× | 0.74× |
| `hazard` (3) | 0.69× | 0.74× | 0.79× | 0.80× |
| `retrieval` (3) | 1.02× | 0.86× | 0.99× | 1.00× |

readb loses `retrieval` outright, as designed — finding one document by what it says is a job for
`rg`, and a whole-bundle load is pure overhead. It is weakest on `backlog`, the small bundle, as
E2 predicted.

**4. The nudge changes what the agent reaches for, and not what it costs.** One frozen sentence,
against the un-nudged arm:

| | Sonnet | Haiku |
| --- | --- | --- |
| readb reached for | 83% → 87% | 79% → **91%** |
| exact | 97% → 100% | 92% → 94% |
| paired cost ratio | 1.00× (p = 0.20) | 0.98× (p = 0.11) |
| failed readb calls | 8 → 19 | 7 → 13 |

It routes, and the routing sticks harder on the weaker model — but neither cost ratio moves, and
both arms roughly double their failed readb calls, because the nudge also pushes the agent toward
readb on questions where readb is the wrong tool. Tool-match rate does not improve either (78% →
79% on Sonnet, 78% → 74% on Haiku): the extra readb calls land on questions whose declared expert
tool is not readb. **On this evidence the sentence is not worth adding to the shipped skill.**

**5. The malformed-file warning is a real mitigation whose effect depends on the model.** This is
the sharpest new result. On the un-warned trap, where a naive `GROUP BY` names the wrong team:

| q18, un-warned | `baseline` | `shell-coached` | `readb-bare` | `readb-nudged` |
| --- | --- | --- | --- | --- |
| Sonnet, exact | 67% | 0% | **100%** | **100%** |
| Haiku, exact | 33% | 0% | **0%** | **0%** |

Every readb run on both models **saw** the skip warning (3/3). On Sonnet the agent read it and
corrected; on Haiku it read it and answered anyway. So readb's permissive load is not the silent
hazard v1 assumed — its warning works — but it works only as well as the model reading it, and on
a weaker model **readb plus an unread warning is worse than reading files** (0% against 33%).
`shell-coached` fails the trap on both models for the opposite reason: its recipe never surfaces
the malformed files at all.

By contrast the *warned* versions, q10 and q10b, are answered correctly by every arm on both
models. The warning in the prompt was doing all the work in v1.

**6. Messiness does not matter, which retires a v1 limitation rather than confirming it.** v1
suspected its uniformly-rendered corpus flattered the shell recipes. The sweep says it did not:
running q2, q3 and q15 against both renderings, every messy/tidy cost ratio lands between 0.99×
and 1.06×, except two where the *messy* corpus was cheaper. Exactness is identical on all nine
cells but one. A quote-tolerant shell recipe pays nothing for mixed rendering.

**7. The shipped skill is discovered less than half the time.** `readb-skill` invoked the Skill
tool on 37 of 78 runs and never touched readb at all on 41 — against 13 for `readb-bare`, which
was simply told the syntax. It is the most expensive readb arm (0.87× against baseline, where the
bare arm reaches 0.72×). Making guidance available is not the same as making it used.

## Overhead-subtracted cost

The floor measures the **runtime's** fixed cost under each arm's configuration, not the arm's own
preamble, which is its treatment and is never subtracted. A ratio below 1.00 always moves further
from 1.00 when a constant is removed from both sides, so both rules are shown and neither is
authoritative:

| vs `baseline` | raw | one floor per run | one prompt prefix per turn |
| --- | --- | --- | --- |
| Sonnet `readb-bare` | 0.72× | 0.59× | 0.44× |
| Sonnet `shell-coached` | 0.75× | 0.61× | 0.46× |
| Haiku `readb-bare` | 0.75× | 0.65× | 0.46× |
| Haiku `shell-coached` | 0.69× | 0.55× | 0.30× |

The two arms move together under every rule, which is the point: no subtraction rule turns a wash
into a win.

# What this supports, and what it does not

**Supported.** On these corpora and this battery, at two models: an agent given readb answers
questions about a bundle of frontmatter documents for **0.72× the money on Sonnet and 0.75× on
Haiku** — both intervals excluding parity — and **12 to 15 accuracy points** above an agent left to
read files, with the gain concentrated in questions that relate more than one document. readb's
skip warning is read and acted on by a capable model.

**Not supported.** That readb beats a competently coached shell pipeline. All three pre-registered
endpoints came back at parity or failed to resolve, on a battery twice v1's size. If a reader's
question is *"should this agent use readb rather than `rg` and `yq`?"*, this experiment does not
answer yes. If it is *"should this agent be given some structured way to attack the bundle?"*, it
answers yes emphatically, and readb is one such way — one that needs no recipe written per corpus
family, which the shell arm did need.

**Contradicted.** H3: readb's engine does not hold accuracy where shell pipelines slip. On Haiku
the two are indistinguishable at 92%.

# Deviations from the pre-registration

**None.** Every arm, corpus, question, stratum, endpoint, statistic and exclusion rule is as
registered. The twelve corrections listed in the pre-registration's Revisions section were all made
before the first surviving run, and every run reported here was produced by the corrected harness.

# Limitations

1. **Two models, one runtime, one machine, one day.** As v1.
2. **E1 is underpowered by construction.** Eight paired questions cannot separate a 0.74× median
   from parity. The pre-registration said so in advance and computed why; it remains true.
3. **E3 could not be tested at all.** Fewer than five of 26 questions discriminate the two arms on
   Haiku, so the registered statistic has no pairs to work with. Reported as parity, which is what
   92% against 92% means, but no p-value stands behind it.
4. **Synthetic corpora.** Two families now, both generated, both cross-checked against their own
   bytes — but neither is a corpus anybody actually maintains.
5. **The coached recipe is per corpus family.** `shell-coached` is handed five commands written for
   the bundle in front of it. readb needs none. That is a real advantage this benchmark does not
   price, because both arms are measured on the same questions after the coaching exists.
6. **`readb-skill`'s numbers are the corrected skill's**, not comparable to v1's retracted ones.
7. **Absolute dollars are not comparable to v1's**, which priced Sonnet at $3/$15 before the
   introductory $2/$10 became standard. Ratios are unaffected.
8. **The hazard finding rests on three questions and one rigged corpus.** That readb's warning is
   read on Sonnet and ignored on Haiku is a two-model observation, not a law.
9. **Tool choice is classified by a declared rule**, not by judgement. A run that used `readb` at
   all is labelled `readb`; the `shell`/`read` split turns on whether a command names one file or
   many. The rule is in the pre-registration and was fixed before the runs.
