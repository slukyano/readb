---
type: Task
title: Close the field editor's remaining frontmatter edge cases
description: Duplicate keys make get and query disagree, and a `---` inside a block scalar ends the frontmatter early for both the editor and the parser.
status: Draft
priority: low
tags:
- fields
- parser
created: 2026-08-07
timestamp: '2026-08-07T00:00:00Z'
---

Surfaced by the independent review of sprint-003, alongside the multi-line corruption bug that
sprint fixed ([026](../archive/026-field-editor-multiline-corruption.md)). These are older, rarer
and were left alone deliberately — none of them is a regression, and each needs a decision rather
than a patch.

## 1. Duplicate keys: `get` and `query` disagree

A frontmatter block with the same key twice is accepted by PyYAML, which resolves it to the
**last** occurrence. `readb set` edits only the **first**, and `readb get` reads only the first.
So after a `set`, `readb get x status` and `SELECT status FROM ... WHERE __name = 'x'` report
different values, both confidently. (`unset` is already consistent: it removes every occurrence.)

Options: refuse to `set` a duplicated key; edit the occurrence YAML would win with; or report
duplicates as a load-time warning. Deciding needs a view on whether readb should ever normalize
a file it did not create.

## 2. `---` inside a block scalar ends the frontmatter early

```yaml
---
note: |
  ---
  still the note
status: open
---
```

Both `_split_frontmatter` in `src/readb/fields.py` and the equivalent in `src/readb/parser.py`
scan for the first line whose strip is `---`, so the block scalar's own `---` closes the
frontmatter. A subsequent `set` then inserts the key into the middle of the scalar. The two
implementations agree, so reading and editing stay consistent with each other — the file is just
parsed differently than a YAML-aware reader would parse it.

Fixing this properly means the frontmatter split becomes indentation-aware, in two places. Worth
weighing against how often a `---` line appears inside frontmatter at all.

## 3. Values that YAML re-reads as another type

Tracked separately as the field note on
[016-field-editor-type-inference](016-field-editor-type-inference.md): `set n=42` writes a bare
`42` that reads back as an integer, while `set flag=true` is quoted and stays text. Listed here
only so the three known write-path wrinkles are findable from one place.
