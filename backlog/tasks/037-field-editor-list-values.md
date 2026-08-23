---
type: Task
title: The field editor cannot change a list-valued key
description: Adding a task to a sprint's `tasks` list — a routine workflow operation — cannot be done with readb set, and the error's suggested workaround destroys the list.
status: Draft
priority: high
tags:
- fields
- cli
- dogfooding
created: 2026-08-22
---

Hit while adding `036-load-pandas-import-probe` to sprint-006's scope, which is an ordinary workflow
operation:

```
$ readb set --bundle ./backlog sprint-006 tasks='[...]'
Error: tasks: multi-line value (list, block scalar, or nested mapping); readb set writes scalar
values only — unset the key first
```

The refusal itself is correct and deliberate
([026-field-editor-multiline-corruption](../archive/026-field-editor-multiline-corruption.md) made
`set` refuse a multi-line key rather than discard half of it). The gap is that **there is no other
command that can do the edit**, and the suggested workaround is worse than the error: `unset`
removes the whole list, after which `set` can only write a scalar back. A required field would be
gone in between.

This blocks dogfooding. Every sprint that changes scope, and every task that gains or loses a
`blocked_by` or a `tag`, needs a hand edit today.

## Notes (to refine)

- The minimal shape is list-aware operations rather than a general YAML writer — something like
  `readb set --bundle B <id> tags+=perf` / `tags-=perf`, and a whole-list form that writes a block
  sequence in the file's existing style. Whether that is new flags on `set` or a separate `list`
  subcommand is open.
- Scope boundary to hold: this is still a *surgical line-based* editor, not a YAML round-trip. The
  key's span is rewritten; nothing else in the file is touched. Block sequences and inline flow
  sequences both have to round-trip in their own style, since bundles are written by other tools.
- The error message should point at whatever the answer is, instead of at a workaround that loses
  data — that part is worth fixing even if the feature waits.
- Overlaps [016-field-editor-type-inference](016-field-editor-type-inference.md): writing a list
  means deciding how a list element is typed, which is the same question `set n=42` raises.
