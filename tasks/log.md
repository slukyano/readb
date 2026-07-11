# Task Bundle Log

## 2026-07-11
* **Sprint 001 review decisions**: Dropped [default-bundle-cwd](default-bundle-cwd.md) after
  implementing it — a cwd default silently treats any directory as a bundle (human decision at
  implementation review; change reverted). Added drafts:
  [bundle-init-discovery](bundle-init-discovery.md) (explicit `readb init` + git-style upward
  discovery, marker doubles as the persistent-index home) and
  [rename-repo-dir](rename-repo-dir.md) (special: no design, must run from the parent dir).

## 2026-07-09
* **Sprint 001 started**: Scope approved in chat — 8 tasks (the CLI/dogfooding cluster plus
  `choose-package-name` and `license-apache-2`). Created [sprint-001](sprint-001.md)
  (`Designing`, branch `sprint/001`).
* **Dogfooding rule + gap tasks**: Recorded the dogfooding rule in `workflow.md` (prefer okdb
  for the local bundles; when okdb fails, stop and record a task; okdb-blocking tasks take
  priority). Added two high-priority gap tasks found while dogfooding:
  [clean CLI errors](cli-clean-errors.md) and [read a full concept](read-full-concept.md).
* **Workflow change**: Replaced the PR-per-step agent loop with the session/sprint workflow
  ([ADR 0001](../docs/adr/0001-sessions-sprints-workflow.md)). Rewrote `workflow.md`; task
  lifecycle is now `Draft → Designed → Done` (+ `Dropped`), sprint state lives in `Sprint`
  concepts. Deleted `scripts/agent-loop.sh`, closed the 15 open refine PRs unmerged (branches
  kept as design input), reset the surviving claimed tasks to `Draft`, and dropped the eight
  loop-era tasks.

## 2026-07-02
* **Agent-loop review**: Added seven draft tasks from a review of the agent loop and the task
  workflow — correctness fixes, a loop test harness, non-intrusive claiming, unattended-run
  hardening, plain-text query output, index/log automation, and workflow-doc alignment.

## 2026-06-29
* **Initialization**: Created the `tasks/` OKF bundle, the [task workflow](/workflow.md), and the
  first seven draft tasks. We dogfood okdb by querying this backlog with okdb itself.
