---
type: Task
title: Read a full concept (frontmatter + body) via okdb
description: No ergonomic way to read one whole concept; long bodies are unusable in table output, forcing cat fallbacks.
status: Draft
priority: high
tags:
- cli
- dx
- dogfooding
created: 2026-07-09
timestamp: '2026-07-09T00:00:00Z'
---

There is no good okdb way to read a whole concept. `okdb get` returns a single frontmatter
field; `SELECT __body FROM task WHERE ...` technically works but multiline text is mangled by
the aligned-table renderer, and `--json` wraps the markdown in JSON escaping. In practice the
agent falls back to `cat tasks/<id>.md`, which breaks the dogfooding rule.

Found while dogfooding: reviewing Draft task bodies for sprint scoping was done with `cat`
(2026-07-09).

## Context

- Reading task bodies is a every-session workflow operation (scoping, design, resuming).
- The read-only constraint is untouched — this is purely a presentation/addressing gap.

## Notes (to refine)

- Candidate shapes: `okdb show --bundle ./tasks <concept-id>` printing the file as-is
  (or frontmatter + body); a `--raw` value output for single-cell query results; or fixing
  multiline rendering in table output.
- Should compose with reading several concepts (e.g. all bodies of the tasks in a sprint).
- Whatever the shape, it stays on the read-only path (no load/query side effects).
