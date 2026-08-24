---
type: Task
title: The shipped skill is invoked on fewer than half the runs where it is available
description: In the v2 benchmark the skill arm loaded the readb skill on 37 of 78 runs and never invoked readb at all on 41 — the arm simply told readb's syntax did far better.
status: Designed
priority: medium
tags:
- skill
- agents
- docs
created: 2026-08-22
timestamp: '2026-08-23T12:00:00Z'
---

Found by the v2 agent-efficiency benchmark (`031-benchmark-v2`, sprint-005), which interleaved the
skill arm into the main batch for the first time — v1 ran it alone and could not compare it fairly.

With the plugin loaded and readb on `PATH`, across 78 Sonnet runs:

| | `readb-skill` | `readb-bare` |
| --- | --- | --- |
| Skill tool invoked for readb | 37 / 78 | — |
| Never invoked readb at all | 41 / 78 | 13 / 78 |
| Billed cost vs `baseline` | 0.87× | 0.72× |
| Exact | 96% | 97% |

`readb-bare` differs from `readb-skill` by one thing: it is *told* readb's syntax in its preamble
instead of being left to discover a skill that describes it. Making guidance available is not the
same as making it used, and the arm that had to find the guidance was the most expensive readb arm
in the experiment.

**This is a finding about discovery, not about the skill's content.** Nothing here says the skill
is wrong — every one of its SQL examples is executed by the test suite. It says an agent with the
skill installed reaches for it about half the time.

## Notes (to refine)

- The obvious lever is the skill's `description` frontmatter, which is what a runtime matches
  against a task before loading the body. Whether it is too narrow, or too abstract, is measurable
  the same way this was.
- Any change here is a change to a shipped public surface and should be **measured after the
  fact**, not tuned until the benchmark improves — the same discipline the routing nudge was held
  to in `031-benchmark-v2`.
- The routing nudge tested in `031-benchmark-v2` is *not* the answer: it moved readb usage up but
  moved no cost ratio, and roughly doubled failed readb calls. That result is recorded in
  [`docs/dev/research/agent-efficiency-v2.md`](../../docs/dev/research/agent-efficiency-v2.md).

## Design

One field changes: the `description` in `skills/readb/SKILL.md`, plus the matching one-line
`description` in `.claude-plugin/plugin.json`. The skill body is not touched — its examples are
executed by the test suite and v2 found nothing wrong with them.

### The hypothesis being tested

The current description is written in **readb's vocabulary rather than the agent's situation**:

> Query a directory of markdown files with YAML frontmatter using real SQL, and make surgical
> single-field frontmatter edits. Use when asked to search, filter, count, group, or
> cross-reference markdown documents by their frontmatter, …

An agent facing *"how many services does the platform team own?"* over a directory of `.md` files
has to first recognize that directory as "markdown documents with YAML frontmatter" before the
trigger clause can fire. The claim is that discovery fails at that recognition step, not at the
question of whether SQL would help — which is consistent with what v2 saw: the arm that was simply
*told* readb's syntax used it, and the arm that had to recognize a match half did not.

The revision therefore leads with the **situation and the artifacts an agent actually sees**, names
the **tools it would otherwise reach for**, and keeps the trigger verbs:

> Answer questions about a directory of markdown files by running SQL over their YAML frontmatter,
> and change one frontmatter field without rewriting the file. Use when a question spans many `.md`
> files in one tree — a docs directory, a notes vault, a knowledge base, an OKF bundle — and
> answering it would otherwise mean grepping, cat-ing or `yq`-ing file after file: counts and
> rollups, "which files have X", filtering or grouping by a frontmatter key, or cross-referencing
> one document type against another. Also use when a single frontmatter field in one file needs
> setting or removing.

**Deviation from the approved text**: the design said "a task backlog" among the example trees.
`tests/test_skill.py` forbids the word *backlog* in the shipped skill — the guard that keeps this
project's own process out of readb's public surfaces — so the example is "a knowledge base"
instead. The guard was right and the text changed, not the guard.

`plugin.json`'s description gets the same treatment in one line, since it is what a marketplace
listing shows:

> Ask a directory of markdown files a question in SQL — counts, filters and cross-references over
> YAML frontmatter — and edit one frontmatter field in place.

### The rule this task is held to

**The text above is frozen when it lands.** It is not adjusted again before
[035-benchmark-v3-cached](035-benchmark-v3-cached.md) measures it, and it is not tuned afterwards
until the benchmark improves — that would measure the tuning. If v3 says discovery did not move, the
result is published and the hypothesis above is wrong. This is the same discipline `readb-nudged`
was held to in v2, and the reason 033 ships a *change* rather than a *fix*.

### Public-surface delta

| Surface | Change |
| --- | --- |
| `skills/readb/SKILL.md` frontmatter `description` | New text (above). `name` and `license` unchanged. |
| `.claude-plugin/plugin.json` `description` | New text (above). |
| Skill body, CLI, Python API, on-disk paths | Unchanged. |

### Tests

- The SKILL.md frontmatter parses, and carries `name`, `description` and `license`.
- The description is a single line and stays within 1024 characters — the budget a runtime that
  matches on it can be relied on to read.
- The existing tests that execute every SQL example in the skill body keep passing untouched,
  which is what makes "the body is fine" a checked claim rather than an assumption.
