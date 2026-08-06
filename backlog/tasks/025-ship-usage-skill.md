---
type: Task
title: Ship a readb usage skill with the repo
description: An agent skill in the readb repo documenting how to use readb, installable into agent environments instead of living in personal dotfiles.
status: Draft
priority: medium
tags:
- docs
- agents
created: 2026-07-21
---

Guidance about tools should ship with the tool: an agent-consumable skill (`SKILL.md`)
maintained in this repo that teaches how to *use* readb — so any agent environment can install
it from the project, rather than each user hand-writing readb notes into personal dotfiles.
Surfaced while the maintainer extracted the sprint workflow into a personal skill library: the
workflow layer is tool-agnostic, the tool-choice layer is personal, but the "how to use readb"
layer has no home readb itself provides.

## Notes (to refine)

- Likely content: the CLI surface (`query`/`schema`/`show`/`get`/`set`/`unset`/`init`), the
  data model (virtual columns, union-of-keys, the type lattice's user-visible effects), the
  registry/discovery model (ADR 0004), the read-only contract and the surgical field editor,
  and worked SQL examples.
- Decide the distribution shape at design time: a `skills/` directory in the repo, packaging
  into the wheel, or both — and how installs reference it (e.g. a directory-level link per the
  emerging agent-skills conventions).
- Keep it usage-only: development-process docs (`tasks/workflow.md`, `AGENTS.md`) stay
  separate; the skill targets readb *users*.
