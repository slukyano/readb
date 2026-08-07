---
type: Process
title: Task workflow
description: How development runs in sessions and sprints — scoping, design, autonomous implementation, and approval gates.
tags:
- meta
- process
timestamp: '2026-07-17T00:00:00Z'
---

# Overview

This `backlog/` directory is the project backlog **and** an OKF bundle — one markdown file per
concept. Active tasks live in `tasks/` (named `NNN-slug.md`, numbered sequentially), closed
tasks move to `archive/` at close-out, and sprint records live in `sprints/`; `workflow.md`,
`index.md`, and `log.md` stay at the bundle root. readb is dogfooded here: the backlog is queried
with readb itself (see [Querying with readb](#querying-with-readb)) and all frontmatter edits
go through readb's own field editor (`readb set`/`unset --bundle ./backlog <id> ...`).

Development happens in **sprints**, driven interactively in **sessions**:

- A **session** is one sitting with the **maintainer** (the project's human owner — the two
  roles throughout this workflow are the maintainer and the coding **agent**): open the repo,
  tell the agent to start or continue development.
- A **sprint** is one batch of tasks taken from scope approval through design and
  implementation to a final merge. A sprint usually spans several sessions.

The bundle holds three concept types:

- `Task` — one backlog item per file.
- `Sprint` — one `sprints/sprint-NNN.md` per sprint: the durable state of active and past work.
- `Process` — this document.

`index.md` and `log.md` are OKF-reserved (a listing and a change log); they are not concepts.
Architecture Decision Records live in the developer-docs bundle,
[`docs/dev/adr/`](../docs/dev/index.md).

## Dogfooding rule

readb is the interface to the local OKF bundles. Reading and querying `backlog/` and `docs/dev/`
goes through `readb query`/`readb schema`/`readb get`; edits go through `readb set`/`unset`. Do not
fall back to `cat`, grep, or manual file reads for what readb should answer. When readb fails or
can't express something needed for the workflow: **stop, immediately record a new `Draft` task**
describing the gap, and only then use a workaround. Tasks that block dogfooding readb take
priority over the rest of the backlog when scoping sprints.

# Task lifecycle

```
   Draft ──────► Designed ──────► Done
  (a seed)   (design merged)  (impl merged)      Dropped (terminal, from anywhere)
```

| `status` | Meaning | Set when |
|----------|---------|----------|
| `Draft` | A seed — a few words to a short description. | Authored directly on `main`, anytime, by maintainer or agent. |
| `Designed` | The task body carries an approved design (a `## Design` section). | The sprint's **design merge** lands on `main`. |
| `Done` | Implemented, gated, approved. | The sprint's **final merge** lands on `main`. |
| `Dropped` | Abandoned; the body records why. | Maintainer decision, anytime. |

There are no lock/claim states and no lease fields: sprints are single-flight, and "in a
sprint" is recorded in the sprint concept, not on the task.

# Sprint lifecycle

One sprint moves through:

```
  (scope approved)          (design approved)         (implementation approved)
        │                          │                            │
        ▼                          ▼                            ▼
    Designing ──────────────► Implementing ──────────────────► Done
        │                          │
        └────────── Aborted ◄──────┘   (maintainer decision; record why)
```

## 1. Session start

Every session begins by checking for unfinished work:

```sh
readb query "SELECT __name, status, branch FROM sprint WHERE status NOT IN ('Done','Aborted')" --bundle ./backlog
```

- **An active sprint exists** → check out its branch (the branch always has the freshest
  sprint state) and resume from the sprint body: the task checklist, open questions, and
  session log say exactly where work stopped.
- **No active sprint** → propose scope for a new one.

(A "table with name sprint does not exist" error means no sprint concept has ever been
created — same as no active sprint. Also glance at `git branch --list 'sprint/*'` for a stray
branch.)

## 2. Scoping

The agent reviews the open backlog (`Draft` tasks, unblocked) and proposes a set for the
sprint — proposing *all* open tasks is fine when the scope feels right. The maintainer adjusts and
approves.

The scope is **presented for approval** in the chat protocol (below), with:

- the sprint id, theme, and branch;
- an **in-scope task ledger** — every task as slug, priority, one-line description, and a
  design-weight flag (trivial vs. design-heavy);
- **ordering / dependencies** among the in-scope tasks;
- **considered but out of scope** — tasks weighed and deferred, each with a one-line why;
- the **scope rationale** — what ties the set together and what is deliberately held back;
- the **sprint-start action** requested (commit `backlog/sprints/sprint-NNN.md`, cut `sprint/NNN`).

**Scope approval is the sprint-start commit on `main`**: create `backlog/sprints/sprint-NNN.md`
(status `Designing`, the task list, the branch name), commit it to `main`, then create the
sprint branch `sprint/NNN` from it. All subsequent work happens on the branch.

## 3. Design phase (interactive)

On the sprint branch, the agent and the maintainer design the tasks **one by one**. The maintainer acts
as stakeholder, product owner, and senior architect; the agent drives — proposes a design,
asks questions, records decisions. Per task, the outcome is:

- a `## Design` section written into the task body — the executable plan; and
- zero or more **ADRs** in `docs/dev/adr/` (status `Proposed`) for decisions of architectural
  weight. See [ADRs](#adrs).

Every `## Design` must enumerate the task's **complete public-surface delta** — every new or
changed CLI command, flag, and output format; every public Python API name; every on-disk path,
config key, and packaged artifact. Public surface means the **user-facing contract**, not internal
module or function structure — those belong in the design prose, not the surface list. A task with
no public-surface change states that explicitly. Carry the same enumeration into the
design-approval and close-out presentations.

Commit throughout the phase. When all tasks in scope are designed, present the batch for approval
via the chat protocol below. The presentation **always includes, for each task**: a **design
summary** (what it builds and how the task transformed from its original framing), the **key
decisions** (with the alternatives weighed), the **ADRs** it introduces — each **stated as the
decision it makes, in plain terms, not just its title** — and its **public-surface delta**; then
the explicit open decisions the maintainer must make. Prefer **structured markdown — tables and
lists — over prose** throughout the presentation. **Design approval** triggers, in order:

1. ADRs from this phase flip `Proposed → Accepted` (only the maintainer approves ADRs).
2. Tasks flip `Draft → Designed`; the sprint flips `Designing → Implementing`.
3. The sprint branch is **merged to `main`** (design merge). The branch stays alive.

## 4. Implementation phase (autonomous)

The agent implements the designed tasks independently — preferably in one long run, using
subagents where appropriate. Rules of the phase:

- **Commit throughout**, per coherent step, on the sprint branch.
- **Track progress** in the sprint body (per-task checklist), so any session can resume.
- **Stop and ask**: if a decision surfaces that belongs to the maintainer — a product call or an
  architectural fork the design doesn't cover — do **not** guess. Record the open question in
  the sprint body (`## Open questions`), commit, and stop that task (or the sprint, if it
  blocks everything). Fidelity over throughput.
- New decisions of architectural weight get ADRs (`Proposed`) as part of the change.

## 5. Gates (must pass before presenting)

- **Validation** — the repository's declared checks pass
  ([`DEVELOPMENT.md` § Checks](../DEVELOPMENT.md#checks)). **Every new code path carries a test**:
  a branch no test exercises is not delivered.
- **Hands-on verification** — every new, changed, or fixed behavior is **run and observed**, not
  merely unit-tested. Automated tests prove the logic; this gate proves the thing works when used.
  Drive the CLI and read its output — commands, flags, output formats, error messages, exit codes
  — and exercise the Python API directly. For a change to the write path, inspect the resulting
  file bytes, not just the parsed result. Where behavior differs between the working copy and an
  installed build, verify the built artifact too. Scenarios that cannot be driven — anything
  needing a credential, a live registry, or a third-party service — are **named as such in the
  presentation, never quietly skipped**.
- **Independent review** — a fresh subagent with no implementation context reviews the full
  sprint diff; findings are fixed (or explicitly presented as known issues).
- **Publication hygiene** — everything committed must be publishable as-is, since the repo
  (history included) is public-bound. Two checks:
  - **Hygiene** — no identifiable individuals except the author/copyright identity in an
    authorship or license capacity; no environment leakage (local paths, credentials, private
    links, internal hostnames, machine-specific artifacts); claims about other projects factual,
    dated, and sourced (state facts, never disparage); and nothing in a user-facing surface that
    presents this project's own development process as part of readb (see `AGENTS.md`).
  - **Voice** — impersonal and agentless: name the thing, not the actor (nominal or passive
    constructions), no second-person or chat-transcript prose, no project "we". The sole
    exception is this document's governance statements, where a role *is* the meaning ("only the
    maintainer approves ADRs"); records, product docs, ADR decisions, and summaries carry no
    roles.

## 6. Close-out, presentation & final merge

Once the gates pass, close the sprint out **on the branch** so the maintainer reviews the exact
state that will merge — bookkeeping included. The only thing gated purely on approval is the
merge itself.

### 6a. Close-out bookkeeping (committed to the branch, before presenting)

1. Flip every delivered task `Designed → Done` via the field editor
   (`readb set --bundle ./backlog <name> status=Done timestamp=<ISO>`); update the timestamp.
2. Flip the sprint `Implementing → Done` (same editor) and update its timestamp.
3. Write a `## Sprint summary` into the sprint body and a close-out `## Session log` line.
4. Move each closed task's file from `tasks/` to `archive/` and bring the hand-maintained
   `backlog/index.md` and `backlog/log.md` current (list Done tasks under `# Done`; mark the
   sprint Done; add a dated log entry).
5. **Every open question / deferred idea must have a home.** If something was left undone —
   deliberately or by omission — it is either done now or captured as a `Draft` task. Never
   say "carried to the backlog" without a concrete task name; create the task if none exists.
6. Commit the bookkeeping (`chore(sprint): close out sprint-NNN ...`).

### 6b. The summary artifact + independent accuracy check

Write the full review to a **file** (e.g. `.scratchpad/sprint-NNN-review.md`), then have a
**fresh reviewer subagent** (no implementation context) verify it against the real diff
(`git diff main..sprint/NNN`) and the live gate output — commit/file counts, test numbers,
task states, and every "what changed" / "bug fixed" / "limitation" claim. Fix any inaccuracy
the reviewer finds **before** presenting. Do not present an unverified summary.

### 6c. Presentation format (always include)

Present in the chat protocol below. The summary MUST include:

- **A task ledger listing *every* task involved** — Done, Dropped, created-this-sprint, and
  planned-but-descoped. For each: its **relative weight** (`major` / `mid` / `minor` — size AND
  importance AND future impact; e.g. a package rename is a small diff but major impact), and a
  **brief description — one sentence, shorter where possible**, covering three things:
  1. **what the change is**;
  2. **what the plan was**;
  3. **how the plan changed**.

  Points 2 and 3 are omitted when the delivered change *is* the approved design with no
  transformation — most tasks. Saying so in the sentence is the whole signal: no warning glyph, no
  separate "transformed" marker, since a mark beside a description that already states the change
  is redundant, and a mark on nearly every row means nothing at all.
- **The public-surface delta** for the sprint as a whole, in the terms §3 defines.
- **Explicitly what was NOT done** — deliberately or by omission — each item paired with its
  disposition (done, or the **named** `Draft` task that now holds it).
- **Breaking changes.**
- **Architectural decisions** made, with their ADRs.
- **Bugs found & fixed** (review findings & how they were resolved) — its own section.
- **Remaining limitations & highlights** — a separate, clearly-flagged must-read section
  (sharp edges, deliberate trade-offs, things a user will trip on), never folded into prose.

Whenever the summary says something was deferred or carried forward, **name the backlog task
that holds it** — never a bare "added to the backlog".

### 6d. Final merge

**Implementation approval** triggers, in order:

1. New ADRs flip `Proposed → Accepted` (or are revised/rejected per the maintainer).
2. The sprint branch is **merged to `main`** (final merge, `--no-ff`) and deleted.

(Task/sprint status flips already happened in 6a; if the maintainer sends changes back, revert or
adjust the bookkeeping before merging.) Tasks that didn't make it stay `Designed` (or return to
`Draft` if the design was invalidated) and go back to the backlog for a future sprint.

# Asking for approval (chat protocol)

All approvals happen **in the chat**. The maintainer decides from what's presented there — files
are for double-clicking into details, never required reading for a decision. Whenever the
agent finishes an iteration or needs a decision, it formats the ask as:

1. a **separator** (`---`),
2. the **question or summary in short** — one or two sentences,
3. the **complete decision context** — everything needed to decide, self-contained in the
   chat (quote the relevant parts; never just point at files, never dump whole files). A
   batch approval that covers tasks (scope, design, implementation) lists **every task in
   the batch with at least a one-line description** — never a bare task name, never "as
   presented before",
4. **references to the key files** touched or decided on (paths, with line numbers where it
   helps), so the maintainer can double-click into any detail,
5. the **explicit list of questions** to answer (or the single question), each answerable
   with a short reply,
6. a closing **TLDR block** — always last, and mandatory (format below).

This applies to scope approval, design approval, implementation approval, ADR acceptance,
and stop-and-ask questions raised mid-implementation.

## The closing TLDR

Every approval gate and every question set ends with:

```
# TLDR - <topic> - <phase> <Approval | Questions>
```

`Questions` means the phase continues after the answers; `Approval` means the next phase begins
on approval. Example headings: `# TLDR - Sprint 004 - Field editor typing - Design Approval`,
`# TLDR - Sprint 004 - Design Questions`.

Under the heading:

- a **bullet summary** of what is being looked at;
- the **list of questions or items to approve explicitly**, with the recommendation in **bold**.

Each question must be understandable **on its own** — no reliance on the prose above it, on an
earlier message, or on a file. The TLDR repeats what a decision needs rather than referring to it.

**Nothing else belongs in it.** The TLDR is read first and often alone, bottom-up; the prose above
exists to be double-clicked into, not summarised a second time. The bar is *just enough to make
scrolling up unnecessary* — and no more. Measurements, narrative, file lists, what was tried and
rejected, per-item detail that does not change an answer: all of that goes above the separator.

- **Gates are one line**: green or not, and the names of the checks that ran — e.g. *gates green
  (ruff format, ruff check, pytest, hands-on, independent review)*. Test counts, timings, and
  per-check output stay above.
- **A fact earns its place only by changing a decision.** If the answer is the same whether or not
  the maintainer knows it, it is not TLDR material.

### Standard sections

In this order, **omitting any that is empty**:

1. **Done** — **applied changes only**: what was written somewhere durable — commits (pushed or
   not), files created or edited, anything published to another repository or service. One line
   per item: slug plus a few words, not a sentence. Includes scope creep and any extra work beyond
   the approved set, marked as such, and work with no task behind it. Analysis, answers, findings,
   and proposals that exist only in the chat are **not** Done — a draft is not a change, and
   neither is a scratch file. If nothing was written, the section is omitted.
2. **Scope rejected** — what the sprint took on and did *not* deliver, dropped after the scope was
   approved. Never lists what was never in the started scope.
3. **ADRs** — what each decides, summarised.
4. **Surfaces** — what changed in the public surface, summarised.
5. **Backlog changes** — changes to the *backlog itself*: tasks created, removed, retitled, or
   re-scoped outside the sprint scope, and anything filed rather than fixed. Work that was simply
   carried out is **Done**, not a backlog change. Informational: **no approval is asked for
   these.**
6. **Gates** — one line, per above.
7. **The asks**, numbered. An ask exists for every decision not already approved explicitly — a
   new or changed ADR, a decision taken during implementation the approved design did not cover.
   **The ask to merge is always last.**

### Message layout

A message is plain prose, then **sections separated by `---`** — including before the TLDR. Each
section covers one topic or one workflow operation: an acknowledgement, the context behind one
ask, the TLDR. Sections are **lettered `A.`, `B.`, `C.`…** in order. Only one may be a TLDR, and
it is always last.

The TLDR's heading **names every topic it covers**, joined with `+`, so it is clear which sections
it draws on.

```
plain chat text — the answer, the finding, whatever is being said
---
A. <topic> - Confirmation
  an approved action that has now been carried out
---
B. <topic> - Approval
  the context behind its ask
---
C. <other topic> - Approval
  the context behind its ask
---
D. TLDR - <topic> + <other topic> - Approval
  the TLDR
```

An action that was already approved and has now been carried out is **confirmed, never
re-approved**: it appears in a Confirmation section and never in the TLDR, whose `Done` covers
only changes belonging to the decision still open.

There is no notes section, and no section for commentary. If an item is not one of the above, the
threshold for mentioning it at all is that a decision changes without it.

**Every ask has a matching section above the TLDR**, one per ask, carrying the context the ask
itself is too short to hold: what the decision is, what the alternatives were, and the references
worth opening — task slugs, ADRs, key files with line numbers. The ask stays one or two lines; the
section above it is where the reasoning lives.

**An ask to publish something carries the thing itself.** Filing an issue, opening a PR, sending a
comment, posting a release note — the exact proposed text is part of the ask, not a summary of it,
because the text *is* what is being approved. Short texts go inline; anything long enough to bury
the decision goes in a file under the scratchpad with its path given in the ask.

Each section **names its ask in its heading** — `## Ask 1 — <the question>` — so the pairing is
obvious from either direction and survives renumbering. Sections appear in ask order.

**An ask is a question or a choice, never a topic.** "Ask 1 — the write path and the guard" is a
subject line; "Ask 1 — should `set` refuse a multi-line key?" is an ask. For an approval, state
the **lasting effect being approved** — how the thing behaves from now on — rather than the edit
that produced it, because the edit is not what is being agreed to. The same sentence opens the
section, so the decision is legible without reading the reasoning under it.

Every presentation is **self-contained**: full context and the explicit question(s) spelled out
each time, never "as before" or a bare pointer. **Final approvals** (scope, design,
implementation) are always presented on the **complete** artifact as a whole; partial or
incremental presentations are legitimate only to gather intermediate feedback, never as the basis
for a final sign-off — unless the maintainer explicitly opts into a partial.

# Sprint frontmatter schema

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `type` | yes | string | Always `Sprint`. |
| `title` | yes | string | Short theme, e.g. "CLI ergonomics". |
| `status` | yes | string | `Designing` \| `Implementing` \| `Done` \| `Aborted`. |
| `branch` | yes | string | The sprint branch, e.g. `sprint/001`. |
| `tasks` | yes | list | concept names of the tasks in scope. |
| `created` | yes | date | ISO date of the sprint-start commit. |
| `timestamp` | recommended | string | OKF-reserved; ISO-8601 of the last meaningful change. |

The **body** is the working state: scope rationale, a per-task checklist (`[ ]` → `[x]`) kept
current during implementation, `## Open questions` (the stop-and-ask log), and a short
`## Session log` (one line per session: date, what moved).

# Task frontmatter schema

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `type` | yes | string | Always `Task`. |
| `title` | yes | string | Short imperative title. |
| `description` | recommended | string | One-line summary; also used in `index.md`. |
| `status` | yes | string | `Draft` \| `Designed` \| `Done` \| `Dropped`. |
| `priority` | recommended | string | `low` \| `medium` \| `high`. |
| `tags` | optional | list | Cross-cutting labels (`research`, `cli`, `packaging`, …). |
| `created` | recommended | date | ISO date the draft was created. |
| `timestamp` | optional | string | OKF-reserved; ISO-8601 of the last meaningful change. |
| `blocked_by` | optional | list | concept names of tasks that must be `Done` first. |

Producers may add more keys — readb's union-of-keys keeps them queryable, and columns simply
appear once the first task uses them. A missing `blocked_by` means unblocked; don't write
empty lists.

## Blockers

`blocked_by` lists the **concept names** of prerequisite tasks (a concept name is the filename
without `.md`). A task is eligible for a sprint when its `status` is `Draft` (or `Designed`,
for implementation) and every task in `blocked_by` is `Done`. A dangling or mistyped blocker
counts as blocking (conservative — better to stall than to double-build). Tasks within one
sprint may depend on each other; the design phase orders them.

# ADRs

Architecture Decision Records live in [`docs/dev/adr/`](../docs/dev/adr/) — a concept
directory in the developer-docs bundle, one concept per decision, named `NNNN-short-slug.md`.
The bundle's [`index.md`](../docs/dev/index.md) owns the ADR schema and lifecycle; the summary
below mirrors it.

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `type` | yes | string | Always `ADR`. |
| `title` | yes | string | The decision, stated as a decision. |
| `status` | yes | string | `Proposed` \| `Accepted` \| `Rejected` \| `Superseded`. |
| `created` | yes | date | ISO date proposed. |
| `sprint` | optional | string | concept name of the originating sprint. |
| `superseded_by` | when superseded | string | concept name of the replacing ADR. |

Body: Context, Decision, Consequences (and Alternatives considered, when useful).

Rules:

- The agent **proposes** ADRs — during design sessions and during implementation — as part of
  the change itself, committed on the sprint branch.
- **Only the maintainer approves ADRs.** `Proposed → Accepted` happens at the batch approval
  (design or implementation), never unilaterally.
- Reversing an accepted decision means a new ADR that supersedes the old one, not an edit.

```sh
readb query "SELECT __name, status, title FROM adr ORDER BY __name" --bundle ./docs/dev
```

# Querying with readb

```sh
# Anything in flight?
readb query "SELECT __name, status, branch FROM sprint WHERE status NOT IN ('Done','Aborted')" --bundle ./backlog

# The open backlog, highest priority first
readb query "SELECT __name, priority, title FROM task WHERE status = 'Draft'
            ORDER BY CASE lower(priority) WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, created" --bundle ./backlog

# Sprint-eligible: Draft and unblocked
readb query "
  SELECT t.__name, t.priority
  FROM task t
  WHERE t.status = 'Draft'
    AND NOT EXISTS (
      SELECT 1 FROM unnest(t.blocked_by) AS b(dep)
      WHERE NOT EXISTS (SELECT 1 FROM task d WHERE d.__name = b.dep AND d.status = 'Done')
    )
  ORDER BY CASE lower(t.priority) WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
           t.created NULLS LAST, t.__name
" --bundle ./backlog

# Count by state
readb query "SELECT status, count(*) AS n FROM task GROUP BY status ORDER BY n DESC" --bundle ./backlog
```
