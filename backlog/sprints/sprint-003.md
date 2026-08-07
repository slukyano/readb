---
type: Sprint
title: Post-0.1.0 adoption — usage skill, prior art, release automation
description: Ship a readb usage skill, place readb honestly among prior art in the README, automate tag-triggered releases, and fix the field editor's multi-line corruption bug.
status: Done
branch: sprint/003
tasks:
- 026-field-editor-multiline-corruption
- 025-ship-usage-skill
- 019-readme-prior-art
- 023-release-automation
created: 2026-08-06
timestamp: '2026-08-07T00:00:00Z'
---

Third sprint under the [session/sprint workflow](../workflow.md), and the first after 0.1.0
reached PyPI.

## Scope rationale

The follow-through on going public: readb now has users, so it should teach its own use
(`ship-usage-skill`), state honestly where it sits among prior art (`readme-prior-art`), and make
the next release a tag push instead of a manual token upload (`release-automation`).

`field-editor-multiline-corruption` was **found during this sprint's own scoping** and added by
the agent: correcting `release-automation`'s stale `blocked_by` — the one bookkeeping fix
approved at scoping — corrupted the file, because the line-based editor orphans the continuation
lines of any multi-line value. It is data loss in readb's only write path and it blocks
dogfooded frontmatter edits, so it leads the sprint (workflow: dogfooding-blocking tasks take
priority). Confirmed in scope by the maintainer, 2026-08-06.

Deliberately out of scope: `measure-agent-efficiency` (largest task in the backlog — corpus
generation, harness, repeat runs; also wants `ship-usage-skill` to exist first, for its third
arm), `bundle-index-log-automation`, and the four research tasks
(`field-editor-type-inference`, `frontmatter-schema-checking`, `cross-bundle-querying`,
`research-body-structured-query`), which form a natural roadmap-shaping sprint of their own.

Scope-time bookkeeping, already committed with this file:

- `release-automation`'s `blocked_by` listed `publish-readb-0-1-0` — a name that never existed
  (the concept is `022-publish-readb-0-1-0`). A dangling blocker counts as blocking, so the task
  was invisible to the eligibility query. The blocker is satisfied (022 is `Done`), so the key
  was removed rather than corrected. Removed by hand: readb itself cannot do this edit today —
  that is `026`.
- Recorded in `AGENTS.md`: readb's public surfaces must never present this project's own
  development process as part of the tool (maintainer instruction at scope approval, 2026-08-06).
  Directly binding on `ship-usage-skill` and `readme-prior-art`.

## Task checklist

Design phase (a checked box = `## Design` section written and discussed):

- [x] 026-field-editor-multiline-corruption — span detection; `set` refuses a multi-line key,
      `unset` deletes the whole span, `get` stops returning `""`; re-parse guard on the write path
- [x] 025-ship-usage-skill — ⚠️ revised 2026-08-07: the repo becomes its own plugin marketplace
      (`.claude-plugin/` + `skills/readb/SKILL.md`); no wheel packaging, no `readb skill` command
- [x] 019-readme-prior-art — `## Prior art` after Type inference, led by the
      transparent-disposable-index framing; adoption figures re-checked at implementation
- [x] 023-release-automation — tag-triggered `release.yml` on `pypa/gh-action-pypi-publish`
      (it generates PEP 740 attestations; `uv publish` does not); `ci.yml`, `CHANGELOG.md` and
      `CONTRIBUTING.md` already landed on `main` outside a sprint

## Implementation checklist (in order)

1. [x] 026-field-editor-multiline-corruption — span-based get/set/unset + write-path guard; 18 new tests (147 total)
2. [x] 025-ship-usage-skill — plugin + marketplace manifests, portable skills/readb/SKILL.md, neutral library fixture, examples executed by tests
3. [x] 019-readme-prior-art — `## Prior art` added, figures re-checked 2026-08-07
4. [x] Public-surface sweep — CLI help/docstrings and package metadata were already clean; the
       README's examples moved from `tasks`/`docs/adr`/`task` to the neutral `library` bundle
5. [x] 023-release-automation — release.yml (tag guard, checks, build, Trusted Publishing, changelog-sourced GitHub release) + tested extractor; PyPI-side config still with the maintainer
6. [x] Gates: `pytest` (186) + `ruff` clean + independent review of the sprint diff; every
       finding fixed or given a task

## Sprint summary

Delivered all four tasks. Gates green at close: **186 tests** (129 at sprint start, +57), all
passing where the optional upstream `ga4` fixture is cloned and 182 passing / 4 skipping where it
is not; `ruff` clean; `claude plugin validate --strict` passes; the built sdist's own suite runs
standalone (182 passed, 4 skipped — the sdist does not vendor that fixture).

