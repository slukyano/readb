---
type: Task
title: Choose a package name (okdb is taken)
description: Pick and verify an available distribution name; okdb is already taken on PyPI.
status: Draft
priority: high
tags:
- packaging
- naming
created: 2026-06-29
blocked_by: []
timestamp: '2026-07-09T00:00:00Z'
---

`okdb` is taken on PyPI, so we need a different distribution name before we can publish.

This task **blocks** [Create a distributable package](/distributable-package.md).

## Context

- The import package and the CLI binary can keep `okdb` locally, but the *distribution* name
  must be unique on the index we publish to.
- Want a short, memorable name that still signals "OKF + SQL".

## Notes / candidates (to refine)

- Confirm availability on PyPI before committing.
- Decide whether the CLI command and the import name change too, or only the dist name.
