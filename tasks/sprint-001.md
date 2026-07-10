---
type: Sprint
title: CLI ergonomics, dogfooding gaps, name & license
status: Designing
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
timestamp: '2026-07-09T00:00:00Z'
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

- [ ] choose-package-name
- [ ] cli-clean-errors
- [ ] read-full-concept
- [ ] default-bundle-cwd
- [ ] query-csv-output
- [ ] remove-id-virtual-field
- [ ] schema-drop-type-mapping
- [ ] license-apache-2

Implementation checklist is added at the design merge.

## Open questions

(none)

## Session log

- 2026-07-09 — Sprint scoped and approved (8 tasks); branch `sprint/001` cut. Design phase
  started.
