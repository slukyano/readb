---
type: Task
title: Research similar markdown+frontmatter task/reader tools
description: Survey Backlog.md, taskmd, and similar wrappers for ideas worth adopting.
status: Draft
priority: low
tags:
- research
created: 2026-06-29
blocked_by: []
timestamp: '2026-07-09T00:00:00Z'
---

Survey existing tools that read/manage markdown-with-frontmatter (especially task managers and
knowledge-base readers) to see what conventions and features we should adopt.

## Context

- Starting points: **Backlog.md**, **taskmd**. Also worth a look: Obsidian Dataview, Foam,
  Dendron, and any "markdown-as-database" projects.
- We care about: frontmatter conventions, status/lifecycle modeling, dependency handling,
  querying ergonomics, and CLI/UX patterns.

## Notes (to refine)

- Produce a short comparison and a concrete list of ideas to bring into okdb / this workflow.

## Findings (2026-07-17, sprint-002 design phase)

Surveyed 11 tools via a fan-out web search verified against each tool's own repo/docs.
Confidence: the Backlog.md and taskmd claims were adversarially verified (2–3 independent
votes each); the Dataview / Foam / Dendron / MarkdownDB / frontmatter-mcp / mdbasequery / yq /
Taskmatter / marad claims are single-extraction from the primary repo or official docs
(sourced, not vote-verified — the verify pass ran out of budget). Sources are listed at the
end.

### The landscape

Two tools sit almost exactly on readb's spot and are the most important finds:

- **frontmatter-mcp** (`kzmshx/frontmatter-mcp`) — "An MCP server for querying Markdown
  frontmatter with **DuckDB SQL**." Same engine, same data model as readb; packaged as an MCP
  server rather than a CLI/library. Proof the exact approach is viable — and that readb's
  differentiation is *packaging* (read-only CLI + Python API + surgical field editor, OKF-shaped),
  not the core idea.
- **MarkdownDB** (`datopian/markdowndb`) — a JS/TS library that indexes a markdown folder into a
  real SQL database (SQLite by default; MySQL/Postgres via Knex) and lets you run raw SQL over
  the index tables (e.g. join `files` with `file_tags`). Same "load markdown into an embedded
  SQL engine, let the engine execute the SQL" architecture readb uses — but an on-disk index +
  JS API vs. readb's in-memory DuckDB + CLI.

The rest cluster into three groups:

- **Markdown task managers** — **Backlog.md** (`MrLesk`), **taskmd** (`driangle`), **Taskmatter**
  (`mtoohey31`). One file per task, YAML frontmatter, dependencies as a list of ids. None expose
  a query *language*; all query via fixed CLI flags/subcommands.
- **Note/KB tools** — **Obsidian Dataview**, **Foam**, **Dendron**. Dataview is the notable
  query-language alternative to SQL; Foam/Dendron are mostly relevant for *identity* conventions.
- **Frontmatter editors / other query engines** — **marad/frontmatter** (Go get/set/delete CLI),
  **mdbasequery** (Obsidian-Bases query engine, not SQL), **yq** (general YAML CLI with a
  front-matter mode).

### Comparison across the five dimensions

**1. Frontmatter conventions & identity.** All task tools duplicate an `id` in both frontmatter
and filename (Backlog.md: `id: BACK-200` + `back-200 - ....md`; taskmd: `id: "001"`). Dates are
strings, typed only when ISO-8601. The interesting split is *display identity vs. address
identity*:
- **Foam**: a `title:` frontmatter key **overrides the filename** as the note's display name in
  the graph, but wikilinks still resolve by **filename** — i.e. producer-settable display name,
  filename stays the address. This is exactly the `name-column-unprefix` proposal.
- **Dendron**: auto-generates an immutable `id` (23-char, the one field a user may not change)
  and *derives* `title` from the filename — identity and display are separate fields.
- **Taskmatter**: namespaces all tool-owned metadata under a single `_tm` key, using an
  underscore prefix to signal "other programs shouldn't touch this" — independent convergence on
  readb's `__`-prefix-means-reader-owned invariant.

