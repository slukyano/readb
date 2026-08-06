---
type: Task
title: Research cross-bundle querying (bundles as DuckDB schemas)
description: Attach each registry-declared bundle as its own DuckDB schema and allow joins across bundles (e.g. tasks.task x adr.adr).
status: Draft
priority: low
tags:
- research
- query
created: 2026-07-20
timestamp: '2026-07-20T00:00:00Z'
---

Spun off from the [bundle-init-discovery](../archive/013-bundle-init-discovery.md) design (sprint-002,
[ADR 0004](../../docs/adr/0004-init-registry-discovery.md)). The registry knows every bundle in a
repo; DuckDB supports multiple schemas in one in-memory database. That opens real cross-bundle
SQL — e.g. join this repo's backlog against its ADRs:

```sql
SELECT t.__name, t.title, a.status AS adr_status
FROM tasks.task t JOIN adr.adr a ON list_contains(t.adrs, a.__name)
```

## Research / decide

- Loading: `readb.open()` on N bundles → one DuckDB, one schema per bundle. Schema naming from
  registry paths (`tasks`, `docs/adr` → ?); sanitization and collision rules.
- CLI surface: repeated `--bundle`? a `--all-bundles` flag driven by the registry? does bare
  discovery from a multi-bundle root grow an "attach everything" mode (and how does that
  interact with ADR 0004's deliberate ambiguity error)?
- Semantics: per-bundle `__DOCUMENTS`/`__INDEXES`/`__LOG`; same type in two bundles (two
  `task` tables in different schemas — fine, or confusing?); virtual-column addressing across
  bundles.
- Read-only invariant unchanged; loading N bundles must stay permissive per bundle.
- Cost: N× load time in memory; interaction with the future persistent cache (per-bundle cache
  reuse would make this cheap).
