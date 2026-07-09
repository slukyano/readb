---
type: Task
title: Keep index.md and log.md current automatically
description: Generate the bundle index from a query and let the loop append log entries, instead of hand-editing both.
status: Draft
priority: low
tags:
- bundle
- dx
- agent-loop
created: 2026-07-02
timestamp: '2026-07-09T00:00:00Z'
---

`tasks/index.md` must be hand-edited for every new task (drift risk — it is a listing okdb
could generate), and `tasks/log.md` has exactly one entry while the loop makes state
transitions it never records.

## Context

- Both writes extend the sanctioned write path (the `okdb.fields` precedent): explicit
  commands, never a side effect of load/query.
- The loop already commits to main at claim/release time, so appending one log line there is
  free and doubles as the audit trail [agent-reliability](agent-reliability.md) asks for.

## Notes (to refine)

- Two separable pieces — decide whether to split when refining:
  1. **Log appends from the loop**: one line per claim/release/advance in `log.md`, riding the
     existing claim/release commits.
  2. **Index generation**: e.g. `okdb index --bundle ./tasks` regenerating the listing from a
     query (grouped by type, title + description). Decide the source of truth for ordering and
     any hand-written prose sections (preserve a header block?).
- Check the OKF spec's expectations for `index.md`/`log.md` shape before fixing a format.