**2. Status / lifecycle.** Backlog.md does *not* hardcode statuses — they're declared centrally
in a config file (`statuses: [...]`, `default_status`) and double as kanban columns. taskmd uses
free per-file `status:` values. Neither models a transition graph in files; the states live in
config or convention. (readb stays out of this — lifecycle is the *bundle's* concern, e.g. our
`Draft→Designed→Done`, not readb's.)

**3. Dependencies / blocking.** Universal pattern: a `dependencies`/`blocked_by` YAML list of
ids on the depending item. Backlog.md **validates that referenced deps exist** and tracks which
are still blocking; taskmd **computes** over the graph — critical paths, auto blocked/blocking
detection, and a `next` command that recommends the next actionable task. readb already has
`blocked_by`; the "next actionable / unblocked" computation is a *query recipe*, not an engine
feature (our workflow.md already ships one).

**4. Query ergonomics.** Real divergence here. **Dataview's DQL** is the main non-SQL model:
four query types (`TABLE`/`LIST`/`TASK`/`CALENDAR`), the query type is the only mandatory
element, and data commands (`FROM`/`WHERE`/`SORT`/`GROUP BY`/`LIMIT`/`FLATTEN`) execute *in
written order* — unlike SQL's fixed clause order and set semantics. Frontmatter keys are
referenced **bare/unquoted** (`date(creadate)`, not `date("creadate")`), and DQL exposes
**implicit file metadata** as queryable fields (`file.name`, `file.cday`) — direct precedent for
readb's virtual columns (`__name`, `__path`). Every task manager, by contrast, is
flag/subcommand filtering (`backlog task list -s "To Do"`, `taskmd list`), not a language.
readb's real-SQL-via-DuckDB choice buys joins/aggregates/window functions none of these have —
a deliberate, defensible divergence (and already a hard constraint: never write a query language).

**5. CLI/UX — init, discovery, output.** Directly feeds `bundle-init-discovery`:
- **Backlog.md** has an explicit `backlog init` that lets you pick the folder (`backlog/`,
  `.backlog/`, or custom) *and* config location, **preserves existing config on re-init**, and
  is scriptable via `--backlog-dir`/`--config-location`.
- **Obsidian** marks a vault with a `.obsidian/` directory; **Dendron** creates a workspace with
  an explicit init step; **taskmd** reportedly cascades config project → `~/.taskmd.yaml`
  (unverified). The dotdir-marker + explicit-init pattern is the established norm — validates the
  proposed `.readb/` marker.
- **Output/errors — feeds `csv-empty-result-header`**: Backlog.md publishes a strict `--json`
  contract worth emulating in spirit — a **versioned envelope**, missing scalars → `null`,
  missing collections → `[]`, date-only stays `YYYY-MM-DD`, datetimes RFC-3339; `--json`/`--plain`
  are mutually exclusive; JSON is always non-interactive; **errors leave stdout empty**, write to
  stderr, exit nonzero. The load-bearing point for our open question: **structure is preserved
  even when empty** (an empty result is `[]`, never *nothing*) — evidence for "emit the header
  row on zero rows."
- **marad/frontmatter** mirrors readb's `get`/`set`/`unset` triad but **infers YAML types from
  CLI syntax** (`count=42`→int, `tags=[a,b]`→list, `published=true`→bool) — the opposite of
  readb's deliberately string-literal, never-guess field editor.

### Ideas — adopt / feed / reject

**Feeds a sprint-002 design (cited there):**

1. `name-column-unprefix` ← **Foam's `title`-overrides-filename** (producer-settable display
   name, filename stays the address) is precedent for a producer-settable `name` with `__path`
   as the invariant key; **Dendron's** separate immutable-id / derived-title split is a second
   data point; **Taskmatter's `_tm`** underscore-namespace independently validates keeping `__`
   for purely reader-owned columns.
2. `bundle-init-discovery` ← **Backlog.md `init`** (pick folder, config *inside* the marker dir,
   preserve-on-re-init, scriptable flags) and the **`.obsidian/`/`.backlog/` dotdir-marker** norm.
3. `csv-empty-result-header` ← **Backlog.md's output contract** — structure preserved when
   empty (`[]`, never nothing); errors to stderr with empty stdout + nonzero exit. Points toward
   "header on zero rows."
