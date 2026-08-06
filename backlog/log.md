# Task Bundle Log

## 2026-08-06
* **Backlog restructure**: The flat `tasks/` bundle became `backlog/` — active tasks in
  `tasks/`, closed ones in `archive/`, sprint records in `sprints/`; task concepts renamed to
  numbered `NNN-slug` names (by creation date). The [task workflow](workflow.md) and all
  internal links updated; the bundle registry now lists `backlog`.
* **Docs and entry points**: Developer docs consolidated into one `docs/dev/` bundle (design
  brief, ADRs, research; its `index.md` owns the ADR lifecycle; docs no longer link into the
  backlog). A root `DEVELOPMENT.md` now declares the map, commands, and checks once — the
  workflow's validation gate points there. Publishing surface added: `CONTRIBUTING.md`
  (discloses and waives this workflow for contributors, carries the release procedure),
  `CHANGELOG.md`, CI running the declared checks, README badges.

## 2026-07-21
* **Published**: The repo went public (github.com/slukyano/readb) after the hygiene pass, and
  [publish-readb-0-1-0](archive/022-publish-readb-0-1-0.md) executed standalone: TestPyPI rehearsal,
  PyPI publish (readb 0.1.0 live), tag `v0.1.0` + GitHub release, post-publish
  `uv tool install` smoke, README install section now PyPI-first. Task flipped
  `Draft → Done` (execution record in the task body);
  [release-automation](tasks/023-release-automation.md) is now unblocked.

## 2026-07-20
* **Publication-hygiene sweep** (pre-publication): a new hygiene gate joined the sprint reviews
  (`workflow.md` §5 — third-person project voice; factual, dated, sourced claims about other
  projects; no personal or environment leakage). Docs swept to maintainer/agent role voice;
  pre-sprint-era process artifacts and stale branches were removed; commit history was
  rewritten to drop private-link trailers.
* **Research bundle**: Created `docs/research/` (a third OKF bundle, `type: Research`) at the
  maintainer's call during final review — durable research artifacts live there, dated point-in-time
  data kept with its date. Moved the similar-tools survey into it
  ([docs/research/similar-tools.md](../docs/dev/research/similar-tools.md));
  [research-similar-tools](archive/006-research-similar-tools.md) keeps a pointer + short version.
  Registered via `readb init docs/research` (dogfooding the registry merge path live).
