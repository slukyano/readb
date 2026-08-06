---
okf_version: "0.1"
---

# Developer documentation

Designs, decisions, and research for people working on readb. An OKF bundle: one `type:`
concept per file; this `index.md` is the listing.

```sh
readb query "SELECT __name, type, title FROM __DOCUMENTS" --bundle ./docs/dev
```

# Docs

* [Design brief](design.md) - the binding MVP spec: goals, non-goals, and the 12 acceptance criteria.

# ADRs

ADR concepts live in [`adr/`](adr/), named `NNNN-short-slug.md`.

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `type` | yes | string | Always `ADR`. |
| `title` | yes | string | The decision, stated as a decision. |
| `status` | yes | string | `Proposed` \| `Accepted` \| `Rejected` \| `Superseded`. |
| `created` | yes | date | ISO date proposed. |
| `sprint` | optional | string | Provenance: the sprint that produced it. |
| `superseded_by` | when superseded | string | Concept name of the replacing ADR. |

Body: Context, Decision, Consequences (and Alternatives considered, when useful).

`Proposed` → `Accepted` (maintainer-only) | `Rejected`. An accepted decision is never edited
into a different decision: write a new ADR and mark the old one `Superseded`.

```sh
readb query "SELECT __name, status, title FROM adr ORDER BY __name" --bundle ./docs/dev
```

## Accepted

* [0002 — Name the package readb (dist, import, and CLI aligned)](adr/0002-package-name-readb.md)
* [0003 — Virtual columns __path/__name/__body/__raw; wiki-style name addressing; __id removed](adr/0003-virtual-columns.md)
* [0004 — Explicit readb init writes a bundle registry; discovery walks up to it](adr/0004-init-registry-discovery.md)

# Research

Durable research artifacts live in [`research/`](research/): one `type: Research` concept per
study. Dated point-in-time observations (adoption numbers, version checks) are kept *with*
their dates.

* [Similar markdown+frontmatter tools](research/similar-tools.md) - 11 tools surveyed 2026-07-17; conventions, adoption, adopt/reject calls (sprint-002).
