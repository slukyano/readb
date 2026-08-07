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
timestamp: '2026-08-07T00:00:00Z'
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

Approved in chat 2026-08-06, revised 2026-08-07 (sprint-003). The first design packaged the
skill inside the wheel and added a `readb skill` command to print it; the maintainer rejected
both — skills do not belong under `src/`, and distribution is a solved problem that readb should
use rather than reinvent.

### Distribution: the repository is its own plugin marketplace

A skill reaches an agent through the **plugin** mechanism, not through the tool's own CLI. A
plugin is a directory with a `.claude-plugin/plugin.json` manifest and skills as
`skills/<name>/SKILL.md`; a marketplace is any git repository carrying
`.claude-plugin/marketplace.json`. A single-plugin repository can be both, so readb's own
repository becomes the distribution channel:

```text
readb/
├── .claude-plugin/
│   ├── plugin.json         # name: readb, description, version (tracks the release)
│   └── marketplace.json    # this repo as a marketplace, one entry: source "./"
└── skills/
    └── readb/SKILL.md      # the portable skill folder
```

Installation is then the standard two commands, no readb-specific machinery:

```sh
/plugin marketplace add slukyano/readb
/plugin install readb@readb
```

Only `.claude-plugin/*.json` is Claude-specific. `skills/readb/SKILL.md` is an ordinary portable
skill folder at the repository root, so runtimes that read skill directories directly (for
example the `.agents/skills` convention) can symlink or copy it with nothing to strip.

**Dropped from the previous design:** the `readb skill` command and wheel packaging. Accepted
trade-off: `pip install readb` alone does not deliver the skill — the marketplace does. That is
how tools ship agent guidance now, and it keeps readb's CLI surface to the data model.

**Not in this task:** submitting the plugin to the `claude-community` marketplace for
discoverability, which depends on an external review pipeline —
[plugin-marketplace-submission](027-plugin-marketplace-submission.md).

### Content (usage only, neutral domains)

The CLI surface (`query`, `schema`, `show`, `get`, `set`, `unset`, `init`); the data
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
skill true as the CLI evolves — a documentation rule would not. Tests also assert that both
manifests parse and that the skill path they point at exists, so a broken plugin cannot ship.

### README ripple

A short "Using readb with an agent" section gives the two install commands and notes that
`skills/readb/SKILL.md` is a portable folder for other runtimes.