4. `tz-aware-datetime-handling` ← minor: **Dataview** only types a value as a date when it's
   ISO-8601 (with a `T` for datetimes); peers are strict about ISO for date typing.

**Adopt as positioning (no code):**

5. A README "prior art / how readb differs" note citing **frontmatter-mcp** (same DuckDB-SQL
   engine, MCP-packaged), **MarkdownDB** (same load-into-SQL architecture, JS/on-disk), and
   **Dataview** (the DQL alternative) — readb's niche is the *read-only CLI + Python API +
   surgical field editor over an OKF bundle*, not a novel engine. → captured as new draft
   **`readme-prior-art`**.

**Consciously reject:**

6. **A query DSL (Dataview-style DQL).** readb runs real SQL on DuckDB by hard constraint; DQL's
   ordered-data-command grammar is strictly less powerful for joins/aggregates. Reject.
7. **Type-inference in the field editor** (marad-style `key=42`→int). readb's field editor is
   deliberately line-based and string-literal ("never guess producer intent"). Reject — but the
   choice deserves one explicit sentence in the editor's docs. → folded into `readme-prior-art`
   (document the deliberate non-inference), not its own task.
8. **Central status config / lifecycle modeling** (Backlog.md). Lifecycle is a property of the
   *bundle's* schema (our workflow's `Draft→Designed→Done`), not of readb the reader. Reject.
9. **Dependency validation / critical-path computation in the engine** (Backlog.md, taskmd).
   These are *queries* over `blocked_by`, and readb is a read-only SQL layer — a "next unblocked
   task" recipe already lives in workflow.md. Nothing to build. Reject as an engine feature.

### Adoption & maturity (checked 2026-07-17)

- **Backlog.md** — **~6.2k stars, 372 forks**, TypeScript, MIT. Very active: v1.48.0 released
  2026-07-12 (days ago), ~1,026 commits, on Homebrew (`backlog-md`), has a community VS Code
  extension. Real traction and a
  [Hacker News launch thread](https://news.ycombinator.com/item?id=44483530) (positive; users
  asked for dependency management and Jira/OpenRouter integration). The most mature/adopted tool
  in the survey by a wide margin.
- **MarkdownDB** (`datopian/markdowndb`) — **~495 stars, 25 forks**, TypeScript, npm `mddb`.
  But **stalled**: latest release v0.9.5 is from **March 2024** (~2.3 years stale), pre-1.0, 9
  open issues / 0 PRs. Moderate one-time interest, little current momentum.
- **frontmatter-mcp** (`kzmshx/frontmatter-mcp`) — **1 star, 2 forks**. Effectively zero
  adoption; a personal project (Python, DuckDB, v0.5.3 Dec 2025). Architecturally it's the
  closest twin to readb, but the niche is validated-yet-unclaimed in practice.

**Positioning takeaway (readb's actual differentiator).** The DuckDB-SQL-over-frontmatter idea
is *proven viable but essentially unadopted* (frontmatter-mcp), and the one tool with real users
in the "markdown-as-SQL" space (MarkdownDB) builds a **managed on-disk index** you regenerate and
maintain. readb's distinction is that **the index is transparent and disposable** — in-memory
today (a wrapped `.readb/` cache later), never a database the user manages: you point at a
directory and query. That "you never manage a DB" framing — plus read-only-load, permissive
lossless parsing, the one narrow write path, and OKF shape — is the niche, and it's open. Folded
into draft `readme-prior-art`.

### Sources

Primary repos/docs: `github.com/MrLesk/Backlog.md` (+ `CLI-INSTRUCTIONS.md`),
`github.com/driangle/taskmd` (+ `driangle.github.io/taskmd`), `github.com/mtoohey31/taskmatter`,
`github.com/marad/frontmatter`, `blacksmithgu.github.io/obsidian-dataview`,
`github.com/blacksmithgu/obsidian-dataview`, `foambubble.github.io/foam`, `wiki.dendron.so`,
`github.com/datopian/markdowndb` (+ `markdowndb.com`), `github.com/kzmshx/frontmatter-mcp`,
`github.com/intellectronica/mdbasequery`, `mikefarah.gitbook.io/yq`.
