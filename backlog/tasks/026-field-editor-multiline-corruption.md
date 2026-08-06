---
type: Task
title: Fix set/unset corrupting multi-line frontmatter values
description: The line-based field editor rewrites only the `key:` line, orphaning block-list, block-scalar and nested-mapping continuation lines into invalid YAML.
status: Draft
priority: high
tags:
- bug
- fields
- dogfooding
created: 2026-08-06
timestamp: '2026-08-06T00:00:00Z'
---

`readb set` and `readb unset` treat a frontmatter key as exactly one line. When the value spans
several lines, the continuation lines are left behind and the file becomes invalid YAML — after
which the permissive load **silently skips the concept**, so it disappears from every query
rather than failing loudly. This is data loss in readb's one sanctioned write path.

## Reproduction (verified 2026-08-06, readb 0.1.0)

Editing `blocked_by` on `023-release-automation`, whose value is a block list:

```sh
readb set --bundle ./backlog 023-release-automation blocked_by=022-publish-readb-0-1-0
```

```yaml
blocked_by: 022-publish-readb-0-1-0
- publish-readb-0-1-0                 # orphaned
```

`unset blocked_by` fails the same way — it deletes the `blocked_by:` line and leaves the `-` item.
Both forms then load as `skipping 023-release-automation.md: malformed YAML frontmatter`.

The same corruption affects every multi-line value form:

| Value form | After `set key=x` |
|---|---|
| block list (`- item` lines) | scalar line + orphaned `- item` lines |
| block scalar (`\|` / `>`) | scalar line + orphaned indented text |
| nested mapping | scalar line + orphaned indented `k: v` lines |

## Notes (to refine)

- The fix is about **span detection**, not about YAML round-tripping: find where a key's value
  ends (the next line at the key's indentation or the closing `---`) and replace or delete that
  whole span. Everything outside the span must stay byte-identical — the surgical-edit contract
  in [ADR 0002](../../docs/dev/adr/0002-frontmatter-field-editor.md) does not change.
- Decide the behavior of `set` on a multi-line key: replace the span with a scalar (a lossy but
  explicit overwrite), or refuse until list-valued assignment exists. Writing list *values* is
  the separate open question in
  [field-editor-type-inference](016-field-editor-type-inference.md); this task must at minimum
  never produce invalid YAML.
- Consider a guard on the write path: re-parse the edited frontmatter before the file is
  replaced and abort on failure, so no future editor bug can ship a broken file.
- A malformed-file skip is currently a log line. Consider whether the editor's own output should
  be louder, since a corrupted concept is invisible afterwards.

## Test coverage to add

Round-trip tests for `set` and `unset` against each multi-line value form, asserting the file
still parses and that untouched keys are byte-identical.
