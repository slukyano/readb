---
type: Task
title: Read a full concept (frontmatter + body) via okdb
description: No ergonomic way to read one whole concept; long bodies are unusable in table output, forcing cat fallbacks.
status: Done
priority: high
tags:
- cli
- dx
- dogfooding
created: 2026-07-09
timestamp: '2026-07-17T00:00:00Z'
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

## Design

Designed 2026-07-10 (maintainer decision: do both `show` and `--format`; add a whole-file virtual
column).

Three pieces:

1. **New virtual column `__raw`** — the byte-exact file text, frontmatter included, exactly as
   on disk (decoded UTF-8). Appended as VARCHAR alongside `__path`/`__body` on every concept
   table (`schema.py` `VIRTUAL_*`, `loader.py` row assembly). `parser.Concept` gains a `raw`
   attribute carrying the full text it already read. `SELECT __raw` is *the* way to get the
   exact document; `__body` stays body-only. Contract change recorded in
   [ADR 0003](../docs/adr/0003-virtual-columns.md) together with the `__id` removal.
2. **`okdb show [--bundle <dir>] <name-or-path> [...]`** — a read-only CLI alias for "get
   `__body`": prints each concept's body (frontmatter stripped), semantics identical to
   `__body` by construction (same parser). Arguments follow the wiki-style resolution of
   [ADR 0003](../docs/adr/0003-virtual-columns.md): a simple name (assumed unique; clash →
   the listing exception) or a full `.md` path (always unambiguous). `okdb show index`/`log`
   work too — file-level and permissive. Does **not** load the bundle into DuckDB (parses
   just the addressed files, like `get`). Multiple arguments are separated by
   `==> <path> <==` header lines (paths, since they are unambiguous); a single argument
   prints the body bare.
3. Reading values verbatim out of SQL (`--format raw`) is designed under
   [query-csv-output](query-csv-output.md); `SELECT __raw ... --format raw` becomes the exact
   `cat` equivalent.

Tests: `show` single/multi/reserved-file; `__raw` equals the on-disk text byte-for-byte;
`__raw` listed in `okdb schema`; a frontmatter key literally named `__raw`/`__body` follows the
existing reserved-name collision handling.
