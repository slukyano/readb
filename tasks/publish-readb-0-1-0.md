---
type: Task
title: Publish readb 0.1.0 to PyPI
description: Special post-sprint task - TestPyPI rehearsal, PyPI publish, tag v0.1.0 + GitHub release. Run standalone after sprint-002 merges.
status: Draft
priority: medium
tags:
- packaging
- release
- special
created: 2026-07-20
blocked_by:
- distributable-package
timestamp: '2026-07-20T00:00:00Z'
---

**Special task — not a normal sprint.** Run as a single standalone task after sprint-002's
final merge, from `main`. The build/verification legwork happens in-sprint
([distributable-package](distributable-package.md)); this task is the outward-facing publish.
Every upload is a **stop-and-ask** — the maintainer holds the PyPI/TestPyPI credentials and gives
the explicit go for each push.

## Steps

1. Preconditions: sprint-002 merged to `main`; version is `0.1.0`; gates green on `main`
   (`uv run pytest`, `uv run ruff check`).
2. **Name check**: re-verify `readb` is still available on PyPI (ADR 0002 deferred certainty to
   this moment). Taken since → stop and ask (fallback candidates in ADR 0002).
3. Fresh `uv build` from the tagged state; `twine check`.
4. **TestPyPI rehearsal**: `uv publish` to TestPyPI (maintainer provides token / runs it);
   `pip install --index-url https://test.pypi.org/simple/ readb` into a scratch venv; smoke
   (`readb --help`, a query, a `set`/`get` round-trip).
5. **PyPI publish**: `uv publish` (maintainer go + credentials).
6. Tag `v0.1.0` on the published commit; GitHub release with notes distilled from the
   sprint-001/002 summaries.
7. Post-publish smoke: `uv tool install readb` from PyPI in a clean environment; `readb --help`.
8. README: add the `pip install readb` / `uv tool install readb` install section (replacing the
   from-clone-only instructions as the primary path).
