---
type: Sprint
title: CLI ergonomics, dogfooding gaps, name & license
status: Done
branch: sprint/001
tasks:
- cli-clean-errors
- read-full-concept
- default-bundle-cwd
- query-csv-output
- remove-id-virtual-field
- schema-drop-type-mapping
- choose-package-name
- license-apache-2
created: 2026-07-09
timestamp: '2026-07-17T00:00:00Z'
---

First sprint under the [session/sprint workflow](workflow.md).

## Scope rationale

Led by the two dogfooding-gap tasks recorded 2026-07-09 (`cli-clean-errors`,
`read-full-concept`) per the dogfooding rule in [workflow.md](workflow.md), plus the rest of
the CLI/schema-surface cluster (`default-bundle-cwd`, `query-csv-output`,
`remove-id-virtual-field`, `schema-drop-type-mapping`). The maintainer added the two high-priority
standalone tasks at scope approval: `choose-package-name` and `license-apache-2`.
`distributable-package` stays out (blocked by `choose-package-name`); research tasks and
`bundle-index-log-automation` deferred.

## Task checklist

Design phase (a checked box = `## Design` section written and discussed):

- [x] choose-package-name — `readb`, aligned dist/import/CLI ([ADR 0002](../docs/adr/0002-package-name-readb.md), Proposed)
- [x] cli-clean-errors — CLI-layer try/except → `click.ClickException`; DuckDB message verbatim
- [x] read-full-concept — `__raw` virtual column + `okdb show` (body); raw SQL output via `--format`
- [x] default-bundle-cwd — `--bundle` optional, default `.`, all five commands
- [x] query-csv-output — `--format table|json|csv|tsv|raw`; stdlib csv; `--json` alias kept
- [x] remove-id-virtual-field — `__id` → wiki-style `__name` + clash exception ([ADR 0003](../docs/adr/0003-virtual-columns.md), Proposed); docs ripple
- [x] schema-drop-type-mapping — CLI section removed; `BundleSchema.type_mapping` stays
- [x] license-apache-2 — Apache 2.0 text + SPDX metadata; no NOTICE

## Implementation checklist (in order)

1. [x] `choose-package-name` (the rename — everything else lands on `readb`)
2. [x] `cli-clean-errors`
3. [x] `read-full-concept` + `query-csv-output` (shared output-format surface)
4. [x] `remove-id-virtual-field` (incl. workflow/CLAUDE doc query rewrites)
5. [x] ~~`default-bundle-cwd`~~ — implemented, then **reverted and Dropped** at implementation
   review (maintainer decision: cwd default = silent wrong-scope operations; successor draft:
   `bundle-init-discovery`)
6. [x] `schema-drop-type-mapping`
7. [x] `license-apache-2` (incl. NOTICE — decision revised at approval)
8. [x] Gates: full `pytest` + `ruff` + independent subagent review of the sprint diff

## Sprint summary

Delivered 7 of the 8 scoped tasks; `default-bundle-cwd` was implemented then reverted and
`Dropped` at implementation review. All tasks now `Done`; sprint `Done`.

**Features delivered (per task):**

- `choose-package-name` — package renamed `okdb → readb` across dist name, import package
  (`src/readb/`), CLI binary, URLs, and all docs/tests ([ADR 0002](../docs/adr/0002-package-name-readb.md)).
- `cli-clean-errors` — `query`/`schema` translate `duckdb.Error` into a one-line
  `click.ClickException` (exit 1); DuckDB's own message is preserved verbatim, no traceback.
- `read-full-concept` — new `__raw` virtual column (byte-exact file text) and `readb show`
  command (the `SELECT __body` alias) for reading a concept's body.
- `query-csv-output` — `readb query --format table|json|csv|tsv|raw` (stdlib `csv`); `--json`
  kept as an alias for `--format json`, and conflicting `--json`/`--format` errors.
- `remove-id-virtual-field` — `__id` removed; four virtual columns now: `__path` (the
  guaranteed key), `__name` (wiki-style, assumed-unique), `__body`, `__raw`. CLI addresses
  concepts by name or full `.md` path ([ADR 0003](../docs/adr/0003-virtual-columns.md)).
- `schema-drop-type-mapping` — the redundant type→table mapping section removed from
  `readb schema` output; `BundleSchema.type_mapping` stays in the API.
