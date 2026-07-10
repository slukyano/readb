---
type: Sprint
title: CLI ergonomics, dogfooding gaps, name & license
status: Implementing
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
timestamp: '2026-07-10T00:00:00Z'
---

First sprint under the session/sprint workflow ([ADR 0001](../docs/adr/0001-sessions-sprints-workflow.md)).

## Scope rationale

Led by the two dogfooding-gap tasks recorded 2026-07-09 (`cli-clean-errors`,
`read-full-concept`) per the dogfooding rule in [workflow.md](workflow.md), plus the rest of
the CLI/schema-surface cluster (`default-bundle-cwd`, `query-csv-output`,
`remove-id-virtual-field`, `schema-drop-type-mapping`). The human added the two high-priority
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
3. [ ] `read-full-concept` + `query-csv-output` (shared output-format surface)
4. [ ] `remove-id-virtual-field` (incl. workflow/CLAUDE doc query rewrites)
5. [ ] `default-bundle-cwd`
6. [ ] `schema-drop-type-mapping`
7. [ ] `license-apache-2` (incl. NOTICE — decision revised at approval)
8. [ ] Gates: full `pytest` + `ruff` + independent subagent review of the sprint diff

## Open questions

(none)

## Session log

- 2026-07-09 — Sprint scoped and approved (8 tasks); branch `sprint/001` cut. Design phase
  started.
- 2026-07-10 — `choose-package-name` designed: name research across registries/GitHub/web;
  human picked `readb` (over `readbl`, `plaindex`, `knowdb`). ADR 0002 proposed.
- 2026-07-10 — `cli-clean-errors` designed (no human forks: CLI-layer error translation,
  DuckDB messages kept verbatim). `read-full-concept` design fork presented to the human.
- 2026-07-10 — Human called the output shape: both `okdb show` (body alias) and `--format`,
  plus a byte-exact whole-file virtual column (named `__raw`, ADR 0003). Remaining five
  designs written (fork-free). All 8 designed — design approval requested.
- 2026-07-10 — Human retired "ID" terminology: wiki-style `__name` (simple file name, assumed
  unique, clash → listing exception) replaces `__id`; `__path` is the guaranteed key.
  ADR 0003 rewritten.
- 2026-07-10 — **Design approved** (human, in chat; NOTICE decision delegated → yes, minimal
  NOTICE). ADRs 0002/0003 Accepted, tasks Designed, sprint Implementing, design merge to
  `main`. Implementation phase started.
