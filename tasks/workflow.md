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

This `tasks/` directory is the project backlog **and** an OKF bundle — one markdown file per
concept. We dogfood readb here: the backlog is queried with readb itself (see
[Querying with readb](#querying-with-readb)) and all frontmatter edits are made with readb's own
field editor (`readb set`/`unset --bundle ./tasks <id> ...`).

Development happens in **sprints**, driven interactively in **sessions**:

- A **session** is one sitting with the human: open the repo, tell the agent to start or
  continue development.
- A **sprint** is one batch of tasks taken from scope approval through design and
  implementation to a final merge. A sprint usually spans several sessions.

The bundle holds three concept types:

- `Task` — one backlog item per file.
- `Sprint` — one `sprint-NNN.md` per sprint: the durable state of active and past work.
- `Process` — this document.

`index.md` and `log.md` are OKF-reserved (a listing and a change log); they are not concepts.
Architecture Decision Records live in a separate bundle, [`docs/adr/`](../docs/adr/index.md).

## Dogfooding rule

readb is the interface to the local OKF bundles. Reading and querying `tasks/` and `docs/adr/`
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
| `Draft` | A seed — a few words to a short description. | Authored directly on `main`, anytime, by human or agent. |
| `Designed` | The task body carries an approved design (a `## Design` section). | The sprint's **design merge** lands on `main`. |
| `Done` | Implemented, gated, approved. | The sprint's **final merge** lands on `main`. |
| `Dropped` | Abandoned; the body records why. | Human decision, anytime. |

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
        └────────── Aborted ◄──────┘   (human decision; record why)
```

## 1. Session start

Every session begins by checking for unfinished work:

```sh
readb query "SELECT __name, status, branch FROM sprint WHERE status NOT IN ('Done','Aborted')" --bundle ./tasks
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
sprint — proposing *all* open tasks is fine when the scope feels right. The human adjusts and
approves.

**Scope approval is the sprint-start commit on `main`**: create `tasks/sprint-NNN.md`
(status `Designing`, the task list, the branch name), commit it to `main`, then create the
sprint branch `sprint/NNN` from it. All subsequent work happens on the branch.

## 3. Design phase (interactive)

On the sprint branch, the agent and the human design the tasks **one by one**. The human acts
as stakeholder, product owner, and senior architect; the agent drives — proposes a design,
asks questions, records decisions. Per task, the outcome is:

- a `## Design` section written into the task body — the executable plan; and
- zero or more **ADRs** in `docs/adr/` (status `Proposed`) for decisions of architectural
  weight. See [ADRs](#adrs).

Commit throughout the phase. When all tasks in scope are designed, the human reviews the
batch. **Design approval** triggers, in order:

1. ADRs from this phase flip `Proposed → Accepted` (only the human approves ADRs).
2. Tasks flip `Draft → Designed`; the sprint flips `Designing → Implementing`.
3. The sprint branch is **merged to `main`** (design merge). The branch stays alive.

## 4. Implementation phase (autonomous)

The agent implements the designed tasks independently — preferably in one long run, using
subagents where appropriate. Rules of the phase:

- **Commit throughout**, per coherent step, on the sprint branch.
- **Track progress** in the sprint body (per-task checklist), so any session can resume.
- **Stop and ask**: if a decision surfaces that belongs to the human — a product call or an
  architectural fork the design doesn't cover — do **not** guess. Record the open question in
  the sprint body (`## Open questions`), commit, and stop that task (or the sprint, if it
  blocks everything). Fidelity over throughput.
- New decisions of architectural weight get ADRs (`Proposed`) as part of the change.

## 5. Gates (must pass before presenting)

- **Validation** — the full suite passes: `uv run pytest` and `uv run ruff check`. New
  behavior is covered by tests.
- **Independent review** — a fresh subagent with no implementation context reviews the full
  sprint diff; findings are fixed (or explicitly presented as known issues).

## 6. Close-out, presentation & final merge

Once the gates pass, close the sprint out **on the branch** so the human reviews the exact
state that will merge — bookkeeping included. The only thing gated purely on approval is the
merge itself.

### 6a. Close-out bookkeeping (committed to the branch, before presenting)

1. Flip every delivered task `Designed → Done` via the field editor
   (`readb set --bundle ./tasks <name> status=Done timestamp=<ISO>`); update the timestamp.
2. Flip the sprint `Implementing → Done` (same editor) and update its timestamp.
3. Write a `## Sprint summary` into the sprint body and a close-out `## Session log` line.
4. Bring the hand-maintained `tasks/index.md` and `tasks/log.md` current (move Done tasks to a
   `# Done` section; mark the sprint Done; add a dated log entry).
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
  **⚠️ mark if it transformed significantly** during design or implementation.
- **Per change: what changed and why, and how the task transformed** from its original framing.
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

1. New ADRs flip `Proposed → Accepted` (or are revised/rejected per the human).
2. The sprint branch is **merged to `main`** (final merge, `--no-ff`) and deleted.

(Task/sprint status flips already happened in 6a; if the human sends changes back, revert or
adjust the bookkeeping before merging.) Tasks that didn't make it stay `Designed` (or return to
`Draft` if the design was invalidated) and go back to the backlog for a future sprint.

# Asking for approval (chat protocol)

All approvals happen **in the chat**. The human decides from what's presented there — files
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
   helps), so the human can double-click into any detail,
5. the **explicit list of questions** to answer (or the single question), each answerable
   with a short reply.

This applies to scope approval, design approval, implementation approval, ADR acceptance,
and stop-and-ask questions raised mid-implementation.

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

Architecture Decision Records live in [`docs/adr/`](../docs/adr/) — itself an OKF bundle, one
concept per decision, named `NNNN-short-slug.md`.

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
- **Only the human approves ADRs.** `Proposed → Accepted` happens at the batch approval
  (design or implementation), never unilaterally.
- Reversing an accepted decision means a new ADR that supersedes the old one, not an edit.

```sh
readb query "SELECT __name, status, title FROM adr ORDER BY __name" --bundle ./docs/adr
```

# Querying with readb

```sh
# Anything in flight?
readb query "SELECT __name, status, branch FROM sprint WHERE status NOT IN ('Done','Aborted')" --bundle ./tasks

# The open backlog, highest priority first
readb query "SELECT __name, priority, title FROM task WHERE status = 'Draft'
            ORDER BY CASE lower(priority) WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, created" --bundle ./tasks

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
" --bundle ./tasks

# Count by state
readb query "SELECT status, count(*) AS n FROM task GROUP BY status ORDER BY n DESC" --bundle ./tasks
```

# History

Until 2026-07-09 the backlog ran on a PR-per-step agent loop (`scripts/agent-loop.sh`, statuses
`Refining`/`Refined`/`Implementing`, claim/lease locks). It was replaced by this
session/sprint workflow — see [ADR 0001](../docs/adr/0001-sessions-sprints-workflow.md).
