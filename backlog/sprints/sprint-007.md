---
type: Sprint
title: Keep the permissive-load promise, then measure the cache
description: Fix the frontmatter shapes that kill a whole load instead of skipping one file, then re-run the full agent-efficiency matrix against the cache and the revised skill description.
tags:
- correctness
- benchmarks
timestamp: '2026-08-23T22:00:00Z'
branch: sprint/007
created: '2026-08-23'
status: Implementing
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

## Design phase

- [x] `041-empty-struct-crashes-the-load` — retitled once the design outgrew the four crashing
      shapes; proposes [ADR 0008](../../docs/dev/adr/0008-struct-field-union.md)
- [x] `035-benchmark-v3-cached` — five arms, the cache isolated in one of them, three
      pre-registered endpoints, ~$50-60

## Decisions taken during design

- **The lattice promotes rather than falling back.** The first design answered JSON for each
  awkward shape; that was rejected for deciding a column's type by which disagreement it met. A
  column now takes the narrowest type holding every value: field union for mappings, `VARCHAR` for
  mixed scalars, JSON only for structural mismatches.
- **Key normalization happens at the parse boundary**, because JSON cannot represent a duplicate
  key — `json.dumps({1: "a", "1": "b"})` emits one twice. Last occurrence wins.
- **The non-string top-level key fix is in scope**: such keys are silently dropped today, which
  breaches union-of-keys, and the same normalization fixes them.
- **v3 spends roughly $50-60** and drops the `readb-nudged` arm as a settled negative.

## Open questions

_(none)_

## Session log

* **2026-08-23** — Design approved: ADR 0008 accepted, scalar promotion and parse-boundary key
  normalization decided, v3's design and budget approved.
* **2026-08-23** — Scope approved: two tasks, branch `sprint/007`. Narrowed from a four-item
  proposal; the field editor's gaps and the 0.3.0 release were dropped.
