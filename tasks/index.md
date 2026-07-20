---
okf_version: "0.1"
---

# Process

* [Task workflow](workflow.md) - sessions, sprints, design/implementation approvals, ADRs.

# Sprints

* [Sprint 002 — Bundle init, packaging & correctness follow-ups](sprint-002.md) - Done.
* [Sprint 001 — CLI ergonomics, dogfooding gaps, name & license](sprint-001.md) - Done.

# Tasks

* [Research structured-body querying](research-body-structured-query.md) - expose the body as JSON/YAML/DOM by headings.
* [Keep index.md and log.md current automatically](bundle-index-log-automation.md) - generate the index; sprint-appended log entries.
* [Add a prior-art note to the README](readme-prior-art.md) - frontmatter-mcp, MarkdownDB, Dataview; the transparent-disposable-index differentiator.
* [Research field-editor type inference](field-editor-type-inference.md) - typed `set` (marad-style) vs. the string-literal stance; maybe an opt-in flag.
* [Research frontmatter schema checking](frontmatter-schema-checking.md) - opt-in declare/check (`readb check`); load stays permissive.
* [Research cross-bundle querying](cross-bundle-querying.md) - registry bundles as DuckDB schemas; joins across bundles.
* [Publish readb 0.1.0 to PyPI](publish-readb-0-1-0.md) - special standalone task after sprint 002; TestPyPI rehearsal + publish + tag.
* [Automate releases](release-automation.md) - GitHub Actions + Trusted Publishing, once releases are routine.

# Done

Standalone:

* [Rename the repo and directory to readb](rename-repo-dir.md) - executed by the human, verified at sprint-002 scoping.

Sprint 002:

* [Explicit readb init + upward bundle discovery](bundle-init-discovery.md) - `.readb/config.toml` registry + upward discovery (ADR 0004).
* [Decide zero-row csv/tsv output](csv-empty-result-header.md) - it was a bug; header always, via `Database.sql_table`.
* [Consider un-prefixing __name -> name](name-column-unprefix.md) - decided against; `__name` immutable, `name:` inert, pinned by tests.
* [Revisit tz-aware datetime handling](tz-aware-datetime-handling.md) - pytz still required to fetch TIMESTAMPTZ; JSON fallback stays, canary added.
* [Research similar task/reader tools](research-similar-tools.md) - 11 tools surveyed; findings + adopt/reject calls in the task body.
* [Create a distributable package](distributable-package.md) - 0.1.0 wheel/sdist built and smoke-tested; publishing → publish-readb-0-1-0.

Sprint 001:

* [Choose a package name](choose-package-name.md) - okdb → readb, aligned dist/import/CLI.
* [Print clean CLI errors instead of Python tracebacks](cli-clean-errors.md) - DuckDB errors as clean one-liners.
* [Read a full concept via readb](read-full-concept.md) - `__raw` virtual column + `readb show`.
* [Add plain-text row output to readb query](query-csv-output.md) - `--format table|json|csv|tsv|raw`.
* [Remove the __id virtual field](remove-id-virtual-field.md) - replaced by wiki-style `__name`; `__path` is the key.
* [Drop the type mapping from `readb schema`](schema-drop-type-mapping.md) - the original type is already shown per table.
* [Change the license to Apache 2.0](license-apache-2.md) - Apache 2.0 text + SPDX metadata + NOTICE.

# Dropped

* [Default --bundle to the current directory](default-bundle-cwd.md) - implemented in sprint 001, reverted at review (silent wrong-scope operations); superseded by init + discovery.

Loop-era tasks retired with the agent loop ([ADR 0001](../docs/adr/0001-sessions-sprints-workflow.md)):

* [Drive the agent until done or blocked](agent-run-until-done.md)
* [Let the agent request human input](agent-request-human-input.md)
* [Handle agent unreliability](agent-reliability.md)
* [Fix agent-loop correctness bugs](loop-fix-correctness-bugs.md)
* [Add a test harness for the agent loop](loop-test-harness.md)
* [Make claiming non-intrusive](loop-nonintrusive-claim.md)
* [Harden the loop for unattended runs](loop-unattended-hardening.md)
* [Align workflow.md with the loop](workflow-doc-alignment.md)