**Per task:**

- `026-field-editor-multiline-corruption` — found while executing this sprint's own scope
  approval. `set`/`unset` assumed a key occupied one line, so any multi-line value had its
  continuation lines orphaned into invalid YAML, after which the permissive loader skipped the
  concept. The *edit* was the silent part — exit 0, no warning — while the skip logged to stderr;
  either way the concept vanished from every query. A key is now addressed by its whole span: `unset` removes it, `set`
  refuses a multi-line key all-or-nothing, `get` returns the raw fragment instead of `""`, and
  `_rewrite` abandons any write that would turn valid frontmatter invalid.
- `025-ship-usage-skill` — ⚠️ **transformed at design review.** The first design packaged the
  skill in the wheel behind a new `readb skill` command; the maintainer rejected both, and the
  result uses the mechanism that already exists: the repository carries `.claude-plugin/` and is
  its own plugin marketplace, with `skills/readb/SKILL.md` as a portable folder. Every SQL
  example in the skill is executed by the suite against a new neutral `library` fixture.
- `019-readme-prior-art` — a `## Prior art` section led by the transparent-disposable-index
  framing. Re-checking the figures was not a formality: MarkdownDB has moved to
  `flowershow/markdowndb` and is active again, so sprint-002's survey reading of it as *stalled*
  (`**Stalled**: latest release v0.9.5 March 2024`) was about to be repeated as a live claim
  about another project. The accuracy check then caught that fixing the README alone was not
  enough — the survey it links to still carried the superseded reading, and now carries a dated
  correction instead.
- `023-release-automation` — ⚠️ **shrank before it started**: `ci.yml`, `CHANGELOG.md` and
  `CONTRIBUTING.md` had already landed on `main` outside a sprint, leaving the release workflow
  itself. Pushing a `v*` tag now guards tag against version, re-runs the checks, builds,
  publishes with Trusted Publishing, and creates the GitHub release from a tested changelog
  extractor. `pypa/gh-action-pypi-publish` beat `uv publish` on evidence: it generates PEP 740
  attestations by default and uv does not.
- Public-surface sweep (added at scope approval) — the README's examples no longer borrow this
  project's own setup, and the sdist no longer ships `backlog/`, `docs/`, `AGENTS.md`.

**Breaking changes:** none to any documented behavior. Two write-path behaviors tighten: `set`
now refuses a multi-line key and a value containing a line break, where both previously wrote
something (in the first case, corruption).

**Architectural decisions:** no ADRs. The write-path contract is unchanged; what changed is that
`fields.py` now uses PyYAML to *verify* a rewrite, which relaxed its "stdlib only" note to the
invariant that always mattered — it never round-trips YAML.

**Bugs found and fixed.** Beyond `026` itself, self-review caught a false "string-literal `set`"
claim in two public surfaces (`n=42` reads back as `BIGINT`; `flag=true` is quoted and stays
text). The independent review then found nine issues, all fixed here:

1. *High, a regression this branch introduced*: the span terminator matched a narrow key
   charset, so a dotted, spaced, quoted or non-ASCII key read as a continuation and was deleted
   with its neighbour — and readb writes dotted keys itself. The test now asks whether a line
   *continues* the value above it.
2. A flow collection left open on the key line (`tags: {x: 1,`) was half-removed, and the
   remainder still parsed, so the guard could not catch it. Bracket depth now bounds the span.
3. The changelog section was validated *after* the irreversible PyPI upload; it moved into the
   build job, plus a test tying the package version to a non-empty section.
4. A manual "TestPyPI rehearsal" on a tag ref would have cut a real GitHub release, and the
   dispatch path could reach real PyPI while skipping the tag guard. Manual runs are now
   TestPyPI-only and never release.
5. The extractor truncated at a `##` inside a fenced block and stripped mid-body link
   definitions — both silently, at exit 0.
6. Every edit rewrote CRLF files to LF, body included, and a no-op edit rewrote the file at all.
7. The guard exempted frontmatter that parsed as a non-mapping — precisely the case an edit
   turns into a parse error.
8. Test gaps: examples were lower-bounded rather than counted, the Python example was
   transcribed rather than extracted, and passing required only "does not raise".
9. Doc claims: `init` takes no `--bundle`, `__LOG` exists only with a `log.md`, and README links
   into sdist-excluded paths now resolve on PyPI.

**Remaining limitations — read before using the write path:**

