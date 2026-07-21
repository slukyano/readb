# Task Bundle Log

## 2026-07-21
* **Published**: The repo went public (github.com/slukyano/readb) after the hygiene pass, and
  [publish-readb-0-1-0](publish-readb-0-1-0.md) executed standalone: TestPyPI rehearsal,
  PyPI publish (readb 0.1.0 live), tag `v0.1.0` + GitHub release, post-publish
  `uv tool install` smoke, README install section now PyPI-first. Task flipped
  `Draft → Done` (execution record in the task body);
  [release-automation](release-automation.md) is now unblocked.

## 2026-07-20
* **Publication-hygiene sweep** (pre-publication): a new hygiene gate joined the sprint reviews
  (`workflow.md` §5 — third-person project voice; factual, dated, sourced claims about other
  projects; no personal or environment leakage). Docs swept to maintainer/agent role voice;
  pre-sprint-era process artifacts and stale branches were removed; commit history was
  rewritten to drop private-link trailers.
* **Research bundle**: Created `docs/research/` (a third OKF bundle, `type: Research`) at the
  maintainer's call during final review — durable research artifacts live there, dated point-in-time
  data kept with its date. Moved the similar-tools survey into it
  ([docs/research/similar-tools.md](../docs/research/similar-tools.md));
  [research-similar-tools](research-similar-tools.md) keeps a pointer + short version.
  Registered via `readb init docs/research` (dogfooding the registry merge path live).
* **Sprint 002 close-out**: All 6 active tasks flipped `Designed → Done`
  ([bundle-init-discovery](bundle-init-discovery.md), [csv-empty-result-header](csv-empty-result-header.md),
  [name-column-unprefix](name-column-unprefix.md), [tz-aware-datetime-handling](tz-aware-datetime-handling.md),
  [research-similar-tools](research-similar-tools.md), [distributable-package](distributable-package.md));
  [sprint-002](sprint-002.md) flipped `Implementing → Done` with a written summary. Implementation:
  `readb init` + registry discovery (ADR 0004, dogfooded — this repo's `.readb/config.toml` committed),
  zero-row csv header via `Database.sql_table`, name contract pinned by tests, tz rationale corrected +
  pytz canary, version 0.1.0 built and clean-venv smoke-tested (3.14 + 3.11). Independent review: 1
  medium (registry resolve-path containment) fixed + a merge-corruption bug caught by its suggested
  test, also fixed. Gates green: 129 tests, ruff clean. Presented for final review + merge.
* **Sprint 002 design approved**: All six active tasks flipped `Draft → Designed`; sprint
  `Designing → Implementing`; [ADR 0004](../docs/adr/0004-init-registry-discovery.md)
  `Proposed → Accepted` (maintainer, in chat). `distributable-package` design: manual `uv publish`,
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
  [rename-repo-dir](rename-repo-dir.md) — executed by the maintainer beforehand, verified
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
  implementing it — a cwd default silently treats any directory as a bundle (maintainer decision at
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
* **Workflow committed**: Adopted the session/sprint workflow — task lifecycle
  `Draft → Designed → Done` (+ `Dropped`), sprint state in `Sprint` concepts, approvals in
  chat. Rewrote `workflow.md` accordingly and reset the open tasks to `Draft`.

## 2026-06-29
* **Initialization**: Created the `tasks/` OKF bundle, the [task workflow](/workflow.md), and the
  first draft tasks. We dogfood okdb by querying this backlog with okdb itself.
