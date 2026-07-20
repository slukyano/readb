---
okf_version: "0.1"
---

# Process

* [Task workflow](workflow.md) - sessions, sprints, design/implementation approvals, ADRs.

# Sprints

* [Sprint 002 — Bundle init, packaging & correctness follow-ups](sprint-002.md) - Designing.
* [Sprint 001 — CLI ergonomics, dogfooding gaps, name & license](sprint-001.md) - Done.

# Tasks

* [Create a distributable package](distributable-package.md) - publish under the new name (sprint 002).
* [Explicit readb init + upward bundle discovery](bundle-init-discovery.md) - the git model; marker doubles as the persistent-index home (sprint 002).
* [Research similar task/reader tools](research-similar-tools.md) - survey Backlog.md, taskmd, and friends (sprint 002).
* [Research structured-body querying](research-body-structured-query.md) - expose the body as JSON/YAML/DOM by headings.
* [Keep index.md and log.md current automatically](bundle-index-log-automation.md) - generate the index; sprint-appended log entries.
* [Consider un-prefixing __name -> name](name-column-unprefix.md) - producer-settable, inferred; sprint-001 open question (sprint 002).
* [Decide zero-row csv/tsv output](csv-empty-result-header.md) - header or nothing on empty results; maybe a bug (sprint-001 review) (sprint 002).
* [Revisit tz-aware datetime handling](tz-aware-datetime-handling.md) - is avoiding pytz still right, or can it be TIMESTAMPTZ? (sprint-001 review) (sprint 002).
* [Add a prior-art note to the README](readme-prior-art.md) - frontmatter-mcp, MarkdownDB, Dataview; the transparent-disposable-index differentiator.
* [Research field-editor type inference](field-editor-type-inference.md) - typed `set` (marad-style) vs. the string-literal stance; maybe an opt-in flag.
* [Research frontmatter schema checking](frontmatter-schema-checking.md) - opt-in declare/check (`readb check`); load stays permissive.
* [Research cross-bundle querying](cross-bundle-querying.md) - registry bundles as DuckDB schemas; joins across bundles.

# Done

Standalone:

* [Rename the repo and directory to readb](rename-repo-dir.md) - executed by the human, verified at sprint-002 scoping.

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
