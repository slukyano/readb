---
type: Task
title: Research similar markdown+frontmatter task/reader tools
description: Survey Backlog.md, taskmd, and similar wrappers for ideas worth adopting.
status: Done
priority: low
tags:
- research
created: 2026-06-29
blocked_by: []
timestamp: '2026-07-20T00:00:00Z'
---

Survey existing tools that read/manage markdown-with-frontmatter (especially task managers and
knowledge-base readers) to see what conventions and features we should adopt.

## Context

- Starting points: **Backlog.md**, **taskmd**. Also worth a look: Obsidian Dataview, Foam,
  Dendron, and any "markdown-as-database" projects.
- We care about: frontmatter conventions, status/lifecycle modeling, dependency handling,
  querying ergonomics, and CLI/UX patterns.

## Notes (to refine)

- Produce a short comparison and a concrete list of ideas to bring into okdb / this workflow.

## Findings

Executed 2026-07-17 during the sprint-002 design phase (fan-out web survey, claims verified
against primary repos/docs). The full survey — landscape, five-dimension comparison, dated
adoption data, adopt/reject calls, sources — lives as a durable research artifact:
**[docs/research/similar-tools.md](../../docs/research/similar-tools.md)** (the `research` OKF
bundle, registered in `.readb/config.toml`).

Short version: two tools sit on readb's exact spot — frontmatter-mcp (same DuckDB-SQL engine,
MCP-packaged, ~1★) and MarkdownDB (same load-into-SQL architecture, managed on-disk index,
~495★ but stalled) — while Backlog.md (~6.2k★, active) is the adopted comparable for the
task-manager workflow. readb's differentiator: the index is transparent and disposable — you
never manage a database. Ideas were routed into the four sprint-002 design tasks and three
backlog drafts (`readme-prior-art`, `field-editor-type-inference`,
`frontmatter-schema-checking`); a query DSL, implicit type inference, and engine-level
lifecycle/dependency features were consciously rejected.
