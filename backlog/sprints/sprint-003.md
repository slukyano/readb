---
type: Sprint
title: Post-0.1.0 adoption — usage skill, prior art, release automation
description: Ship a readb usage skill, place readb honestly among prior art in the README, automate tag-triggered releases, and fix the field editor's multi-line corruption bug.
status: Designing
branch: sprint/003
tasks:
- 026-field-editor-multiline-corruption
- 025-ship-usage-skill
- 019-readme-prior-art
- 023-release-automation
created: 2026-08-06
timestamp: '2026-08-06T00:00:00Z'
---

Third sprint under the [session/sprint workflow](../workflow.md), and the first after 0.1.0
reached PyPI.

## Scope rationale

The follow-through on going public: readb now has users, so it should teach its own use
(`ship-usage-skill`), state honestly where it sits among prior art (`readme-prior-art`), and make
the next release a tag push instead of a manual token upload (`release-automation`).

`field-editor-multiline-corruption` was **found during this sprint's own scoping** and added by
the agent: correcting `release-automation`'s stale `blocked_by` — the one bookkeeping fix
approved at scoping — corrupted the file, because the line-based editor orphans the continuation
lines of any multi-line value. It is data loss in readb's only write path and it blocks
dogfooded frontmatter edits, so it leads the sprint (workflow: dogfooding-blocking tasks take
priority). Pending the maintainer's confirmation of the addition.

Deliberately out of scope: `measure-agent-efficiency` (largest task in the backlog — corpus
generation, harness, repeat runs; also wants `ship-usage-skill` to exist first, for its third
arm), `bundle-index-log-automation`, and the four research tasks
(`field-editor-type-inference`, `frontmatter-schema-checking`, `cross-bundle-querying`,
`research-body-structured-query`), which form a natural roadmap-shaping sprint of their own.

Scope-time bookkeeping, already committed with this file:

- `release-automation`'s `blocked_by` listed `publish-readb-0-1-0` — a name that never existed
  (the concept is `022-publish-readb-0-1-0`). A dangling blocker counts as blocking, so the task
  was invisible to the eligibility query. The blocker is satisfied (022 is `Done`), so the key
  was removed rather than corrected. Removed by hand: readb itself cannot do this edit today —
  that is `026`.
- Recorded in `AGENTS.md`: readb's public surfaces must never present this project's own
  development process as part of the tool (maintainer instruction at scope approval, 2026-08-06).
  Directly binding on `ship-usage-skill` and `readme-prior-art`.

## Task checklist

Design phase (a checked box = `## Design` section written and discussed):

- [ ] 026-field-editor-multiline-corruption — span detection for multi-line values; decide `set`'s
      behavior on a multi-line key (lossy overwrite vs. refuse) and whether a re-parse guard lands
- [ ] 025-ship-usage-skill — content and distribution shape of the shipped usage skill
      (repo directory, wheel packaging, or both); usage-only, no process material
- [ ] 019-readme-prior-art — the prior-art note, led by the transparent-disposable-index framing
- [ ] 023-release-automation — tag-triggered build + publish via OIDC Trusted Publishing; note
      that `ci.yml`, `CHANGELOG.md` and `CONTRIBUTING.md` already landed on `main` outside a sprint

## Implementation checklist (in order)

1. [ ] 026-field-editor-multiline-corruption
2. [ ] 025-ship-usage-skill
3. [ ] 019-readme-prior-art
4. [ ] 023-release-automation
5. [ ] Gates: `pytest` + `ruff` + independent subagent review of the sprint diff

## Open questions

- **Scope addition** (raised 2026-08-06, at sprint start): the maintainer approved `025`, `019`,
  `023`; the agent added `026` on discovering it while executing the approved bookkeeping fix.
  Confirm or drop before design starts.
- **`023` hand-off**: configuring the PyPI trusted publisher is a maintainer action the agent
  cannot perform. Approved at scoping as an in-sprint hand-off — the agent writes and tests the
  workflow, the maintainer flips the PyPI setting before the first tag.

## Session log

- **2026-08-06** — Scope approved in chat (`ship-usage-skill`, `readme-prior-art`,
  `release-automation`). Sprint created, branch `sprint/003`. Scoping turned up the field-editor
  multi-line corruption bug; recorded as `026` and added to scope pending confirmation.
