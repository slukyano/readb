---
type: Task
title: The shipped skill is invoked on fewer than half the runs where it is available
description: In the v2 benchmark the skill arm loaded the readb skill on 37 of 78 runs and never invoked readb at all on 41 — the arm simply told readb's syntax did far better.
status: Draft
priority: medium
tags:
- skill
- agents
- docs
created: 2026-08-22
---

Found by the v2 agent-efficiency benchmark (`031`, sprint-005), which interleaved the skill arm
into the main batch for the first time — v1 ran it alone and could not compare it fairly.

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
  to in `031`.
- The routing nudge tested in `031` is *not* the answer: it moved readb usage up but moved no cost
  ratio, and roughly doubled failed readb calls. That result is recorded in
  [`docs/dev/research/agent-efficiency-v2.md`](../../docs/dev/research/agent-efficiency-v2.md).
