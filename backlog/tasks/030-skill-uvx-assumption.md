---
type: Task
title: The shipped skill's leading example assumes uv is installed
description: skills/readb/SKILL.md opens with `uvx readb …`, which fails on a machine where readb is installed but uv is not.
status: Designed
priority: medium
tags:
- skill
- docs
- agents
created: 2026-08-10
timestamp: '2026-08-22T12:30:00Z'
---

Found by the agent-efficiency benchmark (`024`, sprint-004), where it invalidated a whole arm
before it was understood. The benchmark gave the skill arm `readb` on `PATH` but not `uv`; 17 of
36 runs issued `uvx readb …`, got `exit 127: command not found`, and spent extra turns
recovering. The arm measured 1.21× the baseline's cost until the environment was corrected, at
which point it measured 1.01×.

The benchmark environment was artificial, but the assumption is not:

```
skills/readb/SKILL.md:14   uvx readb query "SELECT …" --bundle ./library
skills/readb/SKILL.md:15   uv tool install readb    # or install it once and drop the uvx prefix
```

The first runnable line an agent reads requires `uv`. Line 15 mentions the alternative, but an
agent that copies the leading example on a machine with `readb` on `PATH` and no `uv` gets a
failure it then has to diagnose. Machines where readb was installed by pip, pipx, Homebrew, a
distribution package, or a plain venv are exactly this case.

## Notes (to refine)

- The cheapest fix is ordering: lead with bare `readb …`, and mention `uvx readb` as the
  no-install path afterwards. That inverts the current presentation.
- Consider having the skill open with a one-line capability probe (`command -v readb || echo
  "use: uvx readb"`), so the agent resolves the invocation once instead of guessing.
- The same assumption may sit in `README.md` and the plugin manifest — check all three surfaces
  together, not just the skill.
- The skill is distributed pinned to a commit through the plugin marketplace, so a correction
  reaches installed copies only on re-pin; worth confirming how that interacts with
  [027-plugin-marketplace-submission](027-plugin-marketplace-submission.md).

## Design

### Surface audit — one surface carries the defect, not three

The notes flagged three surfaces to check together. Checked:

| Surface | Leading invocation | Verdict |
| --- | --- | --- |
| `skills/readb/SKILL.md:13–16` | `uvx readb query …`, then `uv tool install readb` as a comment | **the defect** |
| `README.md:30–38` | an `## Install` section (`uv tool install` / `pip install`), then bare `readb` in every example | correct already |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | none — the manifests carry metadata, no commands | nothing to fix |

The skill is also inconsistent with itself: every one of its other ~20 shell examples invokes the
bare binary. Only the opening block asks for `uv`.

### The fix — invert the ordering, and name the recovery

Lines 13–16 become:

````
```sh
readb query "SELECT title, year FROM book WHERE year < 1980" --bundle ./library
```

If that reports `command not found`, readb is not installed: `uvx readb query ...` runs it
without installing, and `uv tool install readb` or `pip install readb` installs it once.
````

Two properties, both deliberate:

- **The executable surface is uniformly bare.** The fallback is prose, not a fenced line, so
  every runnable line in the file is a command that works on any machine with readb installed.
- **The recovery is stated, not discovered.** An agent on a machine without readb reads the
  failure mode and its fix in the same paragraph, so `exit 127` costs one retry instead of a
  diagnosis.

**Rejected: the capability probe** (`command -v readb || echo "use: uvx readb"`, from the notes).
It spends a turn to learn what the failure already reports — and v1 of the efficiency benchmark
measured cost as turn-driven (`≈ $0.019/turn`), so a probe on every invocation is a standing tax
paid by every agent to protect the minority without readb installed. It also opens a document
about SQL with a shell idiom.

### Regression tests

Two mechanical tests in `tests/test_skill.py`, alongside the existing example-execution suite:

- the first fenced `sh` block's first line invokes `readb` directly;
- no line inside any fenced `sh` block invokes readb through a runner prefix (`uvx `, `uv run `,
  `uv tool run `).

The second is the durable one: it keeps the property as the skill grows, rather than pinning the
one line known to be wrong today.

### Distribution — how the correction reaches installed copies

The repository doubles as its own plugin marketplace (`README.md:122–127`), and an install from
it tracks the repository rather than a pinned commit, so an existing install picks the correction
up on its next marketplace update. The *community* catalog pins to a commit SHA and re-pins as
commits land — but that is [`027-plugin-marketplace-submission`](027-plugin-marketplace-submission.md),
still `Draft`. The fix therefore lands before any submission, and 027 needs no coordination
beyond ordering.

### Ordering against `031`

`030` lands **before the first measured v2 run**, so v2 measures the corrected skill rather than
the artifact whose defect retracted an arm of v1. Two consequences for the benchmark:

- The `readb-skill` arm **keeps `uv` on `PATH`**, as `031`'s approved arm table declares. The fix
  makes `uv` unnecessary, not forbidden; leaving it removes a way for the arm to fail on
  something other than what is being measured. The comment justifying it in
  `benchmarks/run_benchmark.py:157–160` is rewritten to say that, since its current reasoning
  ("that arm cannot execute its own documentation without it") stops being true.
- The v2 write-up states that its skill arm measured the corrected skill, so v2's skill numbers
  are not read as comparable to v1's retracted ones.

### Public-surface delta

`skills/readb/SKILL.md` — the leading example block: `uvx readb query …` plus a
`uv tool install readb` comment becomes a bare `readb query …` line plus a prose fallback naming
`uvx readb`, `uv tool install readb`, and `pip install readb`.

Nothing else. No CLI command, flag, or output format; no Python API name; no config key or
on-disk path; no change to the packaged wheel or sdist (the skill ships through the plugin
manifests, not the distribution).
