---
type: Sprint
title: Post-0.1.0 adoption — usage skill, prior art, release automation
description: Ship a readb usage skill, place readb honestly among prior art in the README, automate tag-triggered releases, and fix the field editor's multi-line corruption bug.
status: Implementing
branch: sprint/003
tasks:
- 026-field-editor-multiline-corruption
- 025-ship-usage-skill
- 019-readme-prior-art
- 023-release-automation
created: 2026-08-06
timestamp: '2026-08-07T00:00:00Z'
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
priority). Confirmed in scope by the maintainer, 2026-08-06.

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

- [x] 026-field-editor-multiline-corruption — span detection; `set` refuses a multi-line key,
      `unset` deletes the whole span, `get` stops returning `""`; re-parse guard on the write path
- [x] 025-ship-usage-skill — ⚠️ revised 2026-08-07: the repo becomes its own plugin marketplace
      (`.claude-plugin/` + `skills/readb/SKILL.md`); no wheel packaging, no `readb skill` command
- [x] 019-readme-prior-art — `## Prior art` after Type inference, led by the
      transparent-disposable-index framing; adoption figures re-checked at implementation
- [x] 023-release-automation — tag-triggered `release.yml` on `pypa/gh-action-pypi-publish`
      (it generates PEP 740 attestations; `uv publish` does not); `ci.yml`, `CHANGELOG.md` and
      `CONTRIBUTING.md` already landed on `main` outside a sprint

## Implementation checklist (in order)

1. [x] 026-field-editor-multiline-corruption — span-based get/set/unset + write-path guard; 18 new tests (147 total)
2. [x] 025-ship-usage-skill — plugin + marketplace manifests, portable skills/readb/SKILL.md, neutral library fixture, examples executed by tests
3. [x] 019-readme-prior-art — `## Prior art` added, figures re-checked 2026-08-07
4. [x] Public-surface sweep — CLI help/docstrings and package metadata were already clean; the
       README's examples moved from `tasks`/`docs/adr`/`task` to the neutral `library` bundle
5. [ ] 023-release-automation
6. [ ] Gates: `pytest` + `ruff` + independent subagent review of the sprint diff

## Open questions

- **`023` hand-off** (open, maintainer action): configuring the PyPI trusted publisher — owner
  `slukyano`, repo `readb`, workflow `release.yml`, environment `pypi`, and the same on TestPyPI
  for the rehearsal. Approved at scoping; the workflow lands first and is verified once the
  setting exists.

Resolved:

- **Scope addition** (2026-08-06) — `026` confirmed in scope by the maintainer.
- **Rust rewrite vs. `023`** (2026-08-07) — the maintainer raised that automating a PyPI release
  pipeline is the wrong investment order if readb is leaving Python. Recorded with its measured
  evidence as [028-evaluate-rust-rewrite](../tasks/028-evaluate-rust-rewrite.md) and sequenced
  behind [024](../tasks/024-measure-agent-efficiency.md); `023` **stays in this sprint** — the
  workflow's skeleton (tag guard, changelog extraction, GitHub release) survives any rewrite, and
  a Python 0.x line would keep releasing through a transition.

## Session log

- **2026-08-06** — Scope approved in chat (`ship-usage-skill`, `readme-prior-art`,
  `release-automation`). Sprint created, branch `sprint/003`. Scoping turned up the field-editor
  multi-line corruption bug; recorded as `026`, confirmed into scope. Design phase completed the
  same day: all four `## Design` sections written; the publishing mechanism decided against
  `uv publish` on the attestation evidence; a public-surface sweep added to implementation.
- **2026-08-07** — Design review with the maintainer. `025` reworked: the skill leaves `src/` and
  the repository becomes its own plugin marketplace; the `readb skill` command and wheel packaging
  are dropped. `019`'s exact README text drafted into the task, with figures re-checked — the
  survey's "MarkdownDB stalled since March 2024" is stale and the repository has moved to
  `flowershow/markdowndb`. New drafts:
  [027-plugin-marketplace-submission](../tasks/027-plugin-marketplace-submission.md),
  [028-evaluate-rust-rewrite](../tasks/028-evaluate-rust-rewrite.md). **Design approved** the same
  day, `023` kept in scope: the four tasks flipped `Draft → Designed`, the sprint flipped
  `Designing → Implementing`, and the branch design-merged to `main`. Implementation started.
