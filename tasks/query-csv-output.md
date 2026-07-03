---
type: Task
title: Add plain-text row output to okdb query
description: A --csv/--tsv output mode so shell callers can read rows without python-parsing --json.
status: Draft
priority: low
tags:
- cli
- dx
created: 2026-07-02
---

`okdb query` emits a pretty table or `--json`. Shell consumers (like the agent loop's
`select_next`) currently need a python one-liner just to pull two fields out of the JSON. A
machine-readable plain-text mode (`--csv` or `--tsv`) would let them use `read -r`/`cut`
directly.

## Context

- `scripts/agent-loop.sh` pipes `--json` through `$PY -c 'import json...'` solely for this;
  a text mode deletes the loop's `PY` dependency entirely.
- DuckDB can already produce CSV natively — prefer delegating to the engine over hand-rolling
  escaping.

## Notes (to refine)

- Decide the flag surface: `--csv`, `--tsv`, or `--format table|json|csv` (one enum flag may age
  better than accumulating booleans; keep `--json` as an alias either way).
- Define NULL and list/JSON-value representation in text output; document it.
- Update the loop's `select_next` to use it once available.