- `license-apache-2` — MIT → Apache 2.0: full `LICENSE`, SPDX `license`/`license-files` in
  `pyproject.toml`, matching classifier, minimal `NOTICE`, README footer.

**Breaking changes:** `okdb` package/CLI renamed to `readb` (import + binary); `__id` virtual
column removed (use `__name` or `__path`); `readb schema` no longer prints the type-mapping
section; license changed MIT → Apache 2.0.

**Architectural decisions:** ADR 0002 (package name `readb`) and ADR 0003 (virtual columns
`__path`/`__name`/`__body`/`__raw`, wiki-style name addressing, `__id` removed) — both
`Accepted` at design approval.

**Difficulties / open questions:** `default-bundle-cwd` was cut mid-review — defaulting
`--bundle` to the cwd silently treats any directory as a bundle (wrong-scope reads and
misdirected name-resolved writes); replaced by drafts `bundle-init-discovery` (explicit init +
upward discovery) and captured in a code comment. One open design question carried forward as
draft `name-column-unprefix`: un-prefix `__name → name` (inferred but producer-settable) —
deferred, not scoped here.

**Review findings & resolution:** independent review of the full diff found 1 high (symlink
escape via name resolution, also writable through `set`), 3 medium (`__raw` CRLF exactness,
glob metachars in names, dirs named `*.md`), 6 low. All fixed with regression tests. One known
limitation documented: a zero-row csv/tsv result prints nothing (header included) because
column names travel with the rows. Gates green at close: 94 tests pass, `ruff` clean.

## Open questions

(none)

## Session log

- 2026-07-09 — Sprint scoped and approved (8 tasks); branch `sprint/001` cut. Design phase
  started.
- 2026-07-10 — `choose-package-name` designed: name research across registries/GitHub/web;
  maintainer picked `readb` (over `readbl`, `plaindex`, `knowdb`). ADR 0002 proposed.
- 2026-07-10 — `cli-clean-errors` designed (no maintainer forks: CLI-layer error translation,
  DuckDB messages kept verbatim). `read-full-concept` design fork presented to the maintainer.
- 2026-07-10 — Maintainer called the output shape: both `okdb show` (body alias) and `--format`,
  plus a byte-exact whole-file virtual column (named `__raw`, ADR 0003). Remaining five
  designs written (fork-free). All 8 designed — design approval requested.
- 2026-07-10 — Maintainer retired "ID" terminology: wiki-style `__name` (simple file name, assumed
  unique, clash → listing exception) replaces `__id`; `__path` is the guaranteed key.
  ADR 0003 rewritten.
- 2026-07-10 — **Design approved** (maintainer, in chat; NOTICE decision delegated → yes, minimal
  NOTICE). ADRs 0002/0003 Accepted, tasks Designed, sprint Implementing, design merge to
  `main`. Implementation phase started.
- 2026-07-10 — All 7 tasks implemented (one commit each, gates green throughout). Independent
  review: 1 high (symlink escape via name resolution — also writable through `set`), 3 medium
  (`__raw` not byte-exact on CRLF, glob metachars in names, directories named `*.md`), 6 low
  (README ripple, shadowed-key silence, csv zero-row header, test gaps, leftover `concept_id`
  param). All fixed with regression tests; csv zero-row prints nothing — documented as a known
  limitation (column names travel with rows). 96 tests pass. Implementation approval requested.
- 2026-07-11 — At review the maintainer dropped `default-bundle-cwd` (reverted; silent wrong-scope
  hazard, verified live from the repo root) in favor of a future explicit-`init` + upward
  discovery (draft: `bundle-init-discovery`). Also drafted `rename-repo-dir` (special: no
  design, runs from the parent dir). Open design question raised: un-prefix `__name` → `name`
  (inferred but producer-settable).
- 2026-07-17 — Close-out: 7 tasks flipped `Designed → Done`, sprint `Implementing → Done`,
  sprint summary written. Gates re-run green (94 tests, `ruff` clean). Final review + merge
  requested. The `__name → name` open question was formalized as draft `name-column-unprefix`
  (it had no backlog task before).
- 2026-07-17 — Review follow-ups (maintainer): symlink-escape errors made explicit by name and path
  + README note; NOTICE product-description line added; drafted `csv-empty-result-header`
  (zero-row csv may be a bug) and `tz-aware-datetime-handling` (revisit avoiding `pytz`).
