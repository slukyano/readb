# Changelog

All notable changes to readb are documented here, following
[Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- `readb set` and `readb unset` no longer corrupt a frontmatter key whose value spans several
  lines (a list, a `|`/`>` block scalar, or a nested mapping). They previously rewrote or removed
  only the `key:` line and left the rest of the value behind as invalid YAML, after which the
  permissive loader skipped the concept silently. Each key is now addressed as a whole span:
  `unset` removes the value entirely, and `set` refuses a multi-line key — with a message saying
  to unset it first — instead of discarding a value you did not name. A refusal leaves the file
  untouched even when other assignments in the same command were valid.
- `readb get` returns a multi-line value as the raw YAML fragment. It previously reported an
  empty string, indistinguishable from an empty scalar.

### Added

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

[Unreleased]: https://github.com/slukyano/readb/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/slukyano/readb/releases/tag/v0.1.0
