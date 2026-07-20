# Task Bundle Log

## 2026-07-20
* **Sprint 002 design approved**: All six active tasks flipped `Draft → Designed`; sprint
  `Designing → Implementing`; [ADR 0004](../docs/adr/0004-init-registry-discovery.md)
  `Proposed → Accepted` (human, in chat). `distributable-package` design: manual `uv publish`,
  version 0.1.0; the outward-facing publishing split into special standalone task
  [publish-readb-0-1-0](publish-readb-0-1-0.md) (after the sprint, not a sprint), with
  [release-automation](release-automation.md) drafted for the eventual CI path. Design merge to
  `main`; implementation phase started.
* **Sprint 002 design phase**: `name-column-unprefix` designed — un-prefix **rejected**; `__name`
  stays immutable/filename-derived, producer `name:` is inert, name-or-path addressing with
  mandatory uniqueness (ADR 0003 affirmed, not amended). `bundle-init-discovery` designed — the
  **registry model**: one `readb init` writes `.readb/config.toml` declaring bundles; discovery
  walks up; `--bundle` stays explicit consent ([ADR 0004](../docs/adr/0004-init-registry-discovery.md),
  Proposed). New drafts from the discussions: [readme-prior-art](readme-prior-art.md),
  [field-editor-type-inference](field-editor-type-inference.md),
  [frontmatter-schema-checking](frontmatter-schema-checking.md),
  [cross-bundle-querying](cross-bundle-querying.md).

## 2026-07-17
* **Sprint 002 started**: Scope approved in chat — 7 tasks: [bundle-init-discovery](bundle-init-discovery.md),
  [distributable-package](distributable-package.md) (unblocked by choose-package-name),
  [csv-empty-result-header](csv-empty-result-header.md),
  [name-column-unprefix](name-column-unprefix.md),
  [tz-aware-datetime-handling](tz-aware-datetime-handling.md),
  [research-similar-tools](research-similar-tools.md), plus
  [rename-repo-dir](rename-repo-dir.md) — executed by the human beforehand, verified
  in-session (remote, cwd, pyproject URLs, tests green) and flipped `Draft → Done`. Created
  [sprint-002](sprint-002.md) (`Designing`, branch `sprint/002`). Design phase started.
* **Sprint 001 close-out**: All 7 delivered tasks flipped `Designed → Done`
  ([choose-package-name](choose-package-name.md), [cli-clean-errors](cli-clean-errors.md),
  [read-full-concept](read-full-concept.md), [query-csv-output](query-csv-output.md),
  [remove-id-virtual-field](remove-id-virtual-field.md),
  [schema-drop-type-mapping](schema-drop-type-mapping.md), [license-apache-2](license-apache-2.md));
  [sprint-001](sprint-001.md) flipped `Implementing → Done` with a written sprint summary.
  Gates re-run green (94 tests, `ruff` clean). Presented for final review + merge. Added draft
  [name-column-unprefix](name-column-unprefix.md), formalizing the sprint-001 open question
  (un-prefix `__name → name`) that had no backlog task.
* **Sprint 001 review follow-ups**: Made the symlink-escape refusal explicit (name *and* path
  errors now name the cause) and documented in the README that symlinks/paths resolving outside
  the bundle are unsupported. Polished NOTICE (added the product-description line). Added two
  research drafts from review questions: [csv-empty-result-header](csv-empty-result-header.md)
  (zero-row csv prints nothing — maybe a bug) and
  [tz-aware-datetime-handling](tz-aware-datetime-handling.md) (is avoiding `pytz` still right?).

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
