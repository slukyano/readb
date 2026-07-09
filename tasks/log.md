# Task Bundle Log

## 2026-07-09
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
