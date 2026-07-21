---
type: Task
title: Automate releases (GitHub Actions + PyPI Trusted Publishing)
description: Replace manual uv publish with a tag-triggered workflow using OIDC trusted publishing; consider a CHANGELOG.
status: Draft
priority: low
tags:
- packaging
- release
- ci
created: 2026-07-20
blocked_by:
- publish-readb-0-1-0
timestamp: '2026-07-20T00:00:00Z'
---

Deferred from the [distributable-package](distributable-package.md) design (sprint-002): 0.1.0
ships via manual `uv publish` with a maintainer-held token. When releases become routine, automate:

- GitHub Actions workflow triggered on `v*` tag push: build, `twine check`, run the test suite,
  publish to PyPI via **Trusted Publishing** (OIDC — no long-lived token secrets).
- Configure the trusted publisher on the PyPI project (exists after
  [publish-readb-0-1-0](publish-readb-0-1-0.md)).
- Decide whether a `CHANGELOG.md` earns its keep at that point, or GitHub release notes remain
  enough.
- First CI in the repo — consider whether tests-on-push comes along for the ride or stays out.
