---
type: Task
title: Change the license to Apache 2.0
description: Replace the MIT license with Apache License 2.0 across the repo and metadata.
status: Draft
priority: high
tags:
- legal
- packaging
created: 2026-06-30
blocked_by: []
timestamp: '2026-07-10T00:00:00Z'
---

Switch the project license from MIT to Apache License 2.0.

## Context

- Currently MIT (`LICENSE` + `pyproject.toml` `license`/classifier).
- Apache 2.0 adds an explicit patent grant and NOTICE conventions.

## Notes (to refine)

- Replace `LICENSE` with the full Apache 2.0 text (© 2026 Stanislav Lukyanov).
- Update `pyproject.toml`: `license = "Apache-2.0"` (SPDX) and the
  `License :: OSI Approved :: Apache Software License` classifier; drop the MIT classifier.
- Update the README license section and any other references (CLAUDE.md, file headers if any).
- Consider adding a `NOTICE` file.

## Design

Designed 2026-07-10.

- `LICENSE`: replace with the canonical Apache License 2.0 text; copyright line
  "Copyright 2026 Stanislav Lukyanov" in the appendix boilerplate.
- `pyproject.toml`: switch `license = { text = "MIT" }` (pyproject.toml:11) to the PEP 639
  SPDX expression `license = "Apache-2.0"` if the pinned hatchling accepts it, else
  `{ text = "Apache-2.0" }`; swap the classifier to
  `License :: OSI Approved :: Apache Software License`.
- README license section and any other MIT references (grep the repo).
- **No `NOTICE` file** — it is optional under Apache 2.0 and there are no third-party
  attributions to carry; add one later if that changes.
- No per-file license headers (none exist today; not introducing them).
- Gate: the wheel still builds (`uv build` or equivalent) with the new metadata.
