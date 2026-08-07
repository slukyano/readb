---
type: Task
title: Fix set/unset corrupting multi-line frontmatter values
description: The line-based field editor rewrites only the `key:` line, orphaning block-list, block-scalar and nested-mapping continuation lines into invalid YAML.
status: Done
priority: high
tags:
- bug
- fields
- dogfooding
created: 2026-08-06
timestamp: '2026-08-07T00:00:00Z'
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
  ends (the next top-level key line or the closing `---`) and replace or delete that whole span.
  Everything outside the span must stay byte-identical — the surgical-edit contract
  (`AGENTS.md` § Hard constraints; the `src/readb/fields.py` module docstring) does not change.
- Decide the behavior of `set` on a multi-line key: replace the span with a scalar (a lossy but
  explicit overwrite), or refuse until list-valued assignment exists. Writing list *values* is
  the separate open question in
  [field-editor-type-inference](../tasks/016-field-editor-type-inference.md); this task must at minimum
  never produce invalid YAML.
- Consider a guard on the write path: re-parse the edited frontmatter before the file is
  replaced and abort on failure, so no future editor bug can ship a broken file.
- A malformed-file skip is currently a log line. Consider whether the editor's own output should
  be louder, since a corrupted concept is invisible afterwards.

## Design

Approved in chat 2026-08-06 (sprint-003). The editor stays line-based and surgical; what changes
is that it learns where a key's value *ends*.

### 1. Span detection

One new helper in `fields.py` replaces every "find the key's line" lookup:

```
_span(frontmatter, key) -> (start, end) | None
  start := first line matching ^<key>\s*:            # top-level only; nested keys are indented
  end   := scan forward to the first line matching ^[A-Za-z0-9_-]+\s*: (the next top-level key),
           or the end of the frontmatter block
  then trim back off the span any trailing blank lines and column-0 comment lines
```

Everything that is not a new top-level key belongs to the span: indented continuation lines
(block scalars, nested mappings, multi-line flow scalars) and column-0 `- item` lines, which YAML
allows a block sequence to use under its parent key. Trailing blanks and comments are trimmed
back out so that a `# documents the next key` line survives an `unset`; a comment *inside* a list
region is trimmed only if it is the last thing in the span. A key whose span is one line behaves
exactly as today — the common path is unchanged, byte for byte.

### 2. `set` on a multi-line key: refuse

`set` keeps its current behavior for absent keys (append) and single-line keys (replace the
line). For a multi-line span it raises a new `FrontmatterError` subclass rather than writing:

```
blocked_by: multi-line value (list, block scalar, or nested mapping);
readb set writes scalar values only — unset the key first
```

Rationale: overwriting a list with a scalar is a type change the caller almost certainly did not
intend, and the CLI has no syntax for a list value yet — that is the separate open question in
[field-editor-type-inference](../tasks/016-field-editor-type-inference.md). Refusing costs nothing today
and turns into a real write if that task lands list assignment. `unset` then `set` is the
explicit escape hatch, named in the error message itself.

The refusal is **all-or-nothing**: `set a=1 b=2` where `b` is multi-line writes neither. This
falls out of the existing structure — `_set` builds the whole new frontmatter before `_rewrite`
writes once, so raising mid-transform leaves the file untouched.

`FrontmatterError` is already caught at `src/readb/cli.py:277` and re-raised as a
`click.ClickException`, so the new subclass prints as a clean one-liner with no traceback (the
`cli-clean-errors` contract) for free.

### 3. `unset` deletes the span

`unset` removes the key's whole span instead of the single `key:` line. Absent keys stay ignored.
This is unambiguous — "remove this key and its value" destroys nothing the caller did not ask to
destroy — so it needs no refusal path.

### 4. `get` stops lying

`get_field` currently matches `^key\s*:\s*(.*?)\s*$` and so returns `""` for a non-empty block
list — indistinguishable from `key: ''`. For a multi-line span it now returns the value verbatim:
the inline remainder of the key line (e.g. the `|` indicator, if any) plus the continuation lines,
exactly as they appear in the file. Single-line scalars keep returning the unquoted scalar, so the
common path and the Python API signature (`str | None`) are unchanged. `get` also stays forgiving:
no frontmatter still returns `None`, never an error.

### 5. Re-parse guard on the write path

`_rewrite` verifies before it writes: if the **original** frontmatter parsed as YAML, the rewritten
frontmatter must parse too, or the write is abandoned and a `FrontmatterError` is raised with the
file left untouched. A file that was *already* invalid is not blocked from being edited — readb
must not be the one tool that refuses to touch a broken file — the guard only forbids *introducing*
invalidity. This makes the whole bug class unshippable, including from future editor changes.

The guard uses `yaml.safe_load` purely to **verify**; output is still produced entirely by the
line editor. The module's "stdlib only" stance therefore relaxes to what actually matters and was
always the real invariant: **the editor never round-trips YAML** — it never lets a parser reflow,
reorder, or re-quote the block. PyYAML is already a hard dependency of readb. The `fields.py`
module docstring and the `AGENTS.md` architecture line are updated to say this. No ADR: the
surgical-edit contract itself is unchanged, and it has never been ADR-borne.

### 6. Louder skips — not here

The note about the permissive loader logging a skip only quietly is real but belongs to the load
path, not the editor: with the guard in place readb can no longer *produce* the broken file. Left
out of this task deliberately; if it should be pursued it needs its own task.

## Test coverage to add

- Round-trip `set` / `unset` / `get` against each multi-line form — block list, `|` and `>` block
  scalars, nested mapping — asserting the file still parses and that untouched lines are
  byte-identical.
- The exact `023-release-automation` shape that triggered the bug, as a regression.
- `set` on a multi-line key: raises, exit code and clean one-line message, file unchanged; and the
  all-or-nothing case where a valid pair accompanies the refused one.
- `unset` deletes the whole span and preserves a trailing comment line that documents the next key.
- `unset` of a column-0 `- item` list, the form the loader silently dropped.
- The guard: a synthetic edit that would produce invalid YAML leaves the file untouched; a file
  that was already invalid is still editable.
- Single-line behavior pinned byte-for-byte, so the span work cannot regress the common path.
