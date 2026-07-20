---
type: Sprint
title: Bundle init, packaging & correctness follow-ups
description: readb init + upward discovery, distributable package, zero-row csv, name un-prefix, tz-aware datetimes, similar-tools research.
status: Implementing
branch: sprint/002
tasks:
- bundle-init-discovery
- distributable-package
- csv-empty-result-header
- name-column-unprefix
- tz-aware-datetime-handling
- research-similar-tools
- rename-repo-dir
created: 2026-07-17
timestamp: '2026-07-20T00:00:00Z'
---

Second sprint under the session/sprint workflow
([ADR 0001](../docs/adr/0001-sessions-sprints-workflow.md)).

## Scope rationale

The two remaining medium infrastructure tasks (`bundle-init-discovery` — the sanctioned
replacement for the dropped `default-bundle-cwd`; `distributable-package` — unblocked now that
`choose-package-name` is Done), the two correctness questions raised at sprint-001's review
(`csv-empty-result-header`, `tz-aware-datetime-handling`), the sprint-001 open design question
(`name-column-unprefix`, added by the human at scoping), and `research-similar-tools` (added by
the human at scoping — its findings may inform the design tasks). `rename-repo-dir` was
executed by the human before this sprint and verified at scoping (see its body); it is in
scope as bookkeeping only, already `Done`. Still deferred: `bundle-index-log-automation`,
`research-body-structured-query` (low).

## Task checklist

Design phase (a checked box = `## Design` section written and discussed):

- [x] research-similar-tools — surveyed 11 tools; `## Findings` written; ideas mapped to designs + draft `readme-prior-art`
- [x] bundle-init-discovery — registry model designed: `readb init` writes `.readb/config.toml` declaring bundles; discovery walks up; ADR 0004 Proposed
- [x] name-column-unprefix — decided: keep `__name` immutable, `name:` inert, name-or-path addressing w/ mandatory uniqueness; no un-prefix, no ADR change
- [x] csv-empty-result-header — decided: bug; header on zero rows via new `Database.sql_table` (DuckDB/psql/pandas precedent, sqlite3 sole dissenter)
- [x] tz-aware-datetime-handling — verified: pytz still required to FETCH any TIMESTAMPTZ (duckdb 1.5.4); keep JSON fallback, fix comment, add revisit canary
- [x] distributable-package — manual `uv publish` (0.1.0); in-sprint = build + clean-env/3.11 smoke; uploads live in special task `publish-readb-0-1-0`
- [x] rename-repo-dir — no design (special task; already Done)

## Implementation checklist (in order)

1. [ ] name-column-unprefix — regression tests pinning the contract + doc line (no prod code expected)
2. [ ] csv-empty-result-header — `Database.sql_table` + csv/tsv header on zero rows; tests
3. [ ] tz-aware-datetime-handling — schema.py rationale fix + pytz revisit canary + JSON-fallback pin
4. [ ] bundle-init-discovery — `readb init` + registry discovery + loader skips `.readb/`; tests
5. [ ] dogfood init — `readb init tasks docs/adr` in this repo; commit config; docs ripple (README/CLAUDE.md/workflow.md; no `default_bundle` — explicit over magic)
6. [ ] distributable-package — bump 0.1.0; `uv build`; `twine check`; clean-venv + 3.11 smoke (no uploads)
7. [ ] Gates: full `pytest` + `ruff` + independent subagent review of the sprint diff

## Open questions

(none)

## Session log

- 2026-07-17 — Sprint scoped and approved in chat (7 tasks: 6 active + `rename-repo-dir`
  verified done and flipped). Branch `sprint/002` cut. Design phase started.
- 2026-07-17 — `research-similar-tools` executed (human chose run-now): deep-research fan-out
  over 11 tools, verified against primary repos/docs. `## Findings` written into the task body;
  ideas routed to the four design tasks + a new draft `readme-prior-art` (positioning note).
  This is a research task — its findings *are* its deliverable, so it is design-complete.
- 2026-07-20 — Discussed adoption/chatter of the prior-art tools (Backlog.md ~6.2k★ active;
  MarkdownDB ~495★ stalled; frontmatter-mcp ~1★) and recorded the human's transparent-disposable-
  index differentiator. Spun off drafts `field-editor-type-inference` and
  `frontmatter-schema-checking`. Designed `name-column-unprefix`: **rejected the un-prefix** —
  keep `__name` immutable/filename-derived, producer `name:` inert, doc access always name-or-path
  with mandatory uniqueness (no Obsidian-style silent first-match). Behavior already matches;
  deliverable is regression tests + a doc line, no production code change and no ADR amendment.
- 2026-07-20 — `bundle-init-discovery` designed against the real common case (one repo, several
  bundles — ours: `tasks/` + `docs/adr/`). Human approved the **registry model**: single
  `readb init [DIRS...]` writes `.readb/config.toml` (`version`, `bundles`, optional
  `default_bundle`); discovery walks up to the nearest registry, picks by containment → sole
  bundle → default → hard error listing bundles; `--bundle` never consults the registry; loader
  skips `.readb/`. ADR 0004 written (Proposed). Spun off draft `cross-bundle-querying`
  (bundles as DuckDB schemas). Fixed a typo in `docs/adr/index.md` (0003: "__id removed").
- 2026-07-20 — Empirical designs for the two correctness tasks. `csv-empty-result-header`:
  verified DuckDB emits headers on zero rows (COPY/write_csv) while sqlite3 emits nothing —
  decided header-always via a new `Database.sql_table() -> (columns, rows)` sibling; json/table/
  raw unchanged; no ADR. `tz-aware-datetime-handling`: hypothesis refuted — duckdb 1.5.4 still
  requires pytz to *fetch* (not bind) any TIMESTAMPTZ, verified live; keep the JSON fallback,
  correct the schema.py rationale, add a skipped-if-pytz revisit canary; no ADR. Both designs
  pending batch design approval.
- 2026-07-20 — `distributable-package` designed (manual publish, 0.1.0, TestPyPI rehearsal; the
  actual publishing split into special standalone task `publish-readb-0-1-0` per the human —
  run after this sprint, not as a sprint; draft `release-automation` records the CI path).
  **Design approved** (human, in chat: "proceed with implementation"). ADR 0004 Accepted; six
  tasks flipped `Draft → Designed`; sprint `Designing → Implementing`; design merge to `main`.
  Implementation phase started (order: name, csv, tz, init, dogfood-init, package, gates).
  Decided at implementation per design note: our repo's registry gets **no** `default_bundle`
  (explicit over magic, matching the human's ambiguity-errs preference); docs keep `--bundle`
  where needed.
