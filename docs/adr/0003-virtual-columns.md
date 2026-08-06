---
type: ADR
title: 'Virtual columns __path, __name, __body, __raw; wiki-style name addressing; __id removed'
status: Accepted
created: 2026-07-10
sprint: sprint-001
timestamp: '2026-07-10T00:00:00Z'
---

# Context

Every concept table carries virtual columns beside the frontmatter-derived ones. Today they
are `__path` (bundle-relative path, with `.md`), `__id` (`__path` minus `.md`), and `__body`
(markdown body, frontmatter stripped). Two sprint-001 tasks touch the contract:
[remove-id-virtual-field](../../backlog/archive/004-remove-id-virtual-field.md) (the `__id`/`__path`
duplication) and [read-full-concept](../../backlog/archive/012-read-full-concept.md) (needs a byte-exact
whole-file value). Discussion exposed a terminology problem: `__id` is not an *ID* — "ID"
implies guaranteed uniqueness, which only the path provides. The bundle walk is recursive
(`rglob`), so concepts can live in subdirectories and simple-name clashes are genuinely
possible.

# Decision

**"ID" terminology is retired** — nothing is called an ID unless it guarantees uniqueness.
Concepts are addressed **wiki-style**: simple file names are *assumed* unique by default, and
the full path is the unambiguous fallback.

The virtual columns, all VARCHAR, on every concept table:

| Column | Value |
|--------|-------|
| `__path` | Bundle-root-relative path, WITH `.md` — guaranteed unambiguous, **the primary key**. |
| `__name` | The simple file name: no directories, no `.md`. Assumed unique, **not guaranteed**. |
| `__body` | Markdown body, frontmatter block stripped. |
| `__raw` | The byte-exact file text as on disk (frontmatter included, decoded UTF-8). |

`__id` is removed.

**Addressing a file** (CLI `show`/`get`/`set`/`unset`, and any future access-by-name API):

- An argument ending in `.md` is a **path**, resolved exactly against the bundle root
  (escape-guarded, as today).
- Any other argument is a **name**: no `/` allowed, resolved by searching the bundle for
  `**/<name>.md`. Exactly one match resolves. Zero matches → no-such-concept error.
- **Two or more matches → an exception**: it lists the clashing paths (at most 5, plus a
  "and N more" tail) and prompts the caller to re-run the operation with the full path
  instead of the simple name.

The clash exception applies only to access-by-name. SQL never raises: duplicate `__name`
values simply coexist in the tables, and `__path` is always there to disambiguate.

Frontmatter cross-references (`blocked_by`, a sprint's `tasks:`) hold **names**; the join is
direct: `WHERE d.__name = b.dep`.

# Consequences

- **Breaking** for existing queries that select `__id` — acceptable pre-release. Workflow docs
  (`tasks/workflow.md`, `CLAUDE.md`) rewrite their queries to `__name`/`__path` and their
  prose from "Concept ID" to "concept name".
- `parser.Concept.concept_id` (path minus `.md`) is replaced by `Concept.name` (basename
  semantics); the CLI resolver is rewritten to the name-or-path rules above.
- Every table gains `__name` and `__raw`; memory cost is negligible for in-memory bundles and
  nothing is dropped (lossless constraint upheld).
- `__TAGS(concept_path, tag)` joins on the path — unaffected.
- In flat bundles (all current ones), `__name` behaves exactly like the old `__id`.

# Alternatives considered

Keeping `__id` = path minus `.md` (neither a guaranteed-unique ID nor a simple wiki name —
worst of both); appending `.md` in joins (`b.dep || '.md'`) instead of a `__name` column (works
only while bundles stay flat); naming the whole-file column `__file`/`__source`/`__text`
(`__raw` pairs with `--format raw`: `SELECT __raw ... --format raw` is the `cat` equivalent).
