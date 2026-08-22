---
type: Research
title: Does readb make an agent cheaper or faster than plain file access?
description: A four-arm benchmark of one agent answering twelve questions over a 600-concept OKF bundle, with and without readb. Measured, not asserted.
tags:
- benchmarks
- agents
measured: 2026-08-10
probed: 2026-08-21
created: 2026-08-10
timestamp: '2026-08-21T00:00:00Z'
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

Q10 is the sharpest of these: readb's permissive load **drops a malformed file from the result**,
so `SELECT count(*) FROM service` returns 180 where `grep` finds 192. It is not silent about it —
one warning per skipped file goes to stderr, which finding 9 shows an agent reads and acts on. The
question asks for the count including them, in every arm's prompt.

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
- Full stream transcripts are captured, which is what makes the integrity checks above possible
  at all: each check runs against the transcript as the run is recorded, and its verdict is
  stored on the run's record. Neither the transcripts nor the per-run records are committed —
  see *Reproducing* — so the checks' verdicts, not their raw inputs, are what this repository
  keeps.

## Metrics

| Metric | Definition |
| --- | --- |
| **Cost, as billed** | Recomputed from token counts at cache prices, against a price table committed with the results. Tracks the runtime's own `total_cost_usd` to a median 0.8% (see limitation 14), which is the check that the table is right. **The headline.** |
| Cost, cache-neutral | The same recomputation with every input token priced as fresh. Reported beside the billed figure because the two disagree, and quoting only the flattering one would be dishonest. |
| New tokens ingested | `input + cache_creation` — content the agent had to pull in, as opposed to prompt prefix re-sent from cache. |
| Cumulative prompt tokens | All input counts summed over turns. Turn-driven: each turn re-sends the whole prefix. |
| Wall clock | Harness-measured, cross-checked against the runtime's own duration. |
| Turns, readb invocations | From the transcript. |
| Exactness / partial credit | Binary set-equality, plus F1, against a normalizer fixed before the first run. |

The two cost bases are not a rescaling of one another. Cache reads are about 92% of all prompt
tokens here and are billed at a tenth of fresh input, so pricing them as fresh inflates the arms
unevenly — hardest for whichever arm takes more turns. Both are published throughout.

Comparisons are **paired by question**: per-question median per arm, then the ratio, then the
median ratio across the twelve questions, with a percentile bootstrap interval resampled over
questions. Between-question variance dominates between-repeat variance here, so a figure pooled
across shapes would mostly report the battery's composition.

## The floor

Four runs put a trivial prompt through the identical harness, one per arm. They measure what a
run costs before any work happens:

| | Billed | Cache-neutral | Ingested | Cumulative prompt tokens | Turns |
| --- | --- | --- | --- | --- | --- |
| Floor, per arm | $0.053 | $0.087 | 7,741 | 29,024 | 1 |

The arms are indistinguishable at the floor; `readb-skill` carries 108 extra tokens, the shipped
skill's always-on description. **This floor is roughly half of a median run's billed cost**, and
it is paid identically by every arm, so every ratio below is diluted toward 1.00 by a constant
that has nothing to do with readb. Floor-subtracted ratios are given alongside the raw ones.

# Results

144 runs (4 arms × 12 questions × 3 repeats) on 2026-08-10, plus a 36-run re-measurement of the
skill arm, a 32-run size sweep, 4 floor runs and a 6-run post-hoc probe. Total spend across
every batch, including the retracted one, $25.66.

**36 of the 144 are excluded** — the whole first `readb-skill` arm, retracted for the environment
defect in finding 6. Those records were flagged `retracted` and the analyzer drops them; the
arm's published numbers come from the re-measurement. Of the 108 that remain, **none**
was excluded for any other reason: no leak into a readb-free arm, no permission denial, no
context compaction, no harness fault.

