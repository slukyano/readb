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
timestamp: '2026-07-09T00:00:00Z'
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
