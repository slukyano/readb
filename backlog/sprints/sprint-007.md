---
type: Sprint
title: Keep the permissive-load promise, then measure the cache
description: Fix the frontmatter shapes that kill a whole load instead of skipping one file, then re-run the full agent-efficiency matrix against the cache and the revised skill description.
tags:
- correctness
- benchmarks
timestamp: '2026-08-23T20:00:00Z'
branch: sprint/007
created: '2026-08-23'
status: Designing
tasks:
- 041-empty-struct-crashes-the-load
- 035-benchmark-v3-cached
---

Seventh sprint under the [session/sprint workflow](../workflow.md).

## Scope rationale

Two tasks, and the order between them is the point.

`041-empty-struct-crashes-the-load` is a promise readb makes and does not keep: a bad file is
supposed to be logged and skipped, never fatal. Four frontmatter shapes — an empty mapping value
among them — instead take the whole bundle down at the DDL step, so a single file nobody looks at
makes every query fail. It was found by the adversarial review in sprint-006 and reproduces on code
that predates it.

`035-benchmark-v3-cached` is the measurement sprint-006 owes. Two shipped surfaces changed without
evidence: the persistent index cache, whose whole claim is a wall-clock claim, and the skill's
`description`, whose new wording is frozen precisely so a benchmark can judge it rather than a
preference. v2's numbers describe a load path that no longer exists.

**`041` runs first because it changes which files load.** Measuring the instrument before fixing it
would measure the wrong instrument, and the corpora the benchmark generates are exactly the place a
malformed shape shows up.

## Scope decisions taken at approval

Proposed and dropped from the scope: `037-field-editor-list-values` and
`029-field-editor-remaining-edges` (the frontmatter editor's gaps, including the one that makes
this file need hand edits), and a release of 0.3.0 carrying sprint-006's work. All three stay in
the backlog; the release has no task yet and needs one when it is next proposed.

## Task checklist

- [ ] 041-empty-struct-crashes-the-load — an empty mapping value, duplicate stringified struct
      keys, an empty-string key and an out-of-range integer each kill an entire load
- [ ] 035-benchmark-v3-cached — the full matrix re-run: five arms, two models, four corpora, the
      26-question battery, pre-registered before the first measured run

## Open questions

_(none yet)_

## Session log

* **2026-08-23** — Scope approved: two tasks, branch `sprint/007`. Narrowed from a four-item
  proposal; the field editor's gaps and the 0.3.0 release were dropped.
