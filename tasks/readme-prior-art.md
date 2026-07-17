---
type: Task
title: Add a "prior art / how readb differs" note to the README
description: Cite frontmatter-mcp, MarkdownDB, and Dataview; state readb's niche and the deliberate non-inference of the field editor.
status: Draft
priority: low
tags:
- docs
created: 2026-07-17
timestamp: '2026-07-17T00:00:00Z'
---

Surfaced by [research-similar-tools](research-similar-tools.md) (sprint-002): the survey found
that readb's core approach is not novel — two maintained tools sit almost exactly on its spot —
so the README should place readb honestly among them and state what actually differentiates it.

## Context

- **frontmatter-mcp** (`kzmshx/frontmatter-mcp`) — an MCP server for querying markdown
  frontmatter with **DuckDB SQL**: same engine, same data model, different packaging.
- **MarkdownDB** (`datopian/markdowndb`) — a JS/TS library that indexes markdown into a real SQL
  DB (SQLite/MySQL/Postgres) and runs raw SQL over the index: same load-into-SQL architecture,
  on-disk index + JS API instead of in-memory DuckDB + CLI.
- **Obsidian Dataview** — the notable non-SQL alternative (its DQL query language), the tool
  most people mean by "query my markdown".

readb's niche: a **read-only CLI + Python API + a surgical frontmatter field editor** over an
**OKF bundle**, running **real SQL on an in-memory DuckDB**. The differentiation is packaging
and constraints (read-only load/query path, permissive lossless load, the one narrow write
path), not a novel engine.

## Notes (to refine)

- Keep it short — a "Prior art" or "How readb differs" subsection, not a survey.
- Fold in one explicit sentence that readb's field editor is **deliberately string-literal**
  (no `key=42`→int type inference, unlike marad/frontmatter) — a conscious "never guess producer
  intent" choice, so readers don't file it as a missing feature.
- Full comparison lives in `research-similar-tools.md`'s `## Findings`; link it rather than
  duplicating.
