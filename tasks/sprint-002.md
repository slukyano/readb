---
type: Sprint
title: Bundle init, packaging & correctness follow-ups
description: readb init + upward discovery, distributable package, zero-row csv, name un-prefix, tz-aware datetimes, similar-tools research.
status: Designing
branch: sprint/002
tasks:
- bundle-init-discovery
- distributable-package
- csv-empty-result-header
- name-column-unprefix
- tz-aware-datetime-handling
- research-similar-tools
- rename-repo-dir
created: 2026-07-17
timestamp: '2026-07-17T00:00:00Z'
---

Second sprint under the session/sprint workflow
([ADR 0001](../docs/adr/0001-sessions-sprints-workflow.md)).

## Scope rationale

The two remaining medium infrastructure tasks (`bundle-init-discovery` — the sanctioned
replacement for the dropped `default-bundle-cwd`; `distributable-package` — unblocked now that
`choose-package-name` is Done), the two correctness questions raised at sprint-001's review
(`csv-empty-result-header`, `tz-aware-datetime-handling`), the sprint-001 open design question
(`name-column-unprefix`, added by the human at scoping), and `research-similar-tools` (added by
the human at scoping — its findings may inform the design tasks). `rename-repo-dir` was
executed by the human before this sprint and verified at scoping (see its body); it is in
scope as bookkeeping only, already `Done`. Still deferred: `bundle-index-log-automation`,
`research-body-structured-query` (low).

## Task checklist

Design phase (a checked box = `## Design` section written and discussed):

- [x] research-similar-tools — surveyed 11 tools; `## Findings` written; ideas mapped to designs + draft `readme-prior-art`
- [ ] bundle-init-discovery — explicit `readb init` marker + upward discovery; ADR
- [x] name-column-unprefix — decided: keep `__name` immutable, `name:` inert, name-or-path addressing w/ mandatory uniqueness; no un-prefix, no ADR change
- [ ] csv-empty-result-header — research peers' zero-row csv behavior; decide header-or-nothing
- [ ] tz-aware-datetime-handling — verify TIMESTAMPTZ binding; lattice node or comment fix
- [ ] distributable-package — target index, release flow, clean-env install verification
- [x] rename-repo-dir — no design (special task; already Done)

## Implementation checklist

(ordered at design approval)

## Open questions

(none)

## Session log

- 2026-07-17 — Sprint scoped and approved in chat (7 tasks: 6 active + `rename-repo-dir`
  verified done and flipped). Branch `sprint/002` cut. Design phase started.
- 2026-07-17 — `research-similar-tools` executed (human chose run-now): deep-research fan-out
  over 11 tools, verified against primary repos/docs. `## Findings` written into the task body;
  ideas routed to the four design tasks + a new draft `readme-prior-art` (positioning note).
  This is a research task — its findings *are* its deliverable, so it is design-complete.
- 2026-07-20 — Discussed adoption/chatter of the prior-art tools (Backlog.md ~6.2k★ active;
  MarkdownDB ~495★ stalled; frontmatter-mcp ~1★) and recorded the human's transparent-disposable-
  index differentiator. Spun off drafts `field-editor-type-inference` and
  `frontmatter-schema-checking`. Designed `name-column-unprefix`: **rejected the un-prefix** —
  keep `__name` immutable/filename-derived, producer `name:` inert, doc access always name-or-path
  with mandatory uniqueness (no Obsidian-style silent first-match). Behavior already matches;
  deliverable is regression tests + a doc line, no production code change and no ADR amendment.
