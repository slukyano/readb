---
type: Task
title: Submit the readb plugin to the community marketplace
description: List the readb plugin in the public community marketplace so agents can discover it without adding this repository as a marketplace first.
status: Draft
priority: low
tags:
- docs
- agents
- distribution
created: 2026-08-07
timestamp: '2026-08-10T00:00:00Z'
---

Deferred from [ship-usage-skill](../archive/025-ship-usage-skill.md) (sprint-003): that task makes this
repository its own plugin marketplace, so installing the skill requires knowing the repository
and adding it first (`/plugin marketplace add slukyano/readb`). Listing the plugin in the public
community marketplace removes that step and makes it discoverable by search.

## Notes (to refine)

- Submission goes through an in-app form and an external review pipeline, so the timeline is not
  the project's to control — that is why it is not part of `ship-usage-skill`.
- `claude plugin validate` is run locally (and ideally in CI) before submitting; the review runs
  the same check plus automated safety screening.
- Approved plugins are pinned to a commit SHA in the public catalog and re-pinned as commits
  land, so the plugin's `version` field and the release cadence should be settled first.
- Check at that point whether other agent runtimes have a comparable public registry worth
  listing in, so the portable skill folder is not Claude-only in practice.

## Distribution findings (checked 2026-08-10)

Prompted by the question of whether tools ship skills behind a CLI flag. Three channels exist;
they are not equivalent, and only one needs work.

### `gh skill` — already works, no submission

GitHub shipped `gh skill` (preview) on 2026-04-16; it is in `gh` 2.97.0. It installs skills from
any GitHub repository into a host-specific directory at user or project scope, with `--agent`
covering Claude Code, Copilot, Cursor, Codex, Gemini CLI, Amp, Goose, OpenCode and a long tail.
There is no registry: `search` queries the GitHub Code Search API over public `SKILL.md` files,
and `publish` validates against the Agent Skills spec and cuts a GitHub release in the
repository itself.

readb needs nothing for this — the layout chosen for the plugin is what `gh` reads:

```sh
gh skill preview slukyano/readb readb          # verified working, nothing published
gh skill install slukyano/readb readb --agent claude-code
```

Open gap: `gh skill search readb` does not surface it — the index returns unrelated "readback"
skills. Whether that needs `gh skill publish`, the `agent-skills` repository topic, or only time
is unestablished, and it is the discoverability half of this task.

Two things surfaced by `gh skill publish --dry-run`:

- The skill was missing a recommended `license` field. Fixed.
- Discovery globs match anywhere in the tree and ignore `.gitignore`, so a run from a working
  copy with the upstream test fixtures cloned also finds `kb-search` under
  `tests/fixtures/upstream/…/skills/`. A real publish from such a copy would release a
  third-party sample skill under readb's name. Publish from a clean checkout.

### The Claude Code hint protocol — blocked, and not by us

A CLI that detects `$CLAUDECODE` can write a one-line `<claude-code-hint … />` marker to stderr;
Claude Code strips it and offers a one-time install prompt. This is what real vendor CLIs do —
`slackapi/slack-cli` emits it from its help output, `pinecone-io/cli` has a dedicated
`pluginhint` package, both with tests. It fires **only** for plugins in the *official* Anthropic
marketplace, which is curated at Anthropic's discretion and is not what the submission form in
this task targets. So it stays out of reach until an official listing exists, and this task
cannot unlock it.

### `--skill` — a dead end, closed

The `skillflag` convention (`<tool> --skill list|show|export`) has no adoption: a GitHub code
search for `"--skill export"` returns one repository, and the hit is a test file; the convention
repository sits at 8 stars seven months after its proposal. `gh skill` covers the same need
without per-tool code. **Do not revisit** a `readb skill`-style command — the design decision in
[025](../archive/025-ship-usage-skill.md) that rejected it is confirmed by the evidence here.

### What this leaves

Distribution is solved twice over; only discovery is open. The npm-model package managers
(`skills.sh`/`npx skills`, `skillpm`, `skills-npm`) consume the same `SKILL.md` artifact, so
adding one later is additive and no channel forecloses another.
