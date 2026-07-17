---
type: Task
title: Rename the repo and working directory to readb
description: Rename the GitHub repo and the local directory okdb -> readb. Special task - no design; must run from the parent directory.
status: Draft
priority: medium
tags:
- meta
- naming
created: 2026-07-11
timestamp: '2026-07-11T00:00:00Z'
---

Finish ADR 0002's rename outside the code: the GitHub repository and the local working
directory are still `okdb`.

**Special task — no design phase needed.** But it has an execution constraint: the agent must
be launched in the **parent directory** (`~/workspaces/personal`), not inside the repo — you
cannot rename the directory you are standing in without breaking the running session (cwd,
open file handles, tool state).

## Steps (mechanical)

1. From the parent dir: `gh repo rename readb --repo slukyano/okdb` (GitHub keeps a redirect;
   `gh` updates the local `origin` remote automatically when run inside the clone — verify
   `git remote -v` afterwards, expect `slukyano/readb`).
2. `mv okdb readb` (locally).
3. Sanity: `cd readb && git status && uv run pytest -q`.
4. Check for absolute-path references to the old directory (IDE workspaces, shell profiles,
   `pyproject.toml` has none — the venv is path-relative but `uv sync` re-links if needed).
