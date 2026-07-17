---
type: Task
title: Consider un-prefixing __name -> name (producer-settable, inferred)
description: __name is inferred from the filename but conceptually producer-settable; weigh dropping the __ prefix to a plain, overridable name column.
status: Draft
priority: low
tags:
- schema
- naming
- design-question
created: 2026-07-17
timestamp: '2026-07-17T00:00:00Z'
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
