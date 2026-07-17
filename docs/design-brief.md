Build `readb`: a transparent, read-only SQL query layer over an Open Knowledge Format (OKF) bundle — a directory of markdown files with YAML frontmatter — so an agent or human can run real SQL against the wiki with no explicit database-creation step.

Start by initializing the project according to /new-project skill.

## Context: what OKF is

OKF is Google Cloud's Open Knowledge Format (v0.1, June 2026). Spec:
https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

Read the spec first. Essentials you must honor:
- A "bundle" is a directory tree of UTF-8 markdown files. Each file is one "concept."
- A concept's identity is its file path with the `.md` suffix removed (the "Concept ID").
- Each file = YAML frontmatter block (delimited by `---`) + a free-form markdown body.
- The ONLY required frontmatter field is `type`. Reserved optional fields: `title`,
  `description`, `resource`, `tags`, `timestamp`. Producers may add arbitrary other keys.
- `index.md` and `log.md` are RESERVED filenames at any directory level — NOT concept docs.
- Consumers MUST be permissive: tolerate unknown keys, broken cross-links, missing
  `index.md`, and malformed files. Never crash on a bad file — log and skip.

## Stack

Python. Defer to my local skills/toolchain for libraries, test framework, project layout,
and packaging — DO NOT prescribe specific versions or dependencies here.

One hard architectural constraint: do NOT write a SQL parser or query planner. Load the
bundle into an embedded engine that supports JSON/nested values AND joins, and let it execute
the SQL. **DuckDB is the recommended engine** (native LIST/STRUCT/JSON types, fast, in-memory
or single-file). The persistent-index format (future) should be a DuckDB file so it can be
opened without rebuilding.

## What to build (MVP)

A library + thin CLI. Conceptually:

    db = readb.open("./path/to/bundle")   # builds an in-memory DuckDB, no files written
    rows = db.sql("SELECT * FROM __DOCUMENTS WHERE type = 'Metric'")

### Tables / views
1. `__DOCUMENTS` — one row per concept across the whole bundle. Columns: the six reserved
   OKF fields (`type`, `title`, `description`, `resource`, `tags`, `timestamp`) + the two
   virtual fields below. These are the only fields guaranteed for every concept.
2. One table per detected `type`. Columns = reserved fields + the UNION of all
   producer-defined keys across docs of that type (missing keys → NULL). Union-of-keys is the
   default and must be lossless.
3. `__INDEXES` — one row per reserved `index.md` file (any directory level). Columns = the
   UNION of frontmatter fields across all `index.md` files + the virtual fields. (`log.md`
   handled the same way as `__LOG` if present, else omit.)
4. `__UNKNOWNTYPE` — one row per non-conformant concept: a doc with NO `type`, a `type` that
   is not a string, or a `type` whose normalized form is empty (see normalization). These
   still appear in `__DOCUMENTS` (with their raw/NULL type).

### Virtual fields (on every table)
- `__path` — concept path relative to the bundle root, WITH the `.md` suffix
  (e.g. `tables/orders.md`). Concept ID is this minus `.md`; expose both if cheap.
- `__body` — the markdown body, frontmatter stripped. (Plain text for now.)

### Type-name normalization (frontmatter `type` → SQL table name)
- Lowercase, then DELETE every character not valid in a SQL identifier (keep `[a-z0-9_]`,
  drop everything else including spaces). E.g. `Big %// Table` → `bigtable`.
- If the result starts with a digit, prefix `_` (e.g. `3D Model` → `_3dmodel`).
- If the result is empty, the doc routes to `__UNKNOWNTYPE`.
- Pure deletion widens the collision surface (`big table` and `bigtable` collide). On
  collision between two distinct original types, append `_2`, `_3`, … and emit a warning.
- Keep a mapping (normalized name ↔ original type string) callers can query via `readb schema`.

### Column type unification (the lattice — get this right)
Per table, per column, infer ONE type at load time that losslessly holds every observed
value, then coerce on insert. **JSON is the top of the lattice and the universal fallback.**
Rules, narrowest-fit-wins:
- Absent / null never constrains the column type.
- All values one scalar kind → that type. `int` mixed with `float` → `double`.
- Scalar mixed with list for the same key → promote each scalar to a singleton list; the
  column is a LIST. Unify element types by these same rules (incompatible elements → element
  type JSON).
- Maps with a consistent key set → STRUCT; inconsistent keys → JSON.
- Any combination that doesn't reduce to a single engine type → store the RAW parsed value as
  a JSON column (queryable via DuckDB JSON path operators). Nothing is dropped.
- Do NOT guess at producer intent: never split a comma-string into a list, never parse
  strings into numbers. A YAML string stays a string.
- `tags` is OKF-reserved and semantically a list: always coerce to LIST (bare scalar →
  singleton). Also expose a normalized `__TAGS(concept_path, tag)` view for join-style tag
  filtering. Arbitrary producer keys use the general lattice above.
