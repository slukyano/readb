---
name: readb
description: Query a directory of markdown files with YAML frontmatter using real SQL, and make surgical single-field frontmatter edits. Use when asked to search, filter, count, group, or cross-reference markdown documents by their frontmatter, when answering a question would otherwise mean opening many files, or when one frontmatter field needs changing.
license: Apache-2.0
---

# readb

readb loads an **OKF bundle** — a directory tree of markdown files with YAML frontmatter — into
an in-memory DuckDB and runs SQL over it. The index is built on each run and thrown away: the
markdown files are the only state, and loading or querying never writes anything.

```sh
uvx readb query "SELECT title, year FROM book WHERE year < 1980" --bundle ./library
uv tool install readb    # or install it once and drop the uvx prefix
```

## When to reach for it

Use readb instead of opening or grepping files whenever the question is about frontmatter across
documents: counts and rollups, filtered listings, "which document has X", joins between document
types, or anything needing `GROUP BY`/`ORDER BY`. One query replaces a directory walk.

Read the document body directly (or `readb show`) when the question is about prose in one known
file. readb indexes the body as a column, not as structure.

## The data model

**One table per `type`.** A concept's `type` frontmatter value becomes a normalized table name:
`type: Book` → table `book`, `type: 3D Model` → `_3dmodel`. Always run `readb schema` first — it
prints every table, its original type, and every column with its inferred type.

**Reserved tables** exist alongside those:

| Table | Rows |
| --- | --- |
| `__DOCUMENTS` | every concept in the bundle |
| `__INDEXES` / `__LOG` | the reserved `index.md` / `log.md` files, which are *not* concepts. `__LOG` exists only if the bundle has a `log.md` |
| `__UNKNOWNTYPE` | concepts with a missing or unusable `type` |
| `__TAGS` | a `(concept_path, tag)` view, for tag filtering by join |

**Four virtual columns** are on every table:

| Column | Value |
| --- | --- |
| `__path` | bundle-relative path including `.md` — the guaranteed-unique key |
| `__name` | the bare file name, no directory and no `.md` (wiki-style) |
| `__body` | the markdown body with frontmatter stripped |
| `__raw` | the byte-exact file text, frontmatter included |

`__name` is derived from the filename and is immutable. A `name:` key in frontmatter is an
ordinary data column and changes nothing about addressing.

**Union of keys, never an error.** A type's table has a column for every key any document of
that type uses; documents missing that key simply have `NULL`. Adding a key to one file adds a
column for the whole type.

**Types are inferred, never guessed.** Each column gets the narrowest DuckDB type that holds
every observed value losslessly (`int` + `float` → `DOUBLE`; a scalar next to a list → a list).
Anything that will not reduce to one type is stored as `JSON` — nothing is dropped. Producer
intent is never inferred: `"1, 2"` stays the string `"1, 2"`, and `"42"` stays a string. `tags`
is always a list.

**Loading is permissive.** Unparseable files are logged and skipped rather than failing the run,
so a bad file means a missing row — if a document you expect is absent from a result, check
stderr for a `skipping ...` line.

## Commands

| Command | Purpose |
| --- | --- |
| `readb query "<SQL>"` | run SQL; `--format table\|json\|csv\|tsv\|raw` |
| `readb schema` | tables, their source types, columns, inferred types |
| `readb show <name>...` | print a concept's body (frontmatter stripped) |
| `readb get <name> <key>` | print one frontmatter field |
| `readb set <name> KEY=VALUE ...` | set frontmatter fields in place |
| `readb unset <name> KEY ...` | remove frontmatter fields |
| `readb init [DIRS...]` | declare bundles so `--bundle` can be omitted |

Every command except `init` takes `--bundle <dir>`. Concepts are addressed by bare `<name>` when unique in the
bundle, or by full `sub/dir/name.md` path; an ambiguous name is a hard error listing the clashes,
never a silent first match.

### Skipping `--bundle`

`readb init docs notes` writes a `.readb/config.toml` registry declaring those directories as
bundles. Commands then walk up from the working directory to the nearest registry and resolve the
bundle containing it. Explicit `--bundle` always wins and works on any directory, registered or
not. Where the choice is genuinely ambiguous — several declared bundles, none containing the
working directory — readb errors and lists them rather than guessing.

## Worked examples

Against a bundle of `Book` and `Author` concepts:

```sh
# What is in here at all?
readb schema --bundle ./library

# Filter and sort on frontmatter fields.
readb query "SELECT title, year, status FROM book WHERE year < 1980 ORDER BY year" --bundle ./library

# Roll up instead of counting by hand.
readb query "SELECT status, count(*) AS n FROM book GROUP BY status ORDER BY n DESC" --bundle ./library

# Join across types — here a book's author field holds another concept's name.
readb query "SELECT b.title, a.title AS author FROM book b JOIN author a ON a.__name = b.author" --bundle ./library

# Find the documents that lack a field, which the union-of-keys model makes trivial.
readb query "SELECT __name FROM book WHERE rating IS NULL" --bundle ./library

# Tags are a list; use the __TAGS view to filter by one.
readb query "SELECT t.tag, count(*) AS n FROM __TAGS t GROUP BY t.tag ORDER BY n DESC" --bundle ./library

# Search the body text when frontmatter is not enough.
readb query "SELECT __name FROM __DOCUMENTS WHERE __body ILIKE '%cyberspace%'" --bundle ./library

# --format raw prints values verbatim: this is exactly cat.
readb query "SELECT __raw FROM book WHERE __name = 'dune'" --format raw --bundle ./library

# Machine-readable output for further processing.
readb query "SELECT title, year FROM book" --format json --bundle ./library
```

Library use is the same engine:

```python
import readb

db = readb.open("./library")
rows = db.sql("SELECT title FROM book WHERE 'classic' IN tags")
```

## Editing frontmatter

`readb set` / `readb unset` are the only way readb writes, and they are deliberately narrow: a
line-based editor that changes only the lines of the keys named. Other fields, list formatting,
and the body stay byte-for-byte identical, so the diff shows exactly the intended change. It is
not a YAML round-trip and it will not reformat a file.

```sh
readb set --bundle ./library dune status=reading rating=5
readb unset --bundle ./library dune notes
```

Two constraints follow from that narrowness:

- **The value is written verbatim, and readb converts nothing.** `rating=5` writes
  `rating: 5`, which YAML then reads back as the number `5`. There is no syntax for lists or
  nested values. Values YAML would misread are quoted so they survive as text: `flag=true`
  writes `flag: 'true'` and stays the string `true`, not a boolean.
- **Multi-line values are refused by `set`.** A key whose value is a list, block scalar, or
  nested mapping cannot be overwritten with a scalar — `unset` it first if that is the intent.
  `unset` removes such a value in full, and `readb get` returns it as its raw YAML fragment.

An edit that would leave the frontmatter unparseable is abandoned and the file left unchanged.

## Rules of thumb

- Run `readb schema` before writing a query against an unfamiliar bundle; column names come from
  the data, not from a fixed schema.
- Query the specific type table when you know the type, `__DOCUMENTS` when you do not.
- Prefer one SQL query over several narrower ones; the bundle is loaded once per invocation, so
  the load, not the query, is the cost.
- `index.md` and `log.md` are reserved names, not concepts — look for them in `__INDEXES`, and
  in `__LOG` where a `log.md` exists (querying `__LOG` in a bundle without one is a
  "table does not exist" error).
- readb never modifies files while reading. Any change comes from an explicit `set`/`unset`.