* **Sprint 002 close-out**: All 6 active tasks flipped `Designed → Done`
  ([bundle-init-discovery](archive/013-bundle-init-discovery.md), [csv-empty-result-header](archive/015-csv-empty-result-header.md),
  [name-column-unprefix](archive/018-name-column-unprefix.md), [tz-aware-datetime-handling](archive/020-tz-aware-datetime-handling.md),
  [research-similar-tools](archive/006-research-similar-tools.md), [distributable-package](archive/003-distributable-package.md));
  [sprint-002](sprints/sprint-002.md) flipped `Implementing → Done` with a written summary. Implementation:
  `readb init` + registry discovery (ADR 0004, dogfooded — this repo's `.readb/config.toml` committed),
  zero-row csv header via `Database.sql_table`, name contract pinned by tests, tz rationale corrected +
  pytz canary, version 0.1.0 built and clean-venv smoke-tested (3.14 + 3.11). Independent review: 1
  medium (registry resolve-path containment) fixed + a merge-corruption bug caught by its suggested
  test, also fixed. Gates green: 129 tests, ruff clean. Presented for final review + merge.
* **Sprint 002 design approved**: All six active tasks flipped `Draft → Designed`; sprint
  `Designing → Implementing`; [ADR 0004](../docs/dev/adr/0004-init-registry-discovery.md)
  `Proposed → Accepted` (maintainer, in chat). `distributable-package` design: manual `uv publish`,
  version 0.1.0; the outward-facing publishing split into special standalone task
  [publish-readb-0-1-0](archive/022-publish-readb-0-1-0.md) (after the sprint, not a sprint), with
  [release-automation](tasks/023-release-automation.md) drafted for the eventual CI path. Design merge to
  `main`; implementation phase started.
* **Sprint 002 design phase**: `name-column-unprefix` designed — un-prefix **rejected**; `__name`
  stays immutable/filename-derived, producer `name:` is inert, name-or-path addressing with
  mandatory uniqueness (ADR 0003 affirmed, not amended). `bundle-init-discovery` designed — the
  **registry model**: one `readb init` writes `.readb/config.toml` declaring bundles; discovery
  walks up; `--bundle` stays explicit consent ([ADR 0004](../docs/dev/adr/0004-init-registry-discovery.md),
  Proposed). New drafts from the discussions: [readme-prior-art](tasks/019-readme-prior-art.md),
  [field-editor-type-inference](tasks/016-field-editor-type-inference.md),
  [frontmatter-schema-checking](tasks/017-frontmatter-schema-checking.md),
  [cross-bundle-querying](tasks/021-cross-bundle-querying.md).

## 2026-07-17
* **Sprint 002 started**: Scope approved in chat — 7 tasks: [bundle-init-discovery](archive/013-bundle-init-discovery.md),
  [distributable-package](archive/003-distributable-package.md) (unblocked by choose-package-name),
  [csv-empty-result-header](archive/015-csv-empty-result-header.md),
  [name-column-unprefix](archive/018-name-column-unprefix.md),
  [tz-aware-datetime-handling](archive/020-tz-aware-datetime-handling.md),
  [research-similar-tools](archive/006-research-similar-tools.md), plus
  [rename-repo-dir](archive/014-rename-repo-dir.md) — executed by the maintainer beforehand, verified
  in-session (remote, cwd, pyproject URLs, tests green) and flipped `Draft → Done`. Created
  [sprint-002](sprints/sprint-002.md) (`Designing`, branch `sprint/002`). Design phase started.
* **Sprint 001 close-out**: All 7 delivered tasks flipped `Designed → Done`
  ([choose-package-name](archive/001-choose-package-name.md), [cli-clean-errors](archive/011-cli-clean-errors.md),
  [read-full-concept](archive/012-read-full-concept.md), [query-csv-output](archive/010-query-csv-output.md),
  [remove-id-virtual-field](archive/004-remove-id-virtual-field.md),
  [schema-drop-type-mapping](archive/007-schema-drop-type-mapping.md), [license-apache-2](archive/008-license-apache-2.md));
  [sprint-001](sprints/sprint-001.md) flipped `Implementing → Done` with a written sprint summary.
  Gates re-run green (94 tests, `ruff` clean). Presented for final review + merge. Added draft
  [name-column-unprefix](archive/018-name-column-unprefix.md), formalizing the sprint-001 open question
  (un-prefix `__name → name`) that had no backlog task.
* **Sprint 001 review follow-ups**: Made the symlink-escape refusal explicit (name *and* path
  errors now name the cause) and documented in the README that symlinks/paths resolving outside
  the bundle are unsupported. Polished NOTICE (added the product-description line). Added two
  research drafts from review questions: [csv-empty-result-header](archive/015-csv-empty-result-header.md)
  (zero-row csv prints nothing — maybe a bug) and
  [tz-aware-datetime-handling](archive/020-tz-aware-datetime-handling.md) (is avoiding `pytz` still right?).

## 2026-07-11
* **Sprint 001 review decisions**: Dropped [default-bundle-cwd](archive/002-default-bundle-cwd.md) after
  implementing it — a cwd default silently treats any directory as a bundle (maintainer decision at
  implementation review; change reverted). Added drafts:
  [bundle-init-discovery](archive/013-bundle-init-discovery.md) (explicit `readb init` + git-style upward
  discovery, marker doubles as the persistent-index home) and
  [rename-repo-dir](archive/014-rename-repo-dir.md) (special: no design, must run from the parent dir).

## 2026-07-09
* **Sprint 001 started**: Scope approved in chat — 8 tasks (the CLI/dogfooding cluster plus
  `choose-package-name` and `license-apache-2`). Created [sprint-001](sprints/sprint-001.md)
  (`Designing`, branch `sprint/001`).
* **Dogfooding rule + gap tasks**: Recorded the dogfooding rule in `workflow.md` (prefer okdb
  for the local bundles; when okdb fails, stop and record a task; okdb-blocking tasks take
  priority). Added two high-priority gap tasks found while dogfooding:
  [clean CLI errors](archive/011-cli-clean-errors.md) and [read a full concept](archive/012-read-full-concept.md).
* **Workflow committed**: Adopted the session/sprint workflow — task lifecycle
  `Draft → Designed → Done` (+ `Dropped`), sprint state in `Sprint` concepts, approvals in
  chat. Rewrote `workflow.md` accordingly and reset the open tasks to `Draft`.

## 2026-06-29
* **Initialization**: Created the `tasks/` OKF bundle, the [task workflow](workflow.md), and the
  first draft tasks. We dogfood okdb by querying this backlog with okdb itself.
