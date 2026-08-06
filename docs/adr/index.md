---
okf_version: "0.1"
---

# Architecture Decision Records

An OKF bundle: one `type: ADR` concept per decision, named `NNNN-short-slug.md`. Statuses:
`Proposed` → `Accepted` (maintainer-only) | `Rejected`; reversals use a new ADR and `Superseded`.
Process: see [the task workflow](../../backlog/workflow.md#adrs).

```sh
readb query "SELECT __name, status, title FROM adr ORDER BY __name" --bundle ./docs/adr
```

* [0002 — Name the package readb (dist, import, and CLI aligned)](0002-package-name-readb.md) - Accepted.
* [0003 — Virtual columns __path/__name/__body/__raw; wiki-style name addressing; __id removed](0003-virtual-columns.md) - Accepted.
* [0004 — Explicit readb init writes a bundle registry; discovery walks up to it](0004-init-registry-discovery.md) - Accepted.
