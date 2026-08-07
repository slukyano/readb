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
timestamp: '2026-08-06T00:00:00Z'
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

## Design

Approved in chat 2026-08-06 (sprint-003).

### Distribution: in the wheel, surfaced by a command

The canonical source is **`src/readb/skill/SKILL.md`**, shipped inside the wheel as package data
and located at runtime with `importlib.resources`. One copy — no build-time include tricks, no
repo/wheel divergence — and it stays browsable on GitHub.

A new read-only `readb skill` command surfaces it:

```sh
uvx readb skill > ~/.../skills/readb/SKILL.md      # default: the skill's content on stdout
ln -s "$(readb skill --path)" ~/.../skills/readb   # --path: where it lives, for a durable install
```

Content-by-default is what makes the `uvx` case work: that environment is thrown away, so its
path is useless while its output is not. `--path` serves the `uv tool install` case, where a
symlink tracks upgrades.

**No install/copy mode.** Writing files into an agent's skill directory would be a second write
path, and the hard constraint is that the frontmatter editor is the only one. The command prints;
the shell redirects or links.

### Content (usage only, neutral domains)

The CLI surface (`query`, `schema`, `show`, `get`, `set`, `unset`, `init`, `skill`); the data
model — the table set, the four virtual columns, union-of-keys, and the user-visible effects of
the type lattice, including the `JSON` fallback; registry discovery and when `--bundle` is still
required; the read-only contract and the deliberate narrowness of the field editor; and worked
SQL recipes. Frontmatter is the portable core only: `name` and `description`.

Per `AGENTS.md` § Hard constraints, examples use neutral bundles and say nothing about this
project's own development process.

### Shape: one file for now

A single `SKILL.md`, not a directory with `references/`. The material fits, and a flat file is
the cheapest thing to keep honest; the directory form stays available if it outgrows that.

### Drift control: the examples are executed

Every SQL example in the skill runs against a fixture bundle in the test suite, so a stale
example fails the checks instead of misleading an agent. This is the mechanism that keeps the
skill true as the CLI evolves — a documentation rule would not.
