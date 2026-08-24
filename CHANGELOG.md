# Changelog

All notable changes to readb are documented here, following
[Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- **Breaking: a column now takes the narrowest type that holds every value in it, instead of
  falling to JSON as soon as two values disagree.** Mixed scalars become `VARCHAR` (a date beside
  a timestamp becomes `TIMESTAMP`, an int beside a float still becomes `DOUBLE`), and maps unify
  into a `STRUCT` of the union of their fields, recursively, with absent fields NULL. JSON remains
  the top of the lattice for values that disagree structurally — a map beside a scalar or a list.
  Queries using JSON extraction on a column that is now `VARCHAR` or `STRUCT` need updating;
  ordinary predicates and struct access start working on those columns.

### Fixed

- Nine frontmatter shapes made an entire bundle unqueryable rather than skipping one file: an
  empty mapping value (which rendered as invalid `STRUCT()` DDL), a mapping whose keys collide once
  stringified, a mapping with an empty-string key, and an integer outside 64 bits. Map keys are now
  stringified when the file is read, with the last of two colliding keys winning, and an integer
  that does not fit is carried as text. If a table still cannot be built it degrades to JSON
  columns — and failing that to its virtual columns — with a warning, instead of failing the load.

- A frontmatter key that is not a string (`1:`, `2026-01-01:`) was silently dropped along with its
  value, breaking the union-of-keys promise. Such keys now become columns under their stringified
  names.

### Added

- A persistent index cache. Once a bundle sits under a `.readb/` registry (`readb init`), readb
  keeps a materialized index in `.readb/cache/` and serves an unchanged bundle from it: on a
  6000-concept bundle a query goes from 4.1 s to 0.14 s, editing one file then querying costs
  0.18 s, and touching every file without changing any costs 0.27 s and re-reads nothing. A
  changed file is re-indexed on its own; anything that would alter the inferred schema rebuilds
  the whole index. Without a registry readb writes nothing, anywhere, exactly as before.
  `readb cache status` and `readb cache clear` inspect and remove it; `--no-cache`,
  `cache = false` in the registry config, and `readb.open(path, cache=False)` switch it off.

- `__hash`, a fifth virtual column on every table: the lowercase hex SHA-256 of the file's bytes,
  the same value `sha256sum` prints. Byte-identical documents are now
  `GROUP BY __hash HAVING count(*) > 1`, and a bundle can be compared against an external record
  without readb growing a feature for it.

### Changed

- The shipped skill and plugin now describe themselves by the situation they apply to rather than
  by their mechanism, naming the trees a question spans and the tools it would otherwise take. A
  benchmark measured the old wording being matched on fewer than half the runs where the skill was
  installed; whether the new wording moves that is a question for the next benchmark, not a claim
  made here.

- Loading a bundle is about 2.9x faster at every size measured. DuckDB's Python client probes each
  non-NULL bound value for pandas types and Python never caches a failed import, so with pandas
  absent every probe walked `sys.path` again — 25,326 times for a 600-concept bundle. The insert
  pass now suppresses the probe: 2000 concepts load in 1.37 s against 3.63 s.

### Fixed

- A query naming a table that does not exist is now answered with the bundle's own tables and a
  pointer to `readb schema`. DuckDB's catalog error was passed through verbatim, so a mistyped
  name could be answered with `Did you mean "duckdb_indexes"?` — a table that exists in no bundle.
  An unknown *column* keeps DuckDB's candidate bindings, which are drawn from the right table, and
  gains the same pointer. `readb.UnknownTableError` is exported and subclasses
  `duckdb.CatalogException`, so existing handlers keep working.

- The shipped usage skill's leading example now invokes `readb` directly. It opened with
  `uvx readb query ...`, so the first runnable line an agent read failed with `command not found`
  on any machine where readb was installed without `uv` — by pip, pipx, Homebrew, a distribution
  package, or a plain venv. `uvx`, `uv tool install` and `pip install` are still named, as the
  recovery for a machine where readb is absent.

## [0.2.0] - 2026-08-09

### Fixed

- `readb set` and `readb unset` no longer corrupt a frontmatter key whose value spans several
  lines (a list, a `|`/`>` block scalar, or a nested mapping). They previously rewrote or removed
  only the `key:` line and left the rest of the value behind as invalid YAML, after which the
  permissive loader skipped the concept — the edit itself reported nothing, so the loss only
  showed up as a document missing from later results. Each key is now addressed as a whole span:
  `unset` removes the value entirely, and `set` refuses a multi-line key — with a message saying
  to unset it first — instead of discarding a value you did not name. A refusal leaves the file
  untouched even when other assignments in the same command were valid.
- `readb get` returns a multi-line value as the raw YAML fragment. It previously reported an
  empty string, indistinguishable from an empty scalar.
- Files with CRLF line endings keep them. Any edit previously rewrote the whole file — body
  included — to LF.
- An edit that changes nothing now writes nothing, so unsetting an absent key leaves the file
  untouched rather than rewriting it.
- `readb set` refuses a value containing a line break instead of writing it across several
  lines, where YAML would fold it into different data.

### Added

- An agent skill teaching how to use readb — the data model, the command surface, and worked SQL
  — shipped from this repository, which now doubles as a plugin marketplace
  (`/plugin marketplace add slukyano/readb`, then `/plugin install readb@readb`). The skill lives
  at `skills/readb/SKILL.md` as a portable folder for runtimes that read skill directories
  directly, and its SQL examples are executed by the test suite so they cannot drift.
- Frontmatter writes are verified before they land: an edit that would turn valid frontmatter
  into invalid frontmatter is abandoned with an error and the file is left unchanged.

## [0.1.0] - 2026-07-21

Initial release.

### Added

- Bundle loading: an OKF bundle (a directory tree of markdown files with YAML frontmatter)
  becomes an in-memory DuckDB database — one table per concept `type`, plus the
  `__DOCUMENTS`, `__INDEXES`, `__LOG`, `__UNKNOWNTYPE` tables and the `__TAGS` view. Loading
  is permissive (bad files are logged and skipped) and strictly read-only.
- Type inference: each column gets the narrowest DuckDB type that losslessly holds every
  observed value, with `JSON` as the universal fallback; the union of producer keys per type
  is lossless (missing key → `NULL`).
- Virtual columns `__path`, `__name`, `__body`, `__raw` on every table; wiki-style concept
  addressing by unique name or full path.
- Library API: `readb.open(path)` → `Database` with `.sql()`.
- CLI: `readb query` (`--format table|json|csv|tsv|raw`), `readb schema`, `readb show`, and
  the surgical frontmatter field editor `readb get`/`set`/`unset`.
- `readb init` and upward bundle discovery: a committed `.readb/config.toml` registry lets
  commands omit `--bundle`.

[Unreleased]: https://github.com/slukyano/readb/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/slukyano/readb/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/slukyano/readb/releases/tag/v0.1.0
