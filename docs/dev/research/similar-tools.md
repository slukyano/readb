---
type: Research
title: Similar markdown+frontmatter tools — survey, comparison, and adoption
description: 11 tools surveyed (task managers, KB readers, markdown-as-database); conventions compared, adoption measured, adopt/reject calls for readb.
tags:
- prior-art
- survey
surveyed: 2026-07-17
created: 2026-07-20
timestamp: '2026-07-20T00:00:00Z'
---

Produced by the backlog task `research-similar-tools` (sprint-002) via a
fan-out web survey verified against each tool's own repo/docs. Point-in-time data (star counts,
maintenance status) is dated inline — true as of the date given, worth keeping *with* the date.

Confidence: the Backlog.md and taskmd claims were adversarially verified (2–3 independent
votes each); the Dataview / Foam / Dendron / MarkdownDB / frontmatter-mcp / mdbasequery / yq /
Taskmatter / marad claims are single-extraction from the primary repo or official docs.

# The landscape

Two tools sit almost exactly on readb's spot and are the most important finds:

- **frontmatter-mcp** (`kzmshx/frontmatter-mcp`) — "An MCP server for querying Markdown
  frontmatter with **DuckDB SQL**." Same engine, same data model as readb; packaged as an MCP
  server rather than a CLI/library. Proof the exact approach is viable — and that readb's
  differentiation is *packaging*, not the core idea.
- **MarkdownDB** (`datopian/markdowndb`) — a JS/TS library that indexes a markdown folder into a
  real SQL database (SQLite by default; MySQL/Postgres via Knex) and lets you run raw SQL over
  the index tables (e.g. join `files` with `file_tags`). Same "load markdown into an embedded
  SQL engine" architecture — but a managed on-disk index + JS API vs. readb's transparent
  in-memory DuckDB + CLI.

The rest cluster into three groups:

- **Markdown task managers** — **Backlog.md** (`MrLesk`), **taskmd** (`driangle`), **Taskmatter**
  (`mtoohey31`). One file per task, YAML frontmatter, dependencies as a list of ids. None expose
  a query *language*; all query via fixed CLI flags/subcommands.
- **Note/KB tools** — **Obsidian Dataview**, **Foam**, **Dendron**. Dataview is the notable
  query-language alternative to SQL; Foam/Dendron are mostly relevant for *identity* conventions.
- **Frontmatter editors / other query engines** — **marad/frontmatter** (Go get/set/delete CLI),
  **mdbasequery** (Obsidian-Bases query engine, not SQL), **yq** (general YAML CLI with a
  front-matter mode).

# Comparison across five dimensions

**1. Frontmatter conventions & identity.** All task tools duplicate an `id` in both frontmatter
and filename (Backlog.md: `id: BACK-200` + `back-200 - ....md`; taskmd: `id: "001"`). Dates are
strings, typed only when ISO-8601. The interesting split is *display identity vs. address
identity*:

- **Foam**: a `title:` frontmatter key **overrides the filename** as the note's display name in
  the graph, but wikilinks still resolve by **filename** — producer-settable display name,
  filename stays the address.
- **Dendron**: auto-generates an immutable `id` (23-char, the one field users may not change)
  and *derives* `title` from the filename — identity and display are separate fields.
- **Taskmatter**: namespaces all tool-owned metadata under a single `_tm` key, using an
  underscore prefix to signal "other programs shouldn't touch this" — independent convergence on
  readb's `__`-prefix-means-reader-owned invariant.

