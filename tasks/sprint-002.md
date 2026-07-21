---
type: Sprint
title: Bundle init, packaging & correctness follow-ups
description: readb init + upward discovery, distributable package, zero-row csv, name un-prefix, tz-aware datetimes, similar-tools research.
status: Done
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

Second sprint under the [session/sprint workflow](workflow.md).

## Scope rationale

The two remaining medium infrastructure tasks (`bundle-init-discovery` — the sanctioned
replacement for the dropped `default-bundle-cwd`; `distributable-package` — unblocked now that
`choose-package-name` is Done), the two correctness questions raised at sprint-001's review
(`csv-empty-result-header`, `tz-aware-datetime-handling`), the sprint-001 open design question
(`name-column-unprefix`, added by the maintainer at scoping), and `research-similar-tools` (added by
the maintainer at scoping — its findings may inform the design tasks). `rename-repo-dir` was
executed by the maintainer before this sprint and verified at scoping (see its body); it is in
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

1. [x] name-column-unprefix — regression tests pinning the contract + doc line (no prod code expected)
2. [x] csv-empty-result-header — `Database.sql_table` + csv/tsv header on zero rows; tests
3. [x] tz-aware-datetime-handling — schema.py rationale fix + pytz revisit canary + JSON-fallback pin
4. [x] bundle-init-discovery — `readb init` + registry discovery + loader skips `.readb/`; tests
5. [x] dogfood init — `readb init tasks docs/adr` in this repo; commit config; docs ripple (README/CLAUDE.md/workflow.md; no `default_bundle` — explicit over magic)
6. [x] distributable-package — bump 0.1.0; `uv build`; `twine check`; clean-venv + 3.11 smoke (no uploads)
7. [x] Gates: full `pytest` + `ruff` + independent subagent review of the sprint diff (findings fixed; see summary)

## Sprint summary

Delivered all 6 active tasks (plus `rename-repo-dir`, executed by the maintainer pre-sprint and
verified at scoping). Gates green at close: **129 tests pass, `ruff` clean**. Final state built
and smoke-tested as an installable 0.1.0 wheel on Python 3.14 and the 3.11 floor.

**Features delivered (per task):**

- `bundle-init-discovery` — new `readb init [DIRS...]` (the third sanctioned write) writes a
  `.readb/config.toml` registry declaring bundles by relative path; `--bundle` is now optional
  on every command, resolved by walking up to the nearest registry (containment → innermost
  wins → sole bundle → `default_bundle` → hard error listing bundles). Explicit `--bundle`
  never consults the registry; the loader skips `.readb/`. Dogfooded: this repo's registry
  (`tasks`, `docs/adr`) is committed, deliberately without `default_bundle`
  ([ADR 0004](../docs/adr/0004-init-registry-discovery.md)).
- `csv-empty-result-header` — the sprint-001 "zero-row csv prints nothing" limitation is fixed
  as a bug: new `Database.sql_table(query) -> (columns, rows)` carries column names
  independently of rows (`sql()` is now a wrapper over it), and csv/tsv always print the
  header. Peers verified empirically: DuckDB's own writers, psql, pandas emit headers on empty;
  sqlite3 was the sole print-nothing peer. json/table/raw zero-row behavior unchanged, pinned.
