---
type: ADR
title: 'Virtual columns are __path, __body, __raw; __id is removed'
status: Proposed
created: 2026-07-10
sprint: sprint-001
timestamp: '2026-07-10T00:00:00Z'
---

# Context

Every concept table carries virtual columns beside the frontmatter-derived ones. Today they
are `__path` (bundle-relative path, with `.md`), `__id` (`__path` minus `.md`), and `__body`
(markdown body, frontmatter stripped). The design brief said "expose both `__path` and `__id`
if cheap"; in practice `__id` is trivially derivable, duplicates `__path` in every table and
in `okdb schema` output, and two sprint-001 tasks touch the contract at once:
[remove-id-virtual-field](../../tasks/remove-id-virtual-field.md) wants the duplication gone,
and [read-full-concept](../../tasks/read-full-concept.md) needs a byte-exact whole-file value
(frontmatter + body), which no current column provides.

# Decision

The virtual-column contract is exactly three columns, all VARCHAR, on every concept table:

| Column | Value |
|--------|-------|
| `__path` | Bundle-root-relative path, WITH `.md` — **the primary key**. |
| `__body` | Markdown body, frontmatter block stripped. |
| `__raw` | The byte-exact file text as on disk (frontmatter included, decoded UTF-8). |

`__id` is removed — **the path is the ID**. Nothing needs a derived bare ID:

- CLI addressing (`show`/`get`/`set`/`unset`) accepts the ID with or without `.md`, so `__path`
  values paste straight into commands.
- Frontmatter cross-references (`blocked_by`, a sprint's `tasks:`) hold bare IDs by the
  workflow's convention; joining them against `__path` appends the suffix:
  `WHERE d.__path = b.dep || '.md'`.

# Consequences

- **Breaking** for existing queries that select `__id` — acceptable pre-release. The workflow
  docs (`tasks/workflow.md`, `CLAUDE.md`) and this repo's own queries move to `__path` (e.g.
  `WHERE __path = 'sprint-001.md'`).
- Mild asymmetry: the CLI editor and `show` address concepts by ID (filename minus `.md`,
  suffix optional) while SQL results show `__path`. The resolver accepting both spellings
  keeps copy-paste between the two working.
- `__TAGS(concept_path, tag)` already joins on the path — unaffected.
- Every table gains `__raw`; memory cost is the file text per concept, negligible for
  in-memory bundles and nothing is dropped (lossless constraint upheld).

# Alternatives considered

Keeping `__id` as a generated/derivable column (still a column everywhere — the duplication is
the complaint); a DuckDB macro `id(__path)` (magic surface for a one-line expression); naming
the new column `__file`/`__source`/`__text` (`__raw` matches `--format raw`, together forming
the `cat` equivalent: `SELECT __raw ... --format raw`).