**2. Status / lifecycle.** Backlog.md does *not* hardcode statuses — they're declared centrally
in a config file (`statuses: [...]`, `default_status`) and double as kanban columns. taskmd uses
free per-file `status:` values. Neither models a transition graph in files; states live in
config or convention. (readb stays out of this — lifecycle is the *bundle's* concern.)

**3. Dependencies / blocking.** Universal pattern: a `dependencies`/`blocked_by` YAML list of
ids on the depending item. Backlog.md **validates that referenced deps exist** and tracks which
are still blocking; taskmd **computes** over the graph — critical paths, auto blocked/blocking
detection, a `next` command recommending the next actionable task. For readb these are *query
recipes* over `blocked_by`, not engine features.

**4. Query ergonomics.** Real divergence. **Dataview's DQL** is the main non-SQL model: four
query types (`TABLE`/`LIST`/`TASK`/`CALENDAR`), the query type is the only mandatory element,
and data commands (`FROM`/`WHERE`/`SORT`/`GROUP BY`/`LIMIT`/`FLATTEN`) execute *in written
order* — unlike SQL's fixed clause order and set semantics. Frontmatter keys are referenced
**bare/unquoted** (`date(creadate)`), and DQL exposes **implicit file metadata** as queryable
fields (`file.name`, `file.cday`) — direct precedent for readb's virtual columns. Dataview only
types a value as a date when it is ISO-8601 (a `T` separator required for datetimes). Every
task manager, by contrast, is flag/subcommand filtering (`backlog task list -s "To Do"`), not a
language. readb's real-SQL-via-DuckDB buys joins/aggregates/window functions none of these have.

**5. CLI/UX — init, discovery, output.**

- **Backlog.md** has an explicit `backlog init` that lets you pick the folder (`backlog/`,
  `.backlog/`, or custom) *and* config location, **preserves existing config on re-init**, and
  is scriptable (`--backlog-dir`/`--config-location`).
- **Obsidian** marks a vault with `.obsidian/`; **Dendron** creates a workspace via explicit
  init; **taskmd** reportedly cascades config project → `~/.taskmd.yaml` (unverified). The
  dotdir-marker + explicit-init pattern is the established norm — it validated readb's
  `.readb/` registry (ADR 0004).
- **Output/errors**: Backlog.md publishes a strict `--json` contract — versioned envelope,
  missing scalars → `null`, missing collections → `[]`, date-only stays `YYYY-MM-DD`,
  datetimes RFC-3339; `--json`/`--plain` mutually exclusive; JSON always non-interactive;
  **errors leave stdout empty**, write to stderr, exit nonzero. Structure is preserved even
  when empty — evidence used to fix readb's zero-row csv header.
- **marad/frontmatter** mirrors readb's `get`/`set`/`unset` triad but **infers YAML types from
  CLI syntax** (`count=42`→int, `tags=[a,b]`→list, `published=true`→bool) — the opposite of
  readb's deliberately string-literal, never-guess field editor.
- **Obsidian on filename clashes**: duplicates across folders are allowed, never warned about;
  a bare `[[note]]` resolves by "shortest path when possible" and manually-typed ambiguous
  links have effectively undefined resolution ("matches the first one it finds"). readb
  deliberately differs: ambiguous bare names are a hard error listing the clashing paths.

# Adoption & maturity (checked 2026-07-17)

- **Backlog.md** — **~6.2k stars, 372 forks**, TypeScript, MIT. Very active: v1.48.0 released
  2026-07-12, ~1,026 commits, on Homebrew (`backlog-md`), community VS Code extension. Positive
  [Hacker News launch thread](https://news.ycombinator.com/item?id=44483530) (top asks:
  dependency management, Jira/OpenRouter integration). The most mature/adopted tool in the
  survey by a wide margin.
- **MarkdownDB** — **~495 stars, 25 forks**, TypeScript, npm `mddb`. **Stalled**: latest
  release v0.9.5 March 2024, pre-1.0, 9 open issues / 0 PRs at check time.
- **frontmatter-mcp** — **1 star, 2 forks** (Python, DuckDB, v0.5.3 Dec 2025). Effectively
  zero adoption; architecturally the closest twin to readb. The niche is validated yet
  unclaimed in practice.

**Positioning takeaway.** The DuckDB-SQL-over-frontmatter idea is *proven viable but
essentially unadopted*, and the one tool with real users in the space (MarkdownDB) builds a
**managed on-disk index** you regenerate and maintain. readb's distinction: **the index is
transparent and disposable** — in-memory today (a wrapped `.readb/` cache later), never a
database the user manages. You point at a directory and query; the DB is an implementation
detail. That framing — plus read-only load, permissive lossless parsing, the one narrow write
path, and OKF shape — is the niche, and it is open.

# Ideas — where they went

Routed into sprint-002 designs (all shipped or decided there):

1. Foam/Dendron identity precedent + Taskmatter's `_tm` → the `name-column-unprefix` decision
   (keep `__name` immutable; producer `name:` inert).
2. Backlog.md `init` + the dotdir-marker norm → `bundle-init-discovery` / ADR 0004.
3. Backlog.md's structure-preserved-when-empty contract → the zero-row csv header fix.
4. Dataview's strict ISO date typing → context for `tz-aware-datetime-handling`.

Adopted as backlog drafts: `readme-prior-art` (public positioning),
`field-editor-type-inference` (typed `set` — research), `frontmatter-schema-checking`
(opt-in declare/check — research).

Consciously rejected: a Dataview-style query DSL (readb runs real SQL by hard constraint);
implicit type inference in the field editor (violates "never guess producer intent");
central status/lifecycle config and dependency computation in the engine (bundle concerns /
plain SQL queries, not reader features).

# Sources

Primary repos/docs: `github.com/MrLesk/Backlog.md` (+ `CLI-INSTRUCTIONS.md`),
`github.com/driangle/taskmd` (+ `driangle.github.io/taskmd`), `github.com/mtoohey31/taskmatter`,
`github.com/marad/frontmatter`, `blacksmithgu.github.io/obsidian-dataview`,
`github.com/blacksmithgu/obsidian-dataview`, `foambubble.github.io/foam`, `wiki.dendron.so`,
`github.com/datopian/markdowndb` (+ `markdowndb.com`), `github.com/kzmshx/frontmatter-mcp`,
`github.com/intellectronica/mdbasequery`, `mikefarah.gitbook.io/yq`, plus the Obsidian forum
(filename-clash behavior) and Hacker News (Backlog.md launch).
