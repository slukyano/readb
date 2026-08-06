# Changelog

All notable changes to readb are documented here, following
[Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
