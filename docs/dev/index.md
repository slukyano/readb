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

## Proposed

* [0006 — The persistent cache writes only under an existing .readb/](adr/0006-cache-consent-and-key.md)
* [0007 — __hash joins the virtual columns: the hex SHA-256 of the file bytes](adr/0007-hash-virtual-column.md)

## Accepted

* [0002 — Name the package readb (dist, import, and CLI aligned)](adr/0002-package-name-readb.md)
* [0003 — Virtual columns __path/__name/__body/__raw; wiki-style name addressing; __id removed](adr/0003-virtual-columns.md)
* [0004 — Explicit readb init writes a bundle registry; discovery walks up to it](adr/0004-init-registry-discovery.md)
* [0005 — readb stays a Python package; per-invocation cost is fixed and cached, not rewritten](adr/0005-stay-on-python.md)

# Research

Durable research artifacts live in [`research/`](research/): one `type: Research` concept per
study. Dated point-in-time observations (adoption numbers, version checks) are kept *with*
their dates.

* [Similar markdown+frontmatter tools](research/similar-tools.md) - 11 tools surveyed 2026-07-17; conventions, adoption, adopt/reject calls (sprint-002).
* [Does readb make an agent cheaper or faster than plain file access?](research/agent-efficiency.md) - four-arm benchmark measured 2026-08-10; 13% cheaper in money, no accuracy or wall-clock effect, concentrated in join-shaped questions (sprint-004).
* [Pre-registration — agent-efficiency benchmark v2](research/agent-efficiency-v2-preregistration.md) - arms, corpora, battery, strata, endpoints, statistics and exclusion rules, fixed before the first measured run; registered 2026-08-22 (sprint-005).
* [Does readb still make an agent cheaper when the shell arm is armed and the corpus is messy?](research/agent-efficiency-v2.md) - five-arm, two-model, 783-run benchmark measured 2026-08-22; no pre-registered endpoint reached significance and readb matches a coached shell agent, while both beat an uncoached one (sprint-005).
