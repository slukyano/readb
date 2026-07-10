---
okf_version: "0.1"
---

# Architecture Decision Records

An OKF bundle: one `type: ADR` concept per decision, named `NNNN-short-slug.md`. Statuses:
`Proposed` → `Accepted` (human-only) | `Rejected`; reversals use a new ADR and `Superseded`.
Process: see [the task workflow](../../tasks/workflow.md#adrs).

```sh
okdb query "SELECT __id, status, title FROM adr ORDER BY __id" --bundle ./docs/adr
```

* [0001 — Replace the PR-per-step agent loop with a session/sprint workflow](0001-sessions-sprints-workflow.md) - Accepted.
* [0002 — Name the package readb (dist, import, and CLI aligned)](0002-package-name-readb.md) - Proposed.
