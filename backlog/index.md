---
okf_version: "0.1"
---

# Process

* [Task workflow](workflow.md) - sessions, sprints, design/implementation approvals, ADRs.

# Sprints

* [Sprint 003 — Post-0.1.0 adoption: usage skill, prior art, release automation](sprints/sprint-003.md) - Implementing.
* [Sprint 002 — Bundle init, packaging & correctness follow-ups](sprints/sprint-002.md) - Done.
* [Sprint 001 — CLI ergonomics, dogfooding gaps, name & license](sprints/sprint-001.md) - Done.

# Tasks

* [Fix set/unset corrupting multi-line frontmatter values](tasks/026-field-editor-multiline-corruption.md) - orphaned continuation lines make the file invalid YAML; the concept then silently disappears. Designed.
* [Research structured-body querying](tasks/005-research-body-structured-query.md) - expose the body as JSON/YAML/DOM by headings.
* [Keep index.md and log.md current automatically](tasks/009-bundle-index-log-automation.md) - generate the index; sprint-appended log entries.
* [Add a prior-art note to the README](tasks/019-readme-prior-art.md) - frontmatter-mcp, MarkdownDB, Dataview; the transparent-disposable-index differentiator. Designed.
* [Research field-editor type inference](tasks/016-field-editor-type-inference.md) - typed `set` (marad-style) vs. the string-literal stance; maybe an opt-in flag.
* [Research frontmatter schema checking](tasks/017-frontmatter-schema-checking.md) - opt-in declare/check (`readb check`); load stays permissive.
* [Research cross-bundle querying](tasks/021-cross-bundle-querying.md) - registry bundles as DuckDB schemas; joins across bundles.
* [Automate releases](tasks/023-release-automation.md) - GitHub Actions + Trusted Publishing on a `v*` tag. Designed.
* [Ship a readb usage skill with the repo](tasks/025-ship-usage-skill.md) - the repo as its own plugin marketplace; a portable `skills/readb/SKILL.md`. Designed.
* [Submit the readb plugin to the community marketplace](tasks/027-plugin-marketplace-submission.md) - public discovery, behind an external review pipeline.
* [Evaluate rewriting readb in Rust](tasks/028-evaluate-rust-rewrite.md) - binary distribution and startup vs. the Python API, YAML semantics, and rebuild cost; sequenced behind the benchmark.
* [Measure readb's efficiency gains for agents](tasks/024-measure-agent-efficiency.md) - A/B benchmark, unguided vs. readb; wall-clock and token usage on large bundles.

# Done

Standalone:

* [Publish readb 0.1.0 to PyPI](archive/022-publish-readb-0-1-0.md) - 0.1.0 live on PyPI; tag v0.1.0 + GitHub release; README installs from PyPI.
* [Rename the repo and directory to readb](archive/014-rename-repo-dir.md) - executed by the maintainer, verified at sprint-002 scoping.

Sprint 002:

* [Explicit readb init + upward bundle discovery](archive/013-bundle-init-discovery.md) - `.readb/config.toml` registry + upward discovery (ADR 0004).
* [Decide zero-row csv/tsv output](archive/015-csv-empty-result-header.md) - it was a bug; header always, via `Database.sql_table`.
* [Consider un-prefixing __name -> name](archive/018-name-column-unprefix.md) - decided against; `__name` immutable, `name:` inert, pinned by tests.
* [Revisit tz-aware datetime handling](archive/020-tz-aware-datetime-handling.md) - pytz still required to fetch TIMESTAMPTZ; JSON fallback stays, canary added.
* [Research similar task/reader tools](archive/006-research-similar-tools.md) - 11 tools surveyed; findings + adopt/reject calls in the task body.
* [Create a distributable package](archive/003-distributable-package.md) - 0.1.0 wheel/sdist built and smoke-tested; publishing → publish-readb-0-1-0.

Sprint 001:

* [Choose a package name](archive/001-choose-package-name.md) - okdb → readb, aligned dist/import/CLI.
* [Print clean CLI errors instead of Python tracebacks](archive/011-cli-clean-errors.md) - DuckDB errors as clean one-liners.
* [Read a full concept via readb](archive/012-read-full-concept.md) - `__raw` virtual column + `readb show`.
* [Add plain-text row output to readb query](archive/010-query-csv-output.md) - `--format table|json|csv|tsv|raw`.
* [Remove the __id virtual field](archive/004-remove-id-virtual-field.md) - replaced by wiki-style `__name`; `__path` is the key.
* [Drop the type mapping from `readb schema`](archive/007-schema-drop-type-mapping.md) - the original type is already shown per table.
* [Change the license to Apache 2.0](archive/008-license-apache-2.md) - Apache 2.0 text + SPDX metadata + NOTICE.

# Dropped

* [Default --bundle to the current directory](archive/002-default-bundle-cwd.md) - implemented in sprint 001, reverted at review (silent wrong-scope operations); superseded by init + discovery.
