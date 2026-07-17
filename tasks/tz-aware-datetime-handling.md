---
type: Task
title: Revisit tz-aware datetime handling (is avoiding pytz still right?)
description: Timezone-aware datetimes route to the JSON fallback to avoid a pytz dep; reassess whether they could bind as TIMESTAMPTZ with stdlib-only, and whether that is better.
status: Draft
priority: low
tags:
- schema
- lattice
- research
created: 2026-07-17
timestamp: '2026-07-17T00:00:00Z'
---

The lattice in `src/readb/schema.py` classifies a timezone-*naive* `datetime` as `TIMESTAMP`
but routes a timezone-*aware* `datetime` to the `JSON` fallback (serialized ISO-8601). The
stated reason (schema.py, `type_of_value` / module docstring) is:

> A timezone-aware `datetime` would require `pytz` to bind, so it routes to the JSON fallback
> (serialized via ISO-8601, which is lossless) to keep the dependency surface minimal.

That justification may be **outdated and worth challenging**:

- Python 3.11+ (we require >=3.11) has stdlib `datetime.timezone` and `zoneinfo` — a tz-aware
  `datetime` needs no `pytz` to *exist* or to serialize.
- DuckDB has a native `TIMESTAMP WITH TIME ZONE` (`TIMESTAMPTZ`) type and can bind tz-aware
  Python datetimes directly in modern versions.

Research and decide:

- Can a tz-aware `datetime` bind to a DuckDB `TIMESTAMPTZ` column with **no** extra dependency
  (verify against our pinned `duckdb>=1.1`)? Where did the "requires pytz" belief come from — is
  it still true for any case (e.g. mixed naive+aware in one column)?
- If it binds cleanly: add a `TIMESTAMPTZ` node to the lattice, decide unification rules for a
  column mixing naive and aware datetimes (likely still JSON, or widen to TIMESTAMPTZ?), and
  keep JSON only as the genuine last resort.
- If it does not: correct the code comment to state the *actual* current reason, so the
  rationale isn't misleading.

Lossless-by-construction and the "never guess producer intent" rules still apply. Likely an ADR
touch-up to ADR 0003 or a small new ADR if the lattice gains a type.
