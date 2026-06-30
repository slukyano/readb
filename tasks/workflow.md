---
type: Process
title: Task workflow
description: How tasks in this bundle are drafted, refined, and implemented — and how the agent loop moves them.
tags:
- meta
- process
timestamp: '2026-06-30T00:00:00Z'
---

# Overview

This `tasks/` directory is the project backlog **and** an OKF bundle — a directory of markdown
files with YAML frontmatter, one file per task. We dogfood okdb here: the backlog is queried
with okdb itself (see [Querying with okdb](#querying-with-okdb)), and an **agent loop**
(`scripts/agent-loop.sh`) advances one task by one step per run.

- Each task is one concept document with `type: Task`.
- This workflow doc is a `type: Process` concept (so it stays out of the `task` table).
- `index.md` and `log.md` are OKF-reserved (a listing and a change log); they are not tasks.

# Lifecycle

A task moves along a single **linear** chain, tracked in the `status` frontmatter field:

```
                 ┌── agent loop · PR · human approval ──┐         ┌── agent loop · PR · human approval ──┐
   Draft ───────►│              Refining                │──────► Refined ──►│           Implementing            │──────► Done
  (a seed)       └──────────── (claim → refine) ─────────┘  (plan merged)   └─────────── (claim → build) ────────┘  (impl merged)
```

There is **no `approved` status**: human approval *is* the PR merge. Approving/merging the
refine PR is what advances `Refining → Refined`; approving/merging the implement PR advances
`Implementing → Done`.

| `status` | Meaning | Who sets it | Advances when |
|----------|---------|-------------|---------------|
| `Draft` | A seed — a few words to a short description. Unclaimed. | Human or agent (often committed directly to `main`) | The loop claims it for refinement. |
| `Refining` | A loop run has **claimed** it; refinement is in progress or its PR awaits human review. **(lock)** | The loop, as a claim commit on `main` | The refine PR is merged. |
| `Refined` | An executable plan is merged and in place. Unclaimed, ready to implement. | The merged refine PR | The loop claims it for implementation. |
| `Implementing` | A loop run has **claimed** it; implementation is in progress or its PR awaits review. **(lock)** | The loop, as a claim commit on `main` | The implement PR is merged. |
| `Done` | Implementation merged. | The merged implement PR | — (terminal) |
| `Dropped` | Abandoned; record why in the body. | Human | — (terminal) |

`Refining` and `Implementing` are **in-progress markers**: while a task sits in one of them, the
loop will not pick it up again. Because the chain is linear and single-writer, exactly one
actor advances a task at a time.

# Claim / lease (the lock)

When the loop picks a task it **claims** it by committing the in-progress status to `main`
(`Draft → Refining` or `Refined → Implementing`) along with advisory lease fields:

- `claimed_by` — who/what holds the claim (e.g. `user@host`).
- `claimed_at` — UTC ISO-8601 time of the claim.

The claim commit is **pushed before any work begins**, so a concurrent run sees the lock and
skips the task (single-flight). If the push is rejected because someone else claimed first, the
run rolls the claim back and bows out.

The lease fields are advisory — they let a human see how long a task has been held. They are
deliberately **not** auto-expired: if a PR is abandoned (closed unmerged), the task stays in its
in-progress state until a human releases it:

```sh
scripts/agent-loop.sh --release <task-id>   # Refining → Draft, or Implementing → Refined
```

(Automatic stale-claim reclaim by lease age is left for later — see the
[research task](research-similar-tools.md) — to avoid duplicating work that is still in review.)

# Frontmatter schema

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `type` | yes | string | Always `Task`. |
| `title` | yes | string | Short imperative title. |
| `description` | recommended | string | One-line summary; also used in `index.md`. |
| `status` | yes | string | `Draft` \| `Refining` \| `Refined` \| `Implementing` \| `Done` \| `Dropped`. |
| `priority` | recommended | string | `low` \| `medium` \| `high`. |
| `tags` | optional | list | Cross-cutting labels (`research`, `cli`, `packaging`, …). |
| `created` | recommended | date | ISO date the draft was created. |
| `timestamp` | optional | string | OKF-reserved; ISO-8601 of the last meaningful change. |
| `blocked_by` | optional | list | Concept IDs of tasks that must be `Done` first (see below). |
| `claimed_by` / `claimed_at` | while claimed | string | Advisory lease (set on `Refining`/`Implementing`). |
| `branch` / `pr` | optional | string | Set by the loop when it opens a branch / PR. |

Producers may add more keys — okdb's union-of-keys keeps them queryable, and columns simply
appear once the first task uses them.

# Blockers

`blocked_by` lists the **Concept IDs** of prerequisite tasks (a Concept ID is the filename
without `.md`, e.g. `choose-package-name`). A task is *ready* when:

1. its `status` is `Draft` or `Refined` (i.e. unclaimed and actionable), and
2. every task in `blocked_by` is `Done`.

A dangling or mistyped blocker counts as blocking (conservative — better to stall than to
double-build). Blocking is a dependency, not a status: keep it in `blocked_by`, not in `status`.

# The agent loop (`scripts/agent-loop.sh`)

One run moves **one task by one step**:

1. Sync `main`.
2. Select the next *ready* task — highest `priority`, then oldest `created`, then `__id`.
3. **Claim** it on `main` (`status` → `Refining`/`Implementing` + lease), and push (the lock).
4. Branch `task/<id>/<refine|implement>`.
5. Invoke the agent to do the work; on success it sets the task to the target status
   (`Refined`/`Done`) and clears the lease, on the branch.
6. For implementation, run the **validation gate** (`uv run pytest` + `uv run ruff check`).
7. Open a PR and stop. **Human review** (plus a **subagent review**) and the merge complete the
   step — landing `Refined`/`Done` on `main`.

```sh
scripts/agent-loop.sh                 # advance one ready task by one step
scripts/agent-loop.sh --dry-run       # show what it would do; change nothing
scripts/agent-loop.sh --task <id>     # operate on a specific task
scripts/agent-loop.sh --release <id>  # release a stuck claim
```

Configuration is via environment variables (see the script header): `BUNDLE` (default `tasks`),
`OKDB`, `AGENT_CMD` (override the agent invocation — defaults to `claude -p`; set it to a no-op
or a different agent for testing), `CLAIM_OWNER`, `BRANCH_PREFIX`, `MAIN_BRANCH`, `NO_PR`.

Schedule the loop (cron, or a `while` wrapper) to keep the backlog moving. Because claimed tasks
are skipped, repeated runs **fan out across distinct tasks** rather than racing on one.

# Gates (must-haves)

- **Human approval** — merging the PR is the approval, and it is what advances the status (both
  transitions). PRs are never auto-merged.
- **Validation** — the result is always covered by tests, and they (plus `ruff`) pass.
- **Review** — a subagent reviews the diff (e.g. `/code-review`) before merge.

# Querying with okdb

```sh
# The whole board, highest priority first
okdb query "SELECT status, priority, title FROM task
            ORDER BY CASE lower(priority) WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END" --bundle ./tasks

# What the loop would pick next: ready (Draft or Refined) and unblocked
okdb query "
  SELECT t.__id, t.status, t.priority
  FROM task t
  WHERE t.status IN ('Draft','Refined')
    AND NOT EXISTS (
      SELECT 1 FROM unnest(t.blocked_by) AS b(dep)
      WHERE NOT EXISTS (SELECT 1 FROM task d WHERE d.__id = b.dep AND d.status = 'Done')
    )
  ORDER BY CASE lower(t.priority) WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
           t.created, t.__id
" --bundle ./tasks

# Count by state
okdb query "SELECT status, count(*) AS n FROM task GROUP BY status ORDER BY n DESC" --bundle ./tasks
```
