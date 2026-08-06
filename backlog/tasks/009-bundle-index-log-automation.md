---
type: Task
title: Keep index.md and log.md current automatically
description: 'Generate the bundle index from a query and append log entries automatically, instead of hand-editing both.'
status: Draft
priority: low
tags:
- bundle
- dx
created: 2026-07-02
timestamp: '2026-07-09T00:00:00Z'
---

`tasks/index.md` must be hand-edited for every new task (drift risk — it is a listing okdb
could generate), and `tasks/log.md` only stays current when someone remembers to append the
state transitions it should record.

## Context

- Both writes extend the sanctioned write path (the `okdb.fields` precedent): explicit
  commands, never a side effect of load/query.
- Appending a dated `log.md` line at sprint events (scope approval, close-out) would double
  as an audit trail for the bundle.

## Notes (to refine)

- Two separable pieces — decide whether to split when refining:
  1. **Log appends at sprint events**: one dated line in `log.md` per scope approval /
     design merge / close-out, riding the commits those events already make.
  2. **Index generation**: e.g. `okdb index --bundle ./tasks` regenerating the listing from a
     query (grouped by type, title + description). Decide the source of truth for ordering and
     any hand-written prose sections (preserve a header block?).
- Check the OKF spec's expectations for `index.md`/`log.md` shape before fixing a format.
