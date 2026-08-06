---
type: Task
title: Research frontmatter schema declaration / validation / enforcement
description: Should readb be able to declare, check, or enforce a frontmatter schema per type (à la a `validate` command)?
status: Draft
priority: low
tags:
- research
- schema
created: 2026-07-17
timestamp: '2026-07-17T00:00:00Z'
---

Surfaced by [research-similar-tools](../archive/006-research-similar-tools.md) (sprint-002). Several surveyed
tools give producers a way to *declare and check* structure, which readb currently does not:

- **Backlog.md** declares its allowed `statuses` (and `default_status`) centrally in a config
  file; those values are the enforced lifecycle.
- **taskmd** ships a `taskmd validate` subcommand that checks task files against the frontmatter
  conventions.
- **Dendron** warns in-editor on missing/broken frontmatter (not fully permissive).

readb today is intentionally **permissive and schema-less on load** (union-of-keys, missing key
→ NULL, malformed file logged and skipped). That is right for the *load/query* path and must not
change. But a **separate, opt-in** capability to declare a per-type schema and *check* a bundle
against it — a `readb check`/`readb lint` that reports violations without touching the load path
— could be valuable for producers (e.g. our own `tasks/` bundle: enforce that every `Task` has a
`status` in a known set).

## Research / decide

- Is this readb's job at all, or a separate linter? (readb is a *reader*; a validator is a new
  role.) Weigh against scope creep.
- If in scope: where does the schema live (a file in the `.readb/` marker dir from
  [bundle-init-discovery](../archive/013-bundle-init-discovery.md)? per-type schema docs in the bundle?), and
  what vocabulary (required keys, type per key, allowed-value sets/enums, cross-link checks)?
- Hard invariant: **read/query stays permissive and lossless**. Any schema check is a distinct,
  explicit command that never rejects a load or mutates files — it only reports.
- Interaction with [field-editor-type-inference](016-field-editor-type-inference.md): a declared
  schema could drive typed `set` (write the value in the type the schema says), which is a
  cleaner answer than syntax-guessing.
- Likely an ADR (new capability + where schemas live) and a multi-task effort if pursued.