- **`set` writes what YAML reads back, not always a string.** `n=42` becomes an integer;
  `flag=true` is quoted and stays text. Documented in the skill; the asymmetry is recorded on
  [016](../tasks/016-field-editor-type-inference.md), whose framing it invalidates.
- **Duplicate keys make `get` and `query` disagree** — `set` edits the first occurrence, YAML
  resolves to the last ([029](../tasks/029-field-editor-remaining-edges.md)).
- **A `---` inside a block scalar ends the frontmatter early** for the editor and the parser
  alike — consistently, but not as a YAML reader would ([029](../tasks/029-field-editor-remaining-edges.md)).
- **The release workflow has never run.** It cannot until the trusted publisher exists on PyPI
  and TestPyPI — a maintainer action. The first tag is also the first live test.
- The skill reaches users through the marketplace, not through `pip install readb`.

**Not done, each with a home:** community-marketplace listing →
[027](../tasks/027-plugin-marketplace-submission.md); the Rust question →
[028](../tasks/028-evaluate-rust-rewrite.md); write-path edges →
[029](../tasks/029-field-editor-remaining-edges.md); typed `set` →
[016](../tasks/016-field-editor-type-inference.md). Still deferred:
[024](../tasks/024-measure-agent-efficiency.md) (untouched but for a re-pointed link),
[009](../tasks/009-bundle-index-log-automation.md),
[005](../tasks/005-research-body-structured-query.md), [017](../tasks/017-frontmatter-schema-checking.md),
[021](../tasks/021-cross-bundle-querying.md) — these four wholly untouched.

## Open questions

- **`023` hand-off** (still open at close, maintainer action): configuring the PyPI trusted
  publisher — owner `slukyano`, repo `readb`, workflow `release.yml`, environment `pypi`, and the
  same on TestPyPI (environment `testpypi`) for rehearsals. Approved at scoping; the workflow
  shipped unverified because it cannot run until this exists.

Resolved:

- **Scope addition** (2026-08-06) — `026` confirmed in scope by the maintainer.
- **Rust rewrite vs. `023`** (2026-08-07) — the maintainer raised that automating a PyPI release
  pipeline is the wrong investment order if readb is leaving Python. Recorded with its measured
  evidence as [028-evaluate-rust-rewrite](../tasks/028-evaluate-rust-rewrite.md) and sequenced
  behind [024](../tasks/024-measure-agent-efficiency.md); `023` **stays in this sprint** — the
  workflow's skeleton (tag guard, changelog extraction, GitHub release) survives any rewrite, and
  a Python 0.x line would keep releasing through a transition.

## Session log

- **2026-08-06** — Scope approved in chat (`ship-usage-skill`, `readme-prior-art`,
  `release-automation`). Sprint created, branch `sprint/003`. Scoping turned up the field-editor
  multi-line corruption bug; recorded as `026`, confirmed into scope. Design phase completed the
  same day: all four `## Design` sections written; the publishing mechanism decided against
  `uv publish` on the attestation evidence; a public-surface sweep added to implementation.
- **2026-08-07** — Design review with the maintainer. `025` reworked: the skill leaves `src/` and
  the repository becomes its own plugin marketplace; the `readb skill` command and wheel packaging
  are dropped. `019`'s exact README text drafted into the task, with figures re-checked — the
  survey's "MarkdownDB stalled since March 2024" is stale and the repository has moved to
  `flowershow/markdowndb`. New drafts:
  [027-plugin-marketplace-submission](../tasks/027-plugin-marketplace-submission.md),
  [028-evaluate-rust-rewrite](../tasks/028-evaluate-rust-rewrite.md). **Design approved** the same
  day, `023` kept in scope: the four tasks flipped `Draft → Designed`, the sprint flipped
  `Designing → Implementing`, and the branch design-merged to `main`. Implementation started.
- **2026-08-07 (close-out)** — Implementation completed in one run, in checklist order. The
  independent review returned nine findings, one of them a High regression this branch had
  introduced into the span logic; all nine were fixed and pinned by tests, and the pre-existing
  edges it surfaced became [029](../tasks/029-field-editor-remaining-edges.md). Tasks flipped
  `Designed → Done`, sprint `Implementing → Done`, files archived, index and log brought current.
  Gates green: 186 tests, `ruff` clean. A second fresh reviewer fact-checked this summary against
  the diff and live gate output; six inaccuracies in it were corrected, one of which was
  substantive — the superseded MarkdownDB reading still shipped in the survey the new README
  section links to, and now carries a dated correction.
