---
type: Task
title: Research type inference for the frontmatter field editor
description: Should `readb set` infer YAML types (int/float/bool/list) from CLI syntax, or stay string-literal? Research the trade-off.
status: Draft
priority: low
tags:
- research
- cli
- fields
created: 2026-07-17
timestamp: '2026-07-17T00:00:00Z'
---

Surfaced by [research-similar-tools](../archive/006-research-similar-tools.md) (sprint-002). The nearest
analogue to readb's field editor, **marad/frontmatter** (Go `get`/`set`/`delete`), **infers YAML
types from CLI argument syntax**: `count=42` → int, `price=19.99` → float, `published=true` →
bool, `tags=[a,b,c]` → list, inline JSON → object. readb's `set`/`unset` today is deliberately
**line-based and string-literal** — it writes the exact `key: value` text and never coerces,
consistent with the "never guess producer intent" rule.

The question is whether that deliberate choice is right, or whether typed `set` would be a real
ergonomic win worth the complexity.

## Tension

- **For inference**: writing a list, number, or bool through `readb set` today means hand-typing
  YAML syntax in the value; a producer setting `priority=1` probably means the integer. Backlog.md
  and marad both type-infer, and it reads naturally.
- **Against (the current stance)**: "never guess producer intent" is a core rule — don't split
  comma-strings into lists, don't parse strings to numbers. Inference on *write* is exactly that
  guessing, one layer up. It also complicates the surgical line editor (which today changes only
  the targeted `key: value` line without a YAML round-trip).

## Research / decide

- Survey how comparable editors expose typing (explicit `--type`? syntax heuristics? a `--raw`
  vs `--yaml` flag? quoting rules?).
- Consider a *middle path*: keep string-literal default, add an **opt-in** typed mode
  (`--json <value>` / `--yaml <value>` / `--type`) so inference is never implicit.
- Decide whether this belongs in readb at all, given the read-mostly design; if yes, likely an
  ADR (it changes the write-path contract) and its own implementation task.
