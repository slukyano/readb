---
type: Task
title: The load pass spends two thirds of its time on a failed pandas import
description: DuckDB attempts `import pandas` twice per non-NULL bound value during the insert pass; Python does not cache failed imports, so every attempt walks sys.path. Removing it makes the load ~2.9x faster.
status: Done
priority: high
tags:
- performance
- loader
- bug
created: 2026-08-22
timestamp: '2026-08-23T18:00:00Z'
---

Found while measuring the load pass for [028-evaluate-rust-rewrite](028-evaluate-rust-rewrite.md),
on the sprint-006 design branch. Measured with duckdb 1.5.4 and CPython 3.14.6 on macOS arm64.

## What happens

`_build_table` inserts rows through `connection.executemany(...)`. For **each non-NULL bound
value**, DuckDB's Python client attempts `import pandas` twice, to decide whether the object is a
pandas type. Python **does not cache a failed import**, so with pandas absent every one of those
attempts walks the whole `sys.path` and fails again. A 600-concept bundle triggers **25,326**
such attempts.

NULL values cost nothing (0 attempts), which is why the effect scales with populated cells rather
than files alone.

## What it costs

Median `load_bundle` time, three runs each, same machine:

| Bundle | As-is | Import short-circuited | |
| --- | --- | --- | --- |
| `backlog/` (34 concepts) | 107 ms | 37 ms | 2.87× |
| 600 concepts | 1123 ms | 384 ms | 2.92× |
| 2000 concepts | 3629 ms | 1266 ms | 2.87× |
| 6000 concepts | 11521 ms | 3873 ms | 2.97× |

The mechanism is confirmed rather than inferred: putting an importable stub module named
`pandas` on `sys.path` — so the import succeeds once and is cached — collapses the 2000-concept
load from 3596 ms to 1029 ms on its own. The cost is the *uncached failure*, not any work pandas
would do.

This hits `uvx readb` hardest, since an isolated tool environment never has pandas in it.

## Notes (to refine)

- **Candidate fix — a scoped sentinel.** Set `sys.modules["pandas"] = None` around the insert
  pass and delete it afterwards, only when pandas was not already imported. Measured: the full
  win, a no-op when pandas *is* importable (1022 ms vs 1027 ms), and `import pandas` still works
  after the guard releases. The wrinkle is that `sys.modules` is process-global, so a concurrent
  import of pandas in another thread during the load window would see the sentinel and fail.
- **Candidate fix — do not bind Python objects per row.** Insert through a path DuckDB reads
  natively (a temp JSON/CSV plus `read_json`/`COPY`) so no per-value conversion happens. Heavier,
  writes a temp file, and changes the insert path far more than the defect warrants.
- Worth a quick check of whether newer duckdb releases cache the negative probe, and whether the
  behaviour is worth reporting upstream.
- Whichever fix lands, the regression test should assert the *count* of `pandas` lookups during a
  load (an import hook counts them deterministically), not a wall-clock threshold.
- This is the baseline [034-persistent-index-cache](034-persistent-index-cache.md) must be measured
  against: a cache that beats a load pass which is itself 3× slower than it should be proves very
  little.
- Benchmark v1 and v2 wall-clock figures for the readb arms were measured with this cost included.
  Nothing token-billed changes, but [035-benchmark-v3-cached](035-benchmark-v3-cached.md) should say
  so.

## Design

**Public-surface delta: none.** No command, flag, output, API name, path or config key changes.
The load simply gets faster; a caller cannot observe anything else.

### The change

`load_bundle` wraps the insert pass — every `_build_table` call, and nothing else — in a guard
that makes the probe fail immediately instead of walking `sys.path`:

```python
@contextmanager
def _suppress_pandas_probe():
    """DuckDB probes for pandas per bound value; a failed import is never cached by Python."""
    absent = "pandas" not in sys.modules
    if absent:
        sys.modules["pandas"] = None
    try:
        yield
    finally:
        if absent:
            del sys.modules["pandas"]
```

`sys.modules[name] = None` is the documented sentinel for "this import fails": Python raises
`ImportError` on sight of it without touching the finders. The guard is entered only when pandas
has not already been imported, so a caller who *is* using pandas keeps it — measured at 1022 ms
against 1027 ms unguarded, i.e. no effect — and `import pandas` still works normally once the
guard releases.

Placement is the load path only. The field editor never inserts rows and never imports duckdb; it
is untouched.

### The known limitation, stated rather than hidden

`sys.modules` is process-global. A *different thread* importing pandas for the first time during
the window in which a bundle is loading would see the sentinel and get an `ImportError`. This is
accepted rather than solved:

- the window is the insert pass of one load, measured in tens to hundreds of milliseconds;
- it only exists for a program that both embeds `readb.open()` and first-imports pandas
  concurrently on another thread;
- the alternatives cost more than the defect — see below.

It is documented in the loader's docstring where the guard lives, so the next reader does not have
to re-derive why a `sys.modules` write is sitting in a read-only load path.

### Tests

- **A counting test, not a timing test.** A `sys.meta_path` finder that counts `find_spec("pandas")`
  calls, installed around a real `load_bundle` of a fixture bundle with several populated columns:
  the count must be 0. Deterministic, and it fails loudly if a future duckdb release moves the
  probe somewhere the guard does not cover.
- The guard restores state: `"pandas" not in sys.modules` after a load that started without it.
- The guard is inert when pandas is already imported: with a stub module pre-inserted into
  `sys.modules`, that exact object is still there afterwards.
- The existing load-path suite is the correctness net — the guard must change no query result.

### Alternatives weighed

| Option | Why not |
| --- | --- |
| Insert through a temp JSON/CSV read natively by DuckDB | Removes per-value conversion entirely and needs no `sys.modules` write, but replaces the whole insert path, adds a temp-file write to a read-only load, and gives up the typed bind path that `coerce` feeds. Disproportionate to the defect. |
| Set the sentinel once at import time and leave it | Simpler, but permanently breaks pandas for any process that imports readb. Unacceptable for a library. |
| Wait for an upstream duckdb fix | Not this project's timeline. Worth reporting upstream regardless; the guard is removable in one commit if a release caches the negative probe. |
