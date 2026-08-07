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
timestamp: '2026-08-07T00:00:00Z'
---

Deferred from [ship-usage-skill](025-ship-usage-skill.md) (sprint-003): that task makes this
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
