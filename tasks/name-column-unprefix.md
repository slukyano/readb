---
type: Task
title: Consider un-prefixing __name -> name (producer-settable, inferred)
description: __name is inferred from the filename but conceptually producer-settable; weigh dropping the __ prefix to a plain, overridable name column.
status: Designed
priority: low
tags:
- schema
- naming
- design-question
created: 2026-07-17
timestamp: '2026-07-20T00:00:00Z'
---

Open design question raised at sprint-001 implementation review (see
[sprint-001](sprint-001.md) session log, 2026-07-11).

The virtual columns settled by [ADR 0003](../docs/adr/0003-virtual-columns.md) all use the
`__` prefix to mark them as reader-injected, non-producer fields (`__path`, `__name`, `__body`,
`__raw`). But `__name` is not quite like the others: unlike `__path`/`__body`/`__raw`, which
are purely mechanical projections of the file, a name is the kind of thing a producer might
legitimately want to *set* in frontmatter and have the reader respect, falling back to the
filename only when absent.

The question: should `__name` become a plain `name` column — inferred from the filename by
default, but overridable by a producer-supplied `name:` frontmatter key? That would blur the
"`__` == reader-injected" invariant ADR 0003 established, so it needs its own decision (and
likely an ADR amendment), not a silent change.

Design phase should decide:

- whether to un-prefix at all (keep the clean `__` invariant vs. ergonomics of a plain `name`);
- if yes, precedence when both a filename and a producer `name:` exist, and what happens on
  clashes (today `__name` clashes raise a listing exception on CLI addressing);
- the ripple: `__name` is a documented public column used across README, workflow.md, ADR 0003,
  and CLI name-or-path addressing (`src/readb/cli.py`).

## Design (2026-07-20, sprint-002)

**Decision: do NOT un-prefix. Keep `__name` immutable and reader-injected; a producer `name:`
frontmatter key has no effect on it.** ADR 0003's `__` invariant stands unchanged.

Rationale (human call, 2026-07-20). The question that unlocked this was "where does *name* even
appear on user surfaces?" There are exactly two, and both are already correct:

1. **The `__name` virtual column** in `readb query`/`readb schema` output — value is the filename
   stem (`loader.py:244`), a mechanical projection like `__path`/`__body`/`__raw`. It belongs
   with them under the `__` invariant.
2. **CLI concept addressing** — the `<name-or-path>` argument to `show`/`get`/`set`/`unset`, all
   routed through one resolver `_concept_path` (`cli.py:172`). It resolves a bare name by globbing
   `**/<name>.md` on the filesystem, and **raises on ambiguity** (`cli.py:223`) telling the caller
   to re-run with the full path. It does not read frontmatter.

The un-prefix (a producer-settable, filename-overriding `name`) would entangle these: either the
column and the addressing diverge (set `name: Foo` on `bar.md`, but still `readb show bar`), or
`set`/`unset` would have to parse the whole bundle to find the file to edit — coupling the write
path to the content it's about to write. The ergonomic win is tiny (this is our own bundle
convention; no external consumer), and it would cost an ADR reversal. Not worth it.

**The contract we affirm (invariant to document and guard):**

- `__name` is **immutable and filename-derived** — the simple file name, no dirs, no `.md`,
  never sourced from frontmatter. A producer may write a `name:` key; it becomes an ordinary
  `name` column and is **inert** with respect to `__name` and to addressing.
- **Doc access is always name-or-path.** For as long as every doc-addressing surface accepts
  name-or-path, a name need not be globally unique: **if the name is not unique you must supply
  the path.**
- **Name addressing always checks uniqueness** — an ambiguous bare name is a hard error listing
  the clashing paths, never a silent first-match (explicitly unlike Obsidian's undefined
  bare-link behavior). The full `.md` path is the always-unambiguous escape hatch.

**Scope of work (small; behavior already matches — this is codify + guard, not change):**

- **No production code change** is expected: `_concept_path` already globs name-or-path and
  raises on ambiguity, and `__name` already ignores frontmatter. If a review finds any
  doc-addressing surface that does *not* route through the uniqueness-checked resolver, fix it —
  that is the one place a code change could arise.
- **Regression tests** pinning the contract: (a) a concept with a producer `name:` key still has
  `__name` == its filename stem and exposes `name` as a separate column; (b) addressing an
  ambiguous bare name raises the "ambiguous … use the full path" error; (c) the full path
  resolves that same concept unambiguously.
- **Docs**: state the invariant once, where addressing is documented (README + `cli.py`
  docstring already describe name-or-path; add the "`__name` is immutable; a producer `name:` is
  inert; ambiguous names must be path-qualified" line). ADR 0003 is **affirmed, not amended** —
  no ADR change, so nothing here needs ADR re-approval.

**Follow-up:** none. The two research drafts spun off during this discussion
([field-editor-type-inference](field-editor-type-inference.md),
[frontmatter-schema-checking](frontmatter-schema-checking.md)) are unrelated to this decision and
stay in the backlog.
