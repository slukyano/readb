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
