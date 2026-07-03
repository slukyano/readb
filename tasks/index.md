---
okf_version: "0.1"
---

# Process

* [Task workflow](workflow.md) - how tasks are drafted, refined, approved, implemented, and merged.

# Tasks

* [Change the license to Apache 2.0](license-apache-2.md) - swap MIT for Apache 2.0.
* [Drive the agent until done or blocked](agent-run-until-done.md) - persist until the step is complete or it must ask.
* [Let the agent request human input](agent-request-human-input.md) - pause, hand off with context, resume.
* [Handle agent unreliability](agent-reliability.md) - retries, anti-laziness, escalation.
* [Choose a package name](choose-package-name.md) - okdb is taken; pick an available distribution name.
* [Create a distributable package](distributable-package.md) - publish under the new name (blocked by: choose a package name).
* [Default --bundle to the current directory](default-bundle-cwd.md) - run commands from inside a bundle with no flag.
* [Remove the __id virtual field](remove-id-virtual-field.md) - __path is already unique and can be the primary key.
* [Drop the type mapping from `okdb schema`](schema-drop-type-mapping.md) - the original type is already shown per table.
* [Research similar task/reader tools](research-similar-tools.md) - survey Backlog.md, taskmd, and friends.
* [Research structured-body querying](research-body-structured-query.md) - expose the body as JSON/YAML/DOM by headings.
* [Fix agent-loop correctness bugs](loop-fix-correctness-bugs.md) - release-path guards, unmasked select errors, claim-push retry, pinned tooling.
* [Add a test harness for the agent loop](loop-test-harness.md) - temp repo, bare origin, scripted fake agent.
* [Make claiming non-intrusive](loop-nonintrusive-claim.md) - claim in a worktree; never touch the user's checkout (blocked by: bug fixes, test harness).
* [Harden the loop for unattended runs](loop-unattended-hardening.md) - timeout, log capture, failure UX, scheduling recipe (blocked by: test harness).
* [Add plain-text row output to okdb query](query-csv-output.md) - --csv/--tsv so shell callers skip python.
* [Keep index.md and log.md current automatically](bundle-index-log-automation.md) - generate the index; loop-appended log entries.
* [Align workflow.md with the loop](workflow-doc-alignment.md) - pr field, fast path, --task semantics, gate right-sizing.