- `name-column-unprefix` — **decided against the un-prefix**: `__name` stays immutable and
  filename-derived; a producer `name:` key is an inert ordinary column; doc addressing is
  always name-or-path with mandatory uniqueness (ambiguous bare name = hard error, unlike
  Obsidian's silent first-match). Behavior already matched; delivered as regression tests +
  README invariant. ADR 0003 affirmed, not amended.
- `tz-aware-datetime-handling` — hypothesis ("avoiding pytz is outdated") **refuted
  empirically**: duckdb 1.5.4 requires pytz to *fetch* any TIMESTAMPTZ value (even pure-SQL
  literals); binding is fine. JSON fallback stays; the misleading "requires pytz to bind"
  comment corrected; a revisit canary test (skipped when pytz importable) fails the day duckdb
  lifts the requirement.
- `research-similar-tools` — 11 tools surveyed (fan-out web research verified against primary
  repos/docs); the full survey lives as a durable artifact in the new **`docs/research/` OKF
  bundle** ([similar-tools](../docs/research/similar-tools.md), registered in
  `.readb/config.toml` via the live `init` merge path; the task body keeps a pointer):
  comparison across frontmatter/lifecycle/dependencies/query/CLI dimensions, dated adoption
  data (Backlog.md ~6.2k★ active; MarkdownDB ~495★ stalled; frontmatter-mcp — readb's
  architectural twin — ~1★), the transparent-disposable-index differentiator, and explicit
  adopt/reject calls. Ideas fed the four design tasks.
- `distributable-package` — version 0.1.0; `uv build` wheel+sdist, `twine check` PASSED;
  clean-venv smokes (CLI + API + init/discovery) on 3.14 and 3.11. No uploads — publishing is
  the special post-sprint task [publish-readb-0-1-0](publish-readb-0-1-0.md).

**Breaking changes:** none for existing invocations (`--bundle` keeps working everywhere);
zero-row csv/tsv output gains a header line (was: empty output) — strictly-empty-output
consumers would notice.

**Architectural decisions:** ADR 0004 (init registry + upward discovery, Accepted at design
approval). ADR 0003 explicitly affirmed on the name question without amendment.

**New tasks created this sprint:** `publish-readb-0-1-0` (special post-sprint publish),
`release-automation`, `readme-prior-art`, `field-editor-type-inference`,
`frontmatter-schema-checking`, `cross-bundle-querying` — all `Draft`, all in the backlog.

**Not done (deliberate), with homes:** publishing/TestPyPI (→ `publish-readb-0-1-0`); README
prior-art note (→ `readme-prior-art`); CI releases (→ `release-automation`); cross-bundle SQL
(→ `cross-bundle-querying`); typed `set` and schema checking (→ `field-editor-type-inference`,
`frontmatter-schema-checking`). Still-deferred backlog: `bundle-index-log-automation`,
`research-body-structured-query`.

**Review findings & resolution:** independent review of the sprint diff: 1 medium — the
registry *resolve* path enforced no containment, so a checked-in `.readb/config.toml` with
`..`/absolute/symlinked entries could point reads *and* `set`/`unset` writes outside the
registry root (init itself refused these; the read path didn't) — fixed in `load_config` with
three pinning tests. Writing the reviewer's suggested test for the multi-line-array merge
guard exposed a second real bug: the surgical merge matched the *opening* line of a multi-line
`bundles` array and corrupted the config with exit 0 — fixed (merge requires a complete
single-line array; clean error otherwise). Low findings: missing tests for two config
validation branches (added); merge-heuristic robustness and a re-init-from-different-cwd
docstring nuance (reviewed, no change needed).

**Remaining limitations & highlights (must-read):**

- From a **multi-bundle registry root**, bare commands error by design (no `default_bundle` is
  set in this repo — explicit over magic). Set `default_bundle` in `.readb/config.toml` if the
  friction annoys.
- `readb init` from a directory below an existing registry creates a **new nested registry**
  (nearest wins) rather than editing the ancestor's — git-model behavior, but can surprise.
- The config merge is surgical and only handles a **single-line** `bundles = [...]`; hand-made
  multi-line arrays read fine but must be hand-edited to extend (clean error says so).
- The pytz canary depends on pytz being absent from the dev env; if a dependency ever drags
  pytz in, the canary silently skips (by design, but the revisit signal weakens).
- `Database.sql` keeps returning dicts; `sql_table` is additive — no API break.

## Open questions

(none)

## Session log

- 2026-07-17 — Sprint scoped and approved in chat (7 tasks: 6 active + `rename-repo-dir`
  verified done and flipped). Branch `sprint/002` cut. Design phase started.
- 2026-07-17 — `research-similar-tools` executed (maintainer chose run-now): deep-research fan-out
  over 11 tools, verified against primary repos/docs. `## Findings` written into the task body;
  ideas routed to the four design tasks + a new draft `readme-prior-art` (positioning note).
  This is a research task — its findings *are* its deliverable, so it is design-complete.
- 2026-07-20 — Discussed adoption/chatter of the prior-art tools (Backlog.md ~6.2k★ active;
  MarkdownDB ~495★ stalled; frontmatter-mcp ~1★) and recorded the maintainer's transparent-disposable-
  index differentiator. Spun off drafts `field-editor-type-inference` and
  `frontmatter-schema-checking`. Designed `name-column-unprefix`: **rejected the un-prefix** —
  keep `__name` immutable/filename-derived, producer `name:` inert, doc access always name-or-path
  with mandatory uniqueness (no Obsidian-style silent first-match). Behavior already matches;
  deliverable is regression tests + a doc line, no production code change and no ADR amendment.
- 2026-07-20 — `bundle-init-discovery` designed against the real common case (one repo, several
  bundles — ours: `tasks/` + `docs/adr/`). Maintainer approved the **registry model**: single
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
  actual publishing split into special standalone task `publish-readb-0-1-0` per the maintainer —
  run after this sprint, not as a sprint; draft `release-automation` records the CI path).
  **Design approved** (maintainer, in chat: "proceed with implementation"). ADR 0004 Accepted; six
  tasks flipped `Draft → Designed`; sprint `Designing → Implementing`; design merge to `main`.
  Implementation phase started (order: name, csv, tz, init, dogfood-init, package, gates).
  Decided at implementation per design note: our repo's registry gets **no** `default_bundle`
  (explicit over magic, matching the maintainer's ambiguity-errs preference); docs keep `--bundle`
  where needed.
- 2026-07-20 — Implementation phase run end-to-end in one session: 6 steps, one commit each
  (name-contract tests; sql_table + csv header; tz rationale + canary; init/registry/discovery
  with 20 tests; dogfooded repo registry + docs; 0.1.0 bump with clean-venv 3.14/3.11 smokes).
  Gates: independent review found 1 medium (registry resolve-path containment gap — fixed,
  3 tests) and its suggested test exposed a second bug (multi-line merge corruption — fixed).
  Close-out: 6 tasks `Designed → Done`, sprint `Done`, summary written. 129 tests, ruff clean.
  Presented for final review + merge.
