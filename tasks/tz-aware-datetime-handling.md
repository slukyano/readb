---
type: Task
title: Revisit tz-aware datetime handling (is avoiding pytz still right?)
description: Timezone-aware datetimes route to the JSON fallback to avoid a pytz dep; reassess whether they could bind as TIMESTAMPTZ with stdlib-only, and whether that is better.
status: Done
priority: low
tags:
- schema
- lattice
- research
created: 2026-07-17
timestamp: '2026-07-20T00:00:00Z'
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

## Design (2026-07-20, sprint-002)

**Research verdict (verified live, duckdb 1.5.4, Python 3.14, pytz absent from the venv): the
pytz requirement is real and current — but it sits on the *read* side, not the bind side.**

- *Binding* a tz-aware `datetime` (stdlib `timezone`, offset, or `zoneinfo` — no pytz) into a
  `TIMESTAMPTZ` column **works** (`INSERT ... VALUES (?)` succeeds).
- **Fetching any `TIMESTAMPTZ` value fails without pytz** — including pure SQL with no Python
  datetime anywhere: `SELECT TIMESTAMPTZ '2026-01-01 00:00:00+00'` raises
  `InvalidInputException: Required module 'pytz' failed to import`. duckdb's Python client
  constructs returned tz-aware datetimes via pytz, unconditionally.
- Naive `TIMESTAMP` fetch is unaffected.

So the task's hypothesis ("the pytz claim is outdated") is **refuted**, but the code comment's
stated reason ("would require pytz *to bind*") is imprecise: binding is fine; it's every
subsequent read that would crash. A `TIMESTAMPTZ` lattice node would make **any query touching
such a column blow up** in a pytz-free environment — strictly worse than the JSON fallback.

**Decision: keep the JSON fallback for tz-aware datetimes (lossless ISO-8601); do not add a
pytz dependency; no lattice change.** Deliverables:

1. Correct the rationale in `src/readb/schema.py` (module docstring + `type_of_value` comment,
   line 28): the actual reason is that duckdb's Python client requires pytz to *fetch* any
   `TIMESTAMPTZ` value (verified duckdb 1.5.4, 2026-07-20) — a TIMESTAMPTZ column would crash
   every query that reads it, so aware datetimes stay in the JSON fallback to keep the
   dependency surface minimal.
2. A **revisit canary** test (skipped when `pytz` is importable in the env): assert that
   fetching `SELECT TIMESTAMPTZ '...'` raises — if a future duckdb drops the pytz requirement,
   the canary fails and tells us to reconsider a `TIMESTAMPTZ` lattice node. Plus a pin that an
   aware-datetime value loads via the JSON fallback (if not already covered).

**No ADR**: the lattice gains no type; nothing in ADR 0003 changes. The mixed naive/aware
unification question is moot while aware never leaves JSON.
