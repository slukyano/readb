---
okf_version: "0.1"
---

# Process

* [Task workflow](workflow.md) - sessions, sprints, design/implementation approvals, ADRs.

# Tasks

* [Print clean CLI errors instead of Python tracebacks](cli-clean-errors.md) - failed queries dump raw DuckDB tracebacks.
* [Read a full concept via okdb](read-full-concept.md) - no ergonomic frontmatter+body read; forces cat fallbacks.
* [Change the license to Apache 2.0](license-apache-2.md) - swap MIT for Apache 2.0.
* [Choose a package name](choose-package-name.md) - okdb is taken; pick an available distribution name.
* [Create a distributable package](distributable-package.md) - publish under the new name (blocked by: choose a package name).
* [Default --bundle to the current directory](default-bundle-cwd.md) - run commands from inside a bundle with no flag.
* [Remove the __id virtual field](remove-id-virtual-field.md) - __path is already unique and can be the primary key.
* [Drop the type mapping from `okdb schema`](schema-drop-type-mapping.md) - the original type is already shown per table.
* [Research similar task/reader tools](research-similar-tools.md) - survey Backlog.md, taskmd, and friends.
* [Research structured-body querying](research-body-structured-query.md) - expose the body as JSON/YAML/DOM by headings.
* [Add plain-text row output to okdb query](query-csv-output.md) - --csv/--tsv so shell callers skip python.
* [Keep index.md and log.md current automatically](bundle-index-log-automation.md) - generate the index; sprint-appended log entries.

# Dropped

Loop-era tasks retired with the agent loop ([ADR 0001](../docs/adr/0001-sessions-sprints-workflow.md)):

* [Drive the agent until done or blocked](agent-run-until-done.md)
* [Let the agent request human input](agent-request-human-input.md)
* [Handle agent unreliability](agent-reliability.md)
* [Fix agent-loop correctness bugs](loop-fix-correctness-bugs.md)
* [Add a test harness for the agent loop](loop-test-harness.md)
* [Make claiming non-intrusive](loop-nonintrusive-claim.md)
* [Harden the loop for unattended runs](loop-unattended-hardening.md)
* [Align workflow.md with the loop](workflow-doc-alignment.md)