- Worked example: `tag: 1, 2, 3` (YAML parses this as the STRING "1, 2, 3") in one doc and
  `tag: [1, 2, 3]` (list of int) in another → singleton-promotion gives `["1, 2, 3"]` vs
  `[1, 2, 3]`, element types don't unify → column type `LIST<JSON>`.

### CLI (binary: `readb`)
- `readb query "<SQL>" --bundle ./path` → results as a table (`--json` for JSON).
- `readb schema --bundle ./path` → detected types, their normalized table names, inferred
  columns + types, and the type-name mapping.

## Explicit NON-goals for this MVP (leave seams, don't implement)
- No persistent/on-disk index. Re-read and re-parse the whole bundle every run (milliseconds
  at hundreds of files). Isolate the load path so a cache can wrap it later. Intended future
  design: index is a DuckDB file keyed to a git hash; on load, diff the working tree against
  that hash and re-parse only changed files (handles dirty working trees). Build the seam, not
  the cache.
- No git awareness, no incremental rebuild, no secondary indexes, no watcher/daemon. (Daemon
  is low-value because, with a DuckDB-file index, page cache + mmap make repeat opens near-free;
  the only residual win is amortizing process startup.)
- No write-back from SQL. The query/load path is strictly READ-ONLY: loading and querying never
  modify the markdown files. (DML-via-SQL would be asymmetric: UPDATE/DELETE map to frontmatter
  rewrites, INSERT does not map cleanly — out of scope.) The one sanctioned write path is a
  separate, explicit frontmatter field editor (`readb get`/`set`/`unset`, `readb.fields`) that edits
  a single concept's `key: value` lines in place — deliberately kept out of the SQL/load path.
- No body-structure parsing. `__body` is text; addressing it as a DOM/JSON tree by heading is
  a future, type-specific feature. Leave a hook.
- No schema enforcement. Inference only. Leave a clean seam for an OPTIONAL future "declared
  schema per type" mode that validates and fails loudly.

## Test fixtures

Clone Google's reference bundles (real, conformant, small, multi-type, cross-linked):

    git clone --depth 1 https://github.com/GoogleCloudPlatform/knowledge-catalog
    # bundles at: knowledge-catalog/okf/bundles/{ga4,stackoverflow,crypto_bitcoin}

- Primary fixture: `okf/bundles/ga4` (17 files; datasets/tables/references types).
- Join-stress fixture: `okf/bundles/crypto_bitcoin` (cross-table FK relationships in prose).
- Hand-author a tiny offline bundle under `tests/fixtures/mini/` so tests don't need network,
  with deliberately nasty cases: a type with spaces and symbols; a type normalizing to a
  leading digit; a type normalizing to empty; two distinct types that collide after
  normalization; two docs of one type with disjoint extra keys; a `tags` list AND a bare-scalar
  `tags`; a key that is scalar in one doc and a list in another; a key with a nested map; a doc
  with no `type`; a doc whose `type` is a number; a broken cross-link; a stray `index.md`; and
  one malformed-YAML file that must be skipped.

## Acceptance criteria (write as tests)
1. `__DOCUMENTS` row count for `ga4` = number of `.md` files EXCLUDING every `index.md`/`log.md`.
2. Each distinct `type` yields a table; `readb schema` lists normalized names, columns+types,
   and the original-type mapping.
3. A doc missing an optional key a sibling has → NULL, not an error (union-of-keys is lossless).
4. `__INDEXES` contains one row per `index.md`, with the union of their frontmatter fields.
5. Docs with no/non-string/empty-normalized type land in `__UNKNOWNTYPE` and still appear in
   `__DOCUMENTS`.
6. Normalization: `Big %// Table` → `bigtable`; leading-digit → `_`-prefixed; empty → routed to
   `__UNKNOWNTYPE`; a normalization collision between two distinct types gets `_2` + a warning.
7. `__path` ends in `.md` and is bundle-root-relative; `__body` has the body and none of the YAML.
8. `tags` is a LIST column (bare scalars promoted to singletons); `__TAGS` view supports
   JOIN-based tag filtering.
9. Type unification: mixed int/float column → double; scalar-vs-list key → LIST; the
   `tag: "1, 2, 3"` vs `tag: [1,2,3]` case → `LIST<JSON>`; an unmixable key → JSON column,
   value preserved.
10. A cross-type JOIN (`__DOCUMENTS` ⋈ a per-type table on `__path`) returns correct rows.
11. The malformed-YAML fixture is skipped with a warning; the load still succeeds.
12. No files are created or modified anywhere in the bundle during any operation.

Start by reading the spec and the `ga4` fixture, then propose the module layout and the
two-pass load (infer unified column types, then coerce + insert) before writing implementation.