Two caveats about that clean sheet, since a control that cannot fail is not evidence: the
"unsupported answer" check is `at least one tool call`, which nothing in this battery could
plausibly fail, and compaction was effectively disabled by setting `--autocompact` to its
maximum identically in every arm. Neither says as much as its zero suggests. The checks that did
have teeth are the readb-leak assertion (0 hits across 72 readb-free runs) and the skill
isolation (the plugin appears in the skill arm's initialisation and nowhere else).

## Headline

| Arm | Exact | Billed | Cache-neutral | Ingested | Wall clock | Output | Turns |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `baseline` | 97% | $0.101 | $0.370 | 9,739 | 11.4 s | 453 | 4.0 |
| `shell-coached` | 100% | $0.098 | $0.368 | 9,051 | 11.8 s | 512 | 4.0 |
| `readb-bare` | 94% | $0.088 | $0.278 | 9,542 | 10.6 s | 338 | 3.0 |
| `readb-skill` | 100% | $0.116 | $0.391 | 12,041 | 12.0 s | 431 | 5.0 |

Medians across the arm. Ratios paired by question, with a percentile bootstrap interval over
questions:

| Arm vs `baseline` | Billed | Billed, floor-subtracted | Cache-neutral | Ingested | Wall clock | Output | Turns |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `shell-coached` | 0.96× [0.87–1.00] | 0.93× | 0.99× [0.79–1.02] | 0.95× [0.91–0.97] | 0.95× [0.79–1.16] | 0.98× [0.70–1.04] | 1.00× [0.79–1.00] |
| `readb-bare` | **0.87×** [0.75–0.97] | **0.76×** | 0.76× [0.62–1.00] | 0.97× [0.85–1.02] | 1.03× [0.70–1.20] | 0.65× [0.43–0.96] | 0.75× [0.62–1.00] |
| `readb-skill` | 1.01× [0.89–1.18] | 1.00× | 1.00× [0.81–1.06] | 1.04× [0.97–1.28] | 1.03× [0.82–1.16] | **0.70×** [0.58–0.94] | 1.00× [0.88–1.29] |

`readb-skill`'s row comes from the re-measurement described in finding 6, paired against the main
matrix's baseline question by question exactly as the other rows are.

## What the numbers say

**1. There is no accuracy effect.** Every arm answered every question shape correctly, including
the two the tool was expected to fail. The three misses in the whole matrix are all Q6 and all a
defect in that question's answer template (below), not a difference in capability. On this corpus
and battery, readb does not make an agent more right — the file-reading arms were not struggling.

**2. The cost saving is real but modest, and how large depends on the basis.** In money,
`readb-bare` costs **13% less** than the baseline (0.87×, interval [0.75–0.97], which does not
cross 1.00). On a cache-neutral basis it is 0.76×, with an interval [0.62–1.001] that does cross
1.00. Subtracting one harness floor per run — the half of every run that is fixed overhead —
the money figure becomes 0.76×.

That last figure needs its rule stated, because it is a choice rather than a correction: a ratio
below 1.00 always moves further from 1.00 when the same constant is removed from both sides. The
rule used is **one floor per run**, which treats the fixed overhead as belonging to neither arm.
A different defensible rule — subtracting one prompt prefix per *turn*, since extra turns are
caused by the approach and their re-sends arguably belong to it — puts the figure back at
**0.89×**, indistinguishable from the raw 0.87×. Both rules are emitted by
`analyze.py --floor`, neither as the authoritative one. So the honest short statement is: **13% less in
money; up to 24% less if the fixed harness overhead is treated as attributable to neither arm — a
choice, not a measurement.**

**3. The saving comes from fewer turns, not from reading less.** New tokens ingested is 0.97× —
nothing. What changes is turn count (0.75×), and since each turn re-sends the whole prompt
prefix, cumulative prompt tokens fall with it (0.76×). Decomposing the cache-neutral cost
difference: **98% of it is prompt tokens, 2% is output.** Output does drop sharply (0.65×), which
is a real behavioural difference — readb answers are short — but output is 2% of the bill and
contributes almost nothing to the saving. readb does not save an agent from reading the bundle;
it saves the agent from *writing* shell pipelines.

**4. Wall clock does not improve** (1.03×, interval spanning 0.70–1.20). readb loads and discards
the whole bundle on every invocation — 0.80–0.89 s for 600 concepts on this machine against roughly
10 ms for a grep — and that overhead cancels the turns it saves.

**5. The effect is concentrated in join-shaped questions.** Per-question billed cost ratio,
`readb-bare` against `baseline` and against `shell-coached`:

| Question | Shape | vs `baseline` | vs `shell-coached` | |
| --- | --- | --- | --- | --- |
| Q8 | Three-predicate multi-hop | **0.46×** | **0.46×** | readb wins decisively |
| Q4 | Cross-reference between types | **0.54×** | 0.70× | |
| Q3 | Filtered listing | 0.66× | 0.76× | |
| Q6, Q12, Q5 | Extremum, session, membership | 0.83–0.87× | 0.81–0.87× | |
| Q11, Q10 | Fuzzy retrieval, malformed count | 0.87–0.89× | 0.93×, **1.84×** | |
| Q1, Q9, Q7 | Rollup, single file, needle | 0.97–1.01× | 1.00–1.10× | parity |
| Q2 | Group-by on one field | **1.15×** | **1.21×** | readb loses |

Grouped by the shape each question was declared to favour *before* the runs, the billed ratios
are: **sql-shaped 0.83× (7 questions), file-shaped 0.93× (4), neutral 0.85× (1)**. The headline
therefore tracks the battery's composition — a battery with fewer join questions would show less.

Q2 is the instructive loss: `grep -h '^status:' … | sort | uniq -c` is a one-liner an agent writes
without hesitation, and paying a bundle load to run `GROUP BY` costs more than it saves. readb
earns its keep where a shell pipeline needs a *join* — Q4 and Q8, where the baseline spent ten and
nine turns debugging nested `awk` loops against readb's four and three.

**6. The skill arm had to be measured twice, and the first measurement was wrong.** The shipped
`skills/readb/SKILL.md` leads with `uvx readb query …`. The first batch put `readb` on that arm's
PATH but not `uv`, so 17 of 36 runs issued a command that failed with exit 127 and spent extra
turns recovering; the arm came out at 1.21× the baseline's cost, and that number was briefly
written up as "the shipped skill costs more than it saves". It was an artefact of the
environment. Re-run with `uv` present, the skill arm sits at **1.01× billed, 1.00× cache-neutral
— parity with doing nothing.** The skill fired in 28 of 36 runs in both batches, and sensibly:
in the re-measured batch, never on the exact-phrase needle or the single-file lookup, and once on
fuzzy retrieval.

Parity in cost is not parity in behaviour, though. The skill arm's **output drops to 0.70×** the
baseline's — close to `readb-bare`'s 0.65× — so the skill does change what the agent writes even
where it does not change what the run costs. It buys `readb-bare`'s terseness and spends the
saving on discovering and reading itself.

(The "17 of 36" figure above was measured during the adversarial audit of the first batch. Those
runs were flagged `retracted` and excluded from every table here.)

The artefact is worth keeping as a finding in its own right, because it is not confined to a
benchmark: **the skill's leading example fails on any machine where readb is installed but `uv`
is not.** That is now backlog task `030-skill-uvx-assumption`.

**7. Coaching alone changes little.** `shell-coached` sits at 0.96× the baseline's billed cost
(0.93× floor-subtracted). A worked `grep`/`awk` recipe buys a few percent, so readb's advantage
is not an artefact of being told what to do.

Against the coached arm directly, though, the saving is **not established at this n**:
**0.90× billed [0.79–1.05]** and 0.76× cache-neutral [0.60–1.01] — both intervals cross 1.00.
By the criterion finding 2 uses, the cost saving is demonstrated against the *uncoached*
baseline and only *consistent with* a saving against the arm this document itself calls readb's
honest competitor. The point estimates agree with the headline; the evidence behind them is
weaker, and twelve questions at three repeats cannot separate 0.90× from 1.00×.

**8. An agent given readb often declines to use it — correctly.** In 12 of 36 `readb-bare` runs
no readb command was issued, and those 12 are exactly the four file-favouring questions (Q7, Q9,
Q10, Q11, 3/3 each). The tool choice was right every time: on those shapes readb offers nothing.

**9. The malformed-file trap never sprang, and a follow-up probe explains why.** Q10 asks for a
count that includes 12 files whose frontmatter does not parse — where `SELECT count(*) FROM
service` returns 180 and `grep` finds 192. Every arm answered 192. In the main matrix the readb
arms answered it by reaching for `grep`, never invoking readb at all, so the question left open
whether an agent that *did* use readb would be misled.

A post-hoc probe settled it (`q10b`, outside the pre-registered battery): the same question,
same corpus, same arms, rephrased from file-and-text language into concept-and-field language —
*"How many `Service` concepts does this knowledge base contain? Count every concept whose `type`
is `Service`, including any whose frontmatter is malformed."* Phrasing alone flipped the tool
choice: `readb-bare` invoked readb in **3 of 3** runs, against 0 of 3 on the original wording.

It still answered 192, every time. readb is not silent about what it drops: the first command is
`readb schema`, and readb writes one warning per unparseable file to stderr:

```
skipping services/svc-9001-edge-collector.md: malformed YAML frontmatter
  (while parsing a flow sequence … tags: [cost, broken …)
```

The agent read those warnings, ran the query anyway, saw 180, cross-checked against
`ls corpus/services | wc -l` → 192, confirmed all 12 skipped files declare `type: Service`, and
answered 192 with the arithmetic shown. The permissive-load contract is silent in the *result set*
but not in the *process output*.

**What the probe does and does not establish.** It shows that an agent using readb on this
question reached the right answer, and that readb's warnings were present and read. It does
**not** isolate those warnings as the cause: the probe's own prompt says "including any whose
frontmatter is malformed", which pre-warns every arm, and all three runs cross-checked with
`ls`/`grep` independently. Establishing the mechanism needs a wording that does not mention
malformed files at all. The tool-choice flip is 3/3 against 0/3 — suggestive, but Fisher's exact
gives p≈0.10 at this n, so read it as a signal, not a settled effect.

On the rephrased question readb is also the cheaper tool — `readb-bare` at **0.65×** the
baseline's cost within the probe, against 0.87× on the original wording in the main matrix. That
cross-batch comparison is loose: the probe ran on a later runtime build (2.1.239 against the
matrix's 2.1.226), under a billing regime reporting 0.676× list (limitation 13), and with `uv` on
the readb arm's `PATH` where the matrix had none. The within-probe ratio is sound; reading it
against the matrix's 0.87× is indicative only.

## Size sweep

The main matrix runs at one size. A separate sweep repeats the four query-shaped questions
(Q3, Q4, Q8, Q12) at 150 and 2000 concepts, `baseline` against `readb-bare`, two repeats — 32
additional runs. The 600 row below is **not** from that sweep: it is the main matrix's subset of
the same four questions, at three repeats, recorded 40 minutes earlier in a different batch. The
three sizes were not measured identically, and the middle row is the odd one out.

Every answer in the sweep was correct in both arms at every size.

| Concepts | n per cell | `baseline` billed | `readb-bare` billed | Billed ratio | Cache-neutral ratio |
| --- | --- | --- | --- | --- | --- |
| 150 | 2 | $0.108–0.213 | $0.084–0.090 | 0.70× | 0.51× |
| 600 | 3 | $0.103–0.192 | $0.086–0.101 | 0.60× | 0.44× |
| 2000 | 2 | $0.121–0.291 | $0.087–0.099 | **0.43×** | **0.29×** |

Ranges are the spread of per-question medians at that size; ratios are the median across the four
questions. At n=2 a "median" is the mean of two runs, and no interval is meaningful — read the
sweep as a direction, not a measurement.

**readb's cost barely moves with corpus size; the baseline's does.** Across a 13× growth in the
bundle, `readb-bare`'s billed cost stayed inside $0.084–0.101 while the baseline's top question
climbed from $0.21 to $0.29. Its cumulative prompt tokens are steadier still — 90,672–91,270 at
2000 concepts, within 1% of the 150-concept median.

The honest reading of that stability is narrower than it looks. `readb-bare` is sitting close to
the harness floor at every size: its cost is set by **neither** the corpus nor the answer, but by
the fixed overhead of a run that takes three turns. The baseline's cost grows — but this design
cannot say whether it grows with the corpus or with the answer, because the answer sets grow
alongside the corpus (Q8's correct answer is 1 name at 150 concepts, 10 at 600, 45 at 2000).
Separating those two would need a fourth corpus holding answer size fixed while the bundle grows.

Wall clock behaves the same way and crosses over: at 2000 concepts the baseline's slowest sweep
run took 70 s against `readb-bare`'s worst of 24 s. The exception is Q12, the five-part session,
where readb *loses* wall clock at 2000 — five queries mean five full bundle loads. Measured load
time for a single `readb query` on this machine:

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
literally — `team-name=31`, `team-name=platform=31`, `team-name=platform, count=31`. In all three
the surrounding prose names the right team and the right count; one of the three ANSWER lines
(`team-name=31`) omits the team itself. The pre-registered scorer marked all three wrong, and
they are left marked wrong rather than re-scored after the fact.

Two of the three are `readb-bare` runs, which is why the published accuracy column reads
baseline 97% against `readb-bare` 94% — an ordering that invites exactly the opposite inference
from the one the transcripts support. Excluding Q6, every arm is at **100%**. The placeholder
should have been a shape the model could not mistake for an answer.

# What this supports, and what it does not

**Supported by the measurement:**

- On a 600-concept bundle, an agent told that readb exists spends **13% less money** per question
  than one working from files (0.87×, [0.75–0.97]) — 24% less once the fixed harness overhead is
  subtracted, or on a cache-neutral basis. The four-question sweep points to the gap widening
  with bundle size, to 0.43× billed at 2000 concepts.
- The saving comes from **fewer turns**. Ingestion is unchanged (0.97×), and output, though it
  drops sharply, is 2% of the bill. The agent stops writing and debugging shell pipelines.
- readb's cost barely moves with bundle size, though at these sizes it is sitting near the
  harness floor, so that stability says less than it appears to.
- The advantage is concentrated in questions needing a **join or several predicates**. On
  single-field group-bys, single-file lookups and exact-phrase searches, readb is at parity or
  worse — 1.15× on the group-by.
- An agent given readb picks correctly when to use it, and skips it on shapes where files win.
- The shipped skill is at **parity** with not having it (1.01× billed): it neither pays for
  itself nor costs anything, on this battery.
- The skill's leading example, `uvx readb`, fails wherever readb is installed but `uv` is not.

**Not supported, and not claimed:**

- No accuracy benefit was observed. Every arm answered every shape correctly.
- No wall-clock benefit at 600 concepts (1.03×). The sweep suggests one at 2000, but reverses for
  repeated queries in one session.
- Nothing about other models, other agent runtimes, or real (non-synthetic) bundles.
- No statistical significance claim. Three repeats support medians and approximate intervals;
  the cache-neutral cost interval crosses 1.00 (upper bound 1.001), the sweep's n=2 cells support
  a direction only, and **against the coached arm the billed interval crosses 1.00 as well**
  (0.90× [0.79–1.05]) — the saving is established against the uncoached baseline, not against a
  coached one.
- No equivalence claim on accuracy. Every arm scored at ceiling, and a battery nobody fails
  cannot detect a difference; "no accuracy effect" here is absence of evidence, not evidence of
  absence.
- Whether the baseline's cost grows with the corpus or with the answer size — the sweep confounds
  them.
- No README figure follows from this document. Publishing a headline number needs a follow-up
  that re-runs the pre-registered analysis, ideally on a second day and a real bundle.

# Limitations

1. **One model, one runtime, one machine, one day.** The wall-clock noise floor was not
   established by a second measurement block.
2. **Synthetic corpus.** Generator and seed are committed, but every frontmatter key is written
   as one greppable `key: value` line, far more regular than a real bundle. That regularity
   flatters the `grep`/`awk` recipes specifically — a messier corpus would break them more often
   than it would break SQL — so this most likely biases *against* readb.
3. **The battery is author-written.** Twelve questions, five of them chosen specifically to be
   hard for readb, but the selection is still not neutral. Per-question results are published so
   the composition can be judged. Four shapes that could move the conclusion are absent: a
   **body-and-frontmatter hybrid** ("which tier-1 services' runbooks mention X"), which is the
   most realistic genuinely contested case since readb exposes `__body`; an **output-heavy
   enumeration** (list all 180 services with owner and tier), where readb's turn advantage should
   shrink; a **zero-result or false-presupposition** question; and anything exercising **real
   bundle messiness** — quoted values, inline versus block lists, drifting key names. Every
   question also names the exact field names, which coaches all arms equally but unrealistically.
4. **Read path only.** `readb set` is not exercised; nothing here speaks to the write path.
5. **n = 3** in the main matrix, **n = 2** in the sweep, and **n = 1 per arm** for the floor —
   so the floor-subtracted figures rest on a single measurement each. The bootstrap resamples
   *questions* only, ignoring within-question uncertainty, and a percentile bootstrap of a median
   over twelve points undercovers its nominal level: read every interval as approximate and
   narrower than honest. The headline's direction survives a cruder test that makes no such
   assumption — 10 of 12 questions fall below 1.00 (sign test p≈0.04).
6. **Q6's answer template was defective**, as described above.
7. **The cost model is a recomputation**, not an invoice: token counts times a committed price
   table. It tracks the runtime's own figure to a median 0.8% (limitation 14), which is the
   check that the table is right.
8. **Designed conditions that were never run, and controls quietly dropped.** Arms measuring the
   skill's *content* separately from its *discovery*, and a cross-check
   against the runtime's own plugin-evaluation harness, were designed but not run. Three controls
   the design promised were also dropped without being renegotiated: a read-only corpus (mode
   `555`/`444`), two discarded warmup runs, and a sweep at 120 concepts — the sweep ran at 150.
   None affects a published number, but the design should have been corrected rather than
   quietly diverged from.
9. **The skill arm was never interleaved.** Every other arm's runs are round-robined against the
   others; `skill_uv` ran alone, 09:12–09:20, against a baseline measured 08:06–08:44. Its
   comparison therefore carries an ordering and cache-warmth confound the matrix was built to
   avoid.
10. **No arm had `Grep` or `Glob`.** In this runtime build they are deferred tools reached through
   a search step, and no run reached for them. Across the 144 published runs (108 main matrix
   plus the 36 re-measured skill runs) the records counted **453 tool calls**, and the 128 runs
   whose transcripts were still intact at the time of counting broke down as `Bash` 357,
   `Skill` 28, `Read` 5 — nothing else.
   Every arm was therefore an agent with a shell, not an agent with native structured search. This is identical across arms, but structured search returns
   truncated, pre-formatted results rather than piping raw text into the context, so its absence
   plausibly *inflates* the file-reading arms' cost. The measured gap is an upper bound on
   readb's advantage over a fully-equipped agent.
11. **Half of every measured run is fixed overhead** — $0.053 of a $0.088–0.101 median. Absolute
    figures here are not "the cost of answering a question with readb"; they are that cost plus a
    constant, and the constant dilutes every ratio toward 1.00.
12. **The raw per-run records and transcripts are not committed.** They were, and it went badly:
    the transcript directory was flat until batches were namespaced, so each batch that reused an
    (arm, question, repeat) cell overwrote an earlier batch's evidence, and 68 published runs lost
    their tool-level detail before anyone noticed. Weighed against 4 MB of a public repository and
    a third party's runtime internals published verbatim, the raw output is no longer kept — the
    aggregated analyses and the per-batch manifests are, and the harness plus the seed regenerates
    the rest. What this costs the reader: the figures here can be recomputed from `analysis.md`,
    but not re-derived from raw output without re-running the experiment. The tool counts in
    limitation 9 were taken over the transcripts that survived, not all of them. The skill
    re-measurement also carries one asymmetry worth naming: reaching `uv` meant putting
    `/opt/homebrew/bin` on that arm's `PATH`, so the skill arm could see binaries the readb-free
    arms could not. Across all 36 runs the only one it invoked from there was `uvx`, 35 times.
13. **The corpus no longer rebuilds byte-for-byte.** A post-hoc fix to the generator (the fuzzy
    candidates for Q11 are now spread across the runbooks rather than planted at fixed indices,
    so they no longer degrade on a small corpus) moved which four runbooks carry a `# Failover`
    section. Rebuilding at seed 24 therefore produces a different checksum from the one
    `manifest-run.json` records — the mechanism worked exactly as intended and caught the drift.
    Everything Q10 depends on is unchanged and was re-verified: 192 files declaring
    `type: Service`, 12 unparseable, readb reporting 180.
14. **A published cost basis outlived its billing regime.** Recomputed cost tracks the runtime's
    own `total_cost_usd` closely but not exactly: median deviation **0.8%**, with 40 of the 216
    recorded runs off by more than 1% and one retracted run off by 20.5%. Runs
    made later, for the `q10b` probe, report at **0.676×** list price — a flat plan discount not
    in effect during the measured batches. This is the reason cost here is recomputed from token
    counts against a committed price table rather than quoted from the runtime: ratios within a
    batch are unaffected, but absolute dollars from different batches are not comparable.

15. **The coached arm's preamble named one of Q3's own answers.** *Found on 2026-08-22, during
    v2's design, and recorded here as a correction to this document.* The `shell-coached`
    treatment quotes one real concept so its commands are runnable as shown, and the harness took
    that name from `truth["q3"]["answer"][0]` — a member of the very set Q3 asks the agent to
    produce. Every `shell-coached` Q3 run therefore read one of its own answers in its preamble.
    The contamination favours the **competitor**, so this document's readb-versus-coached figures
    are conservative rather than inflated; but that arm's Q3 numbers are not comparable to the
    other arms', and no exclusion rule caught it. v2 draws the example from outside every answer
    set and asserts it.

16. **`manifest-run.json` was reconstructed after the fact.** The harness of the time wrote one
    `manifest.json` that later batches overwrote. The corpora it records are the same directories
    the batch read, hashed afterwards and unmodified since, but it is a reconstruction and says
    so. Later batches carry manifests written during the run.

# Reproducing

The harness, corpus generator, battery, scorer, the aggregated analyses and a
`manifest-<batch>.json` per batch are in [`benchmarks/`](../../../benchmarks/README.md). Each
manifest records the runtime version, readb version, model, effort, price table, corpus
checksums, generation seed and machine; the four written during a run carry the per-arm `PATH` as
a structured field, and the reconstructed `manifest-run.json` carries it as a note.

Raw per-run records and transcripts are **not** committed (limitation 11). Re-running the harness
against the same seed regenerates them; the manifests are what make a new batch comparable to
this one.
